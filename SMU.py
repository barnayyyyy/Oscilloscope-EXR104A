# SMU code by John Barney
# with support from Lucas Nichols

from keithley2600 import Keithley2600
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
from matplotlib import gridspec
import warnings
import time
from datetime import datetime

# removing unnecessary warnings APPEND WILL BE REPLACED WITH CONCAT IN PANDAS IN THE FUTURE
warnings.simplefilter(action='ignore', category=FutureWarning)

# creating help command
def help():
    print("\ncall \'SMU.savefile\' to select save location\ncall \'SMU.ip\' to set ip address of SMU\n  Note: USE / for \\ in file path")
    print("\n\
*****EXAMPLES*****\n\
SMU.Settings(0.001)\n\
SMU.Test('IRFZ44N_box_AloopB').AloopB(0.5,2,0.5,0,1.2,0.1)\n\
SMU.Test('IRFZ44N_box_BloopA').BloopA(0,1.2,0.4,0.5,2,0.1)\n\
SMU.Test('IRFZ44N_box_TimeTest').TimeTest(2.75,0.5,5000)\n\
SMU.Graphs_Overlay('IRFZ44N_box_AloopB','IRFZ44N_box_BloopA').Loops_Overlay()\n\
SMU.Graph('IRFZ44N_box_AloopB').Loops()\n\
SMU.Graph('IRFZ44N_box_BloopA').Loops()\n\
SMU.Format('IRFZ44N_box_BloopA').AddTransconductance()\n\
SMU.Graph('IRFZ44N_box_BloopA').Loop_and_Transconductance()\n\
SMU.Graph('IRFZ44N_box_BloopA').Transconductance())\n\
    ")

# Note: USE / for \ in file path
savefile = "Desktop" # where to save file
ip = 'TCPIP0::192.168.10.61::inst0::INSTR'

# Connect Instrument
SMU = Keithley2600(ip)                                                      # Connect to SMU via IP

def Settings(nplc):
    # SMU settings
    SMU.set_integration_time(SMU.smub, nplc)                                # nplc = integration time: 0.001 to 25
    print(f"SMU nplc set to {nplc}")

