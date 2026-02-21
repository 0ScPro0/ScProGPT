import yaml
from pathlib import Path

BASE_DIR = Path(__file__).parent  # ai


def load_models(provider: str) -> dict:
    """Load model configuration from YAML file."""
    config_path = BASE_DIR / f"{provider}.yaml"
    with open(config_path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)
