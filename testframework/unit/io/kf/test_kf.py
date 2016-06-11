import nose

import bpy
import os

from io_scene_nif.io.kf import KFFile
from io_scene_nif.utility.nif_logging import NifLog

class Test_KF_IO:
 
    @classmethod
    def setup_class(cls):
        cls.working_dir = os.path.dirname(__file__)
        
    def test_load_supported_version(self):
        kf_file = KFFile.load_kf(self.working_dir + os.sep + "readable.kf")
        nose.tools.assert_equal(kf_file.version, 67108866)

    @nose.tools.raises(Exception)
    def test_load_unsupported_version(self):
        KFFile.load_kf(self.working_dir + os.sep + "unreadable.kf")
        
    @nose.tools.raises(Exception)
    def test_load_unsupported_file(self):
        KFFile.load_kf(self.working_dir + os.sep + "notkf.txt")
