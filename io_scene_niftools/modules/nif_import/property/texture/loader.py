"""This script contains helper methods for texture pathing."""

# ***** BEGIN LICENSE BLOCK *****
#
# Copyright © 2020, NIF File Format Library and Tools contributors.
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
from functools import reduce
import operator
import traceback
import os.path

import bpy
from pyffi.formats.dds import DdsFormat
from generated.formats.nif import classes as NifClasses

from io_scene_niftools.utils.singleton import NifOp
from io_scene_niftools.utils.logging import NifLog


# TODO once the save_dds PR code is merged into pyffi this section can be deleted.
# This section replaces pyffi methods to impliment functionality immediately.
#################
def get_pixeldata_stream_overide(self):
    if isinstance(self, NifClasses.NiPersistentSrcTextureRendererData):
        return ''.join(
            ''.join([chr(x) for x in tex])
            for tex in self.pixel_data)
    elif isinstance(self, NifClasses.NiPixelData):
        if self.pixel_data:
            # used in older nif versions
            return bytearray(x for tex in self.pixel_data for x in tex)
        else:
            # used in newer nif versions
            return ''.join(self.pixel_data_matrix)
    else:
        raise ValueError(f"cannot retrieve pixel data when saving pixel format {self.pixel_format} as DDS")


def save_as_dds_override(self, stream):
    data = DdsFormat.Data()
    header = data.header
    pixeldata = data.pixeldata

    header.flags.caps = 1
    header.flags.height = 1
    header.flags.width = 1
    header.flags.pixel_format = 1
    header.flags.mipmap_count = 1
    header.mipmap_count = len(self.mipmaps)
    header.height = self.mipmaps[0].height
    header.width = self.mipmaps[0].width
    header.caps_1.complex = 1
    header.caps_1.texture = 1
    header.caps_1.mipmap = 1
    # create header, depending on the format
    if self.pixel_format in (NifClasses.PixelFormat.PX_FMT_RGB8,
                             NifClasses.PixelFormat.PX_FMT_RGBA8):
        # uncompressed RGB(A)
        header.flags.linear_size = 1
        header.linear_size = len(self.pixel_data)
        header.pixel_format.flags.rgb = 1
        header.pixel_format.bit_count = self.bits_per_pixel
        if not self.channels:
            header.pixel_format.r_mask = self.red_mask
            header.pixel_format.g_mask = self.green_mask
            header.pixel_format.b_mask = self.blue_mask
            header.pixel_format.a_mask = self.alpha_mask
        else:
            bit_pos = 0
            for i, channel in enumerate(self.channels):
                mask = (2 ** channel.bits_per_channel - 1) << bit_pos
                if channel.type == NifClasses.ChannelType.CHNL_RED:
                    header.pixel_format.r_mask = mask
                elif channel.type == NifClasses.ChannelType.CHNL_GREEN:
                    header.pixel_format.g_mask = mask
                elif channel.type == NifClasses.ChannelType.CHNL_BLUE:
                    header.pixel_format.b_mask = mask
                elif channel.type == NifClasses.ChannelType.CHNL_ALPHA:
                    header.pixel_format.a_mask = mask
                bit_pos += channel.bits_per_channel
    elif self.pixel_format in (NifClasses.PixelFormat.PX_FMT_DXT1,
                               NifClasses.PixelFormat.PX_FMT_DXT5,
                               NifClasses.PixelFormat.PX_FMT_DXT5_ALT):
        # format used in Megami Tensei: Imagine and Bully SE

        header.flags.linear_size = 0
        header.linear_size = 0
        header.pixel_format.flags.four_c_c = 1
        if self.pixel_format in (NifClasses.PixelFormat.PX_FMT_DXT1,):
            header.pixel_format.four_c_c = DdsFormat.FourCC.DXT1
        if self.pixel_format in (NifClasses.PixelFormat.PX_FMT_DXT5,
                                 NifClasses.PixelFormat.PX_FMT_DXT5_ALT):
            header.pixel_format.four_c_c = DdsFormat.FourCC.DXT5
        header.pixel_format.bit_count = 0
        header.pixel_format.r_mask = 0
        header.pixel_format.g_mask = 0
        header.pixel_format.b_mask = 0
        header.pixel_format.a_mask = 0
    else:
        raise ValueError(f"cannot save pixel format {self.pixel_format} as DDS")

    # pyffi pixeldata can complain about a too long value for perfectly fine data
    pixeldata.set_value(b"")
    data.write(stream)
    # so just dump the bytes directly
    stream.write(self.__get_pixeldata_stream())


NifClasses.NiPixelFormat.__get_pixeldata_stream = get_pixeldata_stream_overide
NifClasses.NiPixelFormat.save_as_dds = save_as_dds_override
#################


