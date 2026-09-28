# expert-mentor diagrams

Rendered copies live in [`docs/images/`](images/). Related docs:
[commands](commands.md), [providers](providers.md), [learning](learning.md),
[configuration](configuration.md).

## From field to mentor

What happens between `mentor --field "Rust"` and a live session, and where the
learner's progress is kept afterwards.

![expert-mentor flow](images/diagram-flow.svg)

```mermaid
flowchart LR
    subgraph IN["Learner input"]
        F["--field · --level<br/>--goal · --context<br/>--style · --language"]
        SAVED["saved mentor<br/>mentor run rustbuddy"]
    end

    subgraph BUILD["Prompt builder · expert_mentor.py"]
        PROF["field profile<br/>references/fields.json<br/>concepts · misconceptions · anchors"]
        TPL["templates/<br/>mentor_system_prompt.md<br/>compact_prompt.md"]
        SHAPE["shape_prompt<br/>markdown or XML · compact<br/>for small local models"]
        HIST["learner history<br/>injected when --learner"]
    end

    subgraph EMIT["Emit (no network)"]
        TXT["text / markdown<br/>paste into any chat"]
        JSON["JSON request body"]
        MF["Ollama Modelfile"]
    end

    subgraph RT["Provider adapters · mentor_runtime.py (stdlib urllib, SSE streaming)"]
        A["Claude<br/>Messages API · thinking"]
        O["OpenAI<br/>reasoning effort"]
        G["Gemini"]
        OL["Ollama<br/>localhost:11434"]
        LC["llama.cpp / LM Studio<br/>OpenAI-compatible"]
    end

    SESS["mentor run<br/>interactive session<br/>intake → roadmap → teach/practice → consolidate"]

    subgraph MEM["~/.config/expert-mentor"]
        TR["sessions/&lt;ts&gt;-&lt;name&gt;.md<br/>transcript + metadata"]
        LP["learners/&lt;name&gt;.json<br/>mastered · shaky · misconceptions"]
        CARDS["learners/&lt;name&gt;.cards.json<br/>SM-2-lite schedule"]
    end

    REV["mentor review<br/>strict JSON assessment"]
    QZ["mentor cards --generate<br/>mentor quiz"]

    F --> PROF
    SAVED --> PROF
    PROF --> TPL --> SHAPE
    HIST --> SHAPE
    SHAPE --> TXT & JSON & MF
    SHAPE --> SESS
    SESS <--> A & O & G & OL & LC
    SESS --> TR
    TR --> REV --> LP
    TR --> QZ --> CARDS
    LP -. "--remember" .-> HIST
```

## A `mentor run --remember` session

```mermaid
sequenceDiagram
    autonumber
    actor L as Learner
    participant M as mentor CLI
    participant P as Provider adapter
    participant LLM as Model (cloud or local)
    participant S as ~/.config/expert-mentor

    L->>M: mentor run --field Rust --provider claude --remember
    M->>S: load learners/rust.json
    M->>M: build system prompt + inject learner history
    M->>P: stream(system, messages)
    P->>LLM: HTTPS / localhost request
    LLM-->>P: SSE chunks (text · thinking · usage)
    P-->>L: streamed reply (Phase 1: intake)
    loop teach / practice
        L->>M: answer or exercise attempt
        M->>P: history (last N turns) + new message
        P->>LLM: request
        LLM-->>L: feedback, next step
    end
    L->>M: /quit
    M->>S: save transcript + metadata
    Note over L,S: later, as separate commands
    L->>M: mentor review rust --apply
    M->>P: review prompt (strict JSON)
    P->>LLM: assess latest transcript
    LLM-->>M: mastered · shaky · misconceptions · next lesson
    M->>S: merge into learners/rust.json
```
