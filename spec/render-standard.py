#!/usr/bin/env python3
"""render-standard.py — generate PROJECT-STANDARD.md from project-standard.yaml.

The YAML is the authority; the Markdown is the readable rendering of it. Keeping both by
hand would make this spec its own first doc-rot casualty, so the Markdown is generated and
a check fails when the two disagree.

Modes:
  (no args)   Regenerate PROJECT-STANDARD.md from the YAML.
  --check     Render in memory and compare. Exit 1 with a unified diff on mismatch.
              This is the gate — wire it into any pre-commit or deploy step.

Deliberately emits NO generation timestamp: a clock in the output would make --check fail on
every run and the gate would be turned off within a week. Determinism is the point.
"""

from __future__ import annotations

import argparse
import difflib
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent

# Stdlib only — no PyYAML. See d-stdlib-only-yaml-subset: PyYAML is absent by default on
# macOS and Windows, so depending on it would make "pip install first" the default first-run
# experience on two of three target platforms. riteyaml is proven against PyYAML by
# scripts/test-riteyaml.py, where PyYAML is the oracle rather than a dependency.
sys.path.insert(0, str(HERE.parent / "scripts"))
import riteyaml  # noqa: E402
import ritefs  # noqa: E402

ritefs.use_utf8_stdio()

SPEC = HERE / "project-standard.yaml"
OUT = HERE / "PROJECT-STANDARD.md"

BANNER = (
    "<!-- GENERATED FROM project-standard.yaml BY render-standard.py — DO NOT EDIT.\n"
    "     Edit the YAML, then re-render: spec/render-standard.py\n"
    "     Verify with:                   spec/render-standard.py --check -->"
)


def _s(value) -> str:
    """Collapse a folded YAML scalar to a single clean line."""
    return " ".join(str(value or "").split())


class Doc:
    """Accumulates markdown lines."""

    def __init__(self) -> None:
        self.lines: list[str] = []

    def add(self, text: str = "") -> None:
        self.lines.append(text)

    def render(self) -> str:
        out: list[str] = []
        for line in self.lines:
            # Never emit more than one consecutive blank line.
            if line == "" and out and out[-1] == "":
                continue
            out.append(line)
        return "\n".join(out).rstrip() + "\n"


def _header(d: Doc, spec: dict) -> None:
    meta = spec.get("meta", {})
    d.add(BANNER)
    d.add()
    d.add(f"# {meta.get('title', 'Project standard')}")
    d.add()
    d.add(f"> {_s(meta.get('one_line'))}")
    d.add()
    d.add(
        f"**Version** `{spec.get('schema_version')}` · "
        f"**As of** `{spec.get('as_of')}` · "
        f"**Status** `{spec.get('status')}`"
    )
    d.add()
    d.add("## Why this exists")
    d.add()
    d.add(_s(meta.get("why_this_exists")))
    d.add()
    d.add(f"**Principle.** {_s(meta.get('principle'))}")
    d.add()


def _evidence(d: Doc, spec: dict) -> None:
    ev = spec.get("meta", {}).get("evidence_base")
    if not ev:
        return
    d.add("## Evidence base")
    d.add()
    d.add("| measure | value |")
    d.add("|---|---|")
    for key in ("span", "sessions", "prompts", "log_entries", "projects_with_log", "adrs"):
        if key in ev:
            d.add(f"| {key.replace('_', ' ')} | {ev[key]} |")
    d.add()
    sampled = ev.get("sampled_for_structure") or []
    if sampled:
        d.add(f"Structure sampled from: {', '.join(f'`{p}`' for p in sampled)}.")
        d.add()


def _layers(d: Doc, spec: dict) -> None:
    layers = spec.get("layers", {})
    if not layers:
        return
    d.add("## Two layers")
    d.add()
    for name, text in layers.items():
        d.add(f"- **{name}** — {_s(text)}")
    d.add()
    stages = spec.get("stage_vocabulary", {})
    if stages:
        values = ", ".join(f"`{v}`" for v in stages.get("values", []))
        d.add(f"**Stages.** {values}")
        d.add()
        d.add(f"Tier 1 becomes required at stage `{stages.get('committed_from')}`.")
        d.add()


