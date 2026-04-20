# Bachelor Thesis — Task Split and Writing Plan

> Generated after the group meeting on 2026-04-20.
> Based on a full repo + thesis analysis by Claude and reviewed by Codex.
> The meeting is done. Pick your track, check the open questions section, and start.
> This document is intentionally neutral: the tracks below are suggested work packages, not fixed person assignments.

---

## How to read this document

1. Read the **Diagnosis** first — one paragraph that explains why the thesis needs work.
2. Check the **Chapter Decision Table** to understand what each section needs.
3. Go to your **Track** and work from that checklist. Do not edit chapters owned by other tracks.
4. The **Open Questions** section lists things that must be consistent across tracks — confirm these are resolved before writing.
5. The **Priority Order** section tells you what is blocking vs. nice-to-have.

---

## Diagnosis

The thesis was written after Scope 1 and has not been updated since. It describes a one-vessel, three-tool, synthetic-telemetry prototype and treats User Stories 2 and 3 as future work — but those are now fully implemented, along with the Scope 3 AI integration layer and a working dynamic dashboard pivot. The abstract overclaims "agent-based observability" in a way that fits Scope 1 just barely, but the conclusion, future work, and sprint deliverables section are factually wrong about what the project delivered. Chapter 5.2 is three Trello screenshots with captions — the weakest possible treatment of sprint results. The thesis needs a targeted expansion in Chapters 4, 5, and 7 to reflect reality, plus a handful of critical formalia fixes that are blocking submission.

**Important framing rule for all tracks:** Always describe the project history as:
**Scope 1 → Scope 2 → Scope 3 foundation → dynamic dashboard pivot/current sprint.**
Do not call it "4 scopes" as a flat list.

---

## Chapter-by-Chapter Decision Table

| Section | Decision | Reason |
|---|---|---|
| Front page | Fix immediately | Title is blank; encoding errors (Sørlandet etc.) |
| Sammendrag | Add new | Norwegian summary required by UiA; does not exist |
| Abstract | Rewrite | Scope 1 only; needs to frame full delivery: UDS, 13 tools, dynamic layer |
| Ch 1.1 Background | Keep + tighten | Solid framing; trim repetition with 1.3 |
| Ch 1.2 Client context | Update | Add Geir as UDS user story source; mention UDS/Telenor Maritime concretely |
| Ch 1.3 Problem area | Update | Still sensor-only; add application monitoring dimension |
| Ch 1.4 Research question | Keep | Formulation holds across the full scope |
| Ch 1.5 Scope and limitations | Rewrite | Currently says "one vessel" — actually 3 vessels, 6 apps, dynamic dashboard |
| Ch 2.1–2.6 Theory | Keep mostly | Academic quality is good; citations solid |
| Ch 2 — possible 2.7 | Only if page room permits | Tightening 2.4 is probably better than expanding theory with a new section |
| Ch 3 Method | Tighten + DSR fix | Add explicit DSR framing; add one paragraph on stakeholder alignment failure as methodological learning |
| Ch 4.1–4.2 | Keep | Requirements and clarifications hold |
| Ch 4.3 Architecture | Update | Architecture figure and description are Scope 1 only; needs updated diagram |
| Ch 4.4 Technology | Update | Missing: pgvector, nomic-embed-text, Ollama limitations, dynamic generation rationale |
| Ch 4.5 Implementation | Expand significantly | Currently Scope 1 only; needs UDS, Scope 2, Scope 3, dynamic sub-sections |
| Ch 4.6 Testing | Tighten | Add one paragraph on UDS validation and dynamic flow testing |
| Ch 5.1 Results pilot | Rewrite | Should cover the full delivery arc, not just Scope 1 |
| Ch 5.2 Sprint deliverables | Rewrite completely | Three Trello screenshots is not a deliverables section |
| Ch 5.3 Phases | Rewrite | Phase 3 "finalization" is wrong; real story is Scope 1 → UDS → Scope 2 → Scope 3 → Dynamic |
| Ch 6.1 Discussion | Update | Must reflect dynamic dashboard as a response to Geir's feedback |
| Ch 6.2 Strengths | Update | Add: programmatic dashboard generation, 13 MCP tools, UDS app monitoring |
| Ch 6.2 Weaknesses | Update | Add: stakeholder misalignment (honest), local LLM limitations in production context |
| Ch 6.2 Lessons learned | Expand | Stakeholder alignment failure with Geir is the most important project-level lesson |
| Ch 6.3 Implications | Update | Reference the full delivery including dynamic dashboard |
| Ch 7.1 Conclusion | Rewrite | Answer to research question is Scope 1 framed; needs to reflect actual delivery |
| Ch 7.2 Contributions | Update | Add UDS monitoring, 13 tools, dynamic dashboard, presentation result |
| Ch 7.3 Future Work | Rewrite | User Stories 2 and 3 listed as future work but are delivered — remove them |
| Ch 7.4 Teamwork reflection | Expand | Add the scope-pivot and stakeholder alignment learning |
| References | Cleanup | IBM URL has utm_source=chatgpt.com; duplicate Lewis; 5–6 missing entries; "From." APA errors |
| Appendices | Add new | Currently a template placeholder; create: User Stories, Tech Stack, MCP Tools list |
| AI disclosure | Fix placement | Give it a proper section heading |

