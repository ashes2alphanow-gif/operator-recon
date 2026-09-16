# A2A Publishing Factory

An engine that turns one title spec into a print-ready Amazon KDP package, and
refuses to finish when the book is not good enough to publish.

It is not a book generator. Generation is the commodity part. What is scarce is
a production line that can tell the difference between a book and 30,000 words
of padding, and that stops when it finds the second one.

## The line

```
G0  intake        resolve the spec, freeze the inputs
G1  blueprint     architecture, word budgets, page and money estimate
    GATE          structure    - overlapping units, impossible page count
G3  manuscript    assemble authored units into a typed block stream
    GATE          substance    - thin, padded, repetitive, abstract, placeholders
G5  interior      print-ready PDF, margins converged against the real page count
    GATE          interior     - measured from the file: trim, parity, embedded
                                 fonts, and whether it holds the approved text
G7  cover         wrap at the exact trim, bleed and spine for the FINAL count
    GATE          cover        - geometry recomputed from the interior, measured
                                 from the written file
G9  listing       title, subtitle, description, 7 keywords, 3 categories, price
    GATE          listing      - Amazon limits, claim language, price floor
G11 compliance    claim / source / story / AI-origin / decision ledgers
    GATE          compliance   - evidence the lane requires
G13 package       manifest, hashes, upload checklist
    STOP          a human signs APPROVAL_REQUIRED.md. There is no publish flag.
```

Every stage writes real files to `output/<slug>/`. Every gate reads those files
back off disk. No stage approves its own work, and the tool that measures a PDF
(`pdfinspect.py`) deliberately does not import the library that wrote it.

A gate that finds a P0 stops the build and writes `BUILD_HALTED.md`. There is no
flag to publish past it. `--keep-going` exists for diagnostics and it still
refuses to call the result finished.

## Run it

```bash
pip install -r factory/requirements.txt          # reportlab, PyYAML
./factory/a2a validate factory/specs/<title>.yml # check a spec, build nothing
./factory/a2a build    factory/specs/<title>.yml # the whole line
./factory/a2a quote --pages 220 --trim 6x9 --paper cream   # page math and money
python3 factory/tests/test_factory.py            # 25 regression tests
```

If the manuscript files do not exist yet, the build writes one authoring pack
per missing unit into `output/<slug>/02_manuscript/authoring/` and stops. Work
the packs, save the files, run it again.

## The four lanes

A lane is a risk-and-structure profile, not a genre. It sets the evidence
burden, the required sections in every unit, and which gates are advisory.

| lane | what is in it | claim risk | review required |
| --- | --- | --- | --- |
| `doctrine` | FORGED, Battlefield Relationships, Smarter Than You Think | elevated | developmental edit |
| `technical` | Money Manual, Survival Is a Decision | high | licensed professional |
| `practice` | The Healing Games, journals, workbooks | elevated | clinician if trauma or grief |
| `devotional` | A Warrior's Code of Prayer, Unbreakable | low | scripture licensing |

## What is locked

- The byline. `Chris G. Stewart`, in `spec.py`. A spec that asks for another
  name fails validation.
- The imprint. `Ashes to Alpha`.
- Print arithmetic. Spine width, trim, bleed, margins, printing cost and the
  royalty floor all come from a dated table in `factory/rates/`. Any band the
  table marks unverified refuses to produce a price at all.
- No brand mark is stamped on a cover automatically. The engine ships a
  typographic wrap and an art brief with the exact geometry. Art direction is a
  human decision.

## Layout

```
factory/
  a2a                  entrypoint
  a2a_factory/
    kdp.py             every countable thing about a physical book
    spec.py            the single input, and what makes one invalid
    lanes.py           the four lane profiles
    typography.py      house type, one place
    textmetrics.py     the measurements the gates run on
    pdfinspect.py      independent PDF reader, no reportlab
    promptpack.py      authoring prompts and the voice contract
    pipeline.py        the line, and the halt logic
    stages/            producers
    gates/             approvers
  prompts/             human-facing prompt packs
  rates/               dated KDP rate tables
  specs/               title specs (the input)
  manuscripts/         authored units (the content)
  tests/               regression suite and the padded fixture
  docs/                blueprint, competitor teardown, catalogue, run report
output/<slug>/         everything a build produced
```
