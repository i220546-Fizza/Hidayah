# Draft permission requests

**None of these has been sent.** Each needs your approval, your name and a real contact address.
I have not invented any addresses: the places to find them are listed under each draft.
Replace every `[ ... ]`. Keep the answers you receive (save the email or letter) in `data/permissions/`
and record the date and wording in `source-register.md`; the database stores who verified the licence and when.

**About Hidayah, used in every draft (edit freely):**
Hidayah is a learning platform for the Quran, hadith, duas and Islamic study, with a website and mobile apps. It
may be offered publicly, possibly with paid features. It shows every passage with its exact source, edition and
credit, and its answer assistant only quotes from sources we are permitted to use.

---

## 1. sunnah.com maintainers

**Where to send:** the contact form at https://sunnah.com/contact (it has Name, Email and message fields; no email address is shown). The developers page https://sunnah.com/developers says API keys are requested through a GitHub issue.

**Subject:** Permission request: use of Sahih al-Bukhari and Sahih Muslim data in Hidayah

Assalamu alaikum,

My name is [Your name]. I am building Hidayah, [one-line description above]. Thank you for the work you do on sunnah.com.

We would like to use the Arabic text, and the English [and Urdu] translations if you can speak for them, of Sahih al-Bukhari and Sahih Muslim, together with the grading information you display. Before we use anything, I would like to ask:

1. **API access:** may we have an API key for this purpose, and what rate limits apply?
2. **Permanent storage:** may we keep a permanent copy of the data in our own database, rather than fetching it on demand?
3. **Search indexing:** may we index it for full-text and semantic (vector) search inside Hidayah?
4. **Answer assistant (RAG):** may passages be retrieved and shown to users, with attribution, by an assistant that answers questions? The assistant only quotes the stored text and never generates hadith text.
5. **Redistribution:** which parts of the data (Arabic, each translation, gradings) do you control the rights to, and which belong to other translators, publishers or graders? Your About page names Shaykh al-Albani and Darussalam (Hafiz Zubair `Ali Za`i) for grades. Please tell us who the rights holders are, and whether we need to ask them separately.
6. **Attribution:** what credit and links do you require, and where should they appear?
7. **Commercial and public deployment:** may we use it in a public website and mobile apps, including if some features are paid?
8. **Edition details:** which edition and numbering does each collection follow, so that our citations are exact?

We do not intend to scrape sunnah.com or republish whole collections as a separate site. We will use only what you permit, and will stop and remove anything on your request.

Jazakum Allahu khayran,
[Your name], [email], [website/project link]

---

## 2. Tanzil Project

**Where to send:** Tanzil's pages do not show an email address. The FAQ (https://tanzil.net/docs/faq) says "ask your question ... via our contact page", so use the contact link on https://tanzil.net. (https://tanzil.net/docs/contact returned "page does not exist".)

**Subject:** Clarifying the terms for the Tanzil Quran text (v1.1)

Assalamu alaikum,

I am building Hidayah, [description], and would like to use the Tanzil Uthmani Quran text (version 1.1, 2021) unchanged, with the credit "Tanzil Project" and a link to tanzil.net, as your terms require. Your terms say the text may not be changed and that the licence is Creative Commons Attribution 3.0. Could you please confirm:

1. **Commercial use.** The download page says the text "can be used in any website or application" with credit, but your FAQ says resources are "available for non-commercial purposes". May we use the Quran text in a public website and mobile apps, including a service with paid features?
2. We may store the text unchanged in our own database.
3. We may create *derived search data* (for example the text with diacritics removed, and numerical embeddings used for search) in separate fields, while the displayed text stays unchanged. Does this count as "changing" the text?
4. We may split the text by verse for retrieval by an answer assistant, quoting verses verbatim with the credit.
5. Is the credit "Quran text: Tanzil Project (tanzil.net), version 1.1, CC BY 3.0" with a link acceptable?

Jazakum Allahu khayran,
[Your name]

---

## 3. Furqaan Institute of Quranic Education (The Clear Quran, Dr. Mustafa Khattab)

