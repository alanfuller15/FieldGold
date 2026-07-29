# FieldGold — migration state

Last updated: 2026-07-28 (**first build, install and launch on a physical
iPhone.** Signing is resolved, the device is registered, a provisioning profile
exists, and FieldGold runs on Alan's iPhone 14. The cable blocker is gone. One
finding is now confirmed on real hardware with a real finger and is **worse
than the simulator recorded it**: the three internal `target="_blank"` links do
nothing, and since `map.html` is referenced exactly once in `index.html` — by
that dead anchor — **the map is UNREACHABLE from the app's UI on a phone.** Not
a broken button: the primary field tool cannot be opened at all)

## Active phase

**Phase 0 — Capacitor shell — COMPLETE 2026-07-28** (PR #4, `main` at
`e7534e4`). Goal met: FieldGold launches from a real app icon on Alan's iPhone,
with zero changes to app code.

**Next phase: Phase 1 — and its scope is not what it was filed as.** The device
run found three silent Pages/shell divergences, two of which make the app
unusable rather than untidy. Read "The class is now confirmed three times over"
and the device residue at the end of this file before planning it. Do not start
Phase 1 work without reading the two constraints on its fixes recorded there —
both are the kind a confident fix gets wrong.

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
| Builds for **device** | **done** 2026-07-28 — `xcodebuild -sdk iphoneos -destination id=00008110-...` → `** BUILD SUCCEEDED **`, exit 0. Verified by artifact, not exit code: `App.app/App` is Mach-O arm64, `embedded.mobileprovision` is present and names this device, and `codesign --verify --deep --strict` exits 0 "satisfies its Designated Requirement" under authority `Apple Development: Alan Fuller (VSSL232H55)` → Apple WWDR CA → Apple Root CA. **A real chain, not the simulator's ad-hoc `--sign -`** [self-tested] |
| Apple Developer Program | **done** 2026-07-28 — **paid, enrollment approved.** Verified from the machine: `isFreeProvisioningTeam = 0`, `teamType = Individual`, team `PWCMJWTT6J` "Alan Fuller" [self-tested] |
| Apple ID added in Xcode | **done** 2026-07-28 — one account under `IDE.Identifiers.Prod`; team resolves and is set in the pbxproj [self-tested] |
| Signing configured | **done** 2026-07-28 — **1** valid identity (`8F3132ED…` `Apple Development: Alan Fuller (VSSL232H55)`), automatic signing, team `PWCMJWTT6J` on both configs. The four earlier certificates were issued to a **different machine**; see the resolution below |
| **Data cable** | **RESOLVED** 2026-07-28 — a data-carrying Lightning cable is in hand. `devicectl list devices` shows `Alans IPhone`, `iPhone 14 (iPhone14,7)`, UDID `00008110-0006398C0ABA401E`, state `connected`, `pairingState paired`, `tunnelState connected`, `transportType wired` [self-tested] |
| Developer Mode on device | **done** 2026-07-28 — Alan enabled it on the phone and rebooted. `developerModeStatus` `disabled` → **`enabled`**, `ddiServicesAvailable` `false` → **`true`**. Corroborated independently: the model string resolved from raw `iPhone14,7` to `iPhone 14 (iPhone14,7)`, which only happens once the DDI mounts. **This blocks destination resolution, which runs BEFORE provisioning** — with it off, `xcodebuild` exits 70 on "Timed out waiting for all destinations", and no signing error is ever reached [self-tested] |
| Device registered | **done** 2026-07-28 — registration happened when Alan selected the phone as the run destination in Xcode. Confirmed by artifact: the profile's `ProvisionedDevices` array contains exactly `00008110-0006398C0ABA401E` [self-tested] |
| Provisioning profile | **done** 2026-07-28 — the profiles directory, absent for the whole project until now, holds `150382bc-….mobileprovision`: `iOS Team Provisioning Profile: *`, team `PWCMJWTT6J`, AppID `PWCMJWTT6J.*`, `get-task-allow true`, created 2026-07-28, expires 2027-07-28 [self-tested] |
| Installed on **simulator** | **done** 2026-07-28 — `simctl install` then `get_app_container` returned a real bundle path, so the install was confirmed by lookup rather than by exit code [self-tested] |
| Launches and renders on **simulator** | **done** 2026-07-28 — launched to PID with `ps` state `Ss`, `index.html` renders, `map.html` loads and draws. Full findings below [self-tested] |
| Installed on device | **done** 2026-07-28 — `devicectl device install app` reported `bundleID io.github.alanfuller15.fieldgold`. Confirmed by **independent lookup** rather than by that output: `devicectl device info apps --bundle-id …` returns `FieldGold  io.github.alanfuller15.fieldgold  1.0  1` [self-tested] |
| Launches on device | **done** 2026-07-28 — confirmed by process lookup, not by the launcher's message: PID **814** at `/private/var/containers/Bundle/Application/57A8A239-972C-416C-B133-1D8EF070D5E1/App.app/App`, the bundle UUID the install returned [self-tested] |
| Renders on device | **done — both pages** [externally-verified] 2026-07-28. `index.html`: Alan drove the real UI — launcher drew, Tools sheet opened, Knowledge tab rendered, external link worked. `map.html`: **draws on the device**, reached via `location.href` in Web Inspector because the UI route is dead. **Rendering is not the same as usable** — the map's controls cannot be tapped; see the safe-area section |

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

## Signing — account and certificates are DONE. The blocker is a cable.

**This section previously said the Developer Program decision was unmade and no
Apple ID had been added. Both were stale.** Re-verified against the machine
2026-07-28, every row checked rather than taken on report [self-tested]:

| | Observed | Meaning |
|---|---|---|
| Developer Program | `isFreeProvisioningTeam = 0`, `teamType = Individual` | **paid, approved** — not a Personal Team |
| Apple ID | one account under `DVTDeveloperAccountManagerAppleIDLists` → `IDE.Identifiers.Prod` | **added** in Xcode → Settings → Accounts |
| Team | `PWCMJWTT6J` / "Alan Fuller" | matches the pbxproj exactly |
| `DEVELOPMENT_TEAM` | `PWCMJWTT6J` on **both** Debug and Release | set — this is the source of the uncommitted `project.pbxproj` change |
| `CODE_SIGN_STYLE` | `Automatic` (both configs) | automatic signing on |
| Certificates | **4** × `Apple Development: Alan Fuller (VSSL232H55)`, `OU=PWCMJWTT6J`, all issued 2026-07-28 between 20:24:59Z and 20:52:24Z, all valid to 2027 | issued, current, and the four timestamps are the revoke-and-reissue cycle |
| Provisioning profiles | `~/Library/Developer/Xcode/UserData/Provisioning Profiles/` **still does not exist** | **no profile has ever been issued** |
| Physical devices | `xcrun devicectl list devices` → `No devices found`; `xctrace list devices` shows only the Mac | **no iPhone is visible to this Mac** |
| `PRODUCT_BUNDLE_IDENTIFIER` | `io.github.alanfuller15.fieldgold` | matches the fixed app identity |
| `IPHONEOS_DEPLOYMENT_TARGET` | 15.0 | |

