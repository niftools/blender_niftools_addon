import nose

import os

from io_scene_nif.io.nif import NifFile


class TestNifIO:
 
    @classmethod
    def setup_class(cls):
        cls.working_dir = os.path.dirname(__file__)
        
    def test_load_supported_version(self):
        data = NifFile.load_nif(self.working_dir + os.sep + "readable.nif")
        nose.tools.assert_equal(data.version, 335544325)

    @nose.tools.raises(Exception)
    def test_load_unsupported_version(self):
        NifFile.load_nif(self.working_dir + os.sep + "unreadable.nif")
        
    @nose.tools.raises(Exception)
    def test_load_unsupported_file(self):
        NifFile.load_nif(self.working_dir + os.sep + "notnif.txt")
