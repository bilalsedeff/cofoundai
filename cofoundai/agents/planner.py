"""
CoFound.ai Planner Agent

This module defines an AI agent that plans the software development process.
The planner agent breaks the user's request into sub-tasks,
creates workflows, and assigns appropriate agents.
"""

from typing import Dict, List, Any
from cofoundai.core.base_agent import BaseAgent
from cofoundai.communication.message import Message


class PlannerAgent(BaseAgent):
    """
    AI agent that plans and coordinates the software development process.
    """

    def __init__(self, config: Dict[str, Any]):
        """
        Initialize the planner agent.
        
        Args:
            config: Dictionary containing the agent's configuration settings
        """
        super().__init__(config)
        self.name = config.get("name", "Planner")
        self.description = config.get("description", "Agent that plans and coordinates software development tasks")
        self.current_plan = None
        
    def process(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process input data and create a project plan.
        
        Args:
            input_data: Input data including project requirements
            
        Returns:
            Output data including project plan
        """
        # Extract project description
        project_description = input_data.get("project_description", "")
        
        # Create a project plan
        plan = self.create_project_plan(project_description)
        
        # Determine tasks for the first phase
        first_phase = plan["phases"][0]["name"] if plan["phases"] else "Design"
        task_assignments = self.assign_tasks(first_phase)
        
        return {
            "status": "success",
            "message": f"Project plan created for '{project_description}'",
            "plan": plan,
            "first_phase": first_phase,
            "task_assignments": task_assignments
        }
    
    def create_project_plan(self, requirements: str) -> Dict[str, Any]:
        """
        Create a project plan based on user requirements.
        
        Args:
            requirements: User's project requirements
            
        Returns:
            Dictionary containing the project plan
        """
        # Here, an LLM would create a project plan from user requirements
        project_plan = {
            "title": "Project Plan",
            "phases": [
                {
                    "name": "Design",
                    "tasks": ["Architecture design", "API design", "Data model design"]
                },
                {
                    "name": "Development",
                    "tasks": ["Infrastructure development", "Core modules", "Integration"]
                },
                {
                    "name": "Testing",
                    "tasks": ["Unit tests", "Integration tests", "Functional tests"]
                },
                {
                    "name": "Documentation",
                    "tasks": ["API documentation", "User guide", "Installation instructions"]
                }
            ]
        }
        
        self.current_plan = project_plan
        return project_plan
    
    def assign_tasks(self, phase_name: str) -> List[Dict[str, Any]]:
        """
        Assign tasks from a specific project phase to appropriate agents.
        
        Args:
            phase_name: Name of the project phase to assign tasks from
            
        Returns:
            List of task assignments with agent information
        """
        # Extract tasks from plan and assign to agents
        task_assignments = []
        
        # Sample task assignments
        if self.current_plan:
            for phase in self.current_plan["phases"]:
                if phase["name"] == phase_name:
                    for task in phase["tasks"]:
                        assigned_agent = self._determine_agent_for_task(task)
                        task_assignments.append({
                            "task": task,
                            "agent": assigned_agent,
                            "status": "Assigned"
                        })
        
        return task_assignments
    
    def _determine_agent_for_task(self, task: str) -> str:
        """
        Determine the appropriate agent for a given task.
        
        Args:
            task: The task to assign
            
        Returns:
            Name of the appropriate agent for the task
        """
        # Determine agent based on task type
        if "architecture" in task.lower() or "design" in task.lower():
            return "Architect"
        elif "development" in task.lower() or "coding" in task.lower():
            return "Developer"
        elif "test" in task.lower():
            return "Tester"
        elif "document" in task.lower():
            return "Documentor"
        else:
            return "Developer"  # Default to Developer agent
    
    def process_message(self, message: Message) -> Message:
        """
        Process an incoming message and generate an appropriate response.
        
        Args:
            message: The message object to process
            
        Returns:
            Response message
        """
        # Process message based on content
        if "plan" in message.content.lower():
            plan = self.create_project_plan(message.content)
            return Message(
                sender=self.name,
                recipient=message.sender,
                content=f"Project plan created: {plan['title']}",
                metadata={"plan": plan}
            )
        elif "task" in message.content.lower():
            phase = "Development"  # Default phase
            assignments = self.assign_tasks(phase)
            return Message(
                sender=self.name, 
                recipient=message.sender,
                content=f"Tasks assigned for {phase} phase",
                metadata={"assignments": assignments}
            )
        else:
            # Fall back to the base implementation which will call process()
            return super().process_message(message) 