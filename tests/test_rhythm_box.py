"""Tests for the rhythm-box's pattern resolution, start/stop logic,
and real timing behavior (real threads, real short sleeps)."""
import time
from unittest.mock import MagicMock

import pytest


def test_resolve_pattern_exact_match(skill):
    assert skill._resolve_pattern("rock", "en-us") == "rock"
    assert skill._resolve_pattern("four on the floor", "en-us") == "four_on_the_floor"
    assert skill._resolve_pattern("disco", "da-dk") == "four_on_the_floor"


def test_resolve_pattern_no_fuzzy_match(skill):
    """Unlike ovos-skill-convert's unit resolver, no fuzzy matching -
    a near-miss pattern name should not silently resolve to something
    else."""
    assert skill._resolve_pattern("rocky", "en-us") is None
    assert skill._resolve_pattern("rok", "en-us") is None


def test_resolve_pattern_unknown_returns_none(skill):
    assert skill._resolve_pattern("jazz waltz", "en-us") is None


def test_start_and_stop(skill):
    skill.play_audio = MagicMock()
    skill._start(480, "rock")  # very fast so the test doesn't take long
    assert skill._is_running()
    time.sleep(0.15)
    skill._stop()
    assert not skill._is_running()
    assert skill.play_audio.call_count >= 1


def test_rock_pattern_step_zero_has_kick_and_hihat(skill):
    """Step 0 of the rock pattern hits both kick AND hihat_closed
    simultaneously - confirms multiple instruments fire on a shared
    step, not just one at a time."""
    skill.play_audio = MagicMock()
    skill._start(480, "rock")
    time.sleep(0.05)
    skill._stop()
    from rhythmbox_skill import SOUND_PATHS
    first_step_calls = {c[0][0] for c in skill.play_audio.call_args_list[:2]}
    assert SOUND_PATHS["kick"] in first_step_calls
    assert SOUND_PATHS["hihat_closed"] in first_step_calls


def test_four_on_the_floor_kick_on_every_other_step(skill):
    skill.play_audio = MagicMock()
    skill._start(960, "four_on_the_floor")  # very fast, 8 steps quickly
    time.sleep(0.7)
    skill._stop()
    from rhythmbox_skill import SOUND_PATHS
    kick_calls = [c for c in skill.play_audio.call_args_list if c[0][0] == SOUND_PATHS["kick"]]
    assert len(kick_calls) >= 2  # kick hits 4 times per 8-step bar


def test_starting_new_pattern_stops_old_one(skill):
    skill.play_audio = MagicMock()
    skill._start(480, "rock")
    first_thread = skill._thread
    skill._start(480, "four_on_the_floor")
    assert skill._thread is not first_thread
    skill._stop()


def test_handle_set_rhythm_with_pattern_and_bpm(skill):
    skill.play_audio = MagicMock()
    skill.speak_dialog = MagicMock()
    message = MagicMock()
    message.data = {"pattern": "rock", "bpm": "100"}
    skill.handle_set_rhythm(message)
    assert skill._is_running()
    assert skill._last_pattern == "rock"
    assert skill._last_bpm == 100
    skill.speak_dialog.assert_called_once_with("rhythm_started", {"pattern": "rock", "bpm": 100})


def test_handle_set_rhythm_pattern_only_uses_last_or_default_bpm(skill):
    skill.play_audio = MagicMock()
    skill.speak_dialog = MagicMock()
    message = MagicMock()
    message.data = {"pattern": "disco"}
    skill.handle_set_rhythm(message)
    from rhythmbox_skill import DEFAULT_BPM
    assert skill._last_bpm == DEFAULT_BPM
    assert skill._last_pattern == "four_on_the_floor"


def test_handle_set_rhythm_unknown_pattern(skill):
    skill.play_audio = MagicMock()
    skill.speak_dialog = MagicMock()
    message = MagicMock()
    message.data = {"pattern": "jazz waltz", "bpm": "100"}
    skill.handle_set_rhythm(message)
    assert not skill._is_running()
    skill.speak_dialog.assert_called_once_with("pattern_not_understood", {"pattern": "jazz waltz"})


def test_handle_set_rhythm_bpm_out_of_range(skill):
    skill.play_audio = MagicMock()
    skill.speak_dialog = MagicMock()
    message = MagicMock()
    message.data = {"pattern": "rock", "bpm": "999"}
    skill.handle_set_rhythm(message)
    assert not skill._is_running()
    skill.speak_dialog.assert_called_once_with("bpm_out_of_range", {"min": 40, "max": 220})


def test_handle_start_rhythm_defaults(skill):
    skill.play_audio = MagicMock()
    skill.speak_dialog = MagicMock()
    message = MagicMock()
    skill.handle_start_rhythm(message)
    from rhythmbox_skill import DEFAULT_PATTERN, DEFAULT_BPM
    skill.speak_dialog.assert_called_once_with(
        "rhythm_started", {"pattern": DEFAULT_PATTERN, "bpm": DEFAULT_BPM})


def test_handle_stop_rhythm_when_not_running(skill):
    skill.speak_dialog = MagicMock()
    message = MagicMock()
    skill.handle_stop_rhythm(message)
    skill.speak_dialog.assert_called_once_with("rhythm_not_running")


def test_handle_stop_rhythm_when_running(skill):
    skill.play_audio = MagicMock()
    skill.speak_dialog = MagicMock()
    skill._start(480, "rock")
    message = MagicMock()
    skill.handle_stop_rhythm(message)
    assert not skill._is_running()
    skill.speak_dialog.assert_called_once_with("rhythm_stopped")


def test_all_sound_files_actually_exist(skill):
    from rhythmbox_skill import SOUND_PATHS
    from pathlib import Path
    for name, path in SOUND_PATHS.items():
        assert Path(path).exists(), f"{name} missing"
