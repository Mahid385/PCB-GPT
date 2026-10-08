from __future__ import annotations

from pathlib import Path
import runpy
import sys

from .model import Circuit


def load_circuit_from_script(script_path: str | Path) -> Circuit:
    """Execute a Python DSL file and return the Circuit it defines.

    The script may either define a global ``circuit`` or ``c`` variable, or a
    zero-argument ``build()`` function that returns a Circuit.
    """

    path = Path(script_path).resolve()
    if not path.exists():
        raise FileNotFoundError(path)
    original_sys_path = list(sys.path)
    try:
        sys.path.insert(0, str(path.parent))
        namespace = runpy.run_path(str(path), run_name="__circuit_dsl_input__")
    finally:
        sys.path = original_sys_path

    if callable(namespace.get("build")):
        circuit = namespace["build"]()
    else:
        circuit = namespace.get("circuit") or namespace.get("c")

    if not isinstance(circuit, Circuit):
        raise TypeError(
            f"{path} must define a Circuit named 'circuit' or 'c', "
            "or a build() function that returns one"
        )
    return circuit