# class for holding all the various tests
class Test:
    def __init__(self,name): # inital parameters given to object of class Test
        print('\nFor MOSFET: attach Vgs to SMUA & Vds to SMUB\n') # how 3 terminal device must be plugged in to SMU
        self.name = name
        self.save = savefile+self.name+'.csv' # path and name of csv file to call in one: self.save

    # For loop where SMUa steps up and SMUb sweeps per step
    def AloopB(self,smua_in1,smua_in2,smua_incr,smub_in1,smub_in2,smub_incr,delay=0,smua_in_type='v',smub_in_type='v',smua_in_name='Vgs (V)',smub_in_name='Vds (V)',meas_name='Ids (A)'):
        self.smua_in_name = smua_in_name
        self.smub_in_name = smub_in_name
        self.meas_name = meas_name

        # varying smu commands based on v or i supplied
        apply_smu = 0                                                  # temportary variable to apply voltage/current
        if smua_in_type == 'v':
            def smua_apply():                                           # function to apply voltage to smua
                return SMU.apply_voltage(SMU.smua, apply_smu)                   
        elif smua_in_type == 'i':
            def smua_apply():                                           # function to apply current to smua
                return SMU.apply_current(SMU.smua, apply_smu)                     
        else:
            raise Exception('smua_in_type must be \'v\' or \'i\'')

        if smub_in_type == 'v':
            def smub_apply():                                           # function to apply voltage to smub
                return SMU.apply_voltage(SMU.smub, apply_smu)    
            def smub_meas():                                            # function to measure current at smub
                return SMU.smub.measure.i()                             
            SMU.display.smub.measure.func = SMU.smub.measure.i()        # displaying measrurement on smub
        elif smub_in_type == 'i':
            def smub_apply():                                           # function to apply current to smub
                return SMU.apply_current(SMU.smub, apply_smu)                    
            def smub_meas():                                            # function to measure voltage at smub
                return SMU.smub.measure.v()
            SMU.display.smub.measure.func = SMU.smub.measure.v()        # displaying measurement on smub
        else:
            raise Exception('smub_in_type must be \'v\' or \'i\'')

        # fixes divide by 0 error caused by np.arange()
        if smua_incr == 0:
            iter_a = 1                                                     # only run for loop once
            for_outer_arr = smua_in1                                       # only one element in legend                                        
        else:
            iter_a = len(np.arange(smua_in1,float(smua_in2+smua_incr),smua_incr))       # how many iterations in for loop
            for_outer_arr = np.arange(smua_in1,float(smua_in2+smua_incr),smua_incr)     # creates array containing legend elements   
        if smub_incr == 0:
            iter_b = 1                                                          # only run loop once
            for_inner_arr = smub_in1                                            # only one set of elements in x axis               
        else:
            iter_b = len(np.arange(smub_in1,float(smub_in2+smub_incr),smub_incr))       # how many iterations in for loop
            for_inner_arr = np.arange(smub_in1,float(smub_in2+smub_incr),smub_incr)     # creates array for the x axis values         

        # initializes
        df = pd.DataFrame()                                                     # initializing empty dataframe for storing data in code
        total = (iter_a*iter_b)+iter_a                                          # calculates total number of iterations
        count = 0                                                               # initializes counter variable

        time_start = datetime.utcnow().strftime('%m-%d-%Y @ %H:%M:%S.%f')[:-3]  # starting time of test
        print(f"\nStarting time: {time_start}\n")                               

        SMU.smua.source.output = SMU.smua.OUTPUT_ON                             # turn on SMUA
        SMU.smub.source.output = SMU.smub.OUTPUT_ON                             # turn on SMUB

        for a in range(0,iter_a):                                               # loop of smua
            print(f"{count+1} out of {total}")                                  # iteration counter
            count = count + 1                                                   # increments counter variable

            apply_smu = for_outer_arr[a]                                        # setting amount of voltage/current to apply to smu 
            smua_apply()                                                        # calling apply voltage/current function
            time.sleep(delay)                                                   # delay the program to limit sample size

            df = df.append({f"{self.smua_in_name}": for_outer_arr[a]}, ignore_index=True)   # adding the outer for loop value to outer for loop labeled column
            df.to_csv(self.save, float_format='%.15f')                                      # save dataframe to csv

            for b in range(0,iter_b):                                           # loop of smub
                print(f"{count+1} out of {total}")                              # iteration counter
                count = count + 1                                               # increments counter variable

                apply_smu = for_inner_arr[b]                                    # setting amount of voltage/current to apply to smu
                smub_apply()                                                    # calling apply voltage/current function
                time.sleep(delay)                                               # delay the program to limit sample size
                meas = smub_meas()                                              # calling measure voltage/current function

                df = df.append({f"{self.smub_in_name}": for_inner_arr[b], f"{self.meas_name}": meas}, ignore_index=True) # adding inner for loop and measured values to labeled columns
                df.to_csv(self.save, float_format='%.15f')                      # save dataframe to csv

            time_end = datetime.utcnow().strftime('%H:%M:%S.%f')[:-3]           # ending time of test
            print(f"\nEnding time: {time_end}\n")

        SMU.smua.source.output = SMU.smua.OUTPUT_OFF                            # turn off SMUA
        SMU.smub.source.output = SMU.smub.OUTPUT_OFF                            # turn off SMUB

        print(f"\nDataframe for {self.name}: \n{df}\n")                         # printing dataframe
        df.to_csv(self.save,index=True, float_format='%.15f')                   # save data to csv
        Format(self.save).RemoveNAN()                                           # Removes NaN's from csv
        Graph(self.save).Loops()                                                # Graphs Loop performed
        return

    def BloopA(self,smub_in1,smub_in2,smub_incr,smua_in1,smua_in2,smua_incr,delay=0,smua_in_type='v',smub_in_type='v',smua_in_name='Vgs (V)',smub_in_name='Vds (V)',meas_name='Ids (A)'):
        self.smua_in_name = smua_in_name
        self.smub_in_name = smub_in_name
        self.meas_name = meas_name

        # varying smu commands based on v or i supplied
        apply_smu = 0                                                           # temporary variable to apply voltage/current to smu
        if smua_in_type == 'v': 
            def smua_apply():                                                   # Function for applying voltage to smua
                return SMU.apply_voltage(SMU.smua, apply_smu)                       
        elif smua_in_type == 'i':   
            def smua_apply():                                                   # Function for applying current to smua
                return SMU.apply_current(SMU.smua, apply_smu)                       
        else:   
            raise Exception('smua_in_type must be \'v\' or \'i\'')  

        if smub_in_type == 'v': 
            def smub_apply():                                                   # Function for applying voltage to smub
                return SMU.apply_voltage(SMU.smub, apply_smu)                        
            def smub_meas():                                                    # Function for measuring current at smub
                return SMU.smub.measure.i() 
            SMU.display.smub.measure.func = SMU.smub.measure.i()                # displaying measured value to smub
        elif smub_in_type == 'i':   
            def smub_apply():                                                   # Function for applying current to smub
                return SMU.apply_current(SMU.smub, apply_smu)                       
            def smub_meas():                                                    # Function for measuring voltage at smub
                return SMU.smub.measure.v() 
            SMU.display.smub.measure.func = SMU.smub.measure.v()                # displaying measured value to smub 
        else:   
            raise Exception('smub_in_type must be \'v\' or \'i\'')

        # fixes divide by 0 error
        if smua_incr == 0:
            iter_a = 1                                                                  # only run for loop once
            for_inner_arr = smua_in1                                                    # only one element in array
        else:   
            iter_a = len(np.arange(smua_in1,float(smua_in2+smua_incr),smua_incr))       # how many times to run for loop
            for_inner_arr = np.arange(smua_in1,float(smua_in2+smua_incr),smua_incr)     # value of elements in array 
        if smub_incr == 0:  
            iter_b = 1                                                                  # only run for loop once
            for_outer_arr = smub_in1                                                    # only one element in array
        else:       
            iter_b = len(np.arange(smub_in1,float(smub_in2+smub_incr),smub_incr))       # how many times to run for loop
            for_outer_arr = np.arange(smub_in1,float(smub_in2+smub_incr),smub_incr)     # value of elements in array
    
        # initializes   
        df = pd.DataFrame()                                                             # initialize empty dataframe
        total = (iter_a*iter_b)+iter_b                                                  # for counter
        count = 0                                                                       # counter variable
    
        time_start = datetime.utcnow().strftime('%m-%d-%Y @ %H:%M:%S.%f')[:-3]  # start test time
        print(f"\nStarting time: {time_start}\n")

        SMU.smua.source.output = SMU.smua.OUTPUT_ON                             # turn on SMUA
        SMU.smub.source.output = SMU.smub.OUTPUT_ON                             # turn on SMUB

        for b in range(0,iter_b):                                               # loop of smub
            print(f"{count+1} out of {total}")                                  # display iteration counter
            count = count + 1                                                   # increment counter

            apply_smu = for_outer_arr[b]                                        # set variable to apply voltage/current to smu
            smub_apply()                                                        # call function to apply voltage/current to smu
            time.sleep(delay)                                                   # delay for loop

            df = df.append({f"{self.smub_in_name}": for_outer_arr[b]}, ignore_index=True) # add applied value to labeled column in dataframe
            df.to_csv(savefile+self.name+'.csv', float_format='%.15f')          # save data to csv

            for a in range(iter_a):                                             # loop of smua
                print(f"{count+1} out of {total}")                              # iteration counter
                count = count + 1                                               # increment counter

                apply_smu = for_inner_arr[a]                                    # set variable to apply voltage/current to smu
                smua_apply()                                                    # call function to apply voltage/current to smu
                time.sleep(delay)                                               # delay for loop
                meas = smub_meas()                                              # measure value

                df = df.append({f"{self.smua_in_name}": for_inner_arr[a], f"{self.meas_name}": meas}, ignore_index=True) # add applied and measured values to labeled columns in dataframe
                df.to_csv(self.save, float_format='%.15f')                      # save dataframe to csv

            time_end = datetime.utcnow().strftime('%H:%M:%S.%f')[:-3]           # end test time
            print(f"\nEnding time: {time_end}\n")

        SMU.smua.source.output = SMU.smua.OUTPUT_OFF                            # turn off SMUA
        SMU.smub.source.output = SMU.smub.OUTPUT_OFF                            # turn off SMUB

        print(f"\nDataframe for {self.name}: \n{df}\n")                         # printing dataframe results
        df.to_csv(self.save,index=True, float_format='%.15f')                   # save data to csv
        Format(self.save).RemoveNAN()                                           # Removes NaN's from csv
        Format(self.save).AddTransconductance()                                 # Adds transconductance to csv
        Graph(self.save).Loop_and_Transconductance()                            # Graphs Loop performed and transconuctance
        return

    def TimeTest(self,smua_in,smub_in,time_total,time_step=0,smua_in_type='v',smub_in_type='v',smua_in_name='Vgs (V)',smub_in_name='Vds (V)',xaxis_name='Time (Sec)',meas_name='Ids (A)'):
        self.smua_in_name = smua_in_name
        self.smub_in_name = smub_in_name
        self.xaxis_name = xaxis_name
        self.meas_name = meas_name

        # varying smu commands based on v or i supplied
        apply_smu = 0                                                           # initializing variable to apply value to smu
        if smua_in_type == 'v':
            def smua_apply():                                                   # Function for applying voltage to smua
                return SMU.apply_voltage(SMU.smua, apply_smu)                   
        elif smua_in_type == 'i':   
            def smua_apply():                                                   # Function for applying current to smua
                return SMU.apply_current(SMU.smua, apply_smu)                   
        else:
            raise Exception('smua_in_type must be \'v\' or \'i\'')

        if smub_in_type == 'v':
            def smub_apply():                                                   # Function for applying voltage to smub
                return SMU.apply_voltage(SMU.smub, apply_smu)                   
            def smub_meas():
                return SMU.smub.measure.i()                                     # Function for measuring current at smub
            SMU.display.smub.measure.func = SMU.smub.measure.i()                # Displaying measurements to smub
        elif smub_in_type == 'i':
            def smub_apply():                                                   # Function for applying current to smub
                return SMU.apply_current(SMU.smub, apply_smu)                   
            def smub_meas():                                                    # Function for measuring voltage at smub
                return SMU.smub.measure.v()
            SMU.display.smub.measure.func = SMU.smub.measure.v()                # Displaying measurements to smub
        else:
            raise Exception('smub_in_type must be \'v\' or \'i\'')

        time_start = datetime.utcnow().strftime('%m-%d-%Y @ %H:%M:%S.%f')[:-3]  # start time of test

        SMU.smua.source.output = SMU.smua.OUTPUT_ON                             # turn on SMUA
        SMU.smub.source.output = SMU.smub.OUTPUT_ON                             # turn on SMUB

        apply_smu = smua_in                                                     # setting variable to apply to smua
        smua_apply()                                                            # applying voltage/current to smua
        apply_smu = smub_in                                                     # setting variable to apply to smub
        smub_apply()                                                            # applying voltage/current to smub

        # initializing dataframe
        df = pd.DataFrame()                                                                                     # initializing empty dataframe for storing data
        df = df.append({f"{self.smua_in_name}": smua_in, f"{self.smub_in_name}": smub_in}, ignore_index=True)   # adding applied voltage/current at smua & smub to labeled columns in dataframe

        t.start()                                                                                               # starting elapse time timer
        for n in len(np.arange(0,time_total+time_step)):                                                        # determining how many times to run for loop
            print(f"{n+1} out of {len(np.arange(0,time_total+time_step))}")                                     # iteration counter for ease of use

            meas = smub_meas()                                                                                  # measuring voltage/current at smub
            elapsed_time = t.stop()                                                                             # calculating elapsed time from last t.start()
            t.start()                                                                                           # restarting elapse time timer

            df = df.append({f"{self.meas_name}": meas,'Time (s)': elapsed_time}, ignore_index=True)             # add measured value to labeled column in dataframe
            df.to_csv(self.save)                                                                                # save dataframe to csv
            time.sleep(time_step)                                                                               # delay for between for loops 
        t.stop()                                                                                                # stopping elapse time timer

        SMU.smua.source.output = SMU.smua.OUTPUT_OFF                            # turn off SMUA
        SMU.smub.source.output = SMU.smub.OUTPUT_OFF                            # turn off SMUB

        time_end = datetime.utcnow().strftime('%H:%M:%S.%f')[:-3]
        print(f"\nStarting time: {time_start}")
        print(f"\nEnding time: {time_end}\n")

        print(f"\nDataframe for {self.name}: \n{df}\n")                         # printing dataframe results
        df.to_csv(self.save, float_format='%.15f')                              # save dataframe to csv
        Format(self.save).RemoveNAN()                                           # Removes NaN's from csv
        Graph(self.save).Timetest()                                             # graph csv file
        return

