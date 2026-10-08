from __future__ import annotations

from dataclasses import replace
from datetime import date
import math
from pathlib import Path
import uuid

from .model import Circuit, Net, Part, PinDef, SymbolTemplate


SCHEMATIC_VERSION = "20211123"
GENERATOR = "circuit_dsl_kicad"
UUID_NAMESPACE = uuid.UUID("86b08bfa-11f9-45d7-9c0b-5c6fd1627ec6")


def write_schematic(circuit: Circuit, output_path: str | Path) -> Path:
    """Compile a Circuit into a KiCad .kicad_sch file."""

    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(emit_schematic(circuit), encoding="utf-8")
    return path


def emit_schematic(circuit: Circuit) -> str:
    placed_parts = _place_parts(circuit.parts)
    root_uuid = _stable_uuid(circuit.name, "root")
    symbols = _unique_symbols(placed_parts)

    lines: list[str] = [
        "(kicad_sch",
        f"  (version {SCHEMATIC_VERSION})",
        f"  (generator {GENERATOR})",
        "",
        f"  (uuid {root_uuid})",
        f"  (paper {_q(circuit.paper)})",
        "",
        "  (title_block",
        f"    (title {_q(circuit.title)})",
        f"    (date {_q(date.today().isoformat())})",
        "  )",
        "",
        "  (lib_symbols",
    ]

    for symbol in symbols:
        lines.extend(_indent(_render_lib_symbol(symbol), 4))
    lines.append("  )")
    lines.append("")

    no_connects: list[str] = []
    wires: list[str] = []
    labels: list[str] = []
    for part in placed_parts:
        for pin in part.symbol.pins:
            endpoint = _pin_endpoint(part, pin)
            net = part.pins.get(pin.number)
            if net is None:
                no_connects.extend(_render_no_connect(part, pin, endpoint))
                continue
            wire_end, label_angle = _label_point(part, pin, endpoint)
            wires.extend(_render_wire(part, pin, endpoint, wire_end))
            labels.extend(_render_label(part, pin, net, wire_end, label_angle))

    if no_connects:
        lines.extend(no_connects)
        lines.append("")
    if wires:
        lines.extend(wires)
        lines.append("")
    if labels:
        lines.extend(labels)
        lines.append("")

    for part in placed_parts:
        lines.extend(_render_part(part, circuit.name, root_uuid))
        lines.append("")

    lines.extend(
        [
            "  (sheet_instances",
            "    (path \"/\" (page \"1\"))",
            "  )",
            ")",
            "",
        ]
    )
    return "\n".join(lines)


def _place_parts(parts: list[Part]) -> list[Part]:
    placed: list[Part] = []
    for index, part in enumerate(parts):
        if part.at is not None:
            placed.append(part)
            continue
        col = index % 4
        row = index // 4
        placed.append(replace(part, at=(45.0 + col * 40.0, 45.0 + row * 25.0)))
    return placed


def _unique_symbols(parts: list[Part]) -> list[SymbolTemplate]:
    symbols: dict[str, SymbolTemplate] = {}
    for part in parts:
        existing = symbols.get(part.lib_id)
        if existing is not None and existing != part.symbol:
            raise ValueError(f"Conflicting symbol templates for {part.lib_id}")
        symbols[part.lib_id] = part.symbol
    return [symbols[key] for key in sorted(symbols)]