def _provenance(d: Doc, spec: dict) -> None:
    ph = spec.get("provenance_header")
    if not ph:
        return
    d.add("## Required provenance header")
    d.add()
    d.add(f"Required in {ph.get('required_in')}.")
    d.add()
    d.add("```yaml")
    for key, info in (ph.get("keys") or {}).items():
        if info.get("type") == "enum":
            d.add(f"{key}: {' | '.join(info.get('values', []))}")
        else:
            d.add(f"{key}: \"{info.get('example', info.get('format', ''))}\"")
    d.add("```")
    d.add()
    for key, info in (ph.get("keys") or {}).items():
        d.add(f"- **`{key}`** — {_s(info.get('means'))}")
    d.add()


def _file_format(d: Doc, spec: dict) -> None:
    ff = spec.get("file_format")
    if not ff:
        return
    d.add("## File format")
    d.add()
    d.add(f"**Rule.** {_s(ff.get('rule'))}")
    d.add()
    d.add("| form | provenance header | structure unit | tested by |")
    d.add("|---|---|---|---|")
    for name, info in (ff.get("forms") or {}).items():
        tested = ", ".join(f"`{r}`" for r in info.get("tested_by", []))
        d.add(
            f"| `{name}` | {_s(info.get('provenance'))} "
            f"| {_s(info.get('structure_unit'))} | {tested} |"
        )
    d.add()
    for key in ("measured_basis", "dependency_note"):
        if ff.get(key):
            d.add(_s(ff[key]))
            d.add()


def _portability(d: Doc, spec: dict) -> None:
    port = spec.get("portability")
    if not port:
        return
    d.add("## Portability")
    d.add()
    d.add(f"Targets: {', '.join(f'`{x}`' for x in port.get('targets', []))}")
    d.add()
    if port.get("harness_note"):
        d.add(_s(port["harness_note"]))
        d.add()
    d.add("| rule | severity | what |")
    d.add("|---|---|---|")
    for r in port.get("rules") or []:
        d.add(f"| `{r.get('id')}` | {r.get('severity')} | {_s(r.get('rule'))} |")
    d.add()
    for r in port.get("rules") or []:
        d.add(f"**`{r.get('id')}`** — {_s(r.get('why'))}")
        d.add()
        for key, label in (
            ("note", "Note"),
            ("distinct_from_enrichment", "Not enrichment"),
            ("rejected_alternative", "Rejected alternative"),
        ):
            if r.get(key):
                d.add(f"_{label}: {_s(r[key])}_")
                d.add()


def _verdicts(d: Doc, spec: dict) -> None:
    v = spec.get("verdicts")
    if not v:
        return
    d.add("## Verdicts and failure semantics")
    d.add()
    d.add(f"Vocabulary: {', '.join(f'`{x}`' for x in v.get('vocabulary', []))} · "
          f"sides: {', '.join(f'`{x}`' for x in v.get('sides', []))}")
    d.add()
    d.add(_s(v.get("side_meaning")))
    d.add()
    d.add("| test level | severity | why |")
    d.add("|---|---|---|")
    for lvl, info in (v.get("level_to_severity") or {}).items():
        d.add(f"| `{lvl}` | **{info.get('severity')}** | {_s(info.get('why'))} |")
    d.add()
    for lvl, info in (v.get("level_to_severity") or {}).items():
        if info.get("note"):
            d.add(f"- `{lvl}` — {_s(info['note'])}")
    d.add()
    ep = v.get("exit_policy") or {}
    d.add(f"**Exit policy.** {_s(ep.get('default'))} — `{_s(ep.get('configurable'))}`")
    d.add()
    for k in ("why_yellow_does_not_fail_by_default", "why_it_can_fail_at_all"):
        if ep.get(k):
            d.add(_s(ep[k]))
            d.add()
    if v.get("never_blocks_a_session"):
        d.add(f"**Never blocks a session.** {_s(v['never_blocks_a_session'])}")
        d.add()


