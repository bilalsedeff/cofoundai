"""
CoFound.ai Extensibility Framework

This module defines the extensible architecture of CoFound.ai.
The hybrid approach (Modular Core + ACP/MCP Adapters) is implemented.
"""

from abc import ABC, abstractmethod
from enum import Enum
from typing import Dict, List, Any, Optional, Callable, Type, Union
import uuid
import json
import logging

from cofoundai.utils.logger import get_logger

logger = get_logger(__name__)

class ProviderType(Enum):
    """Component provider type enumeration"""
    INTERNAL = "internal"      # Directly running in the system
    ACP = "acp"                # Connected via ACP protocol
    MCP = "mcp"                # Connected via MCP protocol
    CUSTOM = "custom"          # Using custom protocol

class ComponentType(Enum):
    """System component type enumeration"""
    AGENT = "agent"            # Agent component
    TOOL = "tool"              # Tool component
    MEMORY = "memory"          # Memory component
    WORKFLOW = "workflow"      # Workflow component

class Capability:
    """Component capability definition"""
    
    def __init__(self, name: str, description: str, parameters: Optional[Dict[str, Any]] = None):
        """
        Create a capability definition.
        
        Args:
            name: Capability name
            description: Capability description
            parameters: Capability parameters (optional)
        """
        self.id = str(uuid.uuid4())
        self.name = name
        self.description = description
        self.parameters = parameters or {}
    
    def to_dict(self) -> Dict[str, Any]:
        """Return capability as a dictionary"""
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "parameters": self.parameters
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Capability':
        """Create capability from dictionary"""
        capability = cls(
            name=data["name"],
            description=data["description"],
            parameters=data.get("parameters", {})
        )
        capability.id = data.get("id", str(uuid.uuid4()))
        return capability

class ExtensibleComponent(ABC):
    """Base class for extensible components"""
    
    def __init__(self, 
                 name: str, 
                 description: str,
                 component_type: ComponentType,
                 provider_type: ProviderType = ProviderType.INTERNAL):
        """
        Create an extensible component.
        
        Args:
            name: Component name
            description: Component description
            component_type: Component type (agent, tool, etc.)
            provider_type: Provider type (internal, acp, etc.)
        """
        self.id = str(uuid.uuid4())
        self.name = name
        self.description = description
        self.component_type = component_type
        self.provider_type = provider_type
        self.capabilities: List[Capability] = []
        self.metadata: Dict[str, Any] = {}
    
    def add_capability(self, capability: Capability) -> None:
        """Add capability to component"""
        self.capabilities.append(capability)
    
    def get_capabilities(self) -> List[Capability]:
        """Return component capabilities"""
        return self.capabilities
    
    def set_metadata(self, key: str, value: Any) -> None:
        """Add component metadata"""
        self.metadata[key] = value
    
    def get_metadata(self, key: str, default: Any = None) -> Any:
        """Get component metadata"""
        return self.metadata.get(key, default)
    
    def to_dict(self) -> Dict[str, Any]:
        """Return component as a dictionary"""
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "component_type": self.component_type.value,
            "provider_type": self.provider_type.value,
            "capabilities": [c.to_dict() for c in self.capabilities],
            "metadata": self.metadata
        }
    
    @abstractmethod
    def invoke(self, *args, **kwargs) -> Any:
        """
        Invoke/execute the component.
        Must be implemented by subclasses.
        """
        pass

class ComponentRegistry:
    """Central registry for extensible components"""
    
    def __init__(self):
        """Initialize the component registry"""
        self._components: Dict[str, ExtensibleComponent] = {}
        self._components_by_type: Dict[ComponentType, Dict[str, ExtensibleComponent]] = {
            ct: {} for ct in ComponentType
        }
        logger.info("Component registry initialized")
    
    def register(self, component: ExtensibleComponent) -> str:
        """
        Register the component
        
        Args:
            component: Component to register
            
        Returns:
            Component ID
        """
        self._components[component.id] = component
        self._components_by_type[component.component_type][component.id] = component
        logger.info(f"Registered component: {component.name} ({component.id})")
        return component.id
    
    def unregister(self, component_id: str) -> bool:
        """
        Remove the component registration
        
        Args:
            component_id: Component ID to remove
            
        Returns:
            True if the operation was successful, False otherwise
        """
        if component_id not in self._components:
            logger.warning(f"Component not found: {component_id}")
            return False
        
        component = self._components[component_id]
        del self._components[component_id]
        del self._components_by_type[component.component_type][component_id]
        logger.info(f"Unregistered component: {component.name} ({component_id})")
        return True
    
    def get(self, component_id: str) -> Optional[ExtensibleComponent]:
        """
        Get component by ID
        
        Args:
            component_id: Component ID
            
        Returns:
            Component or None (if not found)
        """
        return self._components.get(component_id)
    
    def get_by_type(self, component_type: ComponentType) -> List[ExtensibleComponent]:
        """
        Get components by type
        
        Args:
            component_type: Component type
            
        Returns:
            List of components
        """
        return list(self._components_by_type[component_type].values())
    
    def get_by_capability(self, capability_name: str) -> List[ExtensibleComponent]:
        """
        Get components by capability
        
        Args:
            capability_name: Capability name
            
        Returns:
            List of components with the capability
        """
        return [
            component for component in self._components.values()
            if any(cap.name == capability_name for cap in component.capabilities)
        ]
    
    def get_all(self) -> List[ExtensibleComponent]:
        """Get all components"""
        return list(self._components.values())

# Singleton component registry instance
component_registry = ComponentRegistry() 