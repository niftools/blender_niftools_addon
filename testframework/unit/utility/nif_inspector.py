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
        cls.output_dir = cls.input_dir
        cls.output_filename = cls.input_filename + "_out"
        cls.ext = ".nif"
        cls.nif_file = NifFormat.Data()
        print("setup class")
        
    @istest
    def Runner(self):
        'Runner test to allow developer to quickly test in-memory, reading and writing of files'
        print("Test running")
        # self.read_file()
        # self.check_data()
        # self.create_data()
        # self.write_file()
        pass
     
     
    def write_file(self):    
        'Helper method to write a nif file'   
        path = self.output_dir + os.sep + self.output_filename + self.ext
        print("Writing to: " + path)
        with open(path, 'wb') as stream:
            self.nif_file.write(stream)
         
    def read_file(self):
        'Helper method to write a nif file'
        path = self.input_dir + os.sep + self.input_filename + self.ext
        print("Reading : " + path)
        stream = open(path, 'rb')
        self.nif_file.read(stream)
        self.check_data()
         
    def create_data(self):
        'Stub method to populate self.nif_file'
        print("creating nif_file")
        

            
    def check_data(self):
        'Stub method to testing self.nif_file'
        print("Checking nif_file")
        
    