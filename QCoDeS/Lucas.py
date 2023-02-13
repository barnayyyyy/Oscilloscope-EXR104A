# --------------------------------------------------------
# Keithley 2634B System Source Meter Unit: 2-channel, 1fA, 10A pulse, 6.5bit
# Keysight EXR104A Mixed Signal Oscilloscope: 1GHz, 16GSa/s, 10 bit
#  --------------------------------------------------------
########## What #########
# A python script that combines two instruments over ethernet: source meter unit(SMU) & oscilloscope(OS)
# Primary Functions:

########## First time users on Windows #########
# Main Program
# Need latest version of python (3.x)
# in cmd: pip install qcodes

# Plottr Tool
# Download .zip at: https://github.com/data-plottr/plottr
# Place plottr-master folder in same directory as experiments.db
# in cmd, cd to the folder above previous folder(directory above the repository)
# in cmd: pip install -e plottr-master



# --------------------------------------------------------
# Imports
# --------------------------------------------------------
########## QCoDeS #########
import qcodes as qc

# SMU driver
#from qcodes.instrument_drivers.Keithley.Keithley_2634B import Keithley2634B
#smu = Keithley2634B(name='sourcemeter', address='TCPIP0::192.168.10.61::inst0::INSTR', gates=['smua', 'smub'])

# OS driver
#from qcodes.instrument_drivers.Keysight import KeysightInfiniium
#os = KeysightInfiniium(name='oscilloscope', address='TCPIP0::169.254.205.81::hislip0::INSTR')

# Dummy Instrument
from qcodes.tests.instrument_mocks import DummyInstrument
smu = DummyInstrument(name='smu', gates=['smua','smub'])

# Other
from qcodes.instrument.parameter import Parameter
from qcodes.instrument.specialized_parameters import ElapsedTimeParameter
from qcodes.loops import Loop
from qcodes.plots.pyqtgraph import QtPlot
from qcodes.dataset import initialise_database, load_or_create_experiment
from qcodes.data.location import FormatLocation
from qcodes.dataset.legacy_import import import_dat_file
from qcodes.data.io import DiskIO
from qcodes import Station
from qcodes.utils.metadata import diff_param_values
from qcodes import load_by_id
from qcodes.dataset.measurements import Measurement
from qcodes.monitor.monitor import Monitor


########## Other #########



# --------------------------------------------------------
# Setup
# --------------------------------------------------------
########## Parameters #########
# SMU
V_appl_1 = Parameter('V_appl_1', label='V_appl_1', unit='V', get_cmd=smu.smua.get, set_cmd=smu.smua.set) #
V_appl_2 = Parameter('V_appl_2', label='V_appl_2', unit='V', get_cmd=smu.smub.get, set_cmd=smu.smub.set) # 
I_meas = Parameter('I', label='I_meas', unit='A', get_cmd=lambda: float(smu.smua.get()/1000))          # lambda to treat as .get to treat as function

# Time
t = ElapsedTimeParameter('t')           # Time for measurement
t.reset_clock()                         # Reset timer to zero


########## Station #########
station = Station(I_meas) # Inialize station with I_meas parameter

station.add_component(t) # adding a parameter
station.add_component(smu) # adding an instrument
# print(station.components) # Access the parameters via the station
# station.smu.print_readable_snapshot() # Readable quick check for instrument



# --------------------------------------------------------
# Measurments
# --------------------------------------------------------
########## 1D Loop #########
#loop = Loop(V_appl_1.sweep(-1,1,0.01), delay = 0.01).each(V_appl1,I_meas,t) # Sweep parameter V_appl from -1 to 1 at stepping 0.01 --- Delay is waiting for time until next loop


########## 2D Loop #########
loop = Loop(V_appl_1.sweep(-1,1,0.1), delay = 0.001).loop(V_appl_2.sweep(-1,1,0.1), delay = 0.001).each(V_appl_1,V_appl_2,I_meas,t) #



# --------------------------------------------------------
# Plotting
# --------------------------------------------------------
########## Visualising Data #########
#monitor = qc.Monitor(V_appl_1,V_appl_2,I_meas,t)


########## Live #########
data = loop.get_data_set(name='sweep')
plot = QtPlot()                                                     # Make plot
plot.add(data.I)                                                    # Add data to plot
_ = loop.with_bg_task(plot.update).run()                            # Live plotting
plot.save('./Results/graph.png')



# --------------------------------------------------------
# Storing Data in a Database (DB)
# --------------------------------------------------------
########## Initalizing the DB #########
exp_name = 'DC-IV-Sweep'
sample_name = 'Test-Resistor'

qc.config["core"]["db_location"]='./experiments.db'         # File location for database
initialise_database()                                       # Make database
exp=load_or_create_experiment(exp_name, sample_name)        # Load database


########## Snapshot of the Station in DB (.db) #########
measurement = Measurement(exp, station)
measurement.register_parameter(V_appl_1)                    # First sweep
measurement.register_parameter(V_appl_2)                    # Second sweep
measurement.register_parameter(I_meas, setpoints=[V_appl_1, V_appl_2])   # dependent parameter
#with measurement.run() as datasaver:
#    datasaver.add_result((V_appl_1, V_appl_1),(V_appl_2, V_appl_2),(I_meas, data))


