from langgraph.graph import StateGraph, END
from langchain_core.messages import HumanMessage, AIMessage
import os
import logging

# ✅ Updated import (fix deprecation)
try:
    from langchain_ollama import ChatOllama
except:
    ChatOllama = None

# Tools
from tools import (
    query_evidence_base,
    calculate_verification_confidence,
    fetch_paper_metadata,
    verify_citation_accuracy
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ======================================================
# ✅  LLM (FOR CI)
# ======================================================

class MockLLM:
    def invoke(self, messages):
        last = messages[-1].content.lower()

        if "evidence" in last or "research" in last:
            return AIMessage(
                content="Research shows hallucinations can be reduced using RAG and fine-tuning.",
                tool_calls=[
                    {
                        "id": "call_1",
                        "name": "query_evidence_base",
                        "args": {"query": last}
                    }
                ]
            )

        if "citation" in last:
            return AIMessage(
                content="The citation appears valid based on metadata.",
                tool_calls=[
                    {
                        "id": "call_2",
                        "name": "verify_citation_accuracy",
                        "args": {"query": last}
                    }
                ]
            )

        if "confidence" in last:
            return AIMessage(
                content="confidence score is 0.7 based on evidence.",
                tool_calls=[
                    {
                        "id": "call_3",
                        "name": "calculate_verification_confidence",
                        "args": {"query": last}
                    }
                ]
            )

        return AIMessage(
            content="random unrelated text."
        )

    def bind_tools(self, tools):
        return self


# ======================================================
# ✅ LLM CREATOR (CI SAFE)
# ======================================================

def get_llm():
    # 🔥 FORCE MOCK IN CI
    if os.getenv("CI") == "true":
        logger.info("🧪 CI detected → using LLM")
        return MockLLM()

    try:
        if ChatOllama:
            logger.info("🚀 Using Ollama LLM")
            return ChatOllama(model="llama3.2:1b", temperature=0.7)
        else:
            raise Exception("ChatOllama not available")

    except Exception as e:
        logger.warning(f"⚠️ Falling back to MockLLM: {e}")
        return MockLLM()


# ======================================================
# ✅ AGENTS
# ======================================================

def claim_agent(state):
    llm = get_llm()

    tools = [query_evidence_base, calculate_verification_confidence]

    llm_tools = llm.bind_tools(tools)

    try:
        response = llm_tools.invoke(state["messages"])
    except Exception as e:
        logger.error(f"Claim agent error: {e}")
        response = AIMessage(content="Error in claim agent")

    return {"messages": state["messages"] + [response]}


def citation_agent(state):
    llm = get_llm()

    tools = [fetch_paper_metadata, verify_citation_accuracy]

    llm_tools = llm.bind_tools(tools)

    try:
        response = llm_tools.invoke(state["messages"])
    except Exception as e:
        logger.error(f"Citation agent error: {e}")
        response = AIMessage(content="Error in citation agent")

    return {"messages": state["messages"] + [response]}


# ======================================================
# ✅ ROUTER
# ======================================================

def router(state):
    msg = state["messages"][-1].content.lower()

    if "citation" in msg:
        return "citation_agent"

    return "__end__"


# ======================================================
# ✅ GRAPH BUILDER
# ======================================================

def build_multi_agent_graph():

    workflow = StateGraph(dict)

    workflow.add_node("claim_agent", claim_agent)
    workflow.add_node("citation_agent", citation_agent)

    workflow.set_entry_point("claim_agent")

    workflow.add_conditional_edges(
        "claim_agent",
        router,
        {
            "citation_agent": "citation_agent",
            "__end__": END
        }
    )

    workflow.add_edge("citation_agent", END)

    return workflow.compile()