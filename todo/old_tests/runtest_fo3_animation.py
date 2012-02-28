"""Import and export full body (bind pose) nif for Fallout 3."""

import os.path

from nif_test import TestSuite

class Fallout3AnimationTestSuite(TestSuite):
    def run(self):
        self.make_fo3_fullbody()
        fo3_male = os.path.join(
            self.config.get("path", "fallout3"),
            "meshes", "characters", "_male")
        self.test(
            filename="test/nif/fo3/_fullbody.nif",
            config=dict(
                IMPORT_TEXTURE_PATH=[self.config.get("path", "fallout3")],
                IMPORT_KEYFRAMEFILE=os.path.join(fo3_male, "h2haim.kf")))
        self.test(
            filename="test/nif/fo3/_h2haim.kf",
            config=dict(
                game='FALLOUT_3',
                animation='ANIM_KF'), # animation only
            selection=['Scene Root'])

suite = Fallout3AnimationTestSuite("fo3_animation")
suite.run()
