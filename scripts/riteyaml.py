"""riteyaml — a deliberately small YAML reader for the subset Rite actually uses.

Stdlib only. This exists so Rite has NO pip dependency: PyYAML is not installed by default
on macOS or Windows, which would make "pip install first" the default experience on two of
three target platforms.

The subset was MEASURED, not guessed, across 1839 lines of this project's own YAML:
no anchors, no aliases, no tags, no flow mappings, no block literals, no merge keys, no
complex keys. What is used: block mappings, block sequences, sequences of mappings, plain /
single-quoted / double-quoted scalars, folded blocks, flow sequences of scalars, comments,
and a leading document marker.

THE CENTRAL RULE: this parser REFUSES rather than guesses. Anything outside the subset raises
RiteYamlError naming the file and line. A hand-rolled parser that silently mis-parses is far
worse than no parser at all, because everything downstream then reasons from a wrong document.

Its correctness claim rests on a differential test against PyYAML, not on this docstring —
see scripts/test-riteyaml.py. If that test cannot be made to pass, the correct response is to
go back to PyYAML, not to weaken the test.
"""

from __future__ import annotations

import re

__all__ = ["load", "RiteYamlError"]


class RiteYamlError(Exception):
    """A construct outside the supported subset, or malformed input."""

    def __init__(self, msg: str, filename: str, lineno: int, line: str = "") -> None:
        where = f"{filename}:{lineno}"
        detail = f"\n    {line.rstrip()}" if line.strip() else ""
        super().__init__(f"{where}: {msg}{detail}")
        self.filename, self.lineno = filename, lineno


# ── constructs we refuse, with the reason the user needs ────────────────────
# Each is a real YAML feature this project does not use. Refusing loudly beats
# implementing something that has never been exercised against a real document.
_REFUSE = (
    (re.compile(r"(?<![\w&])&[A-Za-z_][\w-]*(\s|$)"), "anchors (&name) are not supported"),
    (re.compile(r"(?<![\w*])\*[A-Za-z_][\w-]*(\s|$)"), "aliases (*name) are not supported"),
    (re.compile(r"!!?[A-Za-z_]"), "tags (!!type) are not supported"),
    (re.compile(r"^\s*<<\s*:"), "merge keys (<<:) are not supported"),
    (re.compile(r"^\s*\?\s"), "complex keys (? ) are not supported"),
)

# The unquoted-key alternative must NOT begin with a quote. Without that exclusion,
# `- "Known cost: spoken aloud ..."` is mis-read as key `"Known cost` plus a value — a
# quoted scalar containing a colon silently becomes a mapping. Found by the differential
# test, not by reading the regex.
_KEY = re.compile(
    r"""^(?P<key>"(?:[^"\\]|\\.)*"|'(?:[^']|'')*'|[^\s:#"'][^:#]*?)\s*:(?:\s+(?P<val>.*?))?\s*$"""
)


def _flow_balanced(s: str) -> bool:
    """True when every '[' in s is closed, ignoring brackets inside quotes."""
    depth, quote = 0, None
    for c in s:
        if quote:
            if c == quote:
                quote = None
        elif c in "\"'":
            quote = c
        elif c == "[":
            depth += 1
        elif c == "]":
            depth -= 1
    return depth <= 0


def _strip_comment(s: str) -> str:
    """Remove a trailing comment, ignoring '#' inside quotes."""
    out, quote, i = [], None, 0
    while i < len(s):
        c = s[i]
        if quote:
            out.append(c)
            if c == "\\" and quote == '"' and i + 1 < len(s):
                out.append(s[i + 1])
                i += 2
                continue
            if c == quote:
                quote = None
        elif c in "\"'":
            quote = c
            out.append(c)
        elif c == "#" and (not out or out[-1] in " \t"):
            break
        else:
            out.append(c)
        i += 1
    return "".join(out).rstrip()


_INT = re.compile(r"^[+-]?\d+$")


