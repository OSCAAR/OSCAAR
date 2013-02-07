##ds9parser.py
##  Called by photom6.py
##  Extracts (x,y,r) coords from the centers
##   of circles in a regions file to use as
##   the initial coordinates of stars of interest
##   in aperture photometry.
import re
os.system("ls "+regsLoc+"> filelists/reglist.txt")

regfile = open('filelists/reglist.txt','r').read().splitlines()[0]

regdata = open(regfile,'r').read().splitlines()

global init_x_list,init_y_list, hww_list

circle_data = []
init_x_list = []
init_y_list = []
hww_list = []
for i in range(0,len(regdata)):
    if regdata[i][0:6] == 'circle':
        circle_data.append(re.split("\(",regdata[i])[1])

for i in range(0,len(circle_data)):
    xydata = re.split("\,",circle_data[i])
    xyhdata = re.split("\)",xydata[2])[0]
    init_y_list.append(float(xydata[0]))
    init_x_list.append(float(xydata[1]))
    hww_list.append(float(xyhdata))
    
print "ds9parser printing hww_list:", hww_list
