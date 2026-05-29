"""
SED Energy AI Marketing System - Multi-Agent Orchestrator
Built on LangGraph for stateful multi-agent coordination.
"""
from typing import TypedDict, Annotated, Sequence, Optional, Any
from langgraph.graph import StateGraph, END
from langgraph.prebuilt import ToolNode
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage
import operator
import logging
import json
from datetime import datetime, timezone

from app.agents.strategy_agent import StrategyAgent
from app.agents.content_agent import ContentAgent
from app.agents.design_agent import DesignAgent
from app.agents.video_agent import VideoAgent
from app.agents.whatsapp_agent import WhatsAppAgent
from app.agents.news_agent import NewsAgent
from app.agents.analytics_agent import AnalyticsAgent
from app.agents.stock_agent import StockAgent
from app.agents.brand_agent import BrandComplianceAgent
from app.agents.engagement_agent import EngagementAgent
from app.core.prompts import SED_MASTER_SYSTEM_PROMPT

logger = logging.getLogger("sed-ai.orchestrator")


class AgentState(TypedDict):
    """Shared state passed between all agents in the graph"""
    messages: Annotated[Sequence[BaseMessage], operator.add]
    task_type: str                          # "generate_content" | "stock_alert" | "news_response" | "analytics"
    platform: Optional[str]
    content_type: Optional[str]
    topic: Optional[str]
    target_audience: Optional[str]
    context: Optional[dict]                 # Additional context from knowledge base
    generated_content: Optional[dict]       # Output from ContentAgent
    design_prompt: Optional[str]            # Output for image generation
    video_prompt: Optional[str]             # Output for video generation
    brand_check_passed: Optional[bool]      # Output from BrandComplianceAgent
    brand_issues: Optional[list]            # Issues found by BrandComplianceAgent
    final_output: Optional[dict]            # Final approved output
    requires_human_approval: bool
    confidence_score: float
    agent_trace: list                       # Execution trace for debugging
    error: Optional[str]
    timestamp: str


