%Range Analysis for QMRDK Radar
%FMCW Mode

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
freq_st = radar_params(1) / 1000;
freq_ed = radar_params(2) / 1000;
no_frame = radar_params(5);
pulse_time = radar_params(4);
type_swipe = radar_params(3);

%parameters
samp_pulse = round(pulse_time*1e-3 * no_frame);
pulse_per_seconds = no_frame / samp_pulse;
BW = (freq_ed - freq_st)*1e9;
rr = 3e8 / (2*BW);
max_range = rr*samp_pulse/2; %range in m

%validation
if (type_swipe == 3) %is CW
    fclose(fid);
    error('Cannot process Continious Wave dumps!!!!');
end

%parse the numbers
while (~feof(fid))
    tmp = fread(fid, 128, 'double'); %increase the number for speed
    rec_rx_data = [rec_rx_data tmp'];
end
fclose(fid);

pulse_samp = round(no_frame * pulse_time*1e-3);
sec_data = round(length(rec_rx_data) / no_frame);
no_pulses = round(length(rec_rx_data) / pulse_samp);

fprintf('Loaded %d seconds of data...\n', sec_data);
fprintf('No of Periods in 1 sec is: %d and pulse period is: %d samples..\n', no_pulses, pulse_samp);

%normalyze
rec_rx_data = 5 ./ (power(2,16) ./ rec_rx_data); %normalyze to 0 to 5v.
rec_rx_data = rec_rx_data - (5/2);
%rec_rx_data = rec_rx_data / mean(rec_rx_data) - 1;

pulse_cancellation = zeros(1, no_frame);
pulse_cancellation_coeff = 1; %should be 1.
pulse_nfft = 4096;

radar_graph = zeros(pulse_nfft/2, sec_data);
%radar_graph = zeros(sec_data, pulse_nfft/2);

range_plt = [];

for i=1:sec_data
    %get the data
    st_pt = ((i-1)*no_frame) + 1;
    ed_pt = i*no_frame;
    
    curr_block_radar = rec_rx_data(st_pt:ed_pt);
    curr_block_radar = curr_block_radar - mean(curr_block_radar); %normalize the data
    orig_radar_sig = curr_block_radar;
    
    %cancel last pulse, so only see moving targets
    curr_block_radar = curr_block_radar - (pulse_cancellation_coeff * pulse_cancellation);
  
    %to the IFFT
    ifft_data = abs(ifft(curr_block_radar, pulse_nfft));
    ifft_data = ifft_data(1:end/2);  
    radar_graph(:,i) = 20*log10(ifft_data); 
    pulse_cancellation = orig_radar_sig; %set the cancellation
end

%build the ramp graph
distance_axis = linspace(1, no_frame, pulse_nfft); %10 000 Hz as the ADC of the RMDK is 20 Khz.
distance_axis = (3e8 * distance_axis * pulse_time * 1e-3) / (2*BW);
tim_axis = linspace(1,length(rec_rx_data)) / no_frame;

%plot the result
figure;
%imagesc(distance_axis, tim_axis, radar_graph.', [-110 -30]);
imagesc(tim_axis, distance_axis , radar_graph, [-110, -30]);
colorbar;
title('Range Analysis (with Pulse Cancellation)');
ylabel('Range (m)');
xlabel('Time (sec)');

noise_floor = -40; %change this accordingly to the RX power for threshold

sec_plot = [];
range_plot = [];
raw_range_plot = [];

%build the range evolution time
for i=1:sec_data
    curr_fft = radar_graph(2:end,i);
    [mval, midx] = max(curr_fft);
    rmet = (midx * pulse_time * 1e-3 * 3e8) / (2*BW);
    
    raw_range_plot = [raw_range_plot rmet];
    if (mval > noise_floor)
        %rmet = (midx * pulse_time * 1e-3 * 3e8) / (2*BW);
        fprintf('Detected range at %d second is %f meters...\n', i, rmet);
        range_plot = [range_plot rmet];
    else
        range_plot = [range_plot 0];
    end
end

figure
%%plot(range_plot, 'bo-');
hold on;
plot(raw_range_plot, 'ro-');
xlabel('Time in seconds');
ylabel('Range (m)');
title('Range Plot');
grid on;
