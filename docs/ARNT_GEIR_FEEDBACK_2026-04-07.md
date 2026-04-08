# Arnt / Geir Feedback - 2026-04-07

Context:
- Meeting on Teams with Jonas, Kristian, Nidal, Pheeraphan, Arnt, and Geir.
- Purpose: present the current prototype and get direction for the next presentation and remaining work.

## Main Message

Arnt and Geir are not primarily asking for a perfect or commercial-ready system.
They want the group to show:

- clear technical growth
- a convincing agentic AI concept
- a prototype that demonstrates feasibility
- a stronger story around dynamic dashboards, MCP, and workflow/actionability

The project should therefore be presented as:

- a working prototype
- an architecture for agentic observability
- a concept that can be extended into something more dynamic and intelligent

## What They Liked

- The project direction is interesting and relevant.
- The agentic AI angle is seen as the most exciting part.
- MCP is a strong concept and should be made visible in the presentation.
- The architecture and feasibility matter a lot for how the project is perceived.

## Main Concerns

### 1. Dashboard is not dynamic enough

The current Grafana dashboards do not visibly adapt based on incoming changes in
the way Arnt and Geir imagined when they talked about dynamic dashboards.

What they seem to want:
- stronger evidence that the system reacts to changing conditions
- a more dynamic and agent-driven story around dashboards
- a demo that shows adaptation, not only static visualization

### 2. AI understanding is too sensor-focused

The current LLM / knowledge setup appears to handle sensors better than
applications.

Examples from the feedback:
- the model can answer sensor-oriented questions more easily
- suggested actions are more sensor-oriented than application-oriented
- the solution becomes less interesting if it cannot also reason about apps and
  application health

### 3. The "agentic" part must be clearer

They want the AI-agent aspect to be much more visible in both the prototype and
the presentation.

Important angle:
- not just "we use an LLM"
- but "agents can observe, reason, coordinate work, and drive action/workflow"

## What They Seem To Want Next

### Near-term presentation goal

For the next presentation, the group should aim to show:

- the architecture
- the MCP role in the system
- how the prototype works today
- why the agentic AI approach is valuable
- a believable path toward dynamic dashboards

### Strong concept to explore

A suggested direction from the meeting was a two-agent concept:

- Agent 1: gathers or interprets metrics/data
- Agent 2: proposes or applies dashboard changes based on what Agent 1 found

This does not need to be a full production feature. Even a small, controlled
proof of concept could be valuable for the presentation.

### Possible demo-friendly experiment

The meeting suggested that the group may:

- create a fake dataset or controlled scenario
- let one agent analyze the dataset
- let another agent propose or trigger a dashboard change

The purpose is to demonstrate that the concept is feasible.

## Follow-up Email Clarification

After the meeting, Arnt sent a follow-up note together with a concept sketch.
The most important clarification was:

- the arrows in the sketch indicate who asks whom
- the arrows do not represent a strict one-way technical data flow
- the real data flow may often go both ways

This matters because the sketch should be read as a conceptual interaction map,
not as a final implementation diagram.

### What the sketch seems to add

The sketch makes the intended concept more concrete:

- a user interacts through a web UI
- an orchestrator coordinates tasks and tools
- an MCP client connects to one or more MCP servers
- separate AI agents may have distinct roles
- Grafana is still the dashboard surface, but AI can influence what gets shown
  or generated

The named agent roles in the sketch are especially useful for planning:

- AI agent for dashboard generation
- AI agent for trend analysis

This strengthens the interpretation that they want a clearer multi-step,
agent-coordinated story, not only a single chatbot answering questions.

### Important scope signal from the email

One note in the sketch is especially important:

- the yellow parts are likely too large in delivery scope
- they are included mainly to visualize the idea
- it is acceptable to generate Grafana JSON for manual import instead of
  building full automatic dashboard provisioning

This lowers the implementation bar for the next presentation.

In practice, a convincing proof of concept could be:

- agent reads metrics or a fake scenario through MCP-like inputs
- agent proposes a dashboard layout or update
- system outputs Grafana JSON
- the JSON is shown or manually imported into Grafana

That is enough to demonstrate feasibility without needing a complete end-to-end
dashboard mutation platform.

### What this likely means for tomorrow's task split

The follow-up email makes these work directions even clearer:

1. Orchestrator / workflow concept
- how one component coordinates tools and multiple agents

2. Dashboard-generation proof of concept
- how AI could output a Grafana dashboard or dashboard update

3. Trend-analysis or metrics-analysis agent
- how one agent can interpret inputs before another agent acts on them

4. Presentation clarity
- how to explain that this is a feasible architecture direction, even if the
  current prototype only implements part of it

### Repo note

The follow-up sketch is important for planning and presentation. It is now kept
in the repository at:

- `docs/images/arnt-geir-dynamic-dashboard-concept-2026-04-07.png`

Reference image:

![Arnt/Geir dynamic dashboard concept](images/arnt-geir-dynamic-dashboard-concept-2026-04-07.png)

## What Seems Most Important For The Group

If time is limited, the meeting suggests prioritizing:

1. A strong presentation narrative
2. A clearer agentic AI concept
3. A small but convincing dynamic-dashboard demonstration
4. Better application-level reasoning, if feasible

Not the top priority:
- making the whole platform perfect
- solving every known technical limitation before the presentation

## Suggested Workstreams For Task Planning

These are reasonable work buckets to divide tomorrow:

### 1. Dynamic Dashboard / Agent Concept

Goal:
- explore or prototype one small dynamic dashboard flow

Examples:
- fake dataset -> agent analysis -> suggested dashboard update
- metric change -> agent proposes changed dashboard focus

### 2. AI Knowledge / App Reasoning

Goal:
- make the AI less sensor-only and more application-aware

Examples:
- improve prompts or context
- improve application-related knowledge
- improve suggested actions for application incidents

### 3. Presentation / Storytelling

Goal:
- make the presentation clearly communicate value

Should cover:
- architecture
- MCP
- agentic workflow
- prototype demo
- what is already working
- what the dynamic concept adds

### 4. Demo Reliability

Goal:
- make sure the demo path is stable and easy to show

Examples:
- confirm which flow to demo
- define fallback demo paths
- prepare one "safe" scenario and one "wow" scenario

## Recommended Framing For The Presentation

The project should probably be framed as:

"We have built a working prototype for agentic maritime observability. The
current system already monitors incidents, uses MCP tools, and supports AI-based
analysis. The next step we are now pushing toward is a more dynamic and clearly
agent-driven dashboard workflow."

## Practical Takeaway

A good outcome before the next presentation would be:

- one stable demo flow that already works
- one clear explanation of MCP and architecture
- one visible example of agentic or dynamic behavior, even if limited

## Open Follow-up

- Geir will send a short document with additional improvements/changes.
- The group should use that together with this summary when assigning new tasks.
