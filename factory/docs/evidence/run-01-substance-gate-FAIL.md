# BUILD HALTED at the substance gate

**A Warrior's Code of Prayer: Forty Days of Prayer for Men Who Work While Others Sleep** did not get past `substance`. Nothing downstream was built.

## Blockers (P0)

### abstract-unit
entry 7 'The Radio Goes Quiet' scores 0.78 concrete markers per 100 words against a lane floor of 1.5

**Fix:** Name the thing. A time, a number, a piece of gear, a decision someone actually made.

### abstract-unit
entry 37 'The Man at the Funeral' scores 0.25 concrete markers per 100 words against a lane floor of 1.5

**Fix:** Name the thing. A time, a number, a piece of gear, a decision someone actually made.

## Also found

- **P1** `filler` 1 filler phrases present
- **P2** `repeated-opening` 'that is the...' opens 17 sentences
- **P2** `repeated-opening` 'it is the...' opens 14 sentences
- **P2** `repeated-opening` 'it is a...' opens 13 sentences
- **P2** `repeated-opening` 'there is a...' opens 10 sentences
- **P2** `repeated-opening` 'that is a...' opens 10 sentences

## Measurements

```
{
  "total_words": 16171,
  "units": 40,
  "concrete_density_per_100w": 1.79,
  "sentence_mean_words": 11.81,
  "sentence_stdev": 7.76,
  "filler_hits": 1,
  "paragraphs": 365,
  "near_duplicate_pairs": 0,
  "near_duplicate_ratio": 0.0
}
```

Fix the blockers and run the build again. The engine does not have a flag to publish past this.