def _participation(d: Doc, spec: dict) -> None:
    p_ = spec.get("participation")
    if not p_:
        return
    d.add("## Participation")
    d.add()
    d.add(f"Model `{p_.get('model')}` · marker `{p_.get('marker')}`")
    d.add()
    for k in ("rule", "why_opt_in", "not_an_artifact"):
        if p_.get(k):
            d.add(_s(p_[k]))
            d.add()
    mc = p_.get("marker_contents") or {}
    if mc:
        d.add(f"- minimal: {_s(mc.get('minimal'))}")
        if mc.get("optional_keys"):
            d.add("- optional keys: " + ", ".join(f"`{k}`" for k in mc["optional_keys"]))
        d.add()
    th = p_.get("thresholds") or {}
    if th:
        d.add("### Thresholds")
        d.add()
        d.add(f"**Rule.** {_s(th.get('rule'))}")
        d.add()
        d.add("| overridable | default |")
        d.add("|---|---|")
        for o in th.get("overridable") or []:
            d.add(f"| `{o.get('key')}` | {o.get('default')} |")
        d.add()
        d.add(_s(th.get("why_overridable")))
        d.add()
        if th.get("fixed"):
            d.add("**Fixed, not overridable:** "
                  + ", ".join(f"`{k}`" for k in th["fixed"]))
            d.add()
            d.add(_s(th.get("why_fixed")))
            d.add()
        ons = th.get("overrides_are_never_silent") or {}
        if ons:
            d.add(f"**Overrides are never silent.** {_s(ons.get('rule'))}")
            d.add()
            d.add(_s(ons.get("why")))
            d.add()
        if th.get("disabled_checks_same_rule"):
            d.add(_s(th["disabled_checks_same_rule"]))
            d.add()


def _capabilities(d: Doc, spec: dict) -> None:
    cap = spec.get("capabilities")
    if not cap:
        return
    d.add("## Capabilities")
    d.add()
    for name, info in (cap.get("prerequisite") or {}).items():
        d.add(f"**Prerequisite — `{name}`.** Needed for {_s(info.get('needed_for'))}.")
        d.add()
        if info.get("not_needed_for"):
            d.add(f"_Not needed for: {_s(info['not_needed_for'])}_")
            d.add()
    for name, info in (cap.get("capability_not_prerequisite") or {}).items():
        d.add(f"**Capability, not prerequisite — `{name}`.**")
        d.add()
        if info.get("enables"):
            d.add("- enables: " + ", ".join(f"`{x}`" for x in info["enables"]))
        for key, label in (("when_absent", "when absent"),
                           ("why_not_required", "why not required"),
                           ("expectation_setting", "expectation")):
            if info.get(key):
                d.add(f"- {label}: {_s(info[key])}")
        d.add()
    tiers = cap.get("degradation_tiers") or []
    if tiers:
        d.add("| available | what works |")
        d.add("|---|---|")
        for t_ in tiers:
            d.add(f"| {_s(t_.get('have'))} | {_s(t_.get('works'))} |")
        d.add()
        for t_ in tiers:
            if t_.get("note"):
                d.add(_s(t_["note"]))
                d.add()
    sc = cap.get("setup_check") or {}
    if sc:
        d.add("### The setup check")
        d.add()
        d.add(f"**Purpose.** {_s(sc.get('purpose'))}")
        d.add()
        for r in sc.get("rules") or []:
            d.add(f"**`{r.get('id')}`** — {_s(r.get('rule'))}")
            d.add()
            for key, label in (("why", "Why"), ("instead", "Instead"),
                               ("wording", "Wording")):
                if r.get(key):
                    d.add(f"_{label}: {_s(r[key])}_")
                    d.add()


def _inventory(d: Doc, spec: dict) -> None:
    inv = spec.get("inventory")
    if not inv:
        return
    d.add("## Inventory freeze")
    d.add()
    d.add(
        f"**{inv.get('count')} artifacts, frozen {inv.get('frozen_on')}.** "
        f"{_s(inv.get('scope'))}"
    )
    d.add()
    exc = inv.get("one_exception")
    if exc:
        d.add(f"_Exception — `{exc.get('artifact')}`: {_s(exc.get('why'))}_")
        d.add()
    items = inv.get("deferred_pending_purpose") or []
    if items:
        d.add("| candidate | what | status |")
        d.add("|---|---|---|")
        for i in items:
            d.add(f"| `{i.get('id')}` | {_s(i.get('what'))} | {_s(i.get('status'))} |")
        d.add()
        for i in items:
            if i.get("note"):
                d.add(f"- **`{i.get('id')}`** — {_s(i['note'])}")
        d.add()


def _write_discipline(d: Doc, spec: dict) -> None:
    wd = spec.get("write_discipline")
    if not wd:
        return
    d.add("## Write discipline")
    d.add()
    d.add(f"**Rule.** {_s(wd.get('rule'))}")
    d.add()
    d.add("| value | means | hazard |")
    d.add("|---|---|---|")
    for name, info in (wd.get("values") or {}).items():
        d.add(
            f"| `{name}` | {_s(info.get('means'))} "
            f"| {_s(info.get('hazard')) or '—'} |"
        )
    d.add()
    d.add("| artifact | write discipline |")
    d.add("|---|---|")
    for a in sorted(spec.get("artifacts") or [], key=lambda x: (x.get("tier", 9), x.get("path", ""))):
        d.add(f"| `{a.get('path')}` | `{a.get('write_discipline', '—')}` |")
    d.add()


