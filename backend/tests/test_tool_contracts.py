"""Closed, strict tool contracts keep model arguments away from branch authority."""

import json

import pytest

from backend.app.core.config import AssistantSettings
from backend.app.services.tool_contracts import (
    MAX_PRODUCT_ID,
    MAX_TOOL_ARGUMENT_BYTES,
    GetBranchInfoArguments,
    GetProductPriceArguments,
    RequestHumanHelpArguments,
    SearchFAQArguments,
    ToolCallValidationError,
    get_tool_schemas,
    validate_tool_call,
)

SETTINGS = AssistantSettings(assistant_branch_code="sucursal-uno", _env_file=None)


def test_responses_function_schemas_have_one_closed_allowlist() -> None:
    schemas = get_tool_schemas()
    expected_fields = {
        "get_product_price": set(GetProductPriceArguments.model_fields),
        "get_branch_info": set(GetBranchInfoArguments.model_fields),
        "search_faq": set(SearchFAQArguments.model_fields),
        "request_human_help": set(RequestHumanHelpArguments.model_fields),
    }

    assert {schema["name"] for schema in schemas} == set(expected_fields)
    assert len(schemas) == len(expected_fields)
    for schema in schemas:
        assert set(schema) == {"type", "name", "description", "strict", "parameters"}
        assert schema["type"] == "function"
        assert schema["strict"] is True
        parameters = schema["parameters"]
        assert parameters["type"] == "object"
        assert parameters["additionalProperties"] is False
        assert set(parameters["properties"]) == expected_fields[schema["name"]]
        assert set(parameters["required"]) == expected_fields[schema["name"]]
    serialized = json.dumps(schemas)
    assert "branch_id" not in serialized
    assert "branch_code" not in serialized
    assert "execute_sql" not in serialized
    assert "run_sql" not in serialized


def test_tool_schema_caller_cannot_modify_shared_allowlist() -> None:
    schemas = get_tool_schemas()
    schemas[0]["name"] = "run_sql"
    schemas[1]["parameters"]["properties"]["branch_code"] = {"type": "string"}

    fresh = get_tool_schemas()
    assert fresh[0]["name"] == "get_product_price"
    assert fresh[1]["parameters"]["properties"] == {}


@pytest.mark.parametrize(
    ("name", "payload", "arguments_type"),
    (
        ("get_product_price", {"product_id": 12, "unit": "kg"}, GetProductPriceArguments),
        ("get_branch_info", {}, GetBranchInfoArguments),
        ("search_faq", {"query": "  ¿Tienen entregas?  "}, SearchFAQArguments),
        (
            "request_human_help",
            {"reason": "customer_requested"},
            RequestHumanHelpArguments,
        ),
    ),
)
def test_validated_calls_bind_scope_only_from_backend_settings(
    name: str, payload: dict[str, object], arguments_type: type
) -> None:
    call = validate_tool_call(name, json.dumps(payload), assistant_settings=SETTINGS)

    assert call.name == name
    assert isinstance(call.arguments, arguments_type)
    assert call.branch_scope.branch_code == "sucursal-uno"
    if name == "search_faq":
        assert call.arguments.query == "¿Tienen entregas?"


def test_same_model_arguments_use_only_the_configured_backend_branch() -> None:
    payload = '{"product_id":12,"unit":"kg"}'
    other_settings = AssistantSettings(assistant_branch_code="sucursal-dos", _env_file=None)

    first = validate_tool_call("get_product_price", payload, assistant_settings=SETTINGS)
    second = validate_tool_call("get_product_price", payload, assistant_settings=other_settings)

    assert first.arguments == second.arguments
    assert first.branch_scope.branch_code == "sucursal-uno"
    assert second.branch_scope.branch_code == "sucursal-dos"


@pytest.mark.parametrize("name", ("run_sql", "update_price", "search_product", "GET_BRANCH_INFO"))
def test_unlisted_tool_names_are_rejected(name: str) -> None:
    with pytest.raises(ToolCallValidationError, match="unsupported tool"):
        validate_tool_call(name, "{}", assistant_settings=SETTINGS)


def test_tool_name_is_checked_before_branch_scope_is_bound() -> None:
    with pytest.raises(ToolCallValidationError, match="unsupported tool"):
        validate_tool_call("run_sql", "{}", assistant_settings="otra-sucursal")


@pytest.mark.parametrize(
    ("name", "payload"),
    (
        ("get_product_price", {"product_id": True, "unit": "kg"}),
        ("get_product_price", {"product_id": 1.0, "unit": "kg"}),
        ("get_product_price", {"product_id": 0, "unit": "kg"}),
        ("get_product_price", {"product_id": MAX_PRODUCT_ID + 1, "unit": "kg"}),
        ("get_product_price", {"product_id": 1, "unit": "KG"}),
        ("get_product_price", {"product_id": 1, "unit": " kg"}),
        ("get_product_price", {"product_id": 1, "unit": "kg\n"}),
        ("get_product_price", {"product_id": 1}),
        ("get_product_price", {"product_id": 1, "unit": "kg", "branch_id": 7}),
        ("get_branch_info", {"branch_code": "otra-sucursal"}),
        ("search_faq", {"query": "   "}),
        ("search_faq", {"query": "???"}),
        ("search_faq", {"query": "pregunta\ninyectada"}),
        ("search_faq", {"query": "a" * 241}),
        ("search_faq", {"query": "Horario", "branch_code": "otra-sucursal"}),
        ("request_human_help", {"reason": "transfer_now"}),
        ("request_human_help", {"reason": "customer_requested", "phone": "1234"}),
    ),
)
def test_invalid_or_extra_arguments_are_rejected(name: str, payload: dict[str, object]) -> None:
    with pytest.raises(ToolCallValidationError, match="invalid tool arguments"):
        validate_tool_call(name, json.dumps(payload), assistant_settings=SETTINGS)


@pytest.mark.parametrize(
    "arguments_json",
    (
        '{"product_id":1,"product_id":2,"unit":"kg"}',
        '[{"product_id":1,"unit":"kg"}]',
        '{"product_id":NaN,"unit":"kg"}',
        '{"product_id":1,"unit":"kg"',
        '{"product_id":1,"unit":"\ud800"}',
        "[" * 1000 + "]" * 1000,
    ),
)
def test_malformed_ambiguous_and_nonstandard_json_is_rejected(arguments_json: str) -> None:
    with pytest.raises(ToolCallValidationError, match="invalid tool arguments"):
        validate_tool_call("get_product_price", arguments_json, assistant_settings=SETTINGS)


def test_oversized_arguments_and_untrusted_scope_are_rejected_without_echoing_input() -> None:
    sensitive_marker = "private customer text"
    with pytest.raises(ToolCallValidationError) as oversized:
        validate_tool_call(
            "search_faq",
            json.dumps({"query": sensitive_marker * MAX_TOOL_ARGUMENT_BYTES}),
            assistant_settings=SETTINGS,
        )
    assert sensitive_marker not in str(oversized.value)

    with pytest.raises(ToolCallValidationError, match="trusted branch configuration"):
        validate_tool_call("get_branch_info", "{}", assistant_settings="otra-sucursal")
