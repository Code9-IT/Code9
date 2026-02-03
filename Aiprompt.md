# PromptForNextAI

**Formål:** Dette dokumentet er en ferdig prompt som kan gis til en annen AI for å lage et helt nytt start‑prosjekt (fra scratch) for bachelorprosjektet vårt. AI-en skal lage **grunnleggende struktur og minimumskode**, men **ikke bygge alt ferdig**. Vi ønsker et solid startpunkt slik at alle fire i gruppa kan kode videre hver for seg uten mye merge‑konflikter.

---

## Introduksjon / bakgrunn (les før prompt)

Dette prosjektet er en bacheloroppgave i samarbeid med **Knowit Sørlandet**, forankret i maritim telemetri (Telenor Maritime / Color Line‑kontekst). Prosjektet ble endret fra «lage dashboard» til **agentic observability**: et nytt lag i teknologistacken hvor en AI‑agent tolker hendelser, forklarer årsak og foreslår tiltak. Vi har fått klar beskjed om:

- **Bygg minimum som fungerer først**, utvid senere (ikke overlov).
- **Python er valgt språk** i ny oppstart (C# er ikke aktuelt nå).
- Lokal utvikling er ok (Ollama lokalt). Sky/GPU kan vurderes senere.
- Vi skal lage **to dashboards** for to roller:
  1) Skipsoperasjon (kaptein/operativt personell)
  2) Data‑kvalitet / data‑integritet (data‑trust/overvåkning av dataplattform)
- Ikke dykk dypt i «tags» (det er enormt og kaotisk i maritime systemer). Bruk få, generiske sensornavn (engine_temp, oil_pressure, osv.).
- **Human‑in‑the‑loop** må frem: en alarm -> noen tar handling.
- Vi kan bruke ekte skipsdata internt når vi får det, men **ikke avsløre hvilket skip** i dokumentasjon/demonstrasjon.

Målet er å gi en **AI‑modell en klar og detaljert start‑prompt** slik at den kan lage en ryddig prosjektstruktur, minimalkode og en fungerende «demo‑pipeline». Vi ønsker bevisst et **starter kit** (ikke ferdig produkt) slik at alle fire i gruppa kan implementere videre i egne filer.

---

## PROMPT (kopiér fra her og gi til neste AI)

Du er en senior full‑stack ingeniør. Lag et **nytt repo fra scratch** for en bachelor‑prototype: **agentic observability for maritime telemetry**. Målet er å få et **minimalt, kjørbart startpunkt**, ikke en full løsning.

### 1) Kontekst og visjon
- Vi bygger en prototype i samarbeid med Knowit.
- Fokus: *agentic observability* (AI‑agent som forklarer hendelser og foreslår tiltak).
- Data er **tidsseriedata** fra skip (vi får testdata senere; nå bruker vi syntetisk data).
- Arkitektur (forenklet):
  - Telemetri / event‑data -> database -> Grafana dashboard
  - Event -> agent -> (RAG‑kontekst) -> LLM -> svar tilbake til Grafana
- Løsningen skal være enkel, men vise flyt og konsept.

### 2) Viktige føringer fra veiledermøte
- **Bygg minimum som fungerer først**. Utvid senere.
- Lokal utvikling er ok. Sky/GPU kan vurderes senere.
- **Python er eneste språk** i denne oppstarten.
- Vi skal lage **to dashboards** for to roller:
  1) Skipsoperasjon (kaptein/operativt personell)
  2) Data‑kvalitet / dataintegritet (data‑trust)
- Unngå å bli fanget i «tags». Bruk få, generiske feltnavn.
- Fokuser på agent‑laget i arkitekturen (det «nye laget» i stacken).
- Få frem **human‑in‑the‑loop**: event -> menneskelig handling.

### 3) Leveranse fra AI (det du skal lage)
Lag en full repo‑struktur med:
- docker‑compose (TimescaleDB + Grafana + agent + generator + evt. Ollama)
- DB‑schema (telemetry, events, ai_analyses)
- Grafana provisioning (datasource + 2 dashboards, minimale paneler)
- Agent‑service (API) med **stubbede / minimale endepunkter**
- Enkel generator som skriver syntetiske data + events
- RAG‑stub (tom funksjon, returnerer tom liste, men tydelig interface)
- README med quick‑start (5–10 min)

**Viktig:** Ikke bygg alt ferdig. Sett inn TODOer og kommentarer, slik at hver student kan implementere sin del videre.

### 4) Teknologi (fast krav)
- Docker + docker‑compose
- TimescaleDB (Postgres)
- Grafana
- **Python** (FastAPI anbefales) for agent
- Python‑basert generator
- Ollama (valgfritt i MVP, men forbered integrasjon)
- RAG = stub

### 5) Minimal dataflyt som MÅ fungere
1) Generator skriver rader til telemetry (og noen events)
2) Grafana viser live data
3) Event log viser events
4) Agent kan analysere et event (selv om svaret er dummy)
5) AI‑insight lagres i ai_analyses og vises i Grafana

### 6) Praktiske detaljer
- Alle konfiger via .env
- Lag simple testdata (2 vessels)
- Ha jevnlige anomalies for demo
- Ikke avanserte auth
- Alt skal kjøre lokalt
- Husk at ekte skipsdata kan brukes internt senere, men anonymiser i demo/rapport

### 7) Repo‑struktur (forslag)
Lag en struktur som gjør at 4 personer kan jobbe parallelt:

```
project-root/
├── docker-compose.yml
├── .env.example
├── README.md
├── db/
│   └── init/001_init.sql
├── grafana/
│   ├── dashboards/
│   └── provisioning/
├── services/
│   ├── agent/        # Python API
│   └── generator/    # Python generator
├── rag/
│   └── (stubs)
├── docs/
│   └── architecture.md
└── scripts/
```

### 8) Ekstra (nice‑to‑have, ikke krav)
- En «Analyze» link i Event Log (Grafana) som kaller agenten
- En enkel HTML‑visning av AI‑analyse (bedre enn rå JSON)

### 9) Husk
- Dette er et **starter kit**, ikke ferdig produkt.
- Kommenter hva som er stub og hva som er ferdig.
- Bruk TODO‑markører slik at vi kan fordele arbeid mellom 4 personer uten konflikt.

### 10) Output‑format
- Lag filene fysisk (full repo)
- Svar med fil‑tre og innhold
- Ikke bruk masse generert dummy‑kode; hold det minimalt

---

**Dette er alt du trenger å vite. Start prosjektet fra bunnen av og gi oss et rent, kjørbart startpunkt.**

## SLUTT PÅ PROMPT
