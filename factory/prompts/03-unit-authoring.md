# Unit authoring pass

The engine generates one of these per unit automatically, filled in with that
unit's title, thesis and word target, whenever a manuscript file is missing.
Look in `output/<slug>/02_manuscript/authoring/`.

The generator lives in `factory/a2a_factory/promptpack.py`. The voice contract
is in that file, in one place, so a change to the voice changes every future
authoring pack at once. Do not copy the contract into a chat and edit it there.

## What the generated pack contains

- The exact file path to save to
- The unit's thesis and the reader it is for
- The word target and the floor the substance gate will enforce
- The sections this lane requires in every unit
- The A2A markdown dialect
- The voice contract
- The checks to run before handing it back

## The markdown dialect

```
# Unit Title
> anchor line here -- Source
Opening paragraph.

## THE DRILL
What the reader does.

::: prayer
The closing lines.
:::
```

`[[lines:8]]` renders eight ruled write-lines. `---` is an ornamental break.
