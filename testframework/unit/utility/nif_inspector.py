import nose

from pyffi.formats.nif import NifFormat

'''Handy class for reading / writing nifs'''

import os.path

class NifInspector:
    
    @classmethod
    def setupClass(cls):
        #Uses script directory to read from/write from, override for different location
        cls.input_dir = os.path.curdir
        cls.input_filename = 'test'
        cls.output_dir = ''
        cls.output_filename = cls.input_filename + "_out"
        cls.data = NifFormat.Data()
        print("setup class")
    
    def runner(self):
        print("test running")
        # self.read_file()
        # self.write_file()
        pass
     
     
    def write_file(self):       
        self.create_data()
        path = self.output_dir + self.output_filename + ".nif"
        print("Writing to: " + path)
        with open(path, 'wb') as stream:
            self.data.write(stream)
         
    def read_file(self):
        path = self.input_dir + self.input_filename + ".nif"
        stream = open(path, 'rb')
        self.data.read(stream)
        self.check_data()
         
    def create_data(self):
        print("creating data")

            
    def check_data(self):
        print("Checking data")

        
    