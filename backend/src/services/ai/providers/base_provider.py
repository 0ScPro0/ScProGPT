from typing import AsyncGenerator, Dict, List, Optional, Union
from abc import ABC, abstractmethod
import re

from utils.logger import log
from schemas.ai import ProviderResponse, AssistantMessage, UserMessage


Message = Union[AssistantMessage, UserMessage]


class BaseProvider(ABC):
    def __init__(self) -> None:
        self._available_models: Dict[str, str] = {}
        self.supported_models: List[str] = []
        self.provider_name: str = "base"
        self.prefix: str = "openai/v1"
        self.requires_v1_prefix: bool = False
        self.v1_provider_pattern: str = rf"^{self.provider_name}/v1(?:/.*)?$"
        self.provider_pattern: str = rf"^{self.provider_name}(?:/.*)?$"

    @abstractmethod
    async def generate_text(
        self, messages: list, model: str, **kwargs
    ) -> ProviderResponse:
        pass

    @abstractmethod
    async def generate_stream(
        self, messages: list, model: str, **kwargs
    ) -> AsyncGenerator:
        pass

    async def is_model_supports(self, model: str) -> bool:
        """
        Check if the model is currently supported.

        Args:
            model: str

        Returns:
            True or False if model is not supported
        """
        if model in self.supported_models:
            return True
        return False

    async def get_supported_models(self) -> List[str]:
        """
        Get list of currently supported models.

        Returns:
            List of supported model names
        """
        return self.supported_models.copy()

    @log
    async def add_supports_model(self, model: str) -> bool:
        """
        Add model to supported

        Args:
            model: str

        Returns:
            True or False if model not available
        """
        if self.validate_model(model):
            self.supported_models.append(model)
            return True
        return False

    async def validate_model(self, model: str) -> Optional[str]:
        """
        Validate input model

        Args:
            model: str

        Returns:
            Model name or None if has not been validated
        """
        stripped_model = model.strip("/")

        # Check in supported_models list (flat list of model names)
        if stripped_model in self.supported_models:
            return stripped_model

        return None

    @log
    async def set_prefix(self, prefix: str) -> Optional[str]:
        """
        Set new prefix

        Args:
            prefix: str

        Returns:
            Prefix name or None if prefix not available
        """
        if self.validate_prefix(prefix):
            return prefix
        return None

    async def validate_prefix(self, prefix: Optional[str] = None) -> Optional[str]:
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
            return stripped_prefix

        return None
