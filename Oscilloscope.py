# Microelectonic Instrumentation - Spring 2023
# John Barney, Lucas Nichols, Adam Hubbard

# =============================================
# Module Imports
# =============================================
import pyvisa as visa
import string
import struct
import sys
import time

# =============================================
# Globals and Constants
# =============================================

# Addresses and connection types for connecting to the oscilloscope
KEYSIGHT_ADDRESS = "TCPIP0::169.254.205.81::hislip0::INSTR"
KEYSIGHT_UTCADDRESS = "TCPIP0::10.44.11.1::INSTR"

# Global timeout time in milliseconds (10s)
GLOBAL_TOUT = 10000


# ====================================================================
# OS Setup test:
# ====================================================================

# Writes command to oscilloscope
def tx(command):
    OS.write("%s" % command)

# Writes IEEE block to oscilloscope
def tx_block(command):
    OS.write_binary_values("%s " % command, values, datatype='B')
    check_instrument_errors(command)

# Queries oscilloscope for string return
def rx_str(query):
    result = OS.query("%s" % query)
    check_instrument_errors(query)
    return result

# Queries oscilloscope for numeric return
def rx_num(query):
    results = OS.query("%s" % query)
    check_instrument_errors(query)
    return float(results)

# Queries oscilloscope for ASCIi return
def rx_ascii(query):
    results = OS.query_ascii_values("%s" % query)
    check_instrument_errors(query)
    results = results[0]        # Results passed into a list for ascii queries
    return results

# Setup parameters for existing test (February 7, 2023)
# ** This is a temporary setup for code testing purposes **
def os_parameters():

    # Set probe attenuation
    tx(":CHANnel1:PROBe 1.0")

    # Set voltage window range
    tx(":CHANnel1:RANGe 800E-3")

    # Set voltage scale to 200mV/div
    tx(":CHANnel1:SCALe 200E-3")

    # Autoscales oscilloscope for channels currently used
    # tx(":AUToscale:CHANnels DISPlayed")
    # tx(":AUToscale")

    # Centers timebase
    tx(":TIMebase:POSition")

    # Set timebase range to 2ms
    tx(":TIMebase:RANGe 2E-3")

    # Sets timebase scale to 200us/div
    tx(":TIMebase:SCALe 200E-6")

    # Displays message on oscilloscope
    # tx(":SYSTem:DSP 'Test 1'")

    # Define trigger mode
    tx(":TRIGger:MODE WINDow")

    # Set trigger source
    tx(":TRIGger:WINDow:SOURce CHANnel1")

    tx(":TRIGger:WINDow:CONDition EXIT")





# ====================================================================
# Check for instrument errors:
# ====================================================================

# Error checking code written by Keysight via:
# Keysight Infiniium MXR/EXR-Series Oscilloscopes Programmer's Guide 2023 Edition

def check_instrument_errors(command, exit_on_error=True):
    while True:
        error_string = OS.query(":SYSTem:ERRor? STRing")
        if error_string: # If there is an error string value.
            if error_string.find("0,", 0, 2) == -1: # Not "No error".
                print("ERROR: %s, command: '%s'" % (error_string, command))
                if exit_on_error:
                    print("Exited because of error.")
                    sys.exit(1)
            else:
                # "No error"
                break
        else:
            # :SYSTem:ERRor? STRing should always return string.
            print("ERROR: :SYSTem:ERRor? STRing returned nothing, command: '%s'"% command)
            print("Exited because of error.")
            sys.exit(1)

# =============================================
# Initialize Oscilloscope Connection
# =============================================

# class setup:
#     def __init__(self):
#     self.name = name


def initialize():
    # Query to check if Oscilloscope connected properly, print the identification string:
    idn_string = OS.query("*IDN?")
    print("Oscilloscope connected: %s" % idn_string)

    # Clear status.
    # OS.write("*CLS")

    # Load default setup, clears previous settings (Note: NOT a factory reset)
    # OS.write("*RST")


# =============================================
# Main loop
# =============================================
# VISA Manager Install Directory (defaults to C:\\Windows\\System32\\visa32.dll)
rm = visa.ResourceManager()

# Setup which connection type desired
OS = rm.open_resource(KEYSIGHT_ADDRESS)

# Select a timeout time
OS.timeout = GLOBAL_TOUT

# Clears instrument bus
# OS.clear()

# check_instrument_errors()
initialize()

# Define trigger mode
tx(":TRIGger:MODE WINDow")

tx(":TRIGger:HTHReshold CHANnel1 200E-3")
tx(":TRIGger:LTHReshold CHANnel1 -200E-3")

# Set trigger source
tx(":TRIGger:WINDow:SOURce CHANnel1")
test = rx_ascii(":TRIGger:LTHReshold? CHANnel1")
print(test)
tx(":TRIGger:WINDow:CONDition EXIT")

# # Trigger Count Test Code
# i = 0
# infCT = rx_num(":COUNter3:CURRent?")
#
# while i < 7 or infCT > 9.9*10**36:
#     CHAN1_trigcount = rx_num(":COUNter3:CURRent?")  # Query ASCII assigns value in a singular value list
#     i = CHAN1_trigcount  # Updating increment value
#     if i == infCT:
#         print(0)
#         time.sleep(0.1)
#     else:
#         print(i)
#         time.sleep(0.1)
#
#
# print("End of program.")

