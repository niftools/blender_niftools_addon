"""Automated skinning tests for the blender nif scripts."""

# ***** BEGIN LICENSE BLOCK *****
# 
# BSD License
# 
# Copyright (c) 2005-2011, NIF File Format Library and Tools
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

class EgmTestSuite(TestSuite):
    def run(self):
        # oblivion imperial head
        ob_head = os.path.join(
            self.config.get("path", "oblivion"),
            "meshes", "characters", "imperial", "headhuman.nif")
        ob_head_egm = os.path.join(
            self.config.get("path", "oblivion"),
            "meshes", "characters", "imperial", "headhuman.egm")
        self.test(
            filename=ob_head,
            config=dict(
                IMPORT_EGMFILE=ob_head_egm,
                IMPORT_EGMANIM=True,
                IMPORT_EGMANIMSCALE=10)
            )
        # note: not all of the egm will be exported back
        # as part of geometry info is stored in tri file
        self.test(
            filename = 'test/nif/ob/_headhuman.nif',
            config = dict(EXPORT_VERSION='Oblivion'),
            selection = ['Scene Root', '_MedNeutral']
            )

suite = EgmTestSuite("egm")
suite.run()
