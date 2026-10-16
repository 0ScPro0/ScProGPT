"""Tests for `utils.logger` and `utils.serializator`."""

import pytest
from pydantic import BaseModel

from utils.logger import log, log_database_queries  # type: ignore
from utils.serializator import serialize_model_to_json  # type: ignore

# ============================================================
# utils.logger
# ============================================================


@log
async def async_add(a: int, b: int) -> int:
    return a + b


@log
def sync_add(a: int, b: int) -> int:
    return a + b


@log
async def async_fail():
    raise ValueError("boom")


@log
def sync_fail():
    raise ValueError("boom")


@log_database_queries
async def async_query(value: str) -> str:
    return f"result-{value}"


@log_database_queries
def sync_query(value: str) -> str:
    return f"result-{value}"


class TestLogDecorator:
    async def test_async_success(self):
        assert await async_add(2, 3) == 5

    async def test_sync_success(self):
        assert sync_add(2, 3) == 5

    async def test_async_error(self):
        with pytest.raises(ValueError):
            await async_fail()

    async def test_sync_error(self):
        with pytest.raises(ValueError):
            sync_fail()

    async def test_wraps_metadata(self):
        assert async_add.__name__ == "async_add"
        assert sync_add.__name__ == "sync_add"


class TestLogDatabaseQueries:
    async def test_async(self):
        assert await async_query("x") == "result-x"

    async def test_sync(self):
        assert sync_query("x") == "result-x"


# ============================================================
# utils.serializator
# ============================================================


class DummyModel(BaseModel):
    name: str
    value: int


class TestSerializeModelToJson:
    async def test_pydantic_model(self):
        result = await serialize_model_to_json(DummyModel(name="a", value=1))
        assert result.startswith("data: ")
        assert result.endswith("\n\n")
        assert '"name":"a"' in result

    async def test_dict_fallback(self):
        result = await serialize_model_to_json({"name": "a", "value": 1})
        assert result == 'data: {"name": "a", "value": 1}\n\n'

    async def test_object_with_model_dump(self):
        class OnlyDump:
            def model_dump(self):
                return {"x": 2}

        result = await serialize_model_to_json(OnlyDump())
        assert result == 'data: {"x": 2}\n\n'
