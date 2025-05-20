"""
CoFound.ai Component Factory Module

This module provides a central factory for creating different component types.
"""

from typing import Dict, List, Any, Optional, Type, Union, Callable
import logging
import importlib
import yaml
import os

from cofoundai.utils.logger import get_logger
from cofoundai.core.extensibility import (
    ExtensibleComponent, ComponentType, ProviderType, Capability, 
    component_registry
)
from cofoundai.communication.acp_adapter import (
    ACPAdapter, ACPVersion, ACPAgentComponent
)
from cofoundai.communication.mcp_adapter import (
    MCPAdapter, MCPToolComponent, MCPModelComponent, MCPRetrievalComponent, MCPToolType
)
from cofoundai.tools.extensible_tool import (
    Tool, FunctionTool, CommandTool, RESTTool
)
from cofoundai.agents.extensible_agent import (
    Agent, LLMAgent, ToolAgent
)

logger = get_logger(__name__)

class ComponentFactory:
    """
    Component factory class.
    
    This class provides a central factory for creating different component types.
    """
    
    def __init__(self, config_path: Optional[str] = None):
        """
        Initialize the component factory.
        
        Args:
            config_path: Configuration file path (optional)
        """
        self.config = {}
        
        if config_path and os.path.exists(config_path):
            self._load_config(config_path)
            
        logger.info("Component factory initialized")
    
    def _load_config(self, config_path: str) -> None:
        """
        Load the configuration file.
        
        Args:
            config_path: Configuration file path
        """
        try:
            with open(config_path, 'r') as f:
                self.config = yaml.safe_load(f)
            logger.info(f"Loaded component factory config from {config_path}")
        except Exception as e:
            logger.error(f"Error loading component factory config: {str(e)}")
    
    def create_component(self, 
                       component_type: Union[ComponentType, str], 
                       component_config: Dict[str, Any]) -> Optional[ExtensibleComponent]:
        """
        Create a component.
        
        Args:
            component_type: Component type (ComponentType enum or string)
            component_config: Component configuration
            
        Returns:
            Created component
        """
        # If string, convert to enum
        if isinstance(component_type, str):
            try:
                component_type = ComponentType(component_type)
            except ValueError:
                logger.error(f"Invalid component type: {component_type}")
                return None
        
        # Create component based on type
        try:
            if component_type == ComponentType.AGENT:
                return self.create_agent(component_config)
            elif component_type == ComponentType.TOOL:
                return self.create_tool(component_config)
            else:
                logger.error(f"Unsupported component type: {component_type}")
                return None
        except Exception as e:
            logger.error(f"Error creating {component_type.value} component: {str(e)}")
            return None
    
    def create_agent(self, agent_config: Dict[str, Any]) -> Optional[Agent]:
        """
        Create an agent component.
        
        Args:
            agent_config: Agent configuration
            
        Returns:
            Created agent
        """
        agent_type = agent_config.get("agent_type", "")
        provider_type = agent_config.get("provider_type", "internal")
        
        name = agent_config.get("name", "")
        description = agent_config.get("description", "")
        
        if not name:
            logger.error("Agent name is required")
            return None
        
        # Check provider type
        if provider_type == "internal":
            # Create internal agent types
            if agent_type == "llm":
                return self._create_llm_agent(agent_config)
            elif agent_type == "tool":
                return self._create_tool_agent(agent_config)
            else:
                logger.error(f"Unsupported internal agent type: {agent_type}")
                return None
        elif provider_type == "acp":
            # Create ACP agent
            return self._create_acp_agent(agent_config)
        elif provider_type == "mcp":
            # Create MCP model
            return self._create_mcp_model(agent_config)
        else:
            logger.error(f"Unsupported provider type: {provider_type}")
            return None
    
    def _create_llm_agent(self, agent_config: Dict[str, Any]) -> Optional[LLMAgent]:
        """
        Create an LLM agent.
        
        Args:
            agent_config: Agent configuration
            
        Returns:
            Created LLM agent
        """
        try:
            name = agent_config.get("name", "")
            description = agent_config.get("description", "")
            
            # Get model configuration
            model_config = agent_config.get("model", {})
            model_provider = model_config.get("provider", "")
            model_name = model_config.get("name", "")
            
            if not model_provider or not model_name:
                logger.error("Model provider and name are required for LLM agent")
                return None
            
            # Create model instance
            model = self._get_model_instance(model_provider, model_name, model_config)
            if not model:
                logger.error(f"Failed to create model {model_provider}/{model_name}")
                return None
            
            # Get prompt template and system message
            prompt_template = agent_config.get("prompt_template", "")
            system_message = agent_config.get("system_message", "")
            
            # Create LLM agent
            llm_agent = LLMAgent(
                name=name,
                description=description,
                model=model,
                prompt_template=prompt_template,
                system_message=system_message
            )
            
            # Save and return
            component_registry.register(llm_agent)
            return llm_agent
        except Exception as e:
            logger.error(f"Error creating LLM agent: {str(e)}")
            return None
    
    def _create_tool_agent(self, agent_config: Dict[str, Any]) -> Optional[ToolAgent]:
        """
        Create a tool agent.
        
        Args:
            agent_config: Agent configuration
            
        Returns:
            Created tool agent
        """
        try:
            name = agent_config.get("name", "")
            description = agent_config.get("description", "")
            
            # Get model configuration
            model_config = agent_config.get("model", {})
            model_provider = model_config.get("provider", "")
            model_name = model_config.get("name", "")
            
            if not model_provider or not model_name:
                logger.error("Model provider and name are required for tool agent")
                return None
            
            # Create model instance
            model = self._get_model_instance(model_provider, model_name, model_config)
            if not model:
                logger.error(f"Failed to create model {model_provider}/{model_name}")
                return None
            
            # Get prompt template and system message
            prompt_template = agent_config.get("prompt_template", "")
            system_message = agent_config.get("system_message", "")
            
            # Get tools to use
            tool_refs = agent_config.get("tools", [])
            tools = {}
            
            for tool_ref in tool_refs:
                # Get tool ID
                tool_id = tool_ref.get("id", "")
                if not tool_id:
                    logger.warning("Tool reference without ID, skipping")
                    continue
                
                # Get tool
                tool = component_registry.get(tool_id)
                if not tool:
                    logger.warning(f"Tool not found: {tool_id}, skipping")
                    continue
                
                # Add tool to list
                tools[tool_id] = tool
            
            # Create tool agent
            tool_agent = ToolAgent(
                name=name,
                description=description,
                model=model,
                prompt_template=prompt_template,
                system_message=system_message,
                tools=tools
            )
            
            # Save and return
            component_registry.register(tool_agent)
            return tool_agent
        except Exception as e:
            logger.error(f"Error creating tool agent: {str(e)}")
            return None
    
    def _create_acp_agent(self, agent_config: Dict[str, Any]) -> Optional[ACPAgentComponent]:
        """
        Create an ACP agent.
        
        Args:
            agent_config: Agent configuration
            
        Returns:
            Created ACP agent
        """
        try:
            name = agent_config.get("name", "")
            description = agent_config.get("description", "")
            
            # Get ACP configuration
            acp_config = agent_config.get("acp", {})
            base_url = acp_config.get("base_url", "")
            api_key = acp_config.get("api_key", "")
            version = acp_config.get("version", "v1alpha")
            
            if not base_url:
                logger.error("ACP base_url is required")
                return None
            
            # Create ACP adapter
            try:
                acp_version = ACPVersion(version)
            except ValueError:
                logger.warning(f"Invalid ACP version: {version}, using v1alpha")
                acp_version = ACPVersion.V1_ALPHA
            
            acp_adapter = ACPAdapter(
                base_url=base_url,
                api_key=api_key,
                version=acp_version
            )
            
            # Create ACP agent
            acp_agent = ACPAgentComponent(
                name=name,
                description=description,
                adapter=acp_adapter
            )
            
            # Save and return
            component_registry.register(acp_agent)
            return acp_agent
        except Exception as e:
            logger.error(f"Error creating ACP agent: {str(e)}")
            return None
    
    def _create_mcp_model(self, agent_config: Dict[str, Any]) -> Optional[MCPModelComponent]:
        """
        Create an MCP model component.
        
        Args:
            agent_config: Agent configuration
            
        Returns:
            Created MCP model component
        """
        try:
            name = agent_config.get("name", "")
            description = agent_config.get("description", "")
            
            # Get MCP configuration
            mcp_config = agent_config.get("mcp", {})
            endpoint_url = mcp_config.get("endpoint_url", "")
            api_key = mcp_config.get("api_key", "")
            model_id = mcp_config.get("model_id", "")
            
            if not endpoint_url or not model_id:
                logger.error("MCP endpoint_url and model_id are required")
                return None
            
            # Create MCP adapter
            mcp_adapter = MCPAdapter(
                endpoint_url=endpoint_url,
                api_key=api_key
            )
            
            # Create MCP model component
            mcp_model = MCPModelComponent(
                name=name,
                description=description,
                model_id=model_id,
                adapter=mcp_adapter
            )
            
            # Save and return
            component_registry.register(mcp_model)
            return mcp_model
        except Exception as e:
            logger.error(f"Error creating MCP model: {str(e)}")
            return None
    
    def create_tool(self, tool_config: Dict[str, Any]) -> Optional[Tool]:
        """
        Create a tool component.
        
        Args:
            tool_config: Tool configuration
            
        Returns:
            Created tool component
        """
        tool_type = tool_config.get("tool_type", "")
        provider_type = tool_config.get("provider_type", "internal")
        
        name = tool_config.get("name", "")
        description = tool_config.get("description", "")
        
        if not name:
            logger.error("Tool name is required")
            return None
        
        # Check provider type
        if provider_type == "internal":
            # Create internal tool types
            if tool_type == "function":
                return self._create_function_tool(tool_config)
            elif tool_type == "command":
                return self._create_command_tool(tool_config)
            elif tool_type == "rest":
                return self._create_rest_tool(tool_config)
            else:
                logger.error(f"Unsupported internal tool type: {tool_type}")
                return None
        elif provider_type == "mcp":
            # Create MCP tool
            mcp_tool_type = tool_config.get("mcp_tool_type", "function")
            
            if mcp_tool_type == "retrieval":
                return self._create_mcp_retrieval(tool_config)
            else:
                return self._create_mcp_tool(tool_config)
        else:
            logger.error(f"Unsupported provider type: {provider_type}")
            return None
    
    def _create_function_tool(self, tool_config: Dict[str, Any]) -> Optional[FunctionTool]:
        """
        Create a function-based tool.
        
        Args:
            tool_config: Tool configuration
            
        Returns:
            Created function tool
        """
        try:
            name = tool_config.get("name", "")
            description = tool_config.get("description", "")
            
            # Get function information
            function_module = tool_config.get("function_module", "")
            function_name = tool_config.get("function_name", "")
            
            if not function_module or not function_name:
                logger.error("Function module and name are required for function tool")
                return None
            
            # Import function
            try:
                module = importlib.import_module(function_module)
                function = getattr(module, function_name)
            except (ImportError, AttributeError) as e:
                logger.error(f"Error importing function {function_module}.{function_name}: {str(e)}")
                return None
            
            # Create function tool
            function_tool = FunctionTool(
                func=function,
                name=name,
                description=description
            )
            
            # Save and return
            component_registry.register(function_tool)
            return function_tool
        except Exception as e:
            logger.error(f"Error creating function tool: {str(e)}")
            return None
    
    def _create_command_tool(self, tool_config: Dict[str, Any]) -> Optional[CommandTool]:
        """
        Create a command-line tool.
        
        Args:
            tool_config: Tool configuration
            
        Returns:
            Created command tool
        """
        try:
            name = tool_config.get("name", "")
            description = tool_config.get("description", "")
            
            # Get command information
            command_template = tool_config.get("command_template", "")
            working_dir = tool_config.get("working_dir", None)
            
            if not command_template:
                logger.error("Command template is required for command tool")
                return None
            
            # Create command tool
            command_tool = CommandTool(
                command_template=command_template,
                name=name,
                description=description,
                working_dir=working_dir
            )
            
            # Save and return
            component_registry.register(command_tool)
            return command_tool
        except Exception as e:
            logger.error(f"Error creating command tool: {str(e)}")
            return None
    
    def _create_rest_tool(self, tool_config: Dict[str, Any]) -> Optional[RESTTool]:
        """
        Create a REST API tool.
        
        Args:
            tool_config: Tool configuration
            
        Returns:
            Created REST tool
        """
        try:
            name = tool_config.get("name", "")
            description = tool_config.get("description", "")
            
            # Get API information
            endpoint = tool_config.get("endpoint", "")
            method = tool_config.get("method", "GET")
            headers = tool_config.get("headers", {})
            auth = tool_config.get("auth", None)
            timeout = tool_config.get("timeout", 30)
            
            if not endpoint:
                logger.error("Endpoint is required for REST tool")
                return None
            
            # Create REST tool
            rest_tool = RESTTool(
                endpoint=endpoint,
                method=method,
                name=name,
                description=description,
                headers=headers,
                auth=auth,
                timeout=timeout
            )
            
            # Save and return
            component_registry.register(rest_tool)
            return rest_tool
        except Exception as e:
            logger.error(f"Error creating REST tool: {str(e)}")
            return None
    
    def _create_mcp_tool(self, tool_config: Dict[str, Any]) -> Optional[MCPToolComponent]:
        """
        Create an MCP tool.
        
        Args:
            tool_config: Tool configuration
            
        Returns:
            Created MCP tool
        """
        try:
            name = tool_config.get("name", "")
            description = tool_config.get("description", "")
            
            # Get MCP configuration
            mcp_config = tool_config.get("mcp", {})
            endpoint_url = mcp_config.get("endpoint_url", "")
            api_key = mcp_config.get("api_key", "")
            tool_id = mcp_config.get("tool_id", "")
            mcp_tool_type_str = mcp_config.get("tool_type", "function")
            
            if not endpoint_url or not tool_id:
                logger.error("MCP endpoint_url and tool_id are required")
                return None
            
            # Create MCP adapter
            mcp_adapter = MCPAdapter(
                endpoint_url=endpoint_url,
                api_key=api_key
            )
            
            # Determine tool type
            try:
                mcp_tool_type = MCPToolType(mcp_tool_type_str)
            except ValueError:
                logger.warning(f"Invalid MCP tool type: {mcp_tool_type_str}, using function")
                mcp_tool_type = MCPToolType.FUNCTION
            
            # Create MCP tool component
            mcp_tool = MCPToolComponent(
                name=name,
                description=description,
                tool_id=tool_id,
                tool_type=mcp_tool_type,
                adapter=mcp_adapter
            )
            
            # Save and return
            component_registry.register(mcp_tool)
            return mcp_tool
        except Exception as e:
            logger.error(f"Error creating MCP tool: {str(e)}")
            return None
    
    def _create_mcp_retrieval(self, tool_config: Dict[str, Any]) -> Optional[MCPRetrievalComponent]:
        """
        Create an MCP retrieval tool.
        
        Args:
            tool_config: Tool configuration
            
        Returns:
            Created MCP retrieval tool
        """
        try:
            name = tool_config.get("name", "")
            description = tool_config.get("description", "")
            
            # Get MCP configuration
            mcp_config = tool_config.get("mcp", {})
            endpoint_url = mcp_config.get("endpoint_url", "")
            api_key = mcp_config.get("api_key", "")
            tool_id = mcp_config.get("tool_id", "")
            
            if not endpoint_url or not tool_id:
                logger.error("MCP endpoint_url and tool_id are required")
                return None
            
            # Create MCP adapter
            mcp_adapter = MCPAdapter(
                endpoint_url=endpoint_url,
                api_key=api_key
            )
            
            # Create MCP retrieval component
            mcp_retrieval = MCPRetrievalComponent(
                name=name,
                description=description,
                tool_id=tool_id,
                adapter=mcp_adapter
            )
            
            # Save and return
            component_registry.register(mcp_retrieval)
            return mcp_retrieval
        except Exception as e:
            logger.error(f"Error creating MCP retrieval: {str(e)}")
            return None
    
    def _get_model_instance(self, 
                         model_provider: str, 
                         model_name: str, 
                         model_config: Dict[str, Any]) -> Optional[Any]:
        """
        Create/get model instance.
        
        Args:
            model_provider: Model provider (openai, anthropic, etc.)
            model_name: Model name
            model_config: Model configuration
            
        Returns:
            Model instance
        """
        try:
            # Create model based on provider
            if model_provider == "openai":
                return self._create_openai_model(model_name, model_config)
            elif model_provider == "anthropic":
                return self._create_anthropic_model(model_name, model_config)
            else:
                logger.error(f"Unsupported model provider: {model_provider}")
                return None
        except Exception as e:
            logger.error(f"Error creating model {model_provider}/{model_name}: {str(e)}")
            return None
    
    def _create_openai_model(self, model_name: str, model_config: Dict[str, Any]) -> Optional[Any]:
        """
        Create an OpenAI model instance.
        
        Args:
            model_name: Model name
            model_config: Model configuration
            
        Returns:
            OpenAI model instance
        """
        try:
            from langchain_openai import ChatOpenAI
            
            api_key = model_config.get("api_key", os.environ.get("OPENAI_API_KEY"))
            
            if not api_key:
                logger.error("OpenAI API key is required")
                return None
            
            # Create model
            model = ChatOpenAI(
                model_name=model_name,
                openai_api_key=api_key,
                temperature=model_config.get("temperature", 0.7)
            )
            
            # Add model information
            model.model_info = {
                "provider": "openai",
                "name": model_name
            }
            
            return model
        except ImportError:
            logger.error("langchain_openai package is required for OpenAI models")
            return None
    
    def _create_anthropic_model(self, model_name: str, model_config: Dict[str, Any]) -> Optional[Any]:
        """
        Create an Anthropic model instance.
        
        Args:
            model_name: Model name
            model_config: Model configuration
            
        Returns:
            Anthropic model instance
        """
        try:
            from langchain_anthropic import ChatAnthropic
            
            api_key = model_config.get("api_key", os.environ.get("ANTHROPIC_API_KEY"))
            
            if not api_key:
                logger.error("Anthropic API key is required")
                return None
            
            # Create model
            model = ChatAnthropic(
                model_name=model_name,
                anthropic_api_key=api_key,
                temperature=model_config.get("temperature", 0.7)
            )
            
            # Add model information
            model.model_info = {
                "provider": "anthropic",
                "name": model_name
            }
            
            return model
        except ImportError:
            logger.error("langchain_anthropic package is required for Anthropic models")
            return None
    
    def create_components_from_config(self, config_path: str) -> List[ExtensibleComponent]:
        """
        Create components from configuration file.
        
        Args:
            config_path: Configuration file path
            
        Returns:
            List of created components
        """
        created_components = []
        
        try:
            # Load configuration
            with open(config_path, 'r') as f:
                config = yaml.safe_load(f)
            
            # Create components
            for component_config in config.get("components", []):
                component_type = component_config.get("type", "")
                component = self.create_component(component_type, component_config)
                
                if component:
                    created_components.append(component)
            
            logger.info(f"Created {len(created_components)} components from config: {config_path}")
            return created_components
        except Exception as e:
            logger.error(f"Error creating components from config: {str(e)}")
            return created_components

# Factory singleton object
component_factory = ComponentFactory() 