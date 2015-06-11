#!/usr/bin/env python

#CSSE7411 - Final Project
#Activity Detection Sensing using FMCW Radar

#main entry point
IS_PLOT = False
RPI_PIN_TX = 11
RPI_PIN_RX = 13

RPI_RX_STATUS = True
RPI_TX_STATUS = True

IS_MODE_WALL = True #begin as wall
count_val = 10
idx_event = 0

import qmrdk as qm
import numpy as np
import time
import os
import Queue
import thread
import bluetooth as bt

if (IS_PLOT == True):
    import matplotlib.pyplot as plt

#queue for data
config_queue = Queue.Queue()
event_queue = Queue.Queue()

#events
event_list = "OFST" #out range, fall, standing, sitting

#reconfiguration of the radar
def configure_radar_params(radar, stfreq, edfreq, swtype, swtime):
    #stop the radar
    radar.qmrdk_set_radio(0) #stop the radar
    
    #reconfigure
    freq_div = (sweep_time) / ((stop_freq - start_freq)*83.8866)
    freq_div = round(freq_div)
    
    if (freq_div == 0):
        freq_div = 1

    radar.qmrdk_set_sweep_configuration(swtype, swtime) #CW and a simple sweep time
    radar.qmrdk_set_frequency_configuration(stfreq, edfreq, freq_div) #Freq Start, End and Freq Div
    radar.qmrdk_set_radio(1) #start the Radar
    
    BW = (edfreq - stfreq) * 1e9
    return BW #return the new bandwidth


#bluetooth thread
def bluetooth_thread(config_queue, v):
    #set the bluetooth connection
    while True:
        radar_server = bt.BluetoothSocket(bt.RFCOMM)
        radar_server.bind(("",bt.PORT_ANY))
        radar_server.listen(1)
        port = radar_server.getsockname()[1]
        uuid = "94f39d29-7d6d-437d-973b-fba39e49d4ee" #random UUID (https://www.uuidgenerator.net/version1)
        bt.advertise_service( radar_server, "QMRDK App",
                           service_id = uuid,
                           service_classes = [ uuid, bt.SERIAL_PORT_CLASS ],
                           profiles = [ bt.SERIAL_PORT_PROFILE ], 
        #                   protocols = [ OBEX_UUID ] 
                            )
        print "[bluetooth_thread]: Waiting for connection on RFCOMM channel %d" % port
        client_sock, client_info = radar_server.accept()
        print "[bluetooth_thread]: Accepted connection from ", client_info
        client_sock.settimeout(2)

        try:
            while True: #loop waiting for data
                client_sock.send("0") #keep alive?
                #check for the event queue
                if not event_queue.empty():
                    event_val = event_queue.get()
                    client_sock.send(event_val) #notify the Android App

                try:
                    rx_data_bt = client_sock.recv(1024)

                    if len(rx_data_bt) < 3: continue
                    #parse if is a config message
                    pream = rx_data_bt[0:3]
                    if (pream == 'RDK'): #preamble
                        print "Received Configuration: ", rx_data_bt.split('-')
                        #put the config in the queue
                        config_queue.put(rx_data_bt)
                        
                except IOError:
                    continue #if timeout, just keep trying

        except IOError: #error on the send, means that the device is not there
            pass #nothing    
        
        print "[bluetooth_thread]: Client ", client_info, " disconnected."
        client_sock.close()
        radar_server.close()
        print "[bluetooth_thread]: Restarting listening"


radar = qm.qmrdk(2012, 13) #connect to the device
rad_info = radar.qmrdk_get_system_info() #get system info
temp_val = radar.qmrdk_get_temperature() #get temperature

print "Found a " + rad_info[0] + ": " + rad_info[1] + " " + rad_info[3]
print "Device Current Temperature is: " + str(temp_val)

if (IS_PLOT == False):
    print "* Plotting in real time was disabled..."
else:
    print "* Plotting in real time was enabled..."

#detect if we are running in the Raspberry Pi
if (os.uname()[4][:3] == 'arm'):
    IS_RPI = True
    print "* Raspberry Pi device detected, enabling antenna switching..."
    import RPi.GPIO as rpgpio #import GPIO libraries
    
    rpgpio.setmode(rpgpio.BOARD) #configure the GPIO
    
    rpgpio.setup(RPI_PIN_RX, rpgpio.OUT, pull_up_down = rpgpio.PUD_DOWN)
    rpgpio.setup(RPI_PIN_TX, rpgpio.OUT, pull_up_down = rpgpio.PUD_DOWN)
    
    rpgpio.output(RPI_PIN_TX, RPI_TX_STATUS)
    rpgpio.output(RPI_PIN_RX, RPI_RX_STATUS)
else:
    IS_RPI = False
    print "* This is not a Raspberry Pi device... antenna switching will be disabled!!!"

#start a thread
#thread.start_new_thread(bluetooth_thread, (config_queue, None))
#print "* Bluetooth thread created..."

#radar parameters
start_freq = 2.4
stop_freq = 2.5

BW = (stop_freq - start_freq) * 1e9
type_sweep = qm.QMRDK_AUTOMATIC_TRIANGLE_SWEEP
sweep_time = 4
no_frames = 1024
freq_div = (sweep_time) / ((stop_freq - start_freq)*83.8866)
freq_div = round(freq_div)

