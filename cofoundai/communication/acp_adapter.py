"""
CoFound.ai ACP (Agent Communication Protocol) Adaptörü

Bu modül, CoFound.ai'nin Agent Communication Protocol (ACP) adaptörünü içerir.
Dış sistemlerle iletişim kurabilmek için ACP protokolünü uygular.
"""

import json
import uuid
import requests
from typing import Dict, List, Any, Optional, Union, Tuple
from enum import Enum
import logging
from urllib.parse import urljoin

from cofoundai.utils.logger import get_logger
from cofoundai.core.extensibility import (
    ExtensibleComponent, ComponentType, ProviderType, Capability
)

logger = get_logger(__name__)

class ACPVersion(str, Enum):
    """ACP Protocol versions"""
    V1_ALPHA = "v1alpha"
    V1 = "v1"

class ACPEndpoint(str, Enum):
    """Standard ACP endpoints"""
    INVOKE = "invoke"  # Invoke agent capability
    STATUS = "status"  # Query operation status
    CANCEL = "cancel"  # Cancel operation
    DESCRIBE = "describe"  # Learn about agent capabilities
    MESSAGE = "message"  # Message in thread

class ACPThreadState(str, Enum):
    """ACP Thread states"""
    RUNNING = "running"
    COMPLETED = "completed" 
    FAILED = "failed"
    CANCELED = "canceled"

