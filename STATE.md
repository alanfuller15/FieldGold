# FieldGold — migration state

Last updated: 2026-07-28 (first **simulator** build, install, launch and render.
The app runs and the map draws. The service-worker question flagged below is
now answered — it does NOT register, and the reason is not the one predicted.
Step 5 signing is still Alan's and still not started; no physical device has
run this app)

## Active phase

**Phase 0 — Capacitor shell**

Goal: FieldGold launches from a real app icon on Alan's iPhone, with zero
changes to app code.

## Status

| Step | State |
|---|---|
| Capacitor installed | **done** 2026-07-28 — `@capacitor/core`, `/cli`, `/ios` all **8.4.2**; `capacitor.config.json` written [self-tested] |
| `capacitor.config` webDir confirmed | **done** — `webDir` is `"docs"`, and `cap sync` demonstrably copied from `docs/` [self-tested] 2026-07-28 |
| App identity fixed | **done** — `appId` `io.github.alanfuller15.fieldgold`, `appName` `FieldGold`. Alan's choice 2026-07-28. **This cannot change without a new app identity** |
| Stage maps in `webDir` — ship or exclude | **decided 2026-07-28 — SHIP.** `webDir` is all of `docs/`. Confirmed in the bundle: all five present. See the decision section for what this accepts |
| iOS platform added | **done** 2026-07-28 — `npx cap add ios` + `npx cap sync` both clean [self-tested] |
| Xcode installed | **done** 2026-07-28 — Xcode **26.6**, build **17F113**, at `/Applications/Xcode.app`; `xcode-select -p` points into it [self-tested]. Alan's action, completed |
| Xcode licence agreed | **done** 2026-07-28 — `sudo xcodebuild -license` accepted by Alan. `xcodebuild -version` and `git status` both exit 0 [self-tested]. Until this landed, **`git` itself was refusing** — see below |
| Project opens in Xcode (step 4) | **done** 2026-07-28 — window `App — App.xcodeproj`, document loaded, **active scheme `App`** [self-tested]. **`cap open ios` did not achieve this on the first run** — see below |
| Builds for **simulator** | **done** 2026-07-28 — `xcodebuild -scheme App -sdk iphonesimulator` → `** BUILD SUCCEEDED **`, and the artifact was checked, not the exit code: `App.app` exists, `App` is a Mach-O 64-bit arm64 executable, `public/` carries all 20 web assets including the five stage maps and `vendor/leaflet/` [self-tested] |
| Builds for **device** | **not started.** Unchanged. A device build needs a signing identity and there are none. Do not read the simulator build as this row |
| Signing configured | **not started.** Preconditions observed — see "Signing preconditions" below. Gated on the Developer Program decision under Open decisions. **The simulator build does not touch this** — see "Simulator builds need no provisioning" |
| Installed on **simulator** | **done** 2026-07-28 — `simctl install` then `get_app_container` returned a real bundle path, so the install was confirmed by lookup rather than by exit code [self-tested] |
| Launches and renders on **simulator** | **done** 2026-07-28 — launched to PID with `ps` state `Ss`, `index.html` renders, `map.html` loads and draws. Full findings below [self-tested] |
| Installed on device | not started — **no physical device has run this app.** The cable path is not carrying data |
| Launches and renders | not started — device row. The simulator rows above do not satisfy it |

## Xcode — installed, licensed, project open

**No longer blocked.** Runbook steps 2, 3 and 4 are done. Both prerequisites
Alan owned landed 2026-07-28: Xcode 26.6 (build 17F113) installed, and the
licence agreed.

**The licence is worth its own line, because it does not fail where you would
look for it.** Before `sudo xcodebuild -license` was accepted, `git` refused
every invocation with "You have not agreed to the Xcode license agreements" —
macOS `git` is a Command Line Tools shim. The SessionStart hook consequently
reported `branch: not a git repo`, which reads like a broken checkout and is
not. `xcodebuild` failed identically. This blocked committing as well as
building, and it was independent of the Developer Program decision. Both
verified working after acceptance [self-tested] 2026-07-28.

### `npx cap open ios` exits 0 whether or not anything opened

Observed **twice on this machine, from two different causes**, with byte-identical
output both times:

