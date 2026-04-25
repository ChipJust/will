# Docs as Inputs, Graph as Overlay

An architectural principle for any repo that ingests third-party content and
wants to annotate it.

**See also:** `context-architecture.md` for the linked-node pattern. This
principle is a specialization that covers what to do when the linked nodes
are content we don't own.

---

## The principle

When the agent system ingests external content (PDFs, articles, transcripts,
research papers) and wants to add knowledge on top — tagging, linking,
classifying, citing — annotations live in a separate graph layer, not in the
source docs.

- **Source content is immutable.** Docs go in, docs stay raw.
- **Annotations are an overlay.** A graph store (or equivalent) holds nodes
  for source spans, concepts, themes, tickers, etc., and edges between them.
- **Source updates may trigger graph re-extraction.** A new revision of a
  source doc may invalidate edges that pointed into it.
- **Graph updates never modify source.** Adding an annotation, fixing a tag,
  or rerunning a classifier does not touch the underlying file.

## Why

- **Decouples source-world from agent-world.** Third-party content has its
  own lifecycle (revisions, takedowns, format changes). Agent annotations
  have a different lifecycle (skill versions, classifier reruns, schema
  evolution). Coupling them through in-place edits hurts both ends.
- **Reproducible re-extraction.** If a skill changes, rerun it against the
  unchanged source corpus and diff the resulting edges. With anchors injected
  into the docs, you'd be diffing edits-of-edits.
- **No merge conflicts on shared sources.** Multiple skills can annotate the
  same span without stepping on each other.
- **Clean ingest contract.** The ingest tool extracts and stores. It never
  has to know about downstream annotation.

## How — span pointers

The interesting design problem is how to point into source content stably
without modifying it. A span tuple with redundant pointers handles this:

```json
{
  "doc_id": "...",
  "char_start": N,
  "char_end": M,
  "text_hash": "sha256:...",
  "text_prefix": "first 80 chars of the span",
  "heading_context": "computed at citation time"
}
```

- **Offsets** are the fast path for retrieving the span text.
- **Hash** is the integrity check — if the doc changed, hashes won't match.
- **Prefix** is the recovery path — if offsets shifted (doc edited), the
  prefix fuzzy-relocates the span.
- **Heading context** is computed at citation time by walking backward
  through the doc to the nearest heading. It isn't stored as an anchor in
  the doc itself.

This is graceful degradation: fast path → integrity check → recovery path.

## When this applies

- Any repo with a `research/refs/` corpus plus a structured way to talk
  about what's in it (predictions, theses, conditions, supplements, themes)
- Any time multiple skills/agents will annotate the same source over time
- Any case where the source corpus updates independently of your annotations

If the only annotation is "I read this and took notes" and the notes are
themselves the artifact, no graph overlay is needed — that's just notes.

## Examples in this ecosystem

- **money:** `research/refs/` (Taylor Dart articles, Bravos report) +
  `graph/nodes.json` + `graph/edges.json` overlay. Concept-skills emit edges;
  docs are never modified. See money's HANDOFF.md and
  `research/concept-skill-prototype.md`.
- **health (future):** the same pattern applies to research refs annotated
  with conditions, supplements, mechanisms. Concept-skills graduating from
  money would slot directly into this.

## Anti-patterns

- **Don't inject anchors into source docs** to make them easier to point at.
  Compute the anchor (heading context, paragraph index) at citation time.
- **Don't store annotations in source frontmatter.** Frontmatter is for
  ingest metadata (title, source_url, ingest_date), not for downstream
  classifications.
- **Don't normalize source content for skill convenience.** If a skill is
  fragile to formatting variation, fix the skill, not the corpus.
