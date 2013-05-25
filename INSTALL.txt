OSCAAR 2.0 BETA

In the same directory as this INSTALL file, execute 

python setup.py install

from a Unix/Linux shell or the Windows command prompt. 
If you're machine runs Windows and you've never run a
Python script from the command prompt before, you'll 
first need to enter this

set path=%path%;C:\python27

in the command prompt in order to be able to access the
"python" command from the command prompt. You only need
to do this once. 

If you have any trouble, check for troubleshooting tips
from similar past issues on our Issue Tracker

https://github.com/OSCAAR/OSCAAR/issues?state=open

or for more tutorials on our wiki

https://github.com/OSCAAR/OSCAAR/wiki

If you've successfully installed OSCAAR, you can open 
the GUI with the follow command (*when not in the same
directory that you installed OSCAAR from*)

python -c "from oscaar import oscaarGUI"