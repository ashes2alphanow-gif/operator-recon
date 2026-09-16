# Listing copy pass

The engine assembles the listing deterministically from spec fields. This pass
writes those fields. The listing gate then checks them against Amazon's limits
and A2A's claim rules.

---

Write these spec keys for **[TITLE]**:

- `listing_hook` - two sentences maximum. This is all most readers see before
  "read more". Put the reader's problem in it, in his words, not yours. Do not
  open with what the book is. Open with where he is.
- `listing_body` - three short paragraphs. What the book does, how it is
  structured, what reading it is actually like.
- `listing_inside` - five bullet items. Concrete. Page count, unit count, trim
  size, what is in every unit, what is in the back.
- `listing_for` - four bullet items naming real people, not segments.
- `listing_not` - one honest paragraph about what this book does not do. This
  sells better than another promise and it keeps the catalogue defensible.
- `back_cover_hook` - one line for the back cover. Under twelve words.
- `back_cover_copy` - three short paragraphs for the back cover.
- `keywords_seed` - at least ten candidates. The engine rejects any that are
  over 50 characters, duplicated, already fully present in the title, or that
  contain terms KDP disallows in keywords. Give it room to reject.

## Claim rules, not suggestions

Banned outright: guaranteed, cure, heal, passive income, get rich, risk-free,
"proven to", any sentence implying a financial, medical, or safety outcome.

The listing gate fails the build on these, and the reason is not squeamishness.
The FTC's 2026 action concerning Publishing.com was about earnings claims,
refund claims, and testimonial and endorsement practices in exactly this market.
A2A does not go near that line.

No claim about sales, rank, reviews, or endorsements that is not true and
documented in the source ledger.
