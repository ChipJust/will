"""Index and search the research corpus across all ecosystem repos.

Solves two problems:
  1. Research is scattered across repos with no cross-repo view.
  2. Research agents re-fetch sources the corpus already holds, wasting tokens
     and money. Agents should search here FIRST, then only fetch the gaps.

Indexes two document kinds, distinguished by directory:
  research/refs/*.md          ingested external sources (papers, transcripts, articles)
  research/agent-reports/*.md synthesized reports produced by research agents

Both carry YAML frontmatter. `refs` frontmatter comes from tools/ingest.py
(title, source_url, ingest_date, ingest_method, quality_score). Agent reports add
type/date/repo/topics/question/key_findings.

Input:  repo scan of D:/_code/* (or --root), no arguments needed
Output: writes will/research-index.md, prints a one-line summary to stdout

Sample:
    $ uv run python tools/research_index.py
    Indexed 47 documents across 4 repos -> D:/_code/will/research-index.md

    $ uv run python tools/research_index.py --search "creatine brain"
    health/research/refs/creatine-cognition-meta-analysis.md
      title: Creatine and cognition: a meta-analysis
      url:   https://pubmed.ncbi.nlm.nih.gov/12345678/
      score: 3 (title, topics)

    $ uv run python tools/research_index.py --has-url "https://www.nature.com/articles/s42255-025-01421-8"
    FOUND health/research/agent-reports/2026-08-22-nad-precursor.md
"""

from __future__ import annotations

import argparse
import io
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path

# Windows cp1252 silently corrupts special characters; force UTF-8 on stdout.
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

DEFAULT_ROOT = Path("D:/_code")
INDEX_PATH = DEFAULT_ROOT / "will" / "research-index.md"
SCAN_DIRS = ("research/refs", "research/agent-reports")
SKIP_REPOS = {"will", "spatium", "vibedaw"}  # no research corpus of this shape

URL_RE = re.compile(r"https?://[^\s<>\"')\]]+")


@dataclass
class Doc:
    """One indexed research document."""

    path: Path
    repo: str
    kind: str  # "ref" or "agent-report"
    title: str = ""
    source_url: str = ""
    date: str = ""
    topics: list[str] = field(default_factory=list)
    question: str = ""
    key_findings: str = ""
    quality_score: str = ""
    urls: set[str] = field(default_factory=set)
    words: int = 0

    @property
    def rel(self) -> str:
        return f"{self.repo}/{self.path.as_posix().split(self.repo + '/', 1)[-1]}"


def parse_frontmatter(text: str) -> tuple[dict[str, str], str]:
    """Split leading YAML frontmatter from body. Returns (fields, body).

    Deliberately minimal: flat key: value pairs and [a, b] lists only. The
    corpus does not use nested YAML, and a real parser is not worth the dep.
    """
    if not text.startswith("---"):
        return {}, text
    end = text.find("\n---", 3)
    if end == -1:
        return {}, text
    raw = text[3:end]
    body = text[end + 4 :]
    fields: dict[str, str] = {}
    for line in raw.splitlines():
        line = line.strip()
        if not line or line.startswith("#") or ":" not in line:
            continue
        key, _, value = line.partition(":")
        fields[key.strip()] = value.strip().strip('"').strip("'")
    return fields, body


def split_list(value: str) -> list[str]:
    """Parse a YAML-ish inline list or comma string into items."""
    value = value.strip().strip("[]")
    return [item.strip().strip('"').strip("'") for item in value.split(",") if item.strip()]


def load_doc(path: Path, repo: str, kind: str) -> Doc:
    text = path.read_text(encoding="utf-8", errors="replace")
    fields, body = parse_frontmatter(text)
    doc = Doc(
        path=path,
        repo=repo,
        kind=kind,
        title=fields.get("title", path.stem.replace("-", " ")),
        source_url=fields.get("source_url", ""),
        date=fields.get("date") or fields.get("ingest_date", ""),
        topics=split_list(fields.get("topics", "")),
        question=fields.get("question", ""),
        key_findings=fields.get("key_findings", ""),
        quality_score=fields.get("quality_score", ""),
        words=len(body.split()),
    )
    doc.urls = set(URL_RE.findall(text))
    if doc.source_url:
        doc.urls.add(doc.source_url)
    return doc


def scan(root: Path) -> list[Doc]:
    docs: list[Doc] = []
    for repo_dir in sorted(p for p in root.iterdir() if p.is_dir()):
        repo = repo_dir.name
        if repo.startswith(".") or repo in SKIP_REPOS:
            continue
        for sub in SCAN_DIRS:
            target = repo_dir / sub
            if not target.is_dir():
                continue
            kind = "ref" if sub.endswith("refs") else "agent-report"
            for md in sorted(target.glob("*.md")):
                docs.append(load_doc(md, repo, kind))
    return docs


