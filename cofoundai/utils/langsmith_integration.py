
"""
CoFound.ai LangSmith Integration

This module provides LangSmith integration for tracing and monitoring
multi-agent workflows across all phases.
"""

import os
import logging
from typing import Dict, Any, Optional, List
from datetime import datetime
import uuid

try:
    from langsmith import Client
    from langsmith.run_helpers import traceable
    LANGSMITH_AVAILABLE = True
except ImportError:
    LANGSMITH_AVAILABLE = False
    
logger = logging.getLogger(__name__)

class LangSmithTracer:
    """
    LangSmith integration for CoFound.ai multi-agent workflows.
    
    This class provides comprehensive tracing and monitoring capabilities
    for tracking agent interactions, phase transitions, and workflow performance.
    """
    
    def __init__(self, project_name: str = "cofoundai-platform"):
        """
        Initialize LangSmith tracer.
        
        Args:
            project_name: Name of the LangSmith project
        """
        self.project_name = project_name
        self.client = None
        self.session_id = None
        
        if LANGSMITH_AVAILABLE and os.getenv("LANGCHAIN_API_KEY"):
            try:
                self.client = Client()
                logger.info("LangSmith client initialized successfully")
            except Exception as e:
                logger.warning(f"Failed to initialize LangSmith client: {e}")
        else:
            logger.warning("LangSmith not available or API key not set")
    
    def start_workflow_session(self, workflow_id: str, user_input: str) -> str:
        """
        Start a new workflow tracing session.
        
        Args:
            workflow_id: Unique workflow identifier
            user_input: User's initial input
            
        Returns:
            Session ID for tracking
        """
        self.session_id = f"workflow_{workflow_id}_{uuid.uuid4().hex[:8]}"
        
        if self.client:
            try:
                # Create a new session in LangSmith
                self.client.create_session(
                    session_name=self.session_id,
                    project_name=self.project_name,
                    metadata={
                        "workflow_id": workflow_id,
                        "user_input": user_input[:200],  # Truncate for metadata
                        "start_time": datetime.now().isoformat(),
                        "platform": "cofoundai"
                    }
                )
                logger.info(f"Started LangSmith session: {self.session_id}")
            except Exception as e:
                logger.error(f"Failed to create LangSmith session: {e}")
        
        return self.session_id
    
    @traceable(name="agent_execution")
    def trace_agent_execution(
        self, 
        agent_name: str, 
        phase: str,
        input_data: Dict[str, Any], 
        output_data: Dict[str, Any],
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Trace individual agent execution.
        
        Args:
            agent_name: Name of the executing agent
            phase: Current phase (Dream, Maturation, Assemble, etc.)
            input_data: Input data for the agent
            output_data: Output data from the agent
            metadata: Additional metadata
            
        Returns:
            Traced execution result
        """
        trace_metadata = {
            "agent_name": agent_name,
            "phase": phase,
            "execution_time": datetime.now().isoformat(),
            "session_id": self.session_id,
            **(metadata or {})
        }
        
        if self.client:
            try:
                # Log the agent execution
                run = self.client.create_run(
                    name=f"{phase}_{agent_name}",
                    run_type="agent",
                    inputs=input_data,
                    outputs=output_data,
                    session_name=self.session_id,
                    project_name=self.project_name,
                    extra=trace_metadata
                )
                logger.debug(f"Traced agent execution: {agent_name} in {phase}")
                return {"run_id": str(run.id), **output_data}
            except Exception as e:
                logger.error(f"Failed to trace agent execution: {e}")
        
        return output_data
    
    @traceable(name="phase_transition")
    def trace_phase_transition(
        self,
        from_phase: str,
        to_phase: str,
        trigger_reason: str,
        agent_decisions: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Trace phase transitions in the workflow.
        
        Args:
            from_phase: Source phase
            to_phase: Target phase
            trigger_reason: Reason for transition
            agent_decisions: List of agent decisions leading to transition
            
        Returns:
            Transition trace result
        """
        transition_data = {
            "from_phase": from_phase,
            "to_phase": to_phase,
            "trigger_reason": trigger_reason,
            "agent_decisions": agent_decisions,
            "transition_time": datetime.now().isoformat(),
            "session_id": self.session_id
        }
        
        if self.client:
            try:
                run = self.client.create_run(
                    name=f"transition_{from_phase}_to_{to_phase}",
                    run_type="chain",
                    inputs={"from_phase": from_phase, "trigger": trigger_reason},
                    outputs={"to_phase": to_phase, "success": True},
                    session_name=self.session_id,
                    project_name=self.project_name,
                    extra=transition_data
                )
                logger.info(f"Traced phase transition: {from_phase} -> {to_phase}")
                return {"transition_id": str(run.id), **transition_data}
            except Exception as e:
                logger.error(f"Failed to trace phase transition: {e}")
        
        return transition_data
    
    @traceable(name="multi_agent_collaboration")
    def trace_agent_handoff(
        self,
        from_agent: str,
        to_agent: str,
        handoff_reason: str,
        context_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Trace agent-to-agent handoffs.
        
        Args:
            from_agent: Source agent
            to_agent: Target agent
            handoff_reason: Reason for handoff
            context_data: Context being passed
            
        Returns:
            Handoff trace result
        """
        handoff_data = {
            "from_agent": from_agent,
            "to_agent": to_agent,
            "handoff_reason": handoff_reason,
            "context_size": len(str(context_data)),
            "handoff_time": datetime.now().isoformat(),
            "session_id": self.session_id
        }
        
        if self.client:
            try:
                run = self.client.create_run(
                    name=f"handoff_{from_agent}_to_{to_agent}",
                    run_type="tool",
                    inputs={"from_agent": from_agent, "reason": handoff_reason},
                    outputs={"to_agent": to_agent, "context_transferred": True},
                    session_name=self.session_id,
                    project_name=self.project_name,
                    extra=handoff_data
                )
                logger.debug(f"Traced agent handoff: {from_agent} -> {to_agent}")
                return {"handoff_id": str(run.id), **handoff_data}
            except Exception as e:
                logger.error(f"Failed to trace agent handoff: {e}")
        
        return handoff_data
    
    def end_workflow_session(self, final_status: str, artifacts: Dict[str, Any]) -> None:
        """
        End the workflow tracing session.
        
        Args:
            final_status: Final workflow status
            artifacts: Final artifacts produced
        """
        if self.client and self.session_id:
            try:
                # Update session with final metadata
                self.client.update_session(
                    session_id=self.session_id,
                    metadata={
                        "final_status": final_status,
                        "end_time": datetime.now().isoformat(),
                        "artifacts_count": len(artifacts),
                        "completed": final_status == "success"
                    }
                )
                logger.info(f"Ended LangSmith session: {self.session_id}")
            except Exception as e:
                logger.error(f"Failed to end LangSmith session: {e}")
        
        self.session_id = None
    
    def get_workflow_analytics(self, workflow_id: str) -> Dict[str, Any]:
        """
        Get analytics for a specific workflow.
        
        Args:
            workflow_id: Workflow identifier
            
        Returns:
            Analytics data
        """
        if not self.client:
            return {"error": "LangSmith not available"}
        
        try:
            # Query runs for this workflow
            runs = self.client.list_runs(
                project_name=self.project_name,
                filter=f"metadata.workflow_id:{workflow_id}"
            )
            
            analytics = {
                "total_runs": len(list(runs)),
                "phases_executed": set(),
                "agents_involved": set(),
                "average_execution_time": 0,
                "success_rate": 0
            }
            
            # Process runs to generate analytics
            # This would be expanded based on specific metrics needed
            
            return analytics
        except Exception as e:
            logger.error(f"Failed to get workflow analytics: {e}")
            return {"error": str(e)}

# Global tracer instance
_tracer = None

def get_tracer(project_name: str = "cofoundai-platform") -> LangSmithTracer:
    """Get or create global LangSmith tracer instance."""
    global _tracer
    if _tracer is None:
        _tracer = LangSmithTracer(project_name)
    return _tracer

# Decorator for easy tracing
def trace_agent_method(phase: str):
    """Decorator to automatically trace agent methods."""
    def decorator(func):
        def wrapper(self, *args, **kwargs):
            tracer = get_tracer()
            
            input_data = {
                "args": str(args)[:500],  # Truncate for storage
                "kwargs": {k: str(v)[:200] for k, v in kwargs.items()}
            }
            
            try:
                result = func(self, *args, **kwargs)
                output_data = {"result": str(result)[:500], "status": "success"}
            except Exception as e:
                output_data = {"error": str(e), "status": "error"}
                raise
            finally:
                tracer.trace_agent_execution(
                    agent_name=getattr(self, 'name', self.__class__.__name__),
                    phase=phase,
                    input_data=input_data,
                    output_data=output_data
                )
            
            return result
        return wrapper
    return decorator
