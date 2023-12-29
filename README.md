#Microwave imaging using portable "Carryout" satellite antenna. 

Gabe Emerson / Saveitforparts 2023. Email: gabe@saveitforparts.com

Video demo: https://youtu.be/4a2HjE11DcQ

**Introduction:**

This code controls a portable satellite antenna over RS-485 using serial commands. 
This is based roughly on my Tailgater-Microwave-Imaging project, adapted for the
Winegard Carryout antenna (vs the original Dish Tailgater / Vuqube). 

The carryout_scan.py program aims the dish to a selected portion of the sky and 
records the RF signal strength from an RTL-SDR. The fix_image.py program reads
the resulting data and creates a heatmap of the scanned area. Frequencies are 
dependent on your antenna feed (provided by the user). For testing I used a hacked
GPS patch antenna in the L microwave band. 

Please note that the author is not an expert in Python, Linux, satellites, or 
radio theory! This code is very experimental, amateur, and not optimized. It will
likely void any warranty your Carryout antenna may have. There are probably better,
faster, and more efficient ways	to do some of the functions and calculations in 
the code. Please feel free to fix, improve, or add to anything (If you do, I'd
love to hear what you did and how it worked!)    


**Applications:**

- Imaging geostationary satellites in RF wavelengths
- Imaging low / medium orbit satellites (depending on speed)
- Surveying an environment or room for microwave radiation
- Imaging an environment using ambient or reflected microwaves 
- Imaging Wifi with a downconverter and different feed


**Hardware Requirements:**

This code has been developed and tested with a Winegard "Carryout" portable
satellite antenna. Specifically, a 2003 version running HandEra HAL 1.00.065
firmware. There are other variations and versions of this hardware, such as the
Carryout G2 and G3. I have not tested it with all models. 

You will need to remove the plastic radome from the top of the antenna to access
the console port and change or modify the receiver feed.

In addition to the antenna, you will need an RS-232 to RS-485 adapter, custom
RJ-25 cable, and USB-to-Serial adapter. I used a "DTECH RS232 to RS485" converter
that includes screw terminals. The DB9 end is connected to my USB serial cable,
and the wiring terminals are connected to an RJ-25 cable (6-conductor phone cord)
as follows:

Looking at the bottom (pin side) of the RJ-25, with end of cable up, the wires
from left to right are:

Pin 1: GND
Pin 2: T/R-
Pin 3: T/R+
Pin 4: RXD-
Pin 5: RXD+
Pin 6: Not connected

(See cable1.jpb and cable2.jpg in the images folder)

Thanks to Kyle from Kismet Emergency Communications for providing the RS-485 info! 

You will also need a new antenna feed if you plan to use this system with anything
other than Ku band. Other users have reported issues using the on-board LNB, so I
have not tested that. I removed the LNB and replaced it with a generic GPS patch 
antenna, with the filter de-soldered and jumpered to allow wider L-band reception.
The antenna is powered by an RTL-SDR bias-tee. 
 
More information on GPS antenna modification can be found at:
wiki.muc.ccc.de/iridium:antennas 
or dodgyengineering.com/2016/09/05/active-gps-antenna-modification/

This code has been tested sucessfully on a range of Linux PCs, from 686-class using
a low-resource distro, to higher-end running a modern distribution. 


**Notes on power supply and auto-scan behavior**

The Winegard Carryout used for testing had a proprietary 12v DC jack, I replaced 
this with a standard barrel jack. The on-board DC could be stepped down to run an
embedded system or SBC if desired. Power of at least 1A seems best. 

When first powered on, the Carryout antenna goes through a series of calibration and
automatic satellite search movements. This can take approximately 10-15 minutes
to complete, depending on DIP switch settings on the control board. It may also 
produce some alarming grinding sounds from the stepper motors and gearing. Winegard
apparently did not bother to install limit switches on early models, and uses motor
stall to determine drive limits. 

Other users have reported that setting all DIP switches to "off" (up) disabled the 
search mode, but that did not work for me. There may be a setting in the firmware to 
disable the search, but I also have not found that (disabling tracking in the "nvs"
firmware submenu also disables the position calibration, which we want to retain for 
accurate aiming). 


**Package Requirements:**

carryout_scan.py uses the numpy, pyserial, regex, pylab, and pyrtlsdr packages. 
fix_image uses matplotlib.
They can be installed individually or by running "pip install -r requirements.txt"


**Setting up / testing Carryout console:**

To connect to a Carryout antenna with RS-485, you will need the cable described above
under Hardware Requirements. 

