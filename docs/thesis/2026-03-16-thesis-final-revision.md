# Thesis Final Revision Plan

> **For AI assistants:** Each student track below is self-contained. You can work on your assigned track without needing to coordinate with the other tracks in real time. When you finish, the group should do one final read-through together.

**Goal:** Fix all remaining critical, major, and minor issues identified in three independent reviews so the thesis is submission-ready.

**Source document:** The thesis is edited in Google Docs (the `.md` file in KristianEkstraFolder is a Markdown export). All edits should be made in the Google Docs master, not in the `.md` file.

**Important rules for all students:**
- Do NOT add content that overclaims beyond Scope 1. Stay grounded in what the repo actually proves.
- Do NOT rewrite chapters that are already strong (Ch 1, Ch 4, Ch 6 are mostly good).
- Do NOT invent sprint content or deliverables that didn't happen. Use Trello history and meeting notes as sources.
- Keep the total report within ~35 pages (excluding appendices and references).
- All references must follow APA 7 format.

---

## Consolidated Finding List (Deduplicated)

All three reviews agreed on these issues. Items marked [ALL] were flagged by all three reviewers.

### Critical
| ID | Finding | Flagged by |
|----|---------|------------|
| C1 | Front page has no project title | ALL |
| C2 | No Norwegian sammendrag | ALL |
| C3 | 5-6 cited sources missing from reference list | Claude, Codex1 |
| C4 | "Figure X" placeholder in section 4.5 | ALL |
| C5 | Appendices section is template placeholder | ALL |
| C6 | Section 4.5 heading is broken (not a real heading) | ALL |
| C7 | References heading is not a proper main heading | Codex1 |
| C8 | Character encoding errors (Sørlandet, Sprintmål, etc.) | Codex1, Codex2 |

### Major
| ID | Finding | Flagged by |
|----|---------|------------|
| M1 | Chapter 5.2 "Sprint deliverables" is too weak | ALL |
| M2 | Duplicate Lewis et al. (2020) reference | ALL |
| M3 | Chapter 2 heading structure inconsistent ("Chapter 2" then "Theoretical Framework") | Claude, Codex1 |
| M4 | TOC page numbers wrong/inconsistent | Claude |
| M5 | Section 7.3 Future Work doesn't name User Stories 2 and 3 | Claude |
| M6 | Figure reference error line 446 ("Figure 1" should be "Figure 2") | Claude, Codex1 |
| M7 | Method chapter doesn't explicitly claim DSR as research design | Codex1, Codex2 |
| M8 | Abstract/conclusion overclaim "agent-based observability" vs actual Scope 1 evidence | ALL |
| M9 | Reference list still has unused/weak sources | Codex1, Codex2 |
| M10 | Report is still too long / chapter weighting not optimal | Codex2 |

### Minor
| ID | Finding | Flagged by |
|----|---------|------------|
| m1 | "From." in references (should be removed per APA 7) | Claude |
| m2 | Image references use ![][imageN] - may be broken | Claude |
| m3 | AI disclosure statement placed awkwardly | Claude, Codex1 |
| m4 | Knowit vs KnowIT consistency | Claude, Codex2 |
| m5 | No "Lessons learned" subsection in 6.2 | Claude |
| m6 | Heading anchor for 4.5 is a Google Docs artifact | Claude |
| m7 | IBM reference has utm_source=chatgpt.com in URL | Codex1 |
| m8 | Section 7.4 doesn't mention individual contributions | Claude |
| m9 | Some repetition between 1.1 and 1.3 | Claude |
| m10 | Method could mention specific sprint duration/rhythm | Claude |

---

## Student Track Overview

