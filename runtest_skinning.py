"""Automated skinning tests for the blender nif scripts."""

# ***** BEGIN LICENSE BLOCK *****
# 
# BSD License
# 
# Copyright (c) 2007-2008, NIF File Format Library and Tools
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

from nif_test import TestSuite
from PyFFI.Formats.NIF import NifFormat
from PyFFI.Spells.NIF.check import SpellCompareSkinData
from PyFFI.Spells.NIF import NifToaster

# some tests to import and export nif files

class TestSuiteChampionArmor(TestSuite):
    def run(self):
        # champion armor
        self.test(
            filename = 'test/nif/cuirass.nif')
        self.test(
            filename = 'test/nif/_cuirass.nif',
            config = dict(
                EXPORT_VERSION = 'Oblivion', EXPORT_SMOOTHOBJECTSEAMS = True,
                EXPORT_FLATTENSKIN = True),
            selection = ['Scene Root'])
        toaster = NifToaster(spellclass=SpellCompareSkinData,
                             options=dict(arg="test/nif/_cuirass.nif",
                                          verbose=99))
        toaster.toast(top="test/nif/cuirass.nif")

class SkinningTestSuite(TestSuite):
    def run(self):
        # oblivion full body
        self.test(
            filename = 'test/nif/skeleton.nif',
            config = dict(IMPORT_SKELETON = 1))
        self.test(
            filename = 'test/nif/upperbody.nif',
            config = dict(IMPORT_SKELETON = 2),
            selection = ['Scene Root'])
        self.test(
            filename = 'test/nif/lowerbody.nif',
            config = dict(IMPORT_SKELETON = 2),
            selection = ['Scene Root'])
        self.test(
            filename = 'test/nif/hand.nif',
            config = dict(IMPORT_SKELETON = 2),
            selection = ['Scene Root'])
        self.test(
            filename = 'test/nif/foot.nif',
            config = dict(IMPORT_SKELETON = 2),
            selection = ['Scene Root'])
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
        toaster.toast(top="test/nif/upperbody.nif")
        toaster.toast(top="test/nif/lowerbody.nif")
        toaster.toast(top="test/nif/hand.nif")
        toaster.toast(top="test/nif/foot.nif")
        # morrowind creature
        self.test(filename = 'test/nif/babelfish.nif')
        self.test(
            filename = 'test/nif/_babelfish.nif',
            config = dict(
                EXPORT_VERSION = 'Morrowind',
                EXPORT_STRIPIFY = False, EXPORT_SKINPARTITION = False),
            selection = ['Root Bone'])
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

### "Scene Root" of champion armor conflicts with "Scene Root" of full body
### test below, so for now this test is disabled until a solution is found
#suite = TestSuiteChampionArmor("champion_armor")
#suite.run()
suite = SkinningTestSuite("skinning")
suite.run()