### The blocker is hardware, not a decision

**No data cable.** The iPhone 14 needs Lightning; the USB-A cable plus USB-C
adapter on hand does not carry data, and Finder does not see the phone. The
causal chain, and it is a chain rather than a list — each link is why the next
one holds:

1. No data connection, so **Xcode cannot register the device** with the account.
2. An iOS App Development profile must name at least one registered device, so
   **no development provisioning profile can be generated**.
3. With no profile, **the two Signing & Capabilities errors persist** — and they
   will persist no matter how many times the certificate is revoked and
   reissued, because certificates were never the missing piece.

Confirmed by running the device build rather than by reading the Xcode UI
[self-tested] 2026-07-28. `xcodebuild -sdk iphoneos -destination
'generic/platform=iOS'` fails at `GatherProvisioningInputs`, exit 65:

```
error: No profiles for 'io.github.alanfuller15.fieldgold' were found:
Xcode couldn't find any iOS App Development provisioning profiles
matching 'io.github.alanfuller15.fieldgold'.
```

Note **what it does not say.** It does not say the team is unset, and it does
not say a certificate is missing. It gets past both and fails on the profile.
That is the signature of this being a device-registration gap.

**What unblocks it is a Lightning cable that carries data.** Nothing in the
software needs changing, and no further certificate work will help.

### RESOLVED 2026-07-28 — the certificates belonged to another machine

**The anomaly recorded below is closed, and the recorded hypothesis was wrong.
Both of the guesses this file made were wrong, in the same direction: each
assumed the tooling was misreporting. It was not.**

What it actually was: the four `Apple Development` certificates were issued to a
**different machine** — "Caitlin's MacBook Pro" — and their private keys were
never on this Mac at all. `find-identity` reporting **0 valid identities** was
not an instrument problem, a keychain-location problem, or a sandbox problem. It
was the literal truth: an identity is a certificate *plus its private key*, the
keys did not exist here, so there were no identities. Corroborated on
2026-07-28 from three independent directions before the fix — `find-identity -v`
returned 0 across **all** policies rather than just `-p codesigning`; four certs
were nonetheless present in `login.keychain-db`; and Xcode's own build error
said it outright:

```
error: Revoke certificate: Your account already has an Apple Development signing
certificate for this machine, but its private key is not installed in your
keychain. Xcode can create a new one after revoking your existing certificate.
```

**The fix, performed by Alan.** Xcode could not revoke them and the account was
at Apple's certificate limit, so he revoked them at `developer.apple.com`, then
created a new one via **Xcode → Settings → Accounts → Manage Certificates → ＋**,
which generates the keypair **locally** and installs it in the login keychain.
Selecting the phone as the run destination then triggered device registration
and profile generation in one step. Result: `find-identity -p codesigning` now
reports **1** valid identity.

**The generalisable lesson, and it is the one this file keeps having to relearn:**
when a tool reports an absence, the cheap hypothesis is that the tool is looking
in the wrong place. That hypothesis was written down twice here and was wrong
both times. `find-identity` was correct throughout. Same family as `cap open
ios` exiting 0, a Pages `built` status naming an earlier commit, and
`caches.open()` creating an empty cache — except inverted: those were tools
reporting **success** that meant nothing, and this was a tool reporting
**failure** that meant exactly what it said. Check the instrument's claim
against a second source before deciding the instrument is broken.

### One anomaly, deliberately recorded rather than explained away — CLOSED, see above

`security find-identity -v -p codesigning` reports **0 valid identities**, and
`codesign --sign "Apple Development: Alan Fuller (VSSL232H55)"` fails with
`no identity found` — while the four certificates above are demonstrably
present in `login.keychain-db` and unexpired. An identity is a certificate plus
its private key, so the CLI is telling us it cannot pair them.

Checked and **not** explained by: the keychain being locked (it is unlocked,
`no-timeout`), or this shell's sandbox (the same command outside the sandbox
returns the same 0).

Do **not** copy the old inference from this. The previous version of this file
read "0 valid identities" as "no Apple ID has been added", and that reading is
now provably wrong — the account is added and the certificates exist. The most
likely explanation is that Xcode 26 keeps signing keys where the legacy
`security` tool cannot enumerate them, which would make `find-identity` simply
the wrong instrument here. **That is a hypothesis and has not been tested.**

It is also not currently load-bearing: the device build fails at profile
generation, which happens *before* code signing, so this has not yet had a
chance to bite. Re-check it once a cable exists and a profile is issued — if
signing then fails with `no identity found`, this is the reason, and the fix is
to let Xcode's GUI reissue into the login keychain rather than to chase it from
the CLI.

**Superseded 2026-07-28.** This paragraph used to read the zero identities and
absent profiles directory as "no Apple ID has been added". That inference was
wrong and is retained only so the mistake is not repeated: an added account and
issued certificates produce exactly the same two observations when no device has
ever been registered. The scheme resolves no device run destination because
there is no device — see the blocker above.

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

- **The header collides with the status bar. CONFIRMED ON THE PHYSICAL
  iPhone 14, 2026-07-28 [externally-verified] — this is not a simulator
  artifact.** Alan read it off the device: the "Field Brain" header still paints
  under the clock and the Dynamic Island on real hardware, exactly as the
  simulator showed. **This half of the safe-area item is closed**; the
  `map.html` panel half remains open and is the one that matters, because that
  panel carries the land-status warnings. On the simulator the `index.html`
  header ("Field Brain · Placer prospecting · Mat-Su") paints underneath the
  clock and the Dynamic Island — the title and the time overlap, and the
  subtitle sits under the island. There is no `safe-area-inset` handling,
  which a browser tab does not need and a native shell does. It is cosmetic on
  the launcher, but the same absent inset applies to `map.html`'s panel, and
  that panel carries land-status warnings — which is the failure shape CLAUDE.md
  already names, "layout is a way of deleting text". Worth a reachability check
  under Capacitor before Phase 1 closes.
- ~~**`map.html` is linked `target="_blank" rel="noopener"`**~~ — **CLOSED
  2026-07-28, and the answer is bad.** See "The Field tools buttons are dead in
  the shell" below. Original wording kept underneath for the record.
- **`map.html` is linked `target="_blank" rel="noopener"`** from `openTools()`
  in `index.html:2766`, as are `bench_hunter.html` and `creek_manual.html`. In a
  browser that opens a tab. In a native shell `target="_blank"` is handled by the
  webview's `createWebViewWith` path and may open externally or not at all.
  **This was not exercised** — the probe loaded `map.html` directly rather than
  through the link, because driving the real UI needs assistive access this
  machine has not granted. So "map.html works" is established and "the button
  that opens map.html works" is **not**. That gap is the one to close first on
  the device run.

