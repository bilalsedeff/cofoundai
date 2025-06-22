"""
CoFound.ai LangSmith Integration

This module provides integration with LangSmith for tracing and monitoring
multi-agent workflows and LLM interactions.
"""

import os
import logging
from typing import Dict, Any, Optional, List, Union
from datetime import datetime
import uuid

# Set up logging
logger = logging.getLogger(__name__)

class LangSmithTracer:
    """
    LangSmith integration for tracing CoFound.ai workflows.

    This class provides methods to trace agent executions, workflow sessions,
    and LLM interactions for monitoring and debugging purposes.
    """

    def __init__(self):
        """Initialize LangSmith tracer."""
        self.enabled = self._check_langsmith_config()
        self.current_session = None

        if self.enabled:
            try:
                from langsmith import Client
                # Initialize with environment variables
                self.client = Client(
                    api_key=os.environ.get("LANGCHAIN_API_KEY"),
                    api_url=os.environ.get("LANGCHAIN_ENDPOINT", "https://api.smith.langchain.com")
                )

                # Set project name
                project_name = os.environ.get("LANGCHAIN_PROJECT", "cofoundai-development")
                os.environ["LANGCHAIN_PROJECT"] = project_name

                logger.info("LangSmith tracing enabled")
            except ImportError:
                logger.warning("LangSmith not installed, tracing disabled")
                self.enabled = False
                self.client = None
            except Exception as e:
                logger.error(f"Failed to initialize LangSmith client: {e}")
                self.enabled = False
                self.client = None
        else:
            self.client = None
            logger.info("LangSmith tracing disabled")

    def _check_langsmith_config(self) -> bool:
        """Check if LangSmith is properly configured."""
        api_key = os.environ.get("LANGCHAIN_API_KEY")
        tracing_enabled = os.environ.get("LANGCHAIN_TRACING_V2", "false").lower() == "true"

        return bool(api_key and tracing_enabled)

    def start_workflow_session(self, project_id: str, initial_input: str) -> Optional[str]:
        """
        Start a new workflow tracing session.

        Args:
            project_id: Unique project identifier
            initial_input: Initial user input

        Returns:
            Session ID if successful, None otherwise
        """
        if not self.enabled or not self.client:
            return None

        try:
            session_id = f"workflow_{project_id}_{uuid.uuid4().hex[:8]}"

            # Create session metadata
            session_metadata = {
                "project_id": project_id,
                "session_type": "multi_agent_workflow",
                "initial_input": initial_input[:200],  # Truncate for storage
                "start_time": datetime.now().isoformat(),
                "platform": "cofoundai",
                "google_cloud_project": os.environ.get("GOOGLE_CLOUD_PROJECT"),
                "llm_provider": os.environ.get("LLM_PROVIDER", "openai"),
                "model_name": os.environ.get("MODEL_NAME", "gpt-4o")
            }

            # Start tracing session
            self.client.create_session(
                session_id=session_id,
                metadata=session_metadata
            )

            self.current_session = session_id
            logger.info(f"Started LangSmith session: {session_id}")

            return session_id

        except Exception as e:
            logger.error(f"Failed to start LangSmith session: {str(e)}")
            return None

    def trace_agent_execution(
        self, 
        agent_name: str, 
        phase: str, 
        input_data: Dict[str, Any], 
        output_data: Dict[str, Any],
        execution_time: Optional[float] = None
    ) -> None:
        """
        Trace an individual agent execution.

        Args:
            agent_name: Name of the executing agent
            phase: Current workflow phase
            input_data: Input data for the agent
            output_data: Output data from the agent
            execution_time: Execution time in seconds
        """
        if not self.enabled or not self.client or not self.current_session:
            return

        try:
            # Create trace record
            trace_data = {
                "agent_name": agent_name,
                "phase": phase,
                "session_id": self.current_session,
                "input_data": input_data,
                "output_data": output_data,
                "execution_time": execution_time,
                "timestamp": datetime.now().isoformat(),
                "google_cloud_project": os.environ.get("GOOGLE_CLOUD_PROJECT"),
                "model_used": os.environ.get("MODEL_NAME", "gpt-4o")
            }

            # Log to LangSmith
            run = self.client.create_run(
                name=f"{agent_name}_{phase}",
                run_type="agent",
                inputs=input_data,
                outputs=output_data,
                session_id=self.current_session,
                extra={
                    "agent_name": agent_name, 
                    "phase": phase,
                    "execution_time": execution_time,
                    "google_cloud_project": os.environ.get("GOOGLE_CLOUD_PROJECT")
                }
            )

            logger.debug(f"Traced {agent_name} execution in phase {phase}")

        except Exception as e:
            logger.error(f"Failed to trace agent execution: {str(e)}")

    def end_workflow_session(self, final_status: str, artifacts: Dict[str, Any]) -> None:
        """
        End the current workflow tracing session.

        Args:
            final_status: Final status of the workflow
            artifacts: Final artifacts produced
        """
        if not self.enabled or not self.client or not self.current_session:
            return

        try:
            # Update session with final data
            session_metadata = {
                "final_status": final_status,
                "artifacts_count": len(artifacts),
                "end_time": datetime.now().isoformat(),
                "total_agents_used": len(set(artifacts.keys())) if artifacts else 0
            }

            self.client.update_session(
                session_id=self.current_session,
                metadata=session_metadata
            )

            logger.info(f"Ended LangSmith session: {self.current_session}")
            self.current_session = None

        except Exception as e:
            logger.error(f"Failed to end LangSmith session: {str(e)}")

# Global tracer instance
_tracer_instance = None

def get_tracer() -> LangSmithTracer:
    """Get the global LangSmith tracer instance."""
    global _tracer_instance
    if _tracer_instance is None:
        _tracer_instance = LangSmithTracer()
    return _tracer_instance

def trace_agent_method(phase: str):
    """
    Decorator for tracing agent methods.

    Args:
        phase: The workflow phase this method belongs to
    """
    def decorator(func):
        def wrapper(self, *args, **kwargs):
            tracer = get_tracer()

            # Extract input data
            input_data = {
                "args": str(args)[:200],  # Truncate for storage
                "kwargs": {k: str(v)[:200] for k, v in kwargs.items()}
            }

            # Execute the method
            start_time = datetime.now()
            try:
                result = func(self, *args, **kwargs)
                execution_time = (datetime.now() - start_time).total_seconds()

                # Extract output data
                output_data = {
                    "result_type": type(result).__name__,
                    "result_summary": str(result)[:200] if result else "None"
                }

                # Trace the execution
                agent_name = getattr(self, 'name', self.__class__.__name__)
                tracer.trace_agent_execution(
                    agent_name=agent_name,
                    phase=phase,
                    input_data=input_data,
                    output_data=output_data,
                    execution_time=execution_time
                )

                return result

            except Exception as e:
                execution_time = (datetime.now() - start_time).total_seconds()

                # Trace the error
                output_data = {
                    "error": str(e),
                    "error_type": type(e).__name__
                }

                agent_name = getattr(self, 'name', self.__class__.__name__)
                tracer.trace_agent_execution(
                    agent_name=agent_name,
                    phase=phase,
                    input_data=input_data,
                    output_data=output_data,
                    execution_time=execution_time
                )

                raise
        return wrapper
    return decorator