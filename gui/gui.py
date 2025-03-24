import tkinter as tk
import math
import serial
from tkinter import ttk, font
from random import randint


# How wide is the measurement.
SAMPLE_BITS = 18
# How many measurement should be retained for the graph.
MEASUREMENT_HISTORY = 300
# How much time (in ms) should pass between measurements.
MEASUREMENT_DELAY = 5
# Path to or the name of the Nucleo serial interface.
# On Linux this is usually "/dev/ttyACM0", on Windows it might be "COM1".
SERIAL_DEVICE_PATH = "/dev/ttyACM0"


# Poll the encoder over the serial connection.
# If the measurement is recovered successfully, it is returned as a list of bytes.
# If an error occurs, only an error message is returned.
def poll_serial(input: serial.Serial) -> tuple[str, list | None]:
    # Clear any junk left in the buffer.
    input.read_all()
    # Send a byte to request a fresh measurement.
    input.write(b" ")
    line = input.readline().decode().strip()

    # A valid measurement consists of an "ok" and 6 hex bytes, separated with spaces.
    # E.g. "ok 00 03 08 f6 43 eb"
    # Validate the measurement form.
    line = line.split(" ")
    if len(line) != 7 or line[0] != "ok":
        return ("Error reading sample", None)

    # Extract the 6 bytes.
    # To simplify the implementation, we assume that if a byte
    # can be successfully parsed, it is valid.
    # Otherwise, treat the whole measurement as invalid.
    sample = []
    for x in line[1:7]:
        try:
            sample.append(int(x, 16))
        except:
            return ("Error reading sample", None)

    return ("OK", sample)


# Lookup table for 0x97 polynomial.
# Source: Application note CRCD01.
# fmt: off
crc_lut = [
    0x00, 0x97, 0xB9, 0x2E, 0xE5, 0x72, 0x5C, 0xCB, 0x5D, 0xCA, 0xE4, 0x73, 0xB8, 0x2F, 0x01, 0x96,
    0xBA, 0x2D, 0x03, 0x94, 0x5F, 0xC8, 0xE6, 0x71, 0xE7, 0x70, 0x5E, 0xC9, 0x02, 0x95, 0xBB, 0x2C,
    0xE3, 0x74, 0x5A, 0xCD, 0x06, 0x91, 0xBF, 0x28, 0xBE, 0x29, 0x07, 0x90, 0x5B, 0xCC, 0xE2, 0x75,
    0x59, 0xCE, 0xE0, 0x77, 0xBC, 0x2B, 0x05, 0x92, 0x04, 0x93, 0xBD, 0x2A, 0xE1, 0x76, 0x58, 0xCF,
    0x51, 0xC6, 0xE8, 0x7F, 0xB4, 0x23, 0x0D, 0x9A, 0x0C, 0x9B, 0xB5, 0x22, 0xE9, 0x7E, 0x50, 0xC7,
    0xEB, 0x7C, 0x52, 0xC5, 0x0E, 0x99, 0xB7, 0x20, 0xB6, 0x21, 0x0F, 0x98, 0x53, 0xC4, 0xEA, 0x7D,
    0xB2, 0x25, 0x0B, 0x9C, 0x57, 0xC0, 0xEE, 0x79, 0xEF, 0x78, 0x56, 0xC1, 0x0A, 0x9D, 0xB3, 0x24,
    0x08, 0x9F, 0xB1, 0x26, 0xED, 0x7A, 0x54, 0xC3, 0x55, 0xC2, 0xEC, 0x7B, 0xB0, 0x27, 0x09, 0x9E,
    0xA2, 0x35, 0x1B, 0x8C, 0x47, 0xD0, 0xFE, 0x69, 0xFF, 0x68, 0x46, 0xD1, 0x1A, 0x8D, 0xA3, 0x34,
    0x18, 0x8F, 0xA1, 0x36, 0xFD, 0x6A, 0x44, 0xD3, 0x45, 0xD2, 0xFC, 0x6B, 0xA0, 0x37, 0x19, 0x8E,
    0x41, 0xD6, 0xF8, 0x6F, 0xA4, 0x33, 0x1D, 0x8A, 0x1C, 0x8B, 0xA5, 0x32, 0xF9, 0x6E, 0x40, 0xD7,
    0xFB, 0x6C, 0x42, 0xD5, 0x1E, 0x89, 0xA7, 0x30, 0xA6, 0x31, 0x1F, 0x88, 0x43, 0xD4, 0xFA, 0x6D,
    0xF3, 0x64, 0x4A, 0xDD, 0x16, 0x81, 0xAF, 0x38, 0xAE, 0x39, 0x17, 0x80, 0x4B, 0xDC, 0xF2, 0x65,
    0x49, 0xDE, 0xF0, 0x67, 0xAC, 0x3B, 0x15, 0x82, 0x14, 0x83, 0xAD, 0x3A, 0xF1, 0x66, 0x48, 0xDF,
    0x10, 0x87, 0xA9, 0x3E, 0xF5, 0x62, 0x4C, 0xDB, 0x4D, 0xDA, 0xF4, 0x63, 0xA8, 0x3F, 0x11, 0x86,
    0xAA, 0x3D, 0x13, 0x84, 0x4F, 0xD8, 0xF6, 0x61, 0xF7, 0x60, 0x4E, 0xD9, 0x12, 0x85, 0xAB, 0x3C
]
# fmt: on