### The Field tools buttons are dead in the shell

> **CONFIRMED ON PHYSICAL HARDWARE, 2026-07-28 [externally-verified].** Alan
> tapped the buttons on his iPhone 14 with a real finger. Test A — the internal
> `map.html` card — **did nothing at all.** Test B, the control, was an
> `https://` link on the *same* `target="_blank"` anchor pattern going through
> the *same* delegate under the *same* gesture: **it opened.** The only variable
> between them is the URL scheme. This closes the one link the simulator run
> could only infer — that a genuine tap reaches the delegate — and it closes it
> the right way round: the delegate *is* reached, and it fails on the scheme.
>
> **The consequence is worse than "the buttons are broken", and it was found by
> counting references rather than by tapping.** `map.html` is referenced
> **exactly once** in `index.html` — line 2766, and that reference *is* the dead
> anchor. There is no other link, no `location.href`, no `window.open` pointing
> at it. So on a phone, **`map.html` is UNREACHABLE from the app's UI.** The
> primary field tool — the only field map screen, the one carrying the
> land-status colours — cannot be opened at all. `bench_hunter.html` and
> `creek_manual.html` are in exactly the same position.
>
> A person holding this app on the ground has the launcher and nothing else.
> **This raises Phase 1's priority: it is no longer a divergence to tidy up, it
> is the app's primary function being absent on the distribution that goes into
> terrain.**
>
> Measured 2026-07-28: `index.html` carries **12** `target="_blank"` links. Only
> **3** are internal (`map.html`, `bench_hunter.html`, `creek_manual.html`) and
> are therefore dead. The other **9** are `https://` — five YouTube, two Apple
> Maps, two dynamic — and per this mechanism they work, which is what Test B
> demonstrated. The fix must not blanket-strip `target="_blank"`; it is doing
> real and correct work on nine of the twelve.

**`target="_blank"` links do nothing under Capacitor. Not "open elsewhere" —
nothing, silently.** Tested on the simulator 2026-07-28 [self-tested], and
confirmed on device [externally-verified] — see above. This
affects **all three** Field tools buttons in `openTools()`: `map.html`
(`index.html:2766`), `bench_hunter.html` (:2781) and `creek_manual.html`
(:2796).

The mechanism, each link established separately:

1. **The anchor is real and reachable.** In the running app the modal opens,
   `a[href="map.html"]` is present, `target="_blank"`, `rel="noopener"`,
   362x72 px, and `elementFromPoint` at its centre returns the anchor itself —
   nothing is covering it. This is not the panel-occlusion failure.
2. **`target="_blank"` routes to Capacitor's popup delegate.** Capacitor
   implements `webView:createWebViewWithConfiguration:forNavigationAction:windowFeatures:`
   — confirmed in the shipped binary and in
   `node_modules/@capacitor/ios/Capacitor/Capacitor/WebViewDelegationHandler.swift`.
   So this is *not* the classic WKWebView case where `target="_blank"` is
   ignored for want of a delegate.
3. **That delegate hands the URL to the operating system and opens no webview:**

   ```swift
   if let url = navigationAction.request.url {
       UIApplication.shared.open(url, options: [:], completionHandler: nil)
   }
   return nil
   ```

4. **The URL it hands over is `capacitor://localhost/map.html`, and iOS cannot
   open it.** The app registers no URL scheme — `Info.plist` has no
   `CFBundleURLTypes`. Asking the OS to perform exactly the operation
   Capacitor performs fails:

   ```
   $ xcrun simctl openurl booted "capacitor://localhost/map.html"
   LSApplicationWorkspaceErrorDomain error 115   (exit 115)
   $ xcrun simctl openurl booted "https://example.com"
   (exit 0)
   ```

   The `https://` control succeeds, so the refusal is about the scheme, not the
   command.

`return nil` means no new webview is created, and the failed `open` reports
nothing to the page. **The user taps a card and the app does nothing at all** —
no navigation, no error, no visible response. That is worse than a broken link,
because there is nothing on screen to distinguish it from a missed tap.

`map.html` itself is fine and is reachable at
`capacitor://localhost/map.html` — it was loaded directly and it draws. **The
file works; the button that opens it does not.**

**Fix in Phase 1, not now** (Phase 0 changes no app code). The likely fix is to
drop `target="_blank"` on same-origin internal links so they navigate in the
webview. Note that `target="_blank"` is doing real work on GitHub Pages, where
these open a tab and the launcher stays put — so this is a genuine divergence
between the two distributions, the same shape as the service-worker finding,
and not simply a mistake to delete.

**THE FIX IS DEMONSTRATED, BEFORE IT IS WRITTEN — 2026-07-28
[externally-verified].** In the Web Inspector console on the physical device,
`location.href = 'map.html'` **navigated**: the inspector's title changed to
`— localhost — map.html`, `location.href` read
`capacitor://localhost/map.html`, and `map.html` drew. This is a **same-origin
navigation inside the webview**; it never reaches
`webView:createWebViewWithConfiguration:` and so never hands a `capacitor://`
URL to `UIApplication.shared.open`. It is recorded as its own result, not folded
into the inset measurement, because it establishes the remedy independently:
**dropping `target="_blank"` on the three internal links should restore them.**

Two constraints that fall out of it and must survive into Phase 1:

- **Do not blanket-strip `target="_blank"`.** Of the 12 in `index.html`, only 3
  are internal and dead; the other 9 are `https://` and work correctly *because*
  of it — that is what the device control test established.
- The `https://` links opening externally is **correct behaviour** on both
  distributions and must not be "fixed".

*(A console error `leaflet.js.map couldn't be opened` appeared during this. That
is a source map requested only by the attached debugger; it is not fetched by
the app and is not a bundle defect.)*

**One link is inferred rather than observed end to end.** Step 1→2 — that a real
finger tap reaches the delegate — was not exercised. A scripted
`dispatchEvent(new MouseEvent('click'))` on the anchor produced no navigation,
no backgrounding, and no `pagehide`/`blur`/`visibilitychange`, and **no
`capacitor://` open attempt appeared in a system-wide log capture**, which means
WebKit blocked it upstream for want of a user gesture rather than the delegate
running and failing. Steps 2, 3 and 4 are verified independently of any gesture,
so the outcome does not depend on that link — but a real tap has not been
watched. Closing it needs a genuine HID event: no tap tooling exists on this
machine (`idb`, `fbsimctl`, `appium` all absent; `simctl` has no tap), so it
needs either Accessibility permission for **Terminal.app** so AppleScript can
click the Simulator window, or an XCUITest target.

### Safe-area insets on the device — text is SAFE, controls are NOT

Measured on the **physical iPhone 14** 2026-07-28 via Safari Web Inspector
against the **shipping bundle** — no instrumented copy, no re-sign, nothing
written to `docs/` [externally-verified]. All three results below are device
readings, not simulator ones.

