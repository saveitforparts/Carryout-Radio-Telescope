#Python program to scan with Winegard Carryout and output signal strength array
#Process output into bitmap with fix_image.py
#Version 1.0
#Gabe Emerson / Saveitforparts 2023, Email: gabe@saveitforparts.com

import serial
import time
import regex as re
import numpy as np
from rtlsdr import RtlSdr
from pylab import *

MHZ = 1e6
#generate timestamp
timestr = time.strftime('%Y%m%d-%H%M%S')

#define "carryout" as the serial port device to interface with
carryout = serial.Serial(
	port = '/dev/ttyUSB0',
	baudrate = 57600,
	parity = serial.PARITY_NONE,
	stopbits = serial.STOPBITS_ONE,
	bytesize = serial.EIGHTBITS,
	timeout = 1)
	
print('Serial port connected')
print('')

#Prompt for scan parameters, with default values and valid range checks
#TODO: Offer these as command line args
if (az_start := int(input('Starting Azimuth in degrees (0-360, default 90): ') or 90) < 0):
	print('Azimuth out of range, setting to 0')
	az_start = 0
if az_start > 360:
	print('Azimuth out of range, setting to 360')
	az_start = 360

if (az_end := int(input('Ending Azimuth in degrees (default 270): ') or 270) < 0):
	print('Azimuth out of range, setting to 0')
	az_end = 0
if az_end > 360:
	print('Azimuth out of range, setting to 360')
	az_end = 360
az_end += 1 #ugly fix to get full user range inclusive

if (el_start := int(input('Starting Elevation in degrees (22-73, default 22): ') or 22) < 22):
	print('Elevation out of range, setting to 22')
	el_start = 21
if el_start > 73:
	print('Elevation out of range, setting to 73')
	el_start = 73

if (el_end := int(input('Ending Elevation in degrees (default 73): ') or 73) < 22):
	print('Elevation out of range, setting to 22')
	el_end = 21
if el_end > 73:
	print('Elevation out of range, setting to 73')
	el_end = 73
	
	
#Configure SDR 
sdr = RtlSdr()

if (user_freq := float(input('Frequency in MHz: ')) < 0.5):
	print('Frequency too low for RTL-SDR, setting to 500khz')
	user_freq = 0.5
if user_freq > 1766:
	print('Frequency too high for RTL-SDR, setting to 1766')
	user_freq = 1766

if (bias_tee := int(input('Bias Tee (1=on, 0=off, default 1): ') or 1) not in [0,1]):
	print('Invalid Bias Tee value, setting to 0')
	bias_tee = 0

print(f'Available gain values are {sdr.valid_gains_db}')
print('')
if (user_gain := float(input('RF Gain (default 20.7, will be rounded to nearest available): ') or 20.7) < 0):
	print('Gain below minimum for RTL-SDR, setting to 0')
	user_gain = 0
if user_gain > 49.6:
	print('Gain above max for RTL-SDR, setting to 49.6')
	user_gain = 49.6
	
sdr.sample_rate = MHZ #MHz higher sample rates causing delays?
sdr.set_bandwidth(8000) #Narrow FM, MAKE THIS USER-SELECTABLE?
sdr.center_freq = user_freq*MHZ # - 200e3 #MHz, with offset to avoid DC spike CHECK THIS
sdr.gain = user_gain
sdr.set_bias_tee(bias_tee)

resolution = 1 #placeholder for potential future high-res scan, if can do fractional degrees of movement. 
np.savetxt(f'scan-settings-{timestr}.txt', (az_start,az_end,el_start,el_end,resolution,user_freq,bias_tee,user_gain))	

az_range = az_end - az_start + 1
el_range = el_end - el_start + 1

#Provide runtime estimate (I'm making a rough guess based on prior runs on two different computers)
time_est = az_range * el_range
if (time_output := round((time_est / 180), 2) > 60):
	print(f'Estimated scan time with your parameters is {time_output/60} hours.')
else:
	print(f'Estimated scan time with your parameters is {time_output} minutes.')
print('')
if input('Proceed with scan? (y/n):').lower().startswith("y"):
	print('Scan in progress...')
else:
	print('exiting.')
	exit()


#create 2D array for raw signal strengths
sky_data = np.zeros((el_range,az_range))

start_time = time.time() #record start time of scan

#initialize starting dish position
print('Moving dish to starting position...')
carryout.write(bytes(b'q\r')) #go back to root menu in case unit's OS was left in a submenu
carryout.write(bytes(b'\r')) 
carryout.write(bytes(b'target\r')) #go to carryout targeting menu
command = (f'g {az_start} {el_start}\r').encode("ascii")
carryout.write(command) #send target to carryout unit

time.sleep(5) #wait for motors to reach starting position

#SDR always seems to be delayed by 1/10th of Az range, because reasons????
#Start reading from SDR "early" to avoid this. May not be the same on all machines.
for i in range(0, round((az_range)/10)+1): 
	samples = sdr.read_samples(256*1024) 	
	
#Main scanning loop
direction = 1	
for elevation in range(el_start,el_end+1):
		sdr_bytes = sdr.read_bytes(256*1024) #avoid blank pixels at start(?)	
		#valid azangle 0-360. Remember carryout increments cw. 
		for azimuth in range (az_start,az_end):
	
			if (direction & 1 == 0):   #check for sweep direction
				azimuth = abs(azimuth-az_end)+az_start-1   #increment backwards on odd numbered loops
						
			#Read RF signal from SDR
			samples = sdr.read_samples(256*1024)
			signal_strength = 10*log10(var(samples))
			print(f'Relative power: {round(signal_strength, 2)} dB') 
			
			#record signal data to array
			sky_data[abs(elevation-el_end),(azimuth-az_end)]=signal_strength
			#write to text file
			np.savetxt(f"raw-data-{timestr}.txt", sky_data)
				
			print(f'Azimuth: {azimuth}, Elevation: {elevation}')  #display current position

			#Tell carryout dish to go to next target position
			carryout.write(bytes(b'target\r'))
			command = (f'g {azimuth} {elevation}\r').encode('ascii')
			carryout.write(command)
			carryout.write(bytes(b'q\r')) #go back to root menu
	
			#time.sleep(0.1) #Allow motors to catch up, reduce shaking. Not necessary if sample size large enough?
			
		direction += 1	

end_time = time.time() #record end time of scan
print('')
print('Scan complete!')
run_time = round(end_time - start_time)
print(f'Elapsed time: {round(run_time/60, 2)} minutes.')      


#close serial connection and turn off SDR
carryout.close()
sdr.set_bias_tee(0)
sdr.close()
