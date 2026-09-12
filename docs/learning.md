# How the mentor teaches

The mentor is not a content database — it is a teacher. Its behaviour is grounded
in established learning science, and it adapts to the learner in real time.

## The teaching contract

Every reply follows these rules (from
[`templates/mentor_system_prompt.md`](../templates/mentor_system_prompt.md)):

1. **Teach, don't dump** — guide with a hint before giving the answer.
2. **One concept at a time** — don't advance until the current idea is solid.
3. **Check understanding** — retrieval questions, not "does that make sense?".
4. **Adapt** — raise difficulty when the learner succeeds; shrink the step when
   they struggle.
5. **Concrete before abstract** — example first, then the principle.
6. **Fade the scaffolds** — do less as the learner gains competence.
7. **Practice over passivity** — every session produces something.
8. **Specific feedback** — name what was right, the exact gap, and the next step.

## Pedagogy

The design draws on:

- **Zone of proximal development** — teach just beyond what the learner can do
  alone, within reach with guidance.
- **Cognitive load theory** — one new element at a time; worked examples early;
  scaffolds removed as fluency grows.
- **Retrieval practice & the testing effect** — pulling knowledge from memory
  strengthens it far more than re-reading.
- **Spacing and interleaving** — revisit and mix, rather than block.
- **Formative feedback** — where am I going, how am I going, where to next.
- **Metacognition** — predict, self-explain, summarise.

Full notes: [`references/pedagogy.md`](../references/pedagogy.md).

## Session flow

```
Phase 1  Intake     — a few questions to find the real starting point
Phase 2  Roadmap    — a short, agreed sequence of milestones
Phase 3  Teach loop — activate → explain + example → check → exercise → feedback
Phase 4  Consolidate— learner summarises, gets one piece of independent practice
```

## The learner model

A learner profile stores what was demonstrated, what was shaky, known
misconceptions, and open questions:

```json
{
  "name": "rust",
  "field": "Rust",
  "level": "intermediate",
  "goal": "ship idiomatic Rust",
  "sessions": 3,
  "mastered": ["ownership"],
  "shaky": ["lifetimes", "borrowing"],
  "misconceptions": ["Rc and Arc are interchangeable"],
  "open_questions": ["when to use Rc vs Box"]
}
```

When history exists, it is injected into the system prompt so the mentor stops
re-teaching what you know and deliberately revisits what is weak.

## Progress review

`mentor review` asks the model to assess the latest transcript and return strict
JSON: mastered / shaky / misconceptions / open questions / level / next lesson.
It merges the result into the profile, promoting anything newly mastered out of
*shaky*. Nothing is invented — items require evidence from the transcript.

```bash
mentor review rust            # show proposed changes
mentor review rust --apply    # save them
mentor review rust --dry-run  # show the review prompt, call nothing
```

## Spaced repetition

`mentor cards --generate` turns a session into flashcards; `mentor quiz` reviews
due cards with an **SM-2-lite** scheduler. Each card tracks an interval (days),
ease factor, repetition count, and due date. Grades:

| Grade | Effect |
|-------|--------|
| `again` | relearn in ~10 minutes; ease down |
| `hard` | shorter next interval; small ease penalty |
| `good` | standard interval growth |
| `easy` | longer interval; ease up |

## Grounding and honesty

The mentor distinguishes established fact, expert consensus, opinion, and
uncertainty; never invents sources; and for health, law, finance, or safety,
frames guidance as educational and flags when a licensed professional is
required.