**1. The land-status text is fully reachable. This is the clean result and it
should be read first.**

| | |
|---|---|
| text nodes walked in `#panelbody` (excl. `#status`) | 57 |
| hit-test sample points | **291** |
| reachable | **291** |
| covered | **0** |
| never on screen | **0** |
| **FAILS** | **0** |

Once the panel is open, **every land-status warning on `map.html` is readable on
the device.** CLAUDE.md's "layout is a way of deleting text" rule **does not
fire**. This was the thing most feared going into the device run — the panel
that carries the AVOID tiers, the BLM federal-register caveat and the
"we do not know how near the nearest state claim is" statement — and it did not
happen. Say so plainly; do not let it get buried under the two problems below.

The measurement is trustworthy on its own terms: `overflowY` computed to `auto`
with `scrollH 860` vs `clientH 844`, so the scroll range was genuine and gated
on computed overflow per the recorded `no-overflow` mutant gotcha, not merely on
`scrollTop` accepting a value.

**2. The CONTROLS are unreachable, and on `map.html` that is worse than the
launcher collision.**

`#panel` measures `top:0, left:0, w:390, h:844` — full-screen from y=0 on a
390x844 device. Its **top 47px sit inside the status-bar region**. The text
flows below that and survives, which is why result 1 is clean. **The toggle does
not.** Alan could not tap the panel's collapse/expand control on the device, and
the Leaflet zoom controls are equally unoperable — both render under the time
and battery icons.

`wasCollapsed: true` confirms `map.html:128` auto-collapses the panel at
`innerWidth <= 600`. So the **first** thing a user sees on the map is a
collapsed panel whose only control cannot be pressed.

Snippet C measured the panel at all only because it removes the `collapsed`
class **programmatically**, sidestepping the very control a finger cannot reach.
The measurement route and the user's route are not the same route, and that gap
is the finding.

**On `index.html` this collision is cosmetic — readable text under the clock. On
`map.html` it makes the map inoperable. The map draws and cannot be used.**

**3. The obvious fix would ship as a no-op. This is a constraint on the fix, not
a footnote.**

`env(safe-area-inset-*)` reads **`0px` on all four sides, on both pages**, while
a 47px notch physically exists. The cause is measured, not guessed:

- Neither `index.html` nor `map.html` sets **`viewport-fit=cover`**. Both carry
  only `width=device-width, initial-scale=1.0, maximum-scale=1.0,
  user-scalable=no`.
- The **only** `env()` in the entire tree is `index.html:166`, a
  `padding-bottom`.
- `innerWH == screenWH == [390, 844]` and `visualViewport.offsetTop == 0` — the
  webview is the full screen and **no inset is applied anywhere**.

Without `viewport-fit=cover`, iOS resolves `env(safe-area-inset-*)` to zero. So
a Phase 1 fix that adds `padding-top: env(safe-area-inset-top)` would ship,
compute to `padding-top: 0`, and change nothing on the device — while looking
correct in the diff and in every desktop browser. **`viewport-fit=cover` must
land first, or the padding does nothing.**

Corroborating geometry on the launcher: `headerRect.top` is **20**, so the
"Field Brain" header paints **27px inside** the 47px status-bar region.

### The class is now confirmed three times over

**Correct on GitHub Pages, broken in the iOS shell, nothing reported on screen.**
Three independent instances, all found on this project's first trip to a device:

| # | Mechanism | On Pages | In the shell |
|---|---|---|---|
| 1 | **Service worker** | `sw.js` is the whole update path | `navigator.serviceWorker` absent — never registers, silently |
| 2 | **`target="_blank"`** | opens a tab, launcher stays put | delegate hands `capacitor://` to iOS, which refuses it — **`map.html` unreachable** |
| 3 | **Safe-area insets** | irrelevant; a browser tab is already inset | webview is full-bleed, `env()` reads 0 — **map controls unusable** |

Each is a *divergence between two distributions*, not a bug in either one, and
each fails **silently** — no error, no console message, nothing on screen. That
is the shared shape, and it is the reason none of the three were found before a
device existed.

**This changes what Phase 1 is for.** It was filed as consolidation — routing
scattered HTML into one app, tidying the bundle/Pages divergence. It is now the
work that **makes the app usable on a phone at all**: the primary field tool
cannot be opened, and when reached by other means its controls cannot be
pressed. Priority accordingly.

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
- **The Apple Developer Program is paid and approved, and the Apple ID is added.**
  `isFreeProvisioningTeam = 0`, `teamType = Individual`, team `PWCMJWTT6J`
  "Alan Fuller"; 4 valid `Apple Development` certificates issued 2026-07-28,
  `OU=PWCMJWTT6J`, valid to 2027 [self-tested] 2026-07-28
- **Phase 0's remaining blocker is a data cable, not a decision.** No physical
  device is visible (`devicectl list devices` → `No devices found`), so no
  device can be registered, so no provisioning profile can be generated. The
  device build fails at `GatherProvisioningInputs` on "No profiles ... were
  found" — past team and certificate resolution [self-tested] 2026-07-28
- **`target="_blank"` links are dead under Capacitor.** The delegate calls
  `UIApplication.shared.open()` on a `capacitor://` URL and returns nil; iOS
  refuses that scheme (`simctl openurl` → LS error 115, vs exit 0 for
  `https://`). All three Field tools buttons silently do nothing
  [self-tested] 2026-07-28
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
- **The iPhone 14 is visible to the toolchain**, not merely to Finder: UDID
  `00008110-0006398C0ABA401E`, `paired` / `connected` / `wired`, iOS 26.5.2
  [self-tested] 2026-07-28
- **Developer Mode gates destination resolution, which runs before provisioning.**
  With it disabled, `xcodebuild` exits **70** on "Timed out waiting for all
  destinations", listing the device with `error:Developer Mode disabled` — no
  signing error is reached at all. After enabling, `developerModeStatus enabled`
  and `ddiServicesAvailable true` [self-tested] 2026-07-28
- **The four earlier `Apple Development` certificates were issued to a different
  machine and their private keys were never on this Mac.** `find-identity -v`
  returned 0 across **all** policies, not just codesigning, while 4 certs sat in
  `login.keychain-db`; Xcode's build error named the missing private key
  explicitly. Revoked at developer.apple.com, reissued via Manage Certificates →
  ＋, which generated the keypair locally → **1** valid identity
  [self-tested] 2026-07-28
- **A provisioning profile exists for the first time in this project's history.**
  `iOS Team Provisioning Profile: *`, team `PWCMJWTT6J`, AppID `PWCMJWTT6J.*`,
  `ProvisionedDevices` = exactly `00008110-0006398C0ABA401E`, expires
  2027-07-28 [self-tested] 2026-07-28