| Track | Student | Focus Area | Estimated effort |
|-------|---------|------------|-----------------|
| A | Student 1 (Jonas) | Front matter, formalia, formatting, TOC, encoding | ~3-4 hours |
| B | Student 2 (Nidal) | References, academic language, DSR framing in Ch 3 | ~3-4 hours |
| C | Student 3 (Kristian) | Chapter 5.2 rewrite, figures, sections 7.3 and 7.4 | ~3-4 hours |
| D | Student 4 (Onu) | Appendices creation, content polish, final QA pass | ~3-4 hours |

---

## Track A: Front Matter, Formalia, Formatting (Student 1 - Jonas)

**Context for AI assistant:** You are helping fix formal and structural issues in a bachelor thesis written in Google Docs. The thesis is about a maritime observability prototype. Your job is strictly formalia and formatting - do not rewrite chapter content.

### Task A1: Add project title to front page
**What:** The front page line "Tittel:" is empty. Add a proper project title.
**Where:** Front page, line 7 in the exported markdown.
**Suggested title (group should agree on final wording):**
> "Agentic Observability for Maritime Application Monitoring: A Scope 1 Prototype for UDS Incident Handling"

Or a shorter alternative:
> "Agent-Based Observability for Maritime Monitoring: A Bachelor Prototype"

**Done when:** The front page has a clear, descriptive title that reflects the actual project.

### Task A2: Add Norwegian sammendrag
**What:** The school template requires a Norwegian summary in addition to the English abstract. Currently only the English abstract exists.
**Where:** Insert immediately before the English "Abstract" section (before line 40).
**How:** Write a Norwegian translation/adaptation of the existing English abstract. It should be ~150-250 words, covering: problem, approach, what was built, key result, limitations. Do NOT expand beyond what the English abstract says. Keep the scope honest (Scope 1 baseline, not full platform).
**Format:**
```
## **Sammendrag** {#sammendrag}

[Norwegian text here]
```
**Done when:** A Norwegian sammendrag exists between Preface and Abstract, and it accurately mirrors the English abstract without overclaiming.

### Task A3: Fix Chapter 2 heading structure
**What:** Chapter 2 currently uses `# **Chapter 2**` as a level-1 heading, then `## **Theoretical Framework**` as level-2. All other chapters use the format `# **1. Introduction**`. This is inconsistent.
**Where:** Lines 228-230 in the markdown export.
**How:** Change to:
```
# **2. Theoretical Framework** {#2.-theoretical-framework}
```
Remove the separate "Chapter 2" heading entirely. The introductory paragraph that currently sits under "Theoretical Framework" should remain as the first text under the new heading.
**Done when:** Chapter 2 follows the same heading format as chapters 1, 3, 4, 5, 6, 7.

### Task A4: Fix section 4.5 heading
**What:** Section 4.5 uses bold text `**4.5 Implementation (pilot)**` instead of a proper heading with anchor. It also has a broken Google Docs anchor `{#heading=h.pgqlnth5pp3y}` in the TOC.
**Where:** Line 386 in the markdown (and corresponding TOC entry at line 114).
**How:** Change the heading to:
```
## **4.5 Implementation (pilot)** {#4.5-implementation-(pilot)}
```
And fix the TOC entry to match.
**Done when:** Section 4.5 appears as a proper heading in the document and in the generated TOC.

### Task A5: Fix References heading
**What:** The references section uses `**References (APA 7)**` as bold text, not a proper main heading.
**Where:** Line 568 in the markdown.
**How:** Change to a proper heading that starts on a new page:
```
# **References** {#references}
```
**Done when:** References is a level-1 heading, consistent with other main sections.

### Task A6: Fix Appendices heading
**What:** The appendices heading exists but the content is template placeholder. Student 4 (Onu) will add content. Your job is to ensure the heading is properly formatted.
**Where:** Line 673 in the markdown.
**How:** Ensure it reads:
```
# **Appendices** {#appendices}
```
Remove the "Examples:" label and the bullet list of template suggestions. Student 4 will add real content.
**Done when:** Appendices heading is clean and properly formatted. No template text remains.

