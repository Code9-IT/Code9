# Underveisnotater – Tekniske valg og refleksjoner

Dette dokumentet brukes løpende gjennom prosjektet til å notere viktige tekniske
beslutninger, avveininger og tanker som oppstår underveis. Nyttig både for intern
kommunikasjon i gruppen og som kildemateriale til bacheloroppgaven.

---

## LLM-valg: Lokal Ollama vs. Claude API (oppdatert 18.02.2026)

### Bakgrunn

Prosjektet bygger et system for *agentic observability* av maritim telemetri. Et
sentralt spørsmål tidlig i implementeringen var hvilken LLM (Large Language Model)
som skal analysere hendelsene og generere forklaringer til operatøren.

To realistiske alternativer ble vurdert:

---

### Alternativ A: Ollama (lokal, gratis)

**Hva det er:**
Ollama er et verktøy for å kjøre open-source LLM-er lokalt på egen maskin, uten
internettilkobling og uten kostnader. Modeller som `llama3.2:3b` (3 milliarder
parametre) og `llama3.1:8b` støtter *function calling* / tool use – noe som er
nødvendig for en agentic arkitektur.

**Fordeler:**
- Gratis, ingen API-nøkkel nødvendig
- Fungerer offline og lokalt (ingen data sendes ut av nettverket)
- Direkte i tråd med industriveileders (Arnt) ønske om lokal kjøring i første omgang
- Passer godt for en akademisk prototype der kostnader må holdes nede
- Enkelt å sette opp via Docker (Ollama har et offisielt Docker-image)

**Ulemper og svakheter (viktig å dokumentere):**
- Analyse-kvaliteten er merkbart lavere enn hos modeller som Claude eller GPT-4.
  Spesielt på komplekse resonneringsoppgaver vil svarene ofte være overfladiske.
- Hallusinering: open-source modeller i 3B–8B-størrelse har høyere tendens til å
  "dikte opp" fakta eller referanser enn større, finjusterte modeller.
- Norsk språkforståelse er svakere. Llama-modellene er primært trent på engelsk.
  Om systemet skal brukes av norske operatører i en reell setting, er dette en
  betydelig begrensning.
- Tool calling (funksjonskall) er ustabilt i mindre modeller – de kan noen ganger
  glemme å kalle et verktøy, kalle feil verktøy, eller formatere argumentene feil.
- Krever maskin med tilstrekkelig RAM: minimum ~4 GB for `llama3.2:3b`,
  ~8–16 GB for `llama3.1:8b`. Dette kan være en flaskehals på studentmaskiner.

---

### Alternativ B: Claude API (Anthropic)

**Hva det er:**
Anthropics Claude-modeller (f.eks. `claude-haiku-4-5`) tilbys via REST API og
er direkte designet for *agentic tool use* via MCP (Model Context Protocol).
Claude er trent spesifikt på å forstå og bruke verktøy på en pålitelig og
strukturert måte.

**Fordeler:**
- Vesentlig høyere kvalitet på analyser og resonering
- Lavere hallusinasjonsrate – spesielt viktig i en maritim sikkerhetskontekst
- Innebygd MCP-støtte: Claude kan bruke tools via protokollen Onu har implementert
  uten at agenten manuelt håndterer verktøy-løkken
- Bedre norsk forståelse og formulering
- Svært billig for demo-formål: Haiku koster ~$0.003 per analyse (rundt 3 øre)

**Ulemper:**
- Krever internettilgang og Anthropic API-nøkkel
- Koster penger (lite for demo, men et prinsipielt spørsmål for lokal drift)
- Data sendes til Anthropics servere – potensielt problematisk med sensitiv skipsdata
- Avhengig av ekstern tjeneste (downtime-risiko)

---

### Valgt løsning for bachelorprosjektet: Ollama (lokalt)

**Beslutning:** Vi velger Ollama med `llama3.2:3b` eller `llama3.1:8b` for
prototypen. Bakgrunnen er:

