import json
import sys
import os
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def _make_tool_use_response(tool_name: str, tool_input: dict, tool_use_id: str = "tu_abc123"):
    tool_block = SimpleNamespace(
        type="tool_use",
        id=tool_use_id,
        name=tool_name,
        input=tool_input,
        model_dump=lambda: {
            "type": "tool_use",
            "id": tool_use_id,
            "name": tool_name,
            "input": tool_input,
        },
    )
    return SimpleNamespace(
        stop_reason="tool_use",
        content=[tool_block],
    )

def _make_text_response(text: str):
    text_block = SimpleNamespace(
        type="text",
        text=text,
        model_dump=lambda: {"type": "text", "text": text},
    )
    return SimpleNamespace(
        stop_reason="end_turn",
        content=[text_block],
    )

def test_natural_language_query_triggers_correct_tool_and_returns_response():
    fake_db_result = {
        "days": 7,
        "total_failed": 2,
        "runs": [
            {
                "id": 3,
                "pipeline_name": "ingestion",
                "status": "failed",
                "start_time": "2024-01-10T08:00:00",
                "end_time": "2024-01-10T08:05:00",
                "rows_processed": 0,
                "error_message": "Connection timeout",
            },
        ],
    }

    final_answer = (
        "There were 2 failed pipeline runs in the last 7 days. "
        "The most recent failure was the ingestion pipeline on Jan 10 due to a connection timeout."
    )

    mock_claude_responses = [
        _make_tool_use_response("get_failed_runs", {"days": 7}),
        _make_text_response(final_answer),
    ]
    call_count = 0

    def fake_create(**kwargs):
        nonlocal call_count
        response = mock_claude_responses[call_count]
        call_count += 1
        return response

    mock_client = MagicMock()
    mock_client.messages.create.side_effect = fake_create

    mock_tool = MagicMock(return_value=fake_db_result)

    with patch.dict(os.environ, {"ANTHROPIC_API_KEY": "sk-test-dummy"}), \
         patch("agent.agent.anthropic.Anthropic", return_value=mock_client), \
         patch.dict("agent.tools.TOOL_DISPATCH", {"get_failed_runs": mock_tool}):

        from agent.agent import run_agent
        response_text, history = run_agent(
            user_message="Show me all failed runs in the last 7 days",
            conversation_history=[],
        )

    # Verify Claude was called twice 
    assert call_count == 2, f"Expected 2 Claude API calls, got {call_count}"

    # Verify the correct tool was called with the correct argument
    mock_tool.assert_called_once_with(days=7)

    # Verify the final response is meaningful text
    assert isinstance(response_text, str)
    assert len(response_text) > 0
    assert response_text == final_answer

    # Verify conversation history was built correctly
    assert len(history) == 4
    assert history[0]["role"] == "user"
    assert history[1]["role"] == "assistant"
    assert history[2]["role"] == "user"

    # The tool_result message must contain our DB result
    tool_result_content = history[2]["content"]
    assert isinstance(tool_result_content, list)
    assert tool_result_content[0]["type"] == "tool_result"
    result_payload = json.loads(tool_result_content[0]["content"])
    assert result_payload["total_failed"] == 2
    assert result_payload["days"] == 7