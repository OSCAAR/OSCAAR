def mkdir(a, b=None):
    """Make new directory with name a where a
       is a string inside of single quotes"""
    if b is None:
        c = ''
    else:
        c = ' '+str(b)
    os.mkdir(str(a)+str(c))
    #command = 'mkdir '+str(a)+str(c)
    #os.system(command)

def cd(a=None):
    """Change to directory a where a is a 
       string inside of single quotes. If a
       is empty, changes to parent directory"""
    if a is None:
        os.chdir(os.pardir)
    else:
        os.chdir(str(a))

def cp(a, b):
    """Copy file a to location b where a,b are
       strings inside of single quotes"""
    shutil.copy(str(a), str(b))
    #command = 'cp '+str(a)+' '+str(b)
    #os.system(command)

def overcheck(filename, checkfiles, varcheck):
    overcheck = None
    for i in range(0, len(checkfiles)):
        if checkfiles[i]== filename and varcheck == 'on':
            overcheck = raw_input('WARNING: Overwrite /' + filename + '/ ? (Y/n): ')
            break
    if overcheck == '' or overcheck == 'Y' or overcheck == 'y':
        shutil.rmtree(filename)
        mkdir(filename)
