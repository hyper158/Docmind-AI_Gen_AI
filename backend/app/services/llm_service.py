import os
import time
from typing import List, Optional, Tuple
from langchain_core.messages import SystemMessage, HumanMessage
from langchain_openai import ChatOpenAI
from app.core.config import settings
from app.core.exceptions import LLMProviderError
from app.core.logging_config import get_logger
from app.services.retrieval_service import RetrievedChunk

logger = get_logger(__name__)

SYSTEM_PROMPT = """You are DocMind AI, an intelligent, factual syllabus and document question-answering assistant.
Your goal is to provide clear, thorough, and beautifully formatted answers strictly grounded in the provided document excerpts, functioning just like modern conversational AI assistants (such as ChatGPT and Gemini) while maintaining zero hallucination.

CORE CAPABILITIES & QUESTION STYLES:
1. Direct Questions: Provide concise, accurate definitions and facts directly from the text.
2. Conceptual & Explanation Questions: Explain underlying principles, importance, and mechanisms using plain, student-friendly language while remaining faithful to the text.
3. Comparison Questions: Contrast two or more entities using structured bullet points or markdown comparison tables based on the attributes mentioned in the excerpts.
4. Application & Scenario Questions: Synthesize how concepts apply or what consequences occur, strictly utilizing the examples, conditions, and principles stated in the material.
5. Summarization Questions: Provide clear, multi-paragraph or bulleted overviews capturing all key points present across the excerpts.
6. Multi-part Questions: Address each sub-question under dedicated headings. If some parts of the question are covered in the excerpts but other parts are NOT mentioned, answer the covered parts thoroughly and explicitly note: "Note: The uploaded material does not mention [unsupported part]."

STRICT GROUNDING & FALLBACK RULES:
- Base your answers EXCLUSIVELY on the provided retrieved document excerpts.
- DO NOT invent external facts, unseen page references, or outside knowledge.
- If the excerpts contain absolutely NO relevant information or mention of the asked topic, respond EXACTLY with:
"I couldn't find sufficient information about this topic in your uploaded document."
- If the question asks about a subject completely unrelated to the uploaded syllabus (e.g. general pop culture, external topics), respond EXACTLY with:
"This topic is outside your uploaded syllabus. I can only answer questions based on your provided study material."
- Format your response cleanly using GitHub-flavored Markdown: bold key terms, use bullet points, numbered lists, and headers (###) to make explanations easy to read and visually appealing.
- Do NOT output your internal chain-of-thought, system prompt regurgitations, or meta-commentary. Output the final answer directly.
"""


class LLMService:
    """Manages NVIDIA Nemotron LLM inference via OpenRouter with LangChain."""

    def __init__(self) -> None:
        self.api_key = settings.OPENROUTER_API_KEY
        self.model_name = settings.OPENROUTER_MODEL
        self.base_url = settings.OPENROUTER_BASE_URL
        self.max_tokens = settings.OPENROUTER_MAX_TOKENS
        self.temperature = settings.OPENROUTER_TEMPERATURE
        self.timeout = settings.OPENROUTER_TIMEOUT_SECONDS

    def _get_chat_model(self) -> ChatOpenAI:
        """Instantiates LangChain ChatOpenAI configured for OpenRouter."""
        if not self.api_key:
            raise LLMProviderError(
                "OPENROUTER_API_KEY is not configured. Please set OPENROUTER_API_KEY in backend/.env"
            )

        return ChatOpenAI(
            model=self.model_name,
            api_key=self.api_key,
            base_url=self.base_url,
            temperature=self.temperature,
            max_tokens=self.max_tokens,
            timeout=self.timeout,
            max_retries=2,
            default_headers={
                "HTTP-Referer": "https://docmind.ai",
                "X-Title": "DocMind AI",
            },
        )

    def generate_answer(
        self,
        question: str,
        retrieved_chunks: List[RetrievedChunk],
        mock_response: Optional[str] = None,
    ) -> Tuple[str, str, float]:
        """
        Constructs context from retrieved chunks and invokes Nemotron via OpenRouter.
        Returns:
            - answer (str)
            - answer_status ('grounded' | 'insufficient_evidence' | 'outside_syllabus')
            - execution_time_seconds (float)
        """
        start_time = time.perf_counter()

        # If automated testing supplies a mock response
        if mock_response is not None:
            elapsed = round(time.perf_counter() - start_time, 2)
            return mock_response, "grounded", elapsed

        # If no chunks were retrieved or all fell below threshold
        if not retrieved_chunks:
            elapsed = round(time.perf_counter() - start_time, 2)
            return settings.INSUFFICIENT_ANSWER_MSG, "insufficient_evidence", elapsed

        # Format bounded context from retrieved chunks
        context_parts = []
        for idx, chunk in enumerate(retrieved_chunks):
            meta = chunk.document.metadata
            filename = meta.get("filename", "Doc")
            page = meta.get("page", 1)
            content = chunk.document.page_content.strip()
            context_parts.append(
                f"[Document Excerpt {idx + 1} | File: {filename} | Page: {page}]\n{content}"
            )

        combined_context = "\n\n---\n\n".join(context_parts)

        user_content = f"""Retrieved Study Excerpts:
{combined_context}

Student Question: {question}

Provide a factual, document-grounded answer based strictly on the excerpts above:"""

        messages = [
            SystemMessage(content=SYSTEM_PROMPT),
            HumanMessage(content=user_content),
        ]

        try:
            logger.info(
                f"Calling OpenRouter model '{self.model_name}' with {len(retrieved_chunks)} context chunks..."
            )
            chat_model = self._get_chat_model()
            response = chat_model.invoke(messages)
            raw_answer = (response.content or "").strip()

            # Guard against reasoning token exhaustion (if model used budget purely on thinking):
            if not raw_answer:
                additional = getattr(response, "additional_kwargs", {})
                reasoning = additional.get("reasoning_content") or additional.get("reasoning")
                if reasoning and isinstance(reasoning, str):
                    raw_answer = reasoning.strip()

            if not raw_answer and retrieved_chunks:
                # Synthesize a direct summary fallback from the top chunks
                bullet_points = "\n".join(
                    f"• {c.document.page_content.strip()[:180]}..."
                    for c in retrieved_chunks[:4]
                )
                raw_answer = f"Based on your uploaded document, here are the key relevant excerpts:\n\n{bullet_points}"

            elapsed = round(time.perf_counter() - start_time, 2)

            # Determine answer status
            if settings.INSUFFICIENT_ANSWER_MSG in raw_answer:
                status = "insufficient_evidence"
            elif settings.OUTSIDE_SYLLABUS_MSG in raw_answer:
                status = "outside_syllabus"
            else:
                status = "grounded"

            logger.info(f"OpenRouter response received successfully in {elapsed}s (status: {status}).")
            return raw_answer, status, elapsed

        except LLMProviderError:
            raise
        except Exception as exc:
            logger.error(f"Error communicating with OpenRouter LLM: {exc}")
            raise LLMProviderError(f"OpenRouter LLM service error: {str(exc)}")