def _tiers(d: Doc, spec: dict) -> None:
    tiers = spec.get("tiers") or []
    if not tiers:
        return
    d.add("## Tiers")
    d.add()
    d.add("| tier | label | rule | evidence |")
    d.add("|---|---|---|---|")
    for t in tiers:
        d.add(
            f"| {t.get('id')} | {t.get('label')} | {_s(t.get('rule'))} "
            f"| {_s(t.get('evidence')) or '—'} |"
        )
    d.add()


def _artifact(d: Doc, art: dict) -> None:
    d.add(f"### `{art.get('path')}`")
    d.add()
    line = (
        f"**Tier {art.get('tier')}** · layer `{art.get('layer')}` · "
        f"audience `{art.get('audience')}`"
    )
    if art.get("form"):
        line += f" · form `{art['form']}`"
    if art.get("write_discipline"):
        line += f" · write `{art['write_discipline']}`"
    d.add(line)
    d.add()
    d.add(f"**Answers:** {_s(art.get('answers'))}")
    d.add()

    st = art.get("structure") or {}
    if st.get("schema_strictness") or art.get("schema_strictness"):
        d.add(f"_Schema strictness: {art.get('schema_strictness')}._")
        d.add()

    for label, key in (
        ("Required keys", "required_keys"),
        ("Required sections", "required_sections"),
        ("Required — at least one of", "required_any_of"),
        ("Required section — at least one of", "required_any_of_sections"),
        ("Recommended keys", "recommended_keys"),
        ("Recommended sections", "recommended_sections"),
        ("Top-level keys", "top_level_keys"),
    ):
        vals = st.get(key)
        if vals:
            d.add(f"**{label}:** {', '.join(f'`{v}`' for v in vals)}")
            d.add()

    if st.get("canonical_name"):
        d.add(f"**Canonical name:** `{st['canonical_name']}`")
        d.add()

    aliases = st.get("key_aliases") or st.get("section_aliases")
    if aliases:
        unit = "key" if st.get("key_aliases") else "section"
        d.add(f"**Canonical {unit}, and the names it replaces:**")
        d.add()
        for canon, alts in aliases.items():
            d.add(f"- `{canon}` ← {', '.join(f'`{a}`' for a in alts)}")
        d.add()

    entry = st.get("entry")
    if entry:
        d.add("**Entry shape:**")
        d.add()
        for label, key in (
            ("required", "required_keys"),
            ("recommended", "recommended_keys"),
            ("provenance", "provenance_keys"),
            ("lifecycle", "lifecycle_keys"),
        ):
            vals = entry.get(key)
            if vals:
                d.add(f"- _{label}_ — {', '.join(f'`{v}`' for v in vals)}")
        d.add()

    genres = st.get("genres")
    if genres:
        d.add("**Genres:**")
        d.add()
        for g in genres:
            d.add(f"- **`{g.get('id')}`** — {_s(g.get('means'))}")
        d.add()

    fm = st.get("required_frontmatter")
    if fm:
        d.add("**Required frontmatter:**")
        d.add()
        d.add("```yaml")
        for key, val in fm.items():
            d.add(f"{key}: {val}")
        d.add("```")
        d.add()

    for label, key in (
        ("Notes", "notes"),
        ("Expiry rule", "expiry_rule"),
        ("Correction discipline", "correction_discipline"),
        ("Attribution problem", "attribution_problem"),
        ("File order vs timestamp", "file_order_vs_timestamp"),
        ("Cold-restart shape", "if_revisiting_cold_shape"),
    ):
        if st.get(key):
            d.add(f"**{label}.** {_s(st[key])}")
            d.add()

    staging = st.get("staging_area")
    if staging:
        d.add(
            f"**Staging area.** {_s(staging.get('rule'))} "
            f"Canonical path: `{staging.get('canonical_path')}`."
        )
        d.add()

    if st.get("generated_by"):
        d.add(f"**Generated by.** `{st['generated_by']}` — read-only, edits do not propagate back.")
        d.add()

    tests = art.get("tests") or []
    if tests:
        d.add("**Completion tests:**")
        d.add()
        d.add("| level | rule | detail |")
        d.add("|---|---|---|")
        for t in tests:
            detail = _s(t.get("means"))
            if t.get("value") is not None:
                prefix = f"`{t.get('key')}` " if t.get("key") else ""
                detail = f"{prefix}`{t['value']}`" + (f" — {detail}" if detail else "")
            if t.get("patterns"):
                detail = ", ".join(f"`{p}`" for p in t["patterns"])
            # A scoped test is not run everywhere. Saying so in the rendered standard is the
            # point of rendering it at all — a reader must not have to open the YAML to learn
            # that a check is deliberately skipped in some contexts.
            if t.get("scope"):
                marker = f"**{t['scope']}-scoped.**"
                detail = f"{marker} {detail}" if detail else marker
            d.add(f"| {t.get('level')} | `{t.get('rule')}` | {detail or '—'} |")
        d.add()


