import sys

def startdebug():
    try:
        # set the PYDEV_SOURCE_DIR correctly before using the debugger
        PYDEV_SOURCE_DIR = 'C:\Program Files\eclipse\plugins\org.python.pydev.debug_2.5.0.2012040618\pysrc'
        
        # test if PYDEV_SOURCE_DIR already in sys.path, otherwise append it
        if sys.path.count(PYDEV_SOURCE_DIR) < 1:
            sys.path.append(PYDEV_SOURCE_DIR)
            
        # import pydevd module
        import pydevd
            
        # set debugging enabled
        pydevd.settrace(None, True, True, 5678, False, False)
    except:
        print("Unable to connect to Remote Debug Server.")
        pass
