"""Dynamic document structure and topic detection service for DocMind AI.

Analyzes extracted PDF pages dynamically without ANY hardcoded subject knowledge,
identifying document titles, units/chapters (if present), logical topic progressions,
subtopics, key terminology, and page ranges.
"""

import re
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
from app.services.pdf_service import ExtractedPage
from app.core.logging_config import get_logger

logger = get_logger(__name__)


@dataclass
class TopicNode:
    """Represents a dynamically detected topic or section within the document."""

    topic_id: str
    title: str
    subtopics: List[str] = field(default_factory=list)
    page_numbers: List[int] = field(default_factory=list)
    key_terms: List[str] = field(default_factory=list)
    summary_hint: str = ""
    has_formulas: bool = False
    has_processes: bool = False
    has_comparisons: bool = False


@dataclass
class DocumentStructure:
    """Structured intermediate representation of the document's logical organization."""

    document_id: str
    detected_title: str
    total_pages: int
    has_formal_chapters: bool
    topics: List[TopicNode]
    detected_units: List[str] = field(default_factory=list)
    glossary_terms: List[str] = field(default_factory=list)


class DocumentAnalyzer:
    """
    Analyzes document text across all pages dynamically.
    Detects document hierarchy, headings, subheadings, topic boundaries,
    and technical artifacts (formulas, comparisons, steps) without hardcoded schemas.
    """

    # Common structural heading patterns (agnostic to domain)
    HEADING_PATTERNS = [
        # Chapter 1 / Unit 1 / Module 1 / Section 1 / Part 1
        r"^(?:chapter|unit|module|section|part|lecture)\s+([0-9ivxlcdm]+)[:.\s\-–—]+(.+)$",
        # 1.0 Title or 1.1 Subtitle or 1. Introduction
        r"^(\d+(?:\.\d+)*)\s*[:.\-–—]\s*(.+)$",
        # ALL CAPS headings (at least 3 words, not an entire page)
        r"^([A-Z0-9\s,\-:]{6,80})$",
    ]

    # Process indicators (agnostic)
    PROCESS_PATTERNS = [
        r"\b(?:step\s+\d+|phase\s+\d+|stage\s+\d+|workflow|pipeline|procedure|lifecycle|algorithm)\b",
        r"\b(?:first|second|third|then|subsequently|finally)\b",
    ]

    # Comparison indicators (agnostic)
    COMPARISON_PATTERNS = [
        r"\b(?:versus|vs\.?|difference\s+between|comparison|contrast|advantages\s+and\s+disadvantages|pros\s+and\s+cons)\b",
        r"\b(?:trade-offs?|differ\s+from|compared\s+to|distinction)\b",
    ]

    # Formula/Math indicators (agnostic)
    FORMULA_PATTERNS = [
        r"[=∑∫√±×÷≠≤≥≈∝∈∉⊂⊆∪∩]",
        r"\b(?:equation|formula|theorem|algorithm|variance|probability|function\s+f\(|matrix)\b",
        r"\b[A-Za-z]\s*=\s*[^,\n]{3,}",
    ]

    @classmethod
    def analyze_document(
        cls,
        document_id: str,
        filename: str,
        pages: List[ExtractedPage],
    ) -> DocumentStructure:
        """
        Dynamically extracts structure, headings, topics, and technical facets from all pages.
        Works universally for syllabi, research papers, technical guides, textbooks, and notes.
        """
        if not pages:
            return DocumentStructure(
                document_id=document_id,
                detected_title=filename,
                total_pages=0,
                has_formal_chapters=False,
                topics=[],
            )

        # 1. Detect Document Title from first page or filename
        detected_title = cls._detect_title(pages[0].page_text, filename)

        # 2. Extract Headings and Structural Anchors across all pages
        detected_headings: List[Dict[str, Any]] = []
        has_formal_chapters = False
        detected_units = []

        for p in pages:
            lines = [line.strip() for line in p.page_text.split("\n") if line.strip()]
            for line in lines[:10]:  # Inspect top lines of each page
                # Check for formal chapter/unit headers
                for pat in cls.HEADING_PATTERNS:
                    match = re.match(pat, line, re.IGNORECASE)
                    if match:
                        heading_text = line
                        if "chapter" in line.lower() or "unit" in line.lower() or "module" in line.lower():
                            has_formal_chapters = True
                            if line not in detected_units:
                                detected_units.append(line)
                        detected_headings.append({
                            "page": p.page_number,
                            "heading": heading_text,
                            "level": 1 if ("chapter" in line.lower() or "unit" in line.lower() or not re.match(r"^\d+\.\d+", line)) else 2,
                        })
                        break

        # 3. Dynamic Topic Segmentation
        topics: List[TopicNode] = []
        all_glossary_terms: List[str] = []

        if detected_headings and len(detected_headings) >= 2:
            # Segment by detected headings
            for idx, h in enumerate(detected_headings):
                start_p = h["page"]
                end_p = (
                    detected_headings[idx + 1]["page"]
                    if idx + 1 < len(detected_headings)
                    else pages[-1].page_number
                )
                topic_pages = [
                    p.page_number
                    for p in pages
                    if start_p <= p.page_number <= max(start_p, end_p)
                ]
                if not topic_pages:
                    topic_pages = [start_p]

                topic_text = " ".join(
                    p.page_text for p in pages if p.page_number in topic_pages
                )
                key_terms = cls._extract_key_terms(topic_text)
                all_glossary_terms.extend(key_terms[:5])

                node = TopicNode(
                    topic_id=f"topic_{idx + 1}",
                    title=cls._clean_heading(h["heading"]),
                    page_numbers=sorted(list(set(topic_pages))),
                    key_terms=key_terms[:8],
                    has_formulas=cls._check_pattern(topic_text, cls.FORMULA_PATTERNS),
                    has_processes=cls._check_pattern(topic_text, cls.PROCESS_PATTERNS),
                    has_comparisons=cls._check_pattern(topic_text, cls.COMPARISON_PATTERNS),
                )
                topics.append(node)
        else:
            # Fallback: Natural page-clustering for documents without clear heading tags
            # Cluster pages in natural logical groups (e.g., 3-5 pages per topic)
            cluster_size = 3 if len(pages) <= 12 else (5 if len(pages) <= 30 else 8)
            for i in range(0, len(pages), cluster_size):
                cluster_pages = pages[i : i + cluster_size]
                page_nums = [p.page_number for p in cluster_pages]
                cluster_text = " ".join(p.page_text for p in cluster_pages)
                key_terms = cls._extract_key_terms(cluster_text)
                all_glossary_terms.extend(key_terms[:5])

                # Synthesize a descriptive title from the first substantive line or top key terms
                sample_heading = cls._derive_cluster_title(cluster_pages, key_terms, i // cluster_size + 1)

                node = TopicNode(
                    topic_id=f"topic_{i // cluster_size + 1}",
                    title=sample_heading,
                    page_numbers=page_nums,
                    key_terms=key_terms[:8],
                    has_formulas=cls._check_pattern(cluster_text, cls.FORMULA_PATTERNS),
                    has_processes=cls._check_pattern(cluster_text, cls.PROCESS_PATTERNS),
                    has_comparisons=cls._check_pattern(cluster_text, cls.COMPARISON_PATTERNS),
                )
                topics.append(node)

        # De-duplicate glossary terms
        seen = set()
        unique_glossary = []
        for t in all_glossary_terms:
            t_clean = t.strip().title()
            if t_clean.lower() not in seen and len(t_clean) > 2:
                seen.add(t_clean.lower())
                unique_glossary.append(t_clean)

        return DocumentStructure(
            document_id=document_id,
            detected_title=detected_title,
            total_pages=len(pages),
            has_formal_chapters=has_formal_chapters,
            topics=topics,
            detected_units=detected_units,
            glossary_terms=unique_glossary[:30],
        )

    @staticmethod
    def _detect_title(first_page_text: str, fallback_filename: str) -> str:
        """Derives title from the first non-empty lines of page 1 or uses the filename."""
        lines = [line.strip() for line in first_page_text.split("\n") if line.strip()]
        for line in lines[:5]:
            # Look for a clean line of 10 to 80 chars that looks like a title
            if 10 <= len(line) <= 80 and not line.lower().startswith("page ") and not line.isdigit():
                return line
        clean_name = re.sub(r"\.pdf$", "", fallback_filename, flags=re.IGNORECASE)
        clean_name = clean_name.replace("_", " ").replace("-", " ")
        return clean_name.title()

    @staticmethod
    def _clean_heading(heading: str) -> str:
        """Cleans formatting artifacts from detected headings."""
        h = re.sub(r"^[#*\s\-–—]+", "", heading).strip()
        h = re.sub(r"[:\s\-–—]+$", "", h).strip()
        return h if h else "Topic Overview"

    @classmethod
    def _derive_cluster_title(
        cls,
        pages: List[ExtractedPage],
        key_terms: List[str],
        cluster_index: int,
    ) -> str:
        """Derives a meaningful topic title for a group of pages without explicit headings."""
        for p in pages:
            lines = [l.strip() for l in p.page_text.split("\n") if l.strip()]
            for line in lines[:4]:
                if 8 <= len(line) <= 60 and not line.isdigit() and not line.startswith("http"):
                    return cls._clean_heading(line)
        if key_terms:
            terms_label = " & ".join(t.title() for t in key_terms[:2])
            return f"Topic {cluster_index}: {terms_label}"
        p_start = pages[0].page_number
        p_end = pages[-1].page_number
        return f"Section {cluster_index} (Pages {p_start}–{p_end})"

    @staticmethod
    def _extract_key_terms(text: str) -> List[str]:
        """Extracts prominent capitalized technical terms, acronyms, and keywords."""
        terms: List[str] = []
        # Acronyms (e.g. ETL, RAG, CNN, API, SQL)
        acronyms = re.findall(r"\b[A-Z]{2,6}\b", text)
        for acr in acronyms:
            if acr not in ("THE", "AND", "FOR", "NOT", "ARE", "ALL", "NEW", "SET", "BUT", "CAN") and acr not in terms:
                terms.append(acr)

        # Capitalized multi-word technical concepts (e.g., "Data Integration", "Gradient Descent")
        multi_words = re.findall(r"\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+){1,2}\b", text)
        for mw in multi_words:
            if mw not in terms and len(mw) > 4:
                terms.append(mw)

        return terms

    @staticmethod
    def _check_pattern(text: str, patterns: List[str]) -> bool:
        """Returns True if any pattern matches the text."""
        for pat in patterns:
            if re.search(pat, text, re.IGNORECASE):
                return True
        return False
