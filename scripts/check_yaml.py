#!/usr/bin/env python
"""
Simple script to validate YAML configuration files against JSON schemas.
"""

import sys
import yaml
import json
import jsonschema
from pathlib import Path

def validate_yaml_against_schema(yaml_file, schema_file):
    """
    Validate a YAML file against a JSON Schema.
    
    Args:
        yaml_file: Path to the YAML file
        schema_file: Path to the JSON Schema file
        
    Returns:
        True if validation is successful, False otherwise
    """
    try:
        # Load YAML file
        with open(yaml_file, 'r', encoding='utf-8') as f:
            yaml_data = yaml.safe_load(f)
        
        # Load JSON Schema
        with open(schema_file, 'r', encoding='utf-8') as f:
            schema = json.load(f)
        
        # Validate
        jsonschema.validate(yaml_data, schema)
        
        return True
    except yaml.YAMLError as e:
        print(f"Error parsing YAML file: {e}")
        return False
    except json.JSONDecodeError as e:
        print(f"Error parsing JSON Schema: {e}")
        return False
    except jsonschema.exceptions.ValidationError as e:
        print(f"Validation error: {e}")
        return False
    except Exception as e:
        print(f"Unexpected error: {e}")
        return False

def main():
    """
    Main entry point.
    """
    # Validate workflows.yaml
    yaml_file = 'cofoundai/config/workflows.yaml'
    schema_file = 'cofoundai/config/schema/workflows_schema.json'
    
    print(f"Validating {yaml_file} against {schema_file}")
    
    if validate_yaml_against_schema(yaml_file, schema_file):
        print("Validation successful! The YAML file conforms to the schema.")
    else:
        print("Validation failed. Please check the errors above.")
        sys.exit(1)

if __name__ == "__main__":
    main() 