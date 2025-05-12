"""
CoFound.ai Orchestration Module

This module handles the coordination and orchestration of 
multi-agent workflows using LangGraph.
"""

from cofoundai.orchestration.langgraph_workflow import LangGraphWorkflow
from cofoundai.orchestration.agentic_graph import AgenticGraph

# API fonksiyonlarını dışa aktar (opsiyonel olarak AP entegrasyonu için)
__all__ = [
    "LangGraphWorkflow",
    "AgenticGraph",
]

# Eğer API paketi yüklüyse, register_as_agent fonksiyonunu shortcut olarak dışa aktar
try:
    from cofoundai.api.app import register_agent_graph
    __all__.append("register_agent_graph")
except ImportError:
    # API paketi yüklü değil, bu durumda sorun yok
    pass
