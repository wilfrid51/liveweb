"""Tests for parser.py — answer extraction from agent output"""

import pytest
from liveweb_arena.core.parser import AnswerParser


@pytest.fixture
def parser():
    return AnswerParser()


class TestParseJsonAnswers:
    """Tests for JSON-format answer parsing."""

    def test_dict_with_answers_key(self, parser):
        response = {"answers": {"answer1": "Bitcoin", "answer2": "Ethereum"}}
        result = parser.parse_answers(response, 2)
        assert result == {"answer1": "Bitcoin", "answer2": "Ethereum"}

    def test_dict_with_list_answers(self, parser):
        response = {"answers": [{"id": 1, "value": "42"}, {"id": 2, "value": "100"}]}
        result = parser.parse_answers(response, 2)
        assert result == {"answer1": "42", "answer2": "100"}

    def test_direct_answer_keys(self, parser):
        response = {"answer1": "yes", "answer2": "no"}
        result = parser.parse_answers(response, 2)
        assert result == {"answer1": "yes", "answer2": "no"}

    def test_single_answer(self, parser):
        response = {"answers": {"answer1": "42.5"}}
        result = parser.parse_answers(response, 1)
        assert result == {"answer1": "42.5"}

    def test_numeric_values_converted_to_str(self, parser):
        response = {"answers": {"answer1": 42}}
        result = parser.parse_answers(response, 1)
        assert result == {"answer1": "42"}

    def test_none_values_skipped(self, parser):
        response = {"answers": {"answer1": None, "answer2": "yes"}}
        result = parser.parse_answers(response, 2)
        assert result["answer1"] is None
        assert result["answer2"] == "yes"

    def test_extra_keys_ignored(self, parser):
        response = {"answers": {"answer1": "x", "answer5": "y"}}
        result = parser.parse_answers(response, 2)
        assert result == {"answer1": "x", "answer2": None}


class TestParseTagAnswers:
    """Tests for <answerN>...</answerN> tag-based parsing."""

    def test_single_tag(self, parser):
        response = "The answer is <answer1>Bitcoin</answer1>"
        result = parser.parse_answers(response, 1)
        assert result == {"answer1": "Bitcoin"}

    def test_multiple_tags(self, parser):
        response = "<answer1>42</answer1> and <answer2>100</answer2>"
        result = parser.parse_answers(response, 2)
        assert result == {"answer1": "42", "answer2": "100"}

    def test_multiline_content(self, parser):
        response = "<answer1>\nBitcoin\nEthereum\n</answer1>"
        result = parser.parse_answers(response, 1)
        assert result["answer1"] == "Bitcoin\nEthereum"

    def test_whitespace_stripped(self, parser):
        response = "<answer1>  spaced  </answer1>"
        result = parser.parse_answers(response, 1)
        assert result["answer1"] == "spaced"

    def test_case_insensitive(self, parser):
        response = "<ANSWER1>test</ANSWER1>"
        result = parser.parse_answers(response, 1)
        assert result["answer1"] == "test"

    def test_dict_with_final_raw(self, parser):
        response = {"final_raw": "<answer1>from raw</answer1>"}
        result = parser.parse_answers(response, 1)
        assert result["answer1"] == "from raw"


class TestParseNone:
    """Edge cases: None and empty inputs."""

    def test_none_response(self, parser):
        result = parser.parse_answers(None, 2)
        assert result == {"answer1": None, "answer2": None}

    def test_empty_string(self, parser):
        result = parser.parse_answers("", 1)
        assert result == {"answer1": None}

    def test_empty_dict(self, parser):
        result = parser.parse_answers({}, 1)
        assert result == {"answer1": None}

    def test_no_matching_tags(self, parser):
        result = parser.parse_answers("just some text", 1)
        assert result == {"answer1": None}


class TestJsonTakesPrecedence:
    """JSON format should be tried before tags."""

    def test_json_preferred_over_tags(self, parser):
        response = {"answers": {"answer1": "from_json"}}
        result = parser.parse_answers(response, 1)
        assert result["answer1"] == "from_json"


class TestGetOutputFormat:
    """Tests for format detection."""

    def test_json_format(self, parser):
        assert parser.get_output_format({"answers": {"answer1": "x"}}) == "json"

    def test_tag_format(self, parser):
        assert parser.get_output_format("<answer1>x</answer1>") == "fallback_tags"

    def test_none_format(self, parser):
        assert parser.get_output_format(None) == "none"

    def test_empty_string_format(self, parser):
        assert parser.get_output_format("no answers here") == "none"

    def test_dict_with_raw_tags(self, parser):
        assert parser.get_output_format({"final_raw": "<answer1>x</answer1>"}) == "fallback_tags"