def _artifacts(d: Doc, spec: dict) -> None:
    arts = spec.get("artifacts") or []
    if not arts:
        return
    d.add("## The artifact set")
    d.add()
    d.add("| tier | path | answers |")
    d.add("|---|---|---|")
    for a in sorted(arts, key=lambda x: (x.get("tier", 9), x.get("path", ""))):
        d.add(f"| {a.get('tier')} | `{a.get('path')}` | {_s(a.get('answers'))} |")
    d.add()
    d.add("## Artifacts in detail")
    d.add()
    for a in sorted(arts, key=lambda x: (x.get("tier", 9), x.get("path", ""))):
        _artifact(d, a)


def _out_of_scope(d: Doc, spec: dict) -> None:
    items = spec.get("out_of_scope") or []
    if not items:
        return
    d.add("## Explicitly out of scope")
    d.add()
    d.add("Named boundaries, so a later session does not re-litigate them.")
    d.add()
    for item in items:
        head = f"**`{item.get('id')}`**"
        if item.get("artifact"):
            head += f" — `{item['artifact']}`"
        if item.get("owner"):
            head += f" (owner: `{item['owner']}`)"
        d.add(head)
        d.add()
        d.add(_s(item.get("why")))
        d.add()
        if item.get("note"):
            d.add(f"_{_s(item['note'])}_")
            d.add()


def _local(d: Doc, spec: dict) -> None:
    local = spec.get("local")
    if not local:
        return
    d.add("## Local layer (configurable — not part of the public standard)")
    d.add()
    d.add(
        "Everything below is this machine's convention. Rite reads it from config; "
        "anyone else overrides or ignores it."
    )
    d.add()
    for key, val in local.items():
        if isinstance(val, dict):
            d.add(f"**`{key}`**")
            d.add()
            for k2, v2 in val.items():
                if isinstance(v2, list):
                    d.add(f"- `{k2}` — {', '.join(f'`{v}`' for v in v2)}")
                else:
                    d.add(f"- `{k2}` — {_s(v2)}")
            d.add()
        else:
            d.add(f"- **`{key}`** — {_s(val)}")
            d.add()


