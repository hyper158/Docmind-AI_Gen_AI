import asyncio
import time
from dataclasses import dataclass, field
from typing import List, Optional
from langchain_core.messages import SystemMessage, HumanMessage
from langchain_openai import ChatOpenAI

from app.core.config import settings
from app.core.exceptions import LLMProviderError
from app.core.logging_config import get_logger
from app.services.summarization.page_summarizer import PageSummaryResult
from app.services.summarization.prompt_templates import (
    SECTION_AGGREGATION_SYSTEM_PROMPT,
    SECTION_AGGREGATION_USER_TEMPLATE,
    FINAL_DOCUMENT_SUMMARY_SYSTEM_PROMPT,
    FINAL_DOCUMENT_SUMMARY_USER_TEMPLATE,
)

logger = get_logger(__name__)


@dataclass
class SectionSummary:
    """Summary of a consecutive group of pages."""

    start_page: int
    end_page: int
    summary_text: str
    page_numbers: List[int] = field(default_factory=list)


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
    Performs multi-level Map-Reduce aggregation over page summaries.
    Preserves original page references, formulas, and technical depth.
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
                "X-Title": "DocMind AI - Hierarchical Aggregator",
            },
        )

    async def _invoke_llm(self, messages: list, context_name: str) -> str:
        if self.mock_mode:
            await asyncio.sleep(0.05)
            return (
                f"# Master Summary for {context_name}\n\n"
                "## 1. Executive Document Overview\n"
                "Comprehensive overview of the document synthesized across all verified pages.\n\n"
                "## 2. Main Themes & Structural Breakdown\n"
                "- Core Syllabus Topic A: Comprehensive analysis [Pages 1-3].\n"
                "- Advanced Architecture B: Methodological walkthrough [Pages 4-8].\n\n"
                "## 3. Comprehensive Concept Analysis & Detailed Explanations\n"
                "Detailed walkthrough of algorithms and concepts.\n\n"
                "## 4. Formal Definitions & Technical Terminology Glossary\n"
                "- **Term 1**: Specific technical definition.\n\n"
                "## 5. Methodologies, Processes, & Sequences\n"
                "Step 1: Ingestion. Step 2: Indexing. Step 3: Retrieval.\n\n"
                "## 6. Quantitative Data, Formulas, & Comparative Analyses\n"
                "- Precision: 99.4%, Recall: 92.1%.\n\n"
                "## 7. Core Conclusions & Critical Takeaways\n"
                "Final key conclusions grounded in source pages.\n\n"
                "## 8. Page Citation Matrix\n"
                "- Foundations: Pages 1-3\n- Advanced Systems: Pages 4-8\n"
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
    ) -> HierarchicalSummaryResult:
        """
        Executes tree-structured aggregation over page summaries:
        Level 1: Page summaries -> Group into section summaries (if > batch_size pages)
        Level 2: Section summaries -> Final comprehensive master summary
        """
        start_time = time.perf_counter()
        total_pages = len(page_summaries)

        # Filter out completely empty or failed pages for cleaner synthesis, but keep page numbers
        usable_pages = [p for p in page_summaries if p.status in ("completed", "partial")]
        if not usable_pages:
            # Handle case where all pages had no text or failed
            elapsed = round(time.perf_counter() - start_time, 2)
            msg = (
                f"# Summary for {filename}\n\n"
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

        # If document has more than batch_size pages, perform intermediate section aggregation
        if len(usable_pages) > self.batch_size:
            levels = 2
            chunks_of_pages = [
                usable_pages[i : i + self.batch_size]
                for i in range(0, len(usable_pages), self.batch_size)
            ]

            logger.info(
                f"Aggregating {len(usable_pages)} pages into {len(chunks_of_pages)} sections (batch_size={self.batch_size})."
            )

            async def _summarize_section(batch: List[PageSummaryResult]) -> SectionSummary:
                start_p = batch[0].page_number
                end_p = batch[-1].page_number
                pages_formatted = "\n\n".join(
                    f"--- [Page {p.page_number}] ---\n{p.summary_text}" for p in batch
                )
                prompt = SECTION_AGGREGATION_USER_TEMPLATE.format(
                    filename=filename,
                    start_page=start_p,
                    end_page=end_p,
                    page_summaries=pages_formatted,
                )
                try:
                    summary_text = await self._invoke_llm(
                        [
                            SystemMessage(content=SECTION_AGGREGATION_SYSTEM_PROMPT),
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
                )

            section_tasks = [_summarize_section(b) for b in chunks_of_pages]
            section_summaries = await asyncio.gather(*section_tasks)

            # Assemble content for final master summary from section summaries
            hierarchical_content = "\n\n========================================\n\n".join(
                f"## Section: Pages {s.start_page} to {s.end_page}\n{s.summary_text}"
                for s in section_summaries
            )
        else:
            # Small document: page summaries directly form section summaries
            for p in usable_pages:
                section_summaries.append(
                    SectionSummary(
                        start_page=p.page_number,
                        end_page=p.page_number,
                        summary_text=p.summary_text,
                        page_numbers=[p.page_number],
                    )
                )
            hierarchical_content = "\n\n".join(
                f"--- [Page {p.page_number}] ---\n{p.summary_text}" for p in usable_pages
            )

        # Generate Final Master Document Summary
        logger.info(f"Generating final master document summary for '{filename}'...")
        final_prompt = FINAL_DOCUMENT_SUMMARY_USER_TEMPLATE.format(
            filename=filename,
            total_pages=total_pages,
            hierarchical_content=hierarchical_content,
        )

        try:
            final_summary = await self._invoke_llm(
                [
                    SystemMessage(content=FINAL_DOCUMENT_SUMMARY_SYSTEM_PROMPT),
                    HumanMessage(content=final_prompt),
                ],
                context_name=filename,
            )
            err_msg = None
        except Exception as final_err:
            logger.error(f"Error generating final summary for {filename}: {final_err}")
            final_summary = f"# Document Summary: {filename}\n\n{hierarchical_content}"
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
