from __future__ import annotations

from collections import OrderedDict, defaultdict
from dataclasses import dataclass
import re
from typing import Mapping, Sequence


@dataclass(frozen=True)
class Net:
    """A named electrical net."""

    name: str

    def __post_init__(self) -> None:
        name = str(self.name).strip()
        if not name:
            raise ValueError("Net names cannot be empty")
        object.__setattr__(self, "name", name)

    def __str__(self) -> str:
        return self.name


NetLike = Net | str


@dataclass(frozen=True)
class PinDef:
    """A KiCad symbol pin definition in symbol-local coordinates."""

    number: str
    name: str
    x: float
    y: float
    rotation: int
    length: float = 2.54
    electrical: str = "passive"
    style: str = "line"


@dataclass(frozen=True)
class SymbolTemplate:
    """Reusable schematic symbol definition embedded in the output file."""

    lib_id: str
    ref_prefix: str
    value: str
    pins: tuple[PinDef, ...]
    graphics: tuple[str, ...] = ()
    in_bom: bool = True
    on_board: bool = True
    pin_numbers_hidden: bool = False
    pin_names_hidden: bool = False
    pin_name_offset: float = 0.508
    description: str = ""
    keywords: str = ""
    footprint_filters: str = ""

    def pin(self, number: str) -> PinDef:
        for pin in self.pins:
            if pin.number == str(number):
                return pin
        raise KeyError(f"Symbol {self.lib_id} has no pin {number!r}")


@dataclass
class Part:
    """A placed component instance."""

    ref: str
    value: str
    symbol: SymbolTemplate
    pins: "OrderedDict[str, Net | None]"
    footprint: str = ""
    datasheet: str = "~"
    at: tuple[float, float] | None = None
    rotate: int = 0
    in_bom: bool | None = None
    on_board: bool | None = None
    dnp: bool = False

    def __post_init__(self) -> None:
        self.ref = str(self.ref).strip()
        self.value = str(self.value)
        self.rotate = int(self.rotate) % 360
        if not self.ref:
            raise ValueError("Part reference cannot be empty")
        normalized: "OrderedDict[str, Net | None]" = OrderedDict()
        for pin, net in self.pins.items():
            normalized[str(pin)] = net
        self.pins = normalized

    @property
    def lib_id(self) -> str:
        return self.symbol.lib_id