def _render_lib_symbol(symbol: SymbolTemplate) -> list[str]:
    lines = [f"(symbol {_q(symbol.lib_id)}"]
    if symbol.pin_numbers_hidden:
        lines.append("  (pin_numbers hide)")
    if symbol.pin_names_hidden:
        lines.append(f"  (pin_names (offset {_fmt(symbol.pin_name_offset)}) hide)")
    else:
        lines.append(f"  (pin_names (offset {_fmt(symbol.pin_name_offset)}))")
    lines.append(f"  (in_bom {_yes_no(symbol.in_bom)})")
    lines.append(f"  (on_board {_yes_no(symbol.on_board)})")
    lines.extend(_render_symbol_property("Reference", symbol.ref_prefix, 0, 0.0, -5.08, hide=False))
    lines.extend(_render_symbol_property("Value", symbol.value, 1, 0.0, 5.08, hide=False))
    lines.extend(_render_symbol_property("Footprint", "", 2, 0.0, 0.0, hide=True))
    lines.extend(_render_symbol_property("Datasheet", "~", 3, 0.0, 0.0, hide=True))
    if symbol.keywords:
        lines.extend(_render_symbol_property("ki_keywords", symbol.keywords, 4, 0.0, 0.0, hide=True))
    if symbol.description:
        lines.extend(_render_symbol_property("ki_description", symbol.description, 5, 0.0, 0.0, hide=True))
    if symbol.footprint_filters:
        lines.extend(_render_symbol_property("ki_fp_filters", symbol.footprint_filters, 6, 0.0, 0.0, hide=True))
    lines.extend(f"  {graphic}" for graphic in symbol.graphics)
    for pin in symbol.pins:
        lines.extend(_render_pin_def(pin))
    lines.append(")")
    return lines


def _render_symbol_property(
    key: str,
    value: str,
    prop_id: int,
    x: float,
    y: float,
    *,
    hide: bool,
) -> list[str]:
    effects = _effects(hidden=hide)
    return [
        f"  (property {_q(key)} {_q(value)} (id {prop_id}) (at {_fmt(x)} {_fmt(y)} 0)",
        f"    {effects}",
        "  )",
    ]


def _render_pin_def(pin: PinDef) -> list[str]:
    return [
        f"  (pin {pin.electrical} {pin.style} (at {_fmt(pin.x)} {_fmt(pin.y)} {pin.rotation}) (length {_fmt(pin.length)})",
        f"    (name {_q(pin.name)} {_effects()})",
        f"    (number {_q(pin.number)} {_effects()})",
        "  )",
    ]


def _render_part(part: Part, project_name: str, root_uuid: uuid.UUID) -> list[str]:
    assert part.at is not None
    x, y = part.at
    part_uuid = _stable_uuid(project_name, part.ref, "symbol")
    lines = [
        f"  (symbol (lib_id {_q(part.lib_id)}) (at {_fmt(x)} {_fmt(y)} {part.rotate}) (unit 1)",
        f"    (in_bom {_yes_no(part.in_bom if part.in_bom is not None else part.symbol.in_bom)})",
        f"    (on_board {_yes_no(part.on_board if part.on_board is not None else part.symbol.on_board)})",
        f"    (dnp {_yes_no(part.dnp)})",
        "    (fields_autoplaced)",
        f"    (uuid {part_uuid})",
    ]
    lines.extend(_indent(_render_instance_property("Reference", part.ref, 0, x, y - 4.064, part.rotate), 4))
    lines.extend(_indent(_render_instance_property("Value", part.value, 1, x, y + 4.064, part.rotate), 4))
    lines.extend(_indent(_render_instance_property("Footprint", part.footprint, 2, x, y, 0, hide=True), 4))
    lines.extend(_indent(_render_instance_property("Datasheet", part.datasheet, 3, x, y, 0, hide=True), 4))
    for pin in part.symbol.pins:
        pin_uuid = _stable_uuid(project_name, part.ref, "pin", pin.number)
        lines.append(f"    (pin {_q(pin.number)} (uuid {pin_uuid}))")
    lines.extend(
        [
            "    (instances",
            f"      (project {_q(project_name)}",
            f"        (path \"/{root_uuid}\"",
            f"          (reference {_q(part.ref)})",
            "          (unit 1)",
            "        )",
            "      )",
            "    )",
            "  )",
        ]
    )
    return lines


def _render_instance_property(
    key: str,
    value: str,
    prop_id: int,
    x: float,
    y: float,
    rotate: int,
    *,
    hide: bool = False,
) -> list[str]:
    return [
        f"(property {_q(key)} {_q(value)} (id {prop_id}) (at {_fmt(x)} {_fmt(y)} {rotate})",
        f"  {_effects(hidden=hide)}",
        ")",
    ]