---

## Priority Order

### Must fix before submission (blocking)

1. Front page title — blank (C1)
2. Norwegian sammendrag — required by UiA (C2)
3. Abstract — factually outdated and overclaims scope
4. Ch 5.2 rewrite — all three reviewers flagged this; currently three Trello screenshots
5. Ch 5.3 phases — Phase 3 "finalization" is wrong; doesn't mention UDS/Scope 2/3/dynamic
6. Ch 7.3 Future Work — User Stories 2 and 3 listed as future work but are delivered
7. Ch 7.1 conclusion answer — still scoped to the Scope 1 prototype
8. Ch 4.5 implementation — needs UDS, Scope 2, Scope 3, dynamic sub-sections
9. Figure X placeholder — still in section 5.3
10. Missing references — 5–6 cited sources not in reference list
11. Duplicate Lewis et al. (2020)
12. IBM utm URL — signals AI-sourced reference
13. "From." in references — APA 7 error throughout

### Should fix if time permits

14. Ch 4.3 architecture diagram update (add UDS and dynamic paths)
15. Ch 3 explicit DSR framing sentence
16. Ch 6.2 stakeholder misalignment as lessons learned
17. Ch 1.5 scope update (still says "one vessel")
18. Appendices creation (User Stories, Tech Stack, MCP tool list)
19. AI disclosure heading fix
20. Encoding errors on front page (Sørlandet, Sprintmål)

### Nice to improve (only if time remains)

21. Knowit vs. KnowIT consistency throughout
22. Trim repetition between 1.1 and 1.3
23. Individual contributions subsection in 7.4
24. TOC page numbers (auto-updates in Google Docs on export)

---

## Track A — Front Matter, Abstract, Introduction Update

**Suggested owner:** ___________________________

**Suggested scope:** Front page, Sammendrag, Abstract, Ch 1.1, Ch 1.2, Ch 1.3, Ch 1.5

**Estimated effort:** 4–5 hours

**Dependency:** Before finalizing the abstract, get a one-paragraph summary from Track C confirming exactly what the dynamic layer delivers. A quick message is enough — you do not need to wait for the full Track C draft.

### Tasks

