"""Tests for TaskRegistry — deterministic task_id mapping."""

import pytest
from liveweb_arena.core.task_registry import TaskRegistry, parse_task_id, max_task_id


class TestParseTaskId:
    """Test parse_task_id determinism and boundary conditions."""

    def test_deterministic_same_result(self):
        """Same task_id always produces identical config."""
        c1 = parse_task_id(1)
        c2 = parse_task_id(1)
        assert c1 == c2

    def test_task_id_1_is_valid(self):
        config = parse_task_id(1)
        assert config["task_id"] == 1
        assert config["combo_index"] == 0
        assert config["variation_seed"] == 0
        assert len(config["templates"]) >= 1

    def test_max_task_id_is_valid(self):
        max_id = max_task_id()
        config = parse_task_id(max_id)
        assert config["task_id"] == max_id

    def test_task_id_0_raises(self):
        with pytest.raises(ValueError, match="must be >= 1"):
            parse_task_id(0)

    def test_task_id_exceeds_max_raises(self):
        with pytest.raises(ValueError, match="out of range"):
            parse_task_id(max_task_id() + 1)

    def test_negative_task_id_raises(self):
        with pytest.raises(ValueError, match="must be >= 1"):
            parse_task_id(-1)

    def test_combo_index_increments_every_10000(self):
        c1 = parse_task_id(1)
        c2 = parse_task_id(10001)
        assert c1["combo_index"] == 0
        assert c2["combo_index"] == 1
        assert c1["template_ids"] != c2["template_ids"]

    def test_variation_seed_cycles_within_combo(self):
        c1 = parse_task_id(1)       # variation_seed = 0
        c2 = parse_task_id(5000)    # variation_seed = 4999
        c3 = parse_task_id(10000)   # variation_seed = 9999
        assert c1["combo_index"] == c2["combo_index"] == c3["combo_index"]
        assert c1["variation_seed"] == 0
        assert c2["variation_seed"] == 4999
        assert c3["variation_seed"] == 9999


class TestNumTasks:
    """Test num_tasks derivation from variation_seed."""

    def test_num_tasks_range(self):
        """num_tasks should be 2, 3, or 4."""
        seen = set()
        for tid in range(1, 100):
            config = parse_task_id(tid)
            assert 2 <= config["num_tasks"] <= 4
            seen.add(config["num_tasks"])
        assert seen == {2, 3, 4}

    def test_num_tasks_formula(self):
        """num_tasks = (variation_seed % 3) + 2."""
        for tid in [1, 2, 3, 4, 5, 6]:
            config = parse_task_id(tid)
            expected = (config["variation_seed"] % 3) + 2
            assert config["num_tasks"] == expected


class TestTemplateConfig:
    """Test template configuration consistency."""

    def test_templates_are_valid_tuples(self):
        config = parse_task_id(1)
        for plugin, template_name in config["templates"]:
            assert isinstance(plugin, str)
            assert isinstance(template_name, str)

    def test_all_template_ids_exist(self):
        """Every template_id in combinations references a real template."""
        TaskRegistry._ensure_initialized()
        for combo in TaskRegistry._combinations:
            for tid in combo:
                assert tid in TaskRegistry.TEMPLATES, f"Template ID {tid} not in TEMPLATES"


class TestVersionOrdering:
    """Test that version ordering is stable."""

    def test_v1_combos_come_first(self):
        """First combo should use only Version 1 template IDs."""
        TaskRegistry._ensure_initialized()
        v1_ids = set(TaskRegistry.TEMPLATE_VERSIONS[0])
        first_combo = TaskRegistry._combinations[0]
        assert all(tid in v1_ids for tid in first_combo)

    def test_later_versions_come_after(self):
        """Combos with Version 2+ IDs should appear after all V1-only combos."""
        TaskRegistry._ensure_initialized()
        v1_ids = set(TaskRegistry.TEMPLATE_VERSIONS[0])
        found_non_v1 = False
        for combo in TaskRegistry._combinations:
            has_non_v1 = any(tid not in v1_ids for tid in combo)
            if has_non_v1:
                found_non_v1 = True
            elif found_non_v1:
                # Found a V1-only combo after a non-V1 combo — ordering broken
                pytest.fail(f"V1-only combo {combo} found after non-V1 combos")

    def test_combo_count_is_stable(self):
        """Combo count should be deterministic."""
        TaskRegistry._initialized = False
        TaskRegistry.rebuild_combinations()
        count1 = len(TaskRegistry._combinations)
        TaskRegistry._initialized = False
        TaskRegistry.rebuild_combinations()
        count2 = len(TaskRegistry._combinations)
        assert count1 == count2


class TestExclusions:
    """Test registry version exclusion filtering."""

    def test_v2_excludes_weather(self):
        """In v2, weather template IDs (1-6) and hybrid_cross_domain_calc (59) should not appear."""
        TaskRegistry._ensure_initialized()
        from liveweb_arena.core.task_registry import ACTIVE_REGISTRY_VERSION, _VERSION_EXCLUSIONS
        excluded = _VERSION_EXCLUSIONS.get(ACTIVE_REGISTRY_VERSION, set())
        if not excluded:
            pytest.skip("Active registry version has no exclusions")
        for combo in TaskRegistry._combinations:
            for tid in combo:
                assert tid not in excluded, f"Excluded template {tid} found in combo {combo}"

    def test_exclusions_reduce_combo_count(self):
        """Exclusions should reduce the number of combinations."""
        from liveweb_arena.core.task_registry import _VERSION_EXCLUSIONS
        v1_excluded = _VERSION_EXCLUSIONS.get("v1", set())
        v2_excluded = _VERSION_EXCLUSIONS.get("v2", set())
        # v2 has more exclusions than v1
        assert len(v2_excluded) > len(v1_excluded)


class TestGetStats:
    """Test get_stats returns expected structure."""

    def test_stats_keys(self):
        stats = TaskRegistry.get_stats()
        assert "num_templates" in stats
        assert "num_combinations" in stats
        assert "max_task_id" in stats
        assert "combinations_by_size" in stats
        assert stats["num_templates"] == len(TaskRegistry.TEMPLATES)
        assert stats["max_task_id"] == stats["num_combinations"] * TaskRegistry.TASK_IDS_PER_COMBO
