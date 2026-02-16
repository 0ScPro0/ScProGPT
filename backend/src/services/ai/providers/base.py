import re
from typing import Any, Optional

from utils.logger import log


class BaseProvider:
    def __init__(self) -> None:
        self._possibly_models = []
        self.supports_models = []
        self.provider_name = "base"
        self.prefix = "openai/v1"
        self.requires_v1_prefix = False
        self.v1_provider_pattern = rf"^{self.provider_name}/v1(?:/.*)?$"
        self.provider_pattern = rf"^{self.provider_name}(?:/.*)?$"

    @log
    def is_model_supports(self, model: str) -> Optional[str]:
        """
        Check if the model is currently supported.

        Args:
            model: str

        Returns:
            Model or None if model is not supported
        """
        if model in self.supports_models:
            return model
        return None

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

    @log
    def validate_model(self, model: str) -> Optional[str]:
        """
        Validate input model

        Args:
            model: str

        Returns:
            Model name or None if has not been validated
        """
        stripped_model = model.strip("/")
        if stripped_model in self._possibly_models:
            return stripped_model
        return None

    @log
    def set_prefix(self, prefix: str) -> Optional[str]:
        """
        Set current prefix

        Args:
            prefix: str

        Returns:
            Prefix name or None if prefix not possible
        """
        if self.validate_prefix(prefix):
            return prefix
        return None

    @log
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
