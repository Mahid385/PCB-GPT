# Circuit DSL to KiCad

A small research prototype exploring **programmatic circuit design and automatic KiCad schematic generation**.

The project introduces a lightweight Python-based DSL (Domain-Specific Language) for describing electronic circuits using Python. A circuit defined with the DSL can then be compiled into a portable **KiCad 6+ schematic (`.kicad_sch`)**.

The main goal is to explore how structured, machine-readable circuit descriptions can be transformed into actual EDA artifacts.

## Research Idea

Traditional schematic design requires manually placing symbols, wiring nets, and configuring component properties inside an EDA tool.

This project explores an alternative workflow:

```text
Circuit Description
        ↓
   Python DSL
        ↓
Circuit Representation
        ↓
     Compiler
        ↓
KiCad Schematic
```

This provides a foundation for experimenting with higher-level systems such as:

- Natural-language → circuit generation
- AI-assisted schematic design
- Programmatic electronics design
- Automated circuit synthesis
- Design-rule and connectivity validation

## Quick Start

Compile a circuit definition:

```powershell
python -m circuit_dsl examples\voltage_divider.py -o build\voltage_divider.kicad_sch
```

The resulting `.kicad_sch` file can be opened directly in KiCad's schematic editor.

## Example

A simple voltage-divider circuit can be described as:

```python
from circuit_dsl import Circuit


def build() -> Circuit:
    c = Circuit("voltage_divider", title="Voltage Divider")

    vin, vout, gnd = c.nets("VIN VOUT GND")

    c.vcc("#PWR01", vin, value="+5V", at=(35, 25))

    c.resistor(
        "R1",
        "10k",
        vin,
        vout,
        at=(55, 45),
        rotate=90
    )

    c.resistor(
        "R2",
        "10k",
        vout,
        gnd,
        at=(55, 70),
        rotate=90
    )

    c.capacitor(
        "C1",
        "100n",
        vout,
        gnd,
        at=(85, 58),
        rotate=90
    )

    c.connector(
        "J1",
        [vin, vout, gnd],
        value="OUT",
        at=(120, 55)
    )

    c.gnd("#PWR02", gnd, at=(55, 88))

    return c
```

The compiler converts this structured description into a KiCad schematic containing symbols, component properties, nets, labels, and wire connections.

## Supported Components

The current prototype provides basic primitives for:

- Resistors
- Capacitors
- Inductors
- Diodes
- LEDs
- Connectors
- Generic components
- VCC power symbols
- GND power symbols

Example:

```python
c.resistor("R1", "10k", net_a, net_b)
c.capacitor("C1", "100n", net_a, net_b)
c.diode("D1", "1N4148", net_a, net_b)
```

Generic components can also be described using explicit pin mappings:

```python
c.component(
    "U1",
    "CUSTOM",
    {"1": net_a, "2": net_b},
    pin_names={"1": "IN", "2": "OUT"}
)
```

## Compiler Input

The compiler accepts a Python file containing one of the following:

```python
def build() -> Circuit:
    ...
```

or a global:

```python
circuit = Circuit(...)
```

or:

```python
c = Circuit(...)
```

## Portable Schematic Generation

One design goal of the prototype is to reduce dependence on the user's globally installed KiCad symbol libraries.

Generated schematics embed simple symbol definitions directly into the schematic file. Components are automatically placed on a grid when coordinates are not explicitly provided.

Connections are represented using KiCad labels and short wire stubs.

This makes the generated schematic easier to transfer between environments.

## Why This Project?

This project is an experiment toward **higher-level representations of electronic circuits**.

Instead of treating a schematic only as a graphical artifact, the circuit can be represented as structured information:

```text
Components
    +
Pins
    +
Nets
    +
Electrical relationships
    ↓
Structured Circuit Model
```

Such a representation could later become an intermediate layer between AI systems and traditional EDA software.

For example:

```text
Engineer / AI
      ↓
Circuit Intent
      ↓
Structured Circuit Representation
      ↓
Validation
      ↓
KiCad Schematic
```

## Current Status

**Research / Experimental Prototype**

The current implementation focuses on:

- Defining circuits programmatically
- Representing components and nets
- Generating KiCad schematic files
- Basic automatic component placement
- Basic connectivity generation
- Portable embedded symbols

It is **not yet intended to replace a conventional EDA workflow**.

## Limitations

The current prototype is intentionally small.

It does not currently attempt to provide:

- Full electrical rule checking
- SPICE simulation
- PCB layout generation
- Automatic component selection
- Design optimization
- Complete KiCad library coverage
- Production-ready schematic generation
- Comprehensive schematic validation

These are potential directions for future research.

## Future Direction

Possible extensions include:

1. **Circuit validation**
   - Connectivity checking
   - Missing connection detection
   - Pin compatibility checking

2. **Circuit simulation**
   - SPICE model integration
   - Automated simulation
   - Electrical behavior verification

3. **Natural-language interface**

   ```text
   "Create a 5V voltage divider with a 10k load"
                  ↓
             Circuit DSL
                  ↓
             KiCad schematic
   ```

4. **AI-assisted circuit design**
   - Circuit reasoning
   - Component selection
   - Design constraint handling
   - Automatic schematic generation

5. **Schematic → structured circuit**
   - Parse existing KiCad schematics
   - Recover circuit topology
   - Build an intermediate representation

## Research Perspective

The long-term research question behind this prototype is:

> **Can electronic circuit design be represented at a sufficiently high level that reasoning systems can generate, validate, and modify real EDA designs programmatically?**

This repository represents an early experiment toward that direction.

## Safety / Execution Note

The compiler intentionally executes the supplied DSL file as Python.

Only compile circuit-definition files that you trust.

## License

License information has not yet been defined for this research prototype.

## Author

**Mahid Sajjad**

Mechatronics & Control Engineering  
UET Lahore, Pakistan

Research interests include:

- AI-assisted engineering
- Electronics design automation
- Mechanical design automation
- Engineering reasoning systems
- AI × EDA