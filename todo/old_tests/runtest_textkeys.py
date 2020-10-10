"""Automated tests for the blender nif scripts: text key import and export."""

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

import Blender
from nif_test import TestSuite
from pyffi.formats.nif import NifFormat

# some tests to import and export nif files

class TextKeyTestSuite(TestSuite):
    def run(self):
        nif_import = self.test(
            filename = 'test/nif/mw/dance.nif')
        textkeys_import = nif_import.root_blocks[0].find(
            block_type = NifFormat.NiTextKeyExtraData)

        nif_export = self.test(
            filename = 'test/nif/mw/_textkeytest.nif',
            config = dict(game = 'MORROWIND'),
            selection = ['Dance'])
        textkeys_export = nif_export.root_blocks[0].find(
            block_type = NifFormat.NiTextKeyExtraData)

        if textkeys_import.num_text_keys != textkeys_export.num_text_keys:
            raise ValueError("number of text keys does not match")
        for textkey_import, textkey_export in zip(textkeys_import.text_keys, textkeys_export.text_keys):
            if abs(textkey_import.time - textkey_export.time) > 0.0001:
                raise ValueError(f"key times do not match "
                                f"({textkey_import.time:f} != "
                                f"{textkey_export.time:f})")
            if textkey_import.value != textkey_export.value:
                raise ValueError(f"key values do not match "
                                 f"({textkey_import.value} != "
                                 f"{textkey_export.value})")

suite = TextKeyTestSuite("textkey")
suite.run()

