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
You can repeat it yourself in one command:

```
python3 - <<'EOF'
import hashlib, base64
for f, want in [
    ("vendor/leaflet/leaflet.js",  "sha256-20nQCchB9co0qIjJZRGuk2/Z9VM+kNiyxNV1lvTlZBo="),
    ("vendor/leaflet/leaflet.css", "sha256-p4NxAoJBhIIN+hmNHrzRCf9tD/miZyoHS5obTRR9BMY="),
]:
    got = "sha256-" + base64.b64encode(hashlib.sha256(open(f, "rb").read()).digest()).decode()
    print(("ok   " if got == want else "BAD  "), f, got)
EOF
```

`tests/test_offline_map.py` runs this comparison as an assertion, so a
silently-swapped Leaflet fails the suite rather than shipping.

## Why `.gitattributes` marks this directory binary

`leaflet.css` ships with **CRLF** line endings. Git diffed it as text, and the
round trip through a patch file normalised them — the file still worked, since
CSS does not care, but its sha256 no longer matched the hash above. That is
worse than a broken file: the provenance claim silently stopped being true
while everything looked fine.

It was caught by `tests/test_offline_map.py` running against the applied tree
during the 0005 delivery verification, not by inspection. `.gitattributes` now
marks `vendor/leaflet/**` as `binary` so the bytes survive a patch and a
checkout exactly. Do not remove that line, and do not "clean up" the line
endings in `leaflet.css` — the CRLFs are part of what leafletjs.com hashed.

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