To connect to the serial console on the antenna, run "screen /dev/ttyUSB0 57600" (or 
appropriate port) on Linux, or use a Windows serial terminal to connect to the usb 
device (typically com3 or similar). You will initially get a blank screen. Typing "?"
should return a menu of available commands and submenus. Typing "q" exits the current
submenu and returns to the root menu.

Some submenus of interest include:
target: send dish to desired azimuth / elevation coordinates
motor: manual motor movements and settings
dvb: Get signal info from the installed LNB
os: List and quit running processes, etc

	
Note that the console does not accept backspace, so if you make a mistake while typing,
just hit enter to clear the console. If necessary, close the console or unplug the 
dish to avoid a motor overrun. 


**Positioning the antenna:**

The Carryout antenna uses a 360-degree clockwise coordinate system, with the coax
/ F connector at approximately 135 degrees. You may have to run some serial console
commands like "target", "g 0 22" to find the 0 or North position. I marked my dish
with sharpie once I determined this. 
		
Generally I place the dish with the "0" position facing due North (for scans of the
Southern sky), but you can place it in any orientation you want.


**Running a scan:**

NOTE: If your USB device is other than ttyUSB0, edit line 19 of carryout_scan.py

Once the dish is connected, powered, and ready on a serial port, run:
"python3 carryout_scan.py"

You will be prompted for the starting and ending azimuth and elevation of your scan. 
Valid azimuth range is 0-360, and valid elevations are 22-73 degrees (The motors can
technically go farther, but the on-board firmware won't accept values outside this
range). If you enter a value outside the valid range, the program will use the minimum
or maximum as appropriate. The default values are from azimuth 90 to 270 (East to West),
and from elevation 22 to 73 degrees. This covers much of the Southern sky (if the dish 
is placed with 0 position aiming due North). A scan with default values takes 
approximately 1 hour. 

Scans of smaller azimuth/elevation ranges should take less time. Estimated scan time 
for your parameters will be shown once the scan starts, and elapsed time shown at the
end. During the scan, the current azimuth, elevation, and signal strength will be
displayed for each dish position. 

	
**Generating an image from a scan:**
	
Once a scan has completed, you will have two output files with the same timestamp:

- "raw-data-<timestamp>.txt"       The raw scan values in a numpy array.
	
- "scan-settings-<timestamp>.txt"  The scan parameters (start & end azimuth / elevation)
	
fix_image.py will use the two text files to create a heatmap of your scan. Run the code 
along with the name of the raw-data scan you want to process. For example:
"python3 fix_image.py raw-data-20230322-153935.txt"
	
The code will load the corresponding scan-settings file automatically, and opens a
heatmap of the scan in a new window. You can save this heatmap for later use. 

There is an ongoing issue where counterclockwise rows are offset slightly from clockwise
rows, this seems to be related to timing between the RTL-SDR reads and the indexing
steps. I have done several hacky fixes trying to address this, but it may be dependent
on your individual SDR and computer. 
 
	
**Example Images:**
I have included several example images to show what the hardware and scans look like:
	 
- "Inmarsat-4 F3.png" shows geostationary Inmarsat satellite transmitting on 1552.2Mhz
			Scanned with a front feed L-band patch antenna. 
			
- "Navsats.png" shows Medium Earth Orbit navigation satellites. Possibly including GPS, 
	    Galilleo, and Beidou (all use similar frequencies). Each satellite appears 
	    multiple times in an arc due to the speed difference between the orbit and
	    the dish
	    
- "Iridium.png" shows a Low Earth Orbit Iridium satellite passing South to North
		(on the left / East side of the image)
				  	  
- "carryout.jpg" shows the antenna unit used for this project.

- "board.jpg" shows the antenna with radome removed, and exposed main control board

- "cable1.jpg" and "cable2.jpg" show the custom USB to RS232 to RS485 / RJ-25 cable. 
		

**Example Files**

I have included some example data files output by carryout_scan.py, for processing with
fix_image.py;

- "raw-data-20231226-161058.txt":   numpy matrix of signal strengths at each position

- "scan-settings-20231226-161058.txt":  scan parameters 


**Additional notes:**
	
The heatmap generated by fix_image.py uses CMRmap. If you wish to use another colormap, 
you can change line 63 of fix_image.py. I also like "seismic" and "gnuplot2", but I feel
that they lose some definition on the background landscape. "hsv" may also be useful for 
noisy scans. 
	
If you use this code and encounter any problems, feel free to email me at the address at
the top of this file. However, I may have to refer back to this to remember how it works! 

