"""

Python Quonset Microwave QMRDK Driver

Copyright (c) 2015 by Bruno Espinoza

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in
all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
THE SOFTWARE.

"""

#imports
import usbtmc
import sys
import math

#define constants based on the QMRDK datasheet

#USBTMC commands
QMRDK_USBTMC_CLS = "*CLS"
QMRDK_USBTMC_RST = "*RST"
QMRDK_USBTMC_IDN = "*IDN?"
QMRDK_USBTMC_TRG = "*TRG" #Trigger: Needed for certain sweep types

#system - get commands
QMRDK_GET_FIRMWARE = "SYST:FIRM?"
QMRDK_GET_SYSTEMID = "SYST:IDEN?"
QMRDK_GET_MODEL_NUMBER = "SYST:MODNUM?"
QMRDK_GET_SERIAL_NUMBER = "SYST:SERNUM?"
QMRDK_GET_STATUS = "SYST:STAT?"
QMRDK_GET_TEMPERATURE = "SYST:TEMP?"
QMRDK_GET_VERSION = "SYST:VERS?"
QMRDK_GET_BLUETOOTH_STATUS = "SYST:BLUE?"
QMRDK_GET_ERROR = "SYST:ERR?"
#system - set commands
QMRDK_CLEAR_MEMORY = "SYST:CLRM "
QMRDK_RESET_DEVICE = "SYST:PRES"

#frequency - get commands
QMRDK_GET_LOCK_STATUS = "FREQ:LOCK?"
QMRDK_GET_FREQUENCY_DIVIDER = "FREQ:REF:DIV?"
#frequency set commands
QMRDK_SET_FREQUENCY_DIVIDER = "FREQ:REF:DIV "

#power
QMRDK_SET_RF_POWER = "POWE:RF "
QMRDK_GET_RF_STATUS = "POWE:RF?"


#sweep get commands
QMRDK_GET_FREQUENCY_START = "SWEEP:FREQSTAR"
QMRDK_GET_FREQUENCY_STOP = "SWEEP:FREQSTOP?"
QMRDK_GET_RAMPTIME = "SWEEP:RAMPTIME?"
QMRDK_GET_SWEEP_TYPE = "SWEEP:TYPE?"

#sweep set commands
QMRDK_SET_FREQUENCY_START = "SWEEP:FREQSTAR "
QMRDK_SET_FREQUENCY_STOP = "SWEEP:FREQSTOP "
QMRDK_SET_RAMPTIME = "SWEEP:RAMPTIME "
QMRDK_START_SWEEP = "SWEEP:START"
QMRDK_STOP_SWEEP = "SWEEP:STOP"
QMRDK_SET_SWEEP_TYPE = "SWEEP:TYPE "

#capture commands ~ only USB is supported for now
QMRDK_GET_CAPTURE_FRAME = "CAPT:FRAM?"
QMRDK_SET_CAPTURE_FRAME = "CAPT:FRAM "

#bluetooth commands, not implemented 
#QMRDK_GET_STREAM = "CAPT:STRE?"
#QMRDK_SET_STREAM = "CAPT:STRE "

#types of SWEEP
QMRDK_RAMP_SWEEP = 0
QMRDK_TRIANGLE_SWEEP = 1
QMRDK_AUTOMATIC_TRIANGLE_SWEEP = 2
QMRDK_CW_SWEEP = 3


