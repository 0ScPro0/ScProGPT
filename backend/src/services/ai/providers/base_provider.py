from typing import Any, Dict, List, Optional
from abc import ABC, abstractmethod
import re

from utils.logger import log


class BaseProvider(ABC):
    def __init__(self) -> None:
        self._available_models: Dict[str, str] = {}
        self.supports_models: List[str] = []
        self.provider_name: str = "base"
        self.prefix: str = "openai/v1"
        self.requires_v1_prefix: bool = False
        self.v1_provider_pattern: str = rf"^{self.provider_name}/v1(?:/.*)?$"
        self.provider_pattern: str = rf"^{self.provider_name}(?:/.*)?$"

    def is_model_supports(self, model: str) -> bool:
        """
        Check if the model is currently supported.

        Args:
            model: str

        Returns:
            True or False if model is not supported
        """
        if model in self.supports_models:
            return True
        return False

    def get_supports_models(self) -> List[str]:
        """
        Get list of currently supported models.

        Returns:
            List of supported model names
        """
        return self.supports_models.copy()

    @log
    def add_supports_model(self, model: str) -> Optional[str]:
        """
        Add model to supported

        Args:
            model: str

        Returns:
            Model name or None if model not possible
        """
        if self.validate_model(model):
            self.supports_models.append(model)
            return model
        return None

    def validate_model(self, model: str) -> Optional[str]:
        """
        Validate input model

        Args:
            model: str

        Returns:
            Model name or None if has not been validated
        """
        stripped_model = model.strip("/")
        if stripped_model in self._available_models:
            return stripped_model
        return None

    @log
    def set_prefix(self, prefix: str) -> Optional[str]:
        """
        Set new prefix

        Args:
            prefix: str

        Returns:
            Prefix name or None if prefix not possible
        """
        if self.validate_prefix(prefix):
            return prefix
        return None

    def validate_prefix(self, prefix: Optional[str] = None) -> Optional[str]:
        """
        Validate input prefix
        If prefix not assigned, takes current prefix to validate

        Args:
            prefix: Optional[str]

        Returns:
            Validated prefix or None if validation failed
        """
        target_prefix = prefix if prefix is not None else self.prefix

        if not target_prefix or not isinstance(target_prefix, str):
            return None

        # Strip
        stripped_prefix = target_prefix.strip("/")

        # Pattern
        pattern = (
            self.provider_pattern
            if not self.requires_v1_prefix
            else self.v1_provider_pattern
        )

        # Validate
        if re.match(pattern, stripped_prefix):
            return target_prefix

        return None