def _render_no_connect(part: Part, pin: PinDef, endpoint: tuple[float, float]) -> list[str]:
    x, y = endpoint
    return [
        "  (no_connect",
        f"    (at {_fmt(x)} {_fmt(y)})",
        f"    (uuid {_stable_uuid(part.ref, pin.number, 'no_connect')})",
        "  )",
    ]


def _render_wire(
    part: Part,
    pin: PinDef,
    start: tuple[float, float],
    end: tuple[float, float],
) -> list[str]:
    return [
        "  (wire",
        f"    (pts (xy {_fmt(start[0])} {_fmt(start[1])}) (xy {_fmt(end[0])} {_fmt(end[1])}))",
        "    (stroke (width 0) (type default) (color 0 0 0 0))",
        f"    (uuid {_stable_uuid(part.ref, pin.number, 'wire')})",
        "  )",
    ]


def _render_label(
    part: Part,
    pin: PinDef,
    net: Net,
    at: tuple[float, float],
    angle: int,
) -> list[str]:
    return [
        f"  (label {_q(net.name)}",
        f"    (at {_fmt(at[0])} {_fmt(at[1])} {angle})",
        f"    {_effects()}",
        f"    (uuid {_stable_uuid(part.ref, pin.number, net.name, 'label')})",
        "  )",
    ]


def _pin_endpoint(part: Part, pin: PinDef) -> tuple[float, float]:
    assert part.at is not None
    dx, dy = _rotate_point(pin.x, pin.y, part.rotate)
    return part.at[0] + dx, part.at[1] + dy


def _label_point(part: Part, pin: PinDef, endpoint: tuple[float, float]) -> tuple[tuple[float, float], int]:
    angle = (pin.rotation + part.rotate) % 360
    vx, vy = _outward_vector(angle)
    return (endpoint[0] + vx * 3.81, endpoint[1] + vy * 3.81), _label_angle(vx, vy)


def _rotate_point(x: float, y: float, angle: int) -> tuple[float, float]:
    normalized = angle % 360
    if normalized == 0:
        return x, y
    if normalized == 90:
        return -y, x
    if normalized == 180:
        return -x, -y
    if normalized == 270:
        return y, -x
    radians = math.radians(normalized)
    return x * math.cos(radians) - y * math.sin(radians), x * math.sin(radians) + y * math.cos(radians)


def _outward_vector(angle: int) -> tuple[float, float]:
    normalized = angle % 360
    if normalized == 0:
        return -1.0, 0.0
    if normalized == 90:
        return 0.0, -1.0
    if normalized == 180:
        return 1.0, 0.0
    if normalized == 270:
        return 0.0, 1.0
    radians = math.radians(normalized)
    return -math.cos(radians), -math.sin(radians)


def _label_angle(vx: float, vy: float) -> int:
    if abs(vx) >= abs(vy):
        return 0 if vx >= 0 else 180
    return 90 if vy < 0 else 270


def _effects(*, hidden: bool = False) -> str:
    hide = " hide" if hidden else ""
    return f"(effects (font (size 1.27 1.27)){hide})"


def _indent(lines: list[str], spaces: int) -> list[str]:
    prefix = " " * spaces
    return [prefix + line if line else "" for line in lines]


def _q(value: object) -> str:
    text = str(value)
    escaped = text.replace("\\", "\\\\").replace("\"", "\\\"")
    return f"\"{escaped}\""


def _yes_no(value: bool) -> str:
    return "yes" if value else "no"


def _fmt(value: float | int) -> str:
    if isinstance(value, int):
        return str(value)
    rounded = round(float(value), 4)
    if rounded == 0:
        rounded = 0.0
    return f"{rounded:.4f}".rstrip("0").rstrip(".")


def _stable_uuid(*parts: object) -> uuid.UUID:
    key = "/".join(str(part) for part in parts)
    return uuid.uuid5(UUID_NAMESPACE, key)
