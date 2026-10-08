from circuit_dsl import Circuit


def build() -> Circuit:
    c = Circuit(
        "esp32_relay_controller",
        title="ESP32-S3 Relay & Temperature Controller"
    )

    # ---------------------------------------------------------
    # POWER NETS
    # ---------------------------------------------------------
    usb5v, v3v3, relay12v, gnd = c.nets(
        "USB_5V 3V3 RELAY_12V GND"
    )

    # USB 5V input
    c.connector(
        "J1",
        ["USB_5V", "USB_D-", "USB_D+", "GND"],
        value="USB Type-B",
        at=(25, 30)
    )

    # 5V -> 3.3V regulator for ESP32-S3
    c.regulator(
        "U2",
        regulator="3V3",
        vin=usb5v,
        vout=v3v3,
        gnd=gnd,
        at=(55, 25)
    )

    # ---------------------------------------------------------
    # ESP32-S3
    # ---------------------------------------------------------
    c.esp32(
        "U1",
        variant="ESP32-S3",
        at=(95, 50)
    )

    # ---------------------------------------------------------
    # USB CONNECTION
    #
    # USB D- -> GPIO19
    # USB D+ -> GPIO20
    # ---------------------------------------------------------
    c.resistor(
        "RUSB1",
        "22R",
        "USB_D-",
        "GPIO19",
        at=(55, 42)
    )

    c.resistor(
        "RUSB2",
        "22R",
        "USB_D+",
        "GPIO20",
        at=(55, 47)
    )

    # ---------------------------------------------------------
    # USB / ESP32 POWER
    # ---------------------------------------------------------
    c.connect(v3v3, "U1.3V3")
    c.connect(gnd, "U1.GND")

    c.capacitor(
        "C1",
        "100n",
        v3v3,
        gnd,
        at=(75, 20)
    )

    c.capacitor(
        "C2",
        "10u",
        v3v3,
        gnd,
        at=(85, 20)
    )

    # ---------------------------------------------------------
    # TEMPERATURE SENSOR
    #
    # DS18B20 DATA -> GPIO0
    # ---------------------------------------------------------
    c.sensor(
        "U3",
        sensor="DS18B20",
        data="GPIO0",
        vcc=v3v3,
        gnd=gnd,
        at=(35, 75)
    )

    # Required 1-Wire pull-up
    c.resistor(
        "R1",
        "4.7k",
        v3v3,
        "GPIO0",
        at=(45, 68)
    )

    # GPIO0 boot/strap button
    c.push_button(
        "SW_BOOT",
        "GPIO0",
        gnd,
        value="BOOT",
        at=(25, 85)
    )

    # ---------------------------------------------------------
    # OLED
    #
    # GPIO4 -> SCL
    # GPIO5 -> SDA
    # GPIO6 -> RESET
    # ---------------------------------------------------------
    c.oled(
        "OLED1",
        controller="SSD1306",
        interface="I2C",
        scl="GPIO4",
        sda="GPIO5",
        reset="GPIO6",
        vcc=v3v3,
        gnd=gnd,
        at=(125, 35)
    )

    # I2C pull-ups
    c.resistor(
        "R2",
        "4.7k",
        v3v3,
        "GPIO4",
        at=(115, 20)
    )

    c.resistor(
        "R3",
        "4.7k",
        v3v3,
        "GPIO5",
        at=(125, 20)
    )

    # ---------------------------------------------------------
    # RELAY DRIVER
    #
    # GPIO3 -> gate resistor -> NMOS
    # NMOS switches 12 V relay coil
    # ---------------------------------------------------------
    c.resistor(
        "R4",
        "100R",
        "GPIO3",
        "RELAY_GATE",
        at=(75, 78)
    )

    c.resistor(
        "R5",
        "100k",
        "RELAY_GATE",
        gnd,
        at=(80, 88)
    )

    c.mosfet(
        "Q1",
        "AO3400A",
        gate="RELAY_GATE",
        source=gnd,
        drain="RELAY_COIL_LOW",
        at=(90, 78)
    )

    # Relay coil
    c.relay(
        "K1",
        coil_voltage="12V",
        coil_pos=relay12v,
        coil_neg="RELAY_COIL_LOW",
        contact_com="RELAY_COM",
        contact_no="RELAY_NO",
        contact_nc="RELAY_NC",
        at=(115, 75)
    )

    # Flyback diode
    c.diode(
        "D1",
        "1N4007",
        anode="RELAY_COIL_LOW",
        cathode=relay12v,
        at=(105, 65)
    )

    # ---------------------------------------------------------
    # RELAY POWER
    # ---------------------------------------------------------
    c.connector(
        "J2",
        [relay12v, gnd],
        value="12V_IN",
        at=(35, 100)
    )

    # ---------------------------------------------------------
    # LED 1
    # GPIO7
    # ---------------------------------------------------------
    c.resistor(
        "R6",
        "1k",
        "GPIO7",
        "LED1_A",
        at=(130, 100)
    )

    c.led(
        "LED1",
        "STATUS",
        anode="LED1_A",
        cathode=gnd,
        at=(145, 100)
    )

    # ---------------------------------------------------------
    # LED 2
    # GPIO8
    # ---------------------------------------------------------
    c.resistor(
        "R7",
        "1k",
        "GPIO8",
        "LED2_A",
        at=(130, 110)
    )

    c.led(
        "LED2",
        "RELAY_STATUS",
        anode="LED2_A",
        cathode=gnd,
        at=(145, 110)
    )

    # ---------------------------------------------------------
    # GROUND SYMBOL
    # ---------------------------------------------------------
    c.gnd(
        "#PWR01",
        gnd,
        at=(70, 120)
    )

    return c