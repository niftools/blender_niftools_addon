"""Automated Fallout 3 skeleton test for the blender nif scripts."""

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

class SkeletonTestSuite(TestSuite):
    def run(self):
        # fo3 body path
        fo3_male = os.path.join(
            self.config.get("path", "fallout3"),
            "meshes", "characters", "_male")
        nif_import = self.test(
            filename=os.path.join(fo3_male, "skeleton.nif"),
            config=dict(
                IMPORT_ANIMATION=True))
        nif_export = self.test(
            filename = 'test/nif/fo3/_skeleton.nif',
            config = dict(
                game='FALLOUT_3', EXPORT_SMOOTHOBJECTSEAMS=True,
                EXPORT_FLATTENSKIN=True),
            selection = ['Scene Root'])
        # open original nif to get rid of possible issues with scale
        # correction in nif_import
        data = NifFormat.Data()
        with open(os.path.join(fo3_male, "skeleton.nif")) as stream:
            data.read(stream)
        # compare NiNode transforms
        for n_imp_node in data.roots[0].tree():
            if not isinstance(n_imp_node, NifFormat.NiNode):
                continue
            for n_exp_node in nif_export.root_blocks[0].tree():
                if not isinstance(n_exp_node, NifFormat.NiNode):
                    continue
                if n_imp_node.name != n_exp_node.name:
                    continue
                # check that transforms are equal
                self.info(f"checking transform of {n_imp_node.name:s}")
                if (n_imp_node.get_transform() != n_exp_node.get_transform()):
                    raise ValueError(f"transforms are different\n"
                                     f"{n_imp_node.get_transform():s}\n"
                                     f"{n_exp_node.get_transform():s}\n")

suite = SkeletonTestSuite("skeleton")
suite.run()

