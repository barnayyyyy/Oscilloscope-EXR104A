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
from datetime import datetime

# =============================================
# Globals and Constants
# =============================================

# Addresses and connection types for connecting to the oscilloscope
KEYSIGHT_ADDRESS = "TCPIP0::169.254.205.81::hislip0::INSTR"
KEYSIGHT_UTCADDRESS = "TCPIP0::10.44.11.1::INSTR"

# Global timeout time in milliseconds (10s)
GLOBAL_TOUT = 10000


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
	OS.write("*CLS")

	# Load default setup, clears previous settings (Note: NOT a factory reset)
	OS.write("*RST")


# ====================================================================
# OS Setup test:
# ====================================================================

# Writes command to oscilloscope
def tx(command):
	OS.write("%s" % command)
	check_instrument_errors(command)


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
	results = results[0]  # Results passed into a list for ascii queries
	return results


def rx_block(query):
	result = OS.query_binary_values("%s" % query, datatype='s', container=bytes)
	check_instrument_errors(query, exit_on_error=False)
	return result


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
	tx(":TIMebase:POSition 0")

	# Set timebase range to 2ms
	tx(":TIMebase:RANGe 1E-3")

	# Sets timebase scale to 200us/div
	tx(":TIMebase:SCALe 200E-6")

	# Displays message on oscilloscope
	# tx(":SYSTem:DSP 'Test 1'")

	# Set trigger source
	tx(":TRIGger:MODE WINDow")
	tx(":TRIGger:WINDow:SOURce CHANnel1")
	tx(":TRIGger:WINDow:CONDition EXIT")

	# Define trigger mode and parameters
	tx(":TRIGger:SWEep TRIG")
	tx(":TRIGger:HTHReshold CHANnel1,300E-3")
	tx(":TRIGger:LTHReshold CHANnel1,-300E-3")

	# Turn on Trigger Qualified Counter (Counter C/3)
	tx(":COUNter3:ENABle 1")
	# Enable "Totalize" Mode for counter
	tx(":COUNter3:MODE TOTalize")
	tx(":COUNter3:SOURce CHAN1")


# *********** The following functions are defined in example code via: ***********
# *********** Keysight Infiniium MXR/EXR-Series Oscilloscopes Programmer's Guide 2023 Edition ***********

# ====================================================================
# Check for instrument errors:
# ====================================================================

# Keysight Infiniium MXR/EXR-Series Oscilloscopes Programmer's Guide 2023 Edition

def check_instrument_errors(command, exit_on_error=False):
	while True:
		error_string = OS.query(":SYSTem:ERRor? STRing")
		if error_string:  # If there is an error string value.
			if error_string.find("0,", 0, 2) == -1:  # Not "No error".
				print("ERROR: %s, command: '%s'" % (error_string, command))
				if exit_on_error:
					print("Exited because of error.")
					sys.exit(1)
			else:
				# "No error"
				break
		else:
			# :SYSTem:ERRor? STRing should always return string.
			print("ERROR: :SYSTem:ERRor? STRing returned nothing, command: '%s'" % command)
			print("Exited because of error.")
			sys.exit(1)


def capture():
	# Set the desired number of waveform points,
	# and capture an acquisition.
	tx(":ACQuire:POINts 64000")
	tx(":DIGitize")