```
✔ Opening the Xcode workspace... in 3.00s
```

exit 0, no error. Once with no Xcode installed. Once with Xcode 26.6 installed
and licensed but **never launched** — Xcode came up cold on `Welcome to Xcode`
+ `What's New in Xcode` with **zero documents loaded** [self-tested] 2026-07-28.

The cause is now pinned to source rather than inferred. `node_modules/@capacitor/cli/dist/ios/open.js`:

```js
await open(config.ios.nativeXcodeProjDirAbs, { wait: false });
await wait(3000);
```

`wait: false` means it never learns the result, and the `3000` is a hardcoded
constant. **"in 3.00s" is a fixed timer, not a measurement.** There is no
failure this command is capable of reporting — the ✔, the exit code and the
duration are all independent of what happened.

Same shape as the Pages `built` status naming an earlier commit, and as
`caches.open()` creating an empty cache that `in caches.keys()` then reports
as present. **Do not mark any step done on the strength of `cap open ios`
exiting 0.**

**What actually fixed it: launch Xcode.app by hand once.** Re-issuing the open
against an already-running Xcode loaded the project in ~2s. The first-run flow
swallows the document silently.

**The word "workspace" in that message is wrong here, and the missing
`App.xcworkspace` is correct.** Capacitor 8 branches on package manager; the
SPM path opens `App.xcodeproj` while printing the same "workspace" text as the
CocoaPods path. This project has no CocoaPods, so there is no `.xcworkspace`
and there should not be one. Do not go looking for it or try to generate one.

**Artifact check, no GUI interaction required:**

```
osascript -e 'tell application "Xcode" to get name of documents'
osascript -e 'tell application "Xcode" to get name of active scheme of workspace document 1'
```

Returned `App.xcodeproj` and `App` [self-tested] 2026-07-28. Empty output means
nothing opened, whatever the CLI printed.

## Signing preconditions — observed, NOT changed

Read off the tree and the keychain while verifying step 4. **Nothing here was
modified**; step 5 is Alan's and is gated on the Developer Program decision.
Recorded so the state before any signing work is on paper [self-tested]
2026-07-28.

| | Observed |
|---|---|
| `CODE_SIGN_STYLE` | `Automatic` (both Debug and Release) |
| `DEVELOPMENT_TEAM` | was **absent**; as of 2026-07-28 `project.pbxproj` carries `DEVELOPMENT_TEAM = PWCMJWTT6J` on both configs, **uncommitted**, written by Xcode. Not written by this session and not reverted by it |
| Codesigning identities | **0 valid identities found** (`security find-identity -v -p codesigning`) |
| Provisioning profiles | directory `~/Library/Developer/Xcode/UserData/Provisioning Profiles/` **does not exist** |
| `PRODUCT_BUNDLE_IDENTIFIER` | `io.github.alanfuller15.fieldgold` — matches the fixed app identity |
| `IPHONEOS_DEPLOYMENT_TARGET` | 15.0 |

The zero identities and absent profiles directory are consistent with no Apple
ID having been added under Xcode → Settings → Accounts. That is step 5's first
action, and it is why the scheme currently resolves no run destinations **for a
device**.

### Simulator builds need no provisioning — confirmed, not assumed

Checked rather than taken on faith, because the whole point of the rule that
caught `cap open ios` is that a plausible claim is not a verified one. The
build was run with **no signing overrides at all** — no `CODE_SIGNING_ALLOWED=NO`,
no team argument — against a keychain holding **0 valid codesigning identities**
and with the provisioning-profiles directory still absent. It succeeded, and
the build log names the mechanism [self-tested] 2026-07-28:

```
Signing Identity:     "Sign to Run Locally"
/usr/bin/codesign --force --sign - --timestamp=none ...
```

`--sign -` is **ad-hoc** signing. No profile is consulted and no identity is
needed. So the two signing errors in Signing & Capabilities are real and still
block a device build, and they do **not** block the simulator. These are
independent paths, and a green simulator run says nothing about step 5.

### The service worker does NOT register under Capacitor — answered

This section previously read "untested, flagged for the first device run." It
is now tested on the simulator [self-tested] 2026-07-28, and **the predicted
cause was wrong.**