# Check the CRC.
# The final byte of the sample is the inverted CRC,
# so to pass we need a byte of all 1's: 255.
# Source: Adapted from application note CRCD01.
def check_crc(sample) -> bool:
    crc = 0
    for byte in sample:
        crc = byte ^ crc_lut[crc]
    return crc == 255


# Draw a compass graph showing the position of the encoder.
def draw_compass(graph: tk.Canvas) -> int:
    width = graph.winfo_reqwidth()
    height = graph.winfo_reqheight()
    halfwidth = width / 2
    halfheight = height / 2

    # Draw the circular frame.
    graph.create_oval(0.1 * width, 0.1 * height, 0.9 * width, 0.9 * height, width=3)

    # Draw the ticks every 15 degrees.
    for i in range(0, 360, 5):
        phi = math.pi * i / 180.0
        x = math.cos(phi)
        y = math.sin(phi)
        weight = 1
        if i % 45 == 0:
            weight = 3
        graph.create_line(
            halfwidth * (1 + 0.8 * x),
            halfheight * (1 - 0.8 * y),
            halfwidth * (1 + 0.87 * x),
            halfheight * (1 - 0.87 * y),
            width=weight,
        )

    # Draw text markers on large ticks.
    graph.create_text(halfwidth * 1.75, halfheight, text="0", anchor="e")
    graph.create_text(halfwidth, halfheight * 0.25, text="90", anchor="n")
    graph.create_text(halfwidth * 0.25, halfheight, text="180", anchor="w")
    graph.create_text(halfwidth, halfheight * 1.75, text="270", anchor="s")

    # Draw the pointer arrow.
    pointer = graph.create_line(
        halfwidth, halfheight, halfwidth * (1.88), halfheight, arrow="last"
    )
    return pointer


# Update the compass indicator to correspond to the new measurement.
def update_compass(graph: tk.Canvas, pointer_id, measurement):
    # Find the extent of the canvas.
    halfwidth = graph.winfo_width() / 2
    halfheight = graph.winfo_height() / 2

    # Calculate the coordinates of the new measurement.
    phi = 2.0 * math.pi * measurement / 2**SAMPLE_BITS
    x_end = halfwidth * (1 + 0.8 * math.cos(phi))
    y_end = halfheight * (1 - 0.8 * math.sin(phi))

    # Reposition the indicator.
    graph.coords(pointer_id, halfwidth, halfheight, x_end, y_end)