# ─── session protocol ───────────────────────────────────────────────────────
def render_protocol(spec: dict) -> str:
    d = Doc()
    meta = spec.get("meta", {})
    d.add(f"# {meta.get('title', 'Session protocol')}")
    d.add()
    d.add(f"> {_s(meta.get('one_line'))}")
    d.add()
    d.add(
        f"**Version** `{spec.get('schema_version')}` · "
        f"**As of** `{spec.get('as_of')}` · "
        f"**Status** `{spec.get('status')}`"
    )
    d.add()
    d.add("_Generated from `spec/session-protocol.yaml`. Do not edit; run "
          "`spec/render-standard.py --protocol`._")
    d.add()
    for key in ("why_this_exists", "the_measurement"):
        if meta.get(key):
            d.add(_s(meta[key]))
            d.add()

    forced = spec.get("forced_by_the_harness") or []
    if forced:
        d.add("## What forces the shape")
        d.add()
        for f in forced:
            d.add(f"**`{f.get('id')}`** — {_s(f.get('fact'))}")
            d.add()
            d.add(f"{_s(f.get('consequence'))}")
            d.add()
            if f.get("status"):
                d.add(f"_Status: {_s(f['status'])}._")
                d.add()
            if f.get("note"):
                d.add(f"_{_s(f['note'])}_")
                d.add()

    phases = spec.get("phases") or []
    if phases:
        d.add("## Phases")
        d.add()
        d.add("| phase | runs as | needs Python | degrades to |")
        d.add("|---|---|---|---|")
        for ph in phases:
            d.add(
                f"| **{_s(ph.get('label'))}** | `{_s(ph.get('runs_as'))}` "
                f"| {'yes' if ph.get('needs_python') else 'no'} "
                f"| {_s(ph.get('degrades_to')) or '—'} |"
            )
        d.add()
        for ph in phases:
            d.add(f"### {_s(ph.get('label'))}")
            d.add()
            for key, label in (
                ("when", "When"),
                ("constraint", "Constraint"),
                ("must_not", "Must not"),
                ("surface_constraint", "Surface constraint"),
            ):
                if ph.get(key):
                    d.add(f"**{label}.** {_s(ph[key])}")
                    d.add()
            for st in ph.get("steps") or []:
                d.add(f"- **`{st.get('id')}`** — {_s(st.get('what'))}")
                for key, label in (
                    ("means", "Means"),
                    ("why", "Why"),
                    ("do_not", "Do NOT"),
                    ("check", "Check"),
                    ("cost_accepted", "Cost accepted"),
                    ("why_blocked", "Why blocked"),
                    ("freeze_point", "Freeze point"),
                ):
                    if st.get(key):
                        d.add(f"  - _{label}:_ {_s(st[key])}")
                for key, label in (
                    ("detail", "Covers"),
                    ("outcomes", "Outcomes"),
                    ("sides", "Sides"),
                ):
                    if st.get(key):
                        d.add(f"  - _{label}:_ " + ", ".join(f"`{v}`" for v in st[key]))
                if st.get("blocked_by"):
                    d.add(f"  - _Blocked by:_ `{st['blocked_by']}`")
                if st.get("tracked_as"):
                    d.add(f"  - _Tracked as:_ `{st['tracked_as']}`")
            d.add()
            nag = ph.get("nag_policy")
            if nag:
                d.add(f"**Nag policy.** {_s(nag.get('rule'))}")
                d.add()
                d.add(_s(nag.get("why")))
                d.add()
                if nag.get("rejected"):
                    d.add(f"_Rejected: {_s(nag['rejected'])}._")
                    d.add()

    r = spec.get("rulings")
    if r:
        d.add("## Rulings that fixed the shape")
        d.add()
        d.add(f"_{_s(r.get('source'))}_")
        d.add()
        for key in ("skipped_end", "log_cadence"):
            if r.get(key):
                d.add(f"- **`{key}`** — {_s(r[key])}")
        for key in ("minimum_session", "start_frame"):
            v = r.get(key)
            if isinstance(v, dict):
                d.add(f"- **`{key}`** — {_s(v.get('ruling'))}")
                for k2, lab in (
                    ("how_it_stays_bearable", "How it stays bearable"),
                    ("why", "Why"),
                    ("dissent", "Dissent recorded"),
                    ("if_ever_built", "If ever built"),
                ):
                    if v.get(k2):
                        d.add(f"  - _{lab}:_ {_s(v[k2])}")
        d.add()

    tests = spec.get("tests") or []
    if tests:
        d.add("## Completion tests")
        d.add()
        d.add("A protocol with no completion test is not a protocol.")
        d.add()
        d.add("| test | level | checks | implementable today |")
        d.add("|---|---|---|---|")
        for t_ in tests:
            d.add(
                f"| `{t_.get('id')}` | {t_.get('level')} | {_s(t_.get('checks'))} "
                f"| {_s(t_.get('implementable_today'))} |"
            )
        d.add()
        for t_ in tests:
            if t_.get("means"):
                d.add(f"- **`{t_.get('id')}`** — {_s(t_['means'])}")
        d.add()

    limits = spec.get("honest_limits") or []
    if limits:
        d.add("## Honest limits")
        d.add()
        for l in limits:
            d.add(f"- {_s(l)}")
        d.add()
    return d.render()


def render(spec: dict) -> str:
    d = Doc()
    _header(d, spec)
    _evidence(d, spec)
    _layers(d, spec)
    _tiers(d, spec)
    _provenance(d, spec)
    _file_format(d, spec)
    _write_discipline(d, spec)
    _verdicts(d, spec)
    _participation(d, spec)
    _capabilities(d, spec)
    _inventory(d, spec)
    _portability(d, spec)
    _artifacts(d, spec)
    _out_of_scope(d, spec)
    _local(d, spec)
    return d.render()


# ── generated blocks ─────────────────────────────────────────────────────────
# A whole generated file cannot drift; a hand-written one that CONTAINS generated data can.
# README.md is prose a human owns with one table this spec owns, so the table is fenced by
# inert markers and refilled from the YAML. `--blocks --check` is the completion test, and it
# is the reason c-stage-table-duplicated-in-three-places could be retired rather than promised
# away. Targets are declared in `generated_blocks` in the YAML, never here — a path list that
# lives only in code is a hardcoded value with no human-visible home.
ROOT = HERE.parent


