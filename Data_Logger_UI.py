#This is the data logger for the ORNA Solar Car Project, Its designed to run on Rasperry Pi 4b.
#It collects the data serially through the ttys0 port, It saves it and presents it in a real time updating GUI, with buttons to plot it.
import tkinter as tk
from tkinter import ttk
import serial
import csv
from datetime import datetime, date
import time
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import concurrent.futures
import threading

# Create the main GUI window
root = tk.Tk()
root.title("Serial Data Logger")

# Get screen dimensions
screen_width = root.winfo_screenwidth()
screen_height = root.winfo_screenheight()

# Set the main window size to match the screen
root.geometry(f"{screen_width}x{screen_height}")

# Create a frame to hold the data labels, data values, and plot buttons
data_frame = ttk.Frame(root)
data_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)  # Add padding for touch-friendly tapping

# Data column labels
column_labels = ["Timestamp", "Ah", "Voltage (V)", "Current (A)", "Power (Watt)", "Speed (m/s)",
                 "Distance (m)", "Degree (°)", "RPM (Rounds/Minute)", "Throttle Out", "Throttle In",
                 "AuxA", "AuxD", "Flgs"]

# Define grid background colors to simulate grid lines
bg_color = "#cccccc"  # Light gray
header_bg_color = "#bbbbbb"  # Slightly darker gray

# Create labels for data values, arrange them in a table-like format
value_labels = []
plot_buttons = []

# Create rows for data values and buttons
for i, label_text in enumerate(column_labels):
    label = ttk.Label(data_frame, text=label_text, font=("Arial", 12, "bold"), background=header_bg_color)
    label.grid(row=0, column=i, padx=5, pady=5, sticky="ew")  # Extend label to fill both horizontal directions

    if i != 0:  # Exclude the timestamp label
        value_label = ttk.Label(data_frame, text="", font=("Arial", 12), background=bg_color)
        value_label.grid(row=1, column=i, padx=5, pady=5, sticky="ew")  # Extend value label to fill both horizontal directions
        value_labels.append(value_label)

        plot_button = ttk.Button(data_frame, text="Plot", state=tk.DISABLED, width=8,
                                 command=lambda i=i: plot_data(i))
        plot_button.grid(row=2, column=i, padx=5, pady=5, sticky="ew")  # Extend plot button to fill both horizontal directions
        plot_buttons.append(plot_button)

# Create a timestamp label and function to update it
timestamp_label = ttk.Label(data_frame, text="", font=("Arial", 12), background=bg_color)
timestamp_label.grid(row=1, column=0, padx=5, pady=5, sticky="ew")

def update_timestamp_label():
    current_time = datetime.now().strftime("%H:%M:%S")
    timestamp_label.config(text=current_time)
    root.after(1000, update_timestamp_label)  # Update every 1 second (1000 milliseconds)

# Call the function to start updating the timestamp label
update_timestamp_label()

# Create a CSV file with headers
current_date = date.today().strftime("%Y-%m-%d")
csv_filename = f"serial_data_{current_date}.csv"

with open(csv_filename, 'w', newline='') as csvfile:
    csv_writer = csv.writer(csvfile, delimiter='\t')
    csv_writer.writerow(column_labels)

ser = serial.Serial('/dev/ttyS0', 9600, timeout=1)

def read_serial_data():
    try:
        while True:
            serial_data = ser.readline().decode().strip().split('\t')
            if len(serial_data) == 12:
                timestamp = datetime.now().strftime("%H:%M:%S")
                current, voltage = float(serial_data[2]), float(serial_data[1])
                power = round(current * voltage, 2)
                serial_data.insert(0, timestamp)
                serial_data.insert(3, power)
                with open(csv_filename, 'a', newline='') as csvfile:
                    csv_writer = csv.writer(csvfile, delimiter='\t')
                    csv_writer.writerow(serial_data)
                update_gui(serial_data)
    except KeyboardInterrupt:
        ser.close()

def update_gui(data):
    for i in range(len(data)):
        value_labels[i].config(text=data[i])
        if i != 0:  # Exclude the timestamp value
            plot_buttons[i].config(state=tk.NORMAL)  # Enable plot buttons

def plot_data(value_index):
    with open(csv_filename, 'r') as csvfile:
        reader = csv.reader(csvfile, delimiter='\t')
        next(reader)  # Skip header row
        timestamps = []
        values = []
        for row in reader:
            timestamps.append(row[0])
            values.append(float(row[value_index]))

    plt.figure(figsize=(8, 4))
    plt.plot(timestamps, values)
    plt.xlabel("Timestamp")
    plt.ylabel(value_labels[value_index]["text"])
    plt.title(f"{value_labels[value_index]['text']} vs Time")
    plt.xticks(rotation=45)
    plt.tight_layout()

    fig = plt.gcf()
    canvas = FigureCanvasTkAgg(fig, master=root)
    canvas.get_tk_widget().pack(side=tk.TOP, fill=tk.BOTH, expand=1)
    canvas.draw()

    # Bind a callback function to handle plot window closure
    def on_closing():
        root.deiconify()  # Restore the main window
        fig.clear()  # Clear the plot
        canvas.get_tk_widget().destroy()  # Destroy the plot canvas
    fig.canvas.mpl_connect('close_event', lambda event: on_closing())

    # Hide the main window while the plot is open
    root.iconify()

# Add a close button at the bottom center of the window
close_button = ttk.Button(root, text="Close", command=root.quit)
close_button.pack(side=tk.BOTTOM, pady=20, anchor=tk.CENTER)

# Start the serial data reading in a separate thread
serial_thread = threading.Thread(target=read_serial_data)
serial_thread.daemon = True  # Exit the thread when the main program exits
serial_thread.start()

# Start the main GUI loop
root.mainloop()