- **The device build is signed with a real certificate chain**, unlike the
  simulator's ad-hoc `--sign -`: authority `Apple Development: Alan Fuller
  (VSSL232H55)` → Apple WWDR CA → Apple Root CA, `TeamIdentifier PWCMJWTT6J`,
  entitlement `application-identifier PWCMJWTT6J.io.github.alanfuller15.fieldgold`,
  and `codesign --verify --deep --strict` exits 0 "satisfies its Designated
  Requirement" [self-tested] 2026-07-28
- **The device bundle is `docs/` exactly**, same as the simulator's: `diff -rq`
  reports only `cordova.js` and `cordova_plugins.js` as extra, 26 files, all
  five stage maps present, **0** `.py` or `test_*` files [self-tested] 2026-07-28
- **FieldGold is installed, launched and running on a physical iPhone.**
  Install confirmed by independent lookup (`devicectl device info apps` →
  `FieldGold 1.0`), launch confirmed by process lookup (PID 814 at the bundle
  UUID the install returned) rather than by either command's own success message
  [self-tested] 2026-07-28
- **`index.html` renders and is interactive on the physical device** — launcher
  drawn, Tools sheet opens, Knowledge tab renders, external link opens
  [externally-verified] 2026-07-28
- **The dead `target="_blank"` links are confirmed on physical hardware with a
  real finger**, with an `https://` control on the same anchor pattern, same
  delegate and same gesture that **did** open. The scheme is the only variable
  [externally-verified] 2026-07-28
- **`map.html` is unreachable from the app UI on a phone.** It is referenced
  exactly once in `index.html` (line 2766) and that reference is the dead
  anchor; there is no other link, `location.href` or `window.open` to it. Same
  for `bench_hunter.html` and `creek_manual.html` [self-tested] 2026-07-28
- Of 12 `target="_blank"` links in `index.html`, **3 are internal and dead, 9
  are `https://` and work**. A blanket strip would break the nine
  [self-tested] 2026-07-28
- **Capacitor ships as a `binaryTarget` xcframework, so `#if DEBUG` inside it is
  resolved at Ionic's build time, not ours** — our build compiled 0 Capacitor
  Swift files. Web inspection therefore depends on the `CAPACITOR_DEBUG`
  Info.plist fallback, which **is** satisfied: the built `Info.plist` carries
  `CAPACITOR_DEBUG = true`, so `webView.isInspectable` is true and Safari Web
  Inspector can attach [self-tested] 2026-07-28
- **The land-status warning text on `map.html` is fully reachable on the
  physical device.** 291 of 291 hit-test sample points across 57 text nodes in
  `#panelbody` (excluding `#status`) resolved to the text's own element — 0
  covered, 0 never-on-screen, **FAILS 0**. Scroll range gated on computed
  `overflow-y: auto` (`scrollH 860` / `clientH 844`), not on `scrollTop`
  accepting a value [externally-verified] 2026-07-28
- **`map.html`'s panel controls are unusable on the device.** `#panel` measures
  `top:0 left:0 w:390 h:844`, so its top 47px lie under the status bar. Alan
  could not tap the collapse/expand toggle, and the Leaflet zoom controls are
  equally unoperable. `wasCollapsed: true` — the panel auto-collapses at phone
  width (`map.html:128`), so the first sight of the map is a collapsed panel
  whose only control cannot be pressed. **The map draws and cannot be used**
  [externally-verified] 2026-07-28
- **`env(safe-area-inset-*)` reads `0px` on all four sides on BOTH pages** while
  a 47px notch physically exists, because **neither page sets
  `viewport-fit=cover`** and the only `env()` in the tree is
  `index.html:166` (a `padding-bottom`). `innerWH == screenWH == [390,844]` and
  `visualViewport.offsetTop == 0` — the webview is full-bleed with no inset
  applied. **A fix adding `padding-top: env(safe-area-inset-top)` without
  `viewport-fit=cover` computes to 0 and ships as a no-op**
  [externally-verified] 2026-07-28
- The launcher header paints **27px inside** the status-bar region:
  `headerRect.top` is 20 against a 47px inset [externally-verified] 2026-07-28
- **`navigator.serviceWorker` is absent on the physical device too**, confirming
  the simulator finding on real hardware; `isSecureContext` is `true`
  [externally-verified] 2026-07-28
- **Same-origin in-webview navigation works on the device**:
  `location.href = 'map.html'` navigated to `capacitor://localhost/map.html` and
  the map drew, without touching the `createWebViewWith` delegate. Phase 1's
  likely fix for the dead internal links, demonstrated before being written
  [externally-verified] 2026-07-28
- **Safari Web Inspector measures the SHIPPING bundle.** All device page
  measurements above were taken against the installed, unmodified app over USB —
  no instrumented copy, no re-sign, no reinstall, nothing written to `docs/`. The
  caveat the simulator findings had to carry does not apply to them
  [self-tested] 2026-07-28

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

> **Phase 1's scope grew on 2026-07-28 and its priority changed.** The device
> run found **three** silent divergences between the Pages build and the iOS
> shell — service worker, `target="_blank"`, safe-area insets — two of which
> make the app unusable rather than untidy: the primary field tool cannot be
> opened, and when reached by other means its controls cannot be pressed. The
> bundle/Pages exclusion described below is now the *smallest* of Phase 1's
> items. See "The class is now confirmed three times over" for the set, and note
> the constraint that `viewport-fit=cover` must precede any `env()` padding or
> the fix is a no-op.

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

- ~~Apple Developer Program ($99/yr) vs free 7-day provisioning.~~
  **DECIDED and PAID 2026-07-28 — Developer Program, enrollment approved.**
  The reasoning was the one this line already carried: free provisioning expires
  after 7 days, and an app that dies in the field cannot be re-signed from a
  riverbank. Verified from the machine, not taken on report —
  `com.apple.dt.Xcode` `IDEProvisioningTeamByIdentifier` reads
  `isFreeProvisioningTeam = 0`, `teamType = Individual`, `teamID = PWCMJWTT6J`,
  `teamName = "Alan Fuller"` [self-tested]. A free Personal Team would read
  `isFreeProvisioningTeam = 1`; this is the paid membership.

**No open decisions remain in Phase 0.** What blocks it now is hardware — see
Next action.

## Deliberately not built yet

These were considered and deferred. Do not start them without Alan saying so.

- MCP verification server (ARDF / BLM / USGS)
- iOS build automation in CI
- Any Phase 1-4 work

## Next action

**The cable arrived and Phase 0's device path is essentially done.** Signing is
resolved, the device is registered, a profile exists, the app is built with a
real certificate chain, installed, launched, and `index.html` renders on Alan's
iPhone 14. What remains in Phase 0:

1. ~~Measure `map.html`'s safe-area insets on the device.~~ **DONE
   [externally-verified] 2026-07-28** via Safari Web Inspector against the
   shipping bundle. Text safe (FAILS 0); controls unusable; the obvious fix
   would be a no-op without `viewport-fit=cover`. See the safe-area section.
