"""riteyaml — a deliberately small YAML reader for the subset Rite actually uses.

Stdlib only. This exists so Rite has NO pip dependency: PyYAML is not installed by default
on macOS or Windows, which would make "pip install first" the default experience on two of
three target platforms.

The subset was MEASURED, not guessed, across 1839 lines of this project's own YAML:
no anchors, no aliases, no tags, no flow mappings, no block literals, no merge keys, no
complex keys. What is used: block mappings, block sequences, sequences of mappings, plain /
single-quoted / double-quoted scalars, folded blocks, flow sequences of scalars, comments,
and a leading document marker.

THE CENTRAL RULE: this parser REFUSES rather than guesses. A hand-rolled parser that silently
mis-parses is far worse than no parser at all, because everything downstream then reasons from a
wrong document.

IT REFUSES IN TWO KINDS, and the distinction is a verdict rather than a detail. YamlInvalid means
the text is not YAML — the project's defect. YamlUnsupported means valid YAML using a construct
outside the declared subset — Rite's limit, declared in the standard under `yaml_subset`. Both
name the file, the line and a stable `construct` id. The split arrived on 2026-09-12, when Rite
began checking every YAML file a project carries instead of only its own artifacts: calling
someone's working docker-compose broken because it uses an anchor would be a wrong answer.

THE SUBSET WAS RE-MEASURED on 2026-09-11 against all 478 YAML files on this machine, with PyYAML
as oracle. It found twelve files this parser ACCEPTED that PyYAML rejects — ten of them a plain
scalar containing ": " — and six it refused that PyYAML accepts. Both directions are fixed here,
and both are now cases in the differential test.

Its correctness claim rests on a differential test against PyYAML, not on this docstring —
see scripts/test-riteyaml.py. If that test cannot be made to pass, the correct response is to
go back to PyYAML, not to weaken the test.
"""

from __future__ import annotations

import re

__all__ = ["load", "RiteYamlError", "YamlInvalid", "YamlUnsupported"]


class RiteYamlError(Exception):
    """Base class. Never raised directly — every refusal declares which KIND it is.

    TWO KINDS, AND THE DIFFERENCE IS A VERDICT. `invalid` means the text is not YAML: the
    project's defect, and RED. `unsupported` means valid YAML using a construct outside the
    subset the standard declares: a conformance note, and YELLOW. One class carrying both is
    what left the checker unable to tell "your file is broken" from "Rite cannot read this" —
    tolerable while only Rite's own artifacts were parsed, and wrong the moment every YAML file
    in a project is.

    `construct` is a stable id. spec/project-standard.yaml declares each one under `yaml_subset`
    and scripts/test-riteyaml.py asserts the two lists are equal, so a refusal can be looked up
    instead of guessed at.
    """

    kind = "invalid"

    def __init__(self, msg: str, filename: str, lineno: int, line: str = "",
                 construct: str = "syntax") -> None:
        where = f"{filename}:{lineno}"
        detail = f"\n    {line.rstrip()}" if line.strip() else ""
        super().__init__(f"{where}: {msg}{detail}")
        self.filename, self.lineno = filename, lineno
        self.construct, self.reason = construct, msg


class YamlInvalid(RiteYamlError):
    """Not YAML at all. PyYAML rejects every case of this in the differential test."""

    kind = "invalid"


class YamlUnsupported(RiteYamlError):
    """Valid YAML outside the declared subset. PyYAML ACCEPTS it; Rite refuses to guess."""

    kind = "unsupported"


# ── constructs refused on a whole line ──────────────────────────────────────
# Only two are line-shaped, and both are STRUCTURE rather than a value. Anchors, aliases and
# tags moved into _scalar on 2026-09-12: an indicator opens a node only at the START of one, so
# `a: see &ref here` and `a: x *y z` are valid YAML that this table refused. Measured against
# PyYAML, which accepts both. A pattern matching anywhere on the line cannot tell an indicator
# from prose.
_REFUSE_LINE = (
    (re.compile(r"^\s*<<\s*:"), "merge keys (<<:) are not supported", "merge_key"),
    (re.compile(r"^\s*\?\s"), "complex keys (? ) are not supported", "complex_key"),
)

