#!/usr/bin/env python

#QMRDK Driver - Dump samples app
#2015 (c) by Bruno Espinoza

#This application captures data from the QMRDK radar and store it in a .bin file that can be opened with Matlab

#Permission is hereby granted, free of charge, to any person obtaining a copy
#of this software and associated documentation files (the "Software"), to deal
#in the Software without restriction, including without limitation the rights
#to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
#copies of the Software, and to permit persons to whom the Software is
#furnished to do so, subject to the following conditions:

#The above copyright notice and this permission notice shall be included in
#all copies or substantial portions of the Software.

#THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
#IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY
#FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
#AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
#LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
#OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
#THE SOFTWARE.

import optparse
import qmrdk as qm
import struct

#parser for options
parser = optparse.OptionParser();
parser.add_option('--f', action="store", dest="file_out", default="radar.out", help="File Name of Capture")
parser.add_option('--s', action="store", dest="frame_rate", default="1024", help="Frame Rate: [0 - 4096], default=1024.")
parser.add_option('--fst', action="store", dest="frequency_start", default="2.4", help="Initial Frequency in GHz")
parser.add_option('--fed', action="store", dest="frequency_stop", default="2.5", help="Final Frequency in GHz")
parser.add_option('--fdiv', action="store", dest="frequency_div", default="1", help="Frequency Divider: [1 to 256]")
parser.add_option('--swty', action="store", dest="sweep_type", default="3", help="Type of Sweep: 0 = Ramp / 1 = Triangle / 2 = Auto Triangle / 3 = CW")
parser.add_option('--swtim', action="store", dest="sweep_time", default="100", help="Sweep Time: [1 to 65536]")
parser.add_option('--dev', action="store", dest="device_address", default="2012:0013", help="USB Device Address of the QMRDK (Def: 2012:0013)")

options, args = parser.parse_args();
dump_file = open(options.file_out, 'wb') #binary write
no_frames = int(options.frame_rate)

start_freq = float(options.frequency_start)
stop_freq = float(options.frequency_stop)
freq_div = int(options.frequency_div)

type_sweep = int(options.sweep_type)
sweep_time = int(options.sweep_time)
qmrdk_addr = options.device_address.split(':')


radar = qm.qmrdk(qmrdk_addr[0], qmrdk_addr[1]) #connect to the device
rad_info = radar.qmrdk_get_system_info() #get system info
temp_val = radar.qmrdk_get_temperature() #get temperature

print "Found a " + rad_info[0] + ": " + rad_info[1] + " " + rad_info[3]
print "Device Current Temperature is: " + str(temp_val)

print "Dumping samples at " + str(no_frames) + " Samples/second in file: " + options.file_out

radar.qmrdk_set_sweep_configuration(type_sweep, sweep_time) #CW and a simple sweep time
radar.qmrdk_set_frequency_configuration(start_freq, stop_freq, freq_div) #Freq Start, End and Freq Div
radar.qmrdk_set_radio(1) #start the Radar

#capture forever and plot
while 1:
    try:
        values = radar.qmrdk_get_data_frame(no_frames) #grab the samples
        for k in range(0,len(values)):
            dump_file.write(struct.pack('f', values[k]))
        
        #safety measure, look at the temperature and if it is too hot, shutdown
        stat = radar.qmrdk_get_status()
        
        if (stat[0] == 110):
            print "Panic! Over temperature. Device will be shutdown..."
            dump_file.close()
            radar.qmrdk_set_radio(0) #stop the radar
            break
                    
    except KeyboardInterrupt:
        dump_file.close()
        radar.qmrdk_set_radio(0) #stop the radar
        print "Interrupt detected, closing..."
        break