2. ~~The header/status-bar collision on `index.html`.~~ **DONE
   [externally-verified] 2026-07-28** — confirmed on real hardware, not a
   simulator artifact.
3. **The step-5 commit.** `ios/App/App.xcodeproj/project.pbxproj` lands together
   with the profile and the first device install, as one coherent change — the
   condition the residue set for it has been met.

**Phase 0 is otherwise complete.** What remains is Phase 1, and its scope has
changed: see "The class is now confirmed three times over".

*Historical, retained: the blocker for most of 2026-07-28 was a Lightning cable
that carries data. It arrived. Everything below this line was written under that
block and is kept because the reasoning is still legible.*

*Session residue from the 2026-07-28 simulator run is at the end of this file —
read it before re-testing anything, particularly before spending a round on
certificates or on GUI automation.*

Everything else in step 5 is done. The Developer Program is paid and approved,
the Apple ID is added, the team is set on both build configurations, automatic
signing is on, and four valid development certificates exist. None of it can
produce a provisioning profile, because a profile must name a registered device
and no device can be registered over a cable that carries no data.

**Do not spend another round on certificates.** Four have been issued and
revoked already; the build does not fail on certificates. It fails on the
profile, and it will keep failing on the profile until the phone can be seen.

Once a working cable exists, in order:

1. Connect the iPhone 14 and confirm **Finder sees it** — that is the check
   that the cable carries data, and it is cheaper than discovering it in Xcode.
2. Trust the Mac on the phone, then let Xcode register the device.
3. Re-run the device build. If it now fails with `no identity found` rather
   than a profile error, that is the keychain anomaly recorded above, not a new
   problem — let Xcode's GUI reissue the certificate.
4. Then, and only then, the device rows in the status table can move.

Everything achievable without a physical device has been done and verified. The
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

- ~~**Exercise the `target="_blank"` links.**~~ **CLOSED 2026-07-28 on physical
  hardware.** Dead, with an `https://` control that opened. And worse than
  recorded: `map.html` is unreachable from the app UI entirely. Phase 1 item,
  now a priority one; see "The Field tools buttons are dead in the shell".
  Original text kept below.
- **Exercise the `target="_blank"` links.** `map.html` was reached directly, not
  through the Field tools button. Whether that button works in the shell is
  untested and is the first thing to tap on the device.
- ~~**Check the safe-area insets.**~~ **CLOSED 2026-07-28 on physical hardware,
  and the answer is split.** The land-status **text is safe** — 291/291 sample
  points reachable, FAILS 0, so "layout is a way of deleting text" does not
  fire. The **controls are not** — `map.html`'s panel toggle and the Leaflet
  zoom controls sit under the status bar and cannot be tapped, making the map
  inoperable. And `env(safe-area-inset-*)` reads 0 on both pages for want of
  `viewport-fit=cover`, so the obvious fix would ship as a no-op. See the
  safe-area section.

The procedure for the Capacitor half is
**`.claude/skills/phase-0-shell/SKILL.md`** — Capacitor init, `cap add ios`,
signing, provisioning, first device install. That file is how; this file is
how far. Update the tables above as its steps land, and record the tier
([self-tested] / [fetched] / [externally-verified]) under Verified facts.
Phase 0a had no runbook — the breakage inventory above was what there was, and
it is now closed history.

## Session residue — 2026-07-28, simulator run

Reasoning that produced the entries above and is not recoverable from them.
Nothing here repeats a conclusion; read the sections above for those.

### Test the mechanism, not the gesture — the method that unblocked this session

The `target="_blank"` question looked blocked. Answering it seemed to need a
real finger tap, there is no tap tooling on this machine (`idb`, `idb_companion`,
`fbsimctl`, `appium` all absent; `simctl` has no tap verb), and a scripted
`dispatchEvent(new MouseEvent('click'))` is not a user gesture — WebKit blocked
it upstream, which was confirmed rather than assumed: a **system-wide** log
capture across the click showed **no `capacitor://` open attempt at all**, so
the delegate never ran.

What broke it open was reading Capacitor's handler and noticing the chain had a
**second half that needs no gesture**:

```swift
UIApplication.shared.open(url)   // capacitor://localhost/map.html
return nil
```

`simctl openurl booted "capacitor://localhost/map.html"` asks the OS to perform
*exactly that call*. It fails with `LSApplicationWorkspaceErrorDomain 115`, and
an `https://` control returns 0 — so the refusal is the scheme, not the harness.
The gesture only governs whether the delegate is *reached*; it has no bearing on
what the delegate *achieves*, and the second half is where the failure lives.

**Generalise this before reaching for automation.** When something seems to need
a real tap, split the chain at the point where it leaves the webview and hands
off to the OS or the native layer. The native half is almost always drivable
from the CLI — `simctl openurl`, `simctl launch`, `simctl push`, a direct
`xcodebuild` — and it is usually the half that decides the outcome. A missing
tap blocks far less than it first appears.

### The Accessibility grant was considered and declined

The one route to a genuine HID tap was granting Accessibility to **Terminal.app**
(`/System/Applications/Utilities/Terminal.app`, established by walking the
parent-process chain — it is the host, not `claude`). Alan offered it.

Declined, for a stated cost: macOS commonly requires quitting and reopening an
app after that toggle, and quitting Terminal **ends the Claude Code session**.
That is a real price for one inferred link, and steps 2–4 of the chain were
already verified without it — the delegate's behaviour, the URL it constructs,
and the OS's refusal of that URL. The outcome does not depend on the unobserved
link, only the completeness of the walk-through does.

**If a later session wants it anyway:** System Settings → Privacy & Security →
Accessibility → enable Terminal. Then AppleScript can address the Simulator
window (`tell application "System Events" to tell process "Simulator"`), which
currently fails with `-1719 osascript is not allowed assistive access`. Worth it
only if something genuinely gesture-gated turns up — a popup, a permission
prompt, a drag. It was not worth it for this.

### `find-identity` — hypothesis, and the exact trigger to re-check it

> **CLOSED 2026-07-28. The hypothesis below is REFUTED.** It was not the
> data-protection keychain and `find-identity` was not the wrong instrument —
> the certificates were issued to another machine and the private keys never
> existed here. See "RESOLVED — the certificates belonged to another machine"
> above. The re-check trigger written below did fire exactly as specified, which
> is the part worth keeping: the device build was run once a profile existed,
> and it failed on the certificate rather than the profile. Retained unedited so
> the reasoning that produced a wrong answer stays legible.

`security find-identity -v -p codesigning` → **0 identities**, and
`codesign --sign "Apple Development: Alan Fuller (VSSL232H55)"` →
`no identity found`, while four unexpired certificates for that exact common
name sit in `login.keychain-db`. An identity is a certificate **plus its private
key**, so the tooling cannot pair them.

