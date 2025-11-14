from __future__ import annotations

import math
import re
from collections import Counter
from datetime import datetime, timezone
from typing import Any, Dict, List, Sequence

from ulid import ULID

from .config import settings
from .feature_flags import feature_flags
from .linking import LinkSuggester
from .models import (
    CapsuleCorePayload,
    CapsuleMetadata,
    CapsuleModel,
    CapsuleNeuroConcentrate,
    CapsuleRecursive,
    IngestRequest,
)
from .store import BaseCapsuleStore
from .text_utils import STOPWORDS, compute_semantic_hash
from .utils.pii import redact_pii, scan_capsule_for_pii
from .validators import CapsuleValidator


class DeepMinePipeline:
    def __init__(self, store: BaseCapsuleStore) -> None:
        self.store = store

    async def run(self, job_id: str, request: IngestRequest) -> CapsuleModel:
        try:
            # 100 queued -> 110 ingesting
            await self.store.update_job(job_id, code=110, stage="ingesting", state="processing", progress=5)
            normalized = self._normalize(request)
            # 120 normalizing
            await self.store.update_job(job_id, code=120, stage="normalizing", progress=15)
            segments = self._segment(normalized)
            # 130 segmenting
            await self.store.update_job(job_id, code=130, stage="segmenting", progress=30)
            extraction = self._extract(segments, normalized)
            # 140 extracting
            await self.store.update_job(job_id, code=140, stage="extracting", progress=45)
            summary = self._synthesize(normalized, extraction)
            # 150 synthesizing
            await self.store.update_job(job_id, code=150, stage="synthesizing", progress=60)
            neighbors = await self.store.list_capsules()
            capsule = self._assemble(request, normalized, summary, extraction, neighbors)
            # 160 assembling
            await self.store.update_job(job_id, code=160, stage="assembling", progress=75)
            
            # Link suggestion (if feature flag enabled)
            if feature_flags.is_enabled("ff.link.suggester"):
                link_suggester = LinkSuggester(self.store)
                suggested_links = await link_suggester.suggest_links(capsule, top_k=5)
                # Merge with existing links, avoiding duplicates
                existing_targets = {link.target_capsule_id for link in capsule.recursive.links}
                for link in suggested_links:
                    if link.target_capsule_id not in existing_targets:
                        capsule.recursive.links.append(link)
            
            # 170 validating
            await self.store.update_job(job_id, code=170, stage="validating", progress=85)
            validator = CapsuleValidator(strict_mode=False)
            is_valid, errors, warnings = await validator.validate(capsule)
            if not is_valid:
                from .models import JobError
                error = JobError(code=500, stage="validating", issues=errors)
                raise ValueError(error.model_dump_json())
            # 180 indexing
            await self.store.update_job(job_id, code=180, stage="indexing", progress=90)
            await self.store.save_capsule(capsule)
            # Generate and save vector embedding
            text = f"{capsule.neuro_concentrate.summary} {' '.join(capsule.neuro_concentrate.keywords)}"
            from .vectorizer import get_vectorizer
            vectorizer = get_vectorizer()
            embedding = vectorizer.embed(text)
            await self.store.save_vector(capsule.metadata.capsule_id, embedding)
            # 190 reporting
            await self.store.update_job(job_id, code=190, stage="reporting", progress=95)
            await self.store.record_artifact(job_id, {"kind": "capsule", "uri": f"capsules/{capsule.metadata.capsule_id}", "expires_at": None})
            # 200 done
            await self.store.update_job(job_id, code=200, stage="done", state="succeeded", progress=100, capsule_id=capsule.metadata.capsule_id)
            return capsule
        except Exception as exc:
            # 500 failed
            from .models import JobError, JobErrorIssue
            try:
                current_job = await self.store.get_job(job_id)
                current_stage = current_job.stage
            except Exception:
                current_stage = "unknown"
            
            # Try to parse error if it's a JSON string
            error_dict = None
            if isinstance(exc, ValueError) and exc.args and exc.args[0].startswith("{"):
                try:
                    import json
                    error_dict = json.loads(exc.args[0])
                except Exception:
                    pass
            
            if error_dict and "code" in error_dict:
                error = JobError(**error_dict)
            else:
                error = JobError(
                    code=500,
                    stage=current_stage,
                    issues=[JobErrorIssue(path="/pipeline", message=str(exc))],
                )
            await self.store.update_job(job_id, code=500, stage="failed", state="failed", progress=100, error=error.model_dump())
            raise

    def _normalize(self, request: IngestRequest) -> str:
        text = request.content.strip()
        if request.privacy_level == "high":
            text = redact_pii(text)
        return re.sub(r"\s+", " ", text)

    def _segment(self, text: str) -> List[dict[str, Any]]:
        size = settings.rag_chunk_size
        stride = settings.rag_chunk_stride
        tokens = text.split()
        segments: List[dict[str, Any]] = []
        start = 0
        index = 1
        while start < len(tokens):
            chunk_tokens = tokens[start : start + size]
            if not chunk_tokens:
                break
            end_token = start + len(chunk_tokens) - 1
            segments.append(
                {
                    "index": index,
                    "text": " ".join(chunk_tokens),
                    "start_token": start,
                    "end_token": end_token,
                    "chunk_id": None,
                }
            )
            index += 1
            start += max(1, size - stride)
        if not segments:
            fallback_end = max(len(tokens) - 1, 0)
            segments.append(
                {
                    "index": 1,
                    "text": text,
                    "start_token": 0,
                    "end_token": fallback_end,
                    "chunk_id": None,
                }
            )
        return segments

    def _extract(self, segments: Sequence[dict[str, Any]], normalized: str) -> dict:
        keywords = self._keywords(normalized)
        entities = self._entities(normalized)
        claims = [f"{kw.title()} is discussed in the capsule" for kw in keywords[:4]]
        insights = ["DeepMine captured structured knowledge for downstream RAG."]
        questions = [f"How can we operationalize {keywords[0]} within N1Hub workflows?"] if keywords else ["What follow-up data do we need?"]
        archetypes = ["researcher", "operator", "reviewer", "architect", "qa"]
        symbols = ["deepmine", "capsule", "rag", "graph"]
        vector_hint = [kw for kw in keywords[:16]]
        while len(vector_hint) < 8:
            vector_hint.append(f"signal-{len(vector_hint)+1}")
        vector_hint = vector_hint[:16]
        return {
            "keywords": keywords,
            "entities": entities,
            "claims": claims,
            "insights": insights,
            "questions": questions,
            "archetypes": archetypes,
            "symbols": symbols,
            "vector_hint": vector_hint,
            "segments": [segment["text"] for segment in segments],
            "segment_metadata": [segment.copy() for segment in segments],
        }

    def _synthesize(self, normalized: str, extraction: dict) -> str:
        sentences = re.split(r"(?<=[.!?]) +", normalized)
        words: List[str] = []
        summary_parts: List[str] = []
        for sentence in sentences:
            tokens = sentence.split()
            if not tokens:
                continue
            summary_parts.append(sentence.strip())
            words.extend(tokens)
            if len(words) >= 70:
                break
        if len(words) < 70:
            summary_parts.append(
                "This capsule documents how DeepMine processed the material into metadata, neuro concentrate, and graph-ready signals, preserving retrieval defaults and guardrails."
            )
            words.extend(summary_parts[-1].split())
        summary = " ".join(summary_parts)
        summary_words = summary.split()
        if len(summary_words) > 140:
            summary = " ".join(summary_words[:140])
        return summary

    def _assemble(
        self,
        request: IngestRequest,
        normalized: str,
        summary: str,
        extraction: dict,
        neighbors: Sequence[CapsuleModel],
    ) -> CapsuleModel:
        capsule_id = str(ULID())
        now = datetime.now(timezone.utc)
        chunk_metadata = self._assign_chunk_ids(capsule_id, extraction.get("segment_metadata", []))
        extraction["segment_metadata"] = chunk_metadata
        tags = list(dict.fromkeys(tag.lower() for tag in request.tags))
        if len(tags) < 3:
            tags.extend(["capsule", "n1hub", "deepmine"])
        tags = tags[:10]
        length = {"chars": len(normalized), "tokens_est": math.ceil(len(normalized) / 4)}
        semantic_hash = self._semantic_hash(summary)
        metadata = CapsuleMetadata(
            capsule_id=capsule_id,
            created_at=now,
            author=request.author,
            language=request.language,
            source=request.source,
            tags=tags,
            length=length,
            semantic_hash=semantic_hash
        )
        core_payload = CapsuleCorePayload(content=normalized, content_type="text/markdown", truncation_note=None)
        neuro = CapsuleNeuroConcentrate(
            summary=summary,
            keywords=extraction["keywords"][:12],
            entities=extraction["entities"],
            claims=extraction["claims"],
            insights=extraction["insights"],
            questions=extraction["questions"],
            archetypes=extraction["archetypes"],
            symbols=extraction["symbols"],
            emotional_charge=0.0,
            vector_hint=extraction["vector_hint"],
            semantic_hash=semantic_hash
        )
        links = self._links_for_capsule(capsule_id, tags, neighbors)
        recursive = CapsuleRecursive(
            links=links,
            actions=[
                {
                    "name": "Validate-Capsule",
                    "intent": "Run schema + guardrail validation",
                    "params": {"strict_mode": True},
                    "hitl_required": False
                },
                {
                    "name": "Notify-Graph",
                    "intent": "Broadcast new capsule hash to graph monitor",
                    "params": {"capsule_id": capsule_id},
                    "hitl_required": False
                }
            ],
            prompts=[
                {
                    "title": "RAG summary",
                    "prompt": "Summarize capsule context in under 3 sentences with citations."
                },
                {
                    "title": "Faithfulness guardrail",
                    "prompt": "Answer only when context fully supports the claim; otherwise reply with idk+dig_deep."
                }
            ],
            confidence=0.92
        )
        capsule = CapsuleModel(
            include_in_rag=request.include_in_rag,
            metadata=metadata,
            core_payload=core_payload,
            neuro_concentrate=neuro,
            recursive=recursive
        )
        pii_hits = scan_capsule_for_pii(capsule)
        if pii_hits:
            raise ValueError(f"Privacy guardrail triggered: {pii_hits}")
        return capsule


    def _assign_chunk_ids(self, capsule_id: str, segments: Sequence[dict[str, Any]]) -> List[dict[str, Any]]:
        assigned: List[dict[str, Any]] = []
        for segment in segments:
            index = int(segment.get("index", 1))
            start_token = int(segment.get("start_token", 0))
            end_token = int(segment.get("end_token", start_token))
            chunk_id = f"{capsule_id}::c{index:04d}@t{start_token}-{end_token}"
            chunk_record = segment.copy()
            chunk_record["chunk_id"] = chunk_id
            assigned.append(chunk_record)
        return assigned


    def _keywords(self, text: str) -> List[str]:
        tokens = [re.sub(r"[^a-z0-9]", "", token.lower()) for token in text.split()]
        filtered = [token for token in tokens if token and token not in STOPWORDS]
        counts = Counter(filtered)
        ranked = [token for token, _ in counts.most_common(12)]
        while len(ranked) < 5:
            ranked.append(f"signal-{len(ranked)+1}")
        return ranked[:12]

    def _entities(self, text: str) -> List[dict]:
        entities = set()
        for token in re.findall(r"[A-Z][a-z]{2,}[^\s]*", text):
            entities.add(token.strip(",.;:"))
        return [{"type": "concept", "name": entity} for entity in list(entities)[:6]]

    def _links_for_capsule(
        self, capsule_id: str, tags: Sequence[str], neighbors: Sequence[CapsuleModel]
    ) -> List[dict]:
        links: List[dict] = []
        seen: set[str] = set()
        for neighbor in neighbors:
            if neighbor.metadata.capsule_id == capsule_id:
                continue
            overlap = set(tags).intersection(neighbor.metadata.tags)
            if not overlap:
                continue
            if neighbor.metadata.capsule_id in seen:
                continue
            seen.add(neighbor.metadata.capsule_id)
            links.append(
                {
                    "rel": "references",
                    "target_capsule_id": neighbor.metadata.capsule_id,
                    "reason": f"Shared tags: {', '.join(sorted(overlap))}",
                    "confidence": min(0.99, neighbor.recursive.confidence),
                }
            )
            if len(links) == 3:
                break
        return links

    def _semantic_hash(self, summary: str) -> str:
        return compute_semantic_hash(summary)
