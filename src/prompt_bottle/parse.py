from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Iterator


@dataclass(slots=True, kw_only=True)
class Tag:
    name: str
    attr: dict[str, str]
    content: str

    @property
    def content_text(self) -> str:
        return self.content

    def __str__(self) -> str:
        attrs = "".join(f' {k}="{v}"' for k, v in self.attr.items())
        return f"<{self.name}{attrs}>{self.content_text}</{self.name}>"

    @classmethod
    def from_str(cls, text: str) -> list[str | Tag]:
        """
        Parse only top-level paired tags.
        - Inner content is preserved as raw text (no recursive parsing).
        - Unmatched tags are left as normal text.
        """
        # Opening tag: <name ...>
        open_tag_re: re.Pattern[str] = re.compile(
            r"<(?P<name>[A-Za-z_][A-Za-z0-9._-]*)\s*(?P<attrs>[^>]*)>", re.DOTALL
        )

        # Closing tag for a specific name: </name>
        # Find either an opening of same name or a closing, for depth counting
        def same_name_token_iter(name: str, start: int) -> Iterator[re.Match[str]]:
            token_re = re.compile(
                rf"<(?P<open>{re.escape(name)})\b[^>]*>|</(?P<close>{re.escape(name)})>",
                re.DOTALL,
            )
            for m in token_re.finditer(text, start):
                yield m

        # Attribute pattern key="value"
        attr_re: re.Pattern[str] = re.compile(
            r'([A-Za-z_][A-Za-z0-9._-]*)\s*=\s*"([^"]*)"'
        )

        parts: list[str | Tag] = []
        pos: int = 0
        while True:
            m_open = open_tag_re.search(text, pos)
            if not m_open:
                if pos < len(text):
                    parts.append(text[pos:])
                break

            # Append text before the opening tag
            if m_open.start() > pos:
                parts.append(text[pos : m_open.start()])

            tag_name: str = m_open.group("name")
            raw_attrs: str = m_open.group("attrs") or ""

            # Walk forward to find the matching closing tag at depth 1
            body: str = ""
            depth: int = 1
            end_idx: int | None = None
            for tok in same_name_token_iter(tag_name, m_open.end()):
                if tok.group("open") is not None:
                    depth += 1
                elif tok.group("close") is not None:
                    depth -= 1
                    if depth == 0:
                        end_idx = tok.end()
                        body = text[m_open.end() : tok.start()]
                        break
            if end_idx is None:
                # Unmatched; treat as plain text
                parts.append(text[m_open.start() : m_open.end()])
                pos = m_open.end()
                continue

            attrs: dict[str, str] = {}
            for am in attr_re.finditer(raw_attrs):
                attrs[am.group(1)] = am.group(2)

            parts.append(cls(name=tag_name, attr=attrs, content=body))
            pos = end_idx

        return parts


if __name__ == "__main__":

    def show(parts: list[str | Tag]) -> None:
        for i, p in enumerate(parts):
            if isinstance(p, str):
                print(f"[{i}] STR: {p!r}")
            else:
                print(f"[{i}] TAG: <{p.name} {p.attr}> content={p.content_text!r}")
        print("-" * 40)

    examples: list[tuple[str, str]] = [
        (
            "simple div with role",
            'Hello <div role="user">world</div>!',
        ),
        (
            "nested same-name tags (no recursion, preserves inner raw)",
            "<div>outer <div>inner</div> after</div>",
        ),
        (
            "multiple top-level tags with plain text",
            'pre <a href="x">link</a> mid <b>bold</b> post',
        ),
        (
            "unmatched opening tag left as text",
            'start <span class="x">no close end',
        ),
        (
            "unmatched closing tag left as text",
            "start </span> end",
        ),
        (
            "attributes with dashes and underscores",
            '<tool_call tool_name="search" tool_call_id="123">{"q":"hi"}</tool_call>',
        ),
    ]

    for title, src in examples:
        print(f"CASE: {title}")
        show(Tag.from_str(src))
