import json
from pathlib import Path
import pytest

from cofoundai.tools import FileManager


@pytest.fixture()
def file_manager(tmp_path):
    """Return a FileManager instance using a temporary directory."""
    return FileManager(workspace_dir=str(tmp_path))


def test_basic_file_operations(file_manager):
    code_dir = "src/main"
    file_manager.create_directory(code_dir)

    test_code = """def hello_world():\n    print('Hello, CoFound.ai!')\n\nif __name__ == '__main__':\n    hello_world()\n"""
    code_file = f"{code_dir}/app.py"
    file_manager.write_file(code_file, test_code)

    assert file_manager.read_file(code_file) == test_code

    dir_content = file_manager.list_directory(code_dir)
    assert len(dir_content) == 1
    assert dir_content[0]["name"] == "app.py"

    file_manager.delete_file(code_file)
    with pytest.raises(FileNotFoundError):
        file_manager.read_file(code_file)


def test_json_yaml_operations(file_manager):
    config_data = {
        "name": "test-project",
        "version": "1.0.0",
        "description": "Test project for FileManager",
    }
    config_file = "config.json"
    file_manager.write_json(config_file, config_data)
    assert file_manager.read_json(config_file) == config_data

    yaml_data = {
        "app": "test-app",
        "dependencies": ["dep1", "dep2"],
        "settings": {"debug": True, "port": 8080},
    }
    yaml_file = "config.yaml"
    file_manager.write_yaml(yaml_file, yaml_data)
    assert file_manager.read_yaml(yaml_file) == yaml_data


def test_path_safety(file_manager, tmp_path):
    outside_path = tmp_path.parent / "unauthorized.txt"
    with pytest.raises(ValueError):
        file_manager.write_file(outside_path, "Unauthorized content")
