# RhythmBox

A simple drum-machine/rhythm-box skill for OVOS - loop a basic beat pattern (rock, four-on-the-floor, etc) at a chosen tempo, using short bundled percussion samples. More involved than the metronome: needs a small sample library and a pattern-sequencing loop, not just a fixed click.

> **This is a skeleton only - not implemented yet.** Repo, structure,
> and design notes are in place; the actual skill logic hasn't been
> written. See "Design notes" in [DEVELOPMENT.md](DEVELOPMENT.md).

## Why this exists

Nothing like this exists in the OVOS ecosystem yet (checked before starting). Needs real design work before implementation: which patterns, how many samples, how looping/stopping works on the bus - flagged as the next one to design properly, following the same review-before-build process as ovos-skill-convert.

## Planned usage (not yet functional)
```
"play a rock beat at 100 bpm"
"start a drum loop"
"stop the beat"
```

## Install

Not yet published to PyPI.

## Development

See [DEVELOPMENT.md](DEVELOPMENT.md).

## Category
**Entertainment**

## Tags
#music #drums #rhythm #beat
