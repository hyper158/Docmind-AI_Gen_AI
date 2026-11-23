import asyncio
import time
from dataclasses import dataclass, field
from typing import List, Optional, Callable, Dict, Any
from langchain_core.messages import SystemMessage, HumanMessage
from langchain_openai import ChatOpenAI

from app.core.config import settings
from app.core.exceptions import LLMProviderError
from app.core.logging_config import get_logger
from app.services.pdf_service import ExtractedPage
from app.services.summarization.token_budget import (
    estimate_token_count,
    split_text_into_token_chunks,
)
from app.services.summarization.prompt_templates import (
    PAGE_SUMMARIZATION_SYSTEM_PROMPT,
    PAGE_SUMMARIZATION_USER_TEMPLATE,
    CHUNK_SUMMARIZATION_SYSTEM_PROMPT,
    CHUNK_SUMMARIZATION_USER_TEMPLATE,
    MERGE_PAGE_CHUNKS_USER_TEMPLATE,
)

logger = get_logger(__name__)


@dataclass
class PageSummaryResult:
    """Summary and processing metadata for a single page."""

    page_number: int
    document_id: str
    filename: str
    summary_text: str
    status: str  # "completed" | "empty" | "insufficient_text" | "failed"
    is_chunked: bool = False
    chunk_count: int = 1
    input_characters: int = 0
    estimated_tokens: int = 0
    processing_time_sec: float = 0.0
    error_message: Optional[str] = None
    key_concepts: List[str] = field(default_factory=list)