The prediction was that a custom scheme would fail the secure-context
requirement. Measured inside the running app:

| probe | value |
|---|---|
| `location.href` | `capacitor://localhost` |
| `window.isSecureContext` | **`true`** |
| `'serviceWorker' in navigator` | **`false`** |
| `'caches' in window` | `true` |
| `caches.keys()` | `[]` |

**The context IS secure. `navigator.serviceWorker` simply does not exist.**
WKWebView does not expose the Service Worker API to a custom-scheme document at
all, so this never reaches a secure-context check and never produces an error.

The consequence is specific and worth stating, because it is easy to misread as
a failure: `index.html:2917` guards on `if ('serviceWorker' in navigator)`. That
test is `false`, so **`register('sw.js')` is never called**. The
`.catch(() => {})` on the next line never runs — there is no rejection to
swallow. Nothing errors, nothing logs, and nothing indicates on screen that the
app's entire offline-caching mechanism is inert. Corroborated from outside the
webview: the app's WebKit `WebsiteData` directory has folders for `LocalStorage`,
`IndexedDB` and others, and **no `ServiceWorkers` directory was ever created**.

**This is not a defect in the native shell, and `sw.js` must not be changed to
chase it.** In the shell the web assets are already local — they are in the app
bundle, served over `capacitor://` — so offline works *by construction* and does
not need the cache. What actually changes is the **delivery mechanism**:

- On GitHub Pages, `CACHE`/`SHELL` in `sw.js` is the whole update path, and
  CLAUDE.md is right that bumping the version is not bookkeeping.
- In the iOS shell, `sw.js` never runs. Updates arrive **only** through
  `npx cap sync` plus a new build. Bumping the cache version has **no effect on
  a phone running the app**, and a stale-shell bug and its fix are now two
  different problems on two distributions.

That divergence is a Phase 1 item. It is recorded here, not fixed here — Phase 0's
rule is change no app code.

## What the app actually shows — simulator, 2026-07-28

Environment, stated because it is not a device: **iPhone 17 Pro simulator,
iOS 26.5 (23F77)**, Xcode 26.6 (17F113), Debug build, `capacitor://localhost`.
Everything in this section is **[self-tested] on that simulator**. None of it is
`[externally-verified]`; no physical iPhone has run this app.

**`index.html` renders.** The Field Brain launcher draws: the 0/100 UNFAVORABLE
score dial, the site-name field, the eight weighted indicator cards, and the
six-tab bar (Evaluate / Sites / Knowledge / Photo / Research / Kit).

**The seed ran, and the land status survived the trip into the shell.** Read
back out of the app's own `localStorage` on the simulator, decoded from
`localstorage.sqlite3`:

| key | value |
|---|---|
| `fieldgold_rem_seeded_v2` | present — v2 path taken |
| `fieldgold_record` | 20 entries, all `kind: bench` |
| `land_status` | **12 `avoid`, 8 `clean`, 0 `unchecked`** |
| `state_claim` | `none` ×20 |
| `state_claim_proximity` | `unknown` ×20 |

That matches the generator payload in `tools/build_loader.py` exactly. The
encumbered twelve are encumbered in the app.

**`map.html` loads and draws.** Reached at `capacitor://localhost/map.html`,
title `FieldGold — Map`. Its own status log, read from the live DOM:

```
map ready ✓ requesting 3 layers… no logged sites yet (log some in Field Brain)
no bench-hunter candidates yet (run the bench hunter)
REM candidates: 20 plotted (8 clean, 0 unchecked, 12 avoid)
basemap (Streets) ✓ claims ✓ geochem samples: 44 ngdbsed ✓
```

44 vector markers and 48 basemap tile images in the DOM. The panel text is
intact and uncut, including the BLM warning in full — "This layer is blank over
Hatcher Pass, and that is not the same as 'no claims'", the 1-vs-143 measurement,
and the statement that the map does not know how near the nearest state claim is.