Ruled out by test, not by reasoning: the keychain being locked (it reports
`no-timeout` and unlocked), and this shell's sandbox (the same command run with
the sandbox disabled returns the same 0).

**The hypothesis — untested — is that Xcode 26 stores signing keys in the
data-protection keychain, which the legacy `security` CLI cannot enumerate.**
If so, `find-identity` is simply the wrong instrument and nothing is wrong.

**Re-check trigger, and it is specific:** once a cable exists and a provisioning
profile has been issued, run the device build. If it fails with
**`no identity found`** — as opposed to a profile error — *this is why*. Do not
treat it as a new problem, and do not chase it from the CLI. The fix is to let
Xcode's GUI reissue the certificate into the login keychain. Until a profile
exists this cannot bite, because the build fails at `GatherProvisioningInputs`,
which runs *before* code signing. That ordering is the reason it was left open
rather than pursued.

### The pbxproj change is intentional, and has now survived two commits on purpose

`ios/App/App.xcodeproj/project.pbxproj` carries `DEVELOPMENT_TEAM = PWCMJWTT6J`
on both Debug and Release. Xcode wrote it when Alan selected the team. It is
**uncommitted by decision**, and has now been **excluded from two commits with
the reason stated in each** — `0265738` (PR #1) and `cd42c73` (PR #2), in both
the commit message and the PR body.

**A third session must not "clean it up".** It is neither drift nor a stray
edit: it is the one piece of runbook step 5 that has landed, and it belongs to
the commit that completes signing — the one that can only be written once a
device has been registered. Reverting it would silently undo a real
configuration change and make the next Xcode session redo it. Committing it
early would attach step 5's only artifact to a documentation commit and make the
signing history unreadable.

The correct move is to leave it alone until the cable arrives, then commit it
**with** the profile and the first device install, as one coherent step-5
change.

### Threads deliberately not pulled

- **Offline behaviour was never exercised.** The Mac had network throughout, so
  48 basemap tiles loaded and `map.html`'s "basemap tiles unavailable — no
  signal" path never ran. This is the single most field-relevant untested thing
  about the shell, and it is now *more* interesting than before: with `sw.js`
  inert, the shell's offline story rests entirely on bundle-local assets and has
  never been observed. Testable on the simulator without a cable — toggle the
  host's network, or use Network Link Conditioner — and it was left only for
  scope.
- **Safe-area insets** were observed failing on the launcher header and not
  measured on `map.html`'s panel, which is the one that carries land-status
  warnings. `tests/test_panel_reachability.py` already exists and hit-tests
  warning text at phone viewports; it does not know about Capacitor's insets.
  Extending it is the obvious move and was out of Phase 0's scope.
- **The stage maps ship in the bundle and were not opened on the simulator.**
  They carry the ARCHIVED banner, so this is low-risk, but "present in the
  bundle" is all that has been verified about them under Capacitor.

### Method note for whoever instruments the app next

Capacitor **does not** forward `console` to the system log by default, so the
shipping bundle cannot report on itself and `log stream` will show nothing from
page JS. Two things that do work, both used here: write results to
`localStorage` and read the container's `localstorage.sqlite3` off disk (values
are **UTF-16LE**, and the payload lives under key `fieldgold_record` as
`{updated, entries}`); or render into a fixed full-screen `<pre>` and screenshot
with `simctl io booted screenshot`. The pattern that keeps this legitimate is to
append the diagnostic to a **copy** of the built `App.app` in the scratchpad,
ad-hoc re-sign it (`codesign --force --sign -`), install, read, then reinstall
the clean build and confirm the diagnostic is absent from the installed bundle.
`docs/` is never touched. Note also that a project hook blocks the Write tool
outside the repo — Alan authorised the scratchpad write explicitly, which is the
remedy the hook itself names.

## Session residue — 2026-07-28, DEVICE run