- [ ] Agree with the group on the project title (see Open Questions), then add it to the front page
- [ ] Fix encoding errors on front page (Sørlandet, Sprintmål)
- [ ] Rewrite the abstract to cover the full delivery: 3-vessel UDS schema, 13 MCP tools, AI chat, alert trends, dynamic dashboard pivot, honest limitations — do not overclaim production readiness
- [ ] Write the Norwegian sammendrag (150–200 words, mirrors updated abstract, no overclaiming)
- [ ] Tighten Ch 1.1 so it focuses on background/motivation and does not repeat points already made in Ch 1.3
- [ ] Update Ch 1.2: add Geir Borgi and Telenor Maritime UDS user stories as the trigger for the UDS pivot; mention Color Line context briefly
- [ ] Update Ch 1.3 so the problem area is not sensor-only; add the application-monitoring dimension and reduce repetition with Ch 1.1
- [ ] Update Ch 1.5 scope: replace "one vessel" with the actual delivery boundary; add that the dynamic dashboard is a proof-of-concept layer, not a production system

### Evidence sources
- `README.md` — project overview and full delivery status
- `docs/ARNT_GEIR_FEEDBACK_2026-04-07.md` — Geir's user stories and pivot rationale
- `docs/DYNAMIC_DASHBOARD_TASK_PLAN.md` Merge Status section — what the dynamic layer actually delivered
- `CLAUDE.md` Current Status — authoritative list of what is complete across all scopes

---

## Track B — Method, References, Chapter 5 Results Rewrite

**Suggested owner:** ___________________________

**Suggested scope:** Ch 2.4 light tightening if needed, Ch 3, Ch 5, References

**Estimated effort:** 5–6 hours

**Dependency:** Before writing Ch 5.2, get the deliverables list from Track C. You can draft the structure of Ch 5.2 first (scope phases as headings, tables ready) and fill in the content once Track C confirms it. Do not wait idly — start Ch 3 and the reference cleanup while waiting.

> Note from Codex review: Track B is the heaviest alongside Track C. If this track gets overloaded, move some reference source-verification work to Track A or Track D rather than rushing it.

### Tasks

**Ch 3 Method:**
- [ ] Add one sentence in Ch 3.1 explicitly naming DSR (Design Science Research) as the research design framing
- [ ] Add one short paragraph in Ch 3.1 or 3.3 on the stakeholder alignment failure with Geir — frame it as a methodological learning about industry-collaborative iterative development, not as an embarrassment. The point is: in retrospect, more structured stakeholder alignment early would have prevented the pivot.

**Ch 2 Theory (light cleanup only):**
- [ ] Tighten Ch 2.4 if needed so "agentic observability" is described honestly at prototype level
- [ ] Do not add a full new Ch 2.7 unless page room clearly allows it and the group explicitly agrees

**Ch 5 Results:**
- [ ] Rewrite Ch 5.1 to cover the full delivery arc (Scope 1 → UDS pivot → Scope 2 → Scope 3 → dynamic). Keep total length similar to current.
- [ ] Replace Ch 5.2 (currently three Trello screenshots) with an actual deliverables section organized by scope phase. Each phase gets: what was built, what tools/dashboards/endpoints were delivered, what user story it addresses. Use tables or bullet lists for clarity.
- [ ] Rewrite Ch 5.3 phase descriptions to reflect the actual phases: Exploration → Scope 1 development → UDS/Scope 2 pivot → Scope 3 AI integration → Dynamic dashboard sprint
- [ ] Fix the "Figure X" placeholder in section 5.3 — coordinate with Track C on whether a project timeline image exists, or replace it with a phase/scope table

**References:**
- [ ] Go through every citation in the thesis text; for each one, verify it exists in the reference list — add the 5–6 missing ones
- [ ] Remove the duplicate Lewis et al. (2020) entry
- [ ] Remove `utm_source=chatgpt.com` from the IBM observability URL
- [ ] Remove all "From." instances from reference entries (APA 7 does not use this format)
- [ ] Add any new sources needed for Track C's new sections once that track provides them

### Evidence sources
- `db/init/003_uds.sql` and `004_uds_reference_data.sql` — schema proof (3 vessels, 6 apps, 18 links)
- `services/mcp/main.py` — all 13 MCP tools
- `grafana/dashboards/` — all 5 provisioned dashboards
- `services/agent/dynamic/` — the dynamic layer files (all 10 exist)
- `docs/DYNAMIC_DASHBOARD_TASK_PLAN.md` Merge Status — exact list of what was merged