**Where to send:** I found no contact address or form on theclearquran.org (its copyright page and contact page returned no terms or contacts). Check the site footer or the publisher's page; the Quran.com team also hosts a permission-request thread at https://feedback.quran.com/translation-and-reciter-requests/p/permission-request-for-educational-use-of-quran-translation, which shows how others have asked.

**Subject:** Licensing request: The Clear Quran in a learning app

Assalamu alaikum,

I am building Hidayah, [description]. We would like to display The Clear Quran by Dr. Mustafa Khattab alongside the Arabic text. We understand Furqaan Institute holds the exclusive licence to publish and distribute it. May we ask what licence you can offer, and in particular:

1. Display in a public website and mobile apps, including with paid features.
2. Permanent storage in our database, and search indexing, of the translation text.
3. Retrieval of verses by our answer assistant, shown verbatim with credit.
4. Fees, if any, the credit line you require, and the edition/version we should cite.
5. Whether you also license the Arabic-and-English edition as an API or data file.

Jazakum Allahu khayran,
[Your name], [email]

---

## 4. Talal A. Itani (Quran in Modern English / ClearQuran)

**Where to send:** the contact page https://blog.clearquran.com/contact (his blog says the translation is under a Creative Commons licence; the 2012 PDF says "All rights reserved". We need him to say which applies).

**Subject:** Clarifying the licence of your Quran translation

Assalamu alaikum Mr. Itani,

I am building Hidayah, [description], and would like to use your English translation. Your blog says you chose to provide it under a Creative Commons licence, while the 2012 PDF carries "Copyright © 2009-2012 Talal A. Itani. All rights reserved." Could you please tell me:

1. Which licence applies (and which version)? Please give the licence name, for example CC BY 4.0.
2. Whether commercial use is allowed, including paid features in a public app.
3. Whether we may store it permanently, index it for search, and quote verses from it in an answer assistant.
4. The credit you would like, and which edition we should cite.

Jazakum Allahu khayran,
[Your name], [email]

---

## 5. IIUM DEED hadith project (English Sahih Muslim, translated by Abdul Hamid Siddiqui)

**Where to send:** deed@iiu.edu.my (the "Email DEED-IIU" link in the footer of https://iium.edu.my/deed/hadith/muslim/index.html; note the address domain is iiu.edu.my). Their page says the collection may "absolutely NOT be copied or used for commercial gain", so this request asks whether that can be varied, and who owns the translation.

**Subject:** Permission request: Siddiqui translation of Sahih Muslim

Assalamu alaikum,

I am building Hidayah, [description]. Your site hosts Abdul Hamid Siddiqui's English translation of Sahih Muslim. Your page says it must not be copied or used for commercial gain. Could you please tell us:

1. Who owns the rights to this translation (the publisher, the translator's heirs, or IIUM)?
2. Whether permission can be granted for display in a public learning app, with permanent storage, search indexing and retrieval by an answer assistant, and under what conditions or fees.
3. Which edition and credit line we should cite.

If it is not possible, we will not use it. Thank you.

Jazakum Allahu khayran,
[Your name], [email]

---

## 6. Generic template: translation publisher or translator (use for Urdu works and others)

**Use for:** Urdu translations (for example Maududi's Tafhim ul-Quran, other publishers), Sahih International, Darussalam (Bukhari English and gradings), Royal Aal al-Bayt Institute (altafsir.com English tafsir), the Hisn al-Muslim publisher.
**Fill in:** `[Work]`, `[translator/author]`, `[edition/year if known]`. Find the publisher's address on the book's copyright page or the publisher's website.

**Subject:** Permission request: [Work] in a learning platform

Assalamu alaikum,

I am building Hidayah, [description]. We would like to include [Work] by [translator/author], [edition/year], alongside the original text, and we want to be sure we have the right to do so. Could you please tell us:

1. Whether we may use it in a public website and mobile apps, including with paid features.
2. Whether we may keep a permanent copy in our own database and index it for search.
3. Whether an answer assistant may retrieve passages and show them verbatim with credit. It never generates or alters this text.
4. Any fee, the credit line you require, and the edition we should cite.
5. If you do not hold these rights, who does.

We will not use the text until we have your written permission.

Jazakum Allahu khayran,
[Your name], [email]
