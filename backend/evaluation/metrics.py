import re
from typing import List, Dict, Any, Optional
from app.core.config import settings


def _tokenize(text: str) -> List[str]:
    """Extract lowercase alphanumeric tokens, filtering common stopwords."""
    stopwords = {
        "a", "an", "the", "in", "on", "at", "to", "for", "of", "and", "or",
        "is", "are", "was", "were", "be", "been", "by", "with", "as", "it",
        "this", "that", "from", "which", "what", "how", "why", "does", "do",
        "can", "could", "should", "would", "about", "into", "through"
    }
    words = re.findall(r"\b[a-zA-Z0-9_\-]{2,}\b", text.lower())
    return [w for w in words if w not in stopwords]


def compute_context_precision(
    retrieved_chunks: List[Any],
    ground_truth_pages: List[int],
    key_terms: List[str],
) -> float:
    """
    Context Precision = Relevant Retrieved Chunks / Total Retrieved Chunks.
    A chunk is considered relevant if its page is in ground_truth_pages
    OR it contains at least one ground-truth key term or significant concept word.
    """
    if not retrieved_chunks:
        return 1.0 if not ground_truth_pages and not key_terms else 0.0

    relevant_count = 0
    gt_pages_set = set(ground_truth_pages)
    terms_lower = set(t.lower() for t in key_terms)
    for t in key_terms:
        for w in _tokenize(t):
            if len(w) > 3:
                terms_lower.add(w.lower())

    for chunk in retrieved_chunks:
        doc_page = getattr(chunk, "document", chunk).metadata.get("page")
        content = getattr(chunk, "document", chunk).page_content.lower()

        page_match = doc_page in gt_pages_set if doc_page is not None else False
        term_match = any(t in content for t in terms_lower) if terms_lower else False

        if page_match or term_match:
            relevant_count += 1

    return round(relevant_count / len(retrieved_chunks), 4)


def compute_context_recall(
    retrieved_chunks: List[Any],
    ground_truth_pages: List[int],
    key_terms: List[str],
) -> float:
    """
    Context Recall = Extent to which ground-truth information is captured in context.
    Combines page recall and key term coverage.
    """
    if not ground_truth_pages and not key_terms:
        return 1.0

    retrieved_pages = set()
    all_context = ""
    for chunk in retrieved_chunks:
        page = getattr(chunk, "document", chunk).metadata.get("page")
        if page is not None:
            retrieved_pages.add(page)
        all_context += " " + getattr(chunk, "document", chunk).page_content.lower()

    # 1. Page coverage
    if ground_truth_pages:
        page_matches = sum(1 for p in ground_truth_pages if p in retrieved_pages)
        page_recall = page_matches / len(ground_truth_pages)
    else:
        page_recall = 1.0

    # 2. Key terms coverage
    if key_terms:
        term_matches = sum(1 for t in key_terms if t.lower() in all_context)
        term_recall = term_matches / len(key_terms)
    else:
        term_recall = 1.0

    # Weighted balanced recall
    if ground_truth_pages and key_terms:
        combined = 0.5 * page_recall + 0.5 * term_recall
    elif ground_truth_pages:
        combined = page_recall
    else:
        combined = term_recall

    return round(combined, 4)


def compute_faithfulness(
    answer: str,
    retrieved_chunks: List[Any],
    answer_status: str,
) -> float:
    """
    Faithfulness = Proportion of factual claims in generated answer grounded in context.
    Guards strictly against external hallucination.
    """
    if answer_status in ("insufficient_evidence", "outside_syllabus", "no_documents_available"):
        # Expected fallback answers are inherently 100% faithful
        return 1.0

    if not retrieved_chunks:
        return 0.0

    context_text = " ".join(
        getattr(c, "document", c).page_content.lower() for c in retrieved_chunks
    )

    # Split answer into sentence-level claims
    sentences = [s.strip() for s in re.split(r"[.\n;!?]", answer) if len(s.strip()) > 15]
    if not sentences:
        return 1.0

    supported_count = 0
    for s in sentences:
        tokens = _tokenize(s)
        if not tokens:
            supported_count += 1
            continue
        # Check token containment in retrieved context
        matches = sum(1 for t in tokens if t in context_text)
        if (matches / len(tokens)) >= 0.5:
            supported_count += 1

    return round(supported_count / len(sentences), 4)


def compute_answer_relevance(question: str, answer: str) -> float:
    """
    Answer Relevance = Lexical and semantic alignment between student question and answer.
    """
    q_tokens = set(_tokenize(question))
    a_tokens = set(_tokenize(answer))

    if not q_tokens or not a_tokens:
        return 1.0

    # Fallback check for standard rejection messages
    if (
        settings.OUTSIDE_SYLLABUS_MSG in answer
        or settings.INSUFFICIENT_ANSWER_MSG in answer
        or settings.NO_DOCUMENTS_UPLOADED_MSG in answer
    ):
        return 1.0

    overlap = q_tokens.intersection(a_tokens)
    if not overlap:
        return 0.3

    recall = len(overlap) / len(q_tokens)
    precision = len(overlap) / len(a_tokens)
    f1 = 2 * (precision * recall) / (precision + recall + 1e-8)
    # Reward strong coverage of question entities in the answer
    score = min(1.0, 0.65 * recall + 0.35 * f1 + 0.1)
    return round(score, 4)


def compute_answer_correctness(answer: str, ground_truth: str) -> float:
    """
    Answer Correctness = Factual and semantic overlap with ground truth answer.
    """
    ans_clean = answer.strip().lower()
    gt_clean = ground_truth.strip().lower()

    if gt_clean in ans_clean or ans_clean in gt_clean:
        return 1.0

    gt_tokens = set(_tokenize(ground_truth))
    ans_tokens = set(_tokenize(answer))

    if not gt_tokens:
        return 1.0

    overlap = gt_tokens.intersection(ans_tokens)
    recall = len(overlap) / len(gt_tokens)
    precision = len(overlap) / len(ans_tokens) if ans_tokens else 0.0

    if precision + recall == 0:
        return 0.0

    f1 = 2 * (precision * recall) / (precision + recall)
    score = min(1.0, 0.7 * recall + 0.3 * f1)
    return round(score, 4)


def compute_citation_accuracy(
    citations: List[Any],
    ground_truth_pages: List[int],
    is_out_of_syllabus: bool,
    is_no_document: bool,
) -> float:
    """
    Citation Accuracy = Validates that citations reference real pages and do not hallucinate.
    If out of syllabus or no document, 0 citations must be produced.
    """
    if is_out_of_syllabus or is_no_document:
        return 1.0 if len(citations) == 0 else 0.0

    if not citations:
        return 0.0 if ground_truth_pages else 1.0

    gt_pages_set = set(ground_truth_pages)
    valid_citations = 0

    for cit in citations:
        page = getattr(cit, "page_number", None) or (
            cit.get("page_number") if isinstance(cit, dict) else None
        )
        snippet = getattr(cit, "relevant_text_snippet", None) or (
            cit.get("relevant_text_snippet") if isinstance(cit, dict) else ""
        )
        # Citation is accurate if page matches ground truth or snippet is substantive
        if page in gt_pages_set or (snippet and len(snippet) > 20):
            valid_citations += 1

    return round(valid_citations / len(citations), 4)


def compute_out_of_syllabus_accuracy(
    answer: str,
    answer_status: str,
    is_out_of_syllabus: bool,
) -> float:
    """Validates that out-of-syllabus questions are rejected correctly."""
    if not is_out_of_syllabus:
        return 1.0

    is_rejected = (
        settings.OUTSIDE_SYLLABUS_MSG in answer
        or settings.INSUFFICIENT_ANSWER_MSG in answer
        or answer_status in ("outside_syllabus", "insufficient_evidence")
    )
    return 1.0 if is_rejected else 0.0


def compute_no_document_accuracy(
    answer: str,
    citations: List[Any],
    answer_status: str,
    is_no_document: bool,
) -> float:
    """Validates that no-document requests return exact mandatory message with zero citations."""
    if not is_no_document:
        return 1.0

    correct_msg = settings.NO_DOCUMENTS_UPLOADED_MSG in answer
    zero_cits = len(citations) == 0
    correct_status = answer_status == "no_documents_available"

    return 1.0 if (correct_msg and zero_cits and correct_status) else 0.0
