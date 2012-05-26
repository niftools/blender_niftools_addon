import sys

DEBUGGING = False
# set the PYDEV_SOURCE_DIR correctly before using the debugger
PYDEV_SOURCE_DIR = 'C:\DevTools\eclipse\plugins\org.python.pydev_2.5.0.2012040618\PySrc'

def startdebug():
    
    if DEBUGGING == True:
        # test if PYDEV_SOURCE_DIR already in sys.path, otherwise append it
        if sys.path.count(PYDEV_SOURCE_DIR) < 1:
            sys.path.append(PYDEV_SOURCE_DIR)
        
        # import pydevd module
        import pydevd
        
        # set debugging enabled
        pydevd.settrace(None, True, True, 5678, False, False)
