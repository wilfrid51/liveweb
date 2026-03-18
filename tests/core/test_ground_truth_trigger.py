"""Tests for ground_truth_trigger.py — GT result types and URL pattern triggers"""

import pytest
from liveweb_arena.core.ground_truth_trigger import (
    GroundTruthResult, GTFailureType, UrlPatternTrigger, TriggerConfig,
)


class TestGroundTruthResultFactories:
    """Test factory methods produce correct state."""

    def test_ok(self):
        r = GroundTruthResult.ok("Bitcoin")
        assert r.success is True
        assert r.value == "Bitcoin"
        assert r.error is None
        assert r.retryable is False
        assert r.failure_type is None

    def test_retry(self):
        r = GroundTruthResult.retry("timeout")
        assert r.success is False
        assert r.retryable is True
        assert r.error == "timeout"

    def test_fail(self):
        r = GroundTruthResult.fail("no data")
        assert r.success is False
        assert r.retryable is False
        assert r.failure_type == GTFailureType.DATA_NOT_COLLECTED

    def test_not_collected(self):
        r = GroundTruthResult.not_collected("agent didn't visit")
        assert r.success is False
        assert r.failure_type == GTFailureType.DATA_NOT_COLLECTED
        assert r.is_data_not_collected() is True
        assert r.is_system_error() is False

    def test_system_error(self):
        r = GroundTruthResult.system_error("parsing bug")
        assert r.success is False
        assert r.failure_type == GTFailureType.SYSTEM_ERROR
        assert r.is_system_error() is True
        assert r.is_data_not_collected() is False

    def test_fail_and_not_collected_produce_same_type(self):
        r1 = GroundTruthResult.fail("reason")
        r2 = GroundTruthResult.not_collected("reason")
        assert r1.failure_type == r2.failure_type


class TestUrlPatternTriggerDomain:
    """Domain matching tests."""

    def test_exact_domain_match(self):
        t = UrlPatternTrigger(domains=["taostats.io"])
        assert t.matches("https://taostats.io/subnets") is True

    def test_subdomain_match(self):
        t = UrlPatternTrigger(domains=["taostats.io"])
        assert t.matches("https://www.taostats.io/page") is True

    def test_domain_no_match(self):
        t = UrlPatternTrigger(domains=["taostats.io"])
        assert t.matches("https://coingecko.com/coins") is False

    def test_multiple_domains(self):
        t = UrlPatternTrigger(domains=["coingecko.com", "stooq.com"])
        assert t.matches("https://www.coingecko.com/en") is True
        assert t.matches("https://stooq.com/q/") is True
        assert t.matches("https://other.com") is False

    def test_empty_url(self):
        t = UrlPatternTrigger(domains=["example.com"])
        assert t.matches("") is False

    def test_about_blank(self):
        t = UrlPatternTrigger(domains=["example.com"])
        assert t.matches("about:blank") is False


class TestUrlPatternTriggerPath:
    """Path matching tests."""

    def test_path_contains(self):
        t = UrlPatternTrigger(domains=["stooq.com"], path_contains="/q/d/")
        assert t.matches("https://stooq.com/q/d/?s=aapl.us") is True
        assert t.matches("https://stooq.com/q/?s=aapl.us") is False

    def test_path_without_domain_restriction(self):
        t = UrlPatternTrigger(path_contains="/subnets")
        assert t.matches("https://taostats.io/subnets") is True
        assert t.matches("https://other.io/subnets") is True


class TestUrlPatternTriggerRegex:
    """Regex matching tests."""

    def test_url_regex(self):
        t = UrlPatternTrigger(url_regex=r"stooq\.com/q/d/\?s=\w+")
        assert t.matches("https://stooq.com/q/d/?s=aapl.us") is True
        assert t.matches("https://stooq.com/q/?s=aapl.us") is False

    def test_regex_combined_with_domain(self):
        t = UrlPatternTrigger(domains=["stooq.com"], url_regex=r"/q/d/")
        assert t.matches("https://stooq.com/q/d/?s=aapl") is True
        assert t.matches("https://other.com/q/d/?s=aapl") is False


class TestUrlPatternTriggerContains:
    """Simple substring and normalized contains tests."""

    def test_url_contains(self):
        t = UrlPatternTrigger(url_contains="subnets")
        assert t.matches("https://taostats.io/subnets") is True
        assert t.matches("https://taostats.io/miners") is False

    def test_normalized_plus_encoding(self):
        t = UrlPatternTrigger(url_contains="Hong Kong")
        assert t.matches("https://wttr.in/Hong+Kong") is True

    def test_normalized_percent_encoding(self):
        t = UrlPatternTrigger(url_contains="Hong Kong")
        assert t.matches("https://wttr.in/Hong%20Kong") is True

    def test_normalized_case_insensitive(self):
        t = UrlPatternTrigger(url_contains="bitcoin")
        assert t.matches("https://coingecko.com/en/coins/Bitcoin") is True


class TestUrlPatternTriggerDescription:
    """Description property tests."""

    def test_description_with_domain(self):
        t = UrlPatternTrigger(domains=["taostats.io"])
        assert "taostats.io" in t.description

    def test_description_with_all_options(self):
        t = UrlPatternTrigger(
            domains=["x.com"], path_contains="/api",
            url_regex=r"test", url_contains="foo",
        )
        desc = t.description
        assert "domains" in desc
        assert "path contains" in desc
        assert "regex" in desc
        assert "contains" in desc


class TestTriggerConfig:
    """TriggerConfig wraps a trigger."""

    def test_trigger_config_holds_trigger(self):
        trigger = UrlPatternTrigger(domains=["x.com"])
        config = TriggerConfig(trigger=trigger)
        assert config.trigger is trigger
        assert config.trigger.matches("https://x.com/page") is True
