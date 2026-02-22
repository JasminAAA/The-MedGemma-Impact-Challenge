EVENT_EXTRACTION_PROMPT = """
You are a medical language model specialized in clinical documentation analysis.

Extract time-stamped clinical events from the provided psychiatric notes.

CRITICAL RULES:
- Preserve exact clinical terminology.
- Preserve negations.
- Preserve uncertainty language.
- Do NOT infer causation.
- Do NOT summarize.
- Extract only explicitly stated information.
- Include exact excerpt from source note.

Return JSON ONLY.

Schema:
[
  {
    "date": "YYYY-MM-DD",
    "type": "symptom | medication | assessment | therapy | test",
    "label": "Short factual description",
    "excerpt": "Exact copied text from note",
    "source_id": "note_id"
  }
]

If none found, return [].
"""


ASSESSMENT_EXTRACTION_PROMPT = """
Extract structured psychiatric assessment scores from the notes.

CRITICAL RULES:
- Extract only explicitly stated numeric scores.
- Do NOT estimate missing values.
- Preserve scale name exactly.
- Include date and source_id.
- Return JSON only.

Schema:
[
  {
    "date": "YYYY-MM-DD",
    "scale": "PHQ-9 | GAD-7 | MMSE | MADRS",
    "score": integer,
    "source_id": "note_id",
    "excerpt": "Exact copied text"
  }
]

If none found, return [].
"""


SUMMARY_PROMPT = """
Generate a clinician-facing pre-session brief.

Inputs:
- Structured clinical events
- Assessment timeline
- Attribution uncertainty flags

CRITICAL SAFETY RULES:
- Do NOT infer causation.
- Do NOT recommend treatment.
- Do NOT diagnose.
- Use neutral language.
- Explicitly state uncertainty where flags exist.

Output format:

Paragraph 1: Concise longitudinal overview.

Paragraph 2: Notable patterns without causal claims.

Section: Uncertainty Areas
- Bullet list

Section: Suggested Discussion Points
- Bullet list

Keep under 250 words.
No markdown.
"""
