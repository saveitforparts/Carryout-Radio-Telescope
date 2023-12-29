#Winegard Carryout version of dish_image.py
#Companion file to carryout_scan.py, processes results array into bitmap. 

import numpy as np
import matplotlib.pyplot as plt
import sys


#Open the filename passed at runtime
print('Loading data file.')
with open(sys.argv[1], 'r') as file_name:
	sky_data = np.loadtxt(file_name)

#Pull timestamp from filename (there's probably a better way to do this)
header, *filename_parts = str(file_name).split('-')     
file_name=str(filename_parts[2])
header, *split = file_name.split('.')
timestamp=(filename_parts[1]+'-'+header)

print('Loading parameters of scan.')
scan_params = np.loadtxt("scan-settings-"+timestamp+".txt")
az_start=int(scan_params[0])
az_end=int(scan_params[1])
el_start=int(scan_params[2])
el_end=int(scan_params[3])
resolution=int(scan_params[4])
user_freq=str(round(scan_params[5], 2))
bias_tee=int(scan_params[6])
if bias_tee==1:
	bias_str="On"
else:
	bias_str="Off"
user_gain=str(scan_params[7])


#Trim off empty edge of the array (probably an ugly hack)
cleaned_data = np.delete(sky_data, obj=0, axis=1)


#The following block is to fix an indexing issue with my dish and scan code
#originally cw scans were off slightly from ccw scans. This may be dish / SDR dependent
#for row_index in range (0,(el_end-el_start-1)):  #iterate through array
#	if (row_index % 2) == 1: 		  #check for scan direction
#		cleaned_data[row_index]=np.roll(cleaned_data[row_index],-8) #Shift every other row of matrix right 
#	else:
#		cleaned_data[row_index]=np.roll(cleaned_data[row_index],8) #Shift every other row of matrix left 
		

az_end = az_end - 1

#set up custom axis labels
x=np.array([0,(az_end-az_start)/2,az_end-az_start])
az_range=np.array([az_start,(az_start+az_end)/2,az_end])
plt.xticks(x,az_range)
y=np.array([0,(el_end-el_start)/2,el_end-el_start])
el_range=np.array([el_end,(el_start+el_end)/2,el_start])
plt.yticks(y,el_range)
	
	
print('Processing heatmap...')


plt.imshow(cleaned_data, cmap='CMRmap')
plt.colorbar(location='bottom',label='RF Signal Strength (dBm)')
plt.xlabel("Azimuth")
plt.ylabel("Elevation")
plt.suptitle("Carryout Scan "+timestamp)
plt.title("Frequency: " + user_freq +"MHz, Gain: " + user_gain + ", Bias Tee: "+ bias_str) 


plt.show()


