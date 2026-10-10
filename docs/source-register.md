# Source licence register

**Review date:** 2026-10-10 (all "checked" entries below were read on this date).
**Nothing has been imported. No email has been sent.** This is a record of what each rights
holder's own page says, plus my reading of it. It is not legal advice, and the statuses are proposals
for you to confirm. Where I could not read a page, the entry says so.

## Statuses

| Status | Meaning |
|---|---|
| `candidate` | Looks usable for our intended use; project decision made or proposed; verification steps still open |
| `approved` | Licence verified by a person, commercial use explicitly allowed, content verified. **Nothing is approved yet** |
| `pending_permission` | Terms are unclear or do not cover our use; we need written permission (a draft email exists) |
| `restricted` | Terms conflict with our use as written, or provenance is unclear, so it cannot be used now |
| `rejected` | Terms forbid our use; not usable unless the rights holder changes them |

**Our intended use** (every question below is asked against it): public website and mobile apps, possibly
commercial; permanent storage in our own PostgreSQL database; full-text and vector search indexing;
retrieval of passages by the answer assistant (RAG); showing the exact edition and credit on every
answer.

**Schema gap (needs your decision).** The `sources` table today knows `draft / under_review / approved /
rejected / archived`, and it records commercial use and redistribution. It has no field for permanent
storage, search indexing or RAG separately, and no `candidate / pending_permission / restricted`. I
recommend a small migration (0002) before any import. Not done yet; see "Decisions" at the end.

---

## 1. Quran Arabic text

### 1.1 Tanzil Project: `candidate` (project decision made; not production-approved)

| Field | Evidence |
|---|---|
| Rights holder | Tanzil Project ("Copyright (C) 2007-2021 Tanzil Project") |
| Licence as stated | "Creative Commons Attribution 3.0", plus Tanzil's own Terms of Use below |
| Terms of Use (verbatim) | "Permission is granted to copy and distribute verbatim copies of the Quran text provided here, but changing the text is not allowed." / "The text can be used in any website or application, provided that its source (Tanzil Project) is clearly indicated, and a link is made to tanzil.net to enable users to keep track of changes." / "This copyright notice shall be included in all verbatim copies of the text, and shall be reproduced appropriately in all files derived from or containing substantial portion of this text." (the header you pasted and the download page agree) |
| Version | Version 1.1, released 12 February 2021 (tanzil.net/updates) |
| Source URL | https://tanzil.net/download/ ; updates: https://tanzil.net/updates/ |
| Text type to use | Uthmani (matches the Madinah mushaf), unchanged. Decision on the exact variant is open |
| Commercial use | Not restricted by the terms; allowed with the credit above |
| Redistribution | Verbatim copies allowed with the notice |
| Permanent database storage | Fits "verbatim copy" only if stored unchanged (see conflicts below) |
| Search indexing | Not mentioned |
| RAG retrieval | Not mentioned |
| Attribution we must show | "Quran text: Tanzil Project (tanzil.net), version 1.1, CC BY 3.0", linked to https://tanzil.net, and the copyright notice kept with the stored text |

**Open points before it can become `approved`:**
- The licence says CC BY 3.0, which normally allows changes, but Tanzil's terms say changing the text is not
  allowed. We follow the stricter reading: store the text byte-for-byte; do any search normalisation
  (removing diacritics for matching) in separate derived columns, never overwriting the stored text.
  Whether derived search columns and embeddings count as "changing" is not stated. This is question 3 in the
  draft email to Tanzil.
- Search indexing and RAG are not mentioned either way. Also in the email.

**Your project decision vs independent verification:**

| Check | Done? |
|---|---|
| You chose Tanzil as first candidate | Yes (your decision, 2026-10-10) |
| Licence text read on tanzil.net download page | Yes (2026-10-10) |
| Version and date read on tanzil.net/updates | Yes (v1.1, 2021-02-12) |
| Actual downloaded file inspected: header present, notice unchanged | No (no import yet) |
| SHA-256 checksum of the file recorded in `source_versions` | No |
| CC BY 3.0 licence URL confirmed and stored in `license_url` | No |
| Tanzil's answer on derived search columns, embeddings, RAG | No (email drafted, not sent) |
| A person (you) records `license_verified_by` and date | No |
| Credit and link shown in the UI wherever the text appears | No (not built) |

