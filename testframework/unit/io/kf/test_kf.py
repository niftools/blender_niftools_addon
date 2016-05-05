import nose

import bpy
import os

from io_scene_nif.io.kf import KFFile
from io_scene_nif.utility.nif_logging import NifLog

class Test_KF_IO:
 
    @classmethod
    def setup_class(cls):
        NifLog.setMockReporter()
        cls.working_dir = os.path.dirname(__file__)
        
    @classmethod
    def teardown_class(cls):
        del cls.kf_file
        
    def test_load_supported_version(self):
        kf_file = KFFile.load_nif(self.working_dir + os.sep + "readable.nif")
        nose.tools.assert_equal(kf_file.version, 335544325)

    @nose.tools.raises(Exception)
    def test_load_unsupported_version(self):
        KFFile.load_nif(self.working_dir + os.sep + "unreadable.nif")
        
    @nose.tools.raises(Exception)
    def test_load_unsupported_file(self):
        KFFile.load_nif(self.working_dir + os.sep + "notnif.txt")
