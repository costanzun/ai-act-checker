"""Render the FactSheet schema compactly for prompts (kept in sync with facts.py)."""

from __future__ import annotations

import typing
from typing import Any, get_args, get_origin

from pydantic import BaseModel
from pydantic.fields import FieldInfo

from app.engine.facts import FactSheet


def _literal_values(tp: Any) -> list[str] | None:
    origin = get_origin(tp)
    if origin is typing.Literal:
        return [str(v) for v in get_args(tp)]
    if origin is typing.Union or str(origin) == "<class 'types.UnionType'>":
        for arg in get_args(tp):
            vals = _literal_values(arg)
            if vals:
                return vals
    return None


def _base_type(tp: Any) -> str:
    origin = get_origin(tp)
    args = [a for a in get_args(tp) if a is not type(None)]
    if origin is typing.Union or str(origin) == "<class 'types.UnionType'>":
        return _base_type(args[0]) if args else "any"
    if origin is list:
        return "list of strings"
    if tp is bool:
        return "true | false"
    if tp is str:
        return "string"
    return "value"


def render_compact_schema(model: type[BaseModel] = FactSheet, indent: int = 0) -> str:
    """One line per field: ``name: type (allowed values) — description``.

    ``null`` is always allowed and means unknown. Nested models are indented.
    """
    lines: list[str] = []
    pad = "  " * indent
    for name, field in model.model_fields.items():
        assert isinstance(field, FieldInfo)
        ann = field.annotation
        # nested model?
        nested = ann if isinstance(ann, type) and issubclass(ann, BaseModel) else None
        if nested is not None:
            lines.append(f"{pad}{name}: {{")
            lines.append(render_compact_schema(nested, indent + 1))
            lines.append(f"{pad}}}")
            continue
        vals = _literal_values(ann)
        if vals:
            tp = " | ".join(f'"{v}"' for v in vals)
        else:
            tp = _base_type(ann)
        desc = f" — {field.description}" if field.description else ""
        nullable = "" if name in {"system_summary", "purpose", "affected_persons", "free_text_notes"} else " | null"
        lines.append(f"{pad}{name}: {tp}{nullable}{desc}")
    return "\n".join(lines)
