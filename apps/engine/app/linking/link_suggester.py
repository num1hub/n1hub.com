"""Link Suggester - Automatic graph edge suggestion (CapsuleOS #11)."""

from __future__ import annotations

from typing import List, Optional

from ..models import CapsuleLink, CapsuleModel
from ..store import BaseCapsuleStore


class LinkSuggester:
    """Suggest graph edges between capsules."""

    def __init__(self, store: BaseCapsuleStore):
        self.store = store

    async def suggest_links(
        self,
        source_capsule: CapsuleModel,
        top_k: int = 5,
        relation_types: Optional[List[str]] = None,
    ) -> List[CapsuleLink]:
        """Suggest links from source to other capsules."""
        all_capsules = await self.store.list_capsules()
        candidates = [
            c
            for c in all_capsules
            if c.metadata.capsule_id != source_capsule.metadata.capsule_id
        ]

        # Score by semantic similarity
        scored = []
        for candidate in candidates:
            score = self._compute_similarity(source_capsule, candidate)
            relation = self._determine_relation(source_capsule, candidate)

            if relation_types and relation not in relation_types:
                continue

            scored.append((candidate, score, relation))

        # Sort and take top_k
        scored.sort(key=lambda x: x[1], reverse=True)
        top_candidates = scored[:top_k]

        # Generate links
        links = []
        for candidate, score, relation in top_candidates:
            reason = self._generate_reason(source_capsule, candidate, relation)
            links.append(
                CapsuleLink(
                    rel=relation,
                    target_capsule_id=candidate.metadata.capsule_id,
                    reason=reason,
                    confidence=min(0.95, max(0.60, score)),
                )
            )

        return links

    def _compute_similarity(self, source: CapsuleModel, target: CapsuleModel) -> float:
        """Compute semantic similarity (keyword + tag overlap)."""
        # Keyword overlap
        source_kw = set(k.lower() for k in source.neuro_concentrate.keywords)
        target_kw = set(k.lower() for k in target.neuro_concentrate.keywords)
        kw_jaccard = len(source_kw & target_kw) / max(1, len(source_kw | target_kw))

        # Tag overlap
        source_tags = set(t.lower() for t in source.metadata.tags)
        target_tags = set(t.lower() for t in target.metadata.tags)
        tag_jaccard = len(source_tags & target_tags) / max(1, len(source_tags | target_tags))

        # Semantic hash match (duplicates)
        if source.metadata.semantic_hash == target.metadata.semantic_hash:
            return 1.0

        return (kw_jaccard * 0.6) + (tag_jaccard * 0.4)

    def _determine_relation(self, source: CapsuleModel, target: CapsuleModel) -> str:
        """Determine relation type using decision tree."""
        # Duplicates check
        if source.metadata.semantic_hash == target.metadata.semantic_hash:
            return "duplicates"

        # Check for extends (version relationship)
        if any("extend" in claim.lower() for claim in source.neuro_concentrate.claims):
            return "extends"

        # Check for depends_on
        if any(
            "depend" in claim.lower() or "require" in claim.lower()
            for claim in source.neuro_concentrate.claims
        ):
            return "depends_on"

        # Default to references
        return "references"

    def _generate_reason(
        self, source: CapsuleModel, target: CapsuleModel, relation: str
    ) -> str:
        """Generate factual reason for link."""
        if relation == "duplicates":
            return f"Shares semantic_hash: {source.metadata.semantic_hash[:30]}..."
        elif relation == "references":
            shared_tags = set(source.metadata.tags) & set(target.metadata.tags)
            return f"References related concepts; shared tags: {', '.join(list(shared_tags)[:2])}"
        elif relation == "extends":
            return f"Extends {target.metadata.tags[0] if target.metadata.tags else 'capsule'} with additional details"
        else:
            return f"Related to {target.metadata.tags[0] if target.metadata.tags else 'capsule'}"
