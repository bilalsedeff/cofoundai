"""
CoFound.ai Short-Term Memory Implementation

This module implements short-term memory for agent conversation history 
and temporary working memory.
"""

from typing import Dict, List, Optional, Any, Union
import json
import time
from datetime import datetime
from collections import deque

from cofoundai.utils.logger import get_logger

logger = get_logger(__name__)

class ConversationMemory:
    """
    Maintains a conversation history for an agent, with a configurable 
    maximum history size and token counting functionality.
    """
    
    def __init__(
            self, 
            max_messages: int = 50,
            window_size: Optional[int] = None
        ):
        """
        Initialize conversation memory.
        
        Args:
            max_messages: Maximum number of messages to retain
            window_size: Optional sliding window size (in tokens) to limit message history
        """
        self.max_messages = max_messages
        self.window_size = window_size
        self.messages = deque(maxlen=max_messages)
        self.token_count = 0
        logger.info(f"Initialized conversation memory with max_messages={max_messages}")
    
    def add_message(self, message: Dict[str, Any]) -> None:
        """
        Add a message to the conversation history.
        
        Args:
            message: Message to add, containing at minimum 'role' and 'content'
        """
        # Add timestamp if not present
        if 'timestamp' not in message:
            message['timestamp'] = datetime.now().isoformat()
            
        # Approximate token count (4 chars ~= 1 token)
        content_length = len(json.dumps(message))
        token_estimate = content_length // 4
        
        self.messages.append(message)
        self.token_count += token_estimate
        
        # If window size is set, prune old messages to stay under limit
        if self.window_size and self.token_count > self.window_size:
            while self.token_count > self.window_size and len(self.messages) > 0:
                oldest = self.messages.popleft()
                # Subtract tokens for removed message
                oldest_length = len(json.dumps(oldest))
                self.token_count -= oldest_length // 4
        
        logger.debug(f"Added message from {message.get('role')} to conversation memory")
    
    def add_messages(self, messages: List[Dict[str, Any]]) -> None:
        """
        Add multiple messages to the conversation history.
        
        Args:
            messages: List of messages to add
        """
        for message in messages:
            self.add_message(message)
    
    def get_messages(self, last_n: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        Get messages from conversation history.
        
        Args:
            last_n: Optional number of most recent messages to retrieve
            
        Returns:
            List of message dictionaries
        """
        if last_n is None:
            return list(self.messages)
        return list(self.messages)[-last_n:]
    
    def clear(self) -> None:
        """Clear all messages from conversation memory."""
        self.messages.clear()
        self.token_count = 0
        logger.info("Cleared conversation memory")


class WorkingMemory:
    """
    Key-value store for agent working memory with automatic expiration.
    Used for storing temporary data needed during task execution.
    """
    
    def __init__(self, default_ttl: int = 3600):
        """
        Initialize working memory.
        
        Args:
            default_ttl: Default time-to-live in seconds for memory items
        """
        self.default_ttl = default_ttl
        self.store: Dict[str, Dict[str, Any]] = {}
        logger.info(f"Initialized working memory with default_ttl={default_ttl}s")
    
    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        """
        Set a value in working memory.
        
        Args:
            key: Key to store value under
            value: Value to store
            ttl: Optional time-to-live in seconds (uses default_ttl if None)
        """
        expiry = time.time() + (ttl if ttl is not None else self.default_ttl)
        self.store[key] = {
            'value': value,
            'expiry': expiry
        }
        logger.debug(f"Set key '{key}' in working memory")
    
    def get(self, key: str, default: Any = None) -> Any:
        """
        Get a value from working memory.
        
        Args:
            key: Key to retrieve
            default: Default value to return if key not found or expired
            
        Returns:
            The stored value or default
        """
        self._clean_expired()
        
        if key not in self.store:
            return default
        
        return self.store[key]['value']
    
    def delete(self, key: str) -> None:
        """
        Delete a key from working memory.
        
        Args:
            key: Key to delete
        """
        if key in self.store:
            del self.store[key]
            logger.debug(f"Deleted key '{key}' from working memory")
    
    def _clean_expired(self) -> None:
        """Remove expired entries from working memory."""
        now = time.time()
        expired_keys = [k for k, v in self.store.items() if v['expiry'] < now]
        
        for key in expired_keys:
            del self.store[key]
            
        if expired_keys:
            logger.debug(f"Removed {len(expired_keys)} expired keys from working memory")
    
    def clear(self) -> None:
        """Clear all data from working memory."""
        self.store.clear()
        logger.info("Cleared working memory") 