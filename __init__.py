"""
skill OVOS Rhythm Box
Copyright (C) 2026  Andreas Lorensen

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <http://www.gnu.org/licenses/>.

---

A simple drum-machine/rhythm-box - loops a fixed 8-step (eighth-note)
pattern at a chosen tempo. Same timing philosophy as
ovos-skill-metronome (a background thread scheduling each step from a
fixed accumulator, not naive repeated sleeping), extended from "one
click on a beat grid" to "up to N samples on an 8-step grid".

Deliberately only 2 patterns for this first release - rock and
four-on-the-floor - to prove the sequencing engine works before
building out a genre library. See README/DEVELOPMENT.md and the
tracked GitHub issues for planned additions (swing/shuffle, funk,
latin, half-time).

All 4 drum sounds (kick, snare, hihat_closed, hihat_open) are
generated, not recorded - see scripts/generate_drums.py. Same
rationale as the metronome's clicks: nothing to source or license.

SIMULTANEOUS HITS - A REAL CAVEAT, NOT SILENTLY ASSUMED AWAY
----------------------------------------------------------------
Some steps have more than one instrument hit at once (e.g. kick +
hi-hat on beat 1). Each is sent as a separate play_audio() call in
quick succession - this relies on the underlying OVOS audio backend
actually mixing/overlapping simultaneous playback (which most real
setups do, via PulseAudio/PipeWire-level mixing) rather than one call
cutting off the previous. If a given deployment's audio backend
doesn't overlap, simultaneous hits may audibly cut each other off -
not fixed here, worth knowing before assuming a laggy-sounding beat
is a code bug rather than a backend limitation.
"""

import json
import threading
import time
from pathlib import Path

from ovos_workshop.skills import OVOSSkill
from ovos_workshop.decorators import intent_handler
from ovos_number_parser import extract_number

SKILL_ROOT = Path(__file__).resolve().parent
LOCALE_DIR = SKILL_ROOT / "locale"
SOUNDS_DIR = SKILL_ROOT / "sounds"

STEP_COUNT = 8  # one 4/4 bar of eighth notes

SOUND_PATHS = {
    "kick": str(SOUNDS_DIR / "kick.wav"),
    "snare": str(SOUNDS_DIR / "snare.wav"),
    "hihat_closed": str(SOUNDS_DIR / "hihat_closed.wav"),
    "hihat_open": str(SOUNDS_DIR / "hihat_open.wav"),
}

# pattern name -> {instrument: [step indices (0-7) that instrument hits]}
PATTERNS = {
    "rock": {
        "hihat_closed": [0, 1, 2, 3, 4, 5, 6, 7],
        "kick": [0, 4],
        "snare": [2, 6],
    },
    "four_on_the_floor": {
        "kick": [0, 2, 4, 6],
        "hihat_open": [1, 3, 5, 7],
        "snare": [2, 6],
    },
}

DEFAULT_PATTERN = "rock"
DEFAULT_BPM = 120
MIN_BPM = 40
MAX_BPM = 220


def _load_pattern_aliases_from_disk():
    """Reads locale/<lang>/rhythm_aliases.json - {spoken name: pattern
    key in PATTERNS} - flattened per language. Same JSON-in-locale
    pattern as ovos-skill-convert's unit_aliases.json and
    ovos-skill-sound-like's sound_aliases.json, for consistency and
    ovos-localize compatibility."""
    merged = {}
    if not LOCALE_DIR.is_dir():
        return merged
    for lang_dir in sorted(LOCALE_DIR.iterdir()):
        if not lang_dir.is_dir():
            continue
        alias_file = lang_dir / "rhythm_aliases.json"
        if not alias_file.exists():
            continue
        with open(alias_file, encoding="utf-8") as f:
            aliases = json.load(f)
        lang = lang_dir.name.lower()
        merged[lang] = {k: v for k, v in aliases.items() if not k.startswith("_")}
    return merged


PATTERN_ALIASES = _load_pattern_aliases_from_disk()


class RhythmBox(OVOSSkill):

    def initialize(self):
        self._stop_event = threading.Event()
        self._thread = None
        self._last_bpm = None
        self._last_pattern = None

    def _pattern_aliases_for(self, lang):
        lang = lang.lower()
        return PATTERN_ALIASES.get(lang) or PATTERN_ALIASES.get("en-us", {})

    def _resolve_pattern(self, raw, lang):
        """Exact match only, no fuzzy matching - same reasoning as
        ovos-skill-sound-like: picking a different (but still
        plausible) named object is a much more noticeable wrong
        answer than a slightly-off numeric guess would be."""
        if not raw:
            return None
        return self._pattern_aliases_for(lang).get(raw.strip().lower())

    def _step_loop(self, bpm, pattern_name):
        pattern = PATTERNS[pattern_name]
        step_interval = 60.0 / bpm / 2  # eighth notes = half a quarter-note beat
        step = 0
        next_time = time.monotonic()
        while not self._stop_event.is_set():
            current = step % STEP_COUNT
            for instrument, steps in pattern.items():
                if current in steps:
                    self.play_audio(SOUND_PATHS[instrument], instant=True)
            step += 1
            next_time += step_interval
            sleep_time = next_time - time.monotonic()
            if sleep_time > 0:
                self._stop_event.wait(sleep_time)
            else:
                next_time = time.monotonic()

    def _start(self, bpm, pattern_name):
        self._stop()
        self._last_bpm = bpm
        self._last_pattern = pattern_name
        self._stop_event.clear()
        self._thread = threading.Thread(
            target=self._step_loop, args=(bpm, pattern_name), daemon=True)
        self._thread.start()

    def _stop(self):
        self._stop_event.set()
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=2)
        self._thread = None

    def _is_running(self):
        return self._thread is not None and self._thread.is_alive()

    def shutdown(self):
        self._stop()

    @intent_handler("set_rhythm.intent")
    def handle_set_rhythm(self, message):
        pattern_raw = message.data.get("pattern")
        bpm_raw = message.data.get("bpm")

        pattern_name = None
        if pattern_raw:
            pattern_name = self._resolve_pattern(pattern_raw, self.lang)
            if pattern_name is None:
                self.speak_dialog("pattern_not_understood", {"pattern": pattern_raw})
                return
        pattern_name = pattern_name or self._last_pattern or DEFAULT_PATTERN

        bpm = None
        if bpm_raw:
            bpm = extract_number(bpm_raw, lang=self.lang)
            if bpm is False or bpm is None:
                self.speak_dialog("bpm_not_understood")
                return
            bpm = int(round(bpm))
            if not (MIN_BPM <= bpm <= MAX_BPM):
                self.speak_dialog("bpm_out_of_range", {"min": MIN_BPM, "max": MAX_BPM})
                return
        bpm = bpm or self._last_bpm or DEFAULT_BPM

        self._start(bpm, pattern_name)
        self.speak_dialog("rhythm_started", {"pattern": pattern_raw or pattern_name, "bpm": bpm})

    @intent_handler("start_rhythm.intent")
    def handle_start_rhythm(self, message):
        pattern_name = self._last_pattern or DEFAULT_PATTERN
        bpm = self._last_bpm or DEFAULT_BPM
        self._start(bpm, pattern_name)
        self.speak_dialog("rhythm_started", {"pattern": pattern_name, "bpm": bpm})

    @intent_handler("stop_rhythm.intent")
    def handle_stop_rhythm(self, message):
        if not self._is_running():
            self.speak_dialog("rhythm_not_running")
            return
        self._stop()
        self.speak_dialog("rhythm_stopped")
