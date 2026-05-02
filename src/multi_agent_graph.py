from langgraph.graph import StateGraph, END
from langchain_community.chat_models import ChatOllama
from langchain_core.messages import HumanMessage
from tools import (
    query_evidence_base,
    calculate_verification_confidence,
    fetch_paper_metadata,
    verify_citation_accuracy
)

def claim_agent(state):
    llm = ChatOllama(model="llama3.2:1b")

    tools = [query_evidence_base, calculate_verification_confidence]

    llm_tools = llm.bind_tools(tools)

    response = llm_tools.invoke(state["messages"])

    return {"messages": [response]}


def citation_agent(state):
    llm = ChatOllama(model="llama3.2:1b")

    tools = [fetch_paper_metadata, verify_citation_accuracy]

    llm_tools = llm.bind_tools(tools)

    response = llm_tools.invoke(state["messages"])

    return {"messages": [response]}


def router(state):
    msg = state["messages"][-1].content.lower()

    if "citation" in msg:
        return "citation_agent"

    return "claim_agent"


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