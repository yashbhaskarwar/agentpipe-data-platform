from typing import Any

TOOL_DEFINITIONS: list[dict[str, Any]] = [
    {
        "name": "get_pipeline_status",
        "description": (
            "Get the latest execution status for a named pipeline. "
            "Optionally filter to a specific date. "
            "Use this when the user asks about the current or recent status of a pipeline, "
            "or asks what happened to a pipeline 'last night', 'today', etc."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "pipeline_name": {
                    "type": "string",
                    "enum": ["ingestion", "transformation", "quality_check"],
                    "description": "The name of the pipeline to check.",
                },
                "date": {
                    "type": "string",
                    "description": (
                        "Optional ISO date string (YYYY-MM-DD) to filter runs to a specific day. "
                        "Omit to get the most recent run regardless of date."
                    ),
                },
            },
            "required": ["pipeline_name"],
        },
    },
    {
        "name": "get_failed_runs",
        "description": (
            "Return all pipeline runs that failed within the last N days. "
            "Use this when the user asks about failures, errors, or broken pipelines "
            "over a time window."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "days": {
                    "type": "integer",
                    "description": (
                        "Number of days to look back. "
                        "For example, 7 returns failures in the past week."
                    ),
                    "minimum": 1,
                    "maximum": 90,
                },
            },
            "required": ["days"],
        },
    },
]