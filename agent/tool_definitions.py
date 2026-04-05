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
    {
        "name": "get_data_quality_issues",
        "description": (
            "Return all failed data quality checks within the last N days. "
            "Use this when the user asks about data quality, bad data, quality check failures, "
            "or whether the data passed validation."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "days": {
                    "type": "integer",
                    "description": "Number of days to look back.",
                    "minimum": 1,
                    "maximum": 90,
                },
            },
            "required": ["days"],
        },
    },
    {
        "name": "trigger_pipeline_run",
        "description": (
            "Trigger (start) a pipeline run. Inserts a new run record with status 'running'. "
            "Use this when the user explicitly asks to run, rerun, start, or trigger a pipeline."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "pipeline_name": {
                    "type": "string",
                    "enum": ["ingestion", "transformation", "quality_check"],
                    "description": "The name of the pipeline to trigger.",
                },
            },
            "required": ["pipeline_name"],
        },
    },
    {
        "name": "get_run_summary",
        "description": (
            "Get full details of a specific pipeline run, including all task steps "
            "and data quality check results. "
            "Use this when the user provides a run ID and wants to see what happened, "
            "or when you need to investigate a specific run in detail."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "run_id": {
                    "type": "integer",
                    "description": "The numeric ID of the pipeline run to retrieve.",
                },
            },
            "required": ["run_id"],
        },
    },
]