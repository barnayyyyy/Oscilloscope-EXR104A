# --------------------------------------------------------
# Keithley 2634B System Source Meter Unit: 2-channel, 1fA, 10A pulse, 6.5bit
# Keysight EXR104A Mixed Signal Oscilloscope: 1GHz, 16GSa/s, 10 bit
#  --------------------------------------------------------

# =============================================
# README
# =============================================

# Purpose of this Program
# ------------------------
# A python script that combines two instruments over ethernet: source meter unit(SMU) & oscilloscope(OS)
# Primary Functions:


# First time use on Windows
# ------------------------
# Main Program:
# Python version required: Python 3.7 or newer
# in cmd: pip install qcodes
#         pip install pyvisa
# For more information, see: https://qcodes.github.io/Qcodes/start/index.html

# Plottr Tool

# Download .zip at: https://github.com/data-plottr/plottr
# Place plottr-master folder in same directory as experiments.db
# in cmd: cd to the folder above previous folder(directory above the repository)
# pip install -e plottr-master


# How to Use
# ------------------------

# Plottr Tool
# cd C:\Users\tvr861\OneDrive - University of Tennessee\Spring 2023\3 - Microelectronics Instrumentation - 4999R\plottr-master
# python apps/inspectr.py --dbpath ./../experiments.db

# Monitor
# Uncomment monitor under plotting
# python -m qcodes.monitor.monitor


# =============================================
# Imports
# =============================================

import time
import matplotlib.pyplot as plt

# pyvisa:
import nntplib

import pandas as pd
import pyvisa as visa

# QCoDeS
import qcodes as qc
from qcodes import Station
from qcodes import load_by_id

from qcodes.instrument.parameter import Parameter
from qcodes.instrument.specialized_parameters import ElapsedTimeParameter

from qcodes.dataset import do0d
from qcodes.dataset import initialise_database, load_or_create_experiment, plot_dataset, plot_by_id
from qcodes.dataset.legacy_import import import_dat_file
from qcodes.dataset.measurements import Measurement

from qcodes.data.io import DiskIO
from qcodes.data.location import FormatLocation

from qcodes.loops import Loop
from qcodes.plots.pyqtgraph import QtPlot
from qcodes.monitor.monitor import Monitor
from qcodes.utils.metadata import diff_param_values

# For simulating instruments
from qcodes.tests.instrument_mocks import DummyInstrument

# =============================================
# Program Globals and Constants
# =============================================

# Addresses and connection types for connecting to the oscilloscope
KEYSIGHT_ADDRESS = "TCPIP0::169.254.205.81::hislip0::INSTR"
KEYSIGHT_UTCADDRESS = "TCPIP0::10.44.11.1::inst0::INSTR"
KEYSIGHT_USB = "USB0::10893::36872::MY61310192::0::INSTR"
KEYPSU_ADDRESS = "TCPIP0::169.254.144.73::INST0::INSTR"

# =============================================
# Instrument Drivers
# =============================================

# rm = visa.ResourceManager()  # Define resource extended information
# scope = rm.open_resource(
#     "TCPIP0::169.254.205.81::hislip0::INSTR")  # Create variable named scope to use for operations to instrument
# scope.clear()  # Clears the input buffer and output queue, reset parser, clear pending commands
# scope.write("*rst; status:preset; *cls")  # Performs default setup and clears all status and error registers

# SMU driver
# from qcodes.instrument_drivers.Keithley.Keithley_2634B import Keithley2634B
# smu = Keithley2634B(name='smu', address='TCPIP0::192.168.10.61::inst0::INSTR', gates=['smua', 'smub'])

# OS driver
from qcodes.instrument_drivers.Keysight import KeysightInfiniium
os = KeysightInfiniium(name='os', address=KEYSIGHT_ADDRESS, timeout=10,
                       channels=4, silence_pyvisapy_warning=True)  # Timeout in seconds



smu = DummyInstrument(name='smu', gates=['smua', 'smub'])
# os = DummyInstrument(name='oscilloscope')

# =============================================
# Instrument Parameters
# =============================================

# SMU:
V_appl_1 = Parameter('V_appl_1', label='V_appl_1', unit='V', get_cmd=smu.smua.get,
                     set_cmd=smu.smua.set)  # source V at channel a
V_appl_2 = Parameter('V_appl_2', label='V_appl_2', unit='V', get_cmd=smu.smub.get,
                     set_cmd=smu.smub.set)  # source V at channel b
V_meas_1 = Parameter('V_meas_1', label='V_meas_1', unit='V', get_cmd=smu.smua.get)  # measure V at channel a
V_meas_2 = Parameter('V_meas_2', label='V_meas_2', unit='V', get_cmd=smu.smub.get)  # measure V at channel b
I_appl_1 = Parameter('I_appl_1', label='I_appl_1', unit='A', get_cmd=smu.smua.get,
                     set_cmd=smu.smua.set)  # source I at channel a
I_appl_2 = Parameter('I_appl_2', label='I_appl_2', unit='A', get_cmd=smu.smub.get,
                     set_cmd=smu.smub.set)  # source I at channel b
