# Field profiles

A **field profile** tells the mentor what professional competence looks like in
a specific field: the concepts, the misconceptions, the authoritative sources,
and the capstone that proves mastery. The generator ships with curated profiles
for a few common fields and falls back to a solid generic profile for everything
else.

## Curated profiles (built in)

- **quantum computing** — `quantum-computing`
- **Rust** — `rust`
- **organic chemistry** — `organic-chemistry`
- **machine learning** — `machine-learning` (also matches "AI")
- **macroeconomics** — `macroeconomics`
- **contract law** — `contract-law`

List them anytime:

```bash
mentor fields
```

## Adding your own

Create `references/fields.json`. The generator merges it over the built-ins at
startup. Keys are arbitrary; each value uses this schema:

```json
{
  "my-field": {
    "key": "the Human-readable field name",
    "aliases": ["my field", "alternate spelling", "abbreviation"],
    "mentor_name": "Dr. Example Name",
    "notes": "A paragraph on what professionalism in this field means: the core reasoning, the standards, the traps, and the canonical anchors.",
    "concepts": ["concept 1", "concept 2"],
    "misconceptions": ["wrong model A", "wrong model B"],
    "resources": ["Author, Title", "standard/body/venue"],
    "capstone": "One realistic project that proves competence."
  }
}
```

### Writing good notes

The `notes` paragraph is the highest-leverage part. A strong profile:

1. Names the field's **foundational reasoning** and demands it first.
2. States the **standards** a professional is held to.
3. Names the **classic traps** learners fall into.
4. Points at **real authorities** (textbooks, standards bodies, journals).

### Matching rules

The resolver checks, in order: exact key / alias match, then substring match,
then falls back to the generic profile. Aliases let one profile cover many
phrasings ("ml", "deep learning", "statistical learning").

## The generic fallback

For fields without a profile, the generator builds notes that force the mentor
to establish vocabulary and models first, then tools and workflows, then applied
judgement — while distinguishing consensus from debate and attacking
misconceptions. This is deliberately field-agnostic but pedagogically strong.
