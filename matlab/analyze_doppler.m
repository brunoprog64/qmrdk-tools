%Range Analysis for QMRDK Radar
%Doppler Mode

clear;
close all;

bin_file = 'radar.out';
rec_rx_data = [];

%read the file
fid = fopen(bin_file, 'rb');

%read the magic number
tmp = fread(fid, 3, 'uint8');
tmp = char(tmp)';

if (strcmp(tmp, 'RDO') == 0) %not a Radar Out File
    fclose(fid);
    error('This is not a valid radar file!!!!');
end

%read the parameters 
%params are: Start Freq, Stop Freq, Type Sweep, Sweep Time, FramesperSecond
radar_params = fread(fid, 5, 'int16');

%parse and assign parameters to the variables
freq_base = radar_params(1) / 1000;
no_frame = radar_params(5);
pulse_time = radar_params(4);
type_swipe = radar_params(3);

%parameters
samp_pulse = pulse_time * no_frame;
pulse_per_seconds = no_frame / samp_pulse;

%validation
if (type_swipe ~= 3) %is CW
    fclose(fid);
    error('Cannot process FM-CW dumps!!!!');
end

%parse the numbers
while (~feof(fid))
    tmp = fread(fid, 128, 'double'); %increase the number for speed
    rec_rx_data = [rec_rx_data tmp'];
end
fclose(fid);


sec_data = round(length(rec_rx_data) / no_frame);
fprintf('Loaded %d seconds of data...\n', round(length(rec_rx_data) / no_frame));

%normalyze
rec_rx_data = 5 ./ (power(2,16) ./ rec_rx_data); %normalyze to 0 to 5v.
rec_rx_data = rec_rx_data - (5/2);

rec_clutter = zeros(1,no_frame);
radar_graph = zeros(sec_data, no_frame);

for i=1:sec_data
    st_pt = ((i-1)*no_frame) + 1;
    ed_pt = i*no_frame;
    curr_block = rec_rx_data(st_pt:ed_pt);
    
    %curr_block = curr_block - mean(curr_block);
    curr_block = curr_block - rec_clutter;
    
    fft_data = fft(curr_block, no_frame*2);
    fft_data = abs(fft_data);
    fft_data = 20*log10(abs(fft_data));
    
    radar_graph(i,:) = fft_data(1:end/2);
    %rec_clutter = curr_block;
end

freq_axis = 1:no_frame/2;
speed_axis = (freq_axis * 3e8) / (freq_base*1e9);
time_axis = linspace(1,sec_data, length(rec_rx_data));

mmax = max(max(radar_graph));
imagesc(speed_axis, time_axis, radar_graph - mmax);
colormap;
colorbar;
xlabel('Speed (m/s))');
ylabel('Time (secs)');
xlim([0 40]);
title('Doppler Analysis');