### Task A7: Fix AI disclosure placement
**What:** The AI use disclosure statement (lines 668-669) floats between References and Appendices with no heading.
**Where:** Lines 668-669.
**How:** Move it to become an appendix (e.g., "Appendix A: Use of Artificial Intelligence") or place it as a properly headed section before References. The group should decide placement, but it must have a heading.
**Done when:** AI disclosure has a proper heading and is in a logical location.

### Task A8: Fix TOC and Figure List
**What:** TOC page numbers don't match actual document. Figure list only has 4 entries but should include the new Figure 5 (database schema from 4.5, currently "Figure X" - Student 3 will assign the number).
**Where:** Lines 50-160 in the markdown.
**How:** After all other students finish their edits, regenerate the TOC from Google Docs (Insert > Table of Contents > Update). Add the new figure to the Figure List. Ensure all anchors resolve correctly.
**Important:** This task must be done LAST, after all other tracks are complete.
**Done when:** TOC page numbers match actual pages. Figure list includes all figures. All links work.

### Task A9: Fix encoding issues
**What:** The markdown export shows encoding errors like `SÃ¸rlandet` instead of `Sørlandet`, `SprintmÃ¥l` instead of `Sprintmål`, etc.
**Where:** Throughout the document (lines 34, 36, 440, etc.).
**How:** If these errors appear in the Google Docs source, fix them there. If they only appear in the markdown export and the Google Docs looks correct, this is a non-issue for the submitted PDF/Word document. **Check the Google Docs source first.**
**Done when:** The Google Docs document has no encoding errors. The submitted PDF/Word renders Norwegian characters correctly.

### Task A10: Verify Knowit branding
**What:** Niels asked about "KnowIT" vs "Knowit". The current report uses "Knowit" consistently.
**Where:** Throughout the document.
**How:** Verify with Arnt which is correct. The current Knowit website and annual report use "Knowit" (lowercase 'now', lowercase 'it'). If confirmed, ensure all instances match. Also check the front page.
**Done when:** Company name is consistently and correctly spelled throughout.

