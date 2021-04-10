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


import bpy
from pyffi.formats.nif import NifFormat

from io_scene_niftools.modules.nif_export.animation.material import MaterialAnimation
from io_scene_niftools.modules.nif_export.block_registry import block_store
from io_scene_niftools.utils.singleton import NifOp
from io_scene_niftools.utils.logging import NifLog

EXPORT_OPTIMIZE_MATERIALS = True


class MaterialProp:

    def __init__(self):
        self.material_anim = MaterialAnimation()

    def export_material_property(self, b_mat, flags=0x0001):
        """Return existing material property with given settings, or create
        a new one if a material property with these settings is not found."""
        # don't export material properties for these games
        if bpy.context.scene.niftools_scene.game in ('SKYRIM', ):
            return
        name = block_store.get_full_name(b_mat)
        # create n_block
        n_mat_prop = NifFormat.NiMaterialProperty()

        # list which determines whether the material name is relevant or not  only for particular names this holds,
        # such as EnvMap2 by default, the material name does not affect rendering
        specialnames = ("EnvMap2", "EnvMap", "skin", "Hair", "dynalpha", "HideSecret", "Lava")

        # hack to preserve EnvMap2, skinm, ... named blocks (even if they got renamed to EnvMap2.xxx or skin.xxx on import)
        if bpy.context.scene.niftools_scene.game in ('OBLIVION', 'FALLOUT_3', 'SKYRIM'):
            for specialname in specialnames:
                if name.lower() == specialname.lower() or name.lower().startswith(specialname.lower() + "."):
                    if name != specialname:
                        NifLog.warn(f"Renaming material '{name}' to '{specialname}'")
                    name = specialname

        # clear noname materials
        if name.lower().startswith("noname"):
            NifLog.warn(f"Renaming material '{name}' to ''")
            name = ""

        n_mat_prop.name = name
        # TODO: - standard flag, check? material and texture properties in morrowind style nifs had a flag
        n_mat_prop.flags = flags
        ambient = b_mat.niftools.ambient_color
        n_mat_prop.ambient_color.r = ambient.r
        n_mat_prop.ambient_color.g = ambient.g
        n_mat_prop.ambient_color.b = ambient.b

        # todo [material] some colors in the b2.8 api allow rgb access, others don't - why??
        # diffuse mat
        n_mat_prop.diffuse_color.r, n_mat_prop.diffuse_color.g, n_mat_prop.diffuse_color.b, _ = b_mat.diffuse_color
        n_mat_prop.specular_color.r, n_mat_prop.specular_color.g, n_mat_prop.specular_color.b = b_mat.specular_color

        emissive = b_mat.niftools.emissive_color
        n_mat_prop.emissive_color.r = emissive.r
        n_mat_prop.emissive_color.g = emissive.g
        n_mat_prop.emissive_color.b = emissive.b

        # map roughness [0,1] to glossiness (MW -> 0.0 - 128.0)
        n_mat_prop.glossiness = min(1/b_mat.roughness - 1, 128) if b_mat.roughness != 0 else 128
        n_mat_prop.alpha = b_mat.niftools.emissive_alpha.v
        # todo [material] this float is used by FO3's material properties
        # n_mat_prop.emit_multi = emitmulti

        # search for duplicate
        # (ignore the name string as sometimes import needs to create different materials even when NiMaterialProperty is the same)
        for n_block in block_store.block_to_obj:
            if not isinstance(n_block, NifFormat.NiMaterialProperty):
                continue

            # when optimization is enabled, ignore material name
            if EXPORT_OPTIMIZE_MATERIALS:
                ignore_strings = not(n_block.name in specialnames)
            else:
                ignore_strings = False

            # check hash
            first_index = 1 if ignore_strings else 0
            if n_block.get_hash()[first_index:] == n_mat_prop.get_hash()[first_index:]:
                NifLog.warn(f"Merging materials '{n_mat_prop.name}' and '{n_block.name}' (they are identical in nif)")
                n_mat_prop = n_block
                break

        block_store.register_block(n_mat_prop)
        # material animation
        self.material_anim.export_material(b_mat, n_mat_prop)
        # no material property with given settings found, so use and register the new one
        return n_mat_prop