I_meas_1 = Parameter('I_meas_1', label='I_meas_1', unit='A', get_cmd=smu.smua.get)  # measure I at channel a
I_meas_2 = Parameter('I_meas_2', label='I_meas_2', unit='A', get_cmd=smu.smub.get)  # measure I at channel b

# Keysight Oscilloscope:
nPoints = Parameter('nPoints', label='nPoints', unit='#', set_cmd=os.acquire_points(10_000))  # desired # waveform point
ch1 = Parameter('ch1', label='ch1', unit='V', get_cmd=os.ch1.trace)  # measure V at channel 1
ch2 = Parameter('ch2', label='ch2', unit='V', get_cmd=os.ch2.trace)  # measure V at channel 2
ch3 = Parameter('ch3', label='ch3', unit='V', get_cmd=os.ch3.trace)  # measure V at channel 3
ch4 = Parameter('ch4', label='ch4', unit='V', get_cmd=os.ch4.trace)  # measure V at channel 4

# Keysight PSU (E36313A):

# Time:
t = ElapsedTimeParameter('t')  # Time for measurement
t.reset_clock()  # Reset timer to zero


# =============================================
# Oscilloscope Functions
# =============================================
def os_setup():

    # Clear status.
    os.write_raw("*CLS")

    # Load default setup, clears previous settings (Note: NOT a factory reset)
    os.write_raw("*RST")

    # Startup
    os.write_raw("CHANnel3:INPut DC")  # DC coupling, 1M Ohm Impedance
    os.auto_digitize(False)  # Disable automatic digitization to acquire multiple channels
    os.write_raw(":ACQuire:SRATe:ANALog AUTO")

    # Prepare trace
    for i in range(4):
        os.channels[i].display(False)
    os.ch3.display(True)
    os.timebase_range(1e-3)
    os.timebase_position(0)
    os.ch3.range(2)

    # os.trigger_edge_source('CHAN3')
    # os.trigger_edge_slope('NEG')
    # os.ch3.trigger_level(0)

    # Set trigger mode to window
    os.trigger_mode('WINDow')
    os.trigger_window_source('CHAN3')
    os.trigger_window_cond("EXIT")
    os.trigger_sweep("TRIG")
    os.ch3.trigger_Hthresh(0.3)
    os.ch3.trigger_Lthresh(-0.3)

    # # Setup timebase
    # os.timebase_range(1E-3)  # Total distance on x-axis
    # os.timebase_position(os.timebase_range() / 2)  # Timescale adjusted to have times starting from zero

    # Data acquisition
    # Take # data points and set sample rate such that the entire waveform is shown (duration set by timebase)
    #    nPoints = 10_000                                   # Desired # waveform points
    #    os.acquire_points(nPoints)                          # Capture acquisition
    #    os.sample_rate(nPoints/os.timebase_range())         # Required sample rate
    os.acquire_interpolate(0)  # Disable interpolation so that the scope returns # points
    os.write_raw(
        "ACQuire:AVERage OFF")  # If on, os acquires multiple data values for each time bucket and averages them

    # Setup trigger mode
    # Trigger Sources
    # input channels, external source other than input signal, power source signal, internal signal generated by os
    # os.trigger_edge_source('CHAN3')  # Use input signal itself as the trigger

    # Trigger Modes - page 1574
    # os.write_raw("TRIGger:MODE EDGE")  # Desired triggering

    # Trigger EDGE parameters
    # os.write_raw(
    #     "TRIGger:EDGE:SLOPE POSitive")  # Slope determines whether trigger point is on the rising or falling edge
    # os.ch1.trigger_level(0.1)  # Level determines where on the edge the trigger point occurs

    # Other trigger
    # os.write_raw(
    #     "TRIGger:SWEep TRIGgered")  # If no trigger occurs, the oscilloscope wil not sweep, previous data remains on screen
    os.run()


def os_cleanup():
    os.write_raw(":ACQuire:SRATe:ANALog AUTO")
    os.run()  # Set the scope back to free-running mode
    # Clear status.
    os.write_raw("*CLS")

    # Load default setup, clears previous settings (Note: NOT a factory reset)
    # os.write_raw("*RST")

# =============================================
# Virtual Stations
# =============================================
station = Station()  # Initialize station
station.add_component(t)  # Add time

# SMU:
station.add_component(smu)  # Add instrument to station
station.add_component(V_appl_1)  # Add parameters to station
station.add_component(V_appl_2)
station.add_component(V_meas_1)
station.add_component(V_meas_2)
station.add_component(I_appl_1)
station.add_component(I_appl_2)
station.add_component(I_meas_1)
station.add_component(I_meas_2)

# OS:
station.add_component(os)  # Add instrument to station

# Checks:
# print(station.components)                               # Access the parameters via the station
# station.smu.print_readable_snapshot()                   # Readable quick check for source-meter
# station.os.print_readable_snapshot()                    # Readable quick check for oscilloscope


# =============================================
# Setup Database (DB)
# =============================================