---

## Track C — Chapter 4 Expansion: UDS, Scope 2–3, Dynamic Dashboard

**Suggested owner:** ___________________________

**Suggested scope:** Ch 4.3, Ch 4.4, Ch 4.5, Ch 4.6

**Estimated effort:** 6–7 hours (critical path — other tracks depend on your content)

**Dependency:** This is the critical-path track. Track A needs the dynamic layer description to finalize the abstract. Track B needs the deliverables list to write Ch 5.2. Aim to have a draft of Ch 4.5 sub-sections done by end of Day 1 and share the key facts with both of them.

> Note from Codex review: For exact technical identifiers, always use repo evidence. The dynamic routes exist in `services/agent/routes/dynamic_dashboard.py`. The dynamic layer has 10 files in `services/agent/dynamic/`. Be careful with branch-vs-main wording — state the actual merge status at the time of writing, based on the current branch, not the docs.

### Tasks

**Ch 4.3 Architecture:**
- [ ] Update the architecture description to reflect the full system: legacy telemetry path + UDS application monitoring path + dynamic dashboard path
- [ ] Update or replace Figure 1 with a diagram that shows both paths and the dynamic layer. If no diagram is ready, describe the architecture clearly in text and note that Figure 1 covers only the Scope 1 baseline.

**Ch 4.4 Technology:**
- [ ] Add justification for pgvector (similarity search for RAG retrieval)
- [ ] Add justification for nomic-embed-text (local embedding model, no cloud dependency)
- [ ] Add the reasoning behind deterministic dashboard generation (why the LLM does not generate raw Grafana JSON — reliability and predictability)
- [ ] Add honest assessment of Ollama/llama3.2 limitations in a production context (resource constraints, quality vs. production-grade models)

**Ch 4.5 Implementation — expand into sub-sections:**
- [ ] **4.5.1 UDS schema and reference data** — describe the 3-vessel, 6-app, 18-link schema; the seeder design; and what reference data was fixed vs. seeded dynamically. Evidence: `db/init/003_uds.sql`, `db/init/004_uds_reference_data.sql`, `db/seed/uds_seed.sql`
- [ ] **4.5.2 Scope 2 — fleet and NOC support** — describe: Fleet Overview dashboard, NOC Support dashboard, and 5 new MCP tools (get_fleet_status, get_fleet_alerts, get_cross_vessel_correlation, get_incident_timeline, get_operational_snapshot). Evidence: `grafana/dashboards/fleet_overview.json`, `noc_support.json`, `services/mcp/main.py`
- [ ] **4.5.3 Scope 3 — AI integration layer** — describe: UDS AI analysis endpoint (`GET /api/v1/uds/analyze/view`), AI chat interface (`GET/POST /api/v1/chat`), alert trend analysis, confidence labels (Low/Medium/High), 13 tools total. Evidence: `services/agent/routes/analyze.py`, `routes/chat.py`, `grafana/dashboards/alert_trends.json`
- [ ] **4.5.4 Dynamic dashboard pivot** — describe: orchestrator, scenario selector (service_down / runtime_pressure / connectivity / generic_incident), dashboard builder, Grafana HTTP API write path, stable UIDs (maritime_dynamic_incident / fleet / noc), inject script for demo reliability, what is deterministic vs. what uses the LLM (summary text only). State clearly whether this is merged to main or on a branch at time of writing. Evidence: `services/agent/dynamic/` (all 10 files), `scripts/inject_dynamic_incident.py`, `services/agent/routes/dynamic_dashboard.py`, `docs/DYNAMIC_DASHBOARD_TASK_PLAN.md` Merge Status

**Ch 4.6 Testing:**
- [ ] Add one paragraph on UDS validation: fresh-stack validation process, acceptance checklist. Evidence: `docs/SCOPE1_ACCEPTANCE_CHECKLIST.md`
- [ ] Add one paragraph on dynamic flow testing: inject → trigger → generated dashboard verification

