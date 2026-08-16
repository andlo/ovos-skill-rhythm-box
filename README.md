# <img src='icon.png' card_color='#A940DB' width='50' height='50' style='vertical-align:bottom'/> Rhythm Box

A simple drum-machine/rhythm-box for OVOS - loops an 8-step (eighth-
note) beat pattern at a chosen tempo. All 4 drum sounds (kick, snare,
closed hi-hat, open hi-hat) are generated, not recorded - nothing to
source or license (see `scripts/generate_drums.py`). Same timing
philosophy as [ovos-skill-metronome](https://github.com/andlo/ovos-skill-metronome):
a background thread scheduling each step from a fixed accumulator,
extended to a step-sequencer instead of a single click.

[![Tests](https://github.com/andlo/ovos-skill-rhythm-box/actions/workflows/test.yml/badge.svg)](https://github.com/andlo/ovos-skill-rhythm-box/actions/workflows/test.yml)
[![PyPI version](https://img.shields.io/pypi/v/ovos-skill-rhythm-box.svg)](https://pypi.org/project/ovos-skill-rhythm-box/)

> **Early 0.0.x release.** Only 2 patterns (rock, four-on-the-floor)
> for now, deliberately kept small to prove the sequencing engine
> before building a genre library - see "Planned patterns" below.

## Usage
```
"play a rock beat at 100 bpm"
"play a disco beat"
"start a drum loop"
"stop the beat"
"spil et rock beat på 100 bpm"    (Danish)
"stop beatet"                     (Danish)
```

Bare "start a drum loop" resumes the last pattern/tempo used this
session, or a 120 bpm rock beat if nothing has been played yet.
Valid range is 40-220 bpm.

## The two patterns

Both are an 8-step grid (one bar of eighth notes):

| Step | 1 | & | 2 | & | 3 | & | 4 | & |
|---|---|---|---|---|---|---|---|---|
| **Rock**: hi-hat | ● | ● | ● | ● | ● | ● | ● | ● |
| **Rock**: kick | ● | | | | ● | | | |
| **Rock**: snare | | | ● | | | | ● | |
| **Four-on-the-floor**: kick | ● | | ● | | ● | | ● | |
| **Four-on-the-floor**: open hat | | ● | | ● | | ● | | ● |
| **Four-on-the-floor**: snare | | | ● | | | | ● | |

## Planned patterns (tracked as issues, not built yet)

- [Swing/shuffle](https://github.com/andlo/ovos-skill-rhythm-box/issues/1) - needs a different timing model (triplet feel), not just a new hit-pattern on the existing straight-eighth grid.
- [Funk, latin/bossa, half-time](https://github.com/andlo/ovos-skill-rhythm-box/issues/2) - half-time is cheap (reuses the existing 4-sample palette); funk/latin likely need more samples.

## A real caveat: simultaneous hits

Some steps hit more than one instrument at once (kick + hi-hat on
beat 1, for example). Each is sent as a separate `play_audio()` call
in quick succession - this relies on the OVOS audio backend actually
mixing overlapping playback rather than one call cutting off the
previous. Most real setups do mix correctly (PulseAudio/PipeWire-level
mixing), but if a beat sounds thin or clipped on a given deployment,
this is a real, known reason why - not something silently assumed
away.

## Install
```bash
pip install ovos-skill-rhythm-box
```

## Development

See [DEVELOPMENT.md](DEVELOPMENT.md).

## Category
**Entertainment**

## Tags
#music #drums #rhythm #beat
