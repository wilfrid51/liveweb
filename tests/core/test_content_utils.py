"""Tests for content_utils.py — page title extraction from accessibility trees and text"""

import pytest
from liveweb_arena.core.content_utils import extract_title_from_content


class TestNoneAndEmpty:
    def test_none_returns_none(self):
        assert extract_title_from_content(None) is None

    def test_empty_string_returns_none(self):
        assert extract_title_from_content("") is None

    def test_whitespace_only_returns_none(self):
        assert extract_title_from_content("   ") is None


class TestWebAreaFormat:
    def test_webarea_simple(self):
        content = 'WebArea "Bitcoin Price Chart"'
        assert extract_title_from_content(content) == "Bitcoin Price Chart"

    def test_root_webarea(self):
        content = 'RootWebArea "CoinGecko Dashboard"'
        assert extract_title_from_content(content) == "CoinGecko Dashboard"

    def test_webarea_strips_site_suffix_pipe(self):
        content = 'WebArea "Bitcoin Price | CoinGecko"'
        assert extract_title_from_content(content) == "Bitcoin Price"

    def test_webarea_strips_site_suffix_dash(self):
        content = 'WebArea "Stooq Quotes - Financial Data"'
        assert extract_title_from_content(content) == "Stooq Quotes"

    def test_webarea_strips_site_suffix_emdash(self):
        content = 'WebArea "Article Title — Medium"'
        assert extract_title_from_content(content) == "Article Title"


class TestDocumentFormat:
    def test_document_role(self):
        content = 'document "Hacker News Top Stories"'
        assert extract_title_from_content(content) == "Hacker News Top Stories"

    def test_document_case_insensitive(self):
        content = 'Document "Page Title Here"'
        assert extract_title_from_content(content) == "Page Title Here"


class TestHeadingFormat:
    def test_heading_role(self):
        content = 'heading "Understanding Web Accessibility"'
        assert extract_title_from_content(content) == "Understanding Web Accessibility"

    def test_heading_too_short_skipped(self):
        # heading with < 5 chars should be skipped
        content = 'heading "Hi"'
        assert extract_title_from_content(content) is None

    def test_heading_exactly_5_chars(self):
        content = 'heading "Hello"'
        assert extract_title_from_content(content) == "Hello"


class TestPriorityOrder:
    def test_webarea_preferred_over_heading(self):
        content = 'WebArea "From WebArea"\nheading "From Heading"'
        assert extract_title_from_content(content) == "From WebArea"

    def test_document_preferred_over_heading(self):
        content = 'document "From Document"\nheading "From Heading"'
        assert extract_title_from_content(content) == "From Document"


class TestPlainTextFallback:
    def test_long_title_line(self):
        content = "\n".join([
            "nav stuff",
            "menu items",
            "login link",
            "home link",
            "This Is a Reasonably Long Article Title That Should Be Found",
        ])
        result = extract_title_from_content(content)
        assert result == "This Is a Reasonably Long Article Title That Should Be Found"

    def test_skips_nav_lines(self):
        content = "\n".join([
            "home page navigation links here for you",
            "about us page with lots of text here",
            "A Valid Title That Should Be Extracted From Content",
        ])
        result = extract_title_from_content(content)
        assert result == "A Valid Title That Should Be Extracted From Content"

    def test_skips_short_lines(self):
        content = "short\nA Proper Article Title That Is Long Enough"
        assert extract_title_from_content(content) == "A Proper Article Title That Is Long Enough"

    def test_skips_url_lines(self):
        content = "example.com/page\nThis Article Has Important Information For You"
        assert extract_title_from_content(content) == "This Article Has Important Information For You"

    def test_no_valid_candidates_returns_none(self):
        content = "ab\ncd\nef\n12345"
        assert extract_title_from_content(content) is None

    def test_quotes_boost_score(self):
        # A line with quotes should score higher than one without (all else equal)
        content = "\n".join([
            'Review: "The Great Gatsby" Stands Test of Time',
        ])
        result = extract_title_from_content(content)
        assert "Great Gatsby" in result
