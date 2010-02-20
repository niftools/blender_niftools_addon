"""Automated skinning tests for the blender nif scripts."""

# ***** BEGIN LICENSE BLOCK *****
# 
# BSD License
# 
# Copyright (c) 2005-2010, NIF File Format Library and Tools
# All rights reserved.
# 
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions
# are met:
# 1. Redistributions of source code must retain the above copyright
#    notice, this list of conditions and the following disclaimer.
# 2. Redistributions in binary form must reproduce the above copyright
#    notice, this list of conditions and the following disclaimer in the
#    documentation and/or other materials provided with the distribution.
# 3. The name of the NIF File Format Library and Tools project may not be
#    used to endorse or promote products derived from this software
#    without specific prior written permission.
# 
# THIS SOFTWARE IS PROVIDED BY THE AUTHOR ``AS IS'' AND ANY EXPRESS OR
# IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED WARRANTIES
# OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE DISCLAIMED.
# IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR ANY DIRECT, INDIRECT,
# INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT
# NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE,
# DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY
# THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
# (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF
# THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
#
# ***** END LICENSE BLOCK *****

from itertools import izip
import os.path

from nif_test import TestSuite
from pyffi.formats.nif import NifFormat
from pyffi.spells.nif.check import SpellCompareSkinData
from pyffi.spells.nif import NifToaster

# some tests to import and export nif files

class SkinningTestSuite(TestSuite):
    def run(self):
        # morrowind creature
        mw_babelfish = os.path.join(
            self.config.get("path", "morrowind"),
            "meshes", "r", "babelfish.nif")
        self.test(filename = mw_babelfish)
        self.test(
            filename = 'test/nif/_babelfish.nif',
            config = dict(
                EXPORT_VERSION = 'Morrowind',
                EXPORT_STRIPIFY = False, EXPORT_SKINPARTITION = False),
            selection = ['Root Bone'])

        # oblivion full body
        ob_male = os.path.join(
            self.config.get("path", "oblivion"),
            "meshes", "characters", "_male")
        ob_skeleton = os.path.join(ob_male, "skeleton.nif")
        ob_bodyparts = [
            os.path.join(ob_male, bodypart + ".nif")
            for bodypart in ["upperbody", "lowerbody", "hand", "foot"]]
        # import skeleton and body parts
        self.test(
            filename = ob_skeleton,
            config = dict(IMPORT_SKELETON = 1))
        for ob_bodypart in ob_bodyparts:
            self.test(
                filename = ob_bodypart,
                config = dict(IMPORT_SKELETON = 2),
                selection = ['Scene Root'])
        # export it
        self.test(
            filename = 'test/nif/_fulloblivionbody.nif',
            config = dict(
                EXPORT_VERSION = 'Oblivion', EXPORT_SMOOTHOBJECTSEAMS = True,
                EXPORT_FLATTENSKIN = True),
            selection = ['Scene Root'])
        # compare skindata
        toaster = NifToaster(spellclass=SpellCompareSkinData,
                             options=dict(arg="test/nif/_fulloblivionbody.nif",
                                          verbose=99))
        for ob_bodypart in ob_bodyparts:
            toaster.toast(top=ob_bodypart)

        # morrowind better bodies mesh
        bbskin_import = self.test(filename = 'test/nif/bb_skinf_br.nif')
        bbskin_export = self.test(
            filename = 'test/nif/_bb_skinf_br.nif',
            config = dict(
                EXPORT_VERSION = 'Morrowind', EXPORT_SMOOTHOBJECTSEAMS = True,
                EXPORT_STRIPIFY = False, EXPORT_SKINPARTITION = False),
            selection = ['Bip01'])
        toaster = NifToaster(spellclass=SpellCompareSkinData,
                             options=dict(arg="test/nif/_bb_skinf_br.nif",
                                          verbose=99))
        toaster.toast(top="test/nif/bb_skinf_br.nif")

suite = SkinningTestSuite("skinning")
suite.run()
