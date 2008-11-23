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

class SkinningTestSuite(TestSuite):
    def run(self):
        # fallout 3 body
        self.test(
            filename = 'test/nif/fo3/fo3_bodybindpose.nif',
            config = dict(IMPORT_SKELETON=1,
                          IMPORT_ANIMATION=False))
        self.test(
            filename = 'test/nif/fo3/femaleupperbody.nif',
            config = dict(IMPORT_SKELETON=2),
            selection = ['Scene Root'])
        self.test(
            filename = 'test/nif/fo3/_femaleupperbody.nif',
            config = dict(
                EXPORT_VERSION = 'Fallout 3', EXPORT_SMOOTHOBJECTSEAMS = True,
                EXPORT_FLATTENSKIN = True),
            selection = ['Scene Root'])
        # compare skindata
        toaster = NifToaster(spellclass=SpellCompareSkinData,
                             options=dict(arg="test/nif/fo3/_femaleupperbody.nif",
                                          verbose=99))
        toaster.toast(top="test/nif/fo3/femaleupperbody.nif")

### "Scene Root" of champion armor conflicts with "Scene Root" of full body
### test below, so for now this test is disabled until a solution is found
#suite = TestSuiteChampionArmor("champion_armor")
#suite.run()
suite = SkinningTestSuite("skinning")
suite.run()

