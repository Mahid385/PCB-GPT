from __future__ import annotations

from functools import lru_cache
import re

from .model import PinDef, SymbolTemplate


def _stroke(width: float = 0.1524) -> str:
    return f"(stroke (width {width:g}) (type default) (color 0 0 0 0))"


def _fill(kind: str = "none") -> str:
    return f"(fill (type {kind}))"


@lru_cache(maxsize=None)
def resistor_symbol() -> SymbolTemplate:
    return SymbolTemplate(
        lib_id="CircuitDSL:R",
        ref_prefix="R",
        value="R",
        pins=_two_pin_defs(),
        graphics=(
            "(rectangle (start -2.54 -1.27) (end 2.54 1.27) "
            f"{_stroke()} {_fill('none')})",
        ),
        description="Generic two pin resistor",
        keywords="resistor R",
        footprint_filters="R_*",
    )


@lru_cache(maxsize=None)
def capacitor_symbol() -> SymbolTemplate:
    return SymbolTemplate(
        lib_id="CircuitDSL:C",
        ref_prefix="C",
        value="C",
        pins=_two_pin_defs(),
        graphics=(
            f"(polyline (pts (xy -1.016 -2.54) (xy -1.016 2.54)) {_stroke()} {_fill()})",
            f"(polyline (pts (xy 1.016 -2.54) (xy 1.016 2.54)) {_stroke()} {_fill()})",
        ),
        description="Generic two pin capacitor",
        keywords="capacitor C",
        footprint_filters="C_*",
    )


@lru_cache(maxsize=None)
def inductor_symbol() -> SymbolTemplate:
    return SymbolTemplate(
        lib_id="CircuitDSL:L",
        ref_prefix="L",
        value="L",
        pins=_two_pin_defs(),
        graphics=(
            f"(arc (start -2.54 0) (mid -1.905 -0.635) (end -1.27 0) {_stroke()} {_fill()})",
            f"(arc (start -1.27 0) (mid -0.635 -0.635) (end 0 0) {_stroke()} {_fill()})",
            f"(arc (start 0 0) (mid 0.635 -0.635) (end 1.27 0) {_stroke()} {_fill()})",
            f"(arc (start 1.27 0) (mid 1.905 -0.635) (end 2.54 0) {_stroke()} {_fill()})",
        ),
        description="Generic two pin inductor",
        keywords="inductor L",
        footprint_filters="L_*",
    )


@lru_cache(maxsize=None)
def diode_symbol() -> SymbolTemplate:
    return SymbolTemplate(
        lib_id="CircuitDSL:D",
        ref_prefix="D",
        value="D",
        pins=_two_pin_defs(("A", "K")),
        graphics=(
            f"(polyline (pts (xy -1.778 -2.032) (xy -1.778 2.032) (xy 1.524 0) (xy -1.778 -2.032)) {_stroke()} {_fill()})",
            f"(polyline (pts (xy 1.524 -2.032) (xy 1.524 2.032)) {_stroke()} {_fill()})",
        ),
        description="Generic diode",
        keywords="diode D",
        footprint_filters="D_*",
    )


@lru_cache(maxsize=None)
def led_symbol() -> SymbolTemplate:
    return SymbolTemplate(
        lib_id="CircuitDSL:LED",
        ref_prefix="D",
        value="LED",
        pins=_two_pin_defs(("A", "K")),
        graphics=(
            f"(polyline (pts (xy -1.778 -2.032) (xy -1.778 2.032) (xy 1.524 0) (xy -1.778 -2.032)) {_stroke()} {_fill()})",
            f"(polyline (pts (xy 1.524 -2.032) (xy 1.524 2.032)) {_stroke()} {_fill()})",
            f"(polyline (pts (xy 0.508 -2.54) (xy 2.286 -4.318)) {_stroke()} {_fill()})",
            f"(polyline (pts (xy 1.778 -2.54) (xy 3.556 -4.318)) {_stroke()} {_fill()})",
        ),
        description="Generic LED",
        keywords="LED diode",
        footprint_filters="LED_*",
    )


@lru_cache(maxsize=None)
def connector_symbol(pin_count: int) -> SymbolTemplate:
    if pin_count < 1:
        raise ValueError("Connectors must have at least one pin")
    pin_numbers = [str(index + 1) for index in range(pin_count)]
    return generic_box_symbol(
        lib_id=f"CircuitDSL:CONN_{pin_count}",
        ref_prefix="J",
        value=f"Conn_{pin_count}",
        pin_numbers=pin_numbers,
        pin_names=pin_numbers,
        width=5.08,
        pin_pitch=2.54,
        left_only=True,
        description=f"Generic {pin_count} pin connector",
        keywords="connector",
        footprint_filters="Connector_*",
    )