def _stage_table_rows(spec: dict) -> list[tuple[str, list[str]]]:
    """(stage, paths it adds) in stage order — exactly what rite-check.py gates on."""
    order = spec.get("stage_vocabulary", {}).get("values", [])
    by_stage: dict[str, list[str]] = {}
    for art in spec.get("artifacts", []):
        stage = art.get("required_from_stage")
        if stage:
            by_stage.setdefault(stage, []).append(_s(art.get("path")))
    return [(s, by_stage[s]) for s in order if s in by_stage]


def _stage_table(spec: dict, target: dict) -> str:
    rows = _stage_table_rows(spec)
    if not rows:
        raise ValueError("no artifact declares required_from_stage")
    style = target.get("style")
    notes = target.get("annotations") or {}

    if style == "md":
        out = ["| stage | what it adds |", "|---|---|"]
        for stage, paths in rows:
            out.append(f"| `{stage}` | " + ", ".join(f"`{p}`" for p in paths) + " |")
        return "\n".join(out)

    if style == "yaml_comment":
        width = max(len(s) for s, _ in rows)
        out = []
        for i, (stage, paths) in enumerate(rows):
            lead = "" if i == 0 else "+ "
            line = f"#   {stage:<{width}}   {lead}" + ", ".join(paths)
            if stage in notes:
                line = f"{line}   {_s(notes[stage])}"
            out.append(line)
        return "\n".join(out)

    raise ValueError(f"unknown block style {style!r}")


def _gate_data(data: dict) -> tuple[list, list]:
    gates = data.get("gates") or []
    return gates, [g for g in gates if g.get("skip_short")]


def _gate_counts(data: dict, target: dict) -> str:
    """The sentence README used to hand-maintain, and got wrong three times in one day.

    The SKIPPED count needs no second source: a gate that declares skip_short is a gate that
    can skip, so both numbers and the reasons all come from .github/gates.yaml.
    """
    gates, skippable = _gate_data(data)
    if not gates:
        raise ValueError("no gates declared")
    ran = len(gates) - len(skippable)
    clauses = ", ".join(
        f"`{_s(g.get('command', [''])[0]).rsplit('/', 1)[-1]}` ({_s(g['skip_short'])})"
        for g in skippable)
    if len(skippable) > 1:
        head, _, tail = clauses.rpartition(", ")
        clauses = f"{head} and {tail}"
    return (
        f"{len(gates)} gates run on every push, across Linux, macOS and Windows. "
        f"{len(skippable)} cannot run on a CI runner — {clauses} — so the runner reports "
        f"**`{ran} of {len(gates)} gates ran`** and names the {len(skippable)} it skipped "
        f"rather than showing an unqualified green."
    )


def _gate_list(data: dict, target: dict) -> str:
    gates, skippable = _gate_data(data)
    skips = {g["id"] for g in skippable}
    out = ["| gate | what it holds | on a runner |", "|---|---|---|"]
    for g in gates:
        gid = _s(g.get("id"))
        mark = "**skips**" if gid in skips else "runs"
        out.append(f"| `{gid}` | {_s(g.get('what'))} | {mark} |")
    return "\n".join(out)


BLOCK_GENERATORS = {
    "stage-table": _stage_table,
    "gate-counts": _gate_counts,
    "gate-list": _gate_list,
}


_SOURCE_CACHE: dict[str, dict] = {}


def _block_source(block: dict, spec: dict) -> dict:
    """The data a block generates FROM.

    Defaults to the standard, which is what every block used until 2026-09-10. The gate blocks
    are fed from .github/gates.yaml instead, because that is the one home for the gate list and
    a generator reaching into the spec for it would recreate the copy it exists to remove.
    """
    rel = block.get("source_file")
    if not rel:
        return spec
    if rel not in _SOURCE_CACHE:
        path = ROOT / rel
        if not path.is_file():
            raise ValueError(f"source_file {rel} does not exist")
        _SOURCE_CACHE[rel] = riteyaml.load(path.read_text(encoding="utf-8"), str(path))
    return _SOURCE_CACHE[rel]


