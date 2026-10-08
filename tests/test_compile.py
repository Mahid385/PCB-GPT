from __future__ import annotations

from pathlib import Path
import tempfile
import unittest

from circuit_dsl import Circuit, emit_schematic, load_circuit_from_script
from circuit_dsl.symbols import resistor_symbol


class CompilerTests(unittest.TestCase):
    def test_emits_modern_kicad_schematic(self) -> None:
        c = Circuit("divider")
        vin, vout, gnd = c.nets("VIN VOUT GND")
        c.vcc("#PWR01", vin, value="+5V")
        c.resistor("R1", "10k", vin, vout)
        c.resistor("R2", "10k", vout, gnd)
        c.gnd("#PWR02", gnd)

        schematic = emit_schematic(c)

        self.assertIn("(kicad_sch", schematic)
        self.assertIn("(version 20211123)", schematic)
        self.assertIn('(generator circuit_dsl_kicad)', schematic)
        self.assertIn('(symbol "CircuitDSL:R"', schematic)
        self.assertIn('(symbol (lib_id "CircuitDSL:R")', schematic)
        self.assertIn('(label "VIN"', schematic)
        self.assertIn('(label "VOUT"', schematic)
        self.assertIn('(sheet_instances', schematic)
        self.assertEqual(schematic.count("("), schematic.count(")"))

    def test_loads_script_build_function(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            script = Path(tmp) / "input.py"
            script.write_text(
                "from circuit_dsl import Circuit\n"
                "def build():\n"
                "    c = Circuit('scripted')\n"
                "    a, b = c.nets('A B')\n"
                "    c.resistor('R1', '1k', a, b)\n"
                "    return c\n",
                encoding="utf-8",
            )

            c = load_circuit_from_script(script)

        self.assertEqual(c.name, "scripted")
        self.assertEqual(len(c.parts), 1)

    def test_astable_example_exercises_compiler_features(self) -> None:
        example_path = Path(__file__).resolve().parents[1] / "examples" / "astable_555.py"

        c = load_circuit_from_script(example_path)
        schematic = emit_schematic(c)

        self.assertEqual(c.name, "astable_555")
        self.assertIn('(title "NE555 Astable Oscillator")', schematic)
        self.assertIn('(symbol (lib_id "CircuitDSL:U1")', schematic)
        self.assertIn('(property "Footprint" "Package_DIP:DIP-8_W7.62mm"', schematic)
        self.assertIn('(label "TIMING"', schematic)
        self.assertIn('(label "OUT"', schematic)
        self.assertIn('(label "LED_A"', schematic)
        self.assertIn('(symbol (lib_id "CircuitDSL:LED")', schematic)
        self.assertEqual(schematic.count("("), schematic.count(")"))

    def test_existing_controller_example_compiles(self) -> None:
        example_path = Path(__file__).resolve().parents[1] / "examples" / "voltage_divider.py"

        c = load_circuit_from_script(example_path)
        schematic = emit_schematic(c)

        self.assertEqual(c.name, "esp32_relay_controller")
        self.assertIn('(title "ESP32-S3 Relay & Temperature Controller")', schematic)
        self.assertIn('(symbol (lib_id "CircuitDSL:U1")', schematic)
        self.assertIn('(symbol (lib_id "CircuitDSL:K1")', schematic)
        self.assertIn('(label "GPIO0"', schematic)
        self.assertIn('(label "RELAY_GATE"', schematic)
        self.assertEqual(schematic.count("("), schematic.count(")"))

    def test_rejects_unknown_pin(self) -> None:
        c = Circuit("bad")
        with self.assertRaises(ValueError):
            c.add_part("R1", "10k", resistor_symbol(), {"3": "A"})


if __name__ == "__main__":
    unittest.main()