# Indicators at the start of a node. Everything here except an anchor or a tag is INVALID rather
# than unsupported — YAML forbids these characters from starting a plain scalar, and the oracle
# agrees on every one.
_ANCHOR = re.compile(r"^&[A-Za-z_][\w-]*(\s|$)")
_ALIAS = re.compile(r"^\*[A-Za-z_][\w-]*$")
_RESERVED = "@`%"

# A plain scalar may not contain ": " or end in ":" — YAML reads that as a mapping. TEN of the
# twelve false accepts measured on 2026-09-11 were this one construct, read as text.
_PLAIN_MAPPING_VALUE = re.compile(r":(\s|$)")

# A tab can never indent a line. Measured: PyYAML rejects a tab in indentation, after a space,
# and in a plain continuation line — while riteyaml accepted all three AND mis-structured the
# document, which is the worse half.
_TAB_INDENT = re.compile(r"^[ ]*\t")

_QUOTE_NAME = {'"': "double", "'": "single"}

# The unquoted-key alternative must NOT begin with a quote. Without that exclusion,
# `- "Known cost: spoken aloud ..."` is mis-read as key `"Known cost` plus a value — a
# quoted scalar containing a colon silently becomes a mapping. Found by the differential
# test, not by reading the regex.
_KEY = re.compile(
    r"""^(?P<key>"(?:[^"\\]|\\.)*"|'(?:[^']|'')*'|[^\s:#"'][^:#]*?)\s*:(?:\s+(?P<val>.*?))?\s*$"""
)


_FLOAT = re.compile(r"^[-+]?(?:\d+\.\d*|\.\d+|\d+(?=[eE]))(?:[eE][-+]?\d+)?$")


def _flow_balanced(s: str) -> bool:
    """True when every '[' and '{' in s is closed, ignoring brackets inside quotes."""
    depth, quote = 0, None
    for c in s:
        if quote:
            if c == quote:
                quote = None
        elif c in "\"'":
            quote = c
        elif c in "[{":
            depth += 1
        elif c in "]}":
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


def _quote_end(s: str, quote: str, start: int = 1) -> int | None:
    """Index of the quote CLOSING a scalar opened with `quote`, or None if it is still open.

    Two escape forms and no others: inside double quotes a backslash escapes the next character,
    and inside single quotes '' is one literal quote. Scanning for the closing quote rather than
    testing the last character is what makes `"a\\""` and `'it''s'` read correctly — and what
    lets a multi-line scalar be recognised as open rather than malformed.
    """
    i = start
    while i < len(s):
        c = s[i]
        if quote == '"' and c == "\\":
            i += 2
            continue
        if c == quote:
            if quote == "'" and s[i + 1:i + 2] == "'":
                i += 2
                continue
            return i
        i += 1
    return None


def _ends_with_escape(body: str) -> bool:
    """Does `body` end in an ODD number of backslashes, so the line break is escaped?

    Even means the backslashes escape each other and the break still folds. `"one\\\\` + break
    is a literal backslash followed by a folded space; `"one\\` + break is neither.
    """
    n = len(body) - len(body.rstrip("\\"))
    return n % 2 == 1


def _quoted(s: str, filename: str, lineno: int, line: str) -> str:
    """Unescape a complete quoted token. Multi-line ones arrive already folded."""
    quote = s[0]
    end = _quote_end(s, quote)
    if end is None:
        raise YamlInvalid(f"unterminated {_QUOTE_NAME[quote]}-quoted scalar",
                          filename, lineno, line, "unterminated_quote")
    if s[end + 1:].strip():
        raise YamlInvalid("text after a closing quote", filename, lineno, line,
                          "text_after_quote")
    body = s[1:end]
    if quote == '"':
        return re.sub(r'\\(.)', lambda m: {"n": "\n", "t": "\t", '"': '"',
                                           "\\": "\\"}.get(m.group(1), m.group(1)), body)
    return body.replace("''", "'")