1. Industriveilederen (Arnt) ønsker at alt kjøres lokalt i første omgang.
2. Det er et akademisk prosjekt med begrenset budsjett.
3. Arkitekturen vi bygger er identisk uansett LLM-valg – vi bytter bare
   ut en komponent. Det gjør det enkelt å skifte til Claude API senere.

**Viktig:** Dette er ikke en permanent anbefaling for et produksjonssystem.
Se seksjonen "Fremtidspotensial" nedenfor.

---

### Fremtidspotensial: Bytte til Claude API

For en reell produksjonssetting – som det Knowit eventuelt ville deploye for en
maritim operatør – anbefaler vi sterkt å bytte fra Ollama til Claude API
(eller tilsvarende). Begrunnelsene er:

- **Sikkerhetskritisk kontekst:** Maritime operasjoner kan involvere sikkerhet for
  mannskap og last. En modell som hallusinerer er potensielt farlig i dette domenet.
- **Ekte MCP-integrasjon:** Claude er designet for MCP og vil bruke tool-calling
  på en pålitelig og spesifisert måte, mens man med Ollama må håndtere verktøy-løkken
  manuelt og tolerere at modellen av og til formaterer feil.
- **Norsk operatørstøtte:** Norske maritime operatører forventer norsk tekst.
  Claude leverer dette på et høyt nivå.
- **Revisjonsspor og tillit:** Med en kommersiell API-leverandør er det klarere
  ansvarsforhold og SLA (Service Level Agreement) sammenlignet med en lokal modell.

En slik overgang krever minimale kodeendringer siden agentarkitekturen allerede
er designet for utskiftbarhet (én `ollama_client.py` er alt som byttes).

---

## MCP-implementasjon: REST-adapter vs. ekte MCP-protokoll (18.02.2026)

### Hva vi fant

Onu implementerte `services/mcp/` som en **FastAPI REST-adapter** med MCP-inspirerte
verktøydefinisjoner (navn + inputSchema). Dette er ikke den offisielle MCP-protokollen
fra Anthropic, som krever enten `stdio`-transport eller `HTTP+SSE` med JSON-RPC 2.0.

### Konsekvenser

- En ekte MCP-klient (som Claude Desktop) vil ikke kunne koble til denne serveren direkte.
- Ollama snakker heller ikke MCP — den bruker sitt eget API-format for function calling.
- For vår arkitektur fungerer REST-adapteren likevel godt: agenten (FastAPI) kaller
  endepunktene direkte via HTTP og håndterer tool-loopen manuelt.

### Vurdering

For bachelorprototypen er dette akseptabelt. Koden henter korrekte data fra databasen,
er godt strukturert, og demonstrerer konseptet. Terminologien er litt misvisende
("MCP server"), men arkitekturen er solid.

**Hvis man ønsker ekte MCP i fremtiden:**
Bruk `pip install mcp` (Anthropics Python SDK) og implementer en MCP-server med
`stdio`-transport. Da kan Claude Desktop eller Claude API kalle verktøyene direkte
uten at agenten trenger å håndtere loopen manuelt.

---

## Notater som kan brukes i bacheloroppgaven

- Valget mellom lokal og skybasert LLM er en sentral trade-off i agentic AI-systemer.
  Lokal drift gir personvern og kostnadsbesparelser, men på bekostning av kvalitet.
- Hallusinering er en kjent svakhet i LLM-er generelt, og særlig i mindre modeller.
  I sikkerhetskritiske domener (som maritim) bør dette adresseres med tydelig
  *human-in-the-loop*-design der operatøren alltid tar den endelige beslutningen.
- MCP som protokoll er relativt ny (Anthropic, 2024) og har begrenset støtte utenfor
  Anthropic-økosystemet. For open-source LLM-er (Ollama) er en REST-adapter et
  pragmatisk alternativ som gir de samme funksjonelle egenskapene.
- Systemarkitekturen er designet for utskiftbarhet: LLM-en, RAG-implementasjonen og
  tool-adapteren er alle separate komponenter som kan byttes uten å endre resten.
  Dette er god software-arkitektur og er verdt å fremheve i oppgaven.

---

*Dokumentet oppdateres løpende. Datoen i overskriftene markerer når den aktuelle
beslutningen ble tatt.*
