# Feature checklist

Statuses: Not Started, In Progress, Implemented, Tested, Blocked.
"Tested" means automated tests actually ran and passed.

## Phase 2: design foundation

| Item | Status | Notes |
|---|---|---|
| Web design tokens (CSS variables, Tailwind theme) | Tested | Contrast checked, see below |
| Mobile design tokens | Implemented | `mobile/src/theme/tokens.ts`; app not created yet |
| Fonts (Playfair, Inter, Amiri, Noto Naskh, Noto Nastaliq) | Implemented | Self-hosted via npm; visual check on a real device pending |
| Logo and emblem | Implemented | Arabic spelling needs human verification before launch |
| Reusable components (Button, Card, Container, EmptyState) | Tested | |
| Responsive navigation | Tested | Menu toggle test; real-device check pending |
| Landing page | Tested | Verse and dua areas are honest empty states until verified data exists |

## Everything else

| Area | Status |
|---|---|
| Backend, database, migrations | Not Started |
| Authentication and accounts | Not Started |
| Quran, translation, tafsir | Not Started (licensing review first) |
| Hadith and gradings | Not Started (licensing review first) |
| Duas | Not Started |
| RAG assistant | Not Started |
| Daily Companion, quizzes, learning paths | Not Started |
| Admin dashboard | Not Started |
| Mobile app | Not Started |
| Deployment | Not Started (needs your approval) |

## Contrast check (WCAG, measured)

Normal text needs 4.5:1. Charcoal on ivory 11.8, ivory on emerald 11.2, emerald on white 12.2,
gold on emerald 5.2. Gold on ivory is 2.2, so gold is never used for text on ivory.
Bronze on ivory is 4.49, used only for the logo's Arabic wordmark.
