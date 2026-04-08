"""Tests for grading utilities."""

import pytest
from grading.utils import (
    normalize_text,
    token_set,
    fuzzy_keyword_match,
    semantic_similarity,
    keyword_group_match,
    calculate_step_penalty,
    calculate_early_bonus,
    calculate_repetition_penalty,
    evaluate_reasoning,
    clamp_score
)


class TestTextProcessing:
    """Test text normalization and tokenization."""

    def test_normalize_text(self):
        """Test text normalization."""
        assert normalize_text("  Hello   World  ") == "hello world"
        assert normalize_text("UPPER CASE") == "upper case"
        assert normalize_text("Multiple   Spaces") == "multiple spaces"

    def test_token_set(self):
        """Test tokenization."""
        tokens = token_set("Hello World 123")
        assert "hello" in tokens
        assert "world" in tokens
        assert "123" in tokens
        assert len(tokens) == 3

    def test_token_set_filters_special_chars(self):
        """Test that special characters are filtered."""
        tokens = token_set("Hello! @World# $123")
        assert "hello" in tokens
        assert "world" in tokens
        assert "123" in tokens
        assert "!" not in tokens
        assert "@" not in tokens


class TestFuzzyMatching:
    """Test fuzzy matching functions."""

    def test_fuzzy_keyword_match_exact(self):
        """Test exact match returns 1.0."""
        score = fuzzy_keyword_match("hello world", ["hello world"])
        assert score == 1.0

    def test_fuzzy_keyword_match_partial(self):
        """Test partial match returns value between 0 and 1."""
        score = fuzzy_keyword_match("hello", ["hello world"])
        assert 0.0 < score < 1.0

    def test_fuzzy_keyword_match_no_match(self):
        """Test no match returns EPS (never 0.0 for competition compliance)."""
        score = fuzzy_keyword_match("foo", ["bar baz"])
        assert score == 0.001

    def test_fuzzy_keyword_match_best_of_multiple(self):
        """Test returns best match from multiple references."""
        score = fuzzy_keyword_match("hello world", [
            "foo bar",
            "hello world test",
            "completely different"
        ])
        assert score > 0.5

    def test_semantic_similarity_identical(self):
        """Test identical text returns high similarity."""
        score = semantic_similarity("hello world", "hello world")
        assert score == 1.0

    def test_semantic_similarity_similar(self):
        """Test similar text returns moderate similarity."""
        score = semantic_similarity("hello world", "world hello")
        assert score > 0.5

    def test_semantic_similarity_different(self):
        """Test different text returns low similarity."""
        score = semantic_similarity("hello world", "foo bar")
        assert score < 0.5

    def test_keyword_group_match(self):
        """Test keyword group matching."""
        groups = {
            "greeting": ["hello", "hi", "hey"],
            "farewell": ["goodbye", "bye", "see you"]
        }
        assert keyword_group_match("hello there", groups) == "greeting"
        assert keyword_group_match("goodbye friend", groups) == "farewell"
        assert keyword_group_match("random text", groups) == ""


class TestPenaltiesAndBonuses:
    """Test penalty and bonus calculations."""

    def test_step_penalty_within_ideal(self):
        """Test minimal penalty when within ideal steps."""
        penalty = calculate_step_penalty(3, 5)
        assert penalty == 0.001  # EPS, never 0.0

    def test_step_penalty_exceeds_ideal(self):
        """Test penalty increases when exceeding ideal steps."""
        penalty1 = calculate_step_penalty(6, 5)
        penalty2 = calculate_step_penalty(10, 5)
        assert penalty1 > 0.0
        assert penalty2 > penalty1

    def test_early_bonus_not_done(self):
        """Test minimal bonus when not done."""
        bonus = calculate_early_bonus(False, 3, 5)
        assert bonus == 0.001  # EPS, never 0.0

    def test_early_bonus_done_early(self):
        """Test bonus when done early."""
        bonus = calculate_early_bonus(True, 3, 5)
        assert bonus > 0.0

    def test_early_bonus_done_late(self):
        """Test minimal bonus when done late."""
        bonus = calculate_early_bonus(True, 6, 5)
        assert bonus == 0.001  # EPS, never 0.0

    def test_repetition_penalty_no_repeats(self):
        """Test minimal penalty with no repeats."""
        penalty = calculate_repetition_penalty("d", ["a", "b", "c"])
        assert penalty == 0.001  # EPS, never 0.0

    def test_repetition_penalty_with_repeats(self):
        """Test penalty when action repeats."""
        penalty = calculate_repetition_penalty("a", ["a", "b", "c"])
        assert penalty > 0.0

    def test_clamp_score(self):
        """Test score clamping to strict (0, 1) — never exactly 0.0 or 1.0."""
        # Scores below 0 should clamp to EPS (0.001)
        assert clamp_score(-0.5) == 0.001
        # Scores in valid range should stay unchanged
        assert clamp_score(0.5) == 0.5
        # Scores above 1 should clamp to 1.0 - EPS (0.999)
        assert clamp_score(1.5) == 0.999
        # Edge cases: exactly 0 and 1 should also be adjusted
        assert clamp_score(0.0) == 0.001
        assert clamp_score(1.0) == 0.999


class TestReasoningEvaluation:
    """Test reasoning quality evaluation."""

    def test_evaluate_reasoning_empty(self):
        """Test empty reasoning gets minimal score (never 0.0)."""
        score = evaluate_reasoning("")
        assert score == 0.001  # EPS, never 0.0

    def test_evaluate_reasoning_short(self):
        """Test very short reasoning gets low score."""
        score = evaluate_reasoning("because")
        assert score < 0.5

    def test_evaluate_reasoning_good(self):
        """Test good reasoning gets decent score."""
        score = evaluate_reasoning(
            "This email is a complaint because the customer expresses "
            "dissatisfaction with the service and requests a resolution."
        )
        assert score > 0.04  # Should get points for length and keywords

    def test_evaluate_reasoning_with_keywords(self):
        """Test reasoning with explanation keywords."""
        score = evaluate_reasoning(
            "I classified this as urgent because it mentions a critical "
            "system failure affecting production."
        )
        assert score > 0.04  # Should get points for keywords and length


class TestDeterminism:
    """Test that all functions are deterministic."""

    def test_fuzzy_match_deterministic(self):
        """Test fuzzy matching is deterministic."""
        text = "hello world test"
        refs = ["hello world", "test case"]
        score1 = fuzzy_keyword_match(text, refs)
        score2 = fuzzy_keyword_match(text, refs)
        assert score1 == score2

    def test_semantic_similarity_deterministic(self):
        """Test semantic similarity is deterministic."""
        score1 = semantic_similarity("hello world", "world hello")
        score2 = semantic_similarity("hello world", "world hello")
        assert score1 == score2

    def test_penalties_deterministic(self):
        """Test penalties are deterministic."""
        history = ["a", "b", "c"]
        penalty1 = calculate_repetition_penalty("a", history)
        penalty2 = calculate_repetition_penalty("a", history)
        assert penalty1 == penalty2
