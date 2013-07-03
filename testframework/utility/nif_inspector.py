import pyffi
from pyffi.formats.nif import NifFormat
import os 

import nose

'''Handy class for reading / writing nifs'''
class TestNifInspector:
    
    @classmethod
    def setupClass(cls):
        #dir to read from/write from eg "C:\\Users\\admin\\Desktop\\
        dir = ''
        filename = ''
    
    def test_runner():
        #write_file()
        #read_file()
        pass
    
    
    def write_file():
        stream = open(dir + filename +".nif", 'wb')
        data = NifFormat.Data()
        #update data        
        data.write(stream)
        
    def read_file():
        stream = open(dir + filename+".nif", 'rb')
        data = NifFormat.Data()
        data.read(stream)
        # write inspection code.
        