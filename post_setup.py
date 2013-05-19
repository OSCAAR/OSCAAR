# -*- coding: utf-8 -*-
import os
import sys
import urllib2
import time

""" Function to download the ds9 version for current platform.
    URLs are tested working on 5-19-2013 """            
def download_ds9():
    import oscaar
    oscaardir = oscaar.__file__
    oscaardirds9 = os.path.join(os.path.dirname(oscaardir),'extras','ds9',sys.platform)
    
    print 'Downloading platform specific DS9:'

    sysplatform = sys.platform
    if sysplatform == 'darwin':
        url = "http://hea-www.harvard.edu/RD/ds9/download/darwinsnowleopard/ds9.darwinsnowleopard.7.2.tar.gz"
    elif sysplatform == 'linux2':
        url = "http://hea-www.harvard.edu/RD/ds9/download/linux/ds9.linux.7.2.tar.gz"
    elif sysplatform == 'win32':
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
        status = r"%10d bytes [%3.2f%%]" % (file_size_dl, file_size_dl * 100. / file_size)
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
        z = tarfile.TarFile(fh) 

    if os.path.exists(oscaardirds9) == False:
        os.mkdir(oscaardirds9)
        
    olddir = os.getcwd()
    os.chdir(oscaardirds9)
    
    z.extractall()
    fh.close()

    os.chdir(olddir)
    os.remove(file_name)
    print 'DS9 installed in oscaar directory!'
    
""" Compile C files in c dir of oscaar"""
def complile_C():
    import oscaar
    oscaardir = oscaar.__file__
    oscaardirC = os.path.join(os.path.dirname(oscaardir),'code','oscaar','c')
    
    olddir = os.getcwd()
    os.chdir(oscaardirC)
    
    import subprocess
    cresult = subprocess.Popen(['python', 'setup.py','build_ext','--inplace'])
    cresult.wait()
    
    os.chdir(olddir)
    
if __name__ == '__main__':
    time.sleep(1)
    download_ds9()
    complile_C()