class PageSummarizer:
    """
    Summarizes individual PDF pages with intelligent chunking for dense/long pages,
    bounded concurrency, and exponential backoff retry handling.
    """

    def __init__(
        self,
        concurrency_limit: int = settings.SUMMARIZATION_CONCURRENCY_LIMIT,
        max_chunk_chars: int = settings.SUMMARIZATION_PAGE_CHUNK_SIZE,
        chunk_overlap: int = settings.SUMMARIZATION_PAGE_CHUNK_OVERLAP,
        max_output_tokens: int = settings.SUMMARIZATION_MAX_OUTPUT_TOKENS,
        max_retries: int = settings.SUMMARIZATION_MAX_RETRIES,
        retry_backoff: float = settings.SUMMARIZATION_RETRY_BACKOFF,
        mock_mode: bool = False,
    ) -> None:
        self.concurrency_limit = max(1, concurrency_limit)
        self.max_chunk_chars = max_chunk_chars
        self.chunk_overlap = chunk_overlap
        self.max_output_tokens = max_output_tokens
        self.max_retries = max_retries
        self.retry_backoff = retry_backoff
        self.mock_mode = mock_mode

    def _get_llm(self, max_tokens: Optional[int] = None) -> ChatOpenAI:
        if not settings.OPENROUTER_API_KEY and not self.mock_mode:
            raise LLMProviderError("OPENROUTER_API_KEY is not configured in backend/.env")

        return ChatOpenAI(
            model=settings.OPENROUTER_MODEL,
            api_key=settings.OPENROUTER_API_KEY or "mock-key",
            base_url=settings.OPENROUTER_BASE_URL,
            temperature=0.1,
            max_tokens=max_tokens or self.max_output_tokens,
            timeout=settings.SUMMARIZATION_TIMEOUT_SECONDS,
            max_retries=0,  # Handled manually with exponential backoff
            default_headers={
                "HTTP-Referer": "https://docmind.ai",
                "X-Title": "DocMind AI - Hierarchical Summarizer",
            },
        )

    async def _invoke_llm_with_retry(
        self,
        messages: list,
        context_name: str,
    ) -> str:
        """Invokes LLM with exponential backoff retries for rate-limiting and timeouts."""
        if self.mock_mode:
            await asyncio.sleep(0.05)
            # Deterministic rich mock summary based on input length
            content = messages[-1].content
            return f"### Summary for {context_name}\n\n- Key Concept 1: Detailed factual point extracted from source.\n- Technical Definition: Formulated specification.\n- Analysis: Structured finding from {context_name}."

        llm = self._get_llm()
        last_error = None

        for attempt in range(1, self.max_retries + 1):
            try:
                response = await asyncio.to_thread(llm.invoke, messages)
                text = (response.content or "").strip()

                if not text:
                    # Check reasoning tokens if present
                    kwargs = getattr(response, "additional_kwargs", {})
                    reasoning = kwargs.get("reasoning_content") or kwargs.get("reasoning")
                    if reasoning:
                        text = str(reasoning).strip()

                if text:
                    return text
                raise LLMProviderError("Received empty response content from LLM provider.")

            except Exception as exc:
                last_error = exc
                wait_time = self.retry_backoff**attempt
                logger.warning(
                    f"LLM call for {context_name} failed (attempt {attempt}/{self.max_retries}): {exc}. Retrying in {wait_time:.1f}s..."
                )
                if attempt < self.max_retries:
                    await asyncio.sleep(wait_time)

        raise LLMProviderError(
            f"Failed to summarize {context_name} after {self.max_retries} attempts: {last_error}"
        )

    async def summarize_page(
        self,
        page: ExtractedPage,
    ) -> PageSummaryResult:
        """
        Summarizes an individual page. If the page is dense (> max_chunk_chars),
        splits into chunks, summarizes each, and merges them.
        """
        start_time = time.perf_counter()
        raw_text = page.page_text.strip()
        char_count = len(raw_text)

        # 1. Handle empty or near-empty pages without wasting LLM tokens
        if not raw_text or page.is_empty:
            return PageSummaryResult(
                page_number=page.page_number,
                document_id=page.document_id,
                filename=page.filename,
                summary_text=f"*Page {page.page_number}: Empty page with no extractable text.*",
                status="empty",
                input_characters=0,
                estimated_tokens=0,
                processing_time_sec=0.001,
            )

        if char_count < 30 or page.is_insufficient_text:
            return PageSummaryResult(
                page_number=page.page_number,
                document_id=page.document_id,
                filename=page.filename,
                summary_text=f"*Page {page.page_number}: Insufficient text content ({char_count} chars). Content: \"{raw_text}\"*",
                status="insufficient_text",
                input_characters=char_count,
                estimated_tokens=estimate_token_count(raw_text),
                processing_time_sec=0.001,
            )

        # 2. Check if page exceeds budget and needs sub-chunking
        if char_count > self.max_chunk_chars:
            chunks = split_text_into_token_chunks(
                raw_text,
                max_chunk_chars=self.max_chunk_chars,
                overlap_chars=self.chunk_overlap,
            )
            logger.info(
                f"Page {page.page_number} ({char_count} chars) exceeds chunk limit; split into {len(chunks)} chunks."
            )

            chunk_summaries = []
            for idx, chunk_text in enumerate(chunks, start=1):
                chunk_prompt = CHUNK_SUMMARIZATION_USER_TEMPLATE.format(
                    filename=page.filename,
                    page_number=page.page_number,
                    chunk_index=idx,
                    total_chunks=len(chunks),
                    chunk_text=chunk_text,
                )
                try:
                    c_sum = await self._invoke_llm_with_retry(
                        [
                            SystemMessage(content=CHUNK_SUMMARIZATION_SYSTEM_PROMPT),
                            HumanMessage(content=chunk_prompt),
                        ],
                        context_name=f"Page {page.page_number} (Chunk {idx}/{len(chunks)})",
                    )
                    chunk_summaries.append(f"### Section {idx} Summary:\n{c_sum}")
                except Exception as chunk_err:
                    logger.error(
                        f"Failed summarizing chunk {idx} of page {page.page_number}: {chunk_err}"
                    )
                    chunk_summaries.append(
                        f"### Section {idx}: [Summary unavailable due to processing error: {chunk_err}]"
                    )

            # Merge chunk summaries into single page summary
            merge_prompt = MERGE_PAGE_CHUNKS_USER_TEMPLATE.format(
                filename=page.filename,
                page_number=page.page_number,
                chunk_summaries="\n\n".join(chunk_summaries),
            )
            try:
                page_final_summary = await self._invoke_llm_with_retry(
                    [
                        SystemMessage(content=PAGE_SUMMARIZATION_SYSTEM_PROMPT),
                        HumanMessage(content=merge_prompt),
                    ],
                    context_name=f"Page {page.page_number} Merged Chunks",
                )
                status = "completed"
                err_msg = None
            except Exception as merge_err:
                logger.error(f"Failed merging chunks for page {page.page_number}: {merge_err}")
                page_final_summary = "\n\n".join(chunk_summaries)
                status = "partial"
                err_msg = str(merge_err)

            elapsed = round(time.perf_counter() - start_time, 2)
            return PageSummaryResult(
                page_number=page.page_number,
                document_id=page.document_id,
                filename=page.filename,
                summary_text=page_final_summary,
                status=status,
                is_chunked=True,
                chunk_count=len(chunks),
                input_characters=char_count,
                estimated_tokens=estimate_token_count(raw_text),
                processing_time_sec=elapsed,
                error_message=err_msg,
            )

        # 3. Standard single-page summarization (fits within budget)
        page_prompt = PAGE_SUMMARIZATION_USER_TEMPLATE.format(
            filename=page.filename,
            page_number=page.page_number,
            page_text=raw_text,
        )

        try:
            summary = await self._invoke_llm_with_retry(
                [
                    SystemMessage(content=PAGE_SUMMARIZATION_SYSTEM_PROMPT),
                    HumanMessage(content=page_prompt),
                ],
                context_name=f"Page {page.page_number}",
            )
            status = "completed"
            err_msg = None
        except Exception as exc:
            logger.error(f"Failed summarizing page {page.page_number}: {exc}")
            summary = f"*Page {page.page_number}: Summarization failed - {exc}*"
            status = "failed"
            err_msg = str(exc)

        elapsed = round(time.perf_counter() - start_time, 2)
        return PageSummaryResult(
            page_number=page.page_number,
            document_id=page.document_id,
            filename=page.filename,
            summary_text=summary,
            status=status,
            is_chunked=False,
            chunk_count=1,
            input_characters=char_count,
            estimated_tokens=estimate_token_count(raw_text),
            processing_time_sec=elapsed,
            error_message=err_msg,
        )

    async def summarize_all_pages(
        self,
        pages: List[ExtractedPage],
        progress_callback: Optional[Callable[[int, int, PageSummaryResult], None]] = None,
    ) -> List[PageSummaryResult]:
        """
        Processes all pages concurrently under a bounded semaphore to prevent API rate limits.
        Maintains strictly sorted original page order.
        """
        semaphore = asyncio.Semaphore(self.concurrency_limit)
        results: Dict[int, PageSummaryResult] = {}
        total = len(pages)

        async def _worker(p: ExtractedPage):
            async with semaphore:
                res = await self.summarize_page(p)
                results[p.page_number] = res
                if progress_callback:
                    try:
                        progress_callback(len(results), total, res)
                    except Exception as cb_err:
                        logger.warning(f"Error in progress callback: {cb_err}")

        tasks = [_worker(p) for p in pages]
        await asyncio.gather(*tasks)

        # Return strictly in original page order (1, 2, 3...)
        sorted_results = [results[p.page_number] for p in pages]
        logger.info(
            f"Completed summarization of {len(sorted_results)} pages (concurrency={self.concurrency_limit})."
        )
        return sorted_results
