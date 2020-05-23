"""
" Edit below this line to fit your needs
"""


## Define voltages
##
FULLBATVOLT = 14.6 # 100% chargé
# Discharged voltage (for a single battery);
#   i.e. 1.05V for a NiMH battery, or 3.4V for a LiPo battery
#   You should use a conservative value in order to avoid destructive
#   discharging
LOWBATVOLT = 12
#LOWBATVOLT = 3.4
# Dangerous voltage
#   You should really not go below this voltage.
DNGBATVOLT = 10

# Value (in ohms) of the lower resistor from the voltage divider, connected to
#   the ground line (1 if no voltage divider). Default value (3900) is for a 
#   battery pack of 8 NiMH batteries, providing 11.2V max, stepped down to about
#   3.2V max.
LOWRESVAL = 1000
# Value (in ohms) of the higher resistor from the voltage divider, connected to 
#   the positive line (0 if no voltage divider). Default value (10000) is for a
#   battery pack of 8 NiMH batteries, providing 11.2V max, stepped down to about
#   3.2V max.
HIGHRESVAL = 5500
# Voltage value measured by the MCP3008 when batteries are fully charged
# It should be near 3.3V due to Raspberry Pi GPIO compatibility)
VHIGHBAT = (FULLBATVOLT)*(LOWRESVAL)/(LOWRESVAL+HIGHRESVAL)
# Voltage value measured by the MCP3008 when batteries are discharged
VLOWBAT = (LOWBATVOLT)*(LOWRESVAL)/(LOWRESVAL+HIGHRESVAL)
# Voltage value measured by the MCP3008 when batteries voltage is dangerously
#   low
VDNGBAT = (DNGBATVOLT)*(LOWRESVAL)/(LOWRESVAL+HIGHRESVAL)

# ADC voltage reference (3.3V for Raspberry Pi)
ADCVREF = 3.3

# Compensation due to the difference between ADC voltage reference and 
#   max value for voltage through resistor divider
#   i.e. : with the given resistances values, VREF is 3.3 V, and max voltage
#   through resistor divider is about 3.14V, leading to about 4.8% deviation.
# This compensation is used to correct computed battery voltage return by
#   network queries
VCOMP = 1+(ADCVREF-VHIGHBAT)/ADCVREF

## Define expected ADC values
# MCP23008 channel to use (from 0 to 7)
ADCCHANNEL = 0
# MCP23008 should return this value when batteries are fully charged
#  * 3.3 is the reference voltage (got from Raspberry Pi's +3.3V power line)
#  * 1024.0 is the number of possible values (MCP23008 is a 10 bit ADC)
ADCHIGH = VHIGHBAT / (ADCVREF / 1024.0)
# MCP23008 should return this value when batteries are discharged
#  * 3.3 is the reference voltage (got from Raspberry Pi's +3.3V power line)
#  * 1024.0 is the number of possible values (MCP23008 is a 10 bit ADC)
ADCLOW = VLOWBAT / (ADCVREF / 1024.0)
# MCP23008 should return this value when batteries atteigns dangerous voltage
#  * 3.3 is the reference voltage (got from Raspberry Pi's +3.3V power line)
#  * 1024.0 is the number of possible values (MCP23008 is a 10 bit ADC)
ADCDNG = VDNGBAT / (ADCVREF / 1024.0)
# MCP should return a value lower than this one when no battery is plugged.
# You should not use 0 because value is floatting around 0 / 150 when nothing
#  is plugged to a analog channel. 
ADCUNP = 300 # No battery plugged
# Maximal MCP return value to consider as "voltage bounce" when kill switch is
#  activated and voltage rises again as current use is reduced. This avoid to
#  switch from dangerous mode to low battery mode and back for a long time.
ADCDNGBOUNCE = ADCDNG + 200

# Refresh rate (ms)  = 30sec
REFRESH_RATE = 30000

# Display some debug values when set to 1, and nothing when set to 0
DEBUGMSG = 0