def analyze():
	# Make measurements.
	# --------------------------------------------------------
	tx(":MEASure:SOURce CHANnel1")
	qresult = rx_str(":MEASure:SOURce?")
	print("Measure source: %s" % qresult)

	tx(":MEASure:FREQuency")
	qresult = rx_str(":MEASure:FREQuency?")
	print("Measured frequency on channel 1: %s" % qresult)

	tx(":MEASure:VAMPlitude")
	qresult = rx_str(":MEASure:VAMPlitude?")
	print("Measured vertical amplitude on channel 1: %s" % qresult)

	# Download the screen image.
	# --------------------------------------------------------
	screen_bytes = rx_block(":DISPlay:DATA? PNG")
	# Save display data values to file.
	f = open("screen_image.png", "wb")
	f.write(screen_bytes)
	f.close()
	print("Screen image written to screen_image.png.")

	# Download waveform data.
	# --------------------------------------------------------
	# Get the waveform type.
	qresult = rx_str(":WAVeform:TYPE?")
	print("Waveform type: %s" % qresult)

	# Get the number of waveform points.
	qresult = rx_str(":WAVeform:POINts?")
	print("Waveform points: %s" % qresult)

	# Set the waveform source.
	tx(":WAVeform:SOURce CHANnel1")
	qresult = rx_str(":WAVeform:SOURce?")
	print("Waveform source: %s" % qresult)

	# Choose the format of the data returned:
	tx(":WAVeform:FORMat BYTE")
	print("Waveform format: %s" % rx_str(":WAVeform:FORMat?"))

	# Display the waveform settings from preamble:
	wav_form_dict = {
		0: "ASCii",
		1: "BYTE",
		2: "WORD",
		3: "LONG",
		4: "LONGLONG",
	}
	acq_type_dict = {
		1: "RAW",
		2: "AVERage",
		3: "VHIStogram",
		4: "HHIStogram",
		6: "INTerpolate",
		10: "PDETect",
	}
	acq_mode_dict = {
		0: "RTIMe",
		1: "ETIMe",
		3: "PDETect",
	}
	coupling_dict = {
		0: "AC",
		1: "DC",
		2: "DCFIFTY",
		3: "LFREJECT",
	}
	units_dict = {
		0: "UNKNOWN",
		1: "VOLT",
		2: "SECOND",
		3: "CONSTANT",
		4: "AMP",
		5: "DECIBEL",
	}

	preamble_string = rx_str(":WAVeform:PREamble?")
	(
		wav_form, acq_type, wfmpts, avgcnt, x_increment, x_origin,
		x_reference, y_increment, y_origin, y_reference, coupling,
		x_display_range, x_display_origin, y_display_range,
		y_display_origin, date, time, frame_model, acq_mode,
		completion, x_units, y_units, max_bw_limit, min_bw_limit
	) = preamble_string.split(",")

	print("Waveform format: %s" % wav_form_dict[int(wav_form)])
	print("Acquire type: %s" % acq_type_dict[int(acq_type)])
	print("Waveform points desired: %s" % wfmpts)
	print("Waveform average count: %s" % avgcnt)
	print("Waveform X increment: %s" % x_increment)
	print("Waveform X origin: %s" % x_origin)
	print("Waveform X reference: %s" % x_reference)

	# Always 0.
	print("Waveform Y increment: %s" % y_increment)
	print("Waveform Y origin: %s" % y_origin)
	print("Waveform Y reference: %s" % y_reference)

	# Always 0.
	print("Coupling: %s" % coupling_dict[int(coupling)])
	print("Waveform X display range: %s" % x_display_range)
	print("Waveform X display origin: %s" % x_display_origin)
	print("Waveform Y display range: %s" % y_display_range)
	print("Waveform Y display origin: %s" % y_display_origin)
	print("Date: %s" % date)
	print("Time: %s" % time)
	print("Frame model #: %s" % frame_model)
	print("Acquire mode: %s" % acq_mode_dict[int(acq_mode)])
	print("Completion pct: %s" % completion)
	print("Waveform X units: %s" % units_dict[int(x_units)])
	print("Waveform Y units: %s" % units_dict[int(y_units)])
	print("Max BW limit: %s" % max_bw_limit)
	print("Min BW limit: %s" % min_bw_limit)

	# Get numeric values for later calculations.
	x_increment = rx_num(":WAVeform:XINCrement?")
	x_origin = rx_num(":WAVeform:XORigin?")
	y_increment = rx_num(":WAVeform:YINCrement?")
	y_origin = rx_num(":WAVeform:YORigin?")

	# Get the waveform data.
	tx(":WAVeform:STReaming OFF")
	sData = rx_block(":WAVeform:DATA?")
	# Unpack signed byte data.
	values = struct.unpack("%db" % len(sData), sData)
	print("Number of data values: %d" % len(values))

	# Waveform naming
	dt = datetime.now()
	dttime = dt.strftime("%h")
	dtstring = dt.strftime("%Y%h%d_%I%M%S_%p")
	wavename = "KeysightData_" + dtstring + ".csv"
	# Save waveform data values to CSV file.
	f = open(wavename, "w")
	for i in range(0, len(values) - 1):
		time_val = x_origin + (i * x_increment)
		voltage = (values[i] * y_increment) + y_origin
		f.write("%E, %f\n" % (time_val, voltage))
	f.close()
	print("Waveform format BYTE data written to '%s' in program home directory" % wavename)


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
OS.clear()

# check_instrument_errors()
initialize()

os_parameters()

# Trigger Count Test Code
i = 0
infCT = rx_num(":COUNter3:CURRent?")

capture()
analyze()

# while i < 7 or infCT > 9.9*10**36:
#     CHAN1_trigcount = rx_num(":COUNter3:CURRent?")  # Query ASCII assigns value in a singular value list
#     i = CHAN1_trigcount  # Updating increment value
#     if i == infCT:
#         print(0)
#         time.sleep(0.1)
#     else:
#         infCT = 0
#         print(i)
#         time.sleep(0.1)


print("End of program.")