class Format:
    def __init__(self,name):
        self.name = name                                                        # Input sheet to modify
        self.save = savefile+self.name+'.csv'                                   # Path and name of csv file to call in one: self.save
        self.df = pd.read_csv(self.save,index_col=0)                            # Read csv file, removes index column
        self.columns = list(self.df)                                            # Lists inputs then outputs4

        return

    def RemoveNAN(self):
        subset_cols = [self.columns[0], self.columns[1]]                            # Specify Columns to modify in next line
        [self.df[col].fillna(method="ffill", inplace=True) for col in subset_cols]  # Fill NaN by using pervious entry(ffill) in first 2 columns, modify current dataframe rather than create a new one(inplace)
        self.df.dropna(inplace=True)                                                # Remove rows that contain at least one NaN's
        self.df.reset_index(drop=True,inplace=True)                                 # Reset index after dropping rows, drop=true to avoid old index being inserted
        self.df.to_csv(self.save,index=True,float_format="%.15f")                   # Write dataframe to csv
        return

    def AddTransconductance(self):
        def np_slope(data):
            return np.polyfit(data.index.values,data.values,1)[0]
        self.df['gm (S)'] = self.df[self.columns[2]].rolling(5,min_periods=2).apply(np_slope,raw=False)        
        self.df.to_csv(self.save,index=True,float_format="%.15f")                  # Write dataframe to csv
        return
        