**The vendored Leaflet resolves from the bundle.** Inside `map.html`,
`typeof L === "object"` and **`L.version === "1.9.4"`**. Every bundle asset
answers over `capacitor://`: `vendor/leaflet/leaflet.js` 200 `text/javascript`,
`vendor/leaflet/leaflet.css` 200 `text/css`, `map.html` 200 `text/html`,
`sw.js` 200 `text/javascript`. Note the last one — `sw.js` is fetchable; it is
simply never registered.

**Caveat on the tiles: the simulator had network.** 48 tiles loaded because the
Mac was online. This run says **nothing** about the offline path, and the
"basemap tiles unavailable — no signal" message was therefore never exercised.
Do not read this section as evidence that offline behaviour is verified.

### Two things seen that are not yet filed as defects

- **The header collides with the status bar.** On the simulator the `index.html`
  header ("Field Brain · Placer prospecting · Mat-Su") paints underneath the
  clock and the Dynamic Island — the title and the time overlap, and the
  subtitle sits under the island. There is no `safe-area-inset` handling,
  which a browser tab does not need and a native shell does. It is cosmetic on
  the launcher, but the same absent inset applies to `map.html`'s panel, and
  that panel carries land-status warnings — which is the failure shape CLAUDE.md
  already names, "layout is a way of deleting text". Worth a reachability check
  under Capacitor before Phase 1 closes.
- **`map.html` is linked `target="_blank" rel="noopener"`** from `openTools()`
  in `index.html:2766`, as are `bench_hunter.html` and `creek_manual.html`. In a
  browser that opens a tab. In a native shell `target="_blank"` is handled by the
  webview's `createWebViewWith` path and may open externally or not at all.
  **This was not exercised** — the probe loaded `map.html` directly rather than
  through the link, because driving the real UI needs assistive access this
  machine has not granted. So "map.html works" is established and "the button
  that opens map.html works" is **not**. That gap is the one to close first on
  the device run.

### How the render findings were obtained

The repo was not modified to get them. `docs/` is byte-identical and
`git status` shows only the pre-existing `project.pbxproj` change. The probe was
a diagnostic `<script>` appended to `index.html` inside a **copy of the built
`App.app`** in the session scratchpad, ad-hoc re-signed and installed; results
were written to `localStorage` and read back off the container's SQLite. The
clean unmodified build was then reinstalled and relaunched, and the installed
bundle was confirmed to contain no diagnostic. Recorded because a reader should
know these numbers came from an instrumented copy, not from the shipping bundle
reporting on itself — Capacitor does not forward `console` to the system log by
default, so the shipping bundle cannot report on itself.

## Verified facts

<!-- Append only. Each entry: claim + tier + date. -->
<!-- Example: Apple Developer Program enrolled [externally-verified] 2026-07-26 -->

- SessionStart hook fires and injects STATE.md [externally-verified] 2026-07-25
- Every web asset lives under `docs/`; `tests/` and `tools/` remain at the repo
  root. 20 tracked files under `docs/`, none outside it that the app serves
  [self-tested] 2026-07-28
- All twelve suites pass against the moved tree. `bash .claude/verify.sh` →
  "VERIFY PASSED — all 12 suites ran and passed" [self-tested] 2026-07-28
- 489 assertions, re-counted by running each suite and reading its own total:
  30/50 node; 30, 31, 39, 48, 29, 25, 15, 109, 68, 15 python. Identical to the
  2026-07-26 measurement recorded in CLAUDE.md [self-tested] 2026-07-28
- GitHub Pages source is branch `main`, path `/docs`, and
  `pages/builds/latest.commit` is `ac215fd` — equal to `origin/main` HEAD, so
  the live bytes are this commit's and not an earlier build's [fetched]
  2026-07-28
- Live site serves the moved tree: `index.html`, `map.html`,
  `fieldgold-data.js`, `vendor/leaflet/leaflet.js` and `stage3_map.html` all
  200, byte counts equal to the local files, and `VISION_PROMPT` /
  "Scan documented gold occurrences" present in the served HTML [fetched]
  2026-07-28
- Nothing in the shipped app pages links to a stage map — zero matches for
  `stage[0-9]` across `index.html`, `map.html`, `bench_hunter.html`,
  `creek_manual.html`, `load_rem_benches.html`, `sw.js`, `manifest.json`. All
  five carry the ARCHIVED BUILD STAGE banner [self-tested] 2026-07-28
