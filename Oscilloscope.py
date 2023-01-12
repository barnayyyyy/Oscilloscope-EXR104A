# Microelectonic Instrumentation - Spring 2023
# John Barney, Lucas Nichols, Adam Hubbard

import pyvisa as visa

KEYSIGHT_ADDRESS = "TCPIP0::169.254.205.81::INSTR"
KEYSIGHT_UTCADDRESS = "TCPIP0::10.44.11.1::INSTR"
GLOBAL_TOUT = 10000

rm = visa.ResourceManager()
OS = rm.open_resource(KEYSIGHT_ADDRESS)
OS.timeout = GLOBAL_TOUT
print(OS.query('*IDN?'))
OS.clear()
