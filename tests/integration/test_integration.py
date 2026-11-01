"""
Integration tests for the Code Review Assistant
using the Google ADK evaluation framework.
"""

import pytest

from google.adk.evaluation.agent_evaluator import AgentEvaluator


@pytest.mark.asyncio
async def test_add_function_review():
    """Test code review of a simple add function."""

    await AgentEvaluator.evaluate(
        agent_module="code_review_assistant",
        eval_dataset_file_path_or_dir=(
            "tests/integration/test_add_function_review.test.json"
        )
    )


@pytest.mark.asyncio
async def test_style_violations():
    """Test detection of Python style violations."""

    await AgentEvaluator.evaluate(
        agent_module="code_review_assistant",
        eval_dataset_file_path_or_dir=(
            "tests/integration/style_violations.test.json"
        )
    )


@pytest.mark.asyncio
async def test_all_integration_tests():
    """Run all evaluation datasets in the integration directory."""

    await AgentEvaluator.evaluate(
        agent_module="code_review_assistant",
        eval_dataset_file_path_or_dir="tests/integration/"
    )