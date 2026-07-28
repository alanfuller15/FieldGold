# Leaflet 1.9.4 — vendored

These files are not written by this project. They are Leaflet 1.9.4, copied in
so the map does not need a network connection to exist.

## Why they are here at all

Every map page used to load Leaflet from
`https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/leaflet.min.js`.

That is a runtime dependency on a third-party host, on an app whose whole
purpose is to work at a trailhead with no signal. It was confirmed empirically
while writing `tests/test_map_sites.py`: with no network, `window.L` is
`undefined` and the page's own status log reads "Leaflet failed" — no map, no
markers, no land-status colours, nothing. Rule 2 in `CLAUDE.md` already
forbade this; the code simply predated the rule.

## Where the bytes came from

Downloaded from the npm registry as `leaflet@1.9.4`:

```
npm pack leaflet@1.9.4
```

| check | value |
|---|---|
| tarball sha1 | `23fae724e282fa25745aff82ca4d394748db7d8d` |
| tarball sha512 | `sha512-nxS1ynzJOmOlHp+iL3FyWqK89GtNL8U8rvlMOsQdTTssxZwCXh8N2NB3GDQOL+YR3XnWyZAxwQixURb+FA74PA==` |

Both match npm's published `dist.shasum` and `dist.integrity` for that version.
That check is registry-internal, though — the registry told me both the file
and the hash, so on its own it proves only that the download was not corrupted.

## The check that actually means something

The subresource-integrity hashes published on **leafletjs.com**, an independent
source from npm, were fetched and compared against these exact bytes:

| file | published SRI (leafletjs.com) | matches |
|---|---|---|
| `leaflet.js` | `sha256-20nQCchB9co0qIjJZRGuk2/Z9VM+kNiyxNV1lvTlZBo=` | yes |
| `leaflet.css` | `sha256-p4NxAoJBhIIN+hmNHrzRCf9tD/miZyoHS5obTRR9BMY=` | yes |

Two independent publishers agreeing on the bytes is the claim being made here.
You can repeat it yourself in one command, **run from the repo root** — the
paths below carry the `docs/` prefix Phase 0a introduced, and without it the
snippet fails with `FileNotFoundError` rather than reporting `BAD`:

```
python3 - <<'EOF'
import hashlib, base64
for f, want in [
    ("docs/vendor/leaflet/leaflet.js",  "sha256-20nQCchB9co0qIjJZRGuk2/Z9VM+kNiyxNV1lvTlZBo="),
    ("docs/vendor/leaflet/leaflet.css", "sha256-p4NxAoJBhIIN+hmNHrzRCf9tD/miZyoHS5obTRR9BMY="),
]:
    got = "sha256-" + base64.b64encode(hashlib.sha256(open(f, "rb").read()).digest()).decode()
    print(("ok   " if got == want else "BAD  "), f, got)
EOF
```

`tests/test_offline_map.py` runs this comparison as an assertion, so a
silently-swapped Leaflet fails the suite rather than shipping.

## The CRLF trap, and what is actually guarding it

`leaflet.css` ships with **CRLF** line endings. Git diffed it as text, and the
round trip through a patch file normalised them — the file still worked, since
CSS does not care, but its sha256 no longer matched the hash above. That is
worse than a broken file: the provenance claim silently stopped being true
while everything looked fine.

It was caught by `tests/test_offline_map.py` running against the applied tree
during the 0005 delivery verification, not by inspection.

**Correction, 2026-07-28 (reconciliation pass).** This section used to be
headed "Why `.gitattributes` marks this directory binary" and stated that
`.gitattributes` marks `vendor/leaflet/**` as `binary`, ending "Do not remove
that line." **There is no `.gitattributes` in this repository and there never
has been** — `git log --all -- .gitattributes` is empty. The line the section
told you not to remove does not exist to remove.

What is true, measured the same day:

- `docs/vendor/leaflet/leaflet.css` in the worktree is 661 CRLF, 0 bare LF, and
  hashes to `sha256-p4NxAoJBhIIN+hmNHrzRCf9tD/miZyoHS5obTRR9BMY=` — the
  published value. The stored blob carries the same 661 CRLF. `[self-tested]`
- The bytes survive because `core.autocrlf` is unset (it defaults to `false`)
  and no attribute forces a conversion, so git stores and checks out these
  bytes as-is. That is a **property of the current checkout's configuration**,
  not a property of the repository.
- The guard that actually holds is `tests/test_offline_map.py`, which asserts
  both hashes on every run. It has caught this once already.

So the conclusion stands and the mechanism named for it did not exist: do not
"clean up" the line endings in `leaflet.css` — the CRLFs are part of what
leafletjs.com hashed. **Open, filed not fixed:** a checkout under
`core.autocrlf=true` (the Windows default) or `input` would normalise this file
and break the hash, and nothing in the repository prevents that. Adding a
`.gitattributes` with `docs/vendor/leaflet/** binary` would close it. That is
new work and was deliberately not done in a reconciliation pass.

## Naming

npm ships the minified build as `dist/leaflet.js`. cdnjs renames the same bytes
to `leaflet.min.js`. The file here keeps the npm name. It is minified — the
first line is the `@preserve` banner and the rest is one long line.

`leaflet-src.js`, the source maps, and the ESM build were deliberately **not**
vendored. They are development aids and would roughly triple what a phone has
to cache.

## The images

`leaflet.css` references `images/marker-icon.png`, `images/marker-shadow.png`
and the layers-control icons by relative path. They must stay in `images/`
directly beside the CSS or the default marker icons render as broken images —
which on this app would be a marker you cannot see, on ground you cannot dig.

## Upgrading

Do not edit these files. To move to a new Leaflet version: `npm pack
leaflet@X.Y.Z`, copy `dist/leaflet.js`, `dist/leaflet.css` and `dist/images/*`
into place, update the hashes in this file **and** in
`tests/test_offline_map.py`, bump the `sw.js` cache version, and run the suites.
If the hashes in the test are not updated, the suite fails — which is the
intended behaviour, not an obstacle.

## What this does NOT fix

Leaflet is the map *library*. The basemap **tiles** still come from OpenStreetMap,
Esri and OpenTopoMap over the network, and they are not vendored — a full tile
cache for this area is a different job with a different size budget. With no
signal you now get a working map with your benches, your logged sites, their
land-status colours and their popups, drawn on a blank background instead of
nothing at all. `map.html` says so on screen rather than leaving you to guess
whether the app is broken.