def _block_targets(spec: dict):
    """(block id, block, target dict, open marker, close marker) for every declared target."""
    cfg = spec.get("generated_blocks") or {}
    markers = cfg.get("markers") or {}
    for block in cfg.get("blocks") or []:
        bid = _s(block.get("id"))
        for target in block.get("targets") or []:
            style = target.get("style")
            pair = markers.get(style)
            if not pair or len(pair) != 2:
                raise ValueError(f"{bid}: no marker pair declared for style {style!r}")
            yield bid, block, target, pair[0].replace("{id}", bid), pair[1]


def render_blocks(spec: dict, check: bool) -> int:
    problems: list[str] = []
    changed: list[str] = []
    seen = 0

    for bid, block, target, open_m, close_m in _block_targets(spec):
        rel = _s(target.get("path"))
        path = ROOT / rel
        seen += 1
        if not path.is_file():
            problems.append(f"{rel}: declared as a target for block '{bid}' but does not exist")
            continue

        text = path.read_text(encoding="utf-8")
        i = text.find(open_m)
        j = text.find(close_m, i + len(open_m)) if i != -1 else -1
        if i == -1 or j == -1:
            problems.append(
                f"{rel}: block '{bid}' has no {'opening' if i == -1 else 'closing'} marker. "
                f"Add {open_m!r} ... {close_m!r} around the generated region."
            )
            continue

        body = BLOCK_GENERATORS[bid](_block_source(block, spec), target)
        rebuilt = text[: i + len(open_m)] + "\n" + body + "\n" + text[j:]
        if rebuilt == text:
            continue
        changed.append(rel)
        if check:
            diff = difflib.unified_diff(
                text.splitlines(keepends=True),
                rebuilt.splitlines(keepends=True),
                fromfile=f"{rel} (on disk)",
                tofile=f"{rel} (from {SPEC.name})",
                n=2,
            )
            sys.stdout.writelines(diff)
        else:
            path.write_text(rebuilt, encoding="utf-8", newline="\n")

    if problems:
        for line in problems:
            print(f"FAIL  {line}")
        return 1

    if check:
        if changed:
            print(f"FAIL  {len(changed)} generated block(s) drifted from {SPEC.name}: "
                  + ", ".join(changed))
            print("\nFix: spec/render-standard.py --blocks")
            return 1
        print(f"OK    {seen} generated block(s) match {SPEC.name}")
        return 0

    if changed:
        print(f"wrote {len(changed)} generated block(s): " + ", ".join(changed))
    else:
        print(f"OK    {seen} generated block(s) already match {SPEC.name}")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument(
        "--check",
        action="store_true",
        help="verify PROJECT-STANDARD.md matches the YAML; exit 1 with a diff if not",
    )
    ap.add_argument(
        "--protocol",
        action="store_true",
        help="render the session protocol instead of the project standard",
    )
    ap.add_argument(
        "--blocks",
        action="store_true",
        help="fill the generated blocks inside hand-written files (README, template)",
    )
    args = ap.parse_args()

    global SPEC, OUT, render
    if args.protocol:
        SPEC = HERE / "session-protocol.yaml"
        OUT = HERE / "SESSION-PROTOCOL.md"
        render = render_protocol

    if not SPEC.exists():
        print(f"FAIL  missing authority file: {SPEC}", file=sys.stderr)
        return 1

    try:
        spec = riteyaml.load(SPEC.read_text(encoding="utf-8"), str(SPEC))
    except riteyaml.RiteYamlError as exc:
        print(f"FAIL  {exc}", file=sys.stderr)
        return 1
    if args.blocks:
        return render_blocks(spec, args.check)

    rendered = render(spec)

    if not args.check:
        OUT.write_text(rendered, encoding="utf-8", newline="\n")
        print(f"wrote {OUT.relative_to(HERE.parent)} ({len(rendered.splitlines())} lines)")
        return 0

    if not OUT.exists():
        print(f"FAIL  {OUT.name} does not exist. Run: python spec/render-standard.py")
        return 1

    current = OUT.read_text(encoding="utf-8")
    if current == rendered:
        print(f"OK    {OUT.name} matches {SPEC.name}")
        return 0

    print(f"FAIL  {OUT.name} is out of sync with {SPEC.name}\n")
    diff = difflib.unified_diff(
        current.splitlines(keepends=True),
        rendered.splitlines(keepends=True),
        fromfile=f"{OUT.name} (on disk)",
        tofile=f"{OUT.name} (from {SPEC.name})",
        n=2,
    )
    sys.stdout.writelines(diff)
    print("\nFix: python spec/render-standard.py")
    return 1


if __name__ == "__main__":
    sys.exit(main())
