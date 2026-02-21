import yaml


def load_models(provider: str) -> dict:
    """Load model configuration from YAML file."""
    config_path = f"core\\ai\\{provider}.yaml"
    with open(config_path, "r") as f:
        return yaml.safe_load(f)
