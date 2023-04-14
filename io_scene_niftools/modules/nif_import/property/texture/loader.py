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
import os.path

import bpy
from pyffi.formats.dds import DdsFormat
from pyffi.formats.nif import NifFormat

from io_scene_niftools.modules.nif_import.property import texture
from io_scene_niftools.utils.singleton import NifOp
from io_scene_niftools.utils.logging import NifLog


# TODO once the save_dds PR code is merged into pyffi this section can be deleted.
# This section replaces pyffi methods to impliment functionality immediately.
#################
def get_pixeldata_stream_overide(self):
    if isinstance(self, NifFormat.NiPersistentSrcTextureRendererData):
        return ''.join(
            ''.join([chr(x) for x in tex])
            for tex in self.pixel_data)
    elif isinstance(self, NifFormat.NiPixelData):
        if self.pixel_data:
            # used in older nif versions
            return bytearray().join(
                bytearray().join([bytearray([x]) for x in tex])
                for tex in self.pixel_data)
        else:
            # used in newer nif versions
            return ''.join(self.pixel_data_matrix)
    else:
        raise ValueError(
            "cannot retrieve pixel data when saving pixel format %i as DDS")
def save_as_dds_override(self, stream):
    data = DdsFormat.Data()
    header = data.header
    pixeldata = data.pixeldata

    # create header, depending on the format
    if self.pixel_format in (NifFormat.PixelFormat.PX_FMT_RGB8,
                             NifFormat.PixelFormat.PX_FMT_RGBA8):
        # uncompressed RGB(A)
        header.flags.caps = 1
        header.flags.height = 1
        header.flags.width = 1
        header.flags.pixel_format = 1
        header.flags.mipmap_count = 1
        header.flags.linear_size = 1
        header.height = self.mipmaps[0].height
        header.width = self.mipmaps[0].width
        header.linear_size = len(self.pixel_data)
        header.mipmap_count = len(self.mipmaps)
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
                if channel.type == NifFormat.ChannelType.CHNL_RED:
                    header.pixel_format.r_mask = mask
                elif channel.type == NifFormat.ChannelType.CHNL_GREEN:
                    header.pixel_format.g_mask = mask
                elif channel.type == NifFormat.ChannelType.CHNL_BLUE:
                    header.pixel_format.b_mask = mask
                elif channel.type == NifFormat.ChannelType.CHNL_ALPHA:
                    header.pixel_format.a_mask = mask
                bit_pos += channel.bits_per_channel
        header.caps_1.complex = 1
        header.caps_1.texture = 1
        header.caps_1.mipmap = 1
        pixeldata.set_value(self.__get_pixeldata_stream())
    elif self.pixel_format == NifFormat.PixelFormat.PX_FMT_DXT1:
        # format used in Megami Tensei: Imagine and Bully SE
        header.flags.caps = 1
        header.flags.height = 1
        header.flags.width = 1
        header.flags.pixel_format = 1
        header.flags.mipmap_count = 1
        header.flags.linear_size = 0
        header.height = self.mipmaps[0].height
        header.width = self.mipmaps[0].width
        header.linear_size = 0
        header.mipmap_count = len(self.mipmaps)
        header.pixel_format.flags.four_c_c = 1
        header.pixel_format.four_c_c = DdsFormat.FourCC.DXT1
        header.pixel_format.bit_count = 0
        header.pixel_format.r_mask = 0
        header.pixel_format.g_mask = 0
        header.pixel_format.b_mask = 0
        header.pixel_format.a_mask = 0
        header.caps_1.complex = 1
        header.caps_1.texture = 1
        header.caps_1.mipmap = 1
        pixeldata.set_value(self.__get_pixeldata_stream())
    elif self.pixel_format in (NifFormat.PixelFormat.PX_FMT_DXT5,
                               NifFormat.PixelFormat.PX_FMT_DXT5_ALT):
        # format used in Megami Tensei: Imagine
        header.flags.caps = 1
        header.flags.height = 1
        header.flags.width = 1
        header.flags.pixel_format = 1
        header.flags.mipmap_count = 1
        header.flags.linear_size = 0
        header.height = self.mipmaps[0].height
        header.width = self.mipmaps[0].width
        header.linear_size = 0
        header.mipmap_count = len(self.mipmaps)
        header.pixel_format.flags.four_c_c = 1
        header.pixel_format.four_c_c = DdsFormat.FourCC.DXT5
        header.pixel_format.bit_count = 0
        header.pixel_format.r_mask = 0
        header.pixel_format.g_mask = 0
        header.pixel_format.b_mask = 0
        header.pixel_format.a_mask = 0
        header.caps_1.complex = 1
        header.caps_1.texture = 1
        header.caps_1.mipmap = 1
        pixeldata.set_value(self.__get_pixeldata_stream())
    else:
        raise ValueError(
            "cannot save pixel format %i as DDS" % self.pixel_format)

    data.write(stream)


NifFormat.ATextureRenderData.__get_pixeldata_stream = get_pixeldata_stream_overide
NifFormat.ATextureRenderData.save_as_dds = save_as_dds_override
#################


class TextureLoader:

    @staticmethod
    def load_image(tex_path):
        """Returns an image or a generated image if none was found"""
        name = os.path.basename(tex_path)
        if name not in bpy.data.images:
            b_image = bpy.data.images.new(name=name, width=1, height=1, alpha=True)
            b_image.filepath=tex_path
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

        if isinstance(source, NifFormat.NiSourceTexture) and not source.use_external and NifOp.props.use_embedded_texture:
            return self.import_embedded_texture_source(source)
        else:
            return self.import_external_source(source)

    def import_embedded_texture_source(self, source):

        fn, tex = self.generate_image_name()

        # save embedded texture as dds file
        with open(tex, "wb") as stream:
            try:
                NifLog.info(f"Saving embedded texture as {tex}")
                source.pixel_data.save_as_dds(stream)
            except ValueError:
                NifLog.warn(f"Pixel format not supported in embedded texture {tex}!")

        return self.load_image(tex)

    @staticmethod
    def generate_image_name():
        """Find a file name (but avoid overwriting)"""
        n = 0
        while n < 1000:
            fn = "image{:0>3d}.dds".format(n)
            tex = os.path.join(os.path.dirname(NifOp.props.filepath), fn)
            if not os.path.exists(tex):
                break
            n += 1
        return fn, tex

    def import_external_source(self, source):
        # the texture uses an external image file
        if isinstance(source, NifFormat.NiSourceTexture):
            fn = source.file_name.decode()
        elif isinstance(source, str):
            fn = source
        else:
            raise TypeError("source must be NiSourceTexture or str")

        fn = fn.replace('\\', os.sep)
        fn = fn.replace('/', os.sep)
        tex = fn
        # probably not found, but load a dummy regardless
        return self.load_image(tex)
