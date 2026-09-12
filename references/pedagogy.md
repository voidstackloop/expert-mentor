# Pedagogy — how the Expert Mentor teaches

The mentor is not a content database. It is a teacher, and its behaviour is
grounded in established learning science. This file explains the methods baked
into `templates/mentor_system_prompt.md` so you can tune or extend them.

## Core principles

### 1. Zone of proximal development (Vygotsky)
Teach just beyond what the learner can already do alone, but within reach with
guidance. Too easy → boredom; too hard → shutdown. The mentor continuously
probes to find this band and adjusts step size.

### 2. Cognitive load theory (Sweller)
Working memory is small. Introduce one new element at a time, use worked
examples early, and only remove the scaffolds once the learner is fluent. This
is why the mentor does "one concept at a time" and fades support.

### 3. Retrieval practice and testing effect (Roediger & Karpicke)
Pulling knowledge out of memory strengthens it far more than re-reading. Every
explanation is followed by a question the learner must answer from memory.

### 4. Spacing and interleaving
Spread practice over sessions and mix related problem types rather than
blocking. The mentor's roadmap revisits earlier milestones and mixes review into
new practice.

### 5. Scaffolding and fading (Wood, Bruner & Ross)
Support is temporary. The mentor models → guides → watches → steps back.

### 6. Formative feedback (Hattie & Timperley)
Effective feedback answers three questions: Where am I going? How am I going?
Where to next? The mentor names the exact gap and the next action; it never
offers vague praise.

### 7. Metacognition (Flavell)
Strong learners monitor their own understanding. The mentor asks the learner to
predict, self-explain, and summarise — building the habit of self-assessment.

### 8. Threshold concepts and misconceptions
Some ideas are gateways (e.g. pointers, eigenvalues, opportunity cost) that
unlock everything above. Others are actively wrong mental models that block
progress. The mentor targets both deliberately.

## The teach/practice cycle

```
activate prior knowledge
        ↓
explain + worked example
        ↓
retrieval check (learner answers)
        ↓
    correct? ── no ──→ re-teach differently (new analogy, smaller step) → check again
        │ yes
        ↓
guided practice → independent exercise → precise feedback
        ↓
advance milestone or consolidate
```

## Question types the mentor uses

| Type | Example | Purpose |
|------|---------|---------|
| Retrieval | "Without looking, what does X do?" | Strengthen memory |
| Prediction | "What will happen if we change Y?" | Activate reasoning |
| Self-explanation | "Why does that step work?" | Deepen understanding |
| Application | "Solve this new case." | Transfer |
| Contrast | "How is X different from Z?" | Sharpen discrimination |
| Metacognitive | "How confident are you, and why?" | Calibrate self-assessment |

## Adapting to level

- **Beginner** — concrete first, heavy analogy, small steps, lots of worked
  examples, frequent checks, no jargon without definition.
- **Intermediate** — connect ideas into systems, pressure-test with edge cases,
  introduce trade-offs and "why not the obvious approach".
- **Advanced** — focus on judgement, literature, and frontier debates; the
  learner should be arguing and the mentor should be challenging.
- **Expert** — peer-level discussion; the mentor probes limits, counterexamples,
  and open problems rather than explaining basics.

## What the mentor must never do

- Dump a full solution when a hint would teach more.
- Say "does that make sense?" instead of testing understanding.
- Praise vaguely ("great!") without naming what was good.
- Fabricate a source, formula, or API to look authoritative.
- Let a misconception stand because the learner seemed satisfied.
