# Context Architecture — Linked Nodes

How knowledge is structured across this ecosystem so that agents can work efficiently
without loading everything into context.

---

## The pattern

Knowledge is organized as **linked nodes** — small, addressable, self-contained files
connected by explicit references from indexes and other nodes. Agents compose their
working context by navigating links, not by pre-loading the corpus.

This is hypertext for agents. The references inside our markdown, YAML, and CSV files
function as a lightweight **context scripting language**: they tell the agent what to
load, when, and how it relates to other knowledge. We don't have a formal DSL — paths
and markdown links are the syntax — but the pattern is deliberate.

## Why this matters

- **Token efficient.** An agent opening `HANDOFF.md` gets the situation summary and
  pointers — not the full corpus. Individual nodes load only when the task needs them.
- **Scales.** A repo with thousands of research refs doesn't overwhelm context because
  nodes are addressable. Only the relevant ones get loaded.
- **Modular.** Updating a node doesn't require rewriting indexes unless its name or
  topic changes.
- **Addressable.** Handoffs and reflections can cite exactly what to load for a given
  task, not "read everything and figure it out."

## Structural elements

**Nodes** — small, topically focused files. One thing each.
- Each memory file is a node (one principle or fact)
- Each research article markdown is a node
- Each research thread (liquidation-plan.md, tax-strategy.md) is a node
- Each tool is a node (one tool, one purpose)
- Each account entry in `accounts.yaml` is a sub-node

**Indexes** — discovery layer, topic → node.
- `MEMORY.md` indexes memory files (one-line descriptions)
- `HANDOFF.md` summarizes current state with pointers to details
- `ORIENTATION.md` indexes the directory structure
- `predictions.csv` indexes research signals by ticker → article slug
- `CLAUDE.md` indexes the conventions an agent in this repo should know

**Links** — references that direct an agent to load a node.
- Markdown paths: `data/accounts.yaml`
- Markdown links: `[title](path.md)`
- YAML frontmatter: `source_file: docs/alluvial-gold/...`
- CSV cross-references: `article_slug` in predictions.csv → article markdown

## Rules for nodes

1. **One topic per file.** Two distinct concerns → split.
2. **Lean frontmatter, substantive body.** Frontmatter is addressable metadata
   (name, description, date, tickers). Body is content. Don't stuff signals into
   frontmatter because they're structured — put them in a purpose-built index.
3. **Self-contained enough to make sense alone.** A node should not require reading
   five others to be understood.
4. **Addressable via stable paths.** Once a node exists at a path, don't move it
   without updating references.

## Rules for indexes

1. **One line per entry.** Indexes are for discovery, not content.
2. **Include a hook** that tells the agent whether to load the node.
3. **Update the index when a node's name or topic changes**, not when its content changes.
4. **Stay under the token limit of your reader.** `MEMORY.md` is always in context —
   keep it under ~200 lines.

## Rules for links

1. **Relative paths** within a repo.
2. **Absolute paths** (or `repo:path`) for cross-repo references.
3. **Enough context at the link site** that the agent knows whether to follow it.
   "See predictions.csv" is worse than "See predictions.csv to look up Taylor Dart's
   current view on RGLD."

## Examples in this ecosystem

| Index | Nodes |
|-------|-------|
| `MEMORY.md` | `feedback_*.md`, `user_*.md`, `project_*.md` |
| `will/HANDOFF.md` | repo-specific `HANDOFF.md` → reflections → memory |
| `money/HANDOFF.md` | `predictions.csv` → article markdown |
| `money/ORIENTATION.md` | `tools/`, `data/`, `research/` |
| `predictions.csv` | `research/refs/YYYY-MM-DD-*.md` |

## When to create new structure

- **New node:** when a topic is substantial and addressable enough to reference on its own
- **New index:** when you're looking up the same thing by a key (ticker, date, topic)
  more than a few times and scrolling a list has become painful
- **New link:** whenever a node references another node's content

Apply YAGNI. Don't create structure before it's earned. Once three examples of the
same linking pattern exist, consider formalizing an index.

## Watch for

The references in our files are a **lightweight context scripting language**. An
agent resolves them at read-time to compose working context. If this evolves — if we
end up wanting explicit load directives, context macros, or typed references — that's
a signal we've outgrown implicit paths and should design a real DSL. Not now. For now,
paths and markdown links are sufficient; the pattern is the point.
