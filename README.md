# Circuit DSL to KiCad

This is a small Python compiler for circuitry DSL scripts. You write a normal
Python file that builds a `Circuit`, then compile it into a KiCad 6+ schematic
file (`.kicad_sch`).

The generated schematic embeds simple symbols, places parts on a grid when no
coordinates are provided, and connects nets with KiCad labels and short wire
stubs. That makes the output portable because it does not depend on the user's
global KiCad symbol libraries.

## Quick Start

```powershell
python -m circuit_dsl examples\astable_555.py -o build\astable_555.kicad_sch
python -m circuit_dsl examples\voltage_divider.py -o build\esp32_relay_controller.kicad_sch
```

Open either generated `.kicad_sch` file in KiCad's schematic editor.

## DSL Example

```python
from circuit_dsl import Circuit


def build() -> Circuit:
    c = Circuit("voltage_divider", title="Voltage Divider")
    vin, vout, gnd = c.nets("VIN VOUT GND")

    c.vcc("#PWR01", vin, value="+5V", at=(35, 25))
    c.resistor("R1", "10k", vin, vout, at=(55, 45), rotate=90)
    c.resistor("R2", "10k", vout, gnd, at=(55, 70), rotate=90)
    c.capacitor("C1", "100n", vout, gnd, at=(85, 58), rotate=90)
    c.connector("J1", [vin, vout, gnd], value="OUT", at=(120, 55))
    c.gnd("#PWR02", gnd, at=(55, 88))

    return c
```

The compiler accepts any script that defines one of these:

- `build()` returning a `Circuit`
- a global `circuit`
- a global `c`

## Built In Parts

- `c.resistor(ref, value, a, b, ...)`
- `c.capacitor(ref, value, a, b, ...)`
- `c.inductor(ref, value, a, b, ...)`
- `c.diode(ref, value, anode, cathode, ...)`
- `c.led(ref, value, anode, cathode, ...)`
- `c.connector(ref, [net1, net2, ...], value="J", ...)`
- `c.component(ref, value, {"1": net1, "2": net2}, pin_names={...}, ...)`
- `c.vcc(ref, net, value="+5V", ...)`
- `c.gnd(ref, net, ...)`

Common keyword arguments are `at=(x, y)`, `rotate=0`, `footprint="Lib:Footprint"`,
`datasheet="~"`, `in_bom=True`, `on_board=True`, and `dnp=False`.

## Demonstration Circuits

- `examples\astable_555.py` is the focused compiler demo. It combines a custom
  NE555 IC, resistors, capacitors, an LED, power symbols, a connector, footprints,
  explicit placement, rotation, and shared named nets.
- `examples\voltage_divider.py` currently contains a larger ESP32 relay-controller
  sketch. It exercises the generic helper APIs for regulators, sensors, OLEDs,
  buttons, MOSFETs, relays, and named part-pin connections.

## Notes

This intentionally executes the input file as Python. Treat DSL files like any
other local Python script and only compile files you trust.
