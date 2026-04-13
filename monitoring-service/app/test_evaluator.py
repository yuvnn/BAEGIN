import pytest
from .evaluator import EvaluationResult, evaluate_paper

# Note: This would normally use a mock for the OpenAI API in a real test suite
def test_evaluation_result_schema():
    result = EvaluationResult(is_relevant=True, score=8.5, review="Good paper")
    assert result.is_relevant is True
    assert result.score == 8.5
    assert result.review == "Good paper"