def _scalar(raw: str, filename: str, lineno: int, line: str):
    """Convert one scalar token to a Python value, matching PyYAML for this subset."""
    s = raw.strip()
    if not s:
        return None
    if s[0] == '"':
        if len(s) < 2 or s[-1] != '"':
            raise RiteYamlError("unterminated double-quoted scalar", filename, lineno, line)
        body = s[1:-1]
        return re.sub(r'\\(.)', lambda m: {"n": "\n", "t": "\t", '"': '"',
                                           "\\": "\\"}.get(m.group(1), m.group(1)), body)
    if s[0] == "'":
        if len(s) < 2 or s[-1] != "'":
            raise RiteYamlError("unterminated single-quoted scalar", filename, lineno, line)
        return s[1:-1].replace("''", "'")
    if s in ("null", "Null", "NULL", "~"):
        return None
    if s in ("true", "True", "TRUE"):
        return True
    if s in ("false", "False", "FALSE"):
        return False
    # YAML 1.1 also reads yes/no/on/off as booleans. This project does not use them, and
    # guessing which way a reader will jump is exactly what this parser refuses to do.
    if s in ("yes", "Yes", "YES", "no", "No", "NO", "on", "On", "ON", "off", "Off", "OFF"):
        raise RiteYamlError(
            f"ambiguous boolean {s!r} — quote it, or use true/false", filename, lineno, line
        )
    if _INT.match(s):
        return int(s)
    if s.startswith("{"):
        raise RiteYamlError("flow mappings ({...}) are not supported", filename, lineno, line)
    if s.startswith("["):
        if not s.endswith("]"):
            raise RiteYamlError("unterminated flow sequence", filename, lineno, line)
        inner = s[1:-1].strip()
        if not inner:
            return []
        return [_scalar(p, filename, lineno, line) for p in _split_flow(inner)]
    return s


def _split_flow(s: str) -> list[str]:
    """Split a flow sequence body on commas that are not inside quotes."""
    parts, buf, quote = [], [], None
    for c in s:
        if quote:
            buf.append(c)
            if c == quote:
                quote = None
        elif c in "\"'":
            quote = c
            buf.append(c)
        elif c == ",":
            parts.append("".join(buf))
            buf = []
        else:
            buf.append(c)
    parts.append("".join(buf))
    return [p.strip() for p in parts if p.strip()]


