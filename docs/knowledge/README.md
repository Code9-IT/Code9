# Knowledge Base Authoring Guide

This folder contains curated maritime reference notes used by RAG.

## Goal

Each file should be focused on one operational topic and written for retrieval quality,
not as a full report.

## Recommended file format

Use this structure:

```md
# Title

## Scope
Short description of what event/sensor patterns this note supports.

## Causes
- ...

## How to diagnose
- ...

## Recommended actions
1. ...
2. ...

## Limits / regulations
- ...

## Sources
- Source title: https://...
- Source title: https://...
```

## Writing rules for this project

- Keep each file short and focused (roughly 400-800 words).
- Keep one theme per file (for example scrubber emissions, lubrication, fuel quality).
- Prefer trusted sources (IMO, class societies, OEM manuals, standards).
- Summarize relevant points; do not paste long raw documents.
- Do not include prompt-like instructions to the AI (only domain facts and procedures).
- Always include the source links at the end.
