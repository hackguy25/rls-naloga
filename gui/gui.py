import tkinter as tk
import math
from tkinter import ttk, font
from random import randint


SAMPLE_BITS = 18
MEASUREMENT_HISTORY = 200


# Dummy sample, for debugging.
# Each call adds a small random offset to the previous sample.
# Emulates a random walk around a circle.
def dummy_sample():
    global dval
    try:
        dval += randint(-5000, 5000) + 500
    except NameError:
        dval = 0
    dval %= 2**SAMPLE_BITS
    return dval


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
    (halfwidth, halfheight, _, _) = graph.coords(pointer_id)

    # Calculate the coordinates of the new measurement.
    phi = 2.0 * math.pi * measurement / 2**SAMPLE_BITS
    x = halfwidth * (1 + 0.8 * math.cos(phi))
    y = halfheight * (1 - 0.8 * math.sin(phi))

    # Reposition the indicator.
    graph.coords(pointer_id, halfwidth, halfheight, x, y)

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
        graph.create_line(right_edge - i * delta, bottom_edge - y_span * history[i] / 2**SAMPLE_BITS, right_edge - (i + 1) * delta, bottom_edge - y_span * history[i + 1] / 2**SAMPLE_BITS, fill="red")


# Read a measurement from the encoder and process it.
def process_measurement(bindings):
    value = dummy_sample()
    bindings["measurement_dec"].set(f"{value:6}")
    bindings["measurement_hex"].set(f"0x{value:05x}")

    degrees = 360.0 * value / 2**SAMPLE_BITS
    degrees_int = int(degrees)
    degrees_frac = degrees - degrees_int
    minutes = degrees_frac * 60
    minutes_int = int(minutes)
    minutes_frac = minutes - minutes_int
    seconds = minutes_frac * 60

    bindings["position_degrees"].set(f"{degrees:9.5f}°")
    bindings["position_dms"].set(f"{degrees_int:3}°{minutes_int:02}'{seconds:04.1f}\"")

    bindings["encoder_status"].set("OK")
    bindings["encoder_crc"].set("OK")

    history = bindings["measurement_history"]
    history.insert(0, value)
    history = history[:MEASUREMENT_HISTORY]

    update_compass(
        bindings["graph_compass"], bindings["graph_compass_indicator"], value
    )

    draw_history(bindings["graph_history"], history)

    window.after(10, process_measurement, bindings)


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

    # Prepare a frame inside the window.
    frame = ttk.Frame(window, padding="12 12 12 12")
    frame.grid(column=0, row=0, sticky=(tk.N, tk.W, tk.E, tk.S))
    window.columnconfigure(0, weight=1)
    window.rowconfigure(0, weight=1)

    # First row: Measurement status.
    bindings["encoder_status"] = tk.StringVar()
    bindings["encoder_crc"] = tk.StringVar()

    status_frame = ttk.Frame(frame)
    status_frame.grid(row=0, column=0, sticky="W")
    ttk.Label(status_frame, text="Status: ", font=font_bold).grid(row=0, column=0)
    ttk.Label(
        status_frame, textvariable=bindings["encoder_status"], font=font_base
    ).grid(row=0, column=1)
    ttk.Label(status_frame, text="   CRC: ", font=font_bold).grid(row=0, column=2)
    ttk.Label(status_frame, textvariable=bindings["encoder_crc"], font=font_base).grid(
        row=0, column=3
    )

    # Second row: Measurement data.
    bindings["measurement_dec"] = tk.StringVar()
    bindings["measurement_hex"] = tk.StringVar()
    bindings["position_degrees"] = tk.StringVar()
    bindings["position_dms"] = tk.StringVar()

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

    # Third row: Graphs.
    graphs_frame = ttk.Frame(frame, padding=(0, 12, 0, 0))
    graphs_frame.grid(row=2, column=0, sticky="W")

    bindings["graph_compass"] = tk.Canvas(
        graphs_frame, width=200, height=200, background="white"
    )
    bindings["graph_compass"].grid(row=0, column=0)
    bindings["graph_compass_indicator"] = draw_compass(bindings["graph_compass"])

    ttk.Label(graphs_frame, padding=(10, 0, 0, 0)).grid(row=0, column=1)
    bindings["graph_history"] = tk.Canvas(
        graphs_frame, width=400, height=200, background="white"
    )
    bindings["graph_history"].grid(row=0, column=2)

    # Start polling.
    window.after_idle(process_measurement, bindings)
    window.mainloop()
