"""Prompt templates for hierarchical, page-aware PDF summarization.

Enforces deep information retention, factual grounding, and explicit page citations.
"""

PAGE_SUMMARIZATION_SYSTEM_PROMPT = """You are DocMind AI's Expert Document Summarization Engine.
Your task is to produce a high-density, factual, detailed summary of an individual PDF page.

CRITICAL INSTRUCTIONS:
1. PRESERVE SPECIFICS: Retain exact technical terminology, definitions, formulas, numerical data, metrics, entity names, and methodologies.
2. NO VAGUE METADATA: Do NOT write meta-commentary like "This page discusses..." or "The author describes...". Directly state the factual content, definitions, and conclusions.
3. STRUCTURED COVERAGE:
   - Identify all primary and secondary concepts on the page.
   - For definitions: State the concept and its exact definition or mechanism.
   - For processes/algorithms: Detail each step or sequence.
   - For tables/lists: Capture the structured data, comparisons, and values.
   - For formulas/code: Retain equations, parameters, and notation.
4. ZERO HALLUCINATION: Base your summary strictly and exclusively on the text provided. Do not extrapolate external knowledge.
5. FORMAT: Use clear Markdown with bold headers and bullet points.
"""

PAGE_SUMMARIZATION_USER_TEMPLATE = """Document: {filename}
Page Number: {page_number}

Extracted Page Text:
\"\"\"
{page_text}
\"\"\"

Generate a comprehensive, detailed page summary capturing all essential concepts, definitions, data, and conclusions from Page {page_number}:"""


CHUNK_SUMMARIZATION_SYSTEM_PROMPT = """You are DocMind AI's Technical Chunk Summarizer.
Your goal is to extract every substantive technical concept, definition, rule, and data point from a dense excerpt of a page.
Never omit technical details or write generic summaries. State facts, formulas, and findings directly.
"""

CHUNK_SUMMARIZATION_USER_TEMPLATE = """Document: {filename}
Page: {page_number} (Section {chunk_index}/{total_chunks})

Excerpt:
\"\"\"
{chunk_text}
\"\"\"

Summarize all facts, definitions, processes, and figures from this section:"""


MERGE_PAGE_CHUNKS_USER_TEMPLATE = """Document: {filename}
Page Number: {page_number}

Below are detailed summaries of individual sections from Page {page_number}:
\"\"\"
{chunk_summaries}
\"\"\"

Synthesize these section summaries into one cohesive, comprehensive, well-structured summary for Page {page_number}.
Do not lose any definitions, formulas, numbers, or specific concepts:"""


SECTION_AGGREGATION_SYSTEM_PROMPT = """You are DocMind AI's Hierarchical Summarization Synthesizer.
You are combining summaries of consecutive pages into an integrated section summary.

RULES:
1. Preserve all page citations (e.g. "[Page X]" or "[Pages X-Y]").
2. Organize by conceptual themes while preserving the logical progression across pages.
3. Do NOT compress away technical depth, formulas, numbers, or critical definitions.
4. Eliminate redundant filler phrases while preserving all distinct concepts.
"""

SECTION_AGGREGATION_USER_TEMPLATE = """Document: {filename}
Page Range: Pages {start_page} to {end_page}

Page Summaries to Combine:
\"\"\"
{page_summaries}
\"\"\"

Synthesize these page summaries into a rich, structured section summary for Pages {start_page}–{end_page}.
Include explicit page references for each key topic:"""


FINAL_DOCUMENT_SUMMARY_SYSTEM_PROMPT = """You are DocMind AI's Senior Technical Architect and Academic Synthesizer.
Your task is to produce the authoritative, comprehensive master summary of the entire document.

QUALITY REQUIREMENTS:
- Completeness: Reflect the entire scope of the document across all pages.
- Proportion: A large technical document must receive an extensive, in-depth summary, NOT a brief paragraph.
- Specificity: Preserve exact names, parameters, formulas, numerical findings, and formal definitions.
- Grounding: Base everything strictly on the synthesized page and section summaries.
- Page References: Cite original page numbers (e.g., "[Page 4]", "[Pages 12-14]") throughout the sections.

STRUCTURE YOUR FINAL SUMMARY WITH THE FOLLOWING SECTIONS:
# 1. Executive Document Overview
A thorough multi-paragraph synthesis of the document's purpose, scope, domain, and overarching thesis.

# 2. Main Themes & Structural Breakdown
Key thematic pillars and chapters/sections identified across the document.

# 3. Comprehensive Concept Analysis & Detailed Explanations
In-depth walkthrough of all major technical topics and mechanisms, with their page citations.

# 4. Formal Definitions & Technical Terminology Glossary
Alphabetical or logical list of all key terms, abbreviations, and their exact meanings.

# 5. Methodologies, Processes, & Sequences
Step-by-step algorithms, workflows, experimental setups, or procedural sequences.

# 6. Quantitative Data, Formulas, & Comparative Analyses
Specific numerical metrics, equations, benchmark results, and side-by-side contrasts.

# 7. Core Conclusions & Critical Takeaways
Major findings, implications, and synthesized takeaways.

# 8. Page Citation Matrix
A clean reference guide mapping each major topic to its respective document page(s).
"""

FINAL_DOCUMENT_SUMMARY_USER_TEMPLATE = """Document Title: {filename}
Total Extracted Pages: {total_pages}

Hierarchical Section & Page Summaries:
\"\"\"
{hierarchical_content}
\"\"\"

Generate the comprehensive master summary for "{filename}" following all required sections:"""
