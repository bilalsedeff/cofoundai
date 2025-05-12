"""
Workflow Visualization Script

This script visualizes dynamic LangGraph-based workflows using Graphviz.
It shows the state machine representation including agents, transitions, and conditions.
"""

import os
import sys
import argparse
import json
import logging
from typing import Dict, Any, List, Optional

import networkx as nx
import matplotlib.pyplot as plt
from matplotlib.colors import LinearSegmentedColormap

from cofoundai.orchestration.dynamic_graph import DynamicWorkflow
from cofoundai.agents.langgraph_agent import (
    LangGraphAgent, 
    PlannerLangGraphAgent,
    ArchitectLangGraphAgent,
    DeveloperLangGraphAgent,
    TesterLangGraphAgent,
    ReviewerLangGraphAgent,
    DocumentorLangGraphAgent
)


# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def create_demo_workflow() -> DynamicWorkflow:
    """
    Create a demo workflow for visualization.
    
    Returns:
        Workflow instance
    """
    # Create a workflow
    workflow = DynamicWorkflow({
        "name": "DemoWorkflow",
        "description": "Demo workflow for visualization"
    })
    
    # Create and register agents
    workflow.register_agent(PlannerLangGraphAgent({"name": "Planner"}))
    workflow.register_agent(ArchitectLangGraphAgent({"name": "Architect"}))
    workflow.register_agent(DeveloperLangGraphAgent({"name": "Developer"}))
    workflow.register_agent(TesterLangGraphAgent({"name": "Tester"}))
    workflow.register_agent(ReviewerLangGraphAgent({"name": "Reviewer"}))
    workflow.register_agent(DocumentorLangGraphAgent({"name": "Documentor"}))
    
    return workflow


def visualize_workflow(workflow: DynamicWorkflow, output_path: Optional[str] = None) -> None:
    """
    Visualize a workflow using matplotlib.
    
    Args:
        workflow: Workflow to visualize
        output_path: Path to save the visualization
    """
    # Get the graph schema
    schema = workflow.get_graph_schema()
    
    if isinstance(schema, dict) and schema.get("status") == "error":
        logger.error(f"Failed to get graph schema: {schema.get('message')}")
        return
    
    try:
        # Create a directed graph
        G = nx.DiGraph()
        
        # Add nodes
        for node_name in schema.get("nodes", []):
            G.add_node(node_name)
        
        # Add the END node
        G.add_node("END")
        
        # Add edges from the schema
        for node, edges in schema.get("edges", {}).items():
            for target in edges:
                if target == "__end__":
                    target = "END"
                G.add_edge(node, target)
        
        # Define colors for nodes
        colors = {
            "supervisor": "#FF9E9E",  # Light red
            "Planner": "#A7C7E7",     # Light blue
            "Architect": "#FAD02C",   # Light yellow
            "Developer": "#77DD77",   # Light green
            "Tester": "#FDFD96",      # Light yellow
            "Reviewer": "#FFB347",    # Light orange
            "Documentor": "#CF9FFF",  # Light purple
            "END": "#D3D3D3"          # Light gray
        }
        
        # Get node colors
        node_colors = [colors.get(node, "#FFFFFF") for node in G.nodes()]
        
        # Plot the graph
        plt.figure(figsize=(12, 8))
        pos = nx.spring_layout(G, seed=42)
        nx.draw(
            G, 
            pos, 
            with_labels=True, 
            node_color=node_colors,
            node_size=3000, 
            arrowsize=20, 
            font_size=10,
            font_weight='bold',
            edge_color='gray'
        )
        
        # Set title
        plt.title(f"Workflow: {workflow.name}", fontsize=16)
        
        # Save the plot if an output path is provided
        if output_path:
            plt.savefig(output_path, bbox_inches='tight')
            logger.info(f"Visualization saved to {output_path}")
        
        # Show the plot
        plt.show()
    
    except Exception as e:
        logger.error(f"Error visualizing workflow: {str(e)}")


def get_agents_from_workflow(workflow_name: str) -> List[Dict[str, Any]]:
    """
    Get agent configurations for a specific workflow from configuration.
    
    Args:
        workflow_name: Name of the workflow
        
    Returns:
        List of agent configurations
    """
    try:
        config_path = os.path.join('cofoundai', 'config', 'workflows.yaml')
        
        if not os.path.exists(config_path):
            logger.error(f"Configuration file not found: {config_path}")
            return []
            
        import yaml
        with open(config_path, 'r') as f:
            config = yaml.safe_load(f)
            
        # Get workflow configuration
        if 'workflows' not in config:
            logger.error("No workflows defined in configuration")
            return []
            
        for workflow in config['workflows']:
            if workflow.get('name') == workflow_name:
                return workflow.get('agents', [])
                
        logger.error(f"Workflow not found: {workflow_name}")
        return []
        
    except Exception as e:
        logger.error(f"Error loading workflow configuration: {str(e)}")
        return []


