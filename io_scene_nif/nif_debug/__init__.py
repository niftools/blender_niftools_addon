import sys
import os

PYDEV_SOURCE_DIR = ""

def startdebug():

    try:
        PYDEV_SOURCE_DIR = os.environ['PYDEV_SOURCE_DIR']
        
        if sys.path.count(PYDEV_SOURCE_DIR) > 0:
            sys.path.append(PYDEV_SOURCE_DIR)
             
        import pydevd
        pydevd.settrace(None, True, True, 5678, False, False)
     
    except:    
        print("Unable to connect to Remote debugging server")
        print("PYDEV_SOURCE_DIR := " + PYDEV_SOURCE_DIR)
        pass