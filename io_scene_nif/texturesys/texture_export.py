"""This script contains helper methods to export textures."""

# ***** BEGIN LICENSE BLOCK *****
# 
# Copyright © 2005-2013, NIF File Format Library and Tools contributors.
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

from pyffi.formats.nif import NifFormat

import io_scene_nif.utility.nif_utils

import os.path

class Texture():
    
    # dictionary of texture files, to reuse textures
    textures = {}

    def __init__(self, parent):
        self.nif_common = parent
        self.properties = parent.properties
        
    def export_texture_filename(self, texture):
        """Returns file name from texture.

        @param texture: The texture object in blender.
        @return: The file name of the image used in the texture.
        """
        if texture.type == 'ENVIRONMENT_MAP':
            # this works for morrowind only
            if self.properties.game != 'MORROWIND':
                raise nif_utils.NifExportError(
                    "cannot export environment maps for nif version '%s'"
                    %self.properties.game)
            return "enviro 01.TGA"
        elif texture.type == 'IMAGE':
            # get filename from image

            # XXX still needed? can texture.image be None in current blender?
            # check that image is loaded
            if texture.image is None:
                raise nif_utils.NifExportError(
                    "image type texture has no file loaded ('%s')"
                    % texture.name)

            filename = texture.image.filepath

            # warn if packed flag is enabled
            if texture.image.packed_file:
                self.nif_export.warning(
                    "Packed image in texture '%s' ignored, "
                    "exporting as '%s' instead."
                    % (texture.name, filename))

            # try and find a DDS alternative, force it if required
            ddsfilename = "%s%s" % (filename[:-4], '.dds')
            if os.path.exists(ddsfilename) or self.properties.force_dds:
                filename = ddsfilename

            # sanitize file path
            if not self.properties.game in ('MORROWIND', 'OBLIVION',
                                           'FALLOUT_3'):
                # strip texture file path
                filename = os.path.basename(filename)
            else:
                # strip the data files prefix from the texture's file name
                filename = filename.lower()
                idx = filename.find("textures")
                if ( idx >= 0 ):
                    filename = filename[idx:]
                else:
                    self.nif_export.warning(
                        "%s does not reside in a 'Textures' folder;"
                        " texture path will be stripped"
                        " and textures may not display in-game" % filename)
                    filename = os.path.basename(filename)
            # for linux export: fix path seperators
            return filename.replace('/', '\\')
        else:
            # texture must be of type IMAGE or ENVMAP
            raise nif_utils.NifExportError(
                "Error: Texture '%s' must be of type IMAGE or ENVMAP"
                % texture.name)
            