### Task A11: Check all images render correctly
**What:** The markdown shows `![][image1]`, `![][image2]`, etc. These may be broken references.
**Where:** Lines 1, 368, 392, 434, 438, 442.
**How:** In Google Docs, verify that all images (front page logo, architecture diagram, database schema diagram, 3 Trello screenshots) are properly embedded and visible. Check that the UiA logo is the current version (Niels flagged the old one as outdated - see https://www.uia.no/om-uia/designmanual/uia-logo.html).
**Done when:** All images render in the Google Docs and will render in the exported PDF. Logo is current version.

---

## Track B: References, Academic Language, DSR Framing (Student 2 - Nidal)

**Context for AI assistant:** You are helping fix reference management and academic language precision in a bachelor thesis. The thesis cites sources that are missing from the reference list, has APA formatting errors, and slightly overclaims in a few places. Your job is to fix references, tighten language, and add one explicit DSR statement to Chapter 3. Do NOT rewrite whole chapters.

### Task B1: Add all missing references
**What:** The following sources are cited in the text but have NO entry in the reference list. This is a critical academic error.
**Where:** Reference list (lines 568-667 in the markdown).

Add these 6 references in correct APA 7 format, inserted alphabetically:

1. **Endsley (1995)** - cited in section 2.4
   ```
   Endsley, M. R. (1995). Toward a theory of situation awareness in dynamic systems.
   Human Factors, 37(1), 32-64. https://doi.org/10.1518/001872095779049543
   ```

2. **Handler et al. (2024)** - cited in section 1.1
   - Search for the actual paper: "Handler et al 2024 decision-makers evidence courses of action"
   - It may be about decision support systems or evidence-based decision making
   - If the exact paper cannot be found, the citation in section 1.1 (line 172) must be removed or replaced with a verifiable source

3. **Cloud Security Alliance (2025)** - cited in section 2.7
   ```
   Cloud Security Alliance. (2025). [Exact title of the document about AI-generated code security].
   https://[exact URL]
   ```
   - Search for the actual CSA 2025 publication about AI-generated code being insecure
   - If not findable, replace the citation in section 2.7 with a verifiable source about AI code security risks

4. **Mathews & Nagappan (2024)** - cited in section 2.7
   - Search for: "Mathews Nagappan 2024 acceptance criteria AI generated code TDD"
   - Add the full APA 7 entry once found
   - If not findable, rephrase the claim in section 2.7 to remove the citation or replace with verifiable source

5. **Yang (2025)** - cited in section 2.7 about "vibe coding"
   - Search for: "Yang 2025 vibe coding"
   - This likely refers to a blog post or article defining vibe coding
   - Add the full APA 7 entry

6. **Willison (2025)** - cited in section 2.7 about "vibe coding"
   - Search for: "Willison 2025 vibe coding" (likely Simon Willison)
   - Add the full APA 7 entry

**Done when:** Every citation in the text has a matching reference entry. Zero orphaned citations.

### Task B2: Remove duplicate Lewis et al. (2020)
**What:** Lines 616-618 have two entries for the same paper (arXiv version and NeurIPS proceedings version).
**Where:** Reference list, lines 616-618.
**How:** Keep the NeurIPS proceedings version (more authoritative). Remove the arXiv preprint version. Check that all in-text citations of Lewis et al. (2020) still resolve correctly.
**Done when:** Only one Lewis et al. (2020) entry exists. In-text citations still work.

### Task B3: Fix APA 7 formatting issues
**What:** Many references end with `From.` before the URL. In APA 7, you do not write "From" before URLs (that was APA 6). Also, one IBM reference (line 596) contains `utm_source=chatgpt.com` in the URL.
**Where:** Throughout the reference list (lines 570-667).
**How:**
- Remove `From.` before all URLs. The format should be: `Retrieved February 2026, from https://...` or just `https://...` depending on source type.
- Actually, in APA 7 for web sources: use just the URL with no "Retrieved from" unless the content is likely to change. For DOI-based sources, just the DOI.
- Remove the tracking parameter from the IBM URL: change `https://www.ibm.com/think/topics/observability-vs-monitoring?utm_source=chatgpt.com` to `https://www.ibm.com/think/topics/observability-vs-monitoring`
**Done when:** All references follow APA 7 format. No "From." artifacts. No tracking URLs.

### Task B4: Audit and remove weak/unused references
**What:** Niels said the reference list is too long and that sources used only as "word explanations" are unnecessary. Several references may not be cited in the new report text.
**Where:** Reference list.
**How:** For each reference, search the document text to confirm it is actually cited. Consider removing or moving to appendix:
- Atlan (2025) - check if cited
- Chan et al. (2022) - check if cited in new version
- Liang et al. (2024) - check if cited
- Three Group Solutions (2025) - check if cited
- Timescale (n.d.) "best time-series databases compared" - check if cited
- OpenAI (2025) ChatGPT page - this is just a product page, not a scholarly source
- Model Context Protocol (2025d) security best practices - check if cited

**Rule:** If a reference is cited in the text, keep it. If it is not cited, remove it. Do not remove references just because they seem weak if they are actually used.
**Done when:** Every reference in the list is actually cited in the text. No orphaned references remain.

### Task B5: Tighten overclaim language in abstract, section 1.4, and section 7.1
**What:** All three reviewers flagged that the abstract and conclusion sometimes claim "agent-based observability" accomplishments that are broader than what Scope 1 actually proves. The UDS Scope 1 baseline is a dashboard + metrics + logs + MCP access for one vessel. The stronger agentic analysis is in the legacy path. The report should not imply Scope 1 itself is a full agentic solution.
**Where:**
- Abstract (line 46-48): "The project demonstrates that an agentic observability approach can provide more useful support than dashboards alone by linking incidents to context, explanation, and suggested follow-up."
- Section 1.4 (line 208): Research question says "agent-based observability approach"
- Section 7.1 (line 520-524): Conclusion says the approach "can provide clear practical value"
- Section 2.4 end (line 274): Claims about agentic observability

**How:** Use hedged language. Replace assertive claims with qualified ones:
- "demonstrates" → "suggests" or "indicates at prototype level"
- "can provide more useful support" → "may support" or "shows potential to support"
- When discussing Scope 1 specifically, be precise: "The UDS Scope 1 baseline demonstrates incident-oriented dashboard support with contextual metrics, logs, and MCP access. The agentic analysis path, demonstrated in the legacy telemetry track, shows how AI-generated explanations can add further interpretive value."
- Do NOT rewrite entire sections. Only change the specific sentences that overclaim.

**Done when:** Abstract, research question answer, and conclusion accurately reflect the difference between what the UDS dashboard proves and what the legacy agentic path demonstrates. No sentence claims more than the repo evidence supports.

### Task B6: Add explicit DSR statement to Chapter 3
**What:** Chapter 2 frames the project as Design Science Research (Peffers et al., 2007), but Chapter 3 (Method) never explicitly says "this project was conducted as a Design Science Research study." Codex 1 and Codex 2 both flagged this gap.
**Where:** Section 3.1 (line 304-306).
**How:** Add one clear sentence at the start of section 3.1, such as:
> "This project was conducted as a Design Science Research (DSR) study, following the methodology outlined by Peffers et al. (2007). In DSR, the research process involves identifying a relevant problem, designing and developing an artifact to address it, demonstrating the artifact, and evaluating it against the defined objectives. In this project, the artifact is the Scope 1 UDS incident-monitoring prototype."

Then briefly map the DSR steps to the project phases (problem identification → design → development → demonstration → evaluation). This should be 2-3 sentences, not a full page.

**Done when:** Chapter 3 explicitly claims DSR as the research design and briefly maps the project to DSR steps.

---

## Track C: Chapter 5 Rewrite, Figures, Sections 7.3/7.4 (Student 3 - Kristian)

**Context for AI assistant:** You are helping strengthen the Results chapter and fix specific issues in Chapters 5 and 7 of a bachelor thesis. The biggest task is rewriting section 5.2 to contain actual sprint deliverables instead of just Trello screenshots. You should use real project history (Trello board, meeting notes, git log) as sources. Do NOT invent deliverables that didn't happen.

### Task C1: Rewrite section 5.2 "Results: sprint deliverables"
**What:** This is the single most important remaining fix. Niels specifically asked for "follow-up on product backlog, sprint for sprint, what you learned and produced." The current section only describes three Trello screenshots with generic commentary. It needs actual deliverables.
**Where:** Section 5.2 (lines 430-446 in the markdown).
**How:**

Structure the section as a phase-by-phase or sprint-group summary. Use the three phases from the old report as a starting structure, but update them to reflect the actual project trajectory including the UDS pivot:

**Phase 1: Exploration (Sprints 1-6, approximately weeks 1-6)**
- What was planned: Understand the domain, explore technologies, define project direction
- What was delivered: Initial C# exploration, technology evaluation, decision to pivot to Python
- Key learning: Dashboard-only approach insufficient, shifted toward agentic observability
- Direction change: C# → Python, static dashboard → agent-based architecture

**Phase 2: Core Development (Sprints 7-14, approximately weeks 7-14)**
- What was planned: Build the core prototype pipeline
- What was delivered: Docker-based environment, TimescaleDB setup, legacy telemetry generator, Ship Operations dashboard, agent service with MCP/RAG integration, Ollama integration
- Key learning: Local LLM requires REST adapter for MCP; RAG grounding improves explanation quality
- Direction change: Geir's UDS input shifted focus from sensor telemetry to application monitoring

**Phase 3: UDS Pivot and Finalization (Sprints 15-20, approximately weeks 15-20)**
- What was planned: Integrate UDS schema, build Scope 1 baseline, test and finalize
- What was delivered: UDS schema and reference data, uds-seeder, UDS Incident Monitoring dashboard, MCP UDS tools, fresh-stack acceptance validation
- Key learning: Scope model prevented overclaiming; fresh-DB validation most reliable proof path
- Scope decisions: Scope 1 as delivered baseline, Scope 2/3 as future work

**Important rules:**
- Use real dates and sprint numbers from Trello
- Reference actual deliverables from the repo (files, services, dashboards)
- Mention the direction changes honestly - they are a strength, not a weakness
- Keep the Trello screenshots as supporting figures, but add narrative around them
- This section should be approximately 1.5-2 pages of text (not counting figures)

**Done when:** Section 5.2 contains a concrete phase-by-phase deliverable summary that answers "what was planned, what was delivered, what changed and why" for each project phase. Trello screenshots remain as supporting evidence.

### Task C2: Replace "Figure X" with real figure number
**What:** Section 4.5 has a placeholder "Figure X: Core UDS database schema..." that needs a real number.
**Where:** Lines 392-394 in the markdown.
**How:**
- The current figures are: Figure 1 (architecture), Figure 2 (Trello initial), Figure 3 (Trello updated), Figure 4 (Trello detailed).
- The database schema diagram should become **Figure 5** (or Figure 2 if you renumber to put it before Trello screenshots - discuss with group).
- Recommended: Keep it as **Figure 5** to avoid renumbering all Trello references.
- Change `Figure X:` to `Figure 5:` in the text.
- Update the Figure List (Student 1 will handle the Figure List in Task A8, but tell them the number).
- Ensure the actual diagram image is embedded in Google Docs.

**Done when:** "Figure X" is replaced with a real number. The figure is in the Figure List. The image renders.

### Task C3: Fix figure reference error in section 5.2
**What:** Line 446 says "the progression from Figure 1 to Figures 2 and 3" but in the new report, Figure 1 is the architecture diagram, not a Trello screenshot. The Trello screenshots are Figures 2, 3, 4.
**Where:** Line 446 in the markdown (end of section 5.2).
**How:** Change to: "the progression from Figure 2 to Figures 3 and 4 illustrates the team's methodological development."
**Done when:** Figure references in section 5.2 correctly refer to the Trello screenshot figures.

### Task C4: Rewrite section 7.3 Future Work to name User Stories
**What:** Section 7.3 discusses future work generically without ever naming User Story 2 or User Story 3. Section 6.1 already evaluates against all three user stories, so 7.3 should connect to that.
**Where:** Section 7.3 (lines 540-554 in the markdown).
**How:** Restructure 7.3 to have clear subsections or paragraphs:

1. **Scope 2 - User Story 2 (Multi-vessel incident monitoring):** The most direct next step. Requires multi-vessel aggregation, cross-vessel correlation, and systemic issue identification. The current single-vessel architecture provides the foundation.

2. **Scope 3 - User Story 3 (NOC support):** Requires role-specific workflows, case-handling support, and broader operational context. Partially anticipated by the current architecture but not delivered.

3. **Production hardening:** Authentication, authorization, migration strategy, real data integration, connectivity handling.

4. **Agentic expansion of UDS path:** Connecting the AI agent (currently strongest in legacy path) to UDS incident context for automated explanation and follow-up suggestion.

5. **User validation:** Structured user testing with actual maritime operators.

Keep the existing generic paragraphs about anomaly detection, RAG expansion, and MCP tool extension, but frame them under the scope model. Total section should be ~1-1.5 pages.

**Done when:** Section 7.3 explicitly names User Stories 2 and 3 and connects all future work items to the scope model.

### Task C5: Add individual contributions to section 7.4
**What:** Section 7.4 (Reflection on teamwork) doesn't mention who did what. The old report mentioned technical ownership areas. The repo's archived `docs/archive/WORK_DISTRIBUTION.md` documents this.
**Where:** Section 7.4 (lines 556-566).
**How:** Add one paragraph that briefly states each member's primary area of responsibility:
- Jonas: project lead, stakeholder coordination, Grafana dashboards
- Kristian: tech lead, agent/LLM services, integration architecture
- Nidal: Scrum master, RAG/knowledge base, pgvector integration
- Onu: MCP service, generator/seeder enhancements, database work

Keep it factual, one sentence per person. State that all members contributed to integration, testing, and report writing.

**Done when:** Section 7.4 includes a brief statement of individual contributions consistent with `docs/archive/WORK_DISTRIBUTION.md`.

### Task C6: Add "Lessons learned" back to section 6.2
**What:** The old report had a "Lessons learned" subsection under 6.2 with genuinely insightful content. The new report dropped it. Some of those insights (constrained model scope, RAG grounding value, time-series data representation, clear scope boundaries) should be preserved.
**Where:** Section 6.2, after "Weaknesses and technical risks" (after line 502).
**How:** Add a subsection:
```
### **Lessons learned** {#lessons-learned}
```
Include 3-4 practical insights from the project, such as:
1. Constraining the model's scope proved at least as important as improving its capabilities
2. RAG demonstrated practical value for grounding explanations
3. The direction change from dashboard-only to agentic observability improved the final delivery
4. The scope model (Scope 1/2/3) was essential for managing expectations

Keep it to ~0.5 pages. These should be real lessons, not generic platitudes.

**Done when:** A "Lessons learned" subsection exists in 6.2 with 3-4 concrete, honest insights.

### Task C7: Reduce repetition between sections 1.1 and 1.3
**What:** Sections 1.1 (Background) and 1.3 (Problem area) overlap in their description of dashboard limitations and cognitive burden on operators.
**Where:** Sections 1.1 and 1.3 (lines 168-200).
**How:** Review both sections. Remove duplicate sentences or concepts. Section 1.1 should focus on background/motivation (what exists, what's changing, why this matters). Section 1.3 should focus on the specific problem (what gap exists, what challenge the project addresses). Do not remove unique content from either section.
**Done when:** Sections 1.1 and 1.3 have minimal overlap while each maintaining their distinct purpose.

---

## Track D: Appendices, Content Polish, Final QA (Student 4 - Onu)

**Context for AI assistant:** You are helping create actual appendix content and doing final quality assurance on a bachelor thesis. The appendices section is currently empty (template placeholder). You need to fill it with real supporting material. You also handle several smaller content fixes and a final proofreading pass.

### Task D1: Create appendix content
**What:** The appendices section currently contains only template examples. It needs real content.
**Where:** After the References section.
**How:** Create the following appendices:

**Appendix A: User Stories (from Geir)**
- Include the three user stories verbatim (they are in the review prompt and in docs/UDS_dashboard_spec.md context)
- Include the system constraints and requirements from Geir's document
- Brief note on source: "Received from Geir Borgi, Telenor Maritime, approximately February 2026"

**Appendix B: Scope 1 Acceptance Checklist**
- Adapt from docs/SCOPE1_ACCEPTANCE_CHECKLIST.md
- Show the repeatable validation flow used for fresh-stack testing
- Include the acceptance criteria used on March 12, 2026

**Appendix C: Architecture Diagrams**
- Include the high-level architecture diagram (same as Figure 1 but full size)
- Include the UDS database schema diagram (same as Figure 5)
- If any earlier/intermediate architecture versions exist, include one to show evolution

**Appendix D: Selected Sprint Goals**
- If available from Trello, include 3-5 representative sprint goal screenshots or summaries
- These supplement section 5.2 without cluttering the main text

**Appendix E: Technology Stack Overview**
- Brief table listing all technologies used: Python, FastAPI, TimescaleDB/PostgreSQL, Grafana, Docker Compose, Ollama, pgvector
- One line per technology explaining its role
- This replaces the old "technology encyclopedia" content that Niels wanted removed from Chapter 2

**Important:** Appendices do NOT count toward the 35-page limit. They should contain supporting material only, not core arguments.

**Done when:** Appendices section contains real content in at least 4-5 appendices. Template placeholder text is completely removed.

### Task D2: Add sprint duration/rhythm to Chapter 3
**What:** Chapter 3 describes the hybrid work process but never mentions specific sprint duration or meeting rhythm.
**Where:** Section 3.3 (lines 316-320 in the markdown).
**How:** Add one sentence specifying:
- Sprint duration (e.g., "Sprints lasted approximately one to two weeks")
- Meeting rhythm (e.g., "Daily scrums were held on weekdays, with weekly sprint reviews and planning sessions")
- How often stakeholder meetings occurred

Keep it to 1-2 sentences. Do not invent details that aren't true.

**Done when:** Section 3.3 includes specific sprint duration and meeting rhythm.

### Task D3: Make section 6.3 more concrete
**What:** Section 6.3 discusses implications for practice but could be more specific about how Geir and Knowit would actually use the prototype.
**Where:** Section 6.3 (lines 504-514 in the markdown).
**How:** Add 2-3 sentences that are more concrete:
- "The repository now contains a tracked UDS schema, seeded reference data, and a repeatable acceptance checklist that Geir can use to validate whether the monitoring flow matches Telenor Maritime's actual operational needs."
- "For Knowit, the Docker-based setup means the prototype can be demonstrated to other maritime customers without requiring any local installation beyond Docker Desktop."
- Connect to the acceptance checklist as a concrete handoff artifact.

**Done when:** Section 6.3 has at least 2-3 concrete, verifiable statements about how Geir/Knowit can use the prototype.

### Task D4: Final proofreading pass
**What:** After all other tracks are complete, do one full read-through checking for:
**Where:** Entire document.
**Checklist:**
- [ ] All figure numbers are sequential and correctly referenced in text
- [ ] All section numbers match TOC entries
- [ ] No "Figure X" or placeholder text remains
- [ ] No "TODO", "FIXME", or similar markers
- [ ] All image references render correctly
- [ ] Norwegian characters display correctly
- [ ] Consistent terminology: "Scope 1" (not "scope 1"), "User Story 1" (not "user story 1")
- [ ] No sentences cut off mid-thought
- [ ] Line spacing is consistent throughout
- [ ] Each main chapter starts on a new page
- [ ] Under each chapter title, there is introductory text before the first subheading
- [ ] Heading levels go no deeper than level 3 (###)
- [ ] No orphaned citations (every citation has a reference; every reference is cited)

**Important:** This task must be done LAST, after tracks A, B, and C are complete.

**Done when:** Full proofread is complete with all checklist items verified.

---

## Execution Order and Dependencies

```
Week 1 (parallel work):
  Track A: Tasks A1-A7, A9-A11 (everything except TOC)
  Track B: Tasks B1-B6
  Track C: Tasks C1-C7
  Track D: Tasks D1-D3

Week 1 end (sync point):
  - All 4 students review each other's changes
  - Resolve any conflicts in Google Docs

Week 2 (sequential):
  Track A: Task A8 (regenerate TOC - must be last)
  Track D: Task D4 (final proofreading - must be very last)
  All: Group read-through and final approval
```

## Success Criteria

The report is ready for submission when:
1. Front page has a title
2. Norwegian sammendrag exists
3. Every in-text citation has a reference entry (and vice versa)
4. No placeholder text (Figure X, template examples) remains
5. Section 5.2 contains actual sprint/phase deliverables
6. Appendices contain real supporting material
7. Chapter headings are consistent
8. TOC matches actual pages
9. The report stays within ~35 pages (excluding appendices and references)
10. A full group read-through finds no remaining issues