class _Reader:
    def __init__(self, text: str, filename: str) -> None:
        self.raw = text.splitlines()
        self.filename = filename
        self.i = 0

    # -- line helpers --------------------------------------------------------
    def _indent(self, s: str) -> int:
        return len(s) - len(s.lstrip(" "))

    def _skip(self) -> None:
        """Advance past blank lines, comments, and document markers."""
        while self.i < len(self.raw):
            s = self.raw[self.i].strip()
            if not s or s.startswith("#") or s in ("---", "..."):
                self.i += 1
            else:
                return

    def _check_refused(self, line: str, lineno: int) -> None:
        stripped = _strip_comment(line)
        if '"' in stripped or "'" in stripped:
            # A refused pattern inside a quoted scalar is content, not syntax.
            probe = re.sub(r'"(?:[^"\\]|\\.)*"|\'(?:[^\']|\'\')*\'', "", stripped)
        else:
            probe = stripped
        for rx, why in _REFUSE:
            if rx.search(probe):
                raise RiteYamlError(why, self.filename, lineno, line)
        if re.search(r":\s*\|[-+]?\s*$", probe):
            raise RiteYamlError(
                "block literals (|) are not supported — this project uses folded (>) only",
                self.filename, lineno, line,
            )
        if re.search(r":\s*>[-+]\s*$", probe):
            raise RiteYamlError(
                "folded chomping indicators (>- / >+) are not supported — plain > only",
                self.filename, lineno, line,
            )

    # -- folded scalars ------------------------------------------------------
    def _folded(self, parent_indent: int) -> str:
        """Read a '>' block. Clip chomping: exactly one trailing newline if non-empty."""
        lines: list[tuple[int, str]] = []
        while self.i < len(self.raw):
            line = self.raw[self.i]
            if not line.strip():
                lines.append((-1, ""))
                self.i += 1
                continue
            ind = self._indent(line)
            if ind <= parent_indent:
                break
            lines.append((ind, line.strip()))
            self.i += 1
        while lines and lines[-1][0] == -1:
            lines.pop()
        if not lines:
            return ""
        base = min(ind for ind, _ in lines if ind >= 0)
        out, prev_more = "", False
        for n, (ind, text) in enumerate(lines):
            if ind == -1:
                out += "\n"
                prev_more = False
                continue
            more = ind > base
            if n and not out.endswith("\n"):
                out += "\n" if (more or prev_more) else " "
            out += (" " * (ind - base) + text) if more else text
            prev_more = more
        return out + "\n"

    def _gather_flow(self, first: str) -> str:
        """Join continuation lines until a flow sequence's brackets balance.

        A flow sequence may wrap:
            recommended_sections:
              ["File format", "Language",
               "Append-only", "Vocabulary"]
        """
        text = first
        start = self.i
        while not _flow_balanced(text):
            if self.i >= len(self.raw):
                raise RiteYamlError("unterminated flow sequence",
                                    self.filename, start, first)
            text += " " + _strip_comment(self.raw[self.i].strip())
            self.i += 1
        return text

    # -- structure -----------------------------------------------------------
    def parse(self):
        self._skip()
        if self.i >= len(self.raw):
            return None
        return self._block(self._indent(self.raw[self.i]))

    def _block(self, indent: int):
        self._skip()
        if self.i >= len(self.raw):
            return None
        line = self.raw[self.i]
        if self._indent(line) < indent:
            return None
        body = _strip_comment(line.strip())
        if body.startswith("["):
            # A flow sequence standing alone as a block value, possibly wrapped.
            lineno = self.i + 1
            self.i += 1
            return _scalar(self._gather_flow(body), self.filename, lineno, line)
        return self._seq(indent) if line.strip().startswith("- ") or line.strip() == "-" \
            else self._map(indent)

    def _seq(self, indent: int) -> list:
        items: list = []
        while True:
            self._skip()
            if self.i >= len(self.raw):
                break
            line = self.raw[self.i]
            ind = self._indent(line)
            if ind < indent or not (line.strip().startswith("- ") or line.strip() == "-"):
                break
            if ind > indent:
                raise RiteYamlError("unexpected indentation in sequence",
                                    self.filename, self.i + 1, line)
            lineno = self.i + 1
            self._check_refused(line, lineno)
            rest = _strip_comment(line.strip()[1:].strip())
            self.i += 1
            if not rest:
                items.append(self._block(indent + 1))
                continue
            m = _KEY.match(rest)
            if m:
                # "- key: value" — a mapping whose first key sits on the dash line.
                self.i -= 1
                self.raw[self.i] = " " * (ind + 2) + rest
                items.append(self._map(ind + 2))
                continue
            if rest in (">",):
                items.append(self._folded(ind))
                continue
            items.append(_scalar(rest, self.filename, lineno, line))
        return items

    def _map(self, indent: int) -> dict:
        out: dict = {}
        while True:
            self._skip()
            if self.i >= len(self.raw):
                break
            line = self.raw[self.i]
            ind = self._indent(line)
            if ind < indent:
                break
            if line.strip().startswith("- "):
                break
            if ind > indent:
                raise RiteYamlError("unexpected indentation in mapping",
                                    self.filename, self.i + 1, line)
            lineno = self.i + 1
            self._check_refused(line, lineno)
            body = _strip_comment(line.strip())
            m = _KEY.match(body)
            if not m:
                raise RiteYamlError("expected 'key: value'", self.filename, lineno, line)
            key = _scalar(m.group("key"), self.filename, lineno, line)
            val = m.group("val")
            self.i += 1
            if val is None or val == "":
                nxt = self._peek_indent()
                out[key] = self._block(nxt) if nxt is not None and nxt > indent else None
            elif val.strip() == ">":
                out[key] = self._folded(indent)
            else:
                v = val.strip()
                if v.startswith("[") and not _flow_balanced(v):
                    v = self._gather_flow(v)
                out[key] = _scalar(v, self.filename, lineno, line)
        return out

    def _peek_indent(self):
        j = self.i
        while j < len(self.raw):
            s = self.raw[j].strip()
            if s and not s.startswith("#") and s not in ("---", "..."):
                return self._indent(self.raw[j])
            j += 1
        return None


def load(text: str, filename: str = "<string>"):
    """Parse `text` as the Rite YAML subset. Raises RiteYamlError outside the subset."""
    return _Reader(text, filename).parse()
