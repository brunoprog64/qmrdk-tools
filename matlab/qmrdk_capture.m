%Capture for QMRDK Radar
%Samples will be written to a binary file called radar.out

clear;
close all;

%QMRDK Device Parameters
freq_start = 2.4; %in GHz
freq_end = 2.5; %in GHz
sweep_type = 2; %0 to 3 (Ramp, Triangle, Auto Triangle and CW)
sweep_time = 4; %in ms
frame_no = 2048 ;
secs_capture = 30;

bin_file = 'radar.out'; %will write to a file

%connect to the device
qmrdk_device = instrfind('Type', 'visa-usb', 'RsrcName', 'USB0::0x2012::0x0013::0036::0::INSTR', 'Tag', '');

% Create the VISA-USB object if it does not exist
% otherwise use the object that was found.
if isempty(qmrdk_device)
    qmrdk_device = visa('NI', 'USB0::0x2012::0x0013::0036::0::INSTR');
else
    fclose(qmrdk_device);
    qmrdk_device = qmrdk_device(1);
end

% Connect to instrument object, obj1.
fopen(qmrdk_device);

% Communicating with instrument object, obj1.
data = query(qmrdk_device, '*IDN?');

fprintf('Found a %s\n',data);

%turn off the radio
fprintf(qmrdk_device, 'POWE:RF 0');
%stop sweep
fprintf(qmrdk_device, 'SWEEP:STOP');


%set parameters
%set frequency
raw_cmd = sprintf('SWEEP:FREQSTAR %.1f', freq_start);
fprintf(qmrdk_device, raw_cmd);
raw_cmd = sprintf('SWEEP:FREQSTOP %.1f', freq_end);
fprintf(qmrdk_device,raw_cmd);

%set sweep time and type
raw_cmd = sprintf('SWEEP:RAMPTIME %d', sweep_time);
fprintf(qmrdk_device, raw_cmd);
raw_cmd = sprintf('SWEEP:TYPE %d', sweep_type);
fprintf(qmrdk_device,raw_cmd);

%compute the frequency division based on the formula
freq_div = sweep_time / ((freq_end - freq_start)*83.8866);
freq_div = round(freq_div);

if (freq_div == 0)
    freq_div = 1;
end

%set frequency division
raw_cmd = sprintf('FREQ:REF:DIV %d', freq_div);
fprintf(qmrdk_device, raw_cmd);

%start sweep
fprintf(qmrdk_device, 'SWEEP:START');
%turn on radio
fprintf(qmrdk_device, 'POWE:RF 1');

%capture some data
rx_data = zeros(1,frame_no);
rec_rx_data = [];

capture_idx = 1;

%rec_rx_data = zeros(1, frame_no*secs_capture);
% rx_clutter = zeros(1,frame_no);
% figure(10)
% lHandle = line(nan, nan);
% grid on;
% title('Real Time Capture (RX)');
% ylim([-2.45 2.45]);

%RX data
for i=1:secs_capture
    data_idx = 1;

    fprintf('Capturing second %d...\n', i);
    raw_cmd = sprintf('CAPT:FRAM %d', frame_no);
    fprintf(qmrdk_device, raw_cmd);
    fcaps = ceil(frame_no / 31);
    
    for k=1:fcaps
        val = query(qmrdk_device, 'CAPT:FRAM?');
        
        for l=1:4:length(val)-1
            tmp = val(l:l+4-1);
            rx_data(data_idx) = hex2dec(tmp);
            data_idx = data_idx + 1;
        end
        %trigger the device
        fprintf(qmrdk_device, '*TRG');
    end
    
%     X = get(lHandle, 'XData');
%     X = 1:length(rx_data);
%     Y = get(lHandle, 'YData');
%     
%     rx_data2 = 5 ./ (power(2,16) ./ rx_data);
%     rx_data2 = rx_data2 - (5/2);
%     
%     Y = rx_data2 - rx_clutter;
%     set(lHandle, 'XData', X, 'YData', Y);
%     pause(0.01);
%     
%     rx_clutter = rx_data2;
    
    rec_rx_data = [rec_rx_data rx_data];
end

%stop the capture
%turn off the radio
fprintf(qmrdk_device, 'POWE:RF 0');
%stop sweep
fprintf(qmrdk_device, 'SWEEP:STOP');
fclose(qmrdk_device); %close the device

%write the data to a file
magic_val = 'RDO';
%params are: Start Freq, Stop Freq, Type Sweep, Sweep Time, FramesperSecond
radar_params = [round(freq_start*1000), round(freq_end*1000), sweep_type, sweep_time, frame_no]; 
radar_params = int16(radar_params);

fid = fopen(bin_file, 'wb');
fwrite(fid, magic_val, 'uint8'); %write signature
fwrite(fid, radar_params, 'int16'); %write params
fwrite(fid, rec_rx_data, 'double');
fclose(fid);

fprintf('Data writted to %s...!\n', bin_file);

%run the analysis
if (sweep_type == 3)
    run('analyze_doppler.m');
else
    run('analyze_range.m');
end