# Initializing the DB
exp_name = 'DC-IV-Sweep'
sample_name = 'Test-Resistor'

qc.config["core"]["db_location"] = './experiments.db'  # File location for database
initialise_database()  # Make database
exp = load_or_create_experiment(exp_name, sample_name)  # Load database

# Snapshot of the Station in DB (.db)
meas = Measurement(exp, station)  # Initialize measurement with loaded or created experiment and station

# SMU - setpoints explained: I_meas is a function of "V_appl_1, V_appl_2 ,..."
# where "V_appl_1, V_appl_2, ..." are known as the setpoints of parameter I_meas
# meas.register_parameter(V_appl_1)  # smua input parameter - outside sweep
# meas.register_parameter(V_appl_2)  # smub input parameter - inside sweep
# meas.register_parameter(I_meas_1, setpoints=[V_appl_1, V_appl_2])  # smua output parameter
# meas.register_parameter(I_meas_2, setpoints=[V_appl_1, V_appl_2])  # smub output parameter

# OS
meas.register_parameter(nPoints)  # os input parameter
# meas.register_parameter(ch1, setpoints=[nPoints])  # os output parameter
# meas.register_parameter(ch2, setpoints=[nPoints])  # os output parameter
meas.register_parameter(ch3, setpoints=[nPoints])  # os output parameter
# meas.register_parameter(ch4, setpoints=[nPoints])  # os output parameter


# =============================================
# Measurements
# =============================================

# SMU:
# Define 1D Loop
# Sweep parameter V_appl_1 from -1 to 1 at stepping 0.01
# Delay is wait time for between each step
# loop = Loop(V_appl_1.sweep(-1,1,0.01), delay = 0.01).each(V_appl1,I_meas,t)

# Define 2D Loop
# Sweep parameter V_appl_2 from -1 to 1 at 0.01 increments at each step of V_appl_1
# Delay is wait time for between each steps
loop = Loop(V_appl_1.sweep(-1, 1, 0.1), delay=0.001).loop(V_appl_2.sweep(-1, 1, 0.1), delay=0.001).each(V_appl_1,
                                                                                                        V_appl_2,
                                                                                                        I_meas_1, t)  #

# Run Respective Loop
# data = loop.get_data_set(name='sweep')


# OS:
os_setup()
# os.digitize()  # Manually digitize once for each acquisition
# do0d(os.ch3.trace, do_plot=True)                    # Perform a measurement of a single parameter

# ds, _, _ = do0d(os.ch3.measure.amplitude, os.ch3.measure.frequency) # Single  return values
# df = ds.to_pandas_dataframe()
# print(df)

# Measuring
meas.add_before_run(os_setup, args=())
# measurement.add_before_run(smu_setup, args=())
meas.add_after_run(os_cleanup, args=())
# os.ch3.cache_setpoints = True

with meas.run() as datasaver:
    for nPointstest in [100, 1_000, 10_000, 50_000]:
        # os.write_raw(":ACQuire:SRATe:ANALog AUTO")
        # os.ch3.update_setpoints()
        time.sleep(1)
        os.acquire_points(nPointstest)  # Capture acquisition
        # os.acquire_interpolate(0)
        # os.sample_rate(nPoints / os.timebase_range())  # Required sample rate
        os.digitize()
        # print(os.ch3.trace.get())
        # # os.auto_digitize()
        df = pd.DataFrame(os.ch3.trace.get())
        df.to_csv(f"{nPointstest}.csv")
        # datasaver.add_result((nPoints,nPointstest),
        #                      (ch3, os.ch3.trace.get()))
        # datasaver.add_result(os.ch3.trace.get())

# dataset = datasaver.dataset
# time.sleep(5)
# # print(dataset.to_pandas_dataframe().head())
# CH3_df = dataset.to_pandas_dataframe_dict()["ch3"]
# # print(dataset.to_pandas_dataframe_dict()["ch3"])
# # _ = plot = plot_dataset(dataset)
# plt.plot(CH3_df.index, CH3_df.ch3)
# plt.savefig('TestPlot.png')

# =============================================
# Storing Data in the Database (DB)
# =============================================

# Store data acquired by loop in .dat file
loc_fmt = './data/{date}/#{counter}_{name}_{sample}'  # Save .dat files in data folder sorted by date, named with counter,name,sample
rcd = {'name': exp_name, 'sample': sample_name}  # Paste values you want to use for line above
loc_provider = FormatLocation(fmt=loc_fmt)  #
loc = loc_provider(DiskIO("."), record=rcd)  # Saving data in location provided before

# loop.run()

# import_dat_file(loc,exp)                                    # Import .dat file's data into database


exit()


# =============================================
# Plotting
# =============================================

# Visualising Data
# monitor = qc.Monitor(V_appl_1,V_appl_2,I_meas,t)


# Live
plot = QtPlot()  # Make plot
plot.add(data.I)  # Add data to plot
_ = loop.with_bg_task(plot.update).run()  # Live plotting
plot.save('./graph.png')  # Save plot

# =============================================
# Cleanup
# =============================================
# OS
os.run()  # Set the scope back to free-running mode