def normalize_url(url: str) -> str:
    """Strip scheme, www, trailing slash and tracking params for comparison."""
    url = re.sub(r"^https?://(www\.)?", "", url.strip())
    url = url.split("?")[0].split("#")[0]
    return url.rstrip("/").lower()


def cmd_search(docs: list[Doc], query: str) -> int:
    terms = [t.lower() for t in query.split() if t]
    scored: list[tuple[int, list[str], Doc]] = []
    for doc in docs:
        score = 0
        where: list[str] = []
        haystacks = {
            "title": doc.title.lower(),
            "topics": " ".join(doc.topics).lower(),
            "question": doc.question.lower(),
            "findings": doc.key_findings.lower(),
            "path": doc.path.name.lower(),
        }
        for term in terms:
            for label, hay in haystacks.items():
                if term in hay:
                    score += 3 if label in ("title", "topics") else 1
                    if label not in where:
                        where.append(label)
    # only surface docs matching at least one term
        if score:
            scored.append((score, where, doc))
    if not scored:
        print(f"No local matches for: {query}")
        print("Corpus does not cover this — web research is justified.")
        return 1
    scored.sort(key=lambda row: -row[0])
    for score, where, doc in scored[:20]:
        print(doc.rel)
        print(f"  title: {doc.title}")
        if doc.source_url:
            print(f"  url:   {doc.source_url}")
        if doc.key_findings:
            print(f"  found: {doc.key_findings}")
        print(f"  score: {score} ({', '.join(where)})")
    return 0


def cmd_has_url(docs: list[Doc], url: str) -> int:
    target = normalize_url(url)
    for doc in docs:
        for known in doc.urls:
            if normalize_url(known) == target:
                print(f"FOUND {doc.rel}")
                print(f"  Already in corpus — read it instead of re-fetching.")
                return 0
    print(f"NOT FOUND — {url} is not in the corpus; fetching is justified.")
    return 1


def write_index(docs: list[Doc], index_path: Path) -> None:
    by_repo: dict[str, list[Doc]] = {}
    for doc in docs:
        by_repo.setdefault(doc.repo, []).append(doc)

    lines = [
        "# Research Index",
        "",
        "*Generated by `will/tools/research_index.py`. Do not hand-edit — rerun the tool.*",
        "",
        "**Agents: search this corpus before fetching from the web.**",
        "",
        "```",
        "uv run python D:/_code/will/tools/research_index.py --search \"<topic>\"",
        "uv run python D:/_code/will/tools/research_index.py --has-url \"<url>\"",
        "```",
        "",
        f"{len(docs)} documents across {len(by_repo)} repos.",
        "",
    ]
    for repo in sorted(by_repo):
        repo_docs = by_repo[repo]
        reports = [d for d in repo_docs if d.kind == "agent-report"]
        refs = [d for d in repo_docs if d.kind == "ref"]
        lines.append(f"## {repo} ({len(repo_docs)})")
        lines.append("")
        if reports:
            lines.append("### Agent reports")
            lines.append("")
            for doc in sorted(reports, key=lambda d: d.date, reverse=True):
                lines.append(f"- **{doc.date}** [{doc.title}]({doc.rel})")
                if doc.question:
                    lines.append(f"  - Q: {doc.question}")
                if doc.key_findings:
                    lines.append(f"  - {doc.key_findings}")
                if doc.topics:
                    lines.append(f"  - topics: {', '.join(doc.topics)}")
            lines.append("")
        if refs:
            lines.append("### Ingested sources")
            lines.append("")
            for doc in sorted(refs, key=lambda d: d.title.lower()):
                url = f" — <{doc.source_url}>" if doc.source_url else ""
                lines.append(f"- [{doc.title}]({doc.rel}){url}")
            lines.append("")

    index_path.parent.mkdir(parents=True, exist_ok=True)
    with io.open(index_path, "w", encoding="utf-8", newline="") as handle:
        handle.write("\n".join(lines) + "\n")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("--root", type=Path, default=DEFAULT_ROOT, help="ecosystem root")
    parser.add_argument("--search", metavar="QUERY", help="search the corpus and exit")
    parser.add_argument("--has-url", metavar="URL", help="check if a URL is already held")
    parser.add_argument("--index-path", type=Path, default=INDEX_PATH)
    args = parser.parse_args()

    if not args.root.is_dir():
        print(f"error: root not found: {args.root}", file=sys.stderr)
        return 2

    docs = scan(args.root)

    if args.search:
        return cmd_search(docs, args.search)
    if args.has_url:
        return cmd_has_url(docs, args.has_url)

    write_index(docs, args.index_path)
    repos = len({d.repo for d in docs})
    reports = sum(1 for d in docs if d.kind == "agent-report")
    print(
        f"Indexed {len(docs)} documents ({reports} agent reports) "
        f"across {repos} repos -> {args.index_path.as_posix()}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
