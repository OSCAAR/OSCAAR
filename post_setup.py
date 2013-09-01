# -*- coding: utf-8 -*-
from __future__ import absolute_import
import os
import sys
import time
import atexit
time.sleep(1.0)

""" Loading the just installed oscaar package to test if import is working,
    and get the path of the pacakge to complete the installation. """
if not hasattr(sys, 'real_prefix'):
    save_path = sys.path[:]
    sys.path.remove(os.path.dirname(os.path.abspath(__file__)))
    import oscaar
    sys.path = save_path
    oscaardir = os.path.dirname(os.path.abspath(oscaar.__file__))
    print oscaardir
""" Function to download the ds9 version for current platform.
    URLs are tested working on 5-29-2013 """            
def download_ds9():
    sysplf = sys.platform
    
    oscaardirds9 = os.path.join(oscaardir,'extras','ds9',sysplf)
    
    if os.path.exists(os.path.dirname(oscaardirds9)) == True:
        print "It seems like DS9 is already installed in the OSCAAR directory."

    import urllib2
    print 'Downloading platform specific DS9:'

    
    if sysplf == 'darwin':
        url = "http://hea-www.harvard.edu/RD/ds9/download/darwinsnowleopard/ds9.darwinsnowleopard.7.2.tar.gz"
    elif sysplf == 'linux2':
       # url = "http://hea-www.harvard.edu/RD/ds9/download/linux/ds9.linux.7.2.tar.gz" This 32-bit download seems problematic
       url = 'http://hea-www.harvard.edu/RD/ds9/download/linux64/ds9.linux64.7.2.tar.gz'
    elif sysplf == 'win32':
        url = "http://hea-www.harvard.edu/RD/ds9/download/windows/SAOImage%20DS9%207.2%20Install.exe"
    
    file_name = url.split('/')[-1]
    u = urllib2.urlopen(url)
    f = open(file_name, 'wb')
    meta = u.info()
    file_size = int(meta.getheaders("Content-Length")[0])
    
    file_size_dl = 0
    block_sz = 8192
    while True:
        buffer = u.read(block_sz)
        if not buffer:
            break
    
        file_size_dl += len(buffer)
        f.write(buffer)
        status = r"%10d bytes [%3.2f%%]" % \
                            (file_size_dl, file_size_dl * 100. / file_size)
        status = status + chr(8)*(len(status)+1)
        print status,
    f.close()    
    print
    
    fh = open(file_name, 'rb')
    if sys.platform == 'win32':
        import zipfile
        z = zipfile.ZipFile(fh)
    else:
        import tarfile
        z = tarfile.open(file_name) 

    if os.path.exists(os.path.dirname(oscaardirds9)) == False:
        os.mkdir(os.path.dirname(oscaardirds9))
    if os.path.exists(oscaardirds9) == False:
        os.mkdir(oscaardirds9)
        
    olddir = os.getcwd()
    os.chdir(oscaardirds9)
    
    z.extractall()
    fh.close()

    if sys.platform != "win32": 
		os.chmod('ds9',0o777)

    os.chdir(olddir)
    os.remove(file_name)
    print 'DS9 installed in oscaar directory!'
    
""" Compile C files in c dir of oscaar"""
def complile_C():
    print
    if sys.platform == 'win32': 
        import shutil
        """ If running Windows, use the precompiled C binary """
        print 'copying precompiled C code for light curve modeling..',
        shutil.copy2(os.path.join(oscaardir,'c', 'windowsBinaries', \
                        'analyticalTransitModel.so'), os.path.join(oscaardir,'c', \
                        'analyticalTransitModel.so'))
        print 'done!'
    else: 
        import subprocess
        """ Otherwise use python setup to compile a shared library 
            (works on unix based machines) """
        print 'compiling C code for light curve modeling..'
        
        oscaardirC = os.path.join(oscaardir,'c')
        olddir = os.getcwd()
        os.chdir(oscaardirC)
        
        """ Build the c-library in place """
        subprocess.Popen(['python', 'setup.py','build_ext', \
                                                        '--inplace']).wait()        
        os.chdir(olddir)
        
def to_do_at_exit():
    if not hasattr(sys, 'real_prefix'):
        #import subprocess
        #subprocess.check_call(['python', 'registration.py'])
        from oscaar import registration
""" Set function to be executed at exit of code (when script is finished) """
atexit.register(to_do_at_exit)
    
if __name__ == '__main__':
    if not hasattr(sys, 'real_prefix'):
        complile_C()
        download_ds9()
