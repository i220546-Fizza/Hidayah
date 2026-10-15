export type Source = {
  slug: string
  title: string
  category: string
  language: string
  author_or_publisher: string | null
  translator: string | null
  edition: string | null
  rights_holder: string | null
  license_name: string | null
  license_url: string | null
  attribution_text: string | null
  original_url: string | null
}
export type Surah = { number: number; name_arabic: string; name_english: string; name_transliterated: string | null; verse_count: number }
export type Translation = { language: string; text: string; source: Source }
export type Verse = { surah_number: number; verse_number: number; text_arabic: string; source: Source; translations: Translation[] }
export type SurahDetail = { surah: Surah; verses: Verse[]; total: number; limit: number; offset: number }
export type Tafsir = { surah_number: number; verse_start: number; verse_end: number; language: string; text: string; source: Source }
export type Collection = { slug: string; name_english: string; name_arabic: string | null; source: Source; record_count: number }
export type Grading = { grader: string; grade: string; reference_note: string | null; source: Source }
export type Hadith = {
  id: number
  collection_slug: string
  collection_name: string
  book_number: string | null
  book_name: string | null
  hadith_number: string
  arabic_text: string | null
  translation_text: string | null
  translation_language: string | null
  narrator: string | null
  source: Source
  gradings: Grading[]
}
export type DuaCategory = { slug: string; name_english: string; name_urdu: string | null; dua_count: number }
export type Dua = {
  id: number
  category_slug: string
  title: string
  arabic_text: string
  transliteration: string | null
  translation_text: string | null
  translation_language: string | null
  provenance: string
  reference_text: string | null
  source: Source | null
}
export type SearchHit = { type: string; title: string; snippet: string; link: string; source: Source }
export type Page<T> = { items: T[]; total: number; limit: number; offset: number }
export type Citation = { kind: string; label: string; text: string; text_arabic: string | null; link: string | null; source: Source }
export type ChatMessage = { id: number; role: 'user' | 'assistant'; content: string; outcome: string | null; created_at: string; citations: Citation[] }
export type AskResponse = { conversation_id: string; message: ChatMessage; disclaimer: string }
export type PathSummary = { slug: string; title: string; description: string | null; difficulty: string; item_count: number }
export type PathDetail = PathSummary & { items: { position: number; title: string; quiz_id: number | null }[]; last_item_position: number; completed: boolean }
export type QuizSummary = { id: number; title: string; topic: string | null; difficulty: string; question_count: number }
export type Quiz = QuizSummary & { questions: { id: number; prompt: string; options: { id: number; text: string }[] }[] }
export type QuizResult = {
  attempt_id: number
  score: number
  total: number
  results: {
    question_id: number
    chosen_option_id: number | null
    correct_option_id: number
    is_correct: boolean
    explanation: { text: string; reference_text: string | null; source: Source } | null
  }[]
}
export type Daily = { date: string; verse: Verse | null; note: string | null }
export type Bookmark = { id: number; type: 'verse' | 'hadith' | 'dua'; target_id: number; created_at: string }

export type AdminSource = {
  id: number
  slug: string
  title: string
  category: string
  language: string
  approval_status: string
  verification_status: string
  commercial_use: string
  redistribution: string
  storage_permission: string
  indexing_permission: string
  rag_permission: string
  rights_holder: string | null
  license_name: string | null
  license_url: string | null
  attribution_text: string | null
  rights_notes: string | null
  original_url: string | null
  license_verified_at: string | null
  edition: string | null
  author_or_publisher: string | null
  translator: string | null
}
export type Readiness = { ready: boolean; missing: string[] }
export type Review = { id: number; from_status: string | null; to_status: string; note: string | null; created_at: string }
export type AuditEvent = { id: number; actor_id: string | null; action: string; entity_type: string; entity_id: string | null; details: Record<string, unknown> | null; created_at: string }
export type Stats = {
  users: number
  sources_by_status: Record<string, number>
  source_versions: number
  conversations: number
  answer_outcomes: Record<string, number>
  feedback_up: number
  feedback_down: number
  quizzes_approved: number
  paths_approved: number
}