def visualize_agent_interactions(agent_configs: List[Dict[str, Any]], output_path: Optional[str] = None) -> None:
    """
    Visualize agent interactions based on agent configurations.
    
    Args:
        agent_configs: List of agent configurations
        output_path: Path to save the visualization
    """
    try:
        # Create a directed graph
        G = nx.DiGraph()
        
        # Add nodes for each agent
        for agent in agent_configs:
            name = agent.get('name', 'Unknown')
            G.add_node(name)
        
        # Add User node
        G.add_node("User")
        
        # Define interactions based on role
        interactions = {
            "Planner": ["Architect"],
            "Architect": ["Developer"],
            "Developer": ["Tester", "Architect"],
            "Tester": ["Developer", "Reviewer"],
            "Reviewer": ["Developer", "Documentor"],
            "Documentor": ["User"]
        }
        
        # Add edges for interactions
        for source, targets in interactions.items():
            if source in G.nodes():
                for target in targets:
                    if target in G.nodes():
                        G.add_edge(source, target)
        
        # Add edge from User to Planner
        if "User" in G.nodes() and "Planner" in G.nodes():
            G.add_edge("User", "Planner")
        
        # Define colors for nodes
        colors = {
            "User": "#FF9E9E",        # Light red
            "Planner": "#A7C7E7",     # Light blue
            "Architect": "#FAD02C",   # Light yellow
            "Developer": "#77DD77",   # Light green
            "Tester": "#FDFD96",      # Light yellow
            "Reviewer": "#FFB347",    # Light orange
            "Documentor": "#CF9FFF",  # Light purple
        }
        
        # Get node colors
        node_colors = [colors.get(node, "#FFFFFF") for node in G.nodes()]
        
        # Plot the graph
        plt.figure(figsize=(12, 8))
        pos = nx.spring_layout(G, seed=42)
        nx.draw(
            G, 
            pos, 
            with_labels=True, 
            node_color=node_colors,
            node_size=3000, 
            arrowsize=20, 
            font_size=10,
            font_weight='bold',
            edge_color='gray'
        )
        
        # Set title
        plt.title("Agent Interactions", fontsize=16)
        
        # Save the plot if an output path is provided
        if output_path:
            plt.savefig(output_path, bbox_inches='tight')
            logger.info(f"Visualization saved to {output_path}")
        
        # Show the plot
        plt.show()
        
    except Exception as e:
        logger.error(f"Error visualizing agent interactions: {str(e)}")


def main():
    """Main function."""
    parser = argparse.ArgumentParser(description="Visualize CoFound.ai workflows")
    parser.add_argument('--output', '-o', type=str, help='Output file path')
    parser.add_argument('--workflow', '-w', type=str, help='Workflow name to visualize')
    parser.add_argument('--demo', '-d', action='store_true', help='Use demo workflow')
    parser.add_argument('--interactions', '-i', action='store_true', help='Visualize agent interactions only')
    
    args = parser.parse_args()
    
    if args.demo:
        # Create and visualize a demo workflow
        workflow = create_demo_workflow()
        visualize_workflow(workflow, args.output)
    elif args.interactions:
        # Visualize agent interactions
        workflow_name = args.workflow or "develop_app"
        agent_configs = get_agents_from_workflow(workflow_name)
        visualize_agent_interactions(agent_configs, args.output)
    elif args.workflow:
        # Create a workflow based on configuration
        try:
            from cofoundai.orchestration.dynamic_graph import SoftwareDevelopmentWorkflow
            
            workflow = SoftwareDevelopmentWorkflow({
                "name": args.workflow
            })
            
            # Add agents
            agent_configs = get_agents_from_workflow(args.workflow)
            for agent_config in agent_configs:
                agent_type = agent_config.get('type', 'default')
                agent_name = agent_config.get('name', 'Unknown')
                
                # Create an agent based on type
                if agent_type == 'planner':
                    agent = PlannerLangGraphAgent({"name": agent_name})
                elif agent_type == 'architect':
                    agent = ArchitectLangGraphAgent({"name": agent_name})
                elif agent_type == 'developer':
                    agent = DeveloperLangGraphAgent({"name": agent_name})
                elif agent_type == 'tester':
                    agent = TesterLangGraphAgent({"name": agent_name})
                elif agent_type == 'reviewer':
                    agent = ReviewerLangGraphAgent({"name": agent_name})
                elif agent_type == 'documentor':
                    agent = DocumentorLangGraphAgent({"name": agent_name})
                else:
                    agent = LangGraphAgent({"name": agent_name})
                
                # Register the agent
                workflow.register_agent(agent)
                
            # Visualize the workflow
            visualize_workflow(workflow, args.output)
            
        except Exception as e:
            logger.error(f"Error creating workflow: {str(e)}")
    else:
        # No options specified, show help
        parser.print_help()


if __name__ == "__main__":
    main() 