fft_size = 4096

if (freq_div == 0):
    freq_div = 1

radar.qmrdk_set_sweep_configuration(type_sweep, sweep_time) #CW and a simple sweep time
radar.qmrdk_set_frequency_configuration(start_freq, stop_freq, freq_div) #Freq Start, End and Freq Div
radar.qmrdk_set_radio(1) #start the Radar

time.sleep(2) #ignore transient

orig_values_wall = np.zeros((1, no_frames))
orig_values_ceiling = np.zeros((1,no_frames))

cluter_cancel_wall = np.zeros((1, no_frames))
cluter_cancel_ceiling = np.zeros((1,no_frames))

wall_plot = np.ones((1, fft_size/2))
ceil_plot = np.ones((1, fft_size/2))

values = np.zeros((1,no_frames))

#Range Parameters
max_range = 10 #limits for reporting range
min_range = 0
noise_level = -65 #magnitude to report a change in range (needs to calibrate)

#Range Analysis
HIST_READS = 5
ceil_readings = np.zeros((1,HIST_READS))
wall_readings = np.zeros((1,HIST_READS))

wall_idx = 0
ceil_idx = 0

wall_spike = 0
ceil_spike = 0

#real time plotting
if (IS_PLOT == True):
    plt.ion()
    plt.show()

while 1:    
    #check if we need to update the radar parameters
    if not config_queue.empty():
        vals = config_queue.get()
        conf_opts = vals.split('-')
        
        print "[bluetooth]: Received request for change of configuration..."
        configure_radar_params(radar, float(conf_opts[3]), float(conf_opts[4]), int(conf_opts[1]), int(conf_opts[2]))
    
    rx_values = radar.qmrdk_get_data_frame(no_frames) #grab the samples
    values = np.array(rx_values, dtype='double')
    values = values.reshape((1,no_frames))
    
    #normalize the array
    values = 5.0 / (np.power(2,16) / values)
    values = values - 2.5
    values = values - np.mean(values) #substract the mean
    
    #do the clutter cancellation
    if IS_MODE_WALL == True:
        orig_values_wall = values;
        values = values - cluter_cancel_wall
        cluter_cancel_wall = orig_values_wall
    else:
        orig_values_ceiling = values;
        values = values - cluter_cancel_ceiling
        cluter_cancel_ceiling = orig_values_ceiling 
    
    ##take the FFT
    values_fft = np.fft.ifft(values, n=fft_size)
    values_fft = np.abs(values_fft)
    
    half_fft = values_fft[0][0:fft_size/2]
    half_fft = half_fft.reshape((1,half_fft.size))
    
    #plot
    if (IS_PLOT == True and IS_MODE_WALL == True):
        wall_plot = half_fft
        wall_plot = half_fft.reshape((1,half_fft.size))
    else:
        ceil_plot = half_fft
        ceil_plot = half_fft.reshape((1,half_fft.size))
    
    if (IS_PLOT == True):
        plt.clf() #clean the plot
        #plt.plot(values.T)
        #plt.ylim([-2.5,2.5])
        plt.subplot(211)
        plt.semilogy(wall_plot.T, 'b-') #plot
        plt.ylim([1e-6,10])
        plt.grid(True)
        plt.title("Wall Plot")
        plt.subplot(212)
        plt.semilogy(ceil_plot.T, 'b-') #plot
        plt.ylim([1e-6,10])
        plt.grid(True)
        plt.title("Ceiling Plot")
        plt.draw() 
        
        #time.sleep(0.06) #sleep briefly
    
    #convert to log scale
    values_fft = 20 * np.log10(half_fft)

    max_val = values_fft.max()
    max_idx = values_fft.argmax()
 
    range_m = (3e8 * (max_idx) * sweep_time * 1e-3) / (2*BW)
    
    

    if IS_MODE_WALL == True:
        wall_spike = abs(max_val)
        
        #if (wall_idx >= HIST_READS):
            #wall_idx = 0
            #wall_readings[0] = 0
        
        #wall_readings[0][wall_idx] = wall_spike
        #wall_idx = wall_idx + 1
        
    else:
        ceil_spike = abs(max_val)
        #if (ceil_idx >= HIST_READS):
            #ceil_idx = 0
            #ceil_readings[0] = 0
        
        #ceil_readings[0][ceil_idx] = ceil_spike
        #ceil_idx = ceil_idx + 1
        
    #activity detection section
    print wall_spike, ceil_spike
    
    if (wall_spike > 60 and ceil_spike > 60):
        print "Activity Detected: Out of Range"

    if (ceil_spike < 55 and wall_spike < 55):
        print "Activity Detected: Standing"
    
    if (ceil_spike > 40 and ceil_spike < 60 and wall_spike > 58): #if (ceil_spike > 40 and ceil_spike < 60 and wall_spike > 58): 
        print "Activity Detected: Falling"
        
    
    if (IS_RPI == True):
        #switch from antenna
        RPI_RX_STATUS = not RPI_RX_STATUS
        RPI_TX_STATUS = not RPI_TX_STATUS
        
        rpgpio.output(RPI_PIN_TX, RPI_TX_STATUS)
        rpgpio.output(RPI_PIN_RX, RPI_RX_STATUS)
        
        #switch from wall to ceiling and viceversa
        IS_MODE_WALL = not IS_MODE_WALL