**Coordination:**
- [ ] Send Track B the exact deliverables list for Ch 5.2 once Ch 4.5 is drafted
- [ ] Send Track A a one-paragraph summary of what the dynamic layer delivers for the abstract

### Evidence sources
- `db/init/` — all schema files
- `services/agent/dynamic/` — all 10 files in this directory
- `services/mcp/main.py` — all 13 tools
- `grafana/dashboards/` — all dashboard JSON files
- `docs/DYNAMIC_DASHBOARD_TASK_PLAN.md` — Merge Status section
- `docs/SCOPE1_ACCEPTANCE_CHECKLIST.md`

---

## Track D — Discussion, Conclusion Rewrite, Appendices, Final QA

**Suggested owner:** ___________________________

**Suggested scope:** Ch 6 updates, Ch 7 rewrite, Appendices, AI disclosure fix, final consistency pass

**Estimated effort:** 5–6 hours

**Dependency:** Get Track C's confirmed dynamic layer description before finalizing Ch 7.1 and Ch 7.2. You can write Ch 6 and the Ch 7 skeleton on Day 1 based on current understanding, then refine on Day 2.

> Note from Codex review: Track D should own the final "consistency pass" — make sure the abstract, conclusion, future work, and appendices all tell the same coherent story. Do this after the other tracks are done.

### Tasks

**Ch 6 Discussion:**
- [ ] Ch 6.1: update the discussion to reflect the full scope. Add that the dynamic dashboard pivot was the direct response to Geir's feedback that the dashboards were not dynamic enough — this is the project's closing argument.
- [ ] Ch 6.2 strengths: add programmatic dashboard generation, 13 MCP tools, multi-vessel UDS monitoring, AI chat, working proof-of-concept demonstration to the existing strengths
- [ ] Ch 6.2 weaknesses/lessons learned: add the stakeholder misalignment with Geir as the most important project-level lesson. The framing: we built what Arnt asked for (AI analysis layer) without fully synchronizing with Geir's vision (dynamic adaptation at runtime). This is honest and shows professional maturity.
- [ ] Ch 6.3 implications: update to reference the full delivery including the dynamic dashboard

**Ch 7 Conclusion:**
- [ ] Ch 7.1: rewrite the research question answer. The answer is no longer "Scope 1 demonstrated X." It needs to cover: tool-calling agent loop (Scope 1), multi-vessel fleet monitoring (Scope 2), AI chat and alert trends (Scope 3), and dynamic dashboard generation (current sprint) — as a progressively more complete answer to the research question.
- [ ] Ch 7.2 contributions: update the list. Add: 3-vessel UDS monitoring with 13 MCP tools; UDS AI analysis with tool-call trace and RAG display; AI chat; alert trend prediction; programmatic Grafana dashboard generation from incident context.
- [ ] Ch 7.3 future work: remove User Stories 2 and 3 (they are delivered). Real future work: real maritime data validation, production deployment (auth, security, MCP protocol compliance), operator usability testing, full multi-agent coordination (separate reasoning agents), scalability beyond 3 vessels/6 apps.
- [ ] Ch 7.4 teamwork reflection: add the scope pivot as a key teamwork moment — the group had to re-align mid-project around Geir's feedback, redistribute tasks, and build a new layer on top of a working system under time pressure. This is a genuine team capability worth documenting.

**Appendices:**
- [ ] Create Appendix A: User Stories — all three from Geir, with acceptance criteria
- [ ] Create Appendix B: Tech stack overview — services, versions, Docker services list
- [ ] Create Appendix C: MCP tool inventory — all 13 tools, one line each (name + purpose)

**Formalia:**
- [ ] Fix AI disclosure heading — give it a proper section heading with the group members listed
- [ ] Final QA pass: verify no broken figure references (no "Figure X"), verify all chapter cross-references, check total page count against 35-page target, verify Knowit vs. KnowIT consistency throughout

