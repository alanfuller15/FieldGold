---
name: prior-art
description: Four-step protocol for checking a mechanism against fields that have already studied it, before it is designed or built. Use before designing any mechanism this project has not built before — a new interaction, a new state model, a new way of reporting failure. Requires two mechanically different searches, both recorded verbatim, and produces findings in a fixed shape. Not for bug fixes, rewordings, or work already grounded.
---

# Prior art — the protocol

**Why this exists.** "Search for prior art" as an instruction is too general to
be checkable. This makes it a procedure with a required shape, so that **"I
searched and found nothing" becomes a claim that can be wrong rather than a
sentence that ends an inquiry.**

**When it applies.** Before designing any mechanism this project has not built
before. **Not** for a bug fix, not for a rewording, not for work already
grounded — if a standard is already cited and fetched in `CLAUDE.md`, `STATE.md`
or a design document, it does not get re-searched.

Four steps. **The third is mandatory and is the one that does the work.**

---

## Step 1 — Rename the thing in field vocabulary, not project vocabulary

**This step decides whether the search can succeed at all.** A project name
finds nothing, because the field that studied the thing does not call it that.
Invented vocabulary is the single largest obstacle to finding prior art, and
this project generates it freely — "working set", "view registry", "problem
row", "land status", "the record".

Write both, explicitly:

- **what we call it**
- **what a person who studies this class of thing would call it**

If you cannot produce the second, **say so and search for the name itself
first.** "What is this called" is a legitimate first query and is often the only
one that matters. A search that returns a *name* has succeeded even if it
returns nothing else.

---

## Step 2 — First search: does this already exist, and what is it called

Search the field's name for it.

**Not "how to build X"** — that returns tutorials, which are the least useful
tier and crowd out everything else. Use the forms that return the studied
version: **"what is X"**, **"X pattern"**, **"X standard"**, **"X
convention"**, **"X guideline"**.

**Record the query verbatim.** Not a paraphrase of it.

---

## Step 3 — Second search, mandatory, mechanically different

**Run this regardless of what the first search returned.** A hit does not excuse
it; a miss does not excuse it. Its purpose is to defeat the framing of the first
query, which silently constrains what can be found.

"Mechanically different" is specified rather than left to judgment. **The second
query must differ from the first in at least two of these dimensions:**

| | dimension | example |
|---|---|---|
| **a** | **REGISTER** — practitioner vocabulary vs academic vs specification language | "undo stack" vs "command pattern" vs "reversible operation history" |
| **b** | **DISCIPLINE** — the same problem is studied under different names in HCI, software engineering, cartography, human factors, information science, library science, safety engineering. **Ask which other field owns this** | a map's silence is an OGC protocol question, a cartographic representation question, and an ecology "true absence vs pseudo-absence" question |
| **c** | **ABSTRACTION LEVEL** — the concrete technique, the pattern name, the standard that governs it, the theory behind it. These return different results | "peek height" vs "bottom sheet component" vs "WCAG 2.4.11" |
| **d** | **ERA** — was this solved before the current vocabulary existed. Many interaction problems were settled in the 1980s and 90s and renamed since | view lifecycle hooks predate every framework that made them implicit |

**Record the query verbatim, and name which two dimensions it varied.** More
than two searches is fine and often better; two is the floor, not the target.

---

## Step 4 — Report, in this shape

For each thing checked:

| field | content |
|---|---|
| **NAME** | what the field calls it, or "no established name found" |
| **STATUS** | EXISTS / PARTIALLY EXISTS / NO PRIOR ART FOUND |
| **THE STANDARD** | the spec, pattern, or guideline, with its identifier |
| **WHAT THEY LEARNED** | the failure modes, caveats and constraints the field already documents — **this is usually worth more than the solution** |
| **FIT** | what applies here, what does not, and why |
| **DELTA** | what remains genuinely ours to design |

### Rules that make the report honest

- **"No prior art found" is a legitimate finding and is reported as "searched
  and did not find", never as "does not exist".** State both queries so the
  claim is checkable and so the next person can vary a dimension you did not.
- **A found standard does not obligate adoption.** Report the fit, *including
  where it does not fit*. Ground rule 1 forbids most of what a framework would
  bring, and **a pattern is knowledge while a library is a dependency** — the
  rule governs the second.
- **Prefer a specification, a standard, or peer-reviewed work over a blog
  post.** Where only practitioner sources exist, **say so**: that is a tier, in
  the same sense as this project's `[self-tested]` / `[fetched]` /
  `[externally-verified]` tiers.
- **Fetch before citing.** An identifier supplied without a fetch is worth
  *less* than a plain description, because it looks checkable and is not. If a
  source cannot be reached — a JS-only documentation site, a paywall, a dead
  archive — **record it as unverified** and let the claim stand or fall on other
  grounds. A search-result summary is not a fetch; label claims drawn from one
  as search-derived.
- **Never let a found standard override a recorded project decision.** If a
  standard contradicts a ground rule or a filed decision, **report the conflict
  and stop.** Resolving it is not this protocol's job.
- **Distinguish "the field solved this" from "the field named this".** A name
  with no accompanying guidance is still valuable — it is the search term
  everyone after you will need — but it is not a solution and must not be
  reported as one.

---

## The failure mode this protocol exists to prevent

A design document that invents a vocabulary, searches for that vocabulary,
finds nothing, and records "no prior art" — while the field that studied the
problem for thirty years calls it something else and has already documented the
failure modes the design is about to rediscover on a phone, in terrain.

Worked examples, all from the 2026-07-29 pass over `PHASE1-DESIGN.md`, recorded
in `PRIOR-ART-PHASE1.md`:

- "working set" found nothing; **"scratch layer"** and **"selection set"** found
  a documented history including the exact data-loss failure the design was
  worried about.
- "survives backgrounding, cleared on deliberate exit" sounded like an
  invention; **Android ships it as a named platform primitive** with a
  three-column table saying precisely what survives what.
- "init/enter" sounded like an invention; it is
  **`viewDidLoad`/`viewWillAppear`**, and the field's own correction to it —
  a *third* hook, because the second one runs before geometry is final — is a
  gap the design had not accounted for.