- Vendored `leaflet.css` still hashes to the published SRI — 661 CRLF, 0 bare
  LF, in both worktree and stored blob [self-tested] 2026-07-28
- Capacitor 8.4.2 installed; `cap init` wrote `capacitor.config.json` with
  `appId` `io.github.alanfuller15.fieldgold`, `appName` `FieldGold`, `webDir`
  `docs` [self-tested] 2026-07-28
- `npx cap add ios` and `npx cap sync` both completed clean. **Capacitor 8 uses
  Swift Package Manager, not CocoaPods** — `ios/App/CapApp-SPM/Package.swift`
  is written instead, so the absent `pod` binary is irrelevant to this project
  [self-tested] 2026-07-28
- The bundle is `docs/` exactly, plus two shims Capacitor injects.
  `diff -rq docs ios/App/App/public` reports **only** `cordova.js` and
  `cordova_plugins.js` as extra — 24 files in, 26 out, no omissions. No `.py`
  and no `test_*` anywhere under the bundle, so `tests/` and `tools/` did not
  leak [self-tested] 2026-07-28
- The App scheme **builds, installs, launches and renders on the iPhone 17 Pro
  simulator (iOS 26.5)**. Artifact-checked at every step: `App.app` exists with
  a Mach-O arm64 binary, `simctl get_app_container` resolves the install, the
  process is alive. `index.html` and `map.html` both render [self-tested]
  2026-07-28
- **A simulator build needs no provisioning profile.** Run with zero signing
  overrides against 0 codesigning identities and no profiles directory, it
  succeeded via ad-hoc `codesign --sign -` ("Sign to Run Locally"). The two
  Signing & Capabilities errors block only a *device* build [self-tested]
  2026-07-28
- **`navigator.serviceWorker` is absent under `capacitor://localhost`**, while
  `isSecureContext` is `true` and `caches` exists. `sw.js` therefore never
  registers in the iOS shell, silently — `index.html`'s `in navigator` guard
  short-circuits before `register()`. No `ServiceWorkers` directory is ever
  created in the app's WebKit data [self-tested] 2026-07-28
- **Vendored Leaflet resolves from the app bundle**: `L.version === "1.9.4"`
  inside `map.html` at `capacitor://localhost/map.html`, with `leaflet.js` and
  `leaflet.css` both answering 200 [self-tested] 2026-07-28
- The v2 seed runs in the shell and the land status is intact on device storage:
  20 bench records, **12 `avoid` / 8 `clean` / 0 `unchecked`**, `state_claim`
  `none` ×20, proximity `unknown` ×20 — matching the generator payload
  [self-tested] 2026-07-28
- All five stage maps are in the bundle, as the 2026-07-28 decision intends
  [self-tested]
- All twelve suites still green after the Capacitor install [self-tested]
  2026-07-28
- Mutation runs are not meaningfully slowed by `node_modules/` (26M) and
  `ios/` (1.1M) landing in the tree that `test_state_claims.py` copytrees:
  `--mutate claim-none-default` completes in 3.4s and is still caught
  [self-tested] 2026-07-28
- Xcode 26.6, build 17F113, installed at `/Applications/Xcode.app`;
  `xcode-select -p` is `/Applications/Xcode.app/Contents/Developer`
  [self-tested] 2026-07-28
- Xcode licence agreed; `xcodebuild -version` and `git status` both exit 0.
  Before acceptance **both refused**, and the `git` refusal presented as
  `not a git repo` in the SessionStart hook [self-tested] 2026-07-28
- `npx cap open ios` printed `✔ Opening the Xcode workspace... in 3.00s` and
  exited 0 **while opening nothing** — Xcode cold-launched to `Welcome to
  Xcode` with zero documents. The duration is a hardcoded `wait(3000)` after an
  `open(..., { wait: false })` in `@capacitor/cli/dist/ios/open.js`, so the
  string is a constant and the exit code carries no information [self-tested]
  2026-07-28
- Opening `ios/App/App.xcodeproj` against an already-running Xcode succeeded in
  ~2s: window `App — App.xcodeproj`, document loaded, active scheme `App`,
  schemes `App` + `CapApp-SPM`, target `App` → `App.app` [self-tested]
  2026-07-28
