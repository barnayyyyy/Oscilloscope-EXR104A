# Microelectonic Instrumentation - Spring 2023
# John Barney, Lucas Nichols, Adam Hubbard


# -------- Module Imports --------
import pyvisa as visa

# -------- Globals and Constants --------
# Addresses and connection types for connecting to the oscilloscope
KEYSIGHT_ADDRESS = "TCPIP0::169.254.205.81::INSTR"  # Try replacing IP address with "localhost": TCPIP0::localhost::INSTR
KEYSIGHT_UTCADDRESS = "TCPIP0::10.44.11.1::INSTR"

# Global timeout time in milliseconds (10s)
GLOBAL_TOUT = 10000

# -------- Initialize Oscilloscope Connection --------

# VISA Manager Install Directory (defaults to C:\\Windows\\System32\\visa32.dll)
rm = visa.ResourceManager()

# Setup which connection type desired
OS = rm.open_resource(KEYSIGHT_ADDRESS)

# Select a timeout time
OS.timeout = GLOBAL_TOUT

# Query to check if Oscilloscope connected properly
print(OS.query('*IDN?'))

# Clears instrument bus
OS.clear()