### 1.2 Other Arabic text sources

| Source | Finding | Status |
|---|---|---|
| Quran Foundation API | See 2.1: no permanent copy without a signed licence | `restricted` |
| Al Quran Cloud (alquran.cloud) | Says Quran text is free to store and display, commercial reproduction needs no permission, acknowledge Tanzil/Quran Academy. It republishes Tanzil's text, so it adds nothing over Tanzil itself | not used |

---

## 2. Quran translations

For every translation: you asked for translator, publisher, edition, official source, licence, commercial
use, attribution, redistribution, permanent storage, indexing and RAG. "Not stated" means the page I read
does not say; it does not mean allowed.

### 2.1 Aggregators (where translations are published, not who owns them)

| Source | Terms found | Status |
|---|---|---|
| Tanzil translations repository | tanzil.net/trans could not be loaded (server error, tried twice). OPUS, which republishes Tanzil's collection, says: "The translations provided at this page are for non-commercial purposes only." and "If used otherwise, you need to obtain necessary permission from the translator or the publisher." That is second-hand until I can read Tanzil's own page | `restricted` |
| QuranEnc.com (Rowwad Translation Center) | "Contents of the translations can be downloaded and re-published, with the following terms and conditions": (1) no modification, addition or deletion; (2) clearly refer to the publisher and source (QuranEnc.com); (3) mention the version number; (4) keep the transcript information inside the document; (5) notify QuranEnc of any note on the translation; (6) update to the latest version issued by QuranEnc; (7) no inappropriate advertisements. No named licence. Commercial use and database storage are **not addressed** | `pending_permission` |
| Quran Foundation API (quran.com) | "A Developer must obtain a signed commercial license before selling, sublicensing, or redistributing QF Content." Caching or storing longer than 1 week is prohibited unless obtained through their Content Sync APIs. Derived materials that allow reconstruction are under the same limits. Page: https://api-docs.quran.foundation/legal/developer-terms/ | `restricted` (needs a signed licence) |
| Tarteel QUL (qul.tarteel.ai) | FAQ: "Some are in the public domain, while others may be subject to specific licenses." "Yes, you can use QUL data in commercial projects. However, please review the licensing terms for each resource." Useful as a directory, not as a grant of rights | discovery only |
| Al Quran Cloud | Translations: "attribute the translator by name". It does not own them | not used |

### 2.2 English

| Translation | Translator / rights holder | Edition and source | Licence evidence | Commercial | Attribution | Redistribution, storage, indexing, RAG | Status |
|---|---|---|---|---|---|---|---|
| Pickthall, *The Meaning of the Glorious Koran* | Marmaduke Pickthall (1875-1936) | Project Gutenberg ebook #16955 ("Three translations of the Koran side by side", release 2005-10-27, updated 2020-12-12) https://gutenberg.org/ebooks/16955 | Gutenberg: "Public domain in the USA." Pickthall died 1936. Original edition year not stated on that page | Public domain in the US per Gutenberg; other countries not checked | Credit the translator and edition anyway | Not restricted if truly public domain. Needs: confirm the original 1930 text vs Gutenberg's proofed copy, and check the countries we will serve | `candidate` (weak: older English; legal confirmation needed) |
| Yusuf Ali | Abdullah Yusuf Ali (1872-1952) | Same Gutenberg ebook; many modern printings differ | WikiIslam (a secondary source) says public domain in Pakistan and many countries but given "pro-forma" US copyright restoration; its own dates look inconsistent. Modern printings (Amana etc.) may add copyrighted revisions | Unclear | n/a | Unclear | `restricted` until a lawyer confirms |
| Shakir | M. H. Shakir (d. 1959) | Same Gutenberg ebook | Gutenberg: public domain in the USA. Other countries not checked | US only | n/a | Unclear outside US | `restricted` |
| Sahih International | Translator team; rights holder not confirmed | Listed on QuranEnc as `english_saheeh`; the page labels it "English Translation - Noor International Center" (inconsistent, unresolved). Islamhouse page gives no rights statement | QuranEnc's seven re-publication terms (above). No commercial statement | Not stated | QuranEnc + publisher credit, version number | Not stated | `pending_permission` |
| The Clear Quran | Dr. Mustafa Khattab | Furqaan Institute of Quranic Education "has the exclusive license to publish, distribute, and disseminate" (per QUL). theclearquran.org/copyright-information returned no terms | No licence found | Not stated | Not stated | Not stated | `pending_permission` |
| Quran in Modern English / ClearQuran | Talal A. Itani | clearquran.com PDF, 2012 edition, ISBN 978-1467948746 | Conflict: the author's blog says "I chose not to copyright the translation but to provide it under the Creative Commons License" (no version), but the PDF says "Copyright (c) 2009-2012 Talal A. Itani. All rights reserved." and requires written permission | Not allowed without permission, per the PDF | n/a | Not allowed without permission | `pending_permission` |
| Muhammad Asad, *The Message of The Qur'an* | Muhammad Asad (d. 1992) | Not checked | Not checked; author died 1992 so copyright is almost certainly still running | Not checked | n/a | Not checked | `restricted` (not reviewed) |

