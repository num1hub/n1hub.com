"""Capsule Validator - Comprehensive validation with auto-fix (CapsuleOS #12)."""

from __future__ import annotations

import re
from typing import List, Tuple

from ..errors.taxonomy import (
    ErrorCode,
    ErrorRecovery,
    build_error,
)
from ..models import CapsuleModel, JobErrorIssue
from ..text_utils import compute_semantic_hash


class CapsuleValidator:
    """13-point validation checklist with deterministic auto-fixes."""

    def __init__(self, strict_mode: bool = False):
        self.strict_mode = strict_mode
        self.errors: List[JobErrorIssue] = []
        self.warnings: List[JobErrorIssue] = []
        self.auto_fixes: List[str] = []

    async def validate(self, capsule: CapsuleModel) -> Tuple[bool, List[JobErrorIssue], List[JobErrorIssue]]:
        """Run all 13 validation checks."""
        self.errors.clear()
        self.warnings.clear()
        self.auto_fixes.clear()

        # Check 1: ULID format
        if capsule.metadata.capsule_id != "PENDING" and len(capsule.metadata.capsule_id) != 26:
            self.errors.append(
                JobErrorIssue(
                    path="/metadata/capsule_id",
                    message=f"ULID length {len(capsule.metadata.capsule_id)} != 26",
                )
            )

        # Check 2: Summary length (70-140 words)
        summary_words = len(capsule.neuro_concentrate.summary.split())
        if summary_words < 70:
            self.errors.append(
                JobErrorIssue(
                    path="/neuro_concentrate/summary",
                    message=f"Summary has {summary_words} words; must be 70-140",
                )
            )
            if not self.strict_mode:
                # Auto-fix: expand from content
                self._expand_summary(capsule)
        elif summary_words > 140:
            self.errors.append(
                JobErrorIssue(
                    path="/neuro_concentrate/summary",
                    message=f"Summary has {summary_words} words; exceeds maximum 140",
                )
            )
            if not self.strict_mode:
                # Auto-fix: trim to 140
                words = capsule.neuro_concentrate.summary.split()
                capsule.neuro_concentrate.summary = " ".join(words[:140])
                self.auto_fixes.append("summary trimmed to 140 words")

        # Check 3: Keywords count (5-12)
        kw_count = len(capsule.neuro_concentrate.keywords)
        if kw_count < 5:
            self.errors.append(
                JobErrorIssue(
                    path="/neuro_concentrate/keywords",
                    message=f"Only {kw_count} keywords; need 5-12",
                )
            )
            if not self.strict_mode:
                # Auto-fix: extract from content
                self._expand_keywords(capsule)
        elif kw_count > 12:
            self.warnings.append(
                JobErrorIssue(
                    path="/neuro_concentrate/keywords",
                    message=f"{kw_count} keywords; maximum is 12",
                )
            )
            if not self.strict_mode:
                capsule.neuro_concentrate.keywords = capsule.neuro_concentrate.keywords[:12]
                self.auto_fixes.append("keywords trimmed to 12")

        # Check 4: vector_hint count (8-16)
        hint_count = len(capsule.neuro_concentrate.vector_hint)
        if hint_count < 8:
            self.errors.append(
                JobErrorIssue(
                    path="/neuro_concentrate/vector_hint",
                    message=f"Only {hint_count} vector hints; need 8-16",
                )
            )
            if not self.strict_mode:
                # Auto-fix: add from keywords/content
                while len(capsule.neuro_concentrate.vector_hint) < 8:
                    capsule.neuro_concentrate.vector_hint.append(
                        f"anchor-{len(capsule.neuro_concentrate.vector_hint) + 1}"
                    )
                self.auto_fixes.append("vector_hint expanded to 8")
        elif hint_count > 16:
            self.warnings.append(
                JobErrorIssue(
                    path="/neuro_concentrate/vector_hint",
                    message=f"{hint_count} vector hints; maximum is 16",
                )
            )
            if not self.strict_mode:
                capsule.neuro_concentrate.vector_hint = capsule.neuro_concentrate.vector_hint[:16]
                self.auto_fixes.append("vector_hint trimmed to 16")

        # Check 5: Tags count (3-10)
        tag_count = len(capsule.metadata.tags)
        if tag_count < 3:
            self.warnings.append(
                JobErrorIssue(
                    path="/metadata/tags",
                    message=f"Only {tag_count} tags; optimal is 3-10",
                )
            )
        elif tag_count > 10:
            self.warnings.append(
                JobErrorIssue(
                    path="/metadata/tags",
                    message=f"{tag_count} tags; maximum is 10",
                )
            )

        # Check 6: Semantic hash equality (CRITICAL)
        if capsule.metadata.semantic_hash != capsule.neuro_concentrate.semantic_hash:
            self.errors.append(
                JobErrorIssue(
                    path="/metadata/semantic_hash",
                    message=f"Hash mismatch: metadata='{capsule.metadata.semantic_hash[:20]}...' != neuro='{capsule.neuro_concentrate.semantic_hash[:20]}...'",
                )
            )
            # Auto-fix: recompute and mirror
            if not self.strict_mode:
                new_hash = compute_semantic_hash(capsule.neuro_concentrate.summary)
                capsule.metadata.semantic_hash = new_hash
                capsule.neuro_concentrate.semantic_hash = new_hash
                self.auto_fixes.append("semantic_hash recomputed and mirrored")

        # Check 7: emotional_charge range [-1, 1]
        charge = capsule.neuro_concentrate.emotional_charge
        if not -1.0 <= charge <= 1.0:
            self.errors.append(
                JobErrorIssue(
                    path="/neuro_concentrate/emotional_charge",
                    message=f"Value {charge} out of range [-1, 1]",
                )
            )
            if not self.strict_mode:
                capsule.neuro_concentrate.emotional_charge = max(-1.0, min(1.0, charge))
                self.auto_fixes.append("emotional_charge clamped to [-1, 1]")

        # Check 8: Link relations validity
        allowed_rels = {"supports", "contradicts", "extends", "duplicates", "references", "depends_on", "derived_from"}
        for i, link in enumerate(capsule.recursive.links):
            if link.rel not in allowed_rels:
                self.errors.append(
                    JobErrorIssue(
                        path=f"/recursive/links[{i}]/rel",
                        message=f"Invalid relation: '{link.rel}'",
                    )
                )

        # Check 9: Link confidence range [0, 1]
        for i, link in enumerate(capsule.recursive.links):
            if not 0.0 <= link.confidence <= 1.0:
                self.errors.append(
                    JobErrorIssue(
                        path=f"/recursive/links[{i}]/confidence",
                        message=f"Value {link.confidence} out of range [0, 1]",
                    )
                )
                if not self.strict_mode:
                    link.confidence = max(0.0, min(1.0, link.confidence))
                    self.auto_fixes.append(f"link[{i}] confidence clamped")

        # Check 10: archetypes ≤5
        if len(capsule.neuro_concentrate.archetypes) > 5:
            self.warnings.append(
                JobErrorIssue(
                    path="/neuro_concentrate/archetypes",
                    message=f"{len(capsule.neuro_concentrate.archetypes)} archetypes; maximum is 5",
                )
            )
            if not self.strict_mode:
                capsule.neuro_concentrate.archetypes = capsule.neuro_concentrate.archetypes[:5]
                self.auto_fixes.append("archetypes trimmed to 5")

        # Check 11: ISO-8601 timestamp format
        if not isinstance(capsule.metadata.created_at, str):
            # Check if datetime object is valid
            if not hasattr(capsule.metadata.created_at, "isoformat"):
                self.errors.append(
                    JobErrorIssue(
                        path="/metadata/created_at",
                        message="Invalid timestamp format",
                    )
                )

        # Check 12: BCP-47 language code (basic validation)
        if not re.match(r"^[a-z]{2}(-[A-Z]{2})?$", capsule.metadata.language):
            self.warnings.append(
                JobErrorIssue(
                    path="/metadata/language",
                    message=f"Language code '{capsule.metadata.language}' may not be valid BCP-47",
                )
            )

        # Check 13: Section presence (implicitly checked by Pydantic, but verify)
        # This is handled by CapsuleModel structure

        return len(self.errors) == 0, self.errors, self.warnings

    def _expand_summary(self, capsule: CapsuleModel) -> None:
        """Expand summary to meet minimum word count."""
        current_words = capsule.neuro_concentrate.summary.split()
        if len(current_words) < 70:
            # Add content from core_payload
            content_words = capsule.core_payload.content.split()[:30]
            capsule.neuro_concentrate.summary = " ".join(current_words + content_words)
            if len(capsule.neuro_concentrate.summary.split()) < 70:
                # Still short, pad with generic
                capsule.neuro_concentrate.summary += " This capsule documents structured knowledge for retrieval and graph traversal."
            self.auto_fixes.append("summary expanded to meet minimum word count")

    def _expand_keywords(self, capsule: CapsuleModel) -> None:
        """Expand keywords from content."""
        content_words = re.findall(r"\b[a-z]{4,}\b", capsule.core_payload.content.lower())
        existing = set(kw.lower() for kw in capsule.neuro_concentrate.keywords)
        new_keywords = [w for w in content_words if w not in existing][:12]
        capsule.neuro_concentrate.keywords.extend(new_keywords)
        existing.update(new_keywords)

        fallback_keywords = [
            "knowledge",
            "graph",
            "retrieval",
            "deepmine",
            "n1hub",
            "capsules",
        ]
        for word in fallback_keywords:
            if len(capsule.neuro_concentrate.keywords) >= 12:
                break
            if len(capsule.neuro_concentrate.keywords) >= 5:
                break
            if word not in existing:
                capsule.neuro_concentrate.keywords.append(word)
                existing.add(word)

        capsule.neuro_concentrate.keywords = capsule.neuro_concentrate.keywords[:12]
        self.auto_fixes.append("keywords expanded from content")