class Graph:
    def __init__(self,name):
        self.name = name                                                        # Input sheet to graph
        self.save = savefile+self.name+'.csv'                                   # Path and name of csv file to call in one: self.save
        self.df = pd.read_csv(self.save,index_col=0)                            # Read csv file, removes index column
        self.columns = list(self.df)                                            # Lists inputs then outputs4

        ##### Splicing Dataframe #####  
        df2 = self.df.copy(deep=True)                                           # Copy dataframe, leaving first one untouched
        df2['step'] = df2[self.columns[0]].diff()                               # Create new column to see when big sweep steps up
        df2.query('`step` != 0', inplace=True)                                  # Find first rows of each big sweep values
        orows = self.df.shape[0]                                                # Find how many rows there are in orignial data frame
        if df2.shape[0] == 1:                                                   # If only sweeping one value
            self.rows = [0, orows]                                              # Get row value from original data frame and create splice
        else:   
            rows = df2.index.array                                              # Create array to represent index values where big sweep chagnes
            self.rows = np.append(rows,orows)                                   # Add final upper limit of splice

       ##### Setup for Plots #####  
        plt.clf()                                                               # Clear active plots
        self.upper = 0                                                          # Variable for determining the upper limit of the splice
        self.lower = 0                                                          # Variable for determining the lower limit of the splice
        return  

    def Loops(self):    
        fig, ax = plt.subplots()                                                # Setup for Plot

        #### Plotting ##### 
        for y in self.rows:                                                     # Loop for amount of big sweep vaules
            self.upper += 1                                                     # Increase upper limit for next splice
            if len(self.rows)-1 < self.upper:                                   # Have we reached the final splice?
                break                                                           # Stop splicing
            y = self.df.iloc[self.rows[self.lower]:self.rows[self.upper]]       # Splice df into each value of big sweep
            self.lower += 1                                                     # Increase upper limit for next splice
            legend = y.iloc[0,0]                                                # Find what big sweep equals to every splice
            plt.plot(y[self.columns[1]],y[self.columns[2]], '-', label=f"{self.columns[0]}: {legend}") # Plot small sweep(xaxis) & Ids(y-axis)

        ##### Labeling Plot #####   
        plt.title(f"{self.name}: {self.columns[2]} vs. {self.columns[1]}",fontsize='20') # Title is name of part and test performed
        Labeloffset(ax, label=self.columns[1], axis="x")                        # Label x axis
        Labeloffset(ax, label=self.columns[2], axis="y")                        # Label y axis
        plt.legend()                                                            # Legend is different splicings
        plt.tight_layout()                                                      # Make plot fit inside window
        plt.savefig(savefile+self.name+'_Loops.png')                            # Saving plot to png file
        return  

    def Transconductance(self): 
        fig, ax = plt.subplots()                                                # Setup for Plot

        #### Plotting ##### 
        for y in self.rows:                                                     # Loop for amount of big sweep vaules
            self.upper += 1                                                     # Increase upper limit for next splice
            if len(self.rows)-1 < self.upper:                                   # Have we reached the final splice?
                break                                                           # Stop splicing
            y = self.df.iloc[self.rows[self.lower]:self.rows[self.upper]]       # Splice df into each value of big sweep
            self.lower += 1                                                     # Increase upper limit for next splice
            legend = y.iloc[0,0]                                                # Find what big sweep equals to every splice
            plt.plot(y[self.columns[1]],y[self.columns[3]], '-', label=f"{self.columns[0]}: {legend}") # Plot small(x-axis) & Transconductance(y-axis)

        ##### Labeling Plot #####   
        plt.title(f"{self.name}: {self.columns[3]} vs. {self.columns[1]}",fontsize='20') # Title is name of part and test performed
        Labeloffset(ax, label=self.columns[1], axis="x")                        # Label x axis
        Labeloffset(ax, label=self.columns[3], axis="y")                        # Label y axis
        plt.legend()                                                            # Legend is different splicings
        plt.tight_layout()                                                      # Make plot fit inside window
        plt.savefig(savefile+self.name+'_Transconductance.png')                 # Saving plot to png file
        return  

    def Loop_and_Transconductance(self):    
        #### Setup Subplots #####   
        fig = plt.figure()  
        gs = gridspec.GridSpec(2,1)                                             # Set height ratios for subplots
        ax0 = plt.subplot(gs[0])                                                # The first subplot
        ax1 = plt.subplot(gs[1], sharex = ax0)                                  # The second subplot

       ##### Plotting ##### 
        for y in self.rows:                                                     # Loop for amount of Vgs vaules
            self.upper += 1                                                     # Increase upper limit for next splice
            if len(self.rows)-1 < self.upper:                                   # Have we reached the final splice?
                break                                                           # Stop splicing
            y = self.df.iloc[self.rows[self.lower]:self.rows[self.upper]]       # Splice df into each value of Vgs
            self.lower += 1                                                     # Increase upper limit for next splice
            legend = y.iloc[0,0]                                                # Find what Vgs equals to every splice
            ax0.plot(y[self.columns[1]],y[self.columns[2]], '-', label=f"{self.columns[0]}: {legend}") # Plot top graph with legend
            ax1.plot(y[self.columns[1]],y[self.columns[3]], '-')                # Plot bottom graph

        ##### Labeling Plot #####   
        plt.subplots_adjust(hspace=.0)                                          # Remove vertical gap between subplots
        fig.suptitle(f"{self.name}: {self.columns[2]} & {self.columns[3]} vs. {self.columns[1]}",fontsize='18') # Title is name of part and test performed
        Labeloffset(ax1, label=self.columns[1], axis="x")                       # Label x axis
        Labeloffset(ax0, label=self.columns[2], axis="y")                       # Label top graph y axis
        Labeloffset(ax1, label=self.columns[3], axis="y")                       # Label bottom graph y axis
        plt.savefig(savefile+self.name+'Loops+Transconductance.png')            # Saving plot to png file
        return  

    def TimeTest(self): 
        #### Plotting ##### 
        for y in self.rows:                                                     # Loop for amount of big sweep vaules
            self.upper += 1                                                     # Increase upper limit for next splice
            if len(self.rows)-1 < self.upper:                                   # Have we reached the final splice?
                break                                                           # Stop splicing
            y = self.df.iloc[self.rows[self.lower]:self.rows[self.upper]]       # Splice df into each value of big sweep
            self.lower += 1                                                     # Increase upper limit for next splice
            legend1 = y.iloc[0,0]                                               # Find what big sweep equals to every splice
            legend2 = y.iloc[0,1]   
            plt.plot(y[self.columns[3]],y[self.columns[2]], '-', label=f"{self.columns[0]}: {legend1}\n{self.columns[1]}: {legend2}") # Plot small sweep(xaxis) & Ids(y-axis)

        ##### Labeling Plot #####   
        plt.title(f"{self.name}: {self.columns[2]} vs. {self.columns[3]}",fontsize='20') # Title is name of part and test performed
        plt.xlabel(self.columns[3])                                             # x axis is time
        plt.ylabel(self.columns[2])                                             # y axis is measured
        plt.legend()                                                            # Legend is different splicings
        plt.tight_layout()                                                      # Make plot fit inside window
        plt.savefig(savefile+self.name+'_Timetest.png')                         # Saving plot to png file
        plt.show()                                                              # Make plot visible
        return  

