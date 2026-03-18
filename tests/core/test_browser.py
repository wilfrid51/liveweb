"""Tests for browser.py and action_handlers.py — pure-function surface only (no Playwright required)"""

import pytest
from liveweb_arena.core.browser import BrowserSession, MAX_CONTENT_LENGTH, VIEW_MORE_OVERLAP
from liveweb_arena.core.action_handlers import ACTION_HANDLERS


def _make_session():
    """Create BrowserSession with None context/page for pure-function tests."""
    return BrowserSession(context=None, page=None)


class TestFormatAccessibilityTree:
    """Tests for BrowserSession._format_accessibility_tree"""

    def test_empty_node(self):
        s = _make_session()
        assert s._format_accessibility_tree({}) == ""
        assert s._format_accessibility_tree(None) == ""

    def test_simple_node(self):
        s = _make_session()
        node = {"role": "button", "name": "Submit"}
        result = s._format_accessibility_tree(node)
        assert 'button "Submit"' in result

    def test_node_with_value(self):
        s = _make_session()
        node = {"role": "textbox", "name": "Email", "value": "test@example.com"}
        result = s._format_accessibility_tree(node)
        assert 'textbox "Email" value="test@example.com"' in result

    def test_node_role_only(self):
        s = _make_session()
        node = {"role": "separator"}
        result = s._format_accessibility_tree(node)
        assert result.strip() == "separator"

    def test_nested_children(self):
        s = _make_session()
        node = {
            "role": "navigation",
            "name": "Main",
            "children": [
                {"role": "link", "name": "Home"},
                {"role": "link", "name": "About"},
            ],
        }
        result = s._format_accessibility_tree(node)
        lines = result.split("\n")
        assert len(lines) == 3
        assert 'navigation "Main"' in lines[0]
        assert '  link "Home"' in lines[1]
        assert '  link "About"' in lines[2]

    def test_deep_nesting(self):
        s = _make_session()
        node = {
            "role": "main",
            "children": [
                {
                    "role": "list",
                    "children": [
                        {"role": "listitem", "name": "Item 1"},
                    ],
                },
            ],
        }
        result = s._format_accessibility_tree(node)
        lines = result.split("\n")
        assert lines[0].startswith("main")
        assert lines[1].startswith("  list")
        assert lines[2].startswith("    listitem")

    def test_empty_children_list(self):
        s = _make_session()
        node = {"role": "div", "children": []}
        result = s._format_accessibility_tree(node)
        assert result.strip() == "div"

    def test_missing_role(self):
        s = _make_session()
        node = {"name": "orphan"}
        result = s._format_accessibility_tree(node)
        assert '"orphan"' in result


class TestViewConstants:
    """Verify virtual scroll constants are consistent."""

    def test_view_step_positive(self):
        assert BrowserSession.VIEW_STEP > 0

    def test_view_step_is_content_minus_overlap(self):
        assert BrowserSession.VIEW_STEP == MAX_CONTENT_LENGTH - VIEW_MORE_OVERLAP

    def test_overlap_less_than_content(self):
        assert VIEW_MORE_OVERLAP < MAX_CONTENT_LENGTH


class TestActionHandlers:
    """Tests for action_handlers.py dispatch table."""

    EXPECTED_ACTIONS = {"goto", "click", "type", "press", "scroll", "wait", "click_role", "type_role"}

    def test_all_actions_registered(self):
        assert set(ACTION_HANDLERS.keys()) == self.EXPECTED_ACTIONS

    def test_handlers_are_callable(self):
        for name, handler in ACTION_HANDLERS.items():
            assert callable(handler), f"{name} handler is not callable"

    def test_no_none_handlers(self):
        for name, handler in ACTION_HANDLERS.items():
            assert handler is not None, f"{name} handler is None"
