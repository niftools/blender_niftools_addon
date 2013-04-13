import sys
import os

PYDEV_SOURCE_DIR = ""

def startdebug():

    try:
        pydev_src = os.environ['PYDEVDEBUG']
        
        if (sys.path.count(pydev_src) < 1) :
             sys.path.append(pydev_src)
             
        import pydevd
    except:
        print("Could not find Python Remote Debugger")
        pass
    
    try:
        pydevd.settrace(None, True, True, 5678, False, False)
    except:    
        print("Unable to connect to Remote debugging server")
        pass