- Capacitor 8's SPM branch opens `App.xcodeproj`, not `App.xcworkspace`, while
  printing "workspace" either way. **The absent `App.xcworkspace` is correct** —
  it is a CocoaPods artifact and this project has none [self-tested] 2026-07-28
- Signing is untouched and unconfigured: `CODE_SIGN_STYLE` `Automatic` with
  **no `DEVELOPMENT_TEAM`**, **0 valid codesigning identities**, and **no
  provisioning profiles directory**. Xcode resolves no valid run destinations
  for scheme `App` [self-tested] 2026-07-28

## Decisions made

- **`webDir` is `"docs"`.** As of Phase 0a this is usable: `docs/` exists,
  holds only web assets, and GitHub Pages serves branch `main` at path
  `/docs`. The public URL is unchanged — Pages maps `docs/` onto the site
  root, which the live check on 2026-07-28 confirmed.

  *(This entry previously read "there is no `docs/` directory yet — so this
  value is not usable until Phase 0a moves the web assets." That was true when
  written and stopped being true on 2026-07-27.)*

  `"."` was rejected. `webDir` is the directory Capacitor copies into the
  native bundle, and at the repo root that sweeps `ios/`, `.git/`, `.claude/`,
  the `.0009-backup-*` directories, `tests/` and `tools/` into the app.

## Phase 0 — DECIDED 2026-07-28: `webDir` ships the stage maps

**Decision: ship them. `webDir` stays `"docs"` — the whole directory, no
exclusions, no prune.** Made by Alan 2026-07-28. The reasoning, the cost this
accepts, and the follow-on filed for Phase 1 are all below. Read the cost
section before you decide this was free.

### Why ship

Phase 0's hard rule is **change no app code**, and its purpose is to isolate
Apple-toolchain friction from everything else. Adding a bundle-prune mechanism
to this phase means that when something fails, the failure could be Capacitor
or it could be the prune — and Phase 0 exists precisely so that question has
one possible answer.

The mitigation being relied on is the banner plus zero inbound links. That is
**the same mitigation already considered adequate on the public site**, which
serves these five pages today at `alanfuller15.github.io/FieldGold/`.

### What this decision ACCEPTS

Recorded plainly so this is not read back as a null result. It is not.

**For the duration of Phase 0, a page that can mislead is reachable by typed
URL on a phone in terrain.** A stage map looks like FieldGold, carries no
land-status layer, and draws nothing. A person who reaches one cannot tell it
from the real map failing. That is a real cost, accepted deliberately, in
exchange for a clean answer to "did the toolchain work" on the first device
install.

It is bounded by three things and by nothing else: the red ARCHIVED BUILD
STAGE banner on all five, zero inbound links from any shipped app page, and
the fact that reaching one requires typing a URL that nothing in the app
displays. If any of those three stops being true, this decision must be
revisited rather than inherited.

### Background

Phase 0a **moved** `stage1_map_test.html` … `stage5_map.html` into `docs/`
along with every other web asset, because they are published today and three
suites load them over HTTP. They now sit inside `webDir`, which means that on
today's configuration **they will ship inside the iOS bundle.**

CLAUDE.md deliberately keeps them out of the `sw.js` SHELL. The reasoning
there: a cached stage map looks like FieldGold, carries no land-status layer,
and shows nothing at all — a browser offline error is the more honest outcome.
`tests/test_stage_maps.py` asserts their absence from SHELL so a future
"helpful" addition trips a test.

Bundling them reintroduces that risk by a different route. The bundle is not
the service worker cache — the mechanism is different and the SHELL assertion
still holds — but a person who reaches one of these pages on a phone cannot
tell the difference. They carry a red ARCHIVED BUILD STAGE banner, and nothing
in the app links to them. That is the mitigation that exists today. It was
written for a browser bookmark, not for a page shipped inside an app icon.

