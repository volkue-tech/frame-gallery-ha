# Current-artwork preview — local/offline validation, 2026-10-22

Unreleased D-246 feature. No version bump, public push, release, HA/TV connection,
installed update/restart, image send or installed card/script/configuration change
is included. The user's installed b16 remains outside this implementation task.
No native Terminal window or credential session was opened for this feature.

## D-249 release-candidate correction

Independent b17 review found that the normal first thumbnail caption resolves
to a Binding, not a DeliveryAssociation, so the initial image could be absent.
Keep caption provenance unchanged and verify the already received thumbnail
against the exact archived delivered reference locally. Only a session-local
observation/receipt proof can select its matching preview; a changed receipt,
TV, content, digest or session invalidates it. No additional TV I/O or stored
schema is added. Matching title/artist alone is insufficient for reused IDs.
Optional verification/read failure preserves an already valid caption without
granting an image; a definitive mismatch remains rejected.

22 new cases were observed red before the fix.568 focused observer/pipeline
cases pass, including real prepare/send/cache/thumbnail-verification/publication
paths in both modes. Final versioned b17 host gates:6228 passed/16 existing
skips in57.69s; Ruff and strict host/Linux mypy318 files; whole100% (11984
statements/2918 branches), mandatory100% (9132/2148). The exact expanded image
probe also executes under H2 with zero network/external-command attempts and
fails when an in-memory negative control reinstates the original preview gap.
These are offline results, not native-image or physical no-wake claims.

## Implemented behaviour

- Derive a JPEG from the exact encoded delivery inside the existing isolated
  prepare task, without a new image task or parent Pillow import. Resize before
  RGB conversion rather than allocating another full-size 4K buffer. Four finite
  encodes yield at most 640x360 / 32 KiB, or no optional preview. Existing worker
  IPC, deadline, memory and confinement limits are unchanged.
- Carry the optional small image only through validated successful delivery.
  Persist the normal per-TV upload association FIRST, then the disposable cache.
  No JPEG enters the association/current/run documents or HA state attributes.
- Cache identity includes actual device ID, content ID, work ID and delivered
  JPEG hash. Strict version/schema, canonical base64, baseline RGB header/size
  and cached-image hash checks reject corruption and swapped images. Old archives
  need no migration; earlier images without a cache entry stay previewless.
- Private cache files total at most 128 MiB including JSON/base64 overhead and
  4,096 entries. File-system metadata and the separate at-most-32-KiB current
  image are additional small overhead, not part of that logical file-size cap.
  Nonblocking writer lock, bounded scans, relative no-follow paths, atomic
  staging/readback, LRU eviction and a 4-MiB free-space reserve are enforced.
  Eviction never deletes associations, history or the old last-sent preview.
- Before current.jpg changes, the existing ownership-checked Core publisher
  acknowledges preview_available=false. Only a verified atomic file replacement
  permits the final true/digest state. A failed first POST cannot touch the file;
  a failed final POST leaves availability false. Missing/corrupt/full cache
  keeps artist metadata and advertises no image. No new Core-management rights.
- Five complete optional native Markdown cards use the same freshness gate for
  image and artist, camera availability, the exact current-file path and digest
  cache busting. The existing Local File integration provides image access;
  no new app option/helper/server/HACS or configuration.yaml edit is needed.
  Existing last-sent/current-artist cards and script blocks remain unchanged.

## Observed offline checks

Final unchanged host command: `bash frame_gallery/scripts/check.sh`, outside the
Mac filesystem sandbox so existing real POSIX group/mode checks remain active.
H2 disables outbound networking for the entire pytest session, including
collection and the tested worker processes.

- 6,154 passed / 16 existing Linux/root platform skips in 53.20 seconds.
- Ruff/format and strict host/Linux typing passed for 316 files.
- Whole line/branch coverage: 100%, 11,927 statements / 2,896 branches.
- Mandatory subset: 100%, 9,132 statements / 2,148 branches.
- 59 additional cases relative to the b16 host suite. Real prepare + selected
  delivery + durable store + reopened cache + current caption/file were tested
  in both one-shot and background modes with injected TV/Core transports.
- Fault cases include other TVs/reused IDs/replaced payloads, malformed/newer/
  missing/oversized cache records, JPEG/hash/identity mismatches, low space,
  busy/nonregular locks, symlink escapes, byte/count/directory bounds, failed
  eviction/cleanup, interrupted staging/readback, deadlines and publication
  refusals. No unrelated files or persistent associations are evicted.
- Four fresh-process in-memory negative controls removed device identity,
  delivered-byte identity, image hash or availability invalidation. Each caused
  its expected assertion failure; no production/test source file was edited.
- Local comparison with the preceding committed b16 verifies all five complete
  current-artist card blocks and the full background-send script unchanged.
  App configuration, AppArmor privileges, Dockerfile, dependency declarations,
  lock/version and existing examples are unchanged.

Evidence is retained locally in ignored `build/current-preview-local-20261022/`,
including `host-gates-final-frozen.log` and the four negative-control logs.

Earlier attempts are retained, not hidden: a test-only mypy import error;
an old source-release assertion that needed to account for the additional
preview encode; and an integration fixture below the accepted source resolution,
which correctly selected a fallback fake candidate. The corrected integration
uses a valid full-size source and asserts the exact delivered candidate. One
intermediate measurement crossed a source edit and had invalid shifted-line
coverage; it is not used as final evidence. The unchanged final run above passed
every original coverage/type/rights gate without added skips or weakened limits.

## Remaining release/live gates

This is not a native ARM/Intel container or Green hardware result. Before public
release, repeat the established exact-source native image/root/memory, source
availability, archive, image and signature gates. The five cards have structural
offline checks, not a claim of actual Home Assistant rendering. Visual file
refresh/guard behaviour needs a separately authorized local installation check.
No new physical sleep, no-wake or all-firmware guarantee is inferred. Existing
experimental observer risks and default-off settings are unchanged.

Setup and complete card: [English](frame_gallery/CURRENT_PREVIEW.md) |
[Deutsch](frame_gallery/CURRENT_PREVIEW.de.md) |
[Français](frame_gallery/CURRENT_PREVIEW.fr.md) |
[Español](frame_gallery/CURRENT_PREVIEW.es.md) |
[Italiano](frame_gallery/CURRENT_PREVIEW.it.md).
