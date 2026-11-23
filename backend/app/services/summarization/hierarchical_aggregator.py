import asyncio
import time
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any
from langchain_core.messages import SystemMessage, HumanMessage
from langchain_openai import ChatOpenAI

from app.core.config import settings
from app.core.exceptions import LLMProviderError
from app.core.logging_config import get_logger
from app.services.summarization.page_summarizer import PageSummaryResult
from app.services.summarization.document_analyzer import DocumentStructure, TopicNode
from app.services.summarization.prompt_templates import (
    TOPIC_CONSOLIDATION_SYSTEM_PROMPT,
    TOPIC_CONSOLIDATION_USER_TEMPLATE,
    COMPREHENSIVE_STUDY_NOTES_SYSTEM_PROMPT,
    COMPREHENSIVE_STUDY_NOTES_USER_TEMPLATE,
)

logger = get_logger(__name__)


@dataclass
class SectionSummary:
    """Summary of a consecutive group of pages or a dedicated topic module."""

    start_page: int
    end_page: int
    summary_text: str
    page_numbers: List[int] = field(default_factory=list)
    topic_title: str = "Topic"


@dataclass
class HierarchicalSummaryResult:
    """Final output of the hierarchical aggregation process."""

    document_id: str
    filename: str
    final_summary: str
    section_summaries: List[SectionSummary]
    total_pages: int
    aggregation_levels: int
    duration_sec: float
    error_message: Optional[str] = None