class ACPAdapter:
    """
    Agent Communication Protocol (ACP) adapter.
    
    This class provides an adapter for interacting with external ACP-compatible services.
    """
    
    def __init__(self, 
                 base_url: str,
                 api_key: Optional[str] = None,
                 version: ACPVersion = ACPVersion.V1_ALPHA,
                 timeout: int = 30):
        """
        Initialize ACP adapter.
        
        Args:
            base_url: Base URL of the ACP service
            api_key: API key (optional)
            version: ACP protocol version
            timeout: Request timeout (seconds)
        """
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.version = version
        self.timeout = timeout
        logger.info(f"Initialized ACP adapter for {base_url} (version: {version})")
    
    def _get_url(self, endpoint: ACPEndpoint) -> str:
        """Create full endpoint URL"""
        return f"{self.base_url}/acp/{self.version}/{endpoint.value}"
    
    def _get_headers(self) -> Dict[str, str]:
        """Create HTTP headers"""
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json"
        }
        
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
            
        return headers
    
    def describe_agent(self) -> Dict[str, Any]:
        """
        Describe agent capabilities.
        
        Returns:
            Agent description (capabilities, metadata, etc.)
        """
        url = self._get_url(ACPEndpoint.DESCRIBE)
        
        try:
            response = requests.get(
                url,
                headers=self._get_headers(),
                timeout=self.timeout
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Error describing agent: {str(e)}")
            return {"error": str(e)}
    
    def invoke_agent(self, 
                    capability: str, 
                    inputs: Dict[str, Any],
                    thread_id: Optional[str] = None) -> Tuple[str, Dict[str, Any]]:
        """
        Invoke a specific agent capability.
        
        Args:
            capability: The name of the capability to invoke
            inputs: Input parameters
            thread_id: Thread ID (optional, adds to existing thread if provided)
            
        Returns:
            Thread ID and response content
        """
        url = self._get_url(ACPEndpoint.INVOKE)
        
        # Create new thread or use existing one
        if not thread_id:
            thread_id = str(uuid.uuid4())
            
        payload = {
            "thread_id": thread_id,
            "capability": capability,
            "inputs": inputs
        }
        
        try:
            response = requests.post(
                url,
                headers=self._get_headers(),
                json=payload,
                timeout=self.timeout
            )
            response.raise_for_status()
            return thread_id, response.json()
        except Exception as e:
            logger.error(f"Error invoking agent capability '{capability}': {str(e)}")
            return thread_id, {"error": str(e)}
    
    def get_status(self, thread_id: str) -> Dict[str, Any]:
        """
        Check thread status.
        
        Args:
            thread_id: Thread ID to check
            
        Returns:
            Thread status and results
        """
        url = self._get_url(ACPEndpoint.STATUS)
        
        try:
            response = requests.get(
                url,
                headers=self._get_headers(),
                params={"thread_id": thread_id},
                timeout=self.timeout
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Error getting status for thread {thread_id}: {str(e)}")
            return {"error": str(e), "state": ACPThreadState.FAILED}
    
    def cancel_thread(self, thread_id: str) -> bool:
        """
        Cancel a running thread.
        
        Args:
            thread_id: Thread ID to cancel
            
        Returns:
            True if operation was successful, False otherwise
        """
        url = self._get_url(ACPEndpoint.CANCEL)
        
        try:
            response = requests.post(
                url,
                headers=self._get_headers(),
                json={"thread_id": thread_id},
                timeout=self.timeout
            )
            response.raise_for_status()
            return True
        except Exception as e:
            logger.error(f"Error canceling thread {thread_id}: {str(e)}")
            return False
    
    def send_message(self, 
                    thread_id: str, 
                    content: str,
                    role: str = "user") -> Dict[str, Any]:
        """
        Send a message to a thread.
        
        Args:
            thread_id: Thread ID to send message to
            content: Message content
            role: Message sender role (default: user)
            
        Returns:
            Response content
        """
        url = self._get_url(ACPEndpoint.MESSAGE)
        
        payload = {
            "thread_id": thread_id,
            "message": {
                "role": role,
                "content": content
            }
        }
        
        try:
            response = requests.post(
                url,
                headers=self._get_headers(),
                json=payload,
                timeout=self.timeout
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Error sending message to thread {thread_id}: {str(e)}")
            return {"error": str(e)}

class ACPAgentComponent(ExtensibleComponent):
    """
    Represents an agent accessed via the ACP protocol.
    """
    
    def __init__(self, 
                name: str, 
                description: str, 
                adapter: ACPAdapter):
        """
        Initialize ACP agent component.
        
        Args:
            name: Agent name
            description: Agent description
            adapter: ACP adapter to use
        """
        super().__init__(
            name=name,
            description=description,
            component_type=ComponentType.AGENT,
            provider_type=ProviderType.ACP
        )
        self.adapter = adapter
        
        # Load agent capabilities
        self._load_capabilities()
    
    def _load_capabilities(self) -> None:
        """Load agent capabilities from ACP service"""
        try:
            agent_info = self.adapter.describe_agent()
            
            if "capabilities" in agent_info:
                for cap_info in agent_info["capabilities"]:
                    capability = Capability(
                        name=cap_info["name"],
                        description=cap_info.get("description", ""),
                        parameters=cap_info.get("parameters", {})
                    )
                    self.add_capability(capability)
                    
            # Add metadata information
            if "metadata" in agent_info:
                for key, value in agent_info["metadata"].items():
                    self.set_metadata(key, value)
                    
            logger.info(f"Loaded {len(self.capabilities)} capabilities for ACP agent '{self.name}'")
        except Exception as e:
            logger.error(f"Error loading capabilities for ACP agent '{self.name}': {str(e)}")
    
    def invoke(self, capability_name: str, inputs: Dict[str, Any], thread_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Invoke an agent's capability.
        
        Args:
            capability_name: The name of the capability to invoke
            inputs: Input parameters
            thread_id: Thread ID (optional)
            
        Returns:
            Response content
        """
        # Check capability
        capabilities = [cap for cap in self.capabilities if cap.name == capability_name]
        if not capabilities:
            raise ValueError(f"Agent '{self.name}' does not have capability '{capability_name}'")
        
        # Invoke via ACP
        thread_id, response = self.adapter.invoke_agent(capability_name, inputs, thread_id)
        
        # Wait for operation result (can be polled for async operations)
        if "state" in response and response["state"] == ACPThreadState.RUNNING:
            max_polls = 10
            poll_count = 0
            
            while poll_count < max_polls:
                status = self.adapter.get_status(thread_id)
                
                if status.get("state") in [ACPThreadState.COMPLETED, ACPThreadState.FAILED, ACPThreadState.CANCELED]:
                    return status
                
                poll_count += 1
                import time
                time.sleep(2)  # 2 seconds wait
            
            return {"warning": "Operation is still running", "thread_id": thread_id}
        
        return response 