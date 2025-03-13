import tkinter as tk
from tkinter import ttk
import time


def process_measurement():
    global last_time
    new_time = time.time()
    delta = new_time - last_time
    last_time = new_time
    window.after(10, process_measurement)


if __name__ == "__main__":
    # Prepare a window for the GUI.
    window = tk.Tk()
    window.title("Encoder demo")
    window.geometry("600x400")
    window.resizable(False, False)

    # Prepare a frame inside the window.
    frame = ttk.Frame(window, padding="12 12 12 12")
    frame.grid(column=0, row=0, sticky=(tk.N, tk.W, tk.E, tk.S))
    window.columnconfigure(0, weight=1)
    window.rowconfigure(0, weight=1)

    # First row: Measurement status.
    status_frame = ttk.Frame(frame)
    status_frame.grid(row=0, column=0, sticky="W")
    status_label = ttk.Label(status_frame, text="Status: ")
    status_label.grid(row=0, column=0)
    status = tk.StringVar()
    status.set("OK")
    status_value = ttk.Label(status_frame, textvariable=status)
    status_value.grid(row=0, column=1)
    crc_label = ttk.Label(status_frame, text="CRC: ")
    crc_label.grid(row=0, column=2)
    crc = tk.StringVar()
    crc.set("OK")
    crc_value = ttk.Label(status_frame, textvariable=crc)
    crc_value.grid(row=0, column=3)

    # Second row: Measurement data.
    measurement_frame = ttk.Frame(frame)
    measurement_frame.grid(row=1, column=0, sticky="W")
    position_label = ttk.Label(measurement_frame, text="Pozicija: ")
    position_label.grid(row=0, column=0)
    # status = tk.StringVar()
    # status.set("OK")
    # status_value = ttk.Label(measurement_frame, textvariable=status)
    # status_value.grid(row=0, column=1)
    # crc_label = ttk.Label(measurement_frame, text="CRC: ")
    # crc_label.grid(row=0, column=2)
    # crc = tk.StringVar()
    # crc.set("OK")
    # crc_value = ttk.Label(measurement_frame, textvariable=crc)
    # crc_value.grid(row=0, column=3)

    # window.after_idle(process_measurement)
    window.mainloop()