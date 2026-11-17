# A2A Command Post — Slice 1 Runbook

**Slice 1 = Recon landing page + email capture + welcome sequence + Field Guide checkout.**

## What's built
| Piece | File | Status |
|---|---|---|
| Landing page | `start/index.html` → served at `/start/` | Built. Live on next merge to `main`. |
| Shared links config | `config.js` | Built. **Empty — needs your values.** |
| In-app hook | STATS tab card → `/start/` | Built. Hidden until config has a value. |
| Welcome sequence (6 emails) | `funnel/recon-welcome-sequence_v01.md` | Written. Needs to be pasted into Kit. |

Every outbound button stays hidden until its value is set in `config.js`. Nothing broken ships.

## To go live (about 30 min, $0)
1. **Kit:** follow the checklist at the bottom of the sequence file. Get the form ID.
2. **Lemon Squeezy:** copy the Field Guide product's checkout/share URL.
3. **Shopify:** copy the Field Guide product URL on ashes2alpha.com.
4. Fill in `config.js`: `KIT_FORM_ID`, `FIELD_GUIDE_LEMON_URL`, `FIELD_GUIDE_SHOPIFY_URL`, `FIELD_GUIDE_PRICE`.
5. Merge to `main`. GitHub Pages serves it.
6. Test from your phone: sign up → redirect banner → email 1 arrives → buy buttons open the right products.

## Routing
- Substack stays a **secondary** channel (field notes link on the page + email 6). Kit owns the list and the automation, since Substack can't run a timed sequence.
- `config.js` is network-first in the service worker, so link changes reach installed apps without a version bump.

## Not in slice 1 (next)
- Email gate on the shareable results card (results card isn't built yet).
- Recon tag → Battlefield Relationships 35-email challenge cross-sell.
- Catalog pages for the six KDP titles + Money toolkit.
- Operator dashboard.