# Draw the measurement history as a line graph.
def draw_history(graph: tk.Canvas, history):
    width = graph.winfo_reqwidth()
    height = graph.winfo_reqheight()
    graph.delete("all")

    # Draw the axis markers.
    graph.create_line(15, height - 10, 15, 10, arrow="last")
    graph.create_line(10, height - 15, width - 10, height - 15, arrow="last")
    graph.create_line(16, 20, width - 20, 20, fill="light grey")

    # Draw the history graph.
    delta = (width - 36) / (MEASUREMENT_HISTORY - 1)
    right_edge = width - 20
    y_span = height - 35.0
    bottom_edge = height - 15
    for i in range(len(history) - 1):
        graph.create_line(
            right_edge - i * delta,
            bottom_edge - y_span * history[i] / 2**SAMPLE_BITS,
            right_edge - (i + 1) * delta,
            bottom_edge - y_span * history[i + 1] / 2**SAMPLE_BITS,
            fill="red",
        )


# Read a measurement from the encoder and process it.
def process_measurement(bindings):
    # Poll the encoder.
    (status, value) = poll_serial(bindings["serial"])

    # Set the status.
    bindings["encoder_status"].set(status)

    if value is None:
        # Polling failed.
        # Clear out integrity values, retain the previous measurement.
        bindings["encoder_crc"].set("X")
        bindings["encoder_error"].set("X")
        bindings["encoder_warning"].set("X")
        history = bindings["measurement_history"]
        history.insert(0, history[0])
        history = history[:MEASUREMENT_HISTORY]

        # Queue up next polling.
        window.after(MEASUREMENT_DELAY, process_measurement, bindings)
        return

    # Extract the values from the measurement.
    crc = check_crc(value)
    turns = value[0] * 256 + value[1]
    if turns > 0x8000:
        turns -= 0x10000
    position = (value[2] * 256 + value[3]) * 256 + (value[4] & 0xFC)
    position = position >> (24 - SAMPLE_BITS)
    error = "T" if value[4] & 0x02 == 0 else "F"
    warning = "T" if value[4] & 0x01 == 0 else "F"

    # Present the integrity values.
    if crc:
        bindings["encoder_crc"].set("OK")
    else:
        bindings["encoder_crc"].set("FAIL")
    bindings["encoder_error"].set(error)
    bindings["encoder_warning"].set(warning)

    # Calculate the degrees, minutes and seconds from the measurement.
    degrees = 360.0 * position / 2**SAMPLE_BITS
    degrees_int = int(degrees)
    degrees_frac = degrees - degrees_int
    minutes = degrees_frac * 60
    minutes_int = int(minutes)
    minutes_frac = minutes - minutes_int
    seconds = minutes_frac * 60

    # Present the measurement values.
    bindings["measurement_dec"].set(f"{position:6}")
    bindings["measurement_hex"].set(f"0x{position:05x}")

    bindings["position_degrees"].set(f"{degrees:9.5f}°")
    bindings["position_dms"].set(f"{degrees_int:3}°{minutes_int:02}'{seconds:04.1f}\"")
    bindings["position_turns"].set(f"{turns: 3}")

    # Update the measurement history.
    history = bindings["measurement_history"]
    history.insert(0, position)
    history = history[:MEASUREMENT_HISTORY]

    # Update the graphs.
    update_compass(
        bindings["graph_compass"], bindings["graph_compass_indicator"], position
    )
    draw_history(bindings["graph_history"], history)

    # Queue up next polling.
    window.after(MEASUREMENT_DELAY, process_measurement, bindings)


