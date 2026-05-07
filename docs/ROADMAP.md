# Roadmap - Suggested Follow-Up Work

This roadmap lists recommended next steps after the delivered prototype. The
current repository should be treated as a local prototype foundation, not a
production deployment.

## Highest Priority

### Validate With Realistic Operational Use

- Test with continuous operational data instead of only seeded scenarios.
- Validate workflows with operators, NOC/support personnel, or domain experts.
- Compare the prototype workflow against existing incident investigation
  routines.
- Evaluate whether AI-supported explanations improve understanding, trust, or
  response time in practice.

### Production Hardening

- Add proper authentication and authorization for agent and dashboard flows.
- Replace demo credentials and review secret handling.
- Define deployment routines for a target environment.
- Add monitoring, audit logging, backup, and restore procedures.
- Add a migration strategy for database schema changes.

## Prototype Extensions

### Dynamic Dashboard

- Connect dynamic dashboard generation to real incident triggers.
- Expand scenario coverage beyond the current proof-of-concept templates.
- Validate generated dashboard content with representative incidents.
- Decide whether Grafana remains the best interface for highly dynamic views or
  whether a custom incident UI is needed.

### AI and Tool Access

- Evaluate stronger hosted or managed models against the local Ollama setup.
- Add stricter tool permissions and rate limits.
- Consider official MCP protocol support if future host/client infrastructure
  requires it.
- Add automated checks for tool output quality and RAG retrieval relevance.

### Testing

- Add automated integration tests for MCP-style tools and agent routes.
- Add dashboard JSON validation checks.
- Add repeatable dynamic-dashboard trigger tests.
- Keep fresh-stack validation as the baseline end-to-end check.

## Lower Priority

- Make seed scenarios configurable from a file or UI.
- Add more vessel and application types.
- Improve cold-start and model warmup handling.
- Add richer incident timeline views.
- Extend the RAG knowledge base with verified operational procedures.
