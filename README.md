
![WhatsApp Image 2025-05-03 at 23 41 29_1700ef67](https://github.com/user-attachments/assets/d2fe88e8-dd01-4435-904b-96693c83000d)




# CoFound.ai - Multi-Agent Software Development System

CoFound.ai is a CLI-based multi-agent system that automates software development processes using LangGraph orchestration. The system coordinates multiple specialized AI agents that work together like a software development team to build applications based on user requirements.

## Key Features

- **Multi-Agent Architecture**: Specialized agents for planning, architecture design, development, testing, review, and documentation
- **LangGraph Orchestration**: Flexible workflow coordination using graph-based orchestration
- **Agent Protocol API**: Standard API integration for agent communication (Agent Protocol compliant)
- **CLI Interface**: Simple command-line interface for interacting with the system
- **Memory Management**: Short-term and long-term vector memory for maintaining context across interactions
- **Tool Integration**: Integration with code generation, testing, and version control tools

## Installation

```bash
# Clone the repository
git clone https://github.com/yourusername/cofoundai.git
cd cofoundai

# Create and activate virtual environment
python -m venv clean_venv
source clean_venv/bin/activate  # Linux/Mac
# OR
clean_venv\Scripts\activate.bat  # Windows

# Install dependencies
pip install -r requirements.txt
```

## Usage

### Basic Usage

```bash
# Start a new project with a description
python -m cofoundai.cli.main "Create a simple TODO list web application with Flask"
```

### Interactive Mode

```bash
# Start in interactive mode
python -m cofoundai.cli.main

# Then use commands:
> develop Create a simple TODO list web application
> status
> help
```

### Running Demo Scripts

CoFound.ai includes several demo scripts to showcase its capabilities:

```bash
# Run agent communication test demo (Windows)
demos\demo_test_agents.bat

# Run CLI demo with a simple calculator application
python -m demos.demo_cofoundai_cli --test --request "Create a simple calculator application"

# Run specific workflow visualization
python -m scripts.visualize_develop_app
```

## Agent Workflow

CoFound.ai implements a dynamic agent workflow system using LangGraph:

1. **Project Request**: User submits a project description
2. **Planning**: Planner agent breaks down the project into tasks
3. **Architecture**: Architect agent designs system components
4. **Development**: Developer agent generates code
5. **Testing**: Tester agent creates and runs tests
6. **Review**: Reviewer agent analyzes code quality
7. **Documentation**: Documenter agent creates documentation

Agents can transfer control to other agents based on task requirements using a handoff mechanism.

## Project Structure

```
cofoundai/
│
├── agents/               # Agent definitions and behaviors
│   ├── planner.py        # Project planning agent
│   ├── architect.py      # Architecture design agent
│   ├── developer.py      # Code development agent
│   ├── tester.py         # Testing agent
│   ├── reviewer.py       # Code review agent
│   └── documentor.py     # Documentation agent
│
├── api/                  # Agent Protocol API implementation
│   └── app.py            # FastAPI Agent Protocol server
│
├── orchestration/        # Agent orchestration and coordination
│   ├── agentic_graph.py  # LangGraph-based agent workflow
│   ├── orchestrator.py   # Main orchestration engine
│   └── workflow.py       # Workflow definitions
│
├── communication/        # Inter-agent communication
│   ├── message_bus.py    # Message transmission system
│   ├── protocol.py       # Agent Protocol adapter
│   └── schemas.py        # Message schemas
│
├── memory/               # Memory systems
│   ├── short_term.py     # Short-term memory
│   ├── long_term.py      # Long-term memory (vector DB)
│   └── project_context.py # Project context
│
├── tools/                # Agent tools
│   ├── code_execution.py # Code execution tool
│   ├── testing_tools.py  # Testing tools
│   ├── version_control.py # Version control (Git) tool
│   └── file_manager.py   # File management
│
├── core/                 # Core system components
│   ├── llm_interface.py  # LLM API integration
│   ├── config_manager.py # Configuration management
│   └── system.py         # System management
│
├── utils/                # Helper functions
│   ├── logger.py         # Logging module
│   ├── prompt_templates.py # Prompt templates
│   └── helpers.py        # Helper functions
│
├── cli/                  # Command line interface
│   ├── main.py           # Main CLI entry point
│   ├── commands.py       # CLI commands
│   └── output_formatter.py # Output formatting
│
├── config/               # Configuration files
│   ├── system_config.yaml # System configurations
│   ├── workflows.yaml     # Workflow definitions
│   └── prompts/          # Prompt files
│
├── tests/                # Test files
│   ├── unit/             # Unit tests
│   └── integration/      # Integration tests
│
├── demos/                # Demo scripts and examples
│   └── demo_cofoundai_cli.py # CLI demo script
│
└── scripts/              # Utility scripts
    └── visualize_develop_app.py # Workflow visualization
```

## Configuration

You can customize the system by modifying the configuration files in the `cofoundai/config/` directory:

- `system_config.yaml`: General system settings, LLM providers, and agent configurations
- `workflows.yaml`: Predefined workflows for different development scenarios

## Development

### Running Tests

```bash
# Run all tests
pytest

# Run specific test categories
pytest cofoundai/tests/unit/
pytest cofoundai/tests/integration/
```

### Adding New Agents

To add a new agent type:

1. Create a new agent class in the `cofoundai/agents/` directory
2. Inherit from the `BaseAgent` class
3. Implement the required methods
4. Register the agent in the configuration

### Agent Protocol Integration

CoFound.ai implements the [Agent Protocol](https://github.com/AI-Engineer-Foundation/agent-protocol) standard for agent communication. This allows:

- Standardized API for agent interaction
- Thread and run management
- State persistence
- Streaming responses

You can access the API through FastAPI endpoints defined in `cofoundai/api/app.py`.

## Troubleshooting

### Common Issues

- **Error: 'return' with value in async generator**: This is fixed in the latest version. The async generator implementation has been corrected.
- **Virtual Environment Activation**: Make sure to activate the correct virtual environment before running scripts.
- **Missing Dependencies**: Run `pip install -r requirements.txt` to ensure all dependencies are installed.
- **Path Issues**: Use absolute paths when running scripts from different directories.

### Logs

Logs are stored in the `logs/` directory:

- `logs/agents/` - Individual agent logs
- `logs/system/` - System-level logs
- `logs/workflows/` - Workflow execution logs

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments

- LangGraph for workflow orchestration
- Agent Protocol for standardized agent communication
- LangChain for LLM integration
- OpenAI and Anthropic for LLM capabilities 
