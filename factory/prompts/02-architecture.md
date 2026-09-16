# Architecture pass

Turns a decision into `factory/specs/<slug>.yml`. The structure gate reads what
you write here, so write it to survive that.

---

Produce the spec YAML. Required keys: `title`, `subtitle`, `lane`, `reader`,
`reader_problem`, `promise`, `transformation`, `units`.

## The unit list is the book

Every unit needs:
- `title` - what it is called, no colons, no cleverness that hides the subject
- `thesis` - one sentence stating what the reader can do after it
- `anchor` - optional, for devotional lanes

Rules the structure gate enforces:
- Unit count has to sit inside the lane's band.
- No two units may argue the same thing. The gate measures overlap between
  title-plus-thesis pairs and fails the build on a match. If two units overlap,
  one of them is a section inside the other.
- A thesis under six words is too vague to write against and gets flagged.

## Also fill in

- `trim`, `paper`, `ink` if you are overriding the lane default
- `list_price` - the engine checks it against the printing-cost floor
- `keywords_seed` - at least ten candidates, because the engine will reject some
- `categories` - three KDP browse paths
- `compliance.ai_origin` - `ai-generated`, `ai-assisted`, or `none` for text,
  images, and translation. This is what gets answered at KDP upload.
- `sources` and `claims` - mandatory in the doctrine and technical lanes
- `stories` - every story gets a provenance: first-hand, composite, or sourced

## Before you hand it over

Run `./factory/a2a validate factory/specs/<slug>.yml`. Then run
`./factory/a2a build` and read what the structure gate says. Fix the spec, not
the gate.