if __name__ == "__main__":
    # Prepare a window for the GUI.
    window = tk.Tk()
    window.title("Encoder demo")
    window.resizable(False, False)

    # Prepare fonts.
    font_size = 12
    font_base = font.nametofont("TkTextFont").copy()
    font_base.config(size=font_size)
    font_bold = font.nametofont("TkTextFont").copy()
    font_bold.config(size=font_size, weight="bold")
    font_mono = font.nametofont("TkFixedFont").copy()
    font_mono.config(size=font_size)

    # Prepare a bindings container.
    # This container will be passed on the the update function.
    bindings = dict()
    bindings["measurement_history"] = list()

    # Open the Nucleo's serial port.
    ser = serial.Serial(SERIAL_DEVICE_PATH, 115200)
    bindings["serial"] = ser

    # Prepare a frame inside the window.
    frame = ttk.Frame(window, padding="12 12 12 12")
    frame.grid(column=0, row=0, sticky=(tk.N, tk.W, tk.E, tk.S))
    window.columnconfigure(0, weight=1)
    window.rowconfigure(0, weight=1)

    # First row: Measurement status.
    bindings["encoder_status"] = tk.StringVar()
    bindings["encoder_crc"] = tk.StringVar()
    bindings["encoder_error"] = tk.StringVar()
    bindings["encoder_warning"] = tk.StringVar()

    status_frame = ttk.Frame(frame)
    status_frame.grid(row=0, column=0, sticky="W")
    ttk.Label(status_frame, text="Status: ", font=font_bold).grid(row=0, column=0)
    ttk.Label(
        status_frame,
        textvariable=bindings["encoder_status"],
        font=font_base,
    ).grid(row=0, column=1)
    ttk.Label(status_frame, text="   CRC: ", font=font_bold).grid(row=0, column=2)
    ttk.Label(status_frame, textvariable=bindings["encoder_crc"], font=font_base).grid(
        row=0, column=3
    )
    ttk.Label(status_frame, text="   E: ", font=font_bold).grid(row=0, column=4)
    ttk.Label(
        status_frame, textvariable=bindings["encoder_error"], font=font_base
    ).grid(row=0, column=5)
    ttk.Label(status_frame, text="   W: ", font=font_bold).grid(row=0, column=6)
    ttk.Label(
        status_frame, textvariable=bindings["encoder_warning"], font=font_base
    ).grid(row=0, column=7)

    # Second row: Measurement data.
    bindings["measurement_dec"] = tk.StringVar()
    bindings["measurement_hex"] = tk.StringVar()
    bindings["position_degrees"] = tk.StringVar()
    bindings["position_dms"] = tk.StringVar()
    bindings["position_turns"] = tk.StringVar()

    measurement_frame = ttk.Frame(frame)
    measurement_frame.grid(row=1, column=0, sticky="W")
    ttk.Label(measurement_frame, text="Pozicija:  ", font=font_bold).grid(
        row=0, column=0
    )
    ttk.Label(
        measurement_frame,
        textvariable=bindings["measurement_dec"],
        font=font_mono,
    ).grid(row=0, column=1)
    ttk.Label(measurement_frame, text=" | ", font=font_base).grid(row=0, column=2)
    ttk.Label(
        measurement_frame,
        textvariable=bindings["measurement_hex"],
        font=font_mono,
    ).grid(row=0, column=3)
    ttk.Label(measurement_frame, text="   =>   ", font=font_base).grid(row=0, column=4)
    ttk.Label(
        measurement_frame,
        textvariable=bindings["position_degrees"],
        font=font_mono,
    ).grid(row=0, column=5)
    ttk.Label(measurement_frame, text=" | ", font=font_base).grid(row=0, column=6)
    ttk.Label(
        measurement_frame,
        textvariable=bindings["position_dms"],
        font=font_mono,
    ).grid(row=0, column=7)
    ttk.Label(measurement_frame, text="   Obratov:  ", font=font_bold).grid(
        row=0, column=8
    )
    ttk.Label(
        measurement_frame,
        textvariable=bindings["position_turns"],
        font=font_mono,
    ).grid(row=0, column=9)

    # Third row: Graphs.
    graphs_frame = ttk.Frame(frame, padding=(0, 12, 0, 0))
    graphs_frame.grid(row=2, column=0, sticky="W")

    bindings["graph_compass"] = tk.Canvas(
        graphs_frame, width=250, height=250, background="white"
    )
    bindings["graph_compass"].grid(row=0, column=0)
    bindings["graph_compass_indicator"] = draw_compass(bindings["graph_compass"])

    ttk.Label(graphs_frame, padding=(10, 0, 0, 0)).grid(row=0, column=1)
    bindings["graph_history"] = tk.Canvas(
        graphs_frame, width=500, height=250, background="white"
    )
    bindings["graph_history"].grid(row=0, column=2)

    # Start polling.
    window.after_idle(process_measurement, bindings)
    window.mainloop()
