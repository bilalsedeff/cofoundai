"""
CoFound.ai Message Class

This module defines the message structure used for agent communication.
"""

from typing import Dict, Any, Optional, Union, List
from datetime import datetime


class MessageContent:
    """
    Class that represents the content of messages sent between agents.
    """
    
    def __init__(self, text: str, data: Optional[Dict[str, Any]] = None):
        """
        Initialize message content.
        
        Args:
            text: Text content of the message
            data: Structured data associated with the message (default: None)
        """
        self.text = text
        self.data = data or {}
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert message content to dictionary format.
        
        Returns:
            Dictionary representation of the message content
        """
        return {
            "text": self.text,
            "data": self.data
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'MessageContent':
        """
        Create a MessageContent object from dictionary data.
        
        Args:
            data: Dictionary representing message content
            
        Returns:
            Created MessageContent object
        """
        return cls(
            text=data.get("text", ""),
            data=data.get("data", {})
        )
    
    def __str__(self) -> str:
        """
        Return a string representation of the message content.
        
        Returns:
            String with message content information
        """
        return f"MessageContent(text={self.text[:50]}{'...' if len(self.text) > 50 else ''}, data_keys={list(self.data.keys())})"


class Message:
    """
    Class that represents messages sent between agents.
    """
    
    def __init__(self, sender: str, recipient: str, content: Union[str, MessageContent], 
                 metadata: Optional[Dict[str, Any]] = None,
                 message_id: Optional[str] = None,
                 timestamp: Optional[float] = None):
        """
        Initialize a message.
        
        Args:
            sender: Identifier of the agent sending the message
            recipient: Identifier of the agent receiving the message
            content: Message content (string or MessageContent object)
            metadata: Additional information about the message (default: None)
            message_id: Unique identifier for the message (default: None, will be auto-generated)
            timestamp: Message creation time (default: None, current time will be used)
        """
        self.sender = sender
        self.recipient = recipient
        self.content = content if isinstance(content, MessageContent) else MessageContent(text=content)
        self.metadata = metadata or {}
        self.message_id = message_id or self._generate_id()
        self.timestamp = timestamp or datetime.now().timestamp()
        
    def _generate_id(self) -> str:
        """
        Generate a unique identifier for the message.
        
        Returns:
            Unique message ID
        """
        import uuid
        return str(uuid.uuid4())
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert message to dictionary format.
        
        Returns:
            Dictionary representation of the message
        """
        return {
            "message_id": self.message_id,
            "sender": self.sender,
            "recipient": self.recipient,
            "content": self.content.to_dict() if isinstance(self.content, MessageContent) else {"text": self.content, "data": {}},
            "metadata": self.metadata,
            "timestamp": self.timestamp
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Message':
        """
        Create a Message object from dictionary data.
        
        Args:
            data: Dictionary representing a message
            
        Returns:
            Created Message object
        """
        content_data = data.get("content", {})
        content = (
            MessageContent.from_dict(content_data) 
            if isinstance(content_data, dict) else 
            MessageContent(text=str(content_data))
        )
        
        return cls(
            sender=data["sender"],
            recipient=data["recipient"],
            content=content,
            metadata=data.get("metadata", {}),
            message_id=data.get("message_id"),
            timestamp=data.get("timestamp")
        )
    
    def is_response_to(self, other_message: 'Message') -> bool:
        """
        Check if this message is a response to another message.
        
        Args:
            other_message: Message to check against
            
        Returns:
            True if this message is a response to the other message, False otherwise
        """
        return (self.recipient == other_message.sender and 
                self.sender == other_message.recipient and
                self.metadata.get("in_response_to") == other_message.message_id)
    
    def create_response(self, content: Union[str, MessageContent], metadata: Optional[Dict[str, Any]] = None) -> 'Message':
        """
        Create a response message to this message.
        
        Args:
            content: Content of the response message
            metadata: Metadata for the response message (default: None)
            
        Returns:
            Created response message
        """
        response_metadata = metadata or {}
        response_metadata["in_response_to"] = self.message_id
        
        return Message(
            sender=self.recipient,
            recipient=self.sender,
            content=content,
            metadata=response_metadata
        )
    
    def __str__(self) -> str:
        """
        Return a string representation of the message.
        
        Returns:
            String with message information
        """
        content_text = self.content.text if isinstance(self.content, MessageContent) else str(self.content)
        return f"Message(id={self.message_id}, sender={self.sender}, recipient={self.recipient}, content={content_text[:50]}{'...' if len(content_text) > 50 else ''})" 