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

# helper functions

def compare_skinning_info(oldroot, newroot):
    """Raises a C{ValueError} if skinning info is different between old and
    new."""
    print("checking skinning data...")
    # get the geometries
    for oldgeom in oldroot.tree(block_type = NifFormat.NiGeometry):
        for newgeom in newroot.tree(block_type = NifFormat.NiGeometry):
            # list all old bones
            for oldbone, oldbonedata \
                in izip(oldgeom.skinInstance.bones,
                        oldgeom.skinInstance.data.boneList):
                for newbone, newbonedata \
                    in izip(newgeom.skinInstance.bones,
                        newgeom.skinInstance.data.boneList):
                    if oldbone.name == newbone.name:
                        print ("  checking bone %s" % oldbone.name)
                        # comparing
                        if oldbonedata.rotation != newbonedata.rotation:
                            raise ValueError(
                                "rotation mismatch\n%s\n!=\n%s\n"
                                % (oldbonedata.rotation, newbonedata.rotation))
                        if oldbonedata.translation != newbonedata.translation:
                            raise ValueError(
                                "translation mismatch\n%s\n!=\n%s\n"
                                % (oldbonedata.translation,
                                   newbonedata.translation))
                        if abs(oldbonedata.scale - newbonedata.scale) > 0.0001:
                            raise ValueError(
                                "scale mismatch %s != %s"
                                % (oldbonedata.scale, newbonedata.scale))
    return

# some tests to import and export nif files

class SkinningTestSuite(TestSuite):
    def run(self):
        # oblivion full body
        bodyskel = self.test(
            filename = 'test/nif/skeleton.nif',
            config = dict(IMPORT_SKELETON = 1))
        bodyupp = self.test(
            filename = 'test/nif/upperbody.nif',
            config = dict(IMPORT_SKELETON = 2),
            selection = ['Scene Root'])
        bodylow = self.test(
            filename = 'test/nif/lowerbody.nif',
            config = dict(IMPORT_SKELETON = 2),
            selection = ['Scene Root'])
        bodyhand = self.test(
            filename = 'test/nif/hand.nif',
            config = dict(IMPORT_SKELETON = 2),
            selection = ['Scene Root'])
        bodyfoot = self.test(
            filename = 'test/nif/foot.nif',
            config = dict(IMPORT_SKELETON = 2),
            selection = ['Scene Root'])
        body_export = self.test(
            filename = 'test/nif/_fulloblivionbody.nif',
            config = dict(
                EXPORT_VERSION = 'Oblivion', EXPORT_SMOOTHOBJECTSEAMS = True,
                EXPORT_FLATTENSKIN = True),
            selection = ['Scene Root'])
        compare_skinning_info(
            NifFormat.read(open("test/nif/upperbody.nif", "rb"), version=0x14000005, user_version=11)[0],
            body_export.root_blocks[0])
        compare_skinning_info(
            NifFormat.read(open("test/nif/lowerbody.nif", "rb"), version=0x14000005, user_version=11)[0],
            body_export.root_blocks[0])
        compare_skinning_info(
            NifFormat.read(open("test/nif/hand.nif", "rb"), version=0x14000005, user_version=11)[0],
            body_export.root_blocks[0])
        compare_skinning_info(
            NifFormat.read(open("test/nif/foot.nif", "rb"), version=0x14000005, user_version=11)[0],
            body_export.root_blocks[0])
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
        compare_skinning_info(
            bbskin_import.root_blocks[0],
            bbskin_export.root_blocks[0])

suite = SkinningTestSuite("skinning")
suite.run()