def _scalar(raw: str, filename: str, lineno: int, line: str, flow: bool = False):
    """Convert one scalar token to a Python value, matching PyYAML for this subset.

    `flow` says the token came from inside [] or {}, where a colon binds a pair instead of
    ending a key — so the plain-scalar check does not apply there.
    """
    s = raw.strip()
    if not s:
        return None
    if s[0] in "\"'":
        return _quoted(s, filename, lineno, line)
    # ── indicators, which mean something only at the START of a node ──────────
    if s[0] == "!":
        raise YamlUnsupported("tags (!type) are not supported", filename, lineno, line, "tag")
    if s[0] == "&":
        if _ANCHOR.match(s):
            raise YamlUnsupported("anchors (&name) are not supported",
                                  filename, lineno, line, "anchor")
        raise YamlInvalid("'&' opens an anchor and needs a name",
                          filename, lineno, line, "reserved_indicator")
    if s[0] == "*":
        if _ALIAS.match(s):
            # Anchors are refused on sight, so reaching an alias means no anchor was ever
            # defined: it is unresolvable, not merely unsupported. PyYAML says the same —
            # "found undefined alias".
            raise YamlInvalid(f"alias {s} refers to an anchor that is not defined",
                              filename, lineno, line, "undefined_alias")
        raise YamlInvalid("'*' opens an alias and needs a name",
                          filename, lineno, line, "reserved_indicator")
    if s[0] in _RESERVED:
        raise YamlInvalid(f"{s[0]!r} cannot start a plain scalar — quote it",
                          filename, lineno, line, "reserved_indicator")
    if s in ("null", "Null", "NULL", "~"):
        return None
    if s in ("true", "True", "TRUE"):
        return True
    if s in ("false", "False", "FALSE"):
        return False
    # YAML 1.1 also reads yes/no/on/off as booleans. This project does not use them, and
    # guessing which way a reader will jump is exactly what this parser refuses to do.
    if s in ("yes", "Yes", "YES", "no", "No", "NO", "on", "On", "ON", "off", "Off", "OFF"):
        raise YamlUnsupported(
            f"ambiguous boolean {s!r} — quote it, or use true/false", filename, lineno, line,
            "ambiguous_boolean",
        )
    if _INT.match(s):
        return int(s)
    if _FLOAT.match(s):
        return float(s)
    if s.startswith("{"):
        if not s.endswith("}"):
            raise YamlInvalid("unterminated flow mapping", filename, lineno, line,
                              "unterminated_flow")
        inner = s[1:-1].strip()
        if not inner:
            return {}
        out = {}
        for part in _split_flow(inner):
            try:
                k, v = _split_kv(part)
            except ValueError:
                raise YamlUnsupported(
                    f"flow mapping entry {part!r} has no ':' — a set is not a mapping",
                    filename, lineno, line, "flow_set",
                ) from None
            out[_scalar(k, filename, lineno, line, flow=True)] = \
                _scalar(v, filename, lineno, line, flow=True)
        return out
    if s.startswith("["):
        if not s.endswith("]"):
            raise YamlInvalid("unterminated flow sequence", filename, lineno, line,
                              "unterminated_flow")
        inner = s[1:-1].strip()
        if not inner:
            return []
        return [_scalar(p, filename, lineno, line, flow=True) for p in _split_flow(inner)]
    if not flow and _PLAIN_MAPPING_VALUE.search(s):
        raise YamlInvalid(
            "a plain scalar cannot contain ': ' or end in ':' — YAML reads that as a mapping, "
            "so quote the value if the colon is part of the text",
            filename, lineno, line, "mapping_value_in_plain_scalar",
        )
    return s


