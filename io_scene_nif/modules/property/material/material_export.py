"""This script contains helper methods to export materials."""

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


from pyffi.formats.nif import NifFormat

from io_scene_nif.modules.object.block_registry import block_store
from io_scene_nif.utility.util_global import NifOp
from io_scene_nif.utility.util_logging import NifLog


class MaterialProp:
    
    def __init__(self, parent):
        self.nif_export = parent
        
    def export_material_property(self, name, flags, ambient, diffuse, specular, emissive, gloss, alpha, emitmulti):
        """Return existing material property with given settings, or create
        a new one if a material property with these settings is not found."""

        # create n_block
        matprop = NifFormat.NiMaterialProperty()

        # list which determines whether the material name is relevant or not  only for particular names this holds,
        # such as EnvMap2 by default, the material name does not affect rendering
        specialnames = ("EnvMap2", "EnvMap", "skin", "Hair",
                        "dynalpha", "HideSecret", "Lava")

        # hack to preserve EnvMap2, skinm, ... named blocks (even if they got renamed to EnvMap2.xxx or skin.xxx on import)
        if NifOp.props.game in ('OBLIVION', 'FALLOUT_3', 'SKYRIM'):
            for specialname in specialnames:
                if name.lower() == specialname.lower() or name.lower().startswith(specialname.lower() + "."):
                    if name != specialname:
                        NifLog.warn("Renaming material '{0}' to '{1}'".format(name, specialname))
                    name = specialname

        # clear noname materials
        if name.lower().startswith("noname"):
            NifLog.warn("Renaming material '{0}' to ''".format(name))
            name = ""

        matprop.name = name
        matprop.flags = flags
        matprop.ambient_color.r = ambient.r
        matprop.ambient_color.g = ambient.g
        matprop.ambient_color.b = ambient.b
        
        matprop.diffuse_color.r = diffuse.r
        matprop.diffuse_color.g = diffuse.g
        matprop.diffuse_color.b = diffuse.b
        
        matprop.specular_color.r = specular.r
        matprop.specular_color.g = specular.g
        matprop.specular_color.b = specular.b
        
        matprop.emissive_color.r = emissive.r
        matprop.emissive_color.g = emissive.g
        matprop.emissive_color.b = emissive.b
        matprop.glossiness = gloss
        matprop.alpha = alpha
        matprop.emit_multi = emitmulti

        # search for duplicate
        # (ignore the name string as sometimes import needs to create different materials even when NiMaterialProperty is the same)
        for n_block in block_store.block_to_obj:
            if not isinstance(n_block, NifFormat.NiMaterialProperty):
                continue

            # when optimization is enabled, ignore material name
            if self.nif_export.EXPORT_OPTIMIZE_MATERIALS:
                ignore_strings = not(n_block.name in specialnames)
            else:
                ignore_strings = False

            # check hash
            first_index = 1 if ignore_strings else 0
            if n_block.get_hash()[first_index:] == matprop.get_hash()[first_index:]:
                NifLog.warn("Merging materials '{0}' and '{1}' (they are identical in nif)".format(matprop.name, n_block.name))
                return n_block

        # no material property with given settings found, so use and register the new one
        return matprop
