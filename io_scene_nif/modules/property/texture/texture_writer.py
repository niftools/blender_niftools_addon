"""This script contains helper methods to export textures sources."""

# ***** BEGIN LICENSE BLOCK *****
# 
# Copyright © 2013, NIF File Format Library and Tools contributors.
# All rights reserved.
# 
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions
# are met:
# 
#    * Redistributions of source code must retain the above copyright
#      notice, this list of conditions and the following disclaimer.
# 
#    * Redistributions in binary form must reproduce the above
#      copyright notice, this list of conditions and the following
#      disclaimer in the documentation and/or other materials provided
#      with the distribution.
# 
#    * Neither the name of the NIF File Format Library and Tools
#      project nor the names of its contributors may be used to endorse
#      or promote products derived from this software without specific
#      prior written permission.
# 
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS
# "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
# LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS
# FOR A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE
# COPYRIGHT OWNER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT,
# INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING,
# BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES;
# LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER
# CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT
# LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN
# ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
# POSSIBILITY OF SUCH DAMAGE.
#
# ***** END LICENSE BLOCK *****

import bpy

from pyffi.formats.nif import NifFormat

from io_scene_nif.utility import nif_utils
from io_scene_nif.utility.nif_logging import NifLog
from io_scene_nif.utility.nif_global import NifOp

import os.path


class TextureWriter:

    def __init__(self, parent):
        self.nif_export = parent

    def export_source_texture(self, texture=None, filename=None):
        """Export a NiSourceTexture.

        :param texture: The texture object in blender to be exported.
        :param filename: The full or relative path to the texture file
            (this argument is used when exporting NiFlipControllers
            and when exporting default shader slots that have no use in
            being imported into Blender).
        :return: The exported NiSourceTexture block.
        """

        # create NiSourceTexture
        srctex = NifFormat.NiSourceTexture()
        srctex.use_external = True
        if filename is not None:
            # preset filename
            srctex.file_name = filename
        elif texture is not None:
            srctex.file_name = self.export_texture_filename(texture)
        else:
            # this probably should not happen
            NifLog.warn("Exporting source texture without texture or filename (bug?).")

        # fill in default values (TODO: can we use 6 for everything?)
        if bpy.context.scene.niftools_scene.nif_version >= 0x0A000100:
            srctex.pixel_layout = 6
        else:
            srctex.pixel_layout = 5
        srctex.use_mipmaps = 1
        srctex.alpha_format = 3
        srctex.unknown_byte = 1

        # search for duplicate
        for block in self.nif_export.nif_export.block_to_obj:
            if isinstance(block, NifFormat.NiSourceTexture) and block.get_hash() == srctex.get_hash():
                return block

        # no identical source texture found, so use and register
        # the new one
        return self.nif_export.nif_export.objecthelper.register_block(srctex, texture)

    def export_tex_desc(self, texdesc=None, uvlayers=None, b_mat_texslot=None):
        """Helper function for export_texturing_property to export each texture
        slot."""
        try:
            texdesc.uv_set = uvlayers.index(b_mat_texslot.uv_layer) if b_mat_texslot.uv_layer else 0
        except ValueError:  # mtex.uv_layer not in uvlayers list
            NifLog.warn("Bad uv layer name '{0}' in texture '{1}'. Using first uv layer".format(b_mat_texslot.uv_layer,
                                                                                                b_mat_texslot.texture.name))
            texdesc.uv_set = 0  # assume 0 is active layer

        texdesc.source = self.export_source_texture(b_mat_texslot.texture)

    def export_texture_filename(self, texture):
        """Returns file name from texture.

        @param texture: The texture object in blender.
        @return: The file name of the image used in the texture.
        """
        if texture.type == 'ENVIRONMENT_MAP':
            # this works for morrowind only
            if NifOp.props.game != 'MORROWIND':
                raise nif_utils.NifError(
                    "cannot export environment maps for nif version '%s'"
                    % NifOp.props.game)
            return "enviro 01.TGA"

        elif texture.type == 'IMAGE':
            # get filename from image

            # TODO [texture] still needed? can texture.image be None in current blender?
            # check that image is loaded
            if texture.image is None:
                raise nif_utils.NifError(
                    "image type texture has no file loaded ('%s')"
                    % texture.name)

            filename = texture.image.filepath

            # warn if packed flag is enabled
            if texture.image.packed_file:
                NifLog.warn(
                    "Packed image in texture '{0}' ignored, exporting as '{1}' instead.".format(texture.name, filename))

            # try and find a DDS alternative, force it if required
            ddsfilename = "%s%s" % (filename[:-4], '.dds')
            if os.path.exists(ddsfilename) or NifOp.props.force_dds:
                filename = ddsfilename

            # sanitize file path
            if NifOp.props.game not in ('MORROWIND', 'OBLIVION', 'FALLOUT_3', 'SKYRIM'):
                # strip texture file path
                filename = os.path.basename(filename)

            else:
                # strip the data files prefix from the texture's file name
                filename = filename.lower()
                idx = filename.find("textures")
                if idx >= 0:
                    filename = filename[idx:]
                else:
                    NifLog.warn("{0} does not reside in a 'Textures' folder; texture path will be stripped and textures may not display in-game".format(filename))
                    filename = os.path.basename(filename)
            # for linux export: fix path separators
            return filename.replace('/', '\\')

        else:
            # texture must be of type IMAGE or ENVMAP
            raise nif_utils.NifError("Error: Texture '{0}' must be of type IMAGE or ENVMAP".format(texture.name))


def has_diffuse_textures(self, b_mat):
    if self.b_mat == b_mat:
        return self.diffusetextures

    for b_mat_texslot in self.get_used_textslots(b_mat):
        if b_mat_texslot.use and b_mat_texslot.use_map_color_diffuse:
            self.diffusetextures.append(b_mat_texslot)
    return self.diffusetextures


def has_glow_textures(self, b_mat):
    if self.b_mat == b_mat:
        return self.glowtextures

    for b_mat_texslot in self.get_used_textslots(b_mat):
        if b_mat_texslot.use and b_mat_texslot.use_map_emit:
            self.glowtextures.append(b_mat_texslot)
    return self.glowtextures


def has_bumpmap_textures(self, b_mat):
    if self.b_mat == b_mat:
        return self.bumpmaptextures

    for b_mat_texslot in self.get_used_textslots(b_mat):
        if b_mat_texslot.use:
            if b_mat_texslot.texture.use_normal_map == False and \
                    b_mat_texslot.use_map_color_diffuse == False:
                self.bumpmaptextures.append(b_mat_texslot)
    return self.bumpmaptextures


def has_gloss_textures(self, b_mat):
    if self.b_mat == b_mat:
        return self.glosstextures

    for b_mat_texslot in self.get_used_textslots(b_mat):
        if b_mat_texslot.use and b_mat_texslot.use_map_color_spec:
            self.glosstextures.append(b_mat_texslot)
    return self.glosstextures


def has_normalmap_textures(self, b_mat):
    if self.b_mat == b_mat:
        return self.normalmaptextures

    for b_mat_texslot in self.get_used_textslots(b_mat):
        if b_mat_texslot.use:
            if b_mat_texslot.use_map_color_diffuse == False and \
                    b_mat_texslot.texture.use_normal_map and b_mat_texslot.use_map_normal:
                self.normalmaptextures.append(b_mat_texslot)
    return self.normalmaptextures
