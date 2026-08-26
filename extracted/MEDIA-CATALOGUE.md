# MEDIA-CATALOGUE — MiSide

Counts and bytes below were MEASURED by the pipeline's own walk
(method recorded per row in `media-catalogue.jsonl`) — never copied
from a doc ([DR-2026-08-18-media-scope], spec §8).

Audio and video stay IN PLACE on the game drive: the live Steam
install is never mutated, no destructive move was performed, and no
pack-held media copies were created. Offload rows in the JSONL are a
*proposal* awaiting the owner's pick.

| Family | Count | Bytes | Scope |
|---|---:|---:|---|
| `audio` | 28727 | 1441448548 | catalogue-in-place |
| `languages-art` | 780 | 366431750 | export-webp |
| `custom-images` | 17 | 11186378 | copy-verbatim |
| `gi-enlighten` | 62 | 5988963 | catalogue-in-place |

Per-family detail, per-directory offload proposals, and
per-locale subset rows: see `media-catalogue.jsonl`.
