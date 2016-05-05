import nose
from nose.tools import istest

import io_scene_nif

from pyffi.formats.nif import NifFormat

import os.path

@istest
class NifInspector:
    '''Handy utility class for debugging and testing reading / writing nifs'''
    
    @classmethod
    def setupClass(cls):
        #Uses script directory to read from/write from, override for different location
        cls.input_dir = os.path.dirname(__file__)
        cls.input_filename = 'test'
        cls.output_dir = ''
        cls.output_filename = cls.input_filename + "_out"
        cls.nif_file = NifFormat.Data()
        print("setup class")
        
    @istest
    def Runner(self):
        print("Test running")
        self.read_file()
        # self.write_file()
        pass
     
     
    def write_file(self):       
        self.create_data()
        path = self.output_dir + os.sep + self.output_filename + ".nif"
        print("Writing to: " + path)
        with open(path, 'wb') as stream:
            self.nif_file.write(stream)
         
    def read_file(self):
        path = self.input_dir + os.sep + self.input_filename + ".nif"
        print("Reading : " + path)
        stream = open(path, 'rb')
        self.nif_file.read(stream)
        self.check_data()
         
    def create_data(self):
        print("creating nif_file")

            
    def check_data(self):
        print("Checking nif_file")

        
    