### 2.3 Urdu

I found **no Urdu translation with a clear licence permitting our use.** Findings:

| Translation | Translator / rights holder | Evidence | Status |
|---|---|---|---|
| Kanz-ul-Iman | Ahmed Raza Khan (d. 1921; translation dated 1910 or 1911, Wikipedia gives both) | Author died long ago, so the translation text is probably out of copyright; but I have **not found a specific digital edition with a stated source and licence**, and modern printings add commentary | `restricted` until an edition is identified |
| Junagarhi | Muhammad Junagarhi (d. 1941) | Same: old author. The Wikipedia page does not name his Quran translation edition. The Saudi "Ahsan ul-Bayan" edition adds Salahuddin Yusuf's commentary, which is separate and probably protected | `restricted` until an edition is identified |
| Jalandhry | Fateh Muhammad Jalandhry | Death year not verified (my search did not confirm it) | `restricted` |
| Maududi, Tafhim ul-Quran | Abul A'la Maududi (d. 1979) | Not checked; likely under copyright with a publisher | `pending_permission` |
| Ahmed Ali, Tahir ul-Qadri, Jawadi, Najafi | Various | Listed in the TeX package `quran-ur` (CTAN). That package's licence (LPPL 1.3c) covers the *package*, and the page says nothing about the translations' source or rights | `restricted` |
| Tanzil's Urdu entries | Per translation | Covered by the non-commercial statement quoted at OPUS (see 2.1) | `restricted` |

---

## 3. Hadith: Sahih al-Bukhari and Sahih Muslim

I looked at the layers separately, as you asked.

| Layer | Finding |
|---|---|
| Arabic text of the collections | The compilers died in the 9th century, so the underlying text is very old. But each digital *edition* (typesetting, numbering, corrections) has its own provenance. Sources below |
| English translation | Separate copyrights per translator and publisher |
| Urdu translation | Not found with clear terms |
| Edition-specific content | Numbering systems and chapter titles differ by edition; we must record which edition each citation uses |
| Gradings | A grading is a modern scholar's judgement and may be protected. Our own rule: always show it with its grader |
| Commentary | None considered; would be separate works |

| Source | Evidence | Status |
|---|---|---|
| sunnah.com | About page: Arabic "sourced from al-eman.com and other now-defunct sources"; English "various translators" (list "will appear here shortly"; not named for Bukhari/Muslim); gradings by Shaykh al-Albani and Darussalam (Hafiz Zubair `Ali Za`i). "We do not permit the scraping of our data, nor mass reproduction of entire books or collections on other websites." "Reproducing individual hadith or selections of hadith for a teaching/didactic/presentation purpose is permitted." API needs a key; bulk dump "not available yet"; no licence statement. Draft email prepared | `pending_permission` |
| fawazahmed0/hadith-api (GitHub) | Repository under the Unlicense. Its References page is a thank-you list, "not a confirmed data provenance list", and names no source for Bukhari. It does not state rights for the texts, translations or grades. The repository licence cannot grant rights the uploader does not hold | `restricted` |
| IIUM, Sahih Muslim (English, Abdul Hamid Siddiqui) | "The collection may absolutely NOT be copied or used for commercial gain." Publisher and edition not named | `rejected` for commercial use (unless the rights holder agrees) |
| Bukhari English (Muhammad Muhsin Khan, Darussalam) | I did not find a rights statement on a primary page. Treat as commercially published and protected until shown otherwise | `pending_permission` (not verified) |
| OpenITI / KITAB project Arabic corpus | I could not read the licence section of its documentation (the FAQ answer was truncated). Contact: kitab@aku.edu | not reviewed |
| Arabic Wikisource, صحيح البخاري | Page could not be read for edition or licence (it appears to be scanned PDFs) | not reviewed |
| Urdu Bukhari / Muslim | Nothing found with clear terms | not reviewed |