class Timer:    
    def __init__(self): 
        self._start_time = None 

    def start(self):    
        self._start_time = time.perf_counter()  
        return  

    def stop(self): 
        elapsed_time = time.perf_counter() - self._start_time   
        self._start_time = None 
        print(f"Elapsed time: {elapsed_time:0.6f} seconds") 
        return elapsed_time 
t = Timer() 

class Graphs_Overlay:   
    def __init__(self,name0,name1): 
        self.name0 = name0                                                      # Input first sheet to graph
        self.name1 = name1                                                      # Input second sheet to graph
        self.save0 = savefile+self.name0+'.csv'                                 # Path and name1 of csv file to call in one: self.save
        self.save1 = savefile+self.name1+'.csv'                                 # Path and name2 of csv file to call in one: self.save
        self.df0 = pd.read_csv(self.save0,index_col=0)                          # Read first csv file, removes index column
        self.df1 = pd.read_csv(self.save1,index_col=0)                          # Read second csv file, removes index column
        self.columns0 = list(self.df0)                                          # Lists inputs then outputs
        self.columns1 = list(self.df1)                                          # Lists inputs then outputs

        ##### Splicing First Dataframe #####    
        df01 = self.df0.copy(deep=True)                                         # Copy dataframe, leaving first one untouched
        df01['step'] = df01[self.columns0[0]].diff()                            # Create new column to see when big sweep steps up
        df01.query('`step` != 0', inplace=True)                                 # Find first rows of each big sweep values
        orows = self.df0.shape[0]                                               # Find how many rows there are in orignial data frame
        if df01.shape[0] == 1:                                                  # If only sweeping one value
            self.rows0 = [0, orows]                                             # Get row value from original data frame and create splice
        else:   
            rows = df01.index.array                                             # Create array to represent index values where big sweep chagnes
            self.rows0 = np.append(rows,orows)                                  # Add final upper limit of splice

        ##### Splicing Second Dataframe #####   
        df11 = self.df1.copy(deep=True)                                         # Copy dataframe, leaving first one untouched
        df11['step'] = df11[self.columns1[0]].diff()                            # Create new column to see when big sweep steps up
        df11.query('`step` != 0', inplace=True)                                 # Find first rows of each big sweep values
        orows = self.df1.shape[0]                                               # Find how many rows there are in orignial data frame
        if df11.shape[0] == 1:                                                  # If only sweeping one value
            self.rows1 = [0, orows]                                             # Get row value from original data frame and create splice
        else:   
            rows = df11.index.array                                             # Create array to represent index values where big sweep chagnes
            self.rows1 = np.append(rows,orows)                                  # Add final upper limit of splice    

       ##### Setup for Plot #####   
        plt.clf()                                                               # Clear active plots
        self.upper0 = 0                                                         # Variable for determining the upper limit of the splice
        self.lower0 = 0                                                         # Variable for determining the lower limit of the splice
        self.upper1 = 0                                                         # Variable for determining the upper limit of the splice
        self.lower1 = 0                                                         # Variable for determining the lower limit of the splice
        return  

    def Loops_Overlay(self):    
        fig, ax0 = plt.subplots()                                               # Setup for Plot
        ax1 = ax0.twiny()                                                       # Overlay Plots, 2 different y-axis

        #### Plotting first csv #####   
        for y in self.rows0:                                                    # Loop for amount of big sweep vaules
            self.upper0 += 1                                                    # Increase upper limit for next splice
            if len(self.rows0)-1 < self.upper0:                                 # Have we reached the final splice?
                break                                                           # Stop splicing
            y = self.df0.iloc[self.rows0[self.lower0]:self.rows0[self.upper0]]  # Splice df into each value of big sweep
            self.lower0 += 1                                                    # Increase upper limit for next splice
            legend = y.iloc[0,0]                                                # Find what big sweep equals to every splice
            ax0.plot(y[self.columns0[1]],y[self.columns0[2]], '-', label=f"{self.columns0[0]}: {legend}") # Plot small sweep(xaxis) & Ids(y-axis)

        #### Plotting second #####  
        for y in self.rows1:                                                    # Loop for amount of big sweep vaules
            self.upper1 += 1                                                    # Increase upper limit for next splice
            if len(self.rows1)-1 < self.upper1:                                 # Have we reached the final splice?
                break                                                           # Stop splicing
            y = self.df1.iloc[self.rows1[self.lower1]:self.rows1[self.upper1]]  # Splice df into each value of big sweep
            self.lower1 += 1                                                    # Increase upper limit for next splice
            legend = y.iloc[0,0]                                                # Find what big sweep equals to every splice
            ax1.plot(y[self.columns1[1]],y[self.columns1[2]], '-', label=f"{self.columns1[0]}: {legend}") # Plot small sweep(xaxis) & Ids(y-axis)

        ##### Labeling Plot #####   
        plt.title(f"{self.name0} & {self.name1}",fontsize='20')                 # Title is name of part and test performed
        Labeloffset(ax0, label=self.columns0[1], axis="x")                      # Label first x axis
        Labeloffset(ax1, label=self.columns1[1], axis="x")                      # Label second x axis
        Labeloffset(ax0, label=self.columns0[2], axis="y")                      # Label y axis
        ax1.yaxis.set(label_position='right',offset_position='right')   
        ax0.legend()                                                            # Legend of first plot
        ax1.legend()                                                            # Legend of second plot
        plt.tight_layout()                                                      # Make plot fit inside window
        plt.savefig(f"{savefile+self.name0} & {self.name1}.png")                # Saving plot to png file
        return  

class Labeloffset():    
    def __init__(self,  ax, label="", axis="y"):    
        formatter = mticker.ScalarFormatter(useMathText=True)                   # Convert 1e-8 to x10^-8
        ax.yaxis.set_major_formatter(formatter)                                 # Show conversion
        self.axis = {"y":ax.yaxis, "x":ax.xaxis}[axis]  
        self.label=label    
        ax.callbacks.connect(axis+'lim_changed', self.update)
        ax.figure.canvas.draw()
        self.update(None)
        return

    def update(self, lim):
        fmt = self.axis.get_major_formatter()
        self.axis.offsetText.set_visible(False)
        self.axis.set_label_text(self.label + " "+ fmt.get_offset() )
        return