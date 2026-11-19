import re


class TextCleaner:
    """Cleans and normalizes extracted PDF text for vector indexing and prompting."""

    @staticmethod
    def clean_text(text: str) -> str:
        """
        Cleans extracted text:
        - Removes control characters and null bytes
        - Fixes hyphenated line breaks (e.g., 'para-\ngraph' -> 'paragraph')
        - Normalizes multiple spaces and tabs to single spaces
        - Collapses 3+ newlines to 2 newlines
        - Strips surrounding whitespace
        """
        if not text:
            return ""

        # Remove null bytes and non-printable control characters (except newline and tab)
        cleaned = re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f-\x9f]", "", text)

        # Fix hyphenated words broken across lines
        cleaned = re.sub(r"(\w+)-\n(\w+)", r"\1\2", cleaned)

        # Normalize carriage returns
        cleaned = cleaned.replace("\r\n", "\n").replace("\r", "\n")

        # Normalize excessive horizontal whitespace (tabs and multiple spaces)
        cleaned = re.sub(r"[ \t]+", " ", cleaned)

        # Collapse more than 2 consecutive newlines
        cleaned = re.sub(r"\n{3,}", "\n\n", cleaned)

        return cleaned.strip()

    @staticmethod
    def sanitize_for_prompt(text: str) -> str:
        """
        Guards against prompt injection in document content by neutralizing common delimiters.
        """
        if not text:
            return ""
        # Neutralize markdown system prompt injection indicators
        sanitized = text.replace("```", "'''")
        return sanitized