class qmrdk:
    def __init__(self, vendor_id, product_id, ty_num='hex'):
        if (ty_num == 'hex'):
            vid = int(str(vendor_id), 16)
            pid = int(str(product_id), 16)
        elif (ty_num == 'dec'):
            vid = vendor_id
            pid = product_id
        else:
            raise ValueError('Only hex or dec are accepted!!!')
        
        #usbtmc expects in decimal
        self.qmrdk_device = usbtmc.Instrument(vid, pid)
        
        #set some useful variables
        self.is_sweep_on = 0 #is TX working?
        self.is_radio_on = 0 #is the radio working?
        self.sweep_type = 3 #sweep type = Ramp, Automatic Triangle, Triangle or CW
        self.sweep_time = 16000
        self.freq_config = [2.4, 2.5, 16] #frequency configuration
        
        #force a reset
        self.qmrdk_device.write(QMRDK_RESET_DEVICE)
    
    #GET Commands
    
    def qmrdk_get_status(self):
        "Returns the Status No and the Description"
        val = self.qmrdk_device.ask(QMRDK_GET_STATUS)
        val = val.split(',')
        
        val[0] = int(val[0]) #get the error in number
        return val
    
    def qmrdk_get_sweep_status(self):
        "Returns ON or OFF accordingly to the Sweep status"
        ret_table = ['OFF', 'ON']
        return ret_table[self.is_sweep_on]
    
    def qmrdk_get_radio_status(self):
        "Returns ON or OFF accordingly to the radio status"
        ret_table = ['OFF', 'ON']
        val = int(self.qmrdk_device.ask(QMRDK_GET_RF_STATUS))
        return ret_table[val] #or ret_table[self.is_radio_on]
    
    def qmrdk_get_sweep_configuration(self):
        "Returns the Sweep Type and the Sweep Ramp Time"
        sweep_table = ['RAMP', 'TRIANGLE', 'AUTO_TRIANGLE', 'CW']
        
        ret_table = []
        val = int(self.qmrdk_device.ask(QMRDK_GET_SWEEP_TYPE))
        ret_table.append(sweep_table[val])
        
        val = int(self.qmrdk_device.ask(QMRDK_GET_RAMPTIME))
        ret_table.append(val)
        
        return ret_table
        
    def qmrdk_get_frequency_configuration(self):
        "Returns the Start Frequency, Stop Frequency and Frequency Divider"
        ret_table = []
        val = float(self.qmrdk_device.ask(QMRDK_GET_FREQUENCY_START))
        ret_table.append[val]
        val = float(self.qmrdk_device.ask(QMRDK_GET_FREQUENCY_STOP))
        ret_table.append[val]
        val = float(self.qmrdk_device.ask(QMRDK_GET_FREQUENCY_DIVIDER))
        ret_table.append[val]
        
        return ret_table
    
    def qmrdk_get_system_info(self):
        "Returns an string with the Product Number, Serial Number, Firmware Version and Device ID"
        val = self.qmrdk_device.ask(QMRDK_USBTMC_IDN)
        val = val.split(',')
        return val
    
    def qmrdk_get_temperature(self):
        "Returns the device internal temperature"
        val = self.qmrdk_device.ask(QMRDK_GET_TEMPERATURE)
        val = float(val)
        return val
    
    
    #SET Commands
    def qmrdk_set_radio_power_status(self, rw=0):
        "Turns ON or OFF the radio, depending if a 1 or a 0 is passed"
        rw = int(rw > 0) #force a 0 or a 1
        raw_cmd = QMRDK_SET_RF_POWER + str(rw)
        self.qmrdk_device.write(raw_cmd)
    
    def qmrdk_set_sweep_configuration(self, type_sweep, sweep_time=16000):
        "Sets the Sweep Type and the Sweep Time (Ramp Time)"
        #check the types
        if (type_sweep > 3 or type_sweep < 0):
            raise ValueError('Only Sweep Type supported are RAMP, TRI, AUTO and CW!!!!')
        
        #check the sweep time
        if (sweep_time > 65536 or sweep_time < 1):
            raise ValueError('Sweep Time must be between 1 to 65536 ms!!!')
        
        #TODO: Validate with the formulas that the Sweep Time is valid.
        self.qmrdk_device.write(QMRDK_SET_SWEEP_TYPE + str(type_sweep))
        self.qmrdk_device.write(QMRDK_SET_RAMPTIME + str(sweep_time))
        
        #check if an error has ocurred
        val = self.qmrdk_device.ask(QMRDK_GET_ERROR)
        val = val.split(',')
        
        if (int(val[0]) == 201):
            raise ValueError('Invalid Sweep Type for this configuration')
        
        self.sweep_type = type_sweep
        self.sweep_time = sweep_time
    
    def qmrdk_set_frequency_configuration(self, start_frequency=2.4, end_frequency=2.5, freq_div=1):
        "Sets the Start and Stop Frequency + Frequency Divider"
        
        #check the frequencies
        if (start_frequency > 2.5 or start_frequency < 2.4):
            raise ValueError('Frequency only valid on 2.4 to 2.5 GHz range!!!!')
        
        if (end_frequency > 2.5 or end_frequency < 2.4):
            raise ValueError('Frequency only valid on 2.4 to 2.5 GHz range!!!!')
        
        if (freq_div > 256 or freq_div < 1):
            raise ValueError('Frequency Divisor only valid on 1 to 256 range!!!')
        
        self.qmrdk_device.write(QMRDK_SET_FREQUENCY_START + str(start_frequency))
        self.qmrdk_device.write(QMRDK_SET_FREQUENCY_STOP + str(end_frequency))
        self.qmrdk_device.write(QMRDK_SET_FREQUENCY_DIVIDER + str(freq_div))
            
        self.freq_config[0] = float(start_frequency)
        self.freq_config[1] = float(end_frequency)
        self.freq_config[2] = int(freq_div)
    
    def qmrdk_set_radio(self, rw=0):
        "Turn ON the Sweep and the radio transmission, depending if a 1 or a 0 is passed"
        
        rw = int(rw > 0) #force a 0 or 1
        
        if (rw == 0): #stop everything
            self.qmrdk_device.write(QMRDK_STOP_SWEEP)
        else:
            self.qmrdk_device.write(QMRDK_START_SWEEP)
        
        self.qmrdk_device.write(QMRDK_SET_RF_POWER + str(rw))
        self.is_radio_on = rw
        self.is_sweep_on = rw
    
    #Capture Commands
    def qmrdk_get_data_frame(self, frame_val = 1024):
        "Return the indicated number of frames"
        
        #only can capture up to 4096 frames
        if (frame_val > 4096):
            print "[qmrdk_driver]: Invalid frame rate, clipping to 4096..."
            frame_val = 4096
        
        #not negatives allowed
        if (frame_val < 0):
            print "[qmrdk_driver]: Invalid frame rate, clipping to 1024..."
            frame_val = 1024
        
        ret_val = []
        no_captures = math.ceil(frame_val / 31)
        self.qmrdk_device.write(QMRDK_SET_CAPTURE_FRAME + str(frame_val))
        
        for i in range(0, int(no_captures)+1):
            str_hex = self.qmrdk_device.ask(QMRDK_GET_CAPTURE_FRAME)
            hex_l = len(str_hex)
            
            for k in range(0,hex_l-1,4):
                tmp = int(str_hex[k:k+4], 16)
                ret_val.append(tmp)
                
            #if the type of Sweep is 0 or 1, then trigger the device to keep the data flowing
            if (self.sweep_type < 2):
                self.qmrdk_device.write(QMRDK_USBTMC_TRG)
        

            #print "[qmrdk_driver]: QMRDK board triggered..."
            
        return ret_val
        
    
    #Debug commands - Only use if you know what are you doing!!!
    def send_raw_command(self, raw_cmd):
        self.qmrdk_device.write(raw_cmd)
    
    def send_raw_ask(self, raw_cmd):
        return self.qmrdk_device.ask(raw_cmd)
    
    def qmrdk_get_last_error(self):
        "Returns the Error No and the Description"
        val = self.qmrdk_device.ask(QMRDK_GET_ERROR)
        val = val.split(',')
        
        val[0] = int(val[0]) #get the error in number
        return val
