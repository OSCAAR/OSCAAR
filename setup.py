# -*- coding: utf-8 -*-

"""Made by Luuk Visser (UL/TUD), with tweaks by Brett Morris (NASA GSFC/UMD)"""
	
import os
import sys
import shutil
import subprocess
import atexit

""" Checking for all required packages and if these are recent enough """
minimum_numpy_version = "1.6"
minimum_matplotlib_version = "1.0"
minimum_pyfits_version = "3.1.0" # lower versions may work (not tested)
minimum_scipy_version = "0.10" # lower versions may work (not tested)
minimum_wxpython_version = "2.0" # lower versions may work (not tested)
sysplatform = sys.platform

if not hasattr(sys, 'real_prefix'):
	""" Currently only Python 2.7.x is supported """
	if sys.version_info[:2] != (2, 7):
	    raise RuntimeError("must use python 2.7.x")
	
	"""  Check if the package dependancies/requirements are fulfilled """
	try:
	    from setuptools import setup
	except:
	    raise RuntimeError("Setuptools not found, setup cannot continue without it")
	    
	try:
	    import numpy as np
	except:
	    raise RuntimeError("Numpy not found")
	if np.__version__ < minimum_numpy_version:
	    print("*Error*: NumPy version is lower than needed: %s < %s" %
			  (np.__version__, minimum_numpy_version))
	    sys.exit(1)
	
	try:
	    import scipy
	except:
	    raise RuntimeError("Scipy not found")
	if scipy.__version__ < minimum_scipy_version:
	    print("*Error*: Scipy version is lower than needed: %s < %s" %
			  (scipy.__version__, minimum_scipy_version))
	    sys.exit(1)  
		
	try:
	    import matplotlib
	except:
	    raise RuntimeError("matplotlib not found")
	if matplotlib.__version__ < minimum_matplotlib_version:
	    print("*Error*: matplotlib version is lower than needed: %s < %s" %
			  (matplotlib.__version__, minimum_matplotlib_version))
	    sys.exit(1)
		
	try:
	    import pyfits
	except:
	    raise RuntimeError("PyFITS not found")
	if pyfits.__version__ < minimum_pyfits_version:
	    print("*Error*: PyFITS version is lower than needed: %s < %s" %
			  (pyfits.__version__, minimum_pyfits_version))
	    sys.exit(1)  
		
	try:
	    if sysplatform == 'darwin' or 'linux2':
	         import wx
	    else:
	         """ (assuming in this case that sysplatform == 'win32' """
	         import wxPython
	except:
	    raise RuntimeError("wxPython not found")
	if wx.__version__ < minimum_wxpython_version:
	    print("*Error*: wxPython version is lower than needed: %s < %s" %
			  (wx.__version__, minimum_wxpython_version))
	    sys.exit(1)  
else: 
	from setuptools import setup

""" Walk through the subdirs and add all non-python scripts to MANIFEST.in """
def create_manifest():	
	print 'creating manifest.in'
	matches = []
	for root, dirnames, filenames in os.walk('oscaar'):
		if ('.git' in str(root)) == False:
			for filename in filenames:
				if filename.endswith(('.py', '.pyc')) == False:
				  matches.append(os.path.join(root, filename))
	for root, dirnames, filenames in os.walk('docs'):
		if ('.git' in str(root)) == False:
			for filename in filenames:
				if filename.endswith(('.py', '.pyc')) == False:
				  matches.append(os.path.join(root, filename))
	"""Manually add extra files from the top-level directory"""
	matches.append(os.path.join(os.path.dirname(__file__),'post_setup.py'))
	matches.append(os.path.join(os.path.dirname(__file__),'INSTALL.txt'))
	matches.append(os.path.join(os.path.dirname(__file__),'LICENSE.txt'))

	with open('MANIFEST.in', 'w') as f:
		f.writelines(("include %s\n" % l.replace(' ','?') for l in matches))

""" To remove the manifest file after installation """
def delete_manifest():
	if os.path.exists('MANIFEST.in'):
		os.remove('MANIFEST.in')
	
""" Create list for Python scripts directories to include """
def get_packages():
	print 'searching for packages'
	matches = []
	for root, dirnames, filenames in os.walk('oscaar'):
		if ('.git' in str(root)) == False:
			for filename in filenames:
				if filename.endswith(('.py', '.pyc')) == True:
					matches.append(root)
	matches = list(set(matches))
	return matches
	
def del_dir(dirname):
	if os.path.exists(dirname):
		shutil.rmtree(dirname)
	
""" The setup configuration for installing OSCAAR """


def setup_package():
	create_manifest()
	list = ['Numpy>=1.6','Scipy>=0.1','pyfits>=3.1','pyephem>=3.7', 'matplotlib>1.0']
	setup(
		name = "OSCAAR",
		version = "2.0beta",
		author = "Core Developer: Brett M. Morris. Contributors: "+\
                      "Daniel Galdi, Dharmatej Mikkilineni, Luuk Visser",
		author_email = "oscaarteam@gmail.com",
		description = ("oscaar is an open source project aimed at "+\
                      "helping you begin to study transiting extrasolar "+\
                      "planets with differential photometry."),
		license = 'LICENSE.txt',
		keywords = "oscaar transit astronomy photometry exoplanets",
		url = "https://github.com/OSCAAR/OSCAAR/wiki",
		packages=get_packages(),
		include_package_data = True,
		zip_safe = False,
		long_description=open(os.path.join(os.path.dirname(\
                      os.path.abspath(__file__)),'README')).read(),
		download_url='https://github.com/OSCAAR/OSCAAR/archive/master.zip',
 		install_requires=list,
		classifiers=[
		  'Development Status :: 4 - Beta',
		  'Intended Audience :: Science/Research',
		  'License :: OSI Approved :: MIT License',
		  'Operating System :: OS Independent',
		  'Programming Language :: Python :: 2.7',
		  'Programming Language :: C',
		  'Topic :: Scientific/Engineering :: Astronomy',
		  'Topic :: Scientific/Engineering :: Physics'
	  ],
	)


""" At exit delete temporary files, and run post setup script if argument is
    'install' """
def to_do_at_exit():
	delete_manifest()
	#del_dir('build')
	#del_dir('OSCAAR.egg-info')
	
	if 'install' in sys.argv: 
		del_dir('dist')
		
		'Installation finished. Starting DS9 downloader and compile C\n'
		subprocess.check_call(['python', 'post_setup.py',sys.argv[-1]])

""" Set function to be executed at exit of code (when script is finished) """
atexit.register(to_do_at_exit)
	
if __name__ == '__main__':
	setup_package()