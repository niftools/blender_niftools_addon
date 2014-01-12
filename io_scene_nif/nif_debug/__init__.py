import sys
import os

def startdebug():

    try:
        pydev_src = os.environ['PYDEVDEBUG']
        
        if (sys.path.count(pydev_src) < 1) :
            sys.path.append(pydev_src)
             
        import pydevd
        print("Found: " + pydev_src)
        
        try:
            pydevd.settrace(None, True, True, 5678, False, False)
        except:    
            print("Unable to connect to Remote debugging server")
        pass
    
    except:
        print("Python Remote Debugging Server not found")
        pass
    
    