Both halves of that mitigation re-verified against the tree 2026-07-28
[self-tested]: all five files contain `ARCHIVED BUILD STAGE`, and `stage[0-9]`
has **zero** matches across `index.html`, `map.html`, `bench_hunter.html`,
`creek_manual.html`, `load_rem_benches.html`, `sw.js` and `manifest.json` —
reachable by typed URL only. `tests/test_stage_maps.py` still asserts their
absence from the `sw.js` SHELL, and `tests/test_panel_reachability.py` still
covers all five, so both remain load-bearing whichever way the decision goes.

The branch not taken was to exclude them from `webDir`. That option is not
discarded — it moves to Phase 1 as its own item, below. See "Phase 1 — enforce
the bundle/Pages divergence".

Do not resolve this by quietly deleting the stage maps. They are the build
history of `map.html` and CLAUDE.md keeps them on purpose.

## Phase 0a — move web assets to docs/ — **COMPLETE 2026-07-27**

A prerequisite that Phase 0 uncovered. Not in the original 0-4 plan.

Phase 0 could not set a safe `webDir` until the web assets sat in a directory
that contains only web assets. Phase 0a did that move and nothing else.

| Step | State | Evidence |
|---|---|---|
| Move web assets into `docs/` | **done** — `11e8dcf`, pure renames | 20 tracked files under `docs/` [self-tested] 2026-07-28 |
| Flip Pages source `/` -> `/docs` | **done** | `pages.source` = `{branch: main, path: /docs}` [fetched] 2026-07-28 |
| Repoint test suites at the new web root | **done** — `2bcc960` | all 10 python suites define `REPO` then `ROOT = REPO / "docs"`; both `.js` suites join `'docs'`; two suites (`test_state_claims.py`, `test_seed_drift.py`) carry a genuine REPO/WEB split as predicted [self-tested] 2026-07-28 |
| Repoint `tools/build_loader.py` | **done** — `2bcc960` | `SRC`/`DST`/`DATA_JS` all under `_WEB` [self-tested] 2026-07-28 |
| Full suite green | **done** | `bash .claude/verify.sh` → all 12 ran and passed; 489 assertions [self-tested] 2026-07-28 |

Deploy verified beyond the status field, per CLAUDE.md's rule that a `built`
status can name an earlier commit: `pages/builds/latest.commit` = `ac215fd` =
`origin/main` HEAD, and the served assets match the local bytes with content
greps hitting [fetched] 2026-07-28.

Two follow-ons landed after the move and are also complete: `docs/.nojekyll`
(`53edb99`), and `ac215fd` which **retracted** that commit's stated reason —
the claim that Jekyll's default excludes would drop `vendor/` was untested and
wrong. The file stays for determinism; the justification was corrected rather
than the file removed.

Retained below for history — this was the pre-move inventory, and every item on
it was addressed by `2bcc960`. Kept because it records *why* two suites needed a
REPO/WEB split rather than a one-line constant change, which is not obvious from
the diff.

Known to break on the move (inspected 2026-07-26, no changes made):

- All 10 Python suites compute `ROOT = __file__.parent.parent` and serve it as
  the HTTP document root, then fetch `/map.html`, `/index.html`,
  `/load_rem_benches.html`. Those 404.
- ~17 direct `ROOT / "<file>"` joins across 8 suites — the mutation-injection
  targets. A mutant that cannot find its file aborts exit 2 rather than
  reporting a false pass.
- Both `.js` suites: `path.join(path.dirname(__dirname), 'fieldgold-data.js')`.
- `tools/build_loader.py` `_ROOT` — both `SRC`/`DST` and `DATA_JS` writes.
- `tests/test_seed_drift.py` copies those two files plus the generator by
  `ROOT/name`.
- `tests/test_state_claims.py:480` needs **both** roots in one tree: it
  copytrees the root and runs `tools/build_loader.py` inside it. This one
  needs a genuine `REPO` / `WEB` split, not a one-line constant change.

Not affected: in-app links, `manifest.json` (`start_url` and `scope` are
relative), the `sw.js` SHELL (all `./`-relative), and the service worker
registration. Served URLs are identical after the move, so the move alone
does not require a cache version bump.

## Phase 1 — enforce the bundle/Pages divergence

**Filed 2026-07-28, not started. This is an item, not a note.** It is the
branch Phase 0 did not take, deferred with a reason rather than dropped.

Excluding the stage maps from the iOS bundle means **`webDir` stops being "the
directory Pages serves"**. Once those two trees are allowed to differ, nothing
in this repo currently notices if they differ in some *other* way — a file
dropped from the bundle by accident reads exactly like a file excluded on
purpose. So the work is two parts and neither is optional:

1. **A mechanism** — a copy step or a post-`sync` prune. `webDir` cannot simply
   be repointed at a subdirectory, because the stage maps must keep being
   served by Pages and keep being loadable over HTTP by
   `tests/test_stage_maps.py`, `tests/test_panel_reachability.py` and the other
   suites that fetch them.
2. **A test asserting the bundle and the Pages tree diverge exactly as intended
   and no further** — enumerating both trees and requiring the difference to be
   precisely the five stage maps. Without this, the mechanism is unguarded and
   the first silent drop ships.

**Untested here:** Capacitor's ignore behaviour for `webDir` contents. Whether
`cap copy` honours any exclusion mechanism at all was not verified on this
machine, and the plan above assumes it may not. Establish that before designing
around it.

**Why Phase 1 is the right home.** Phase 1 consolidates the scattered HTML into
one routed app. That is the change which legitimately decides what is
reachable — reachability becomes a property of the router rather than of which
files happen to sit in a directory. Bolting an exclusion onto the wrapper
answers the same question in a weaker place.

Until this lands, the accepted cost recorded under the Phase 0 decision stands.

## Open decisions

- Apple Developer Program ($99/yr) vs free 7-day provisioning.
  Free tier requires re-signing weekly — likely unworkable for field use.
  **Not yet decided.**

## Deliberately not built yet

These were considered and deferred. Do not start them without Alan saying so.

- MCP verification server (ARDF / BLM / USGS)
- iOS build automation in CI
- Any Phase 1-4 work

## Next action

**Runbook step 5 — signing. It is Alan's, and it is the only thing moving.**

Steps 2, 3 and 4 are done: Capacitor 8.4.2 installed, `ios/` scaffolded,
`cap sync` copying `docs/` into the bundle correctly, Xcode installed and
licensed, and the App target open with scheme `App` selected.

Step 5 is two actions, in order, and **both are Alan's**:

1. **Decide Apple Developer Program ($99/yr) vs free 7-day provisioning.** See
   Open decisions — still undecided. The 7-day expiry means the app dies in the
   field with no way to re-sign from a riverbank. **Do not pick a tier to keep
   moving.**
2. **Add the Apple ID** under Xcode → Settings → Accounts, then App target →
   Signing & Capabilities → team. Nothing can be signed before this: there are
   0 codesigning identities on this machine and no provisioning profiles
   directory, which is also why the scheme resolves no run destinations.

Everything achievable without a signing tier has been done and verified. The
block does not reach backwards — and it reaches less far than it looked. The
simulator run on 2026-07-28 proved the shell **works**: it builds, installs,
launches, renders `index.html`, loads `map.html`, resolves the vendored Leaflet
and seeds all 20 benches with land status intact, none of which needed a
signing tier. What signing gates is putting it on **Alan's phone**, not
knowing whether it functions.

**Do not mark "Installed on device" or "Launches and renders" done on the
strength of the simulator run.** Those rows are about a physical iPhone and no
physical iPhone has run this app. The simulator has its own rows.

Two things the simulator run added to step 5's checklist, both open:

- **Exercise the `target="_blank"` links.** `map.html` was reached directly, not
  through the Field tools button. Whether that button works in the shell is
  untested and is the first thing to tap on the device.
- **Check the safe-area insets.** The header already collides with the status
  bar on the simulator. `map.html`'s panel carries land-status warnings, and
  CLAUDE.md's own rule is that layout is a way of deleting text.

The procedure for the Capacitor half is
**`.claude/skills/phase-0-shell/SKILL.md`** — Capacitor init, `cap add ios`,
signing, provisioning, first device install. That file is how; this file is
how far. Update the tables above as its steps land, and record the tier
([self-tested] / [fetched] / [externally-verified]) under Verified facts.
Phase 0a had no runbook — the breakage inventory above was what there was, and
it is now closed history.