class HierarchicalAggregator:
    """
    Performs multi-level Map-Reduce aggregation over page summaries to produce
    comprehensive educational study notes organized topic-by-topic.
    Preserves original page references, formulas, comparisons, and technical depth.
    Strict text-only output guaranteed.
    """

    def __init__(
        self,
        batch_size: int = 5,
        max_output_tokens: int = settings.SUMMARIZATION_MAX_OUTPUT_TOKENS,
        mock_mode: bool = False,
    ) -> None:
        self.batch_size = max(2, batch_size)
        self.max_output_tokens = max_output_tokens
        self.mock_mode = mock_mode

    def _get_llm(self) -> ChatOpenAI:
        return ChatOpenAI(
            model=settings.OPENROUTER_MODEL,
            api_key=settings.OPENROUTER_API_KEY or "mock-key",
            base_url=settings.OPENROUTER_BASE_URL,
            temperature=0.1,
            max_tokens=self.max_output_tokens,
            timeout=settings.SUMMARIZATION_TIMEOUT_SECONDS * 2,
            max_retries=2,
            default_headers={
                "HTTP-Referer": "https://docmind.ai",
                "X-Title": "DocMind AI - Educational Notes Synthesizer",
            },
        )

    async def _invoke_llm(self, messages: list, context_name: str) -> str:
        if self.mock_mode:
            await asyncio.sleep(0.05)
            return (
                f"# Comprehensive Study Notes: {context_name}\n\n"
                "## 1. Executive Overview & Learning Objectives\n"
                "This document provides an in-depth academic exploration of core principles, methodologies, "
                "and architectural frameworks. The overarching purpose of this course material is to equip students "
                "with theoretical foundations and practical applications across all syllabus modules.\n\n"
                "## 2. Dynamic Topic-by-Topic Comprehensive Teaching & Notes\n\n"
                "### Topic 1: Foundational Architecture & Core Mechanics ([Pages 1-2])\n"
                "- **Core Concept & Definition**: **System Architecture** refers to the conceptual model that defines "
                "the structure, behavior, and more views of a distributed computational system.\n"
                "- **How It Works & Underlying Mechanism**: Incoming data payloads are partitioned and ingested into pipeline stages. "
                "Each stage executes transformations in isolated memory buffers before writing to persistent storage.\n"
                "- **Key Components & Terminology**: **Ingestion Gateway**, **Processing Pipeline**, **State Storage**.\n"
                "- **Step-by-Step Process / Methodology**:\n"
                "  1. Ingestion of raw payloads from client nodes.\n"
                "  2. Validation against schema specifications.\n"
                "  3. Transformation and feature normalization.\n"
                "  4. Commit to immutable ledger or index.\n"
                "- **Comparison & Trade-offs**:\n\n"
                "| Feature | Pipeline Processing | Batch Processing |\n"
                "| :--- | :--- | :--- |\n"
                "| Latency | Sub-second real-time | Periodic batch delay |\n"
                "| Resource Utilization | Continuous baseline | Burst-oriented spikes |\n"
                "| Fault Tolerance | Stream checkpoints | Complete job restart |\n\n"
                "- **Examples**: (Source Example: An e-commerce platform processing transaction records) "
                "(Pedagogical Example: Like a fast-food assembly line where each station specializes in one preparation task).\n"
                "- **Advantages & Limitations**: High throughput and immediate consistency, but requires continuous stream monitoring.\n\n"
                "### Topic 2: Optimization Strategies & Algorithmic Models ([Pages 3-5])\n"
                "- **Core Concept & Definition**: **Algorithmic Optimization** minimizes computational overhead while maximizing precision.\n"
                "- **Formulas & Quantitative Metrics**: Efficiency gain equation: $E = \\frac{T_{baseline} - T_{optimized}}{T_{baseline}} \\times 100\\%$.\n"
                "- **How It Works**: Iterative refinement with gradient descent converges toward global minima.\n\n"
                "## 3. Technical Terminology & Formal Definitions Glossary\n"
                "- **Ingestion Gateway**: Hardware or software boundary receiving inbound signals [Page 1].\n"
                "- **Pipeline Checkpoint**: State snapshot allowing deterministic resume upon node failure [Page 2].\n"
                "- **Convergence Rate**: Speed at which optimization algorithms approach optimal parameters [Page 4].\n\n"
                "## 4. Key Formulas, Methodologies & Quantitative Rules\n"
                "- **Efficiency Ratio**: $E = \\frac{\\Delta T}{T_0} \\times 100\\%$\n"
                "- **Threshold Constraint**: Convergence criterion $\\epsilon \\le 10^{-4}$\n\n"
                "## 5. Comprehensive Summary & Master Page Citation Matrix\n\n"
                "| Module / Topic | Core Concepts | Supporting Pages |\n"
                "| :--- | :--- | :--- |\n"
                "| Foundational Architecture | Ingestion, Buffering, Pipelines | Pages 1-2 |\n"
                "| Optimization Models | Convergence, Gradient Descent, Benchmarking | Pages 3-5 |\n"
            )

        llm = self._get_llm()
        response = await asyncio.to_thread(llm.invoke, messages)
        content = (response.content or "").strip()

        if not content:
            kwargs = getattr(response, "additional_kwargs", {})
            reasoning = kwargs.get("reasoning_content") or kwargs.get("reasoning")
            if reasoning:
                content = str(reasoning).strip()

        if not content:
            raise LLMProviderError(f"Empty response during {context_name}")
        return content

    async def aggregate(
        self,
        document_id: str,
        filename: str,
        page_summaries: List[PageSummaryResult],
        structure: Optional[DocumentStructure] = None,
    ) -> HierarchicalSummaryResult:
        """
        Executes tree-structured aggregation over page summaries:
        Level 1: Page summaries -> Group into section/topic summaries
        Level 2: Topic summaries -> Final comprehensive master educational notes
        """
        start_time = time.perf_counter()
        total_pages = len(page_summaries)

        usable_pages = [p for p in page_summaries if p.status in ("completed", "partial")]
        if not usable_pages:
            elapsed = round(time.perf_counter() - start_time, 2)
            msg = (
                f"# Educational Notes for {filename}\n\n"
                f"No extractable text was found across {total_pages} pages. "
                "The PDF may be password-protected, encrypted, or contain only scanned images."
            )
            return HierarchicalSummaryResult(
                document_id=document_id,
                filename=filename,
                final_summary=msg,
                section_summaries=[],
                total_pages=total_pages,
                aggregation_levels=0,
                duration_sec=elapsed,
            )

        section_summaries: List[SectionSummary] = []
        levels = 1

        # Build structure outline string for the LLM
        structure_outline = ""
        if structure and structure.topics:
            outline_lines = [f"Document: {structure.detected_title} ({structure.total_pages} pages)"]
            if structure.detected_units:
                outline_lines.append(f"Units/Chapters detected: {', '.join(structure.detected_units)}")
            outline_lines.append("Topic Outline:")
            for t in structure.topics:
                outline_lines.append(f"- {t.title} (Pages {', '.join(map(str, t.page_numbers))})")
                if t.key_terms:
                    outline_lines.append(f"  Key Terms: {', '.join(t.key_terms[:5])}")
            structure_outline = "\n".join(outline_lines)
        else:
            structure_outline = f"Standard sequential breakdown across {total_pages} pages."

        # Topic/Section Aggregation
        if len(usable_pages) > self.batch_size:
            levels = 2
            chunks_of_pages = [
                usable_pages[i : i + self.batch_size]
                for i in range(0, len(usable_pages), self.batch_size)
            ]

            logger.info(
                f"Aggregating {len(usable_pages)} pages into {len(chunks_of_pages)} topic sections (batch_size={self.batch_size})."
            )

            async def _summarize_section(batch: List[PageSummaryResult], batch_idx: int) -> SectionSummary:
                start_p = batch[0].page_number
                end_p = batch[-1].page_number
                topic_title = f"Section {batch_idx + 1}"
                if structure and batch_idx < len(structure.topics):
                    topic_title = structure.topics[batch_idx].title

                pages_formatted = "\n\n".join(
                    f"--- [Page {p.page_number}] ---\n{p.summary_text}" for p in batch
                )
                prompt = TOPIC_CONSOLIDATION_USER_TEMPLATE.format(
                    filename=filename,
                    topic_title=topic_title,
                    start_page=start_p,
                    end_page=end_p,
                    page_summaries=pages_formatted,
                )
                try:
                    summary_text = await self._invoke_llm(
                        [
                            SystemMessage(content=TOPIC_CONSOLIDATION_SYSTEM_PROMPT),
                            HumanMessage(content=prompt),
                        ],
                        context_name=f"Pages {start_p}-{end_p}",
                    )
                except Exception as sec_err:
                    logger.error(f"Error in section {start_p}-{end_p}: {sec_err}")
                    summary_text = pages_formatted

                return SectionSummary(
                    start_page=start_p,
                    end_page=end_p,
                    summary_text=summary_text,
                    page_numbers=[p.page_number for p in batch],
                    topic_title=topic_title,
                )

            section_tasks = [_summarize_section(b, idx) for idx, b in enumerate(chunks_of_pages)]
            section_summaries = await asyncio.gather(*section_tasks)

            hierarchical_content = "\n\n========================================\n\n".join(
                f"## Topic Module: {s.topic_title} (Pages {s.start_page} to {s.end_page})\n{s.summary_text}"
                for s in section_summaries
            )
        else:
            for p in usable_pages:
                section_summaries.append(
                    SectionSummary(
                        start_page=p.page_number,
                        end_page=p.page_number,
                        summary_text=p.summary_text,
                        page_numbers=[p.page_number],
                        topic_title=f"Page {p.page_number}",
                    )
                )
            hierarchical_content = "\n\n".join(
                f"--- [Page {p.page_number}] ---\n{p.summary_text}" for p in usable_pages
            )

        # Generate Master Educational Study Notes
        logger.info(f"Generating comprehensive educational study notes for '{filename}'...")
        final_prompt = COMPREHENSIVE_STUDY_NOTES_USER_TEMPLATE.format(
            filename=filename,
            total_pages=total_pages,
            structure_outline=structure_outline,
            hierarchical_content=hierarchical_content,
        )

        try:
            final_summary = await self._invoke_llm(
                [
                    SystemMessage(content=COMPREHENSIVE_STUDY_NOTES_SYSTEM_PROMPT),
                    HumanMessage(content=final_prompt),
                ],
                context_name=filename,
            )
            err_msg = None
        except Exception as final_err:
            logger.error(f"Error generating final study notes for {filename}: {final_err}")
            final_summary = f"# Comprehensive Study Notes: {filename}\n\n{hierarchical_content}"
            err_msg = str(final_err)

        elapsed = round(time.perf_counter() - start_time, 2)
        return HierarchicalSummaryResult(
            document_id=document_id,
            filename=filename,
            final_summary=final_summary,
            section_summaries=section_summaries,
            total_pages=total_pages,
            aggregation_levels=levels,
            duration_sec=elapsed,
            error_message=err_msg,
        )
