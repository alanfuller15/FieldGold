---
name: phase-0-shell
description: Runbook for FieldGold migration Phase 0 — wrapping the existing PWA in a Capacitor iOS shell and getting it signed and installed on a physical iPhone. Use when starting, resuming, or troubleshooting Phase 0, or when the task involves capacitor init, cap add ios, Xcode signing, provisioning profiles, or first device install.
---

# Phase 0 — Capacitor shell

## Purpose

Prove the build → sign → install chain end to end. The riskiest unknown in
this migration is Apple toolchain friction, not FieldGold's code. Hit that
wall first, with nothing else in flight.

## Hard rule

**Change no app code in this phase.** Not a bug fix, not a cleanup, not a
"while we're here." If the wrapped app has the same bugs it had in Safari,
Phase 0 succeeded. Mixing app changes into this phase means a failure could
be Capacitor or could be the edit, and you won't know which.

## Prerequisites

- macOS with Xcode installed (includes command line tools)
- Node available
- A decision on Apple Developer Program — see "Signing" below

## Steps

### 1. Confirm webDir

Find what the static site actually serves. Check whether GitHub Pages is
publishing from the repo root or from `docs/`.

```
ls index.html docs/index.html 2>/dev/null
```

`webDir` must point at the directory containing `index.html`. Getting this
wrong produces a blank white app that is confusing to debug later.

**Stop and confirm with Alan before proceeding.**

### 2. Install Capacitor

```
npm install @capacitor/core @capacitor/cli
npx cap init
```

`cap init` prompts for app name, bundle ID, and webDir. Bundle ID should be
reverse-DNS and stable — it cannot be changed later without a new app
identity.

### 3. Add iOS

```
npm install @capacitor/ios
npx cap add ios
npx cap sync
```

### 4. Open Xcode

```
npx cap open ios
```

### 5. Signing

In Xcode: select the App target → Signing & Capabilities → check
"Automatically manage signing" → select your team.

Two paths, and this is a real decision:

| | Cost | Rebuild cadence |
|---|---|---|
| Free Apple ID | $0 | every 7 days |
| Developer Program | $99/yr | every 12 months |

The 7-day expiry means the app dies in the field with no way to re-sign
from a riverbank. If FieldGold is meant to be relied on at the Little Su,
the free tier is not viable.

**This is Alan's call. Do not assume one.**

### 6. Install on device

Plug in the iPhone, select it as the run destination, press Run.

First run will require trusting the developer certificate on the phone:
Settings → General → VPN & Device Management.

## Done when

- App icon on the home screen
- Launches without a blank screen
- Existing FieldGold UI renders
- Map view loads at least one tile with the phone on wifi

That last item is deliberately weak. Offline tiles are Phase 3. All Phase 0
proves is that the webview is alive and networking works.

## Not in scope

Offline tiles, SQLite, background GPS, HTML consolidation. Each has its own
phase. If one of those problems surfaces here, write it into `STATE.md`
under open items and move on.

## Common failures

- **Blank white screen** — almost always wrong `webDir`, or `npx cap sync`
  not run after a change.
- **Plugin not found** — `npx cap sync` not run after `npm install`.
- **Signing fails with no team** — Xcode → Settings → Accounts, add the
  Apple ID first.

## On completion

Update `STATE.md`: mark Phase 0 steps done, record the install as
`[externally-verified]` with the date, set active phase to 1. Commit.