class SEDMarketingOrchestrator:
    """
    LangGraph-based multi-agent orchestrator for SED Energy marketing operations.
    Coordinates 10 specialized agents in a stateful workflow graph.
    """

    def __init__(self):
        self.strategy_agent = StrategyAgent()
        self.content_agent = ContentAgent()
        self.design_agent = DesignAgent()
        self.video_agent = VideoAgent()
        self.whatsapp_agent = WhatsAppAgent()
        self.news_agent = NewsAgent()
        self.analytics_agent = AnalyticsAgent()
        self.stock_agent = StockAgent()
        self.brand_agent = BrandComplianceAgent()
        self.engagement_agent = EngagementAgent()

        self.graph = self._build_graph()
        self.app = self.graph.compile()

    def _build_graph(self) -> StateGraph:
        """Build the LangGraph workflow"""
        workflow = StateGraph(AgentState)

        # Add all agent nodes
        workflow.add_node("strategy",        self._strategy_node)
        workflow.add_node("content",         self._content_node)
        workflow.add_node("design",          self._design_node)
        workflow.add_node("video",           self._video_node)
        workflow.add_node("whatsapp",        self._whatsapp_node)
        workflow.add_node("brand_check",     self._brand_check_node)
        workflow.add_node("news",            self._news_node)
        workflow.add_node("analytics",       self._analytics_node)
        workflow.add_node("stock",           self._stock_node)
        workflow.add_node("engagement",      self._engagement_node)
        workflow.add_node("finalize",        self._finalize_node)

        # Entry point routing
        workflow.set_conditional_entry_point(
            self._route_task,
            {
                "generate_content": "strategy",
                "stock_alert": "stock",
                "news_response": "news",
                "analytics_run": "analytics",
                "engagement_reply": "engagement",
                "whatsapp_message": "whatsapp",
            }
        )

        # Content generation flow: strategy → content → design → brand_check → finalize
        workflow.add_edge("strategy", "content")
        workflow.add_conditional_edges(
            "content",
            self._route_after_content,
            {
                "needs_image": "design",
                "needs_video": "video",
                "whatsapp_only": "whatsapp",
                "brand_check": "brand_check",
            }
        )
        workflow.add_edge("design", "brand_check")
        workflow.add_edge("video", "brand_check")
        workflow.add_edge("whatsapp", "brand_check")
        workflow.add_conditional_edges(
            "brand_check",
            self._route_after_brand_check,
            {
                "approved": "finalize",
                "needs_revision": "content",
                "escalate": "finalize",  # Escalate to human
            }
        )
        workflow.add_edge("stock", "content")
        workflow.add_edge("news", "content")
        workflow.add_edge("analytics", "finalize")
        workflow.add_edge("engagement", "finalize")
        workflow.add_edge("finalize", END)

        return workflow

    def _route_task(self, state: AgentState) -> str:
        return state.get("task_type", "generate_content")

    def _route_after_content(self, state: AgentState) -> str:
        content = state.get("generated_content", {})
        platform = state.get("platform", "")
        content_type = content.get("content_type", "")

        if content_type in ["video", "reel"]:
            return "needs_video"
        elif platform == "whatsapp":
            return "whatsapp_only"
        elif content_type in ["image_post", "carousel", "story"]:
            return "needs_image"
        else:
            return "brand_check"

    def _route_after_brand_check(self, state: AgentState) -> str:
        if not state.get("brand_check_passed", False):
            issues = state.get("brand_issues", [])
            if any(i.get("severity") == "critical" for i in issues):
                return "escalate"
            return "needs_revision"
        return "approved"

    async def _strategy_node(self, state: AgentState) -> AgentState:
        logger.info("🎯 Strategy Agent running...")
        state["agent_trace"].append({"agent": "strategy", "started_at": datetime.now(timezone.utc).isoformat()})
        result = await self.strategy_agent.run(state)
        state.update(result)
        return state

    async def _content_node(self, state: AgentState) -> AgentState:
        logger.info("✍️  Content Agent running...")
        state["agent_trace"].append({"agent": "content", "started_at": datetime.now(timezone.utc).isoformat()})
        result = await self.content_agent.run(state)
        state.update(result)
        return state

    async def _design_node(self, state: AgentState) -> AgentState:
        logger.info("🎨 Design Agent running...")
        state["agent_trace"].append({"agent": "design", "started_at": datetime.now(timezone.utc).isoformat()})
        result = await self.design_agent.run(state)
        state.update(result)
        return state

    async def _video_node(self, state: AgentState) -> AgentState:
        logger.info("🎥 Video Agent running...")
        state["agent_trace"].append({"agent": "video", "started_at": datetime.now(timezone.utc).isoformat()})
        result = await self.video_agent.run(state)
        state.update(result)
        return state

    async def _whatsapp_node(self, state: AgentState) -> AgentState:
        logger.info("💬 WhatsApp Agent running...")
        state["agent_trace"].append({"agent": "whatsapp", "started_at": datetime.now(timezone.utc).isoformat()})
        result = await self.whatsapp_agent.run(state)
        state.update(result)
        return state

    async def _brand_check_node(self, state: AgentState) -> AgentState:
        logger.info("✅ Brand Compliance Agent running...")
        state["agent_trace"].append({"agent": "brand_check", "started_at": datetime.now(timezone.utc).isoformat()})
        result = await self.brand_agent.run(state)
        state.update(result)
        return state

    async def _news_node(self, state: AgentState) -> AgentState:
        logger.info("📰 News Agent running...")
        state["agent_trace"].append({"agent": "news", "started_at": datetime.now(timezone.utc).isoformat()})
        result = await self.news_agent.run(state)
        state.update(result)
        return state

    async def _analytics_node(self, state: AgentState) -> AgentState:
        logger.info("📊 Analytics Agent running...")
        state["agent_trace"].append({"agent": "analytics", "started_at": datetime.now(timezone.utc).isoformat()})
        result = await self.analytics_agent.run(state)
        state.update(result)
        return state

    async def _stock_node(self, state: AgentState) -> AgentState:
        logger.info("📦 Stock Agent running...")
        state["agent_trace"].append({"agent": "stock", "started_at": datetime.now(timezone.utc).isoformat()})
        result = await self.stock_agent.run(state)
        state.update(result)
        return state

    async def _engagement_node(self, state: AgentState) -> AgentState:
        logger.info("💡 Engagement Agent running...")
        state["agent_trace"].append({"agent": "engagement", "started_at": datetime.now(timezone.utc).isoformat()})
        result = await self.engagement_agent.run(state)
        state.update(result)
        return state

    async def _finalize_node(self, state: AgentState) -> AgentState:
        logger.info("🏁 Finalizing output...")
        content = state.get("generated_content", {})
        confidence = state.get("confidence_score", 0.0)

        # Auto-approve high-confidence, non-sensitive content
        requires_approval = (
            confidence < 0.85
            or content.get("has_pricing", False)
            or content.get("has_specs", False)
            or not state.get("brand_check_passed", False)
        )

        state["requires_human_approval"] = requires_approval
        state["final_output"] = {
            "content": content,
            "design_prompt": state.get("design_prompt"),
            "video_prompt": state.get("video_prompt"),
            "confidence_score": confidence,
            "brand_approved": state.get("brand_check_passed", False),
            "requires_human_approval": requires_approval,
            "agent_trace": state.get("agent_trace", []),
            "generated_at": datetime.now(timezone.utc).isoformat(),
        }
        return state

    async def run(self, task_type: str, **kwargs) -> dict:
        """Main entry point for running the orchestrator"""
        initial_state: AgentState = {
            "messages": [],
            "task_type": task_type,
            "platform": kwargs.get("platform"),
            "content_type": kwargs.get("content_type"),
            "topic": kwargs.get("topic"),
            "target_audience": kwargs.get("target_audience"),
            "context": kwargs.get("context", {}),
            "generated_content": None,
            "design_prompt": None,
            "video_prompt": None,
            "brand_check_passed": None,
            "brand_issues": [],
            "final_output": None,
            "requires_human_approval": True,
            "confidence_score": 0.0,
            "agent_trace": [],
            "error": None,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

        try:
            result = await self.app.ainvoke(initial_state)
            return result.get("final_output", {})
        except Exception as e:
            logger.error(f"Orchestrator error: {e}", exc_info=True)
            return {"error": str(e), "requires_human_approval": True}


# Singleton
_orchestrator: Optional[SEDMarketingOrchestrator] = None


def get_orchestrator() -> SEDMarketingOrchestrator:
    global _orchestrator
    if _orchestrator is None:
        _orchestrator = SEDMarketingOrchestrator()
    return _orchestrator
