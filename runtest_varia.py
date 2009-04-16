"""Automated various tests for the blender nif scripts."""

# ***** BEGIN LICENSE BLOCK *****
# 
# BSD License
# 
# Copyright (c) 2005-2009, NIF File Format Library and Tools
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
from PyFFI.Formats.NIF import NifFormat

# some tests to import and export nif files

class VariaTestSuite(TestSuite):
    def isTwoSided(self, b_mesh):
        return b_mesh.data.mode & Blender.Mesh.Modes.TWOSIDED

    def hasStencil(self, nif_geom):
        return any(isinstance(prop, NifFormat.NiStencilProperty)
                   for prop in nif_geom.properties)

    def run(self):
        self.test_stencil()
        self.test_alpha()
        self.test_name_ends_with_null()
        self.test_unsupported_root()
        self.test_packed_textures()
        self.test_fo3_texture_slots()
        self.test_mw_nifxnifkf()

    def test_stencil(self):
        # stencil test
        self.test(
            filename = 'test/nif/stenciltest.nif')
        assert(self.isTwoSided(Blender.Object.Get("Stencil")))
        assert(not self.isTwoSided(Blender.Object.Get("NoStencil")))
        nif_export = self.test(
            filename = 'test/nif/_stenciltest.nif',
            config = dict(EXPORT_VERSION = 'Oblivion'),
            selection = ['NoStencil', 'Stencil'])
        nif_stencil = nif_export.root_blocks[0].find(
            block_type = NifFormat.NiGeometry, block_name = "Stencil")
        nif_nostencil = nif_export.root_blocks[0].find(
            block_type = NifFormat.NiGeometry, block_name = "NoStencil")
        assert(self.hasStencil(nif_stencil))
        assert(not self.hasStencil(nif_nostencil))

    def test_alpha(self):
        # alpha property test
        self.test(
            filename = 'test/nif/alphatest.nif')
        alpha_obj = Blender.Object.Get("Alpha")
        # check Z transparency
        assert(alpha_obj.data.materials[0].mode & Blender.Material.Modes.ZTRANSP)
        # check that transparency was exported
        alpha_obj_alpha = alpha_obj.data.materials[0].alpha
        assert(alpha_obj_alpha < 0.99)
        nif_export = self.test(
            filename = 'test/nif/_alphatest.nif',
            config = dict(EXPORT_VERSION = 'Oblivion'),
            selection = ['Alpha'])
        nif_alpha = nif_export.root_blocks[0].find(
            block_type = NifFormat.NiGeometry, block_name = "Alpha")
        nif_alpha_mat = nif_alpha.find(
            block_type = NifFormat.NiMaterialProperty)
        nif_alpha_alpha = nif_alpha.find(
            block_type = NifFormat.NiAlphaProperty)
        assert(nif_alpha_alpha.flags == 0x12ED)
        assert(nif_alpha_mat.alpha == alpha_obj_alpha)

    def test_name_ends_with_null(self):
        # name ends with null test
        self.test(
            filename = 'test/nif/name_ends_with_null.nif')
        obj = Blender.Object.Get("nullatend") # exists: null removed

    def test_unsupported_root(self):
        # unsupported root block (just check that it does not raise an
        # exception)
        self.test(
            filename='test/nif/unsupported_root.nif',
            next_layer=True)

    def test_packed_textures(self):
        """Check that textures:

        * raise an error if they have no filename
        * if they are packed, the filename is used and they are not packed
          in the nif.
        """
        # create a mesh
        self.logger.info("creating mesh")
        mesh_data = Blender.Mesh.Primitives.Cube()
        mesh_obj = self.scene.objects.new(mesh_data, "packed_tex_test")
        # add a texture
        self.logger.info("creating material and texture")
        mat = Blender.Material.New("packed_tex_mat")
        tex = Blender.Texture.New("packed_tex_tex")
        tex.setType("Image")
        # do not set an image for now... export must fail
        mat.setTexture(0, tex,
                       Blender.Texture.TexCo.UV, Blender.Texture.MapTo.COL)
        mesh_data.materials += [mat]
        mesh_data.addUVLayer("packed_tex_uv")
        try:
            nif_export = self.test(
                filename='test/nif/_packedtexurestest1.nif',
                config=dict(EXPORT_VERSION = 'Fallout 3'),
                selection=['packed_tex_test'],
                next_layer=False)
        except NifExportError, e:
            if str(e).startswith("image type texture has no file loaded"):
                pass
            else:
                raise ValueError(
                    "no texture loaded but wrong exception raised: "
                    "%s" % e)
            raise ValueError(
                "no texture loaded but no exception raised")
        # now set the image
        image = Blender.Image.New("test/nif/stub.tga", 1, 1, 24) # stub image
        tex.setImage(image)
        # this should work
        nif_export = self.test(
            filename='test/nif/_packedtexurestest2.nif',
            config=dict(EXPORT_VERSION = 'Fallout 3'),
            selection=['packed_tex_test'],
            next_layer=False)
        # now pack the image
        image.pack()
        # this should work too - although with a warning
        nif_export = self.test(
            filename='test/nif/_packedtexurestest3.nif',
            config=dict(EXPORT_VERSION = 'Fallout 3'),
            selection=['packed_tex_test'],
            next_layer=True)

    def test_fo3_texture_slots(self):
        self.test(
            filename = 'test/nif/fo3_textureslots.nif')
        # check textures (this example has all supported slots)
        obj = Blender.Object.Get("FO3TextureSlots")
        mat = obj.data.materials[0]
        mtex_diff = None
        mtex_norm = False
        mtex_glow = False
        for mtex in mat.textures:
            # skip empty ones
            if mtex is None:
                continue
            # check that mapping input is UV
            assert(mtex.texco == Blender.Texture.TexCo.UV)
            # check mapping output
            if mtex.mapto == Blender.Texture.MapTo.COL:
                if mtex_diff:
                    raise ValueError("more than one diffuse texture!")
                mtex_diff = mtex
            if mtex.mapto == Blender.Texture.MapTo.NOR:
                if mtex_norm:
                    raise ValueError("more than one normal texture!")
                mtex_norm = mtex
            # be forgiving for glow: EMIT or COL + EMIT
            if (mtex.mapto == Blender.Texture.MapTo.EMIT
                or mtex.mapto == Blender.Texture.MapTo.COL | Blender.Texture.MapTo.EMIT):
                if mtex_glow:
                    raise ValueError("more than one glow texture!")
                mtex_glow = mtex
        if not mtex_diff:
            raise ValueError("missing diffuse texture!")
        if not mtex_norm:
            raise ValueError("missing normal texture!")
        if not mtex_glow:
            raise ValueError("missing glow texture!")
        # test export too
        nif_export = self.test(
            filename='test/nif/_fo3_textureslots.nif',
            config=dict(EXPORT_VERSION='Fallout 3'),
            selection=['FO3TextureSlots'],
            next_layer=True)
        # check presence of the slots
        nif_textureset = nif_export.root_blocks[0].find(
            block_type = NifFormat.BSShaderTextureSet)
        assert(nif_textureset.numTextures == 6)
        assert(nif_textureset.textures[0] == "stub.dds")
        assert(nif_textureset.textures[1] == "stub_n.dds")
        assert(nif_textureset.textures[2] == "stub_g.dds")
        assert(nif_textureset.textures[3] == "")
        assert(nif_textureset.textures[4] == "")
        assert(nif_textureset.textures[5] == "")

    def test_mw_nifxnifkf(self):
        """Test the nif xnif kf export option."""
        # import a nif with animation
        self.test(
            filename = 'test/nif/mw/dance.nif')
        # export as nif + xnif + kf
        self.test(
            filename='test/nif/mw/_testnifxnifkf.nif',
            config=dict(EXPORT_VERSION='Morrowind',
                        EXPORT_MW_NIFXNIFKF=True),
            selection=['Dance'],
            next_layer=True)
        # check that these files are present, and check some of their properties
        with closing(open('test/nif/mw/_testnifxnifkf.nif')) as stream:
            nif = NifFormat.Data()
            nif.read(stream)
        with closing(open('test/nif/mw/x_testnifxnifkf.nif')) as stream:
            xnif = NifFormat.Data()
            xnif.read(stream)
        with closing(open('test/nif/mw/x_testnifxnifkf.kf')) as stream:
            xkf = NifFormat.Data()
            xkf.read(stream)
        # check root blocks
        assert(len(nif.roots) == 1)
        assert(len(xnif.roots) == 1)
        assert(len(xkf.roots) == 1)
        assert(isinstance(nif.roots[0], NifFormat.NiNode))
        assert(isinstance(xnif.roots[0], NifFormat.NiNode))
        assert(isinstance(xkf.roots[0], NifFormat.NiSequenceStreamHelper))
        # compare text keys
        nif_textkeys = nif.roots[0].extraData
        xkf_textkeys = xkf.roots[0].extraData
        assert(isinstance(nif_textkeys, NifFormat.NiTextKeyExtraData))
        assert(isinstance(xkf_textkeys, NifFormat.NiTextKeyExtraData))
        assert(nif_textkeys == xkf_textkeys)

suite = VariaTestSuite("varia")
suite.run()
