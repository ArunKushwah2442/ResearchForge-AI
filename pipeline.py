import re

from agent import (
    build_reader_agent,
    build_search_agent,
    planner_chain,
    writer_chain,
    critic_chain,
)


# ==========================================================
# Helper
# ==========================================================

def extract_text(content):
    """
    Convert LangChain content blocks into plain text.
    Works with latest LangChain versions.
    """

    if isinstance(content, str):
        return content

    if isinstance(content, list):
        text = ""

        for item in content:
            if isinstance(item, dict):
                if item.get("type") == "text":
                    text += item.get("text", "")
            else:
                text += str(item)

        return text

    return str(content)


# ==========================================================
# Main Pipeline
# ==========================================================

def run_research_pipeline(topic: str):

    state = {
        "topic": topic,
        "research_plan": "",
        "search_results": "",
        "sources": [],
        "scraped_content": "",
        "report": "",
        "feedback": "",
    }

    # ======================================================
    # STEP 1 - PLANNER AGENT
    # ======================================================

    print("\n" + "=" * 70)
    print("STEP 1 - PLANNER AGENT")
    print("=" * 70)

    try:
        state["research_plan"] = planner_chain.invoke(
            {
                "topic": topic,
            }
        )

    except Exception as e:
        print("Planner Error:", e)
        state["research_plan"] = ""

    print("\nRESEARCH PLAN\n")
    print(state["research_plan"])

    # ======================================================
    # STEP 2 - SEARCH AGENT
    # ======================================================

    print("\n" + "=" * 70)
    print("STEP 2 - SEARCH AGENT")
    print("=" * 70)

    try:
        search_agent = build_search_agent()

        search_result = search_agent.invoke(
            {
                "messages": [
                    (
                        "user",
                        f"""
Research Topic:

{topic}


Research Plan:

{state['research_plan']}


Find recent, reliable and detailed information according to this plan.

Use the web_search tool.

Prefer:
- Official websites
- Research papers
- Trusted sources
""",
                    )
                ]
            }
        )

        state["search_results"] = extract_text(
            search_result["messages"][-1].content
        )

    except Exception as e:
        print("Search Error:", e)
        state["search_results"] = ""

    print("\nSEARCH RESULTS\n")
    print(state["search_results"])

    # ======================================================
    # STEP 3 - READER AGENT
    # ======================================================

    print("\n" + "=" * 70)
    print("STEP 3 - READER AGENT")
    print("=" * 70)

    urls = re.findall(
        r"https?://[^\s)>\]]+",
        state["search_results"],
    )

    # Remove duplicate URLs
    urls = list(dict.fromkeys(urls))

    # Store sources for citation
    state["sources"] = urls[:3]

    if len(state["sources"]) == 0:

        print("\nNo URL found.\n")
        state["scraped_content"] = ""

    else:

        print("\nSelected Sources\n")

        for url in state["sources"]:
            print(url)

        try:
            reader_agent = build_reader_agent()

            scraped_content = []

            for url in state["sources"]:

                print("\nScraping:", url)

                try:
                    reader_result = reader_agent.invoke(
                        {
                            "messages": [
                                (
                                    "user",
                                    f"""
Use scrape_url tool.

URL:
{url}

Return useful research information only.
""",
                                )
                            ]
                        }
                    )

                    content = extract_text(
                        reader_result["messages"][-1].content
                    )

                    scraped_content.append(
                        f"""
SOURCE:
{url}


CONTENT:

{content[:4000]}
"""
                    )

                except Exception as e:
                    print("Reader Error for", url, ":", e)

            state["scraped_content"] = "\n\n".join(scraped_content)

        except Exception as e:
            print("Reader Agent Error:", e)
            state["scraped_content"] = ""

    print("\nSCRAPED CONTENT\n")
    print(state["scraped_content"][:1500])

    # ======================================================
    # STEP 4 - WRITER
    # ======================================================

    print("\n" + "=" * 70)
    print("STEP 4 - WRITER")
    print("=" * 70)

    research = f"""

RESEARCH PLAN:

{state['research_plan']}


SEARCH RESULTS:

{state['search_results']}


SCRAPED CONTENT:

{state['scraped_content']}


SOURCES:

{state['sources']}

"""

    try:
        state["report"] = writer_chain.invoke(
            {
                "topic": topic,
                "research": research,
            }
        )

    except Exception as e:
        print("Writer Error:", e)
        state["report"] = ""

    print("\nREPORT\n")
    print(state["report"])

    # ======================================================
    # STEP 5 - CRITIC
    # ======================================================

    print("\n" + "=" * 70)
    print("STEP 5 - CRITIC")
    print("=" * 70)

    try:
        state["feedback"] = critic_chain.invoke(
            {
                "report": state["report"],
            }
        )

    except Exception as e:
        print("Critic Error:", e)
        state["feedback"] = ""

    print("\nCRITIC REPORT\n")
    print(state["feedback"])

    return state


# ==========================================================
# MAIN
# ==========================================================

if __name__ == "__main__":

    topic = input("\nEnter a research topic: ")

    run_research_pipeline(topic)