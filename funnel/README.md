# Recon Funnel — Slice 1 Runbook

**Scope:** Recon landing page → Kit email capture → 6-email sequence → Field Guide checkout → PDF delivered.
This is slice 1 only. Catalog, Money toolkit, the Battlefield Relationships sequence, the dashboard and approval notifications are **not built**.

## Status
| Piece | Where | State |
|---|---|---|
| Landing page | `start/index.html` → `/start/` | Built and tested locally. Not on `main` yet. |
| Links config | `config.js` | **Empty.** Every capture and buy button stays hidden until it's filled. |
| In-app card | STATS tab → `/start/` | Built. Hidden until config has a value. |
| Start new cycle | Settings → archives baseline and retest | Built and tested locally. |
| Welcome sequence | `funnel/recon-welcome-sequence_v02.md` | Written. **Not in Kit yet.** |
| Kit form + automation | Kit | **Not set up.** |
| Checkout + PDF delivery | Lemon Squeezy (primary) | **Not verified.** |

## Go-live steps
1. **Kit:** follow the checklist at the bottom of the sequence file.
2. **Lemon Squeezy:** confirm the Field Guide product delivers **`A2A_OPERATOR_RECON_Field_Guide_v1.1.pdf`**, the newest file in Drive (Nov 13). Older 48-page and "OLD - no links" versions are also in Drive. Make sure the product isn't serving one of those.
3. **Fill `config.js`:** `KIT_FORM_ID`, `FIELD_GUIDE_LEMON_URL`, `FIELD_GUIDE_PRICE`. Shopify URL is optional. Launch with one checkout.
4. Merge this branch to `main`. GitHub Pages serves it.
5. Run the verification below. It's live when every box is checked, not before.

## Verification: the whole path, on your phone
**Signup**
- [ ] `/start/` loads on cellular, not just Wi-Fi.
- [ ] Submit the form with a fresh address you control (Gmail `+recon` alias works).
- [ ] Redirect lands on `/start/?joined=1` and shows "✓ You're on the list."
- [ ] In Kit, that subscriber exists, has tag `recon-lead`, and is **active** in sequence `Recon Briefings`. (The banner proves nothing about this. Check Kit.)
- [ ] Email 1 arrives in the inbox, not spam. Links open the app and the guide section.
- [ ] Kit shows Email 2 scheduled about 3 days out.

**Purchase**
- [ ] Buy button shows the right price and opens the **Field Guide** product, not another one.
- [ ] Complete a real purchase. Use Lemon Squeezy test mode, or a 100%-off code limited to one use, then delete it.
- [ ] Receipt email arrives.
- [ ] Download link delivers the **v1.1** PDF, and it opens on the phone.
- [ ] The order appears in the Lemon Squeezy dashboard.

**App**
- [ ] Installed app shows the Field Guide card on STATS (config is network-first, no reinstall needed).
- [ ] Settings → Start new cycle: previous baseline and retest appear under STATS → Previous cycles.

## Weekly numbers: 5 minutes, no new tools
Every Monday, write three numbers down:
1. **New subscribers.** Kit → Subscribers, filtered by tag `recon-lead`, last 7 days.
2. **Field Guide orders and revenue.** Lemon Squeezy → Orders, last 7 days.
3. **Sequence health.** Kit → Sequence → open and click rate on emails 1 and 6.

There's no page-visit count yet. GitHub Pages has no analytics. Add one only if subscriber numbers raise a question that visits would answer.

## Open items for Chris
- **Brand stylization in the Field Guide.** The PDF says "Ashes 2 Alpha." The site and emails use "Ashes to Alpha," per your call. Fix one or the other before buyers see both.
- **The Field Guide's liability line names Roughset USA.** That puts RSU on an A2A product, against the brand firewall. Confirm it's intended.
- **Approval.** Section 2.2 of the context pack raises the approval question for paid software or memberships. It doesn't set a blanket requirement for every A2A PDF. The Field Guide is a writing product. Your call whether it needs anything.