class TextureLoader:

    external_textures = set()

    @staticmethod
    def load_image(tex_path):
        """Returns an image or a generated image if none was found"""
        name = os.path.basename(tex_path)
        if name not in bpy.data.images:
            try:
                b_image = bpy.data.images.load(tex_path)
            except:
                NifLog.warn(f"Texture '{name}' not found or not supported and no alternate available")
                b_image = bpy.data.images.new(name=name, width=1, height=1, alpha=True)
                b_image.filepath = tex_path
        else:
            b_image = bpy.data.images[name]
        return b_image

    def import_texture_source(self, source):
        """Convert a NiSourceTexture block, or simply a path string, to a Blender Texture object.
        :return Texture object
        """

        # if the source block is not linked then return None
        if not source:
            return None

        if isinstance(source, NifClasses.NiSourceTexture) and not source.use_external and NifOp.props.use_embedded_texture:
            return self.import_embedded_texture_source(source)
        else:
            return self.import_external_source(source)

    def import_embedded_texture_source(self, source):
        # first try to use the actual file name of this NiSourceTexture
        tex_name = source.file_name
        tex_path = os.path.join(os.path.dirname(NifOp.props.filepath), tex_name)
        # not set, then use generated sequence name
        if not tex_name:
            tex_path = self.generate_image_name()

        # only save them once per run, obviously only useful if file_name was set
        if tex_path not in self.external_textures:
            # save embedded texture as dds file
            with open(tex_path, "wb") as stream:
                try:
                    NifLog.info(f"Saving embedded texture as {tex_path}")
                    source.pixel_data.save_as_dds(stream)
                except ValueError:
                    NifLog.warn(f"Pixel format not supported in embedded texture {tex_path}!")
                    traceback.print_exc()
            self.external_textures.add(tex_path)

        return self.load_image(tex_path)

    @staticmethod
    def generate_image_name():
        """Find a file name (but avoid overwriting)"""
        n = 0
        while n < 10000:
            fn = f"image{n:0>4d}.dds"
            tex = os.path.join(os.path.dirname(NifOp.props.filepath), fn)
            if not os.path.exists(tex):
                break
            n += 1
        return tex

    def import_external_source(self, source):
        # the texture uses an external image file
        if isinstance(source, NifClasses.NiSourceTexture):
            fn = source.file_name
        elif isinstance(source, str):
            fn = source
        else:
            raise TypeError("source must be NiSourceTexture or str")

        fn = fn.replace('\\', os.sep)
        fn = fn.replace('/', os.sep)
        # go searching for it
        import_path = os.path.dirname(NifOp.props.filepath)
        search_path_list = [import_path]
        if bpy.context.preferences.filepaths.texture_directory:
            search_path_list.append(bpy.context.preferences.filepaths.texture_directory)

        # TODO [general][path] Implement full texture path finding.
        nif_dir = os.path.join(os.getcwd(), 'nif')
        search_path_list.append(nif_dir)

        # if it looks like a Morrowind style path, use common sense to guess texture path
        meshes_index = import_path.lower().find("meshes")
        if meshes_index != -1:
            search_path_list.append(import_path[:meshes_index] + 'textures')

        # if it looks like a Civilization IV style path, use common sense to guess texture path
        art_index = import_path.lower().find("art")
        if art_index != -1:
            search_path_list.append(import_path[:art_index] + 'shared')

        # go through all texture search paths
        for texdir in search_path_list:
            if texdir[0:2] == "//":
                # Blender-specific directory, slows down resolve_ncase:
                relative = True
                texdir = texdir[2:]
            else:
                relative = False
            texdir = texdir.replace('\\', os.sep)
            texdir = texdir.replace('/', os.sep)
            # go through all possible file names, try alternate extensions too; for linux, also try lower case versions of filenames
            texfns = reduce(operator.add,
                            [[fn[:-4] + ext, fn[:-4].lower() + ext]
                             for ext in ('.DDS', '.dds', '.PNG', '.png',
                                         '.TGA', '.tga', '.BMP', '.bmp',
                                         '.JPG', '.jpg')])

            texfns = [fn, fn.lower()] + list(set(texfns))
            for texfn in texfns:
                # now a little trick, to satisfy many Morrowind mods
                if texfn[:9].lower() == 'textures' + os.sep and texdir[-9:].lower() == os.sep + 'textures':
                    # strip one of the two 'textures' from the path
                    tex = os.path.join(texdir[:-9], texfn)
                else:
                    tex = os.path.join(texdir, texfn)

                # "ignore case" on linuxW
                if relative:
                    tex = bpy.path.abspath("//" + tex)
                tex = bpy.path.resolve_ncase(tex)
                NifLog.debug(f"Searching {tex}")
                if os.path.exists(tex):
                    if relative:
                        return self.load_image(bpy.path.relpath(tex))
                    else:
                        return self.load_image(tex)

        else:
            tex = fn
        # probably not found, but load a dummy regardless
        return self.load_image(tex)