@lru_cache(maxsize=None)
def power_symbol(value: str) -> SymbolTemplate:
    safe = _safe_id(value)
    return SymbolTemplate(
        lib_id=f"CircuitDSL:PWR_{safe}",
        ref_prefix="#PWR",
        value=value,
        pins=(PinDef("1", value, 0.0, 0.0, 90, length=0.0, electrical="power_in"),),
        graphics=(
            f"(polyline (pts (xy -1.524 -2.54) (xy 0 -5.08) (xy 1.524 -2.54)) {_stroke()} {_fill()})",
            f"(polyline (pts (xy 0 -5.08) (xy 0 0)) {_stroke()} {_fill()})",
        ),
        in_bom=False,
        on_board=False,
        pin_numbers_hidden=True,
        pin_names_hidden=True,
        description="Generated power symbol",
        keywords="power",
    )


@lru_cache(maxsize=None)
def gnd_symbol() -> SymbolTemplate:
    return SymbolTemplate(
        lib_id="CircuitDSL:GND",
        ref_prefix="#PWR",
        value="GND",
        pins=(PinDef("1", "GND", 0.0, 0.0, 90, length=0.0, electrical="power_in"),),
        graphics=(
            f"(polyline (pts (xy 0 0) (xy 0 1.27)) {_stroke()} {_fill()})",
            f"(polyline (pts (xy -2.54 1.27) (xy 2.54 1.27)) {_stroke()} {_fill()})",
            f"(polyline (pts (xy -1.524 2.032) (xy 1.524 2.032)) {_stroke()} {_fill()})",
            f"(polyline (pts (xy -0.762 2.794) (xy 0.762 2.794)) {_stroke()} {_fill()})",
        ),
        in_bom=False,
        on_board=False,
        pin_numbers_hidden=True,
        pin_names_hidden=True,
        description="Generated ground symbol",
        keywords="ground GND",
    )


def generic_box_symbol(
    *,
    lib_id: str,
    ref_prefix: str,
    value: str,
    pin_numbers: list[str],
    pin_names: list[str] | None = None,
    width: float = 12.7,
    pin_pitch: float = 2.54,
    left_only: bool = False,
    description: str = "Generated component",
    keywords: str = "component",
    footprint_filters: str = "",
) -> SymbolTemplate:
    if not pin_numbers:
        raise ValueError("Generic components must have at least one pin")
    if pin_names is None:
        pin_names = pin_numbers
    if len(pin_names) != len(pin_numbers):
        raise ValueError("pin_names must have the same length as pin_numbers")

    if left_only:
        height = max(5.08, (len(pin_numbers) + 1) * pin_pitch)
        top = -height / 2
        bottom = height / 2
        pins = tuple(
            PinDef(number, name, -width / 2 - 2.54, top + (index + 1) * pin_pitch, 0)
            for index, (number, name) in enumerate(zip(pin_numbers, pin_names))
        )
    else:
        left_numbers = pin_numbers[::2]
        right_numbers = pin_numbers[1::2]
        max_side = max(len(left_numbers), len(right_numbers), 1)
        height = max(7.62, (max_side + 1) * pin_pitch)
        top = -height / 2
        bottom = height / 2
        left_pins = [
            PinDef(number, pin_names[pin_numbers.index(number)], -width / 2 - 2.54, top + (idx + 1) * pin_pitch, 0)
            for idx, number in enumerate(left_numbers)
        ]
        right_pins = [
            PinDef(number, pin_names[pin_numbers.index(number)], width / 2 + 2.54, top + (idx + 1) * pin_pitch, 180)
            for idx, number in enumerate(right_numbers)
        ]
        pins = tuple(left_pins + right_pins)

    return SymbolTemplate(
        lib_id=lib_id,
        ref_prefix=ref_prefix,
        value=value,
        pins=pins,
        graphics=(
            f"(rectangle (start {-width / 2:g} {top:g}) (end {width / 2:g} {bottom:g}) "
            f"{_stroke()} {_fill('background')})",
        ),
        description=description,
        keywords=keywords,
        footprint_filters=footprint_filters,
    )


def _two_pin_defs(names: tuple[str, str] = ("1", "2")) -> tuple[PinDef, PinDef]:
    return (
        PinDef("1", names[0], -5.08, 0.0, 0),
        PinDef("2", names[1], 5.08, 0.0, 180),
    )


def _safe_id(raw: str) -> str:
    cleaned = re.sub(r"[^A-Za-z0-9_]+", "_", str(raw).strip())
    return cleaned.strip("_") or "NET"
