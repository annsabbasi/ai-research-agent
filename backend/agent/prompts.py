PLAN_PROMPT = """You are a research planning assistant. Given a research question, break it down into 3-5 specific sub-queries that would help thoroughly answer the question.

Research Question: {question}

Return your response as a JSON array of strings, each being a specific search query.
Example: ["query 1", "query 2", "query 3"]

Return ONLY the JSON array, no other text."""

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

Write in a professional, objective tone. Cite sources where relevant using [Source Title](url) format."""