########## Data Folder (.dat) #########
loc_fmt='./data/{date}/#{counter}_{name}_{sample}'          # Save .dat files in data folder sorted by date, named with counter,name,sample
rcd={'name':exp_name,'sample':sample_name}                  # Paste values you wan to use for line above
loc_provider = FormatLocation(fmt=loc_fmt)                  # 
loc = loc_provider(DiskIO("."),record=rcd)                  # Saving data in location provided before

loop.run()

import_dat_file(loc,exp)                                    # Import .dat file's data into database

exit()
# --------------------------------------------------------
# Extra
# --------------------------------------------------------
# Reading Data from the DB
#load_or_create_experiment(exp_name,sample_name)             # Load data from previous experiment

########## Comparing two diffferente Snapshots #########
from qcodes.utils.metadata import diff_param_values
from qcodes import load_by_id

snapshot1 = dataset.snapshot
snapshot2 = load_by_id(8).snapshot # in Run 8 I changed the v5 init voltage to 1

diff_param_values(snapshot1, snapshot2).changed

# Using Plottr Tool
# cd C:\Users\tvr861\OneDrive - University of Tennessee\Spring 2023\3 - Microelectronisc Instrumentation - 4999R\plottr-master 
# python apps/inspectr.py --dbpath ./../experiments.db

# Using Monitor
# python -m qcodes.monitor.monitor


exit()
from qcodes.dataset import (
    Measurement,
    plot_by_id,
    plot_dataset,
    load_or_create_experiment,
    initialise_or_create_database_at,
    do0d,
)
from qcodes.parameters import Parameter
from qcodes.station import Station
initialise_or_create_database_at("C:/Users/tvr861/OneDrive - University of Tennessee/Spring 2023/3 - Microelectronisc Instrumentation - 4999R/Results")
exp = qc.load_or_create_experiment("Push Button", "Learning")        # Experiement name, Sample name


def os_setup():
    ########## Startup ##########
    station = qc.Station(os)                            # For multiple instruments
    os.ch1.input('DC50')                                # DC coupling, 50 Ohm Impedance
    os.auto_digitize(False)                             # Disable automatic digizitation to aquire multiple channels


    ########## Setup inputs ##########
    for i in range(4):
        os.channels[i].display(False)                   # All channels are hidden
    os.ch3.display(True)                                # Turn on connected channel
    os.ch3.range(2.5)                                   # Range of channel


    ########## Setup timebase ##########
    os.timebase_range(10e-3)                            # Total distance on x-axis
    os.timebase_position(os.timebase_range()/2)         # Time scale adjusted to have times starting from zero


    ########## Data acquisition ##########                         
    # Take # data points and set sample rate such that the entire waveform is shown (duration set by timebase)
    nPoints = 10_000                                    # Desired # waveform points
    os.acquire_points(nPoints)                          # Capture acquisition
    os.sample_rate(nPoints/os.timebase_range())         # Required sample rate
    os.acquire_interpolate(0)                           # Disable interpolation so that the scope reutrns # points
    os.acquire_average(False)                           # If on, os acquires multiple data values for each time bucket and averages them


    ########## Setup trigger ##########
    # Trigger Sources - input channels, external source other than input signal, power source signal, internal signal generated by os
    os.trigger_edge_source('CHAN3')                     # Use input signal istelf as the trigger

    # Trigger Modes - page 1574
    os.trigger_mode('EDGE')                             # Desired triggering

    # Trigger EDGE parameters  
    os.trigger_edge_slope('POS')                        # Slope determines whether trigger point is on the rising or falling edge
    os.ch3.trigger_level(0)                             # Level determines where on the edge the trigger point occurs 

    # Other trigger
    os.trigger_sweep('triggered')                       # If no trigger occurs, the oscilloscope wil not sweep, previous data remains on screen


    ########## Ending ##########
    os.run()                                            # Set the scope back to free-running mode

########## Parameters ##########
x = Parameter(name='x',   label='Voltage', unit='V', set_cmd=None, get_cmd=None)
t = Parameter(name='t',   label='Time',    unit='s', set_cmd=None, get_cmd=None)
y = Parameter(name='y',   label='Voltage', unit='V', set_cmd=None, get_cmd=None)
y2 = Parameter(name='y2', label='Current', unit='A', set_cmd=None, get_cmd=None)


########## Dataset ##########
# run id, experiement name, sample name, name
meas = Measurement(exp, 'Detecting Transients')
meas.register_parameter(x)
meas.register_parameter(t)
meas.register_parameter(y, setpoints=(x,t))
meas.register_parameter(y2, setpoints=(x,t))
meas.register_parameter(os.ch3.trace)
meas.add_before_run(os_setup)

with meas.run() as datasaver:
    trace = os.ch1.trace.get()
    datasaver.add_result(os.ch1.trace, trace)
dataset = datasaver.dataset
plot_dataset(dataset)
df = dataset.to_pandas_dataframe()
df.to_csv("C:/Users/tvr861/OneDrive - University of Tennessee/Spring 2023/3 - Microelectronisc Instrumentation - 4999R/Results/test.csv")


########## Take measurement ##########
#os.digitize                                         # Manually digitize once for each aquisition
#do0d(os.ch3.trace, do_plot=True)                    # Perform a measurement of a single parameter

#ds, _, _ = do0d(os.ch3.measure.amplitude, os.ch3.measure.frequency)
#df = ds.to_pandas_dataframe()
#df

########## Cleanup ##########
os.run()                                            # Set the scope back to free-running mode
os.close()                                          # Disconnect from oscilloscope