### Evidence sources
- `docs/ARNT_GEIR_FEEDBACK_2026-04-07.md` — stakeholder misalignment and pivot rationale
- `docs/DYNAMIC_DASHBOARD_TASK_PLAN.md` — dynamic pivot description
- `CLAUDE.md` Current Status — authoritative list of all delivered scopes
- `docs/SCOPE1_ACCEPTANCE_CHECKLIST.md`
- `README.md` Known Limitations section

---

## Open Questions — Confirm these are resolved

These must be consistent across all tracks. If unresolved, they will cause contradiction between chapters.

**Q1 — Project title.**
The front page title is blank. Agreed title: ___________________________
*(Track A cannot finalize the front page or sammendrag until this is locked.)*

Suggested options:
- "Agentic Observability for Maritime Application Monitoring: A Prototype with Dynamic Dashboard Generation"
- "Agent-Based Maritime Observability: From Incident Dashboards to Dynamic Dashboard Generation"

**Q2 — Phase naming in Ch 5.**
Do we restructure Chapter 5 around Scopes (Scope 1, Scope 2, Scope 3, Dynamic pivot) or keep the existing Phase 1/2/3 structure?
- Scopes is more accurate to the actual work
- Phases matches the current Trello framing
*(Track B cannot finalize Ch 5.2 and 5.3 structure until this is decided.)*

**Q3 — How much to say about the Geir misalignment.**
The stakeholder alignment failure is the most honest and interesting thesis reflection. Agreed framing:
- Option A: "we misunderstood Geir's vision" (direct)
- Option B: "the two stakeholder visions were not fully synchronized early enough" (diplomatic)
*(Affects Ch 6.2 lessons learned and Ch 7.4 — both part of Track D.)*

**Q4 — Is the dynamic dashboard merged to main before submission?**
At the time of writing Ch 4.5.4, Track C must state whether the dynamic layer is on `main` or still on a feature branch. The thesis must reflect the actual state honestly.
*(Check `docs/DYNAMIC_DASHBOARD_TASK_PLAN.md` Merge Status and current git branch.)*

**Q5 — Screenshot for Figure X placeholder.**
Section 5.3 has a broken "Figure X — project timeline" placeholder. Options:
- Replace with a project timeline screenshot or Gantt image if anyone has one
- Replace with a phase/scope table instead (no image needed)
*(Track B owns this fix but needs an answer from the group.)*

**Q6 — Who does the final Google Docs transfer?**
All tracks produce text in their own environment. Someone must be responsible for assembling everything into the master Google Docs document and doing the final render/export check before submission.
Assigned to: ___________________________

---

## Dependency Map

```
Day 1 morning
  Track C → draft Ch 4.5 sub-sections — critical path starts here
  Track B → draft Ch 5.2 structure and start reference cleanup
  Track D → draft Ch 6 and Ch 7 skeleton based on current knowledge
  Track A → front page fixes; wait for title agreement; draft sammendrag structure

Day 1 afternoon
  Track C → share deliverables list with Track B and Track A
  Track A → finalize abstract and sammendrag once deliverables confirmed
  Track B → fill Ch 5.2 with Track C's deliverables list
  Track D → refine Ch 7 with Track C's confirmed dynamic layer description

Day 2
  All tracks  → refine and review each other's sections
  Track D     → final QA pass and appendices
  Track B     → references final cleanup

Day 3
  Google Docs assembly by assigned person
  Group read-through
  Final export and page count check (target: ~35 pages excluding appendices and references)
```

---

## Page budget reminder

Stay within approximately 35 pages excluding appendices and references. The key discipline:
- Ch 4 expansion adds ~3–4 pages; trim the existing Scope 1 description slightly to compensate
- Ch 5 rewrite should stay the same total length, just with real content instead of screenshots
- Ch 6 and 7 updates add ~1–2 pages
- New sammendrag adds ~0.5 pages
- Do not add a new Chapter 2.7 unless the page budget clearly allows it — tightening Ch 2.4 is better
