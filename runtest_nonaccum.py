"""Automated non-accum node tests for the blender nif scripts."""

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

from __future__ import with_statement
from contextlib import closing
from itertools import izip

import Blender
from nif_test import TestSuite
from pyffi.formats.nif import NifFormat

# some tests to import and export nif files

class NonAccumTestSuite(TestSuite):

    def run(self):
        self.test_nonaccum_export()

    def test_nonaccum_export(self):
        """Test the nonaccum xy export option."""
        # import a nif with animation
        dance = self.test(
            filename = 'test/nif/mw/dance.nif')
        # export as nif with animation, default
        self.test(
            filename='test/nif/ob/_testnonaccum_default.nif',
            config=dict(EXPORT_VERSION='Oblivion',
                        EXPORT_NONACCUM=0),
            selection=['Dance'],
            next_layer=False)
        # export as nif with animation, accum xy
        self.test(
            filename='test/nif/ob/_testnonaccum_accumxy.nif',
            config=dict(EXPORT_VERSION='Oblivion',
                        EXPORT_NONACCUM=1),
            selection=['Dance'],
            next_layer=False)
        # export as nif with animation, no accum
        self.test(
            filename='test/nif/ob/_testnonaccum_accumnone.nif',
            config=dict(EXPORT_VERSION='Oblivion',
                        EXPORT_NONACCUM=2),
            selection=['Dance'],
            next_layer=False)
        # check that these files are present, and check some of their properties
        with closing(open('test/nif/ob/_testnonaccum_default.nif')) as stream:
            self.logger.info("Reading test/nif/ob/_testnonaccum_default.nif")
            nif_default = NifFormat.Data()
            nif_default.read(stream)
        with closing(open('test/nif/ob/_testnonaccum_accumxy.nif')) as stream:
            self.logger.info("Reading test/nif/ob/_testnonaccum_accumxy.nif")
            nif_xy = NifFormat.Data()
            nif_xy.read(stream)
        with closing(open('test/nif/ob/_testnonaccum_accumnone.nif')) as stream:
            self.logger.info("Reading test/nif/ob/_testnonaccum_accumnone.nif")
            nif_none = NifFormat.Data()
            nif_none.read(stream)
        # check root blocks
        assert(len(nif_default.roots) == 1)
        assert(len(nif_xy.roots) == 1)
        assert(len(nif_none.roots) == 1)
        assert(isinstance(nif_default.roots[0], NifFormat.NiNode))
        assert(isinstance(nif_xy.roots[0], NifFormat.NiNode))
        assert(isinstance(nif_none.roots[0], NifFormat.NiNode))

suite = NonAccumTestSuite("nonaccum")
suite.run()
