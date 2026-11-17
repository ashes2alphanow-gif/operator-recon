# OPERATOR RECON — Welcome Sequence v01
**Platform:** Kit (ConvertKit) → Sequence named `Recon Briefings`
**Trigger:** subscribes via the Recon form on `/start/` (Kit form → auto-add to sequence, tag `recon-lead`)
**Sender:** Chris G. Stewart · Ashes to Alpha
**Length:** 6 emails over ~6 weeks. Timing is from signup, which assumes he starts the program within a few days of signing up. Good enough for v01.

`{{ subscriber.first_name | default: "Brother" }}` is Kit's Liquid. Swap "Brother" if you want a different fallback.

Placeholders to replace before turning the sequence on:
- `[APP_LINK]`: the app URL (GitHub Pages root, or your custom domain)
- `[GUIDE_LINK]`: the `/start/#guide` URL, or the Lemon Squeezy product URL directly
- `[SUBSTACK_LINK]`: https://chrisstewarta2a.substack.com

---

## Email 1 — Send immediately
**Subject:** Week 1. Write the numbers down.
**Preview:** The baseline is the only part of this program you can't redo.

{{ subscriber.first_name | default: "Brother" }},

You signed up. That puts you ahead of everybody still telling himself he'll start Monday.

Here's what matters this week: **the baseline test.** Week 1, Monday. Four events, full rest between each:

- Push-ups, 2 minutes
- Sit-ups, 2 minutes
- Strict pull-ups, one set
- 2-mile run for time

Log every number in the app, even the ugly ones. *Especially* the ugly ones. In six weeks you retest the same four events, and the app puts them side by side. That comparison is the whole point. You can't have it if you skip the first half.

Two rules for test day:

1. **Don't pace yourself to look good.** A soft baseline makes for a fake retest.
2. **Don't hurt yourself proving something.** Stop a set when form breaks, not when your ego does.

Open the app: [APP_LINK]
On iPhone, open it in Safari, then Share → Add to Home Screen. It works offline after that.

Next briefing in a few days: what to do when you miss a day. You will miss a day.

— Chris | Ashes to Alpha

*P.S. If you want the whole program on paper, the Field Guide is here: [GUIDE_LINK]. The app stays free either way.*

---

## Email 2 — Day 3
**Subject:** You're going to miss a day
**Preview:** Here's the rule for when you do.

{{ subscriber.first_name | default: "Brother" }},

Somewhere in the next six weeks a shift runs long, a kid gets sick, or you just don't go. Plan for it now so it doesn't turn into three days, then a week, then "I'll restart next month."

**The rule: miss one, don't miss two.**

- Missed a session? Don't try to make it up by doubling tomorrow. Do tomorrow's session as written.
- Missed two in a row? Do the next session at about 70% and get back on the line.
- Missed a whole week? Repeat that week. Don't jump ahead to stay on the calendar.

The streak counter in the app isn't decoration. It's there because consistency beats intensity in every program anybody has ever finished.

Six weeks isn't long. It only feels long in week 3.

— Chris

---

## Email 3 — Day 10
**Subject:** The knee, the back, the shoulder
**Preview:** Scaling isn't quitting.

{{ subscriber.first_name | default: "Brother" }},

Most of us coming back to this have something. A knee that's been loud since 2014. A back that tells you about the weather. A shoulder you don't talk about.

Here's how to think about it:

- **Pain that's sharp, pinpoint, or gets worse as you go: stop.** That's not a toughness test. Get it looked at by someone qualified.
- **Dull, general, "I haven't done this in years" soreness: normal.** It should ease as you warm up and settle in a day or two.
- **Scale the movement, keep the slot.** Can't run? Ruck, bike or swim the same time block. Can't do pull-ups? Do negatives or band-assisted. The session still counts if you showed up and did honest work.

I'm not your doctor and this email isn't medical advice. If something is actually injured, see a professional and come back when you're cleared. The program will still be here.

What you can't do is use "something hurts" as permission to quit the whole thing when it only means you need to change one movement.

— Chris

---

## Email 4 — Day 15
**Subject:** Week 3 is where it costs something
**Preview:** Phase 2. Build.

{{ subscriber.first_name | default: "Brother" }},

Rebuild is done. You're in **Build** now. Intervals get harder, strength gets heavier, the rucks get longer.

This is the phase where most people quietly fall off, and it's almost never the training that does it. It's what happens between sessions:

- **Sleep.** If you're getting five hours, the program can't work. Log it in the app. Look at the number honestly.
- **Protein.** The app sets a target from your bodyweight. Most men are well short of it. Hit it before you worry about anything fancier.
- **Water.** Same deal. Boring. Works.

You don't need supplements, a new watch, or a better program. You need to sleep, eat, drink water, and show up for the next session.

Halfway point is coming. Check your STATS tab this weekend and look at your compliance number. That's your real score right now.

— Chris

---

## Email 5 — Day 29
**Subject:** Peak. Then you back off.
**Preview:** The taper is part of the program, not a reward.

{{ subscriber.first_name | default: "Brother" }},

Week 5. **Peak** phase. This is the hardest training of the six weeks, and then in week 6 the volume drops on purpose.

Men like us are bad at the taper part. We feel good, so we add work. Don't. The lighter week is when your body catches up to everything you've put it through. Show up to the retest fresh, not fried.

Retest is **Week 6, Friday.** Same four events, same order, same rest as your baseline. Same conditions if you can manage it: same time of day, same route for the run.

Then, if you've got it in you, Saturday is the optional capstone: **5 miles, 45 lb ruck.**
- Sub-75 minutes: operational
- Sub-65: good
- Sub-60: you're back

Ten days. Finish it.

— Chris

---

## Email 6 — Day 40
**Subject:** What did the numbers say?
**Preview:** Baseline vs. retest. And what comes next.

{{ subscriber.first_name | default: "Brother" }},

If you ran the program, you've got your retest numbers by now. Open the STATS tab. Baseline on the left, retest on the right.

Whatever's there is true. Better than you hoped, or not as much as you wanted, it's real data on a man who decided to do something and then did it for six weeks. Most people never get that far.

Hit reply and tell me your numbers. I read these.

**What's next:**

- **Run it again.** Reset the program in the app's settings, make your retest your new baseline, go six more weeks.
- **Get the Field Guide** if you want the program on paper for the next round: [GUIDE_LINK]
- **Keep reading.** I write field notes on discipline, fatherhood and carrying weight that isn't in a ruck: [SUBSTACK_LINK]

Stay on the line.

— Chris | Ashes to Alpha

---

## Kit setup checklist (do once)
1. Kit → Grow → Landing Pages & Forms → **Create form** → Inline. Name: `Recon — Start Page`.
2. Form settings → Incentive: off (no double opt-in for v01), or on if you want confirmed emails only. Your call.
3. Form settings → **After subscribing → Redirect to URL** → `[APP_DOMAIN]/start/?joined=1`
4. Copy the form ID (the number in the form URL). Paste into `config.js` → `KIT_FORM_ID`.
5. Kit → Send → **Sequences** → New → `Recon Briefings`. Paste the 6 emails above with the delays shown.
6. Kit → Automate → **Visual Automation**: Trigger "Joins form: Recon — Start Page" → Add tag `recon-lead` → Subscribe to sequence `Recon Briefings`.
7. Send yourself through the form once. Confirm email 1 lands and the redirect shows the "✓ You're on the list" banner.
