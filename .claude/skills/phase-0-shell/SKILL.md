---
name: phase-0-shell
description: Runbook for FieldGold migration Phase 0 — wrapping the existing PWA in a Capacitor iOS shell and getting it signed and installed on a physical iPhone. Use when starting, resuming, or troubleshooting Phase 0, or when the task involves capacitor init, cap add ios, Xcode signing, provisioning profiles, or first device install.
---

# Phase 0 — Capacitor shell

## Where phase status lives

**`STATE.md` at the repo root, not this file.** This runbook says how to
perform the steps; `STATE.md` records which of them are done, what is verified
and at which tier, and what is still an open decision. Read it before starting
and update it as steps land. If the two ever disagree about progress,
`STATE.md` is right and this file is a procedure that was followed or wasn't.

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

All three can be passed as arguments instead of answering prompts, which is
what was actually run on 2026-07-28:

```
npx cap init "FieldGold" "io.github.alanfuller15.fieldgold" --web-dir docs
```

**Capacitor 8 uses Swift Package Manager, not CocoaPods.** `cap add ios`
writes `ios/App/CapApp-SPM/Package.swift`; there is no `pod install` step and
a missing `pod` binary does not block anything here. Older guidance that lists
CocoaPods as a prerequisite does not apply to this project.

### 3. Add iOS

```
npm install @capacitor/ios
npx cap add ios
npx cap sync
```

### 4. Open Xcode

**Launch Xcode.app by hand once before running this.** On a machine where
Xcode has never been opened, `cap open ios` loses the document to the
first-run flow — see below.

```
npx cap open ios
```

**This command carries no information about whether it worked.** Read
`node_modules/@capacitor/cli/dist/ios/open.js`:

```js
await open(config.ios.nativeXcodeProjDirAbs, { wait: false });
await wait(3000);
```

`wait: false` means it never learns the result, and the `3000` is a hardcoded
constant. **The "in 3.00s" is a fixed timer, not a measurement** — that exact
string prints whether Xcode opens the project, ignores it, or isn't installed
at all. Exit 0 and the ✔ are equally uninformative.

**Observed 2026-07-28 [self-tested], with Xcode 26.6 installed and licensed:**
`npx cap open ios` printed `✔ Opening the Xcode workspace... in 3.00s`, exited
0, and **did not open the project**. Xcode launched cold to `Welcome to Xcode`
+ `What's New in Xcode` with zero documents loaded. Re-issuing the same open
against an already-running Xcode loaded it in ~2s. The first-run flow swallows
the document; nothing reports that.

**Ignore the word "workspace" in that message.** Capacitor 8 branches on the
package manager and the SPM path opens `App.xcodeproj`:

```js
if ((await config.ios.packageManager) == 'SPM') {
  await open(config.ios.nativeXcodeProjDirAbs, { wait: false });
} else {
  await open(await config.ios.nativeXcodeWorkspaceDirAbs, { wait: false });
}
```

The message text is the same on both branches. **The absent
`ios/App/App.xcworkspace` is correct, not a defect** — it is a CocoaPods
artifact and this project has no CocoaPods. Do not go looking for it, and do
not try to generate one.

**Verify the artifact, not the exit code.** The artifact is an Xcode window
with the App target selected. Checked without touching the GUI:

```
osascript -e 'tell application "Xcode" to get name of documents'
osascript -e 'tell application "Xcode" to get name of active scheme of workspace document 1'
```

Expected: `App.xcodeproj` and `App`. Empty output means nothing opened,
whatever the CLI printed.

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
- **`npx cap open ios` prints ✔ and exits 0 when nothing opened.** Observed
  twice on this machine 2026-07-28, from two different causes: once with no
  Xcode installed, once with Xcode 26.6 installed but never launched. Identical
  output both times — "Opening the Xcode workspace... in 3.00s", exit 0, no
  error. See step 4: the duration is a hardcoded timer and the call is made
  with `wait: false`, so **there is no failure this command can report.**
  Diagnose by cause: `xcode-select -p` returning
  `/Library/Developer/CommandLineTools` means Xcode is not installed; an Xcode
  sitting on `Welcome to Xcode` with no documents means the first-run flow ate
  the document — just open the project again. The artifact is an Xcode window,
  not an exit code.
- **`git` fails with "You have not agreed to the Xcode license agreements."**
  Not a repo problem. macOS `git` is a Command Line Tools shim and every
  invocation refuses until the licence is accepted, which reads at a glance
  like a broken checkout — the SessionStart hook reported `not a git repo`
  [self-tested] 2026-07-28. `xcodebuild` fails the same way. Fix with
  `sudo xcodebuild -license` (needs an admin password, so it is Alan's action).
  This blocks committing as well as building, and it is independent of the
  Developer Program decision.

## On completion

Update `STATE.md`: mark Phase 0 steps done, record the install as
`[externally-verified]` with the date, set active phase to 1. Commit.
