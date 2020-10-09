from pyffi.formats.nif import NifFormat

import os.path

import unittest


class TestNifInspector(unittest.TestCase):
    """Handy utility class for debugging and testing reading / writing nifs"""

    def test_runner(self):
        """Runner test to allow developer to quickly test in-memory, reading and writing of files"""
        print("Test running")
        self._read_file()
        # self.check_data()
        # self.create_data()
        # self.write_file()
        pass

    @classmethod
    def setUpClass(cls):
        # Uses script directory to read from/write from, override for different location
        cls.root = os.path.dirname(__file__)
        cls.input_dir = os.path.join(cls.root, "input")
        cls.output_dir = os.path.join(cls.root, "output")
        cls.input_filename = ''  # Replace with name of file to be loaded
        cls.ext = ".nif"
        cls.output_filename = cls.input_filename + "_out"
        cls.nif_file = NifFormat.Data()
        print("setup class")

    def _write_file(self):
        """Helper method to write a nif file"""
        path = self.output_dir + os.sep + self.output_filename + self.ext
        print(f"Writing to: {path}")
        with open(path, 'wb') as stream:
            self.nif_file.write(stream)
         
    def _read_file(self):
        """Helper method to write a nif file"""
        path = self.input_dir + os.sep + self.input_filename + self.ext
        print(f"Reading : {path}")
        with open(path, 'rb') as stream:
            self.nif_file.read(stream)
        print(self.nif_file)

    def _create_data(self):
        """Stub method to populate self.nif_file"""
        print("creating nif_file")

    def _check_data(self):
        """Stub method to testing self.nif_file"""
        print("Checking nif_file")

