# OPERATOR RECON — Welcome Sequence v02
**Platform:** Kit (ConvertKit) → Sequence `Recon Briefings`
**Trigger:** joins form `Recon — Start Page` → tag `recon-lead` → subscribe to sequence
**Sender:** Chris G. Stewart · Ashes to Alpha

### Changes from v01
- Missed-day rule now matches the Field Guide: skipped days are not made up. Move forward. (v01 said "repeat the week," which contradicted the Guide.)
- Email 6 no longer says "reset." It points to **Start new cycle** in the app, which archives baseline and retest. Reset (now labeled "Erase all logs") deletes them.
- Copy no longer assumes the reader started training the day he subscribed. Each email works whether he's on schedule, behind, or hasn't started.
- The schedule is written as Kit enters it: **days after the previous email**, not days after signup.

### Schedule: enter exactly this in Kit
Kit sequence delays count from the **previous email**, not from signup.

| # | Subject | Kit delay field | ≈ Day from signup |
|---|---|---|---|
| 1 | Week 1. Write the numbers down. | **0 days** (send immediately) | 0 |
| 2 | You're going to miss a day | **3 days** | 3 |
| 3 | The knee, the back, the shoulder | **7 days** | 10 |
| 4 | Week 3 is where it costs something | **5 days** | 15 |
| 5 | Peak. Then you back off. | **14 days** | 29 |
| 6 | What did the numbers say? | **11 days** | 40 |

Set send days to all seven days of the week (Kit defaults can skip weekends and shift the schedule).

### Placeholders to replace before turning it on
- `[APP_LINK]` → https://ashes2alphanow-gif.github.io/operator-recon/
- `[GUIDE_LINK]` → https://ashes2alphanow-gif.github.io/operator-recon/start/#guide
- `[SUBSTACK_LINK]` → https://chrisstewarta2a.substack.com

`{{ subscriber.first_name | default: "Brother" }}` is Kit's Liquid. Change the fallback if you want.

---

## Email 1 — immediately
**Subject:** Week 1. Write the numbers down.
**Preview:** The baseline is the only part of this program you can't redo.

{{ subscriber.first_name | default: "Brother" }},

You signed up. That puts you ahead of everybody still telling himself he'll start Monday.

First move: open the app, tap the gear, and set your **program start date** to the Monday you'll actually begin. It doesn't have to be this Monday. Pick a real one.

That Monday is **the baseline test.** Four events, in this order, full rest between each:

- Push-ups, 2 minutes
- Sit-ups, 2 minutes
- Strict pull-ups, one set
- 2-mile run for time

Log every number, even the ugly ones. *Especially* the ugly ones. Six weeks later you retest the same four events and the app puts them side by side. That comparison is the whole point, and you can't have it if you skip the first half.

Two rules for test day:

1. **Don't pace yourself to look good.** A soft baseline makes for a fake retest.
2. **Don't turn it into a hero day.** Test, do the light lower work as written, and go home. Stop a set when form breaks, not when your ego does.

Open the app: [APP_LINK]
On iPhone, open it in Safari, then Share → Add to Home Screen. After the first load it works offline. Back up your log now and then with Export JSON in Settings, because the data lives on your phone.

— Chris | Ashes to Alpha

*P.S. The app is free and stays free. If you want the program on paper with scaling tables and travel versions of every session, that's the Field Guide: [GUIDE_LINK]*

---

## Email 2 — 3 days after Email 1
**Subject:** You're going to miss a day
**Preview:** Here's the rule for when you do.

{{ subscriber.first_name | default: "Brother" }},

Whether you've started yet or not, this one's worth reading before it happens.

Somewhere in the next six weeks a shift runs long, a kid gets sick, or you just don't go. Decide now what you'll do, so one missed day doesn't become a week, then "I'll restart next month."

**The rule: a skipped day is gone. Move forward.**

- Don't make it up by stacking two hard days. Do today's session as written.
- Short on time? Do a 20-minute version of the day and mark it **modified** in the app. A modified day still counts.
- Travelling? Keep the day's intent, shrink the footprint, and log it modified. A hotel-room session beats a missed day you planned to crush when you got home.
- If you lose several days in a row, you can shift the whole week by a day, as long as you still have room before the retest.

The streak counter in the app isn't decoration. Consistency beats intensity in every program anybody has finished.

— Chris

---

## Email 3 — 7 days after Email 2
**Subject:** The knee, the back, the shoulder
**Preview:** Scaling isn't quitting.

{{ subscriber.first_name | default: "Brother" }},

Most of us coming back to this have something. A knee that's been loud for ten years. A back that tells you about the weather. A shoulder you don't talk about.

How to think about it:

- **Pain that's sharp, radiating, or getting worse: stop.** That isn't a toughness test. Get it looked at by someone qualified.
- **Dull, general "haven't done this in years" soreness: normal.** It should ease once you're warm and settle in a day or two.
- **Scale the movement, keep the slot.** Can't run today? Use a lower-impact substitute for the same time block and mark the day modified. Can't do pull-ups yet? Regress them. Honest work at a lower level still counts.

Two hard lines: **never swim alone, and no breath-hold or underwater work.** If there's no supervised pool, use a dry-land substitute.

I'm not your doctor, and this isn't medical advice. If something is actually injured, see a professional and come back when you're cleared. The program will still be here.

What you can't do is use "something hurts" as permission to drop the whole thing when it only means changing one movement.

*The Field Guide has full beginner and injury substitution tables if you want the exact swaps: [GUIDE_LINK]*

— Chris

---

## Email 4 — 5 days after Email 3
**Subject:** Week 3 is where it costs something
**Preview:** Phase 2. Build.

{{ subscriber.first_name | default: "Brother" }},

If you started on time, you're about to move from **Rebuild** into **Build.** If you started later, save this one for when you get there.

In Build the shape of the week stays the same, but each day costs more. Intervals get sharper, lifting gets denser, and the ruck goes to 40 lb.

Most people who fall off here don't quit because of the training. They quit because of what happens between sessions:

- **Sleep.** Five hours a night and the program can't work. Log it. If it drops for several nights, back off the next hard day instead of pushing through.
- **Protein and water.** The app sets targets from your bodyweight. Hit them before you worry about anything fancier.
- **Feet.** Deal with a hot spot the day you feel it, not when it's a blister that costs you the Week 5 ruck.

And don't invent a harder version of the program. The increases are already written in. Do them as written.

— Chris

---

## Email 5 — 14 days after Email 4
**Subject:** Peak. Then you back off.
**Preview:** The taper is part of the program.

{{ subscriber.first_name | default: "Brother" }},

On schedule, you're in **Peak.** Week 5 is the hardest week of the six: heavier lifting, faster repeats, a swim time trial, and the 8-mile ruck at 45 lb. Behind schedule? That's fine. Keep this for when you get there.

Then Week 6 gets lighter on purpose. Men like us are bad at that part. We feel good, so we add work. Don't. The lighter week is when your body catches up. Show up to the retest fresh, not fried.

**Retest: Week 6, Friday.** Same four events, same order, same rest as your baseline. Same conditions if you can manage it: same time of day, same route, same shoes.

If you've got it in you, Saturday is the optional capstone, a 5-mile ruck at 45 lb, walked, for time. The app shows three marks: sub-75, sub-65, sub-60. Those are this program's own shorthand, not any official standard. Record your honest time either way.

— Chris

---

## Email 6 — 11 days after Email 5
**Subject:** What did the numbers say?
**Preview:** Baseline vs. retest, and what comes next.

{{ subscriber.first_name | default: "Brother" }},

If you've retested, open the STATS tab. Baseline on the left, retest on the right.

Whatever's there is true. Better than you hoped or not as much as you wanted, it's real data on a man who decided to do something and then did it. Most people never get that far.

Not there yet? Keep going. This email will still be in your inbox when you retest.

**What's next:**

1. **Take a lighter Week 7.** Easy cardio, easier lifting, a short ruck. Don't jump straight into something harder because the retest felt good.
2. **Then go again, or pick a focus.** To repeat the program, use **Settings → Start new cycle.** It archives your baseline and retest so you can see them under STATS → Previous cycles and beat them. (Don't use "Erase all logs." That deletes everything.) Export a JSON backup first if you want one off your phone.
3. **Want the next block planned on paper?** The Field Guide's "Weeks 7 and after" section walks you through picking a focus and writing the plan down: [GUIDE_LINK]

I also write field notes on discipline, fatherhood, and carrying weight that isn't in a ruck: [SUBSTACK_LINK]

— Chris | Ashes to Alpha

---

## Kit setup checklist (do once)
1. Kit → Grow → Landing Pages & Forms → **Create form** → Inline. Name: `Recon — Start Page`.
2. Form settings → **After subscribing → Redirect to URL** → `https://ashes2alphanow-gif.github.io/operator-recon/start/?joined=1`
3. Double opt-in (incentive email): your call. On means fewer but confirmed subscribers, and the sequence only starts after he clicks confirm. Test whichever you pick.
4. Copy the form ID (the number in the form's URL). Paste it into `config.js` → `KIT_FORM_ID`.
5. Kit → Send → **Sequences** → New → `Recon Briefings`. Paste the six emails. Use the **Kit delay field** column above, not the day-from-signup column. Allow all send days.
6. Kit → Automate → **Visual Automation:** trigger "Joins a form: Recon — Start Page" → action "Add tag: recon-lead" → action "Subscribe to sequence: Recon Briefings." **Publish** the automation (drafts don't run).
7. Run the verification in `funnel/README.md`. Don't consider it live until every step passes.
