"""
CoFound.ai Config Loader

This module handles loading configuration data from environment variables,
.env files, and config files (YAML).
"""

import os
import yaml
import logging
from pathlib import Path
from typing import Dict, Any, Optional

# Import dotenv for loading environment variables from .env file
try:
    from dotenv import load_dotenv
    DOTENV_AVAILABLE = True
except ImportError:
    DOTENV_AVAILABLE = False

# Set up logger
logger = logging.getLogger(__name__)

class ConfigLoader:
    """
    Loads and manages configuration from multiple sources.
    
    Hierarchy of config sources (highest priority first):
    1. Environment variables
    2. .env file
    3. Configuration files (YAML)
    4. Default values
    """
    
    def __init__(self):
        """Initialize the config loader."""
        self.config: Dict[str, Any] = {}
        self.env_loaded = False
        self.config_dir = Path(__file__).parent.parent / "config"
        
        # Load .env file if available
        self._load_env()
        
    def _load_env(self) -> None:
        """Load environment variables from .env file."""
        if not DOTENV_AVAILABLE:
            logger.warning("python-dotenv not installed, skipping .env file loading. "
                          "Install with: pip install python-dotenv")
            return
        
        # Try loading from .env file in project root
        project_root = Path(__file__).parent.parent.parent
        env_path = project_root / ".env"
        
        if env_path.exists():
            # Load the .env file
            load_dotenv(dotenv_path=str(env_path))
            self.env_loaded = True
            logger.info(f"Loaded environment variables from {env_path}")
        else:
            logger.info(f"No .env file found at {env_path}")
            
    def load_yaml_config(self, filename: str) -> Dict[str, Any]:
        """
        Load configuration from a YAML file.
        
        Args:
            filename: Name of the YAML file in the config directory
            
        Returns:
            Configuration dictionary
        """
        config_path = self.config_dir / filename
        
        if not config_path.exists():
            logger.warning(f"Config file not found: {config_path}")
            return {}
        
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f)
            logger.debug(f"Loaded configuration from {config_path}")
            return config or {}
        except Exception as e:
            logger.error(f"Error loading config file {config_path}: {str(e)}")
            return {}
    
    def get_env(self, key: str, default: Any = None) -> Any:
        """
        Get value from environment variables.
        
        Args:
            key: Environment variable name
            default: Default value if not found
            
        Returns:
            Value of environment variable or default
        """
        return os.environ.get(key, default)
    
    def get_bool_env(self, key: str, default: bool = False) -> bool:
        """
        Get boolean value from environment variables.
        
        Args:
            key: Environment variable name
            default: Default value if not found
            
        Returns:
            Boolean value of environment variable or default
        """
        value = self.get_env(key, None)
        if value is None:
            return default
            
        # Convert to boolean
        return value.lower() in ("true", "yes", "1", "t", "y")
    
    def is_dummy_test_mode(self, cli_flag: bool = False) -> bool:
        """
        Check if we should use dummy test mode.
        
        Args:
            cli_flag: Was the -dummy-test CLI flag provided
            
        Returns:
            Whether to use dummy test mode
        """
        # CLI flag takes highest priority
        if cli_flag:
            return True
            
        # Then check environment variable
        return self.get_bool_env("DUMMY_TEST_MODE", False)
    
    def get_llm_provider(self) -> str:
        """
        Get the configured LLM provider.
        
        Returns:
            LLM provider name ("openai", "anthropic", or "test")
        """
        return self.get_env("LLM_PROVIDER", "test")
    
    def get_llm_config(self) -> Dict[str, Any]:
        """
        Get LLM configuration based on the provider.
        
        Returns:
            Configuration dictionary for the LLM
        """
        provider = self.get_llm_provider()
        
        if provider == "openai":
            return {
                "api_key": self.get_env("OPENAI_API_KEY"),
                "model_name": self.get_env("OPENAI_MODEL", "gpt-4")
            }
        elif provider == "anthropic":
            return {
                "api_key": self.get_env("ANTHROPIC_API_KEY"),
                "model_name": self.get_env("ANTHROPIC_MODEL", "claude-3-sonnet-20240229")
            }
        else:
            # Default to test mode
            return {
                "model_name": "test-model",
                "responses": {}  # Can be expanded with predefined test responses
            }

# Create a global instance
config_loader = ConfigLoader()