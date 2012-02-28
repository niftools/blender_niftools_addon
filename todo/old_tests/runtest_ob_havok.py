"""Automated havok tests for the blender nif scripts."""

import os.path

from nif_test import TestSuite

# some tests to import and export nif files
# as list of (filename, config dictionary, list of objects to be selected)
# if the config has a game key then the test is an export test
# otherwise it's an import test

class TestSuiteHavok(TestSuite):
    def run(self):
        ob_meshes = os.path.join(
            self.config.get("path", "oblivion"), "meshes")

        self.test(
            filename=os.path.join(
                ob_meshes, "characters", "_male", "skeleton.nif"))
        self.test(
            filename="test/nif/_skeleton.nif",
            config=dict(
                game='OBLIVION',
                EXPORT_OB_MATERIAL=7, # skin
                EXPORT_OB_BSXFLAGS=7, # anim + havok + skel
                EXPORT_OB_MASS=605.0, # total mass, divided over all blocks
                EXPORT_OB_MOTIONSYSTEM=6,
                EXPORT_OB_QUALITYTYPE=2,
                EXPORT_OB_LAYER=8), # biped
            selection=['Scene Root'])

        self.test(
            filename=os.path.join(
                ob_meshes, "weapons", "blackaxe", "battleaxe.nif"))
        self.test(
            filename="test/nif/_battleaxe.nif",
            config=dict(game='OBLIVION',
                EXPORT_OB_LAYER=5, # weapon
                EXPORT_BHKLISTSHAPE=True,
                EXPORT_OB_MASS=23.0),
            selection=['BattleAxe'])

        self.test(
            filename=os.path.join(
                ob_meshes, "clutter", "magesguild", "crystalball02.nif"))
        self.test(
            filename="test/nif/_crystalball02.nif",
            config=dict(
                game='OBLIVION',
                EXPORT_BHKLISTSHAPE=True,
                EXPORT_OB_LAYER=4, # clutter
                EXPORT_OB_MASS=9.5),
            selection=['CrystalBall02'])

        self.test(
            filename=os.path.join(
                ob_meshes, "architecture", "anvil", "anvilcirclebench01.nif"))
        self.test(
            filename="test/nif/_anvilcirclebench01.nif",
            config=dict(game='OBLIVION'),
            selection=['AnvilCircleBench01'])

        self.test(
            filename=os.path.join(
                ob_meshes, "architecture", "magestower", "frostatron.nif"))
        self.test(
            filename="test/nif/_frostatron.nif",
            config=dict(game='OBLIVION'),
            selection=['FrostAtron'])

suite = TestSuiteHavok("havok")
suite.run()
