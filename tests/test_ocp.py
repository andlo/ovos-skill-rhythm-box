"""OCP: "play a rock beat" is taken by the OCP pipeline before padatious,
so the skill answers OCP's search and plays via @ocp_play (#3)."""
import threading
from unittest.mock import MagicMock

import pytest
from ovos_utils.ocp import MediaType, PlaybackType

import rhythmbox_skill as rb


@pytest.fixture(autouse=True)
def _no_entity_autoregister(monkeypatch):
    monkeypatch.setattr(rb.RhythmBox, "_auto_register_entity_files",
                        lambda *a, **k: None, raising=False)


@pytest.mark.parametrize("phrase,pattern,bpm,conf", [
    ("a rock beat", "rock", 120, 100),
    ("a disco beat at 100 bpm", "four_on_the_floor", 100, 100),
    ("the four on the floor beat", "four_on_the_floor", 120, 100),
    ("a beat", "rock", 120, 90),
    ("a drum loop", "rock", 120, 90),
])
def test_search_answers_beats(skill, phrase, pattern, bpm, conf):
    [r] = skill.search_beat(phrase, MediaType.MUSIC)
    assert r.uri == f"/{skill.skill_id}/{pattern}/{bpm}"
    assert r.match_confidence == conf
    assert r.playback == PlaybackType.SKILL
    assert r.media_type == MediaType.MUSIC


@pytest.mark.parametrize("phrase", [
    "beat it",                   # Michael Jackson
    "rock beat by some band",
    "the drums",
    "a rock beat at 500 bpm",    # out of range
    "",
])
def test_search_ignores_other_phrases(skill, phrase):
    assert skill.search_beat(phrase, MediaType.MUSIC) == []


def test_search_danish(skill, monkeypatch):
    monkeypatch.setattr(rb.RhythmBox, "lang", "da-dk", raising=False)
    [r] = skill.search_beat("et rockbeat", MediaType.AUDIO)
    assert r.uri.endswith("/rock/120")


def test_ocp_play_path_through_workshop(skill, monkeypatch):
    started = []
    monkeypatch.setattr(skill, "_start", lambda bpm, p: started.append((p, bpm)))
    skill._playing, skill._paused = threading.Event(), threading.Event()
    skill._OVOSCommonPlaybackSkill__playback_handler = skill.play_beat
    msg = MagicMock()
    msg.data = {"uri": f"/{skill.skill_id}/four_on_the_floor/100"}
    skill._OVOSCommonPlaybackSkill__handle_ocp_play(msg)
    msg.data = {"uri": f"/{skill.skill_id}/nonsense/9999"}
    skill.play_beat(msg)
    assert started == [("four_on_the_floor", 100), ("rock", rb.MAX_BPM)]


def test_stop(skill, monkeypatch):
    monkeypatch.setattr(skill, "play_audio", MagicMock())
    assert skill.stop() is False
    skill._start(120, "rock")
    assert skill.can_stop() is True
    assert skill.stop() is True and not skill._is_running()
