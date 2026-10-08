from __future__ import annotations

import argparse
from pathlib import Path

from .compiler import load_circuit_from_script
from .kicad import write_schematic


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="circuit-dsl",
        description="Compile a Python circuit DSL script into a KiCad schematic.",
    )
    parser.add_argument("input", help="Python DSL file that defines a Circuit")
    parser.add_argument(
        "-o",
        "--output",
        help="Output .kicad_sch path. Defaults to <input stem>.kicad_sch.",
    )
    args = parser.parse_args(argv)

    input_path = Path(args.input)
    output = Path(args.output) if args.output else input_path.with_suffix(".kicad_sch")
    circuit = load_circuit_from_script(input_path)
    out_path = write_schematic(circuit, output)
    print(f"Wrote {out_path}")
    return 0
