import nose

import os

from io_scene_nif.io.egm import EGMFile


class TestEGMIO:
 
    @classmethod
    def setup_class(cls):
        cls.working_dir = os.path.dirname(__file__)
        
    def test_load_supported_version(self):
        data = EGMFile.load_egm(self.working_dir + os.sep + "readable.egm")
        nose.tools.assert_equal(data.version, 335544325)

    @nose.tools.raises(Exception)
    def test_load_unsupported_version(self):
        EGMFile.load_egm(self.working_dir + os.sep + "unreadable.egm")
        
    @nose.tools.raises(Exception)
    def test_load_unsupported_file(self):
        EGMFile.load_egm(self.working_dir + os.sep + "notegm.txt")
