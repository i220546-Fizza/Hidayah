# Source policy

## Why this matters

Hidayah is intended for public and commercial use. Redistribution rights differ widely between
Quran texts, translations, tafsir works and hadith collections. Many translations and tafsir
are copyrighted. Content that is free to read online is not automatically free to republish
or sell.

## Rules

1. No dataset is imported until its source, edition, translator or author, license and
   attribution requirements are recorded here.
2. Commercial use must be explicitly permitted by the license. If it is unclear, the source is
   not used until the rights holder confirms.
3. Quran Arabic text, hadith and duas are stored as canonical records and are never generated
   by a language model.
4. Hadith gradings are recorded per grader. A grading is shown only with its source.
5. No claim of scholarly review is made unless a named reviewer actually approved the content.
6. Only sources with status Approved can enter the production search index.

## How a licence is recorded (before any import)

Every source gets a row in the `sources` table with these fields filled in by a person, from
the rights holder's own licence page or written permission:

| Field | What to record |
|---|---|
| `rights_holder` | Who owns the rights (publisher, translator, foundation) |
| `license_name`, `license_url` | The exact licence and where it is published |
| `commercial_use` | `allowed`, `not_allowed`, `requires_permission` or `unknown` |
| `redistribution` | Same four values: may we store and serve the text ourselves? |
| `attribution_required`, `attribution_text` | The credit line we must show |
| `rights_notes` | Anything unusual: field of use limits, no-derivatives, edition quirks |
| `license_verified_at`, `license_verified_by` | When and who confirmed it |

Starting state is `unknown` rights and `draft`. The database refuses to mark a source `approved`
unless `commercial_use = 'allowed'` and the licence is verified. If a licence only allows
non-commercial use, the source stays out of production, whatever its quality.

Each import then registers a `source_version` (with SHA-256 checksum) and every Quran, hadith,
dua or chunk row points back to it, so any displayed text can be traced to its licence.

## Source register

The checked register lives in [source-register.md](source-register.md). Nothing is approved yet.
Candidate sources are NOT permission to import; each needs a person's confirmation.