class Circuit:
    """Circuit container used by Python DSL scripts."""

    def __init__(self, name: str, *, title: str | None = None, paper: str = "A4") -> None:
        self.name = str(name).strip()
        if not self.name:
            raise ValueError("Circuit name cannot be empty")
        self.title = title or self.name
        self.paper = paper
        self.parts: list[Part] = []
        self._nets: dict[str, Net] = {}
        self._ref_counts: defaultdict[str, int] = defaultdict(int)

    def net(self, name: str) -> Net:
        key = str(name).strip()
        if not key:
            raise ValueError("Net names cannot be empty")
        if key not in self._nets:
            self._nets[key] = Net(key)
        return self._nets[key]

    def nets(self, names: str | Sequence[str]) -> tuple[Net, ...]:
        if isinstance(names, str):
            names = names.replace(",", " ").split()
        return tuple(self.net(name) for name in names)

    def add_part(
        self,
        ref: str | None,
        value: str,
        symbol: SymbolTemplate,
        pins: Mapping[str, NetLike | None],
        *,
        footprint: str = "",
        datasheet: str = "~",
        at: tuple[float, float] | None = None,
        rotate: int = 0,
        in_bom: bool | None = None,
        on_board: bool | None = None,
        dnp: bool = False,
    ) -> Part:
        ref = ref or self._next_ref(symbol.ref_prefix)
        normalized: "OrderedDict[str, Net | None]" = OrderedDict()
        known_pins = {pin.number for pin in symbol.pins}
        for pin in symbol.pins:
            raw_net = pins.get(pin.number)
            normalized[pin.number] = None if raw_net is None else self._coerce_net(raw_net)
        unknown = sorted(set(map(str, pins.keys())) - known_pins)
        if unknown:
            raise ValueError(f"{ref} uses unknown pin(s) for {symbol.lib_id}: {', '.join(unknown)}")
        part = Part(
            ref=ref,
            value=value,
            symbol=symbol,
            pins=normalized,
            footprint=footprint,
            datasheet=datasheet,
            at=at,
            rotate=rotate,
            in_bom=in_bom,
            on_board=on_board,
            dnp=dnp,
        )
        self.parts.append(part)
        return part

    def connect(self, net: NetLike, target: str | NetLike) -> None:
        """Connect a net to a named part pin such as ``U1.GPIO0``.

        If ``target`` is a plain net name, this simply ensures both net names
        exist. Named part targets may use either the symbol pin number or pin
        name after the dot.
        """

        coerced = self._coerce_net(net)
        if isinstance(target, Net):
            self._coerce_net(target)
            return
        target_text = str(target).strip()
        if "." not in target_text:
            self._coerce_net(target_text)
            return

        ref, pin_key = target_text.split(".", 1)
        ref = ref.strip()
        pin_key = pin_key.strip()
        if not ref or not pin_key:
            raise ValueError(f"Invalid connection target {target!r}")
        part = self._find_part(ref)
        pin = self._find_symbol_pin(part, pin_key)
        part.pins[pin.number] = coerced

    def resistor(
        self,
        ref: str | None,
        value: str,
        a: NetLike,
        b: NetLike,
        **kwargs,
    ) -> Part:
        from .symbols import resistor_symbol

        return self.add_part(ref, value, resistor_symbol(), {"1": a, "2": b}, **kwargs)

    def capacitor(
        self,
        ref: str | None,
        value: str,
        a: NetLike,
        b: NetLike,
        **kwargs,
    ) -> Part:
        from .symbols import capacitor_symbol

        return self.add_part(ref, value, capacitor_symbol(), {"1": a, "2": b}, **kwargs)

    def inductor(
        self,
        ref: str | None,
        value: str,
        a: NetLike,
        b: NetLike,
        **kwargs,
    ) -> Part:
        from .symbols import inductor_symbol

        return self.add_part(ref, value, inductor_symbol(), {"1": a, "2": b}, **kwargs)

    def diode(
        self,
        ref: str | None,
        value: str,
        anode: NetLike,
        cathode: NetLike,
        **kwargs,
    ) -> Part:
        from .symbols import diode_symbol

        return self.add_part(ref, value, diode_symbol(), {"1": anode, "2": cathode}, **kwargs)

    def led(
        self,
        ref: str | None,
        value: str,
        anode: NetLike,
        cathode: NetLike,
        **kwargs,
    ) -> Part:
        from .symbols import led_symbol

        return self.add_part(ref, value, led_symbol(), {"1": anode, "2": cathode}, **kwargs)

    def connector(
        self,
        ref: str | None,
        nets: Sequence[NetLike | None],
        *,
        value: str | None = None,
        **kwargs,
    ) -> Part:
        from .symbols import connector_symbol

        symbol = connector_symbol(len(nets))
        pins = OrderedDict((str(index + 1), net) for index, net in enumerate(nets))
        return self.add_part(ref, value or f"Conn_{len(nets)}", symbol, pins, **kwargs)

    def component(
        self,
        ref: str | None,
        value: str,
        pins: Mapping[str, NetLike | None],
        *,
        pin_names: Mapping[str, str] | None = None,
        footprint: str = "",
        datasheet: str = "~",
        at: tuple[float, float] | None = None,
        rotate: int = 0,
        in_bom: bool | None = None,
        on_board: bool | None = None,
        dnp: bool = False,
    ) -> Part:
        from .symbols import generic_box_symbol

        ordered_pins: "OrderedDict[str, NetLike | None]" = OrderedDict(
            (str(pin), net) for pin, net in pins.items()
        )
        pin_names = {str(pin): name for pin, name in (pin_names or {}).items()}
        symbol_key = ref or f"{value}_{'_'.join(ordered_pins.keys())}"
        symbol = generic_box_symbol(
            lib_id=f"CircuitDSL:{_safe_symbol_name(symbol_key)}",
            ref_prefix=_ref_prefix(ref or "U"),
            value=value,
            pin_numbers=list(ordered_pins.keys()),
            pin_names=[pin_names.get(pin, pin) for pin in ordered_pins.keys()],
        )
        return self.add_part(
            ref,
            value,
            symbol,
            ordered_pins,
            footprint=footprint,
            datasheet=datasheet,
            at=at,
            rotate=rotate,
            in_bom=in_bom,
            on_board=on_board,
            dnp=dnp,
        )

    def regulator(
        self,
        ref: str | None,
        *,
        regulator: str,
        vin: NetLike,
        vout: NetLike,
        gnd: NetLike,
        **kwargs,
    ) -> Part:
        return self.component(
            ref,
            f"Regulator {regulator}",
            {"VIN": vin, "VOUT": vout, "GND": gnd},
            pin_names={"VIN": "VIN", "VOUT": "VOUT", "GND": "GND"},
            **kwargs,
        )

    def esp32(
        self,
        ref: str | None,
        *,
        variant: str = "ESP32",
        **kwargs,
    ) -> Part:
        pin_names = [
            "3V3",
            "GND",
            "GPIO0",
            "GPIO3",
            "GPIO4",
            "GPIO5",
            "GPIO6",
            "GPIO7",
            "GPIO8",
            "GPIO19",
            "GPIO20",
        ]
        pins = OrderedDict((pin, pin) for pin in pin_names)
        return self.component(
            ref,
            variant,
            pins,
            pin_names={pin: pin for pin in pin_names},
            **kwargs,
        )

    def sensor(
        self,
        ref: str | None,
        *,
        sensor: str,
        data: NetLike,
        vcc: NetLike,
        gnd: NetLike,
        **kwargs,
    ) -> Part:
        return self.component(
            ref,
            sensor,
            {"VCC": vcc, "DATA": data, "GND": gnd},
            pin_names={"VCC": "VCC", "DATA": "DATA", "GND": "GND"},
            **kwargs,
        )

    def oled(
        self,
        ref: str | None,
        *,
        controller: str,
        interface: str,
        scl: NetLike,
        sda: NetLike,
        reset: NetLike,
        vcc: NetLike,
        gnd: NetLike,
        **kwargs,
    ) -> Part:
        return self.component(
            ref,
            f"{controller} {interface}",
            {"VCC": vcc, "GND": gnd, "SCL": scl, "SDA": sda, "RESET": reset},
            pin_names={
                "VCC": "VCC",
                "GND": "GND",
                "SCL": "SCL",
                "SDA": "SDA",
                "RESET": "RESET",
            },
            **kwargs,
        )

    def push_button(
        self,
        ref: str | None,
        a: NetLike,
        b: NetLike,
        *,
        value: str = "SW",
        **kwargs,
    ) -> Part:
        return self.component(
            ref,
            value,
            {"1": a, "2": b},
            pin_names={"1": "A", "2": "B"},
            **kwargs,
        )

    def mosfet(
        self,
        ref: str | None,
        value: str,
        *,
        gate: NetLike,
        source: NetLike,
        drain: NetLike,
        **kwargs,
    ) -> Part:
        return self.component(
            ref,
            value,
            {"G": gate, "D": drain, "S": source},
            pin_names={"G": "G", "D": "D", "S": "S"},
            **kwargs,
        )

    def relay(
        self,
        ref: str | None,
        *,
        coil_voltage: str,
        coil_pos: NetLike,
        coil_neg: NetLike,
        contact_com: NetLike,
        contact_no: NetLike,
        contact_nc: NetLike,
        **kwargs,
    ) -> Part:
        return self.component(
            ref,
            f"Relay {coil_voltage}",
            {
                "COIL+": coil_pos,
                "COIL-": coil_neg,
                "COM": contact_com,
                "NO": contact_no,
                "NC": contact_nc,
            },
            pin_names={
                "COIL+": "COIL+",
                "COIL-": "COIL-",
                "COM": "COM",
                "NO": "NO",
                "NC": "NC",
            },
            **kwargs,
        )

    def power(
        self,
        ref: str | None,
        net: NetLike,
        *,
        value: str | None = None,
        at: tuple[float, float] | None = None,
    ) -> Part:
        from .symbols import power_symbol

        coerced = self._coerce_net(net)
        symbol = power_symbol(value or coerced.name)
        return self.add_part(
            ref,
            value or coerced.name,
            symbol,
            {"1": coerced},
            at=at,
            in_bom=False,
            on_board=False,
        )

    def vcc(
        self,
        ref: str | None = None,
        net: NetLike = "VCC",
        *,
        value: str | None = None,
        at: tuple[float, float] | None = None,
    ) -> Part:
        return self.power(ref, net, value=value, at=at)

    def gnd(
        self,
        ref: str | None = None,
        net: NetLike = "GND",
        *,
        at: tuple[float, float] | None = None,
    ) -> Part:
        from .symbols import gnd_symbol

        coerced = self._coerce_net(net)
        return self.add_part(
            ref,
            "GND",
            gnd_symbol(),
            {"1": coerced},
            at=at,
            in_bom=False,
            on_board=False,
        )

    def compile(self, output_path: str) -> None:
        from .kicad import write_schematic

        write_schematic(self, output_path)

    def _coerce_net(self, net: NetLike) -> Net:
        if isinstance(net, Net):
            return self.net(net.name)
        return self.net(str(net))

    def _next_ref(self, prefix: str) -> str:
        self._ref_counts[prefix] += 1
        if prefix == "#PWR":
            return f"#PWR{self._ref_counts[prefix]:03d}"
        return f"{prefix}{self._ref_counts[prefix]}"

    def _find_part(self, ref: str) -> Part:
        for part in self.parts:
            if part.ref == ref:
                return part
        raise ValueError(f"No part with reference {ref!r}")

    def _find_symbol_pin(self, part: Part, pin_key: str) -> PinDef:
        for pin in part.symbol.pins:
            if pin.number == pin_key or pin.name == pin_key:
                return pin
        raise ValueError(f"{part.ref} has no pin named or numbered {pin_key!r}")


def _safe_symbol_name(raw: str) -> str:
    cleaned = re.sub(r"[^A-Za-z0-9_]+", "_", str(raw).strip())
    return cleaned.strip("_") or "Component"


def _ref_prefix(raw: str) -> str:
    match = re.match(r"^[#A-Za-z]+", str(raw))
    return match.group(0) if match else "U"
