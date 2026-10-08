from circuit_dsl import Circuit


def build() -> Circuit:
    c = Circuit("astable_555", title="NE555 Astable Oscillator")
    vcc, timing, discharge, control, output, led_anode, gnd = c.nets(
        "VCC TIMING DISCHARGE CONTROL OUT LED_A GND"
    )

    c.vcc("#PWR01", vcc, value="+5V", at=(35, 25))
    c.gnd("#PWR02", gnd, at=(50, 105))

    c.component(
        "U1",
        "NE555",
        {
            "1": gnd,
            "2": timing,
            "3": output,
            "4": vcc,
            "5": control,
            "6": timing,
            "7": discharge,
            "8": vcc,
        },
        pin_names={
            "1": "GND",
            "2": "TRIG",
            "3": "OUT",
            "4": "RESET",
            "5": "CTRL",
            "6": "THRESH",
            "7": "DISCH",
            "8": "VCC",
        },
        footprint="Package_DIP:DIP-8_W7.62mm",
        datasheet="https://www.ti.com/lit/ds/symlink/ne555.pdf",
        at=(85, 60),
    )

    c.resistor(
        "R1",
        "10k",
        vcc,
        discharge,
        footprint="Resistor_THT:R_Axial_DIN0207_L6.3mm_D2.5mm_P7.62mm_Horizontal",
        at=(45, 45),
        rotate=90,
    )
    c.resistor(
        "R2",
        "100k",
        discharge,
        timing,
        footprint="Resistor_THT:R_Axial_DIN0207_L6.3mm_D2.5mm_P7.62mm_Horizontal",
        at=(45, 70),
        rotate=90,
    )
    c.capacitor(
        "C1",
        "10u",
        timing,
        gnd,
        footprint="Capacitor_THT:CP_Radial_D5.0mm_P2.00mm",
        at=(45, 95),
        rotate=90,
    )
    c.capacitor(
        "C2",
        "10n",
        control,
        gnd,
        footprint="Capacitor_THT:C_Disc_D5.0mm_W2.5mm_P2.50mm",
        at=(120, 78),
        rotate=90,
    )
    c.resistor(
        "R3",
        "330",
        output,
        led_anode,
        footprint="Resistor_THT:R_Axial_DIN0207_L6.3mm_D2.5mm_P7.62mm_Horizontal",
        at=(125, 45),
    )
    c.led(
        "D1",
        "Blink",
        led_anode,
        gnd,
        footprint="LED_THT:LED_D5.0mm",
        at=(150, 45),
    )
    c.connector(
        "J1",
        [vcc, output, gnd],
        value="POWER_OUT",
        footprint="Connector_PinHeader_2.54mm:PinHeader_1x03_P2.54mm_Vertical",
        at=(165, 76),
    )
    c.gnd("#PWR03", gnd, at=(150, 62))

    return c
