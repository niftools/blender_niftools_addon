"""Automated various tests for the blender nif scripts."""

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

class VariaTestSuite(TestSuite):
    def isTwoSided(self, b_mesh):
        return b_mesh.data.show_double_sided

    def hasStencil(self, nif_geom):
        return any(isinstance(prop, NifFormat.NiStencilProperty)
                   for prop in nif_geom.properties)

    def run(self):
        self.test_bounding_box()
        self.test_bounding_box_bsbound()
        self.test_stencil()
        self.test_alpha()
        self.test_name_ends_with_null()
        self.test_unsupported_root()
        self.test_packed_textures()
        self.test_fo3_texture_slots()
        self.test_fo3_emit()
        self.test_fo3_emit2()
        self.test_uv_controller()
        self.test_mw_nifxnifkf()
        self.test_anim_buffer_out_of_range()
        self.test_ob_animsequencename()

    def test_bounding_box(self):
        """Bounding box test."""
        # import
        nif_import = self.test(
            filename='test/nif/bounding_box.nif')
        b_bbox = Blender.Object.Get("Bounding Box")
        # test stuff
        assert(b_bbox.display_bounds_type == 'BOX')
        # export
        nif_export = self.test(
            filename='test/nif/_bounding_box.nif',
            config=dict(game = 'MORROWIND'),
            selection = ['Bounding Box'])
        # test stuff...
        bbox = nif_export.root_blocks[0].children[0]
        assert(bbox.has_bounding_box)

    def test_bounding_box_bsbound(self):
        """Oblivion bounding box (BSBound) test."""
        def check_bsbound(root_blocks):
            bsbound = root_blocks[0].extra_data_list[0]
            assert(isinstance(bsbound, NifFormat.BSBound))
            assert(bsbound.name == "BBX")
            assert(bsbound.next_extra_data is None)
            # using assert_equal because we compare floats
            self.assert_equal(bsbound.center.x, 0.0)
            self.assert_equal(bsbound.center.y, 0.0)
            self.assert_equal(bsbound.center.z, 66.2201843262)
            self.assert_equal(bsbound.dimensions.x, 23.0976696014)
            self.assert_equal(bsbound.dimensions.y, 17.6446208954)
            self.assert_equal(bsbound.dimensions.z, 66.2201843262)
        # import
        with closing(open('test/nif/bounding_box_bsbound.nif')) as stream:
            self.info("Reading test/nif/bounding_box_bsbound.nif")
            nif = NifFormat.Data()
            nif.read(stream)
            check_bsbound(nif.roots)
        nif_import = self.test(
            filename='test/nif/bounding_box_bsbound.nif')
        b_bbox = Blender.Object.Get("BSBound")
        # test stuff
        assert(b_bbox.display_bounds_type == 'BOX')
        # export
        nif_export = self.test(
            filename='test/nif/_bounding_box_bsbound.nif',
            config=dict(game = 'OBLIVION'),
            selection = ['BSBound'])
        # test stuff...
        with closing(open('test/nif/_bounding_box_bsbound.nif')) as stream:
            self.info("Reading test/nif/_bounding_box_bsbound.nif")
            nif = NifFormat.Data()
            nif.read(stream)
            check_bsbound(nif.roots)

    def test_stencil(self):
        # stencil test
        self.test(
            filename = 'test/nif/stenciltest.nif')
        assert(self.isTwoSided(Blender.Object.Get("Stencil")))
        assert(not self.isTwoSided(Blender.Object.Get("NoStencil")))
        nif_export = self.test(
            filename = 'test/nif/_stenciltest.nif',
            config = dict(game = 'OBLIVION'),
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
            config = dict(game = 'OBLIVION'),
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
        self.info("creating mesh")
        mesh_data = Blender.Mesh.Primitives.Cube()
        mesh_obj = self.context.scene.objects.new(mesh_data, "packed_tex_test")
        # add a texture
        self.info("creating material and texture")
        mat = bpy.data.materials.new("packed_tex_mat")
        tex = bpy.ops.texture.new()
        tex.name = "packed_tex_tex"
        tex.setType("Image")
        # do not set an image for now... export must fail
        mat.setTexture(0, tex,
                       'UV', FIXME.use_map_color_diffuse)
        mesh_data.materials += [mat]
        mesh_data.addUVLayer("packed_tex_uv")
        try:
            nif_export = self.test(
                filename='test/nif/_packedtexturestest1.nif',
                config=dict(game = 'FALLOUT_3'),
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
            filename='test/nif/_packedtexturestest2.nif',
            config=dict(game = 'FALLOUT_3'),
            selection=['packed_tex_test'],
            next_layer=False)
        # now pack the image
        image.pack()
        # this should work too - although with a warning
        nif_export = self.test(
            filename='test/nif/_packedtexturestest3.nif',
            config=dict(game = 'FALLOUT_3'),
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
            assert(mtex.texture_coords == 'UV')
            # check mapping output
            if mtex.use_map_color_diffuse:
                if mtex_diff:
                    raise ValueError("more than one diffuse texture!")
                mtex_diff = mtex
            if mtex.use_map_normal:
                if mtex_norm:
                    raise ValueError("more than one normal texture!")
                mtex_norm = mtex
            if mtex.use_map_emit:
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
            config=dict(game='FALLOUT_3'),
            selection=['FO3TextureSlots'],
            next_layer=True)
        # check presence of the slots
        nif_textureset = nif_export.root_blocks[0].find(
            block_type = NifFormat.BSShaderTextureSet)
        assert(nif_textureset.num_textures == 6)
        assert(nif_textureset.textures[0] == "stub.dds")
        assert(nif_textureset.textures[1] == "stub_n.dds")
        assert(nif_textureset.textures[2] == "stub_g.dds")
        assert(nif_textureset.textures[3] == "")
        assert(nif_textureset.textures[4] == "")
        assert(nif_textureset.textures[5] == "")

    def test_mw_nifxnifkf(self):
        """Test the nif xnif kf export option."""
        def check_ctrl_flags(root):
            # test the kfctrl flags to be active + clamp
            for ctrl in root.get_global_iterator():
                if not isinstance(ctrl, NifFormat.NiTimeController):
                    continue
                if ctrl.flags != 12:
                    raise ValueError("bad value for controller flags")
        
        # import a nif with animation
        dance = self.test(
            filename = 'test/nif/mw/dance.nif')
        check_ctrl_flags(dance.root_blocks[0])
        # export as nif + xnif + kf
        self.test(
            filename='test/nif/mw/_testnifxnifkf.nif',
            config=dict(game='MORROWIND',
                        animation='ALL_NIF_XNIF_XKF'),
            selection=['Dance'],
            next_layer=True)
        # check that these files are present, and check some of their properties
        with closing(open('test/nif/mw/_testnifxnifkf.nif')) as stream:
            self.info("Reading test/nif/mw/_testnifxnifkf.nif")
            nif = NifFormat.Data()
            nif.read(stream)
        with closing(open('test/nif/mw/x_testnifxnifkf.nif')) as stream:
            self.info("Reading test/nif/mw/x_testnifxnifkf.nif")
            xnif = NifFormat.Data()
            xnif.read(stream)
        with closing(open('test/nif/mw/x_testnifxnifkf.kf')) as stream:
            self.info("Reading test/nif/mw/x_testnifxnifkf.kf")
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
        nif_textkeys = nif.roots[0].extra_data
        xkf_textkeys = xkf.roots[0].extra_data
        assert(isinstance(nif_textkeys, NifFormat.NiTextKeyExtraData))
        assert(isinstance(xkf_textkeys, NifFormat.NiTextKeyExtraData))
        #assert(nif_textkeys == xkf_textkeys) # ... up to extra data chain
        # check that xkf has no target set in keyframe controller
        ctrl = xkf.roots[0].controller
        while ctrl:
            if ctrl.target is not None:
                raise ValueError(
                    "NiKeyframeController target should be None in xkf")
            ctrl = ctrl.next_controller
        # check controller flags
        check_ctrl_flags(xkf.roots[0])

    def test_fo3_emit(self):

        def check_emit(nif):
            nif_mat = nif.root_blocks[0].find(
                block_type = NifFormat.NiMaterialProperty)
            self.assert_equal(nif_mat.emissive_color.r, 0.123)
            self.assert_equal(nif_mat.emissive_color.g, 0.456)
            self.assert_equal(nif_mat.emissive_color.b, 0.789)
            self.assert_equal(nif_mat.emit_multi, 3.82)
        
        # loading the test nif
        # (this nif has emit color 1,0,1 and emitmulti 3)
        # stencil test
        nif = self.test(filename='test/nif/fo3/test_emit.nif')
        # double check that the nif itself has the claimed values
        check_emit(nif)
        # check imported values
        obj = Blender.Object.Get("TestEmit")
        self.assert_equal(obj.data.materials[0].rgbCol[0], 0.123)
        self.assert_equal(obj.data.materials[0].rgbCol[1], 0.456)
        self.assert_equal(obj.data.materials[0].rgbCol[2], 0.789)
        self.assert_equal(obj.data.materials[0].emit, 0.382) # emitmulti divided by 10
        # write the file
        nif = self.test(
            filename='test/nif/fo3/_test_emit.nif',
            config=dict(game = 'FALLOUT_3'),
            selection=['TestEmit'],
            next_layer=True)
        # check that the correct values were exported
        check_emit(nif)

    def test_fo3_emit2(self):
        """Check that emissive and multi are preserved also when they are
        zero and one.
        """
        def check_emit2(nif):
            nif_mat = nif.root_blocks[0].find(
                block_type = NifFormat.NiMaterialProperty)
            self.assert_equal(nif_mat.emissive_color.r, 0.0)
            self.assert_equal(nif_mat.emissive_color.g, 0.0)
            self.assert_equal(nif_mat.emissive_color.b, 0.0)
            self.assert_equal(nif_mat.emit_multi, 1.0)
        
        # loading the test nif
        # (this nif has emit color 1,0,1 and emitmulti 3)
        # stencil test
        nif = self.test(filename='test/nif/fo3/test_emit2.nif')
        # double check that the nif itself has the claimed values
        check_emit2(nif)
        # check imported values
        obj = Blender.Object.Get("TestEmit2")
        self.assert_equal(obj.data.materials[0].rgbCol[0], 1.0)
        self.assert_equal(obj.data.materials[0].rgbCol[1], 1.0)
        self.assert_equal(obj.data.materials[0].rgbCol[2], 1.0)
        self.assert_equal(obj.data.materials[0].emit, 0.0)
        # write the file
        nif = self.test(
            filename='test/nif/fo3/_test_emit2.nif',
            config=dict(game='FALLOUT_3'),
            selection=['TestEmit2'],
            next_layer=True)
        # check that the correct values were exported
        check_emit2(nif)

    def test_uv_controller(self):
        """Test whether uv controllers are imported and exported correctly."""
        def check_uv_controller(nif):
            # XXX some uv controlled geometries need such node...
            #nif_animnode = nif.root_blocks[0].find(
            #    block_type = NifFormat.NiBSAnimationNode)
            #assert(nif_animnode)
            nif_node = nif.root_blocks[0].find(
                block_type=NifFormat.NiTriBasedGeom)
            assert(nif_node.name.startswith("TestUVController"))
            nif_uvctrl = nif_node.get_controllers()[0]
            assert(nif_uvctrl)
            nif_uvdata = nif_uvctrl.data
            assert(nif_uvdata)
            nif_ofsu = nif_uvdata.uv_groups[0]
            assert(nif_ofsu.num_keys == 2)

        # loading the test nif
        # (this nif has emit color 1,0,1 and emitmulti 3)
        # stencil test
        nif = self.test(filename='test/nif/mw/test_uvcontroller.nif')
        # double check that nif has the claimed values
        check_uv_controller(nif)
        # check that the controllers are present in blender
        obj = Blender.Object.Get("TestUVController")
        mat = obj.data.materials[0]
        # check that there is material offset animation data
        assert(mat.ipo)
        assert(mat.ipo[Blender.Ipo.MA_OFSX])
        # export
        nif = self.test(
            filename='test/nif/mw/_test_uvcontroller.nif',
            config=dict(game='MORROWIND'),
            selection=['TestUVController'],
            next_layer=False)
        # check that nif was correctly exported
        check_uv_controller(nif)
        # export again, with BSAnimationNode
        nif = self.test(
            filename='test/nif/mw/_test_bsanimation_uvcontroller.nif',
            config=dict(
                game='MORROWIND',
                EXPORT_MW_BS_ANIMATION_NODE=True),
            selection=['TestUVController'],
            next_layer=True)
        # check that nif was correctly exported
        check_uv_controller(nif)
        assert(isinstance(nif.root_blocks[0], NifFormat.NiBSAnimationNode))
        assert(nif.root_blocks[0].flags == 42)

    def test_anim_buffer_out_of_range(self):
        # create animation keys
        try:
            animtxt = Blender.Text.Get("Anim")
            animtxt.clear()
        except NameError:
            animtxt = Blender.Text.New("Anim")
        animtxt.write("%i/Idle: Start/Idle: Loop Start\n"
                      "%i/Idle: Loop Stop/Idle: Stop"
                      % (-1000000, 1000000))
        # export: should warn but not fail
        nif = self.test(
            filename='test/nif/mw/_test_anim_buffer_out_of_range.nif',
            config=dict(game='MORROWIND'),
            selection=[],
            next_layer=False)
        # remove the animation keys
        Blender.Text.unlink(animtxt)

    def test_ob_animsequencename(self):
        """Test Oblivion animation sequence name export option."""
        # import a nif with animation
        dance = self.test(
            filename = 'test/nif/mw/dance.nif')
        # export as kf
        self.test(
            filename='test/nif/ob/_testanimseqname.kf',
            config=dict(game='OBLIVION',
                        animation='ANIM_KF',
                        EXPORT_ANIMSEQUENCENAME="TestAnimSeqName"),
            selection=['Dance'],
            next_layer=True)
        # check that these files are present, and check some of their properties
        with closing(open('test/nif/ob/_testanimseqname.kf')) as stream:
            self.info("Reading test/nif/ob/_testanimseqname.kf")
            kf = NifFormat.Data()
            kf.read(stream)
        # check root block
        assert(len(kf.roots) == 1)
        assert(isinstance(kf.roots[0], NifFormat.NiControllerSequence))
        # check animation sequence name
        assert(kf.roots[0].name == "TestAnimSeqName")

suite = VariaTestSuite("varia")
suite.run()
