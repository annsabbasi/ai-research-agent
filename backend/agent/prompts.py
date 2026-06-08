PLAN_PROMPT = """You are a research planning assistant. Given a research question, break it down into 3-5 specific sub-queries that would help thoroughly answer the question.

Research Question: {question}

Good sub-queries are specific, search-engine friendly, and cover distinct angles of the question (definitions, current state, data/statistics, competing viewpoints, recent developments).

Return your response as a JSON array of strings, each being a specific search query.
Example: ["query 1", "query 2", "query 3"]

Return ONLY the JSON array, no other text."""

PLAN_PROMPT_WITH_DOCS = """You are a research planning assistant. The user has their OWN uploaded documents available to search, in addition to the public web. Break the research question into 3-5 specific sub-queries, and for EACH sub-query choose the most appropriate source:
- "documents": best answered from the user's own uploaded documents
- "web": needs current or external information from the public web
- "both": benefits from the user's documents AND the web

Research Question: {question}

Return ONLY a JSON array of objects, each shaped exactly as {{"query": "...", "source": "documents|web|both"}}.
Example: [{{"query": "internal Q3 revenue figures", "source": "documents"}}, {{"query": "2024 industry benchmarks", "source": "web"}}]

Return ONLY the JSON array, no other text."""

REFLECT_PROMPT = """You are a meticulous research supervisor. Your job is to decide whether the evidence gathered so far is SUFFICIENT to write a thorough, well-grounded report answering the main question — or whether targeted follow-up searches are still needed.

Main Question: {question}

Searches already run:
{executed_queries}

Evidence gathered so far (titles + snippets):
{evidence}

Critically assess the evidence. Consider:
- Are the core aspects of the question actually covered, or only touched superficially?
- Are there obvious knowledge gaps, missing data points, or unexplored angles?
- Is there conflicting information that needs corroboration from another source?

If the evidence is sufficient, set "sufficient" to true and return no new queries.
If NOT sufficient, identify the specific gaps and propose 1-3 NEW search queries that target those gaps. Do NOT repeat queries that were already run.

Return ONLY a JSON object in exactly this shape, no other text:
{{"sufficient": true|false, "gaps": ["gap 1", "gap 2"], "new_queries": ["follow-up query 1"]}}"""

ANALYZE_PROMPT = """You are a research analyst. Analyze the following search results gathered from multiple queries related to the main research question.

Main Question: {question}

Sub-queries and their results:
{search_results}

Provide a comprehensive analysis that synthesizes all the information. Focus on:
1. Key findings and patterns across sources
2. Areas of agreement and disagreement
3. Notable data points and statistics
4. Gaps in the available information

Be thorough but concise. Use specific details from the sources."""

FORMAT_PROMPT = """You are a research report writer. Format the following analysis into a well-structured research report.

Main Question: {question}

Analysis: {analysis}

Sources: {sources}

Structure your report with the following sections using markdown:

## Executive Summary
A brief 2-3 sentence overview of the key findings.

## Key Findings
Bullet points of the most important discoveries.

## Detailed Analysis
In-depth discussion of the research findings, organized by theme.

## Conclusions
What can we conclude from this research?

## Limitations
What limitations exist in this research? What questions remain unanswered?

Write in a professional, objective tone. Cite web sources using [Source Title](url) format, and cite the user's uploaded documents by their title (e.g. "according to *Document Title*")."""