Gradings (separate status): al-Albani and Zubair Ali Za'i gradings via sunnah.com: `pending_permission`. Until
permission exists, Hidayah shows **no grade**, and says so; we do not infer one.

---

## 4. Tafsir

| Source | Evidence | Status |
|---|---|---|
| altafsir.com (Royal Aal al-Bayt Institute, Jordan) | Notice "Copyrights 2026 Royal Aal al-Bayt Institute for Islamic Thought". Described as "a completely free, non-profit website". No terms-of-use section found. Hosts English: Tafsir al-Jalalayn, Ibn 'Abbas, al-Wahidi's Asbab al-Nuzul, al-Tustari, Baydawi, al-Kashani, Ibn 'Ajiba. Urdu not mentioned. The English renderings are commissioned works; the original Arabic authors are centuries dead, but the translations are separate | `pending_permission` |
| Quran Foundation tafsir content | Covered by the same developer terms as 2.1 | `restricted` |
| Ibn Kathir (abridged English, Darussalam), Maarif-ul-Quran, other Urdu tafsir | Not checked | not reviewed |
| Classical Arabic tafsir (original text) | Authors long dead, but need a specific edition and its provenance | not reviewed |

## 5. Duas

- **Original wording** of duas comes from the Quran and from hadith. Those follow the Quran and hadith rows
  above; a dua may only be added with a reference to an approved source record (the database already requires a
  reference for sourced duas).
- **Compilations and translations** such as *Hisn al-Muslim* (Sa'id al-Qahtani) are separate works.
  The Islamhouse page I read lists the author but states no translator, publisher, edition or rights, so there is no
  evidence of permission: `pending_permission` (not verified).
- Our own editorial notes (explanations we write) are our original work and can carry our licence; they are flagged
  `editorial` in the schema and never presented as source text.

---

## 6. Summary

| Content | Best position today |
|---|---|
| Arabic Quran text | Tanzil v1.1: `candidate`; questions drafted |
| English translation | Pickthall `candidate` (needs legal confirmation); everything else needs permission |
| Urdu translation | Nothing usable yet |
| Hadith (Bukhari, Muslim) | Nothing usable yet; sunnah.com request drafted |
| Tafsir | Nothing usable yet |
| Duas | Only via references to approved Quran/hadith records |

## 7. Implementation rules (enforced, not just written)

1. Only `approved` sources enter the production index. The database already refuses `approved` without a verified
   licence and `commercial_use = allowed`.
2. Every stored passage points to its source and `source_versions` row (edition label and SHA-256), so each answer
   can name the exact edition or translation and show the required credit.
3. Stored source text is kept byte-for-byte. Search-friendly forms are separate derived columns.
4. An answer may only quote passages from approved sources; with none, it says it cannot answer.
5. No grading is shown without its grader and permission.

## Decisions I need from you

1. **Schema migration 0002**: add `candidate`, `pending_permission`, `restricted` statuses and separate permissions
   for storage, indexing and RAG. Recommended before any import. Approve?
2. **Emails**: six drafts are in `docs/permission-requests.md`. I have no verified contact addresses for most
   rights holders, so you (or I, once you give approval) would look those up first.
3. **Urdu strategy**: since no Urdu translation is clearly usable, do you prefer to (a) pursue permission from
   specific publishers, (b) identify a specific public-domain edition of Kanz-ul-Iman or Junagarhi with a
   clean text source, or (c) launch Arabic + English first?
4. **English strategy**: Pickthall is usable but dated; do you want to wait for permission for a modern translation?
