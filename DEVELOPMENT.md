# Development

## Setup
```bash
git clone https://github.com/andlo/ovos-skill-rhythm-box.git
cd ovos-skill-rhythm-box
python3 -m venv .venv && source .venv/bin/activate
pip install -e .
pip install -r requirements-test.txt
```

## Running tests
```bash
pytest tests/ -v
```
Real threads with real short `time.sleep()` calls, not mocked timing -
`test_rhythm_box.py` starts an actual sequencer loop at a fast tempo
for a fraction of a second and checks the real sequence of instrument
hits (including that multiple instruments genuinely fire on a shared
step), not just the pattern-lookup logic in isolation.

## Regenerating the drum sounds
```bash
python3 scripts/generate_drums.py
```
Overwrites `sounds/{kick,snare,hihat_closed,hihat_open}.wav`. All are
generated (pitch-swept sine for the kick, tone+noise mix for the
snare, filtered-feeling noise bursts for the hi-hats) - see the
script for the exact synthesis. Nothing to source or license. Tweak
duration/decay/frequency directly in the script for a different kit
character.

## Adding a new pattern

1. Check the tracked issues first - [#1](https://github.com/andlo/ovos-skill-rhythm-box/issues/1)
   (swing/shuffle) and [#2](https://github.com/andlo/ovos-skill-rhythm-box/issues/2)
   (funk/latin/half-time) already have open design notes for the
   most-requested additions.
2. Add the hit-pattern to `PATTERNS` in `__init__.py` - a dict of
   `{instrument: [step indices 0-7]}`. Reuses the existing 4 samples
   if possible; only add a new sample if the pattern genuinely needs
   a sound none of the existing 4 can stand in for.
3. Add the spoken name(s) to `locale/en-us/rhythm_aliases.json` first,
   then the Danish equivalent in `locale/da-dk/rhythm_aliases.json` -
   **as a structural translation, not a literal one**. Danish
   drum/genre terminology is lower-confidence territory than the
   da-dk work in `ovos-skill-convert` (no equivalent "false-friend"
   research has been done here yet) - if a literal translation feels
   forced or uncertain, it's fine to just use the English/loanword
   term (as `disco`/`rock` already do) rather than inventing a
   translation nobody actually says.
4. If the new pattern needs different TIMING (not just a different
   hit-pattern on the existing straight-eighth grid - see issue #1 for
   why swing needs this), that's a bigger change to `_step_loop()`,
   not just a `PATTERNS` entry - flag it for review before
   implementing rather than quietly hacking the grid.
5. Add a `test_resolve_pattern_*` case per language and a
   `test_*_pattern_step_*` case confirming the actual hit sequence
   from a real (short) timed run, same style as the existing rock/
   four-on-the-floor tests. Confirm `pytest tests/ -v` still passes.

## Live bus testing

Same discipline as the rest of the OVOS projects here:
- One utterance per script run.
- `time.sleep(6-10)` after sending, to give the skill time to respond.
- `time.sleep(30-60)` between separate test runs.
- Test device: `ovos@192.168.65.43` (systemd/venv install).
- Listen for whether simultaneous hits (kick+hihat on beat 1) actually
  sound layered or cut each other off - see README's "simultaneous
  hits" caveat. This is real backend-dependent behavior worth
  confirming on the actual target device, not just assuming from the
  test suite (which only checks that both `play_audio()` calls
  happened, not how the audio backend handled them).

## Versioning

`version.py` follows `VERSION_MAJOR.VERSION_MINOR.VERSION_BUILD[aVERSION_ALPHA]`.
Stays on **0.0.x** until at least one more pattern (swing or the
funk/latin/half-time set) has shipped.

## Releasing

Releases are tag-triggered (`v*`):
```bash
git add version.py
git commit -m "chore: bump version to 0.0.X"
git tag vX.Y.Z
git push && git push --tags
```
Triggers `.github/workflows/test.yml` then `.github/workflows/publish.yml`
(PyPI via trusted publishing - see `ovos-skill-convert`'s
DEVELOPMENT.md for the one-time PyPI setup needed before the first
tagged release).

## Style / conventions

- License: GPL-3.0-or-later (matches the other `andlo` skill repos).
- `locale/<lang-code>/` layout, `skill.json` inside each locale folder.
- Category-grouped-free alias JSON (`rhythm_aliases.json`) - same
  JSON-in-locale pattern as `ovos-skill-convert`'s `unit_aliases.json`
  and `ovos-skill-sound-like`'s `sound_aliases.json`.
- Present design changes (new patterns, timing-model changes) for
  review before implementing.
