"""
This project is designed to read and log CO2, humidity, and temperature data from a CozIR CO2 sensor
connected to a Raspberry Pi via the serial port. The collected data is timestamped and saved in a 
CSV file for further analysis or archiving. Additionally, the project includes real-time data visualization
using the Matplotlib library.

    created 11 June 2024
    by Vipul Naranbhai Jethwa
"""

import datetime
import time
import serial
import re
import csv
import matplotlib.pyplot as plt
from collections import deque
import os


#Initializing RPI GPIO 
import RPi.GPIO as GPIO
GPIO.setmode(GPIO.BOARD)
GPIO.setwarnings(False)

#GPIO Connectionns
Co2_valve = 31
GPIO.setup(Co2_valve, GPIO.OUT,initial=False)

# Open a serial connection with the specified parameters
serial_data = serial.Serial(port="/dev/ttyS0", baudrate=9600, parity=serial.PARITY_NONE, stopbits=serial.STOPBITS_ONE, bytesize=serial.EIGHTBITS, timeout=1)
print("serial_data", serial_data)

# Define a regular expression pattern to match the desired values
pattern = re.compile(r'H\s*(\d+)\s*T\s*(\d+)\s*Z\s*(\d+)')

# Default directory to log csv data
default_dir = "/home/cnce"

# Prompt the user for the file name and directory
file_name = input("Enter the file name (without extension): ")
file_dir = input("Enter the directory path (leave blank for default): ")

# Use the default directory if the user didn't provide one
if not file_dir:
    file_dir = default_dir

# Create the full file path
file_path = os.path.join(file_dir, f"{file_name}.csv")

# Create the directory if it doesn't exist
os.makedirs(os.path.dirname(file_path), exist_ok=True)

# Open the CSV file in append mode
with open(file_path, "a", newline="") as csvfile:
    fieldnames = ["Timestamp", "Data1", "Data2", "Data3"]
    writer = csv.DictWriter(csvfile, fieldnames=fieldnames)

def extract_values(data_str):
    """
    Extract humidity, temperature, and CO2 values from the received data string.

    Args:
        data_str (bytes): The received data from the serial port.

    Returns:
        tuple: A tuple containing the current timestamp, humidity value, temperature value, and CO2 value.
    """
    data_str = data_str.decode('utf-8')
    match = pattern.search(data_str)

    if match:
        h_value = (int(match.group(1))) /10
        t_value = ((int(match.group(2)))-1000) /10
        z_value = int(match.group(3))
        current_dtime = datetime.datetime.now()
        print(f"\r| CO2 | Cell Temp | Humidity | Date & Time", end="")
        print(f"\r| {z_value:^6}  | {t_value:^11} | {h_value:^15} | {current_dtime}", end="\n")
        return current_dtime, h_value, t_value, z_value
    else:
        return None, None, None, None

def plot_trends(data):
    """
    Plot the trends of humidity, temperature, and CO2 values over time.

    Args:
        data (deque): A deque containing tuples of timestamp, humidity value, temperature value, and CO2 value.
    """
    timestamps, h_values, t_values, z_values = zip(*data)

    # Clear the previous plot
    for ax in [ax1, ax2, ax3]:
        ax.clear()

    # Plot the trends on the respective subplots
    ax1.plot(timestamps, h_values, label='Humidity')
    ax2.plot(timestamps, t_values, label='Temperature')
    ax3.plot(timestamps, z_values, label='CO2')
   # Set titles and labels
    ax1.set_title('Humidity Value Trend')
    ax1.set_ylabel('Humidity (%)')
    ax1.legend()

    ax2.set_title('Temperature Value Trend')
    ax2.set_ylabel('Temperature (°C)')
    ax2.legend()

    ax3.set_title('CO2 Value Trend')
    ax3.set_xlabel('Time')
    ax3.set_ylabel('CO2 (ppm)')
    ax3.legend()
    # Adjust the x-axis limits
    ax3.set_xlim(min(timestamps), max(timestamps))

    
    # Show the plot
    plt.draw()
    plt.pause(0.01)

data = deque(maxlen=60)  # Store up to 60 data points
plot_interval = 10  # Plot the trends every 10 data points

# Create a figure with three subplots
fig, (ax1, ax2, ax3) = plt.subplots(3, 1, figsize=(8, 6), sharex=True)

while True:
    # Read data from the serial port
    sensor_data = serial_data.readline()
    current_dtime, h_value, t_value, z_value = extract_values(sensor_data)
    
    #Controlling the CO2 value inside Environment chamber 
    if 420 < z_value < 510:
        GPIO.output(Co2_valve, False)
        print("Co2_valve is OFF")
    else:
        GPIO.output(Co2_valve, True)
        print("Co2_valve is ON")
    
    if None not in (current_dtime, h_value, t_value, z_value):
        # Append the extracted values and timestamp to the data deque
        data.append((current_dtime, h_value, t_value, z_value))

        # Write the data to a CSV file
        with open(file_path, mode='a', newline='') as file:
            writer = csv.writer(file)
            writer.writerow([current_dtime, h_value, t_value, z_value])

        # Plot the trends if the data deque has enough entries
        if len(data) >= plot_interval:
            plot_trends(data)

# Close the serial connection when the script is terminated
serial_data.close()