def _split_flow(s: str) -> list[str]:
    """Split a flow body on commas at depth 0, outside quotes.

    Depth-aware so `{a: [1, 2], b: 3}` yields two parts, not three.
    """
    parts, buf, quote, depth = [], [], None, 0
    for c in s:
        if quote:
            buf.append(c)
            if c == quote:
                quote = None
        elif c in "\"'":
            quote = c
            buf.append(c)
        elif c in "[{":
            depth += 1
            buf.append(c)
        elif c in "]}":
            depth -= 1
            buf.append(c)
        elif c == "," and depth == 0:
            parts.append("".join(buf))
            buf = []
        else:
            buf.append(c)
    parts.append("".join(buf))
    return [p.strip() for p in parts if p.strip()]


def _split_kv(s: str) -> tuple[str, str]:
    """Split one flow-mapping entry on its first depth-0, unquoted colon."""
    quote, depth = None, 0
    for n, c in enumerate(s):
        if quote:
            if c == quote:
                quote = None
        elif c in "\"'":
            quote = c
        elif c in "[{":
            depth += 1
        elif c in "]}":
            depth -= 1
        elif c == ":" and depth == 0:
            return s[:n].strip(), s[n + 1:].strip()
    raise ValueError(s)


_BLOCK_HEADER = re.compile(r"^([>|])([-+]?)$")


class _Reader:
    def __init__(self, text: str, filename: str) -> None:
        self.raw = text.splitlines()
        self.filename = filename
        self.i = 0
        # Has the document's content begun? Before it, `---` is this document's marker; after
        # it, `---` opens a SECOND document. Skipping both merged two documents into one.
        self.started = False

    # -- line helpers --------------------------------------------------------
    def _indent(self, s: str) -> int:
        return len(s) - len(s.lstrip(" "))

    def _skip(self) -> None:
        """Advance past blank lines and comments, and a document marker before content.

        A `---` AFTER content is not skippable. It begins a second document, and skipping it
        silently merged two documents into one — a wrong answer that reads as a whole document.
        It is left in place for the structure readers to stop at, and parse() reports it.
        """
        while self.i < len(self.raw):
            s = self.raw[self.i].strip()
            if not s or s.startswith("#"):
                self.i += 1
            elif s in ("---", "...") and not self.started:
                self.i += 1
            else:
                return

    def _check_structure(self, line: str, lineno: int) -> None:
        """Refusals that are properties of the LINE rather than of a value."""
        if _TAB_INDENT.match(line):
            raise YamlInvalid("a tab cannot indent a line — YAML forbids tabs in indentation",
                              self.filename, lineno, line, "tab_indentation")
        stripped = _strip_comment(line)
        for rx, why, construct in _REFUSE_LINE:
            if rx.search(stripped):
                raise YamlUnsupported(why, self.filename, lineno, line, construct)

    # -- block scalars -------------------------------------------------------
    @staticmethod
    def _chomp(body: str, trailing_blanks: int, chomp: str) -> str:
        """Apply the chomping indicator to an already-assembled block scalar.

        clip (default): exactly one trailing newline. strip (-): none.
        keep (+): the trailing blank lines are content and are preserved.
        """
        if not body:
            return "" if chomp == "-" else body
        if chomp == "-":
            return body[:-1] if body.endswith("\n") else body
        if chomp == "+":
            return body + "\n" * trailing_blanks
        return body

    def _literal(self, parent_indent: int, chomp: str = "") -> str:
        """Read a '|' block. Newlines are content: every line break is preserved."""
        lines: list[str | None] = []
        while self.i < len(self.raw):
            line = self.raw[self.i]
            if not line.strip():
                lines.append(None)
                self.i += 1
                continue
            if self._indent(line) <= parent_indent:
                break
            lines.append(line)
            self.i += 1
        trailing = 0
        while lines and lines[-1] is None:
            lines.pop()
            trailing += 1
        if not lines:
            return ""
        base = min(self._indent(x) for x in lines if x is not None)
        body = "\n".join("" if x is None else x[base:].rstrip("\r") for x in lines) + "\n"
        return self._chomp(body, trailing, chomp)

    def _folded(self, parent_indent: int, chomp: str = "") -> str:
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
        trailing = 0
        while lines and lines[-1][0] == -1:
            lines.pop()
            trailing += 1
        if not lines:
            return ""
        base = min(ind for ind, _ in lines if ind >= 0)
        out, prev_more, blanks, started = "", False, 0, False
        for ind, text in lines:
            if ind == -1:
                blanks += 1
                continue
            more = ind > base
            if started:
                # A blank line contributes one newline; a more-indented line adds its own,
                # because the break before it is literal rather than folded. With no blank,
                # a break folds to a space unless either side is more-indented.
                if blanks:
                    out += "\n" * blanks + ("\n" if (more or prev_more) else "")
                else:
                    out += "\n" if (more or prev_more) else " "
            out += (" " * (ind - base) + text) if more else text
            prev_more, blanks, started = more, 0, True
        return self._chomp(out + "\n", trailing, chomp)

    def _continue_plain(self, first: str, own_indent: int) -> str:
        """Absorb continuation lines of an unquoted multi-line scalar.

            - Make cartridge replacement a 20-minute task, not an
              event that shuts off water for the whole family.

        YAML folds those into one string. A continuation is more indented than the line that
        started the scalar, is not itself a `key:`, and is not a sequence entry — anything
        else ends the scalar. Quoted and flow values are excluded by the caller.
        """
        parts = [first]
        while self.i < len(self.raw):
            line = self.raw[self.i]
            if not line.strip():
                break
            if self._indent(line) <= own_indent:
                break
            if _TAB_INDENT.match(line):
                raise YamlInvalid("a tab cannot indent a line — YAML forbids tabs in indentation",
                                  self.filename, self.i + 1, line, "tab_indentation")
            body = _strip_comment(line.strip())
            if body.startswith("- "):
                # PyYAML folds this into the plain value as one string: `- a` then `  - b` is
                # "a - b". It is valid, and it is almost always a nested list whose parent key
                # was forgotten — so it is reported rather than quietly turned into prose.
                raise YamlUnsupported(
                    "a more-indented '- ' under a plain value — YAML folds it into the value as "
                    "one string, which is almost never what was meant",
                    self.filename, self.i + 1, line, "nested_list_under_plain_item")
            if not body or body == "-" or _KEY.match(body):
                break
            if _BLOCK_HEADER.match(body):
                break
            parts.append(body)
            self.i += 1
        return " ".join(parts)

    def _gather_quoted(self, first: str, lineno: int, line: str) -> str:
        """Absorb the continuation lines of a quoted scalar that spans several lines.

        SIX REAL FILES were refused as "unterminated" for doing what YAML plainly allows — the
        largest single gap the 2026-09-11 measurement found:

            - "Rolling-release is the WORST fit for a sit-idle-then-rely backup: the
              cost lands exactly when you need it."

        The folding is PyYAML's, confirmed case by case: a line break becomes a space, a blank
        line becomes a newline, trailing white space is discarded, and in a double-quoted scalar
        a trailing backslash escapes the break entirely. Returns one folded token, so _quoted's
        unescaping needs no knowledge of any of this.
        """
        quote = first[0]
        if _quote_end(first, quote) is not None:
            return first
        body, blanks = first[1:].rstrip(), 0
        while self.i < len(self.raw):
            nxt = self.raw[self.i]
            s = nxt.strip()
            # A document marker inside a quoted scalar is an error in YAML, not content. Without
            # this, one unterminated quote would swallow the rest of the file and the damage
            # would report as something else entirely.
            if s in ("---", "..."):
                break
            if _TAB_INDENT.match(nxt):
                raise YamlInvalid("a tab cannot indent a line — YAML forbids tabs in indentation",
                                  self.filename, self.i + 1, nxt, "tab_indentation")
            self.i += 1
            if not s:
                blanks += 1
                continue
            end = _quote_end(s, quote, 0)
            piece = s if end is None else s[:end]
            if quote == '"' and _ends_with_escape(body):
                body = body[:-1] + piece
            elif blanks:
                body = body + "\n" * blanks + piece
            else:
                body = body + " " + piece
            blanks = 0
            if end is not None:
                if s[end + 1:].strip():
                    raise YamlInvalid("text after a closing quote", self.filename, self.i, nxt,
                                      "text_after_quote")
                return quote + body + quote
        raise YamlInvalid(f"unterminated {_QUOTE_NAME[quote]}-quoted scalar",
                          self.filename, lineno, line, "unterminated_quote")

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
                raise YamlInvalid("unterminated flow collection",
                                  self.filename, start, first, "unterminated_flow")
            text += " " + _strip_comment(self.raw[self.i].strip())
            self.i += 1
        return text

    # -- structure -----------------------------------------------------------
    def parse(self):
        self._skip()
        if self.i >= len(self.raw):
            return None
        self.started = True
        value = self._block(self._indent(self.raw[self.i]))
        self._require_end_of_document()
        return value

    def _require_end_of_document(self) -> None:
        """Nothing may follow the root structure except blank lines and comments.

        THE SILENT TRUNCATION GUARD, and general on purpose rather than a patch for the two
        cases that exposed it. Every structure reader STOPS at a line it cannot use — a root
        mapping stops at `- item`, a root sequence stops at `key:` — and until 2026-09-12 parse()
        returned what it had and threw the rest of the file away. A document that lost half its
        content parsed cleanly, passed every check, and read as complete. Two real files on this
        machine did exactly that.
        """
        while self.i < len(self.raw):
            s = self.raw[self.i].strip()
            if not s or s.startswith("#"):
                self.i += 1
                continue
            lineno, line = self.i + 1, self.raw[self.i]
            if s in ("---", "..."):
                # A marker followed by nothing but blanks and comments ends the document.
                # Anything else is a second one — valid YAML as a STREAM, and refused because
                # Rite reads one document per file: the second would simply be ignored.
                rest = [x.strip() for x in self.raw[self.i + 1:]]
                if any(x and not x.startswith("#") and x not in ("---", "...") for x in rest):
                    raise YamlUnsupported(
                        "a second YAML document in one file — Rite reads one document per file",
                        self.filename, lineno, line, "multi_document")
                if s == "---":
                    raise YamlUnsupported(
                        "a trailing '---' opens a second, empty document",
                        self.filename, lineno, line, "multi_document")
                self.i += 1
                continue
            raise YamlInvalid(
                "content after the end of the top-level structure — the structure above ended "
                "here, so everything below would be silently dropped",
                self.filename, lineno, line, "content_after_root")

    def _block(self, indent: int):
        self._skip()
        if self.i >= len(self.raw):
            return None
        line = self.raw[self.i]
        if self._indent(line) < indent:
            return None
        body = _strip_comment(line.strip())
        if body[:1] in ("[", "{"):
            # A flow collection standing alone as a block value, possibly wrapped.
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
            if line.strip() in ("---", "..."):
                break  # end of this document; parse() decides what that means
            ind = self._indent(line)
            if ind < indent or not (line.strip().startswith("- ") or line.strip() == "-"):
                break
            if ind > indent:
                raise YamlInvalid("unexpected indentation in sequence",
                                  self.filename, self.i + 1, line, "bad_indentation")
            lineno = self.i + 1
            self._check_structure(line, lineno)
            rest = _strip_comment(line.strip()[1:].strip())
            self.i += 1
            if not rest:
                items.append(self._block(indent + 1))
                continue
            if rest[:1] in ("[", "{"):
                # "- {a: 1}" / "- [1, 2]" — a flow collection as the item itself. This must be
                # tested BEFORE _KEY, which otherwise reads `{a` as a key and `1}` as a value.
                items.append(_scalar(self._gather_flow(rest), self.filename, lineno, line))
                continue
            m = _KEY.match(rest)
            if m:
                # "- key: value" — a mapping whose first key sits on the dash line.
                self.i -= 1
                self.raw[self.i] = " " * (ind + 2) + rest
                items.append(self._map(ind + 2))
                continue
            hdr = _BLOCK_HEADER.match(rest)
            if hdr:
                style, chomp = hdr.group(1), hdr.group(2)
                reader = self._literal if style == "|" else self._folded
                items.append(reader(ind, chomp))
                continue
            if rest[:1] in ('"', "'"):
                rest = self._gather_quoted(rest, lineno, line)
            else:
                rest = self._continue_plain(rest, ind)
            items.append(_scalar(rest, self.filename, lineno, line))
        return items

    def _map(self, indent: int) -> dict:
        out: dict = {}
        while True:
            self._skip()
            if self.i >= len(self.raw):
                break
            line = self.raw[self.i]
            if line.strip() in ("---", "..."):
                break  # end of this document; parse() decides what that means
            ind = self._indent(line)
            if ind < indent:
                break
            if line.strip().startswith("- "):
                break
            if ind > indent:
                raise YamlInvalid("unexpected indentation in mapping",
                                  self.filename, self.i + 1, line, "bad_indentation")
            lineno = self.i + 1
            self._check_structure(line, lineno)
            body = _strip_comment(line.strip())
            m = _KEY.match(body)
            if not m:
                raise YamlInvalid("expected 'key: value'", self.filename, lineno, line,
                                  "expected_key_value")
            key = _scalar(m.group("key"), self.filename, lineno, line)
            val = m.group("val")
            self.i += 1
            if val is None or val == "":
                nxt = self._peek_indent()
                # A block sequence is allowed to sit at its key's own indentation:
                #   steps:
                #   - id: presets
                # Requiring nxt > indent read that as an empty value and dropped the list.
                same_indent_seq = (nxt == indent and self._peek_is_item())
                out[key] = (self._block(nxt)
                            if nxt is not None and (nxt > indent or same_indent_seq)
                            else None)
            elif _BLOCK_HEADER.match(val.strip()):
                hdr = _BLOCK_HEADER.match(val.strip())
                style, chomp = hdr.group(1), hdr.group(2)
                reader = self._literal if style == "|" else self._folded
                out[key] = reader(indent, chomp)
            else:
                v = val.strip()
                if v[:1] in ("[", "{"):
                    if not _flow_balanced(v):
                        v = self._gather_flow(v)
                elif v[:1] in ('"', "'"):
                    v = self._gather_quoted(v, lineno, line)
                else:
                    v = self._continue_plain(v, ind)
                out[key] = _scalar(v, self.filename, lineno, line)
        return out

    def _peek_is_item(self) -> bool:
        """Is the next meaningful line a sequence entry?

        A document marker ends the search rather than being skipped past: what follows it
        belongs to another document, and treating it as this key's value is how two documents
        became one.
        """
        j = self.i
        while j < len(self.raw):
            t = self.raw[j].strip()
            if t in ("---", "..."):
                return False
            if t and not t.startswith("#"):
                return t.startswith("- ") or t == "-"
            j += 1
        return False

    def _peek_indent(self):
        j = self.i
        while j < len(self.raw):
            s = self.raw[j].strip()
            if s in ("---", "..."):
                return None
            if s and not s.startswith("#"):
                return self._indent(self.raw[j])
            j += 1
        return None


def load(text: str, filename: str = "<string>"):
    """Parse `text` as the Rite YAML subset.

    Raises YamlInvalid for text that is not YAML, and YamlUnsupported for valid YAML using a
    construct the standard declares out of subset. Both derive from RiteYamlError, so a caller
    that only wants "could this be read?" needs no change.

    A leading byte order mark is stripped. Editors on Windows write one, PyYAML ignores it, and
    riteyaml read it into the first key — so `\\ufeffas_of` was a different key from `as_of` and
    every check on that document silently found nothing.
    """
    if text.startswith("﻿"):
        text = text[1:]
    return _Reader(text, filename).parse()
