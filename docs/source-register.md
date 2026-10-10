# Source licence register (Phase 5, step 1)

Checked on 2026-10-10 by reading each rights holder's own published terms. **Nothing has been
imported.** This is a factual record of what the pages say, not legal advice. A person must
confirm each row before the database will accept it as `approved` (see `source-policy.md`).

Status words: **Candidate** = looks usable, waiting for your confirmation. **Blocked** = terms
conflict with how Hidayah must store and serve content. **Unknown** = no usable terms found.

| Source | What it covers | What its terms say | Commercial use | Fits our model (we store text in our own database and search it)? | Status |
|---|---|---|---|---|---|
| Tanzil Project, Quran Arabic text | Arabic text only | "Copyright (C) 2007-2021 Tanzil Project. License: Creative Commons Attribution 3.0." Verbatim copies may be copied and distributed; **changing the text is not allowed**. May be used in any website or application if Tanzil is credited and linked to tanzil.net; the copyright notice must be kept in files containing a substantial part of the text. | Allowed with attribution (nothing in the terms limits it) | Yes, if the text is stored unchanged and the credit line is shown | **Candidate** |
| Tanzil translations repository | Many translations | Page could not be fetched, so terms are **not read**. Translations normally carry their own licences, separate from the Arabic text. | Unknown | Unknown | **Unknown** |
| Quran Foundation API (quran.com) | Text, translations, tafsir, audio | A paid or ad-supported app may use content shown to end users. "A Developer must obtain a signed commercial license before selling, sublicensing, or redistributing QF Content." Storing content longer than 1 week is not allowed except through their Content Sync APIs. Derived material that allows reconstructing the content is under the same limits. | Allowed for display inside an app; **not** for our own copy | **No.** Our database and search index would hold a permanent copy. Needs a signed licence from them first | **Blocked** until a licence is signed |
| Al Quran Cloud (alquran.cloud) | Text, translations, recitations | Quran text: free to store and display; for commercial reproduction no permission needed, minimum is a source acknowledgement. Translations: "attribute the translator by name". Audio: free non-commercial only; reciters keep copyright. Tafsir: not mentioned. This site republishes other people's work, so it cannot grant rights it does not hold. | Text: yes. Translations: unclear. Audio: no | Only for the Arabic text (same Tanzil source), so no benefit over Tanzil directly | **Not used** |
| sunnah.com | Hadith with gradings | Needs an API key; bulk download "not available yet"; **no licence stated** on the developer page. | Unknown | Unknown | **Unknown**: ask the maintainers (sunnah.com/contact) |
| fawazahmed0/hadith-api (GitHub) | Hadith in many languages, with grades | The repository is under the Unlicense (public domain dedication). It says nothing about the copyright of the underlying hadith editions, translations or grades. A repository licence cannot give away rights the uploader does not hold. | Repository: yes. Content: unknown | Not until the origin of each text and grade is traced | **Unknown** |
| Tafsir works | Per work | No source checked yet | Unknown | Unknown | **Not reviewed** |
| Duas | Cited originals | No source checked yet | Unknown | Unknown | **Not reviewed** |

## What this means

1. **One source is ready for your decision: the Tanzil Arabic Quran text.** It can be stored
   unchanged, with the credit "Tanzil Project" and a link to tanzil.net on every page that shows it.
2. **Translations are the hard part.** The Arabic text is not copyrighted in the same way, but
   English and Urdu translations usually belong to a translator or publisher. We need a translation
   whose own licence allows commercial use and storing it. None is confirmed yet.
3. **Hadith needs a clean chain.** Classical Arabic texts are very old, but the *edition*, the
   *translation* and each *grading* (a modern scholar's judgement) can each be copyrighted. We must
   record that chain per collection before import.
4. **The Quran Foundation API is not usable as our content store** without a signed commercial licence.

## Decisions I need from you

1. Do you confirm the Tanzil Arabic text as our first approved source? Your confirmation is what
   `license_verified_by` records.
2. For translations: shall I (a) check each candidate translation's own licence from the translator
   or publisher, listing English and Urdu ones you prefer, and/or (b) draft permission emails you
   can send to rights holders?
3. For hadith: which collections matter first (for example Bukhari and Muslim), and shall I draft the
   request to sunnah.com's maintainers?