**Phase 0 is complete and merged (PR #4, `main` at `e7534e4`). Nothing was in
flight when this session ended.** The tree is clean, `main` is in sync, all 12
suites pass, and the step-5 commit that had been deferred through two PRs has
landed. This section is the reasoning behind the device findings, which is not
recoverable from the findings themselves. Nothing here repeats a conclusion.

### The Web Inspector method — and the check that made it more than a plausible idea

**Every device page measurement in this file was taken against the SHIPPING
bundle** — Safari Web Inspector over USB, attached to the installed,
unmodified app. No instrumented copy, no re-sign, no reinstall, nothing written
to `docs/`. **This removes the caveat every simulator finding had to carry**
("these numbers came from an instrumented copy, not from the shipping bundle
reporting on itself"). Prefer this route over the instrumented-copy method
recorded above whenever a device is attached; that method is now the fallback,
not the default.

**It was nearly not available, and the check that established it is the part
worth keeping.** Capacitor sets `webView.isInspectable = isWebDebuggable`, and
`isWebDebuggable` comes from `#if DEBUG` in `CAPInstanceDescriptor.swift`. The
tempting inference — "we built Debug, so DEBUG is set" — is **wrong**.
Capacitor ships as a **`binaryTarget` xcframework**: our build compiled **0**
Capacitor Swift files and passed it no `-D DEBUG`, so that `#if` was resolved
when Ionic built the framework, not by our configuration. The code has a
fallback for exactly this case (its own comment says "this is needed for SPM
xcframework Capacitor"): a `CAPACITOR_DEBUG` Info.plist key. The **built**
`Info.plist` carries `CAPACITOR_DEBUG = true`, so inspection works.

That check took one command and is the difference between proposing something
grounded and proposing something plausible. **If a future Capacitor upgrade
moves to a source-based SPM package, or a Release build is used, re-run it
before assuming the inspector will attach.**

**The route onto `map.html` matters as much as the inspector.** Once the UI
route proved dead, the panel could only be reached by typing
`location.href = 'map.html'` in the console. That is a **same-origin navigation
inside the webview**, which never enters
`webView:createWebViewWithConfiguration:` and so never hands a `capacitor://`
URL to `UIApplication.shared.open`. It is both the measurement route and,
incidentally, the proof of Phase 1's fix.

### The measurement route and the user's route were not the same route

**This is the finding that would have been missed by trusting the numbers.**

Snippet C reports `FAILS 0` — every one of 291 sample points reachable. Read
alone, that says the panel is fine. It is not. The snippet could only measure
the panel because it does `panel.classList.remove('collapsed')`
**programmatically** — sidestepping the exact toggle that a finger cannot reach,
because that toggle sits under the status bar. The panel auto-collapses at phone
width, so the user's first sight of the map is a collapsed panel with an
unpressable control.

**A green measurement obtained by a route the user does not have is not a green
user experience.** The clean number and the broken experience are both true, and
they are about different things: the text is reachable *given* an open panel,
and the user cannot open the panel. Alan's report of what he could not tap is
what caught this; no automated measurement in this session would have.

This is the same family as the existing `no-overflow` mutant note — `scrollTop`
succeeding on an `overflow-y:hidden` element proves text is *programmatically
addressable*, not that a finger can get to it. Here the identical trap appeared
one level up, on the control rather than the content.

### Two wrong hypotheses in the same direction — the instrument lesson

This file recorded **two** explanations for `security find-identity` reporting
0 identities: first "no Apple ID has been added", then "Xcode 26 stores keys in
the data-protection keychain, so `find-identity` is the wrong instrument". Both
were wrong, and **wrong in the same direction — each assumed the tool was
looking in the wrong place.**

It was reporting the literal truth. The certificates had been issued to a
**different machine** and their private keys never existed on this one. An
identity is a certificate plus its private key; there were no identities.

**The inverse of the family this project already knows.** `cap open ios` exiting
0, a Pages `built` status naming an earlier commit, `caches.open()` creating an
empty cache that `in caches.keys()` reports as present — all tools reporting
**success** that meant nothing. This was a tool reporting **failure** that meant
exactly what it said, and it was disbelieved for a whole session.

The cheap check that would have settled it: `find-identity -v` **without**
`-p codesigning` returns 0 across *all* policies, which no keychain-location
story explains. **Check an instrument's claim against a second source before
concluding the instrument is broken.**

### An early gate hides every later one

Developer Mode gates **destination resolution**, which runs *before*
provisioning. With it disabled, `xcodebuild` exits **70** on "Timed out waiting
for all destinations" and **no signing error is ever produced** — the device is
listed with `error:Developer Mode disabled` and nothing about certificates or
profiles is evaluated.

That is the same shape as `GatherProvisioningInputs` running before code
signing, which is precisely why the certificate problem stayed invisible for an
entire session: the build kept failing on the profile, so the certificate never
got a chance to fail. **Three stages, each masking the next.** When a pipeline
has ordered gates, a failure at stage N tells you nothing about stages N+1
onward — and "we fixed the thing it complained about" can be true three times
before the real problem surfaces.

### Constraints that forced the method — named so they do not read as choices

- **The device delegate could not be watched from the Mac.** `log stream` in
  this macOS build has **no `--device-udid`** option, and `idevicesyslog`,
  `ideviceinfo` and `ios-deploy` are all absent. So the plan to observe the
  `capacitor://` open attempt live was abandoned — not rejected on merit.
- **`devicectl` has no `openurl` verb.** The `simctl openurl` split-the-chain
  trick that answered this question on the simulator has **no device analogue**.
  What replaced it was the `https://` control test through the *same* anchor
  pattern and delegate — which is arguably better evidence, since it varies only
  the scheme, but it was chosen under constraint.
- **Alan's finger was the only available HID.** Accessibility for Terminal
  remains ungranted, for the reason recorded in the simulator residue: the
  toggle typically requires quitting Terminal, which ends the Claude Code
  session. Unchanged, and it did not need to change.
- **A project hook blocks the `Write` tool outside the repo.** A helper script
  for the log capture was blocked; the work was done with inline `bash -c`
  instead. No scratchpad authorisation was needed this session.
- **macOS has no `timeout`**, and zsh mangled a compound backgrounded command
  (`log ... & sleep; kill` → "too many arguments"). `bash -c '...'` gives
  predictable parsing for that shape.

### Small traps that cost time here and will cost it again

- **`devicectl device info processes` lists by executable path, and this app's
  executable is named `App`, not `FieldGold`.** Grepping the process list for
  the app name or bundle id finds **nothing on a perfectly healthy running
  app**, which reads exactly like a crash on launch. Grep the **bundle UUID**
  that `install` printed instead — here `57A8A239-…`.
- **`devicectl`'s `install` and `process launch` both print success messages
  that are the command reporting on itself.** Confirm with
  `device info apps --bundle-id …` and `device info processes`. Both were used
  here and both are cheap.
- **A `leaflet.js.map` console error appears under the inspector.** It is a
  source map requested only by the attached debugger, not fetched by the app.
  Not a bundle defect; ignore it.

### The measurements' bounds

One device, one orientation, one OS. **iPhone 14 (`iPhone14,7`), iOS 26.5.2,
portrait, 390x844 at dpr 3, Debug build.** The 47px top inset is a notch
figure — a Dynamic Island device reads 59px, and the simulator work was done on
an iPhone 17 Pro, so the two sets of numbers are not directly comparable.
**Landscape was never measured**, and landscape is where left/right insets
appear; the panel's behaviour there is unknown.

### Threads deliberately not pulled

- **Offline behaviour — still the most field-relevant untested thing about this
  app, and now untested on *three* targets.** Both the Mac and the phone had
  network throughout, so `map.html` drew its basemap tiles and the
  "basemap tiles unavailable — no signal" path **has never run anywhere**. With
  `sw.js` inert in the shell, the shell's entire offline story rests on
  bundle-local assets and **has never been observed**. This is testable without
  any new hardware — put the phone in Airplane Mode with the inspector attached.
  It was left purely for scope, twice now.
- **The stage maps still have not been opened on any target.** "Present in the
  bundle" remains the only thing verified about them under Capacitor.
- **The nine working `https://` links were not individually exercised** — one
  YouTube link was tapped as the control. The other eight are inferred from the
  same mechanism.
- **`tests/test_panel_reachability.py` was not extended to simulate Capacitor's
  insets.** It is the obvious durable tripwire and belongs in Phase 1. Note it
  can only ever be a simulation — it cannot produce an `[externally-verified]`
  result, so it complements the device measurement rather than replacing it.

### Two constraints on Phase 1's fixes, both established by measurement

Recorded here because both are the kind of thing a confident fix gets wrong.

1. **Do not blanket-strip `target="_blank"`.** Of the 12 in `index.html`, only
   **3** are internal and dead. The other **9** are `https://` and work
   *because* of it — stripping them would break nine working links to fix three
   broken ones. Fix the three by href, not the attribute globally.
2. **`viewport-fit=cover` must land before any `env()` padding.** Without it
   `env(safe-area-inset-*)` computes to `0`, so a `padding-top:
   env(safe-area-inset-top)` fix would ship, look correct in the diff, pass in
   every desktop browser, and change **nothing** on the phone.

### Next action

**Start Phase 1, and start it with the three shell divergences rather than with
consolidation.** In hand: `map.html` is unreachable (fix the 3 internal hrefs,
not the attribute); the map's controls are under the status bar
(`viewport-fit=cover` first, then insets); `sw.js` is inert in the shell so
updates arrive only via `npx cap sync` + rebuild. Nothing is blocked — the
device, the cable, the signing and the inspector route all work. The one thing
worth doing *before* writing any fix is the offline test above, because it is
cheap, it needs no new hardware, and it is the last unmeasured thing that
decides whether this app functions where it is actually used.
