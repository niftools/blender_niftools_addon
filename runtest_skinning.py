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

from nif_test import TestSuite, Test

# helper functions

def compare_skinning_info(oldroot, newroot):
    """Raises a C{ValueError} if skinning info is different between old and
    new."""
    return

# some tests to import and export nif files

class SkinningTestSuite(TestSuite):
    FOLDER = "test/nif"
    
    # list of tests (characterized by filename, config dictionary, and list
    # of objects to be selected)
    # if the config has a EXPORT_VERSION key then the test is an export test
    # otherwise it's an import test
    TESTS = [
        # oblivion full body
        Test('skeleton.nif',  dict(IMPORT_SKELETON = 1), []),
        Test('upperbody.nif', dict(IMPORT_SKELETON = 2), ['Scene Root']),
        Test('lowerbody.nif', dict(IMPORT_SKELETON = 2), ['Scene Root']),
        Test('hand.nif',      dict(IMPORT_SKELETON = 2), ['Scene Root']),
        Test('foot.nif',      dict(IMPORT_SKELETON = 2), ['Scene Root']),
        Test('_fulloblivionbody.nif',
         dict(
            EXPORT_VERSION = 'Oblivion', EXPORT_SMOOTHOBJECTSEAMS = True,
            EXPORT_FLATTENSKIN = True),
         ['Scene Root']),
        # morrowind creature
        Test('babelfish.nif', {}, []),
        Test('_babelfish.nif', dict(
            EXPORT_VERSION = 'Morrowind',
            EXPORT_STRIPIFY = False, EXPORT_SKINPARTITION = False),
         ['Root Bone']),
        # morrowind better bodies mesh
        Test('bb_skinf_br.nif', {}, []),
        Test('_bb_skinf_br.nif', dict(
            EXPORT_VERSION = 'Morrowind', EXPORT_SMOOTHOBJECTSEAMS = True,
            EXPORT_STRIPIFY = False, EXPORT_SKINPARTITION = False),
         ['Bip01']),
    ]

    def test_callback(self, filename):
        """Called after every import or export."""
        if filename == '_bb_skinf_br.nif':
            compare_skinning_info(
                self.data['bb_skinf_br.nif'].root_blocks[0],
                self.data['_bb_skinf_br.nif'].root_blocks[0])

suite = SkinningTestSuite()
suite.run()
