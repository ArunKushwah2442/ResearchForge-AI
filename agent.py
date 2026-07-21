from dotenv import load_dotenv

from langchain.agents import create_agent
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_mistralai import ChatMistralAI

from tools import scrape_url, web_search

load_dotenv()


# ==========================================================
# LLM CONFIGURATION
# ==========================================================

# Search + Reader + Critic
# Accuracy focused
research_llm = ChatMistralAI(
    model="mistral-small-latest",
    temperature=0,
)

# Writer
# Better explanation and report quality
writer_llm = ChatMistralAI(
    model="mistral-small-latest",
    temperature=0.2,
)

# Planner
# Better research breakdown
planner_llm = ChatMistralAI(
    model="mistral-small-latest",
    temperature=0.3,
)


# ==========================================================
# Search Agent
# ==========================================================

def build_search_agent():

    return create_agent(
        model=research_llm,
        tools=[web_search],
system_prompt="""
You are a research search specialist.

Your task:

- Find reliable and authoritative sources.
- Prefer primary sources over secondary sources.
- Prefer:
    - arxiv.org
    - research papers
    - official company research blogs
    - Stanford AI Index
    - MIT Research
    - Google DeepMind Research
    - OpenAI Research
    - Microsoft Research
    - NIST AI reports
    - Government AI reports

- Avoid:
    - Medium articles
    - LinkedIn posts
    - YouTube videos
    - generic blogs
    - AI generated articles

- Collect URLs clearly.
- Provide factual summaries.
- Focus on recent and verifiable information.
"""
    )


# ==========================================================
# Reader Agent
# ==========================================================

def build_reader_agent():

    return create_agent(
        model=research_llm,
        tools=[scrape_url],
        system_prompt="""
You are a research reader agent.

Your job:

- Extract useful information from webpages
- Remove unnecessary content
- Focus on facts, numbers, dates and important details
- Preserve important names and statistics
- Return only useful research information
""",
    )


# ==========================================================
# Writer Chain
# ==========================================================
# ==========================================================
# Writer Chain
# ==========================================================

writer_prompt = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            """
You are a professional research analyst.

Create detailed, factual, and well-structured research reports.

Rules:

- Use only the provided research information.
- Do not hallucinate or create unsupported facts.
- Mention uncertainty if information is missing.
- Add inline citations after important factual claims.
- Use only the provided source URLs for citations.
- Do not create fake references or sources.
- Every major factual statement should mention its source.
- Add a final References section containing all used sources.
- Provide balanced analysis including advantages, limitations, challenges, and future scope.
- Maintain a professional research paper style.
- Organize information clearly using headings and bullet points where required.

"""
        ),
        (
            "human",
            """
Research Topic:

{topic}

Collected Information:

{research}

Generate a detailed research report using the following structure:

# Executive Summary

Provide a brief overview of the research topic and key findings.

# Introduction

Explain the topic, importance, and current relevance.

# Background

Provide historical context and technical background.

# Key Findings

Discuss the major discoveries, advancements, trends, and important information from the research.

# Analysis

Provide deeper analysis, comparisons, and practical implications.

# Advantages

Explain benefits and positive impacts.

# Challenges

Discuss limitations, risks, ethical concerns, and technical challenges.

# Future Scope

Explain future possibilities, upcoming trends, and expected developments.

# Conclusion

Summarize the overall findings and final insights.

# References

List all sources used during research with proper URLs.

"""
        ),
    ]
)


writer_chain = ( writer_prompt  | writer_llm  | StrOutputParser()
)


# ==========================================================
# Critic Chain
# ==========================================================

critic_prompt = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            """
You are a senior research quality evaluator.

Review the report critically.

Check:

1. Accuracy
2. Completeness
3. Source reliability
4. Logical flow
5. Missing information
6. Research depth
""",
        ),
        (
            "human",
            """
Report:

{report}


Evaluate:


Score:

Accuracy:

Completeness:

Sources:

Writing Quality:


Strengths:

- ...


Weaknesses:

- ...


Required Improvements:

- ...


Final Verdict:

""",
        ),
    ]
)

critic_chain = ( critic_prompt | research_llm | StrOutputParser()
)

# ==========================================================
# Planner Agent
# ==========================================================

planner_prompt = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            """
You are a research planning expert.

Your task is to create a research plan before searching.

Break the topic into important research sections.

Do not answer the topic.

Only create a research strategy.
""",
        ),
        (
            "human",
            """
Research Topic:

{topic}


Create a detailed research plan.
""",
        ),
    ]
)

planner_chain = (planner_prompt| planner_llm| StrOutputParser()
)






