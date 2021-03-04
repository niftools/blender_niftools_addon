""" Nif User Interface, custom nif properties for shaders"""

# ***** BEGIN LICENSE BLOCK *****
# 
# Copyright © 2012, NIF File Format Library and Tools contributors.
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
from bpy.props import (PointerProperty,
                       BoolProperty,
                       EnumProperty,
                       )
from bpy.types import PropertyGroup

from pyffi.formats.nif import NifFormat

from io_scene_niftools.utils.decorators import register_classes, unregister_classes


class ShaderProps(PropertyGroup):

    bs_shadertype: EnumProperty(
        name='Shader Type',
        description='Type of property used to display meshes.',
        items=(
            ('None', 'None', "", 0),
            ('BSShaderProperty', 'BS Shader Property', "", 1),
            ('BSShaderPPLightingProperty', 'BS Shader PP Lighting Property', "", 2),
            ('BSLightingShaderProperty', 'BS Lighting Shader Property', "", 3),
            ('BSEffectShaderProperty', 'BS Effect Shader Property', "", 4)
        )
    )

    bsspplp_shaderobjtype: EnumProperty(
        name='BS Shader PP Lighting Object Type',
        description='Type of object linked to shader',
        items=[(item, item, "", i) for i, item in enumerate(NifFormat.BSShaderType._enumkeys)],
        default='SHADER_DEFAULT'
    )

    bslsp_shaderobjtype: EnumProperty(
        name='BS Lighting Shader Object Type',
        description='Type of object linked to shader',
        items=[(item, item, "", i) for i, item in enumerate(NifFormat.BSLightingShaderPropertyShaderType._enumkeys)],
        # default = 'SHADER_DEFAULT'
    )

    sf_specular: BoolProperty(
        name='Specular'
    )

    sf_skinned: BoolProperty(
        name='Skinned'
    )

    sf_low_detail: BoolProperty(
        name='Low Detail'
    )

    sf_vertex_alpha: BoolProperty(
        name='Vertex Alpha'
    )

    sf_unknown_1: BoolProperty(
        name='Unknown 1'
    )

    sf_single_pass: BoolProperty(
        name='Single Pass'
    )

    sf_empty: BoolProperty(
        name='Empty'
    )

    sf_environment_mapping: BoolProperty(
        name='Environment Mapping'
    )

    sf_alpha_texture: BoolProperty(
        name='Alpha Texture'
    )

    sf_unknown_2: BoolProperty(
        name='Unknown 2'
    )

    sf_face_gen: BoolProperty(
        name='Face Gen'
    )

    sf_parallax_shader_index_15: BoolProperty(
        name='Parallax Shader Index'
    )

    sf_unknown_3: BoolProperty(
        name='Unknown 3'
    )

    sf_non_projective_shadows: BoolProperty(
        name='Non-Projective Shadows'
    )

    sf_unknown_4: BoolProperty(
        name='Unknown 4'
    )

    sf_refraction: BoolProperty(
        name='Refraction'
    )

    sf_fire_refraction: BoolProperty(
        name='Fire Refraction'
    )

    sf_eye_environment_mapping: BoolProperty(
        name='Eye Environment Mapping'
    )

    sf_hair: BoolProperty(
        name='Hair'
    )

    sf_dynamic_alpha: BoolProperty(
        name='Dynamic Alpha'
    )

    sf_localmap_hide_secret: BoolProperty(
        name='Local Map Hide Secret'
    )

    sf_window_environment_mapping: BoolProperty(
        name='Window Environment Mapping'
    )

    sf_tree_billboard: BoolProperty(
        name='Tree Billboard'
    )

    sf_shadow_frustum: BoolProperty(
        name='Shadow Frustum'
    )

    sf_multiple_textures: BoolProperty(
        name='Multiple Textures'
    )

    sf_remappable_textures: BoolProperty(
        name='Remappable Textures'
    )

    sf_decal_single_pass: BoolProperty(
        name='Decal Single Pass'
    )

    sf_dynamic_decal_single_pass: BoolProperty(
        name='Dynamic Decal Single Pass'
    )

    sf_parallax_occulsion: BoolProperty(
        name='Parallax Occlusion'
    )

    sf_external_emittance: BoolProperty(
        name='External Emittance'
    )

    sf_shadow_map: BoolProperty(
        name='Shadow Map'
    )

    sf_z_buffer_test: BoolProperty(
        name='Z Buffer Test'
    )

    slsf_1_specular: BoolProperty(
        name='Specular'
    )

    slsf_1_skinned: BoolProperty(
        name='Skinned'
    )

    slsf_1_temp_refraction: BoolProperty(
        name='Temp Refraction'
    )

    slsf_1_vertex_alpha: BoolProperty(
        name='Vertex Alpha'
    )

    slsf_1_greyscale_to_palettecolor: BoolProperty(
        name='Greyscale to Palette Color'
    )

    slsf_1_greyscale_to_palettealpha: BoolProperty(
        name='Greyscale to Palette Alpha'
    )

    slsf_1_use_falloff: BoolProperty(
        name='Use Falloff'
    )

    slsf_1_environment_mapping: BoolProperty(
        name='Environment Mapping'
    )

    slsf_1_recieve_shadows: BoolProperty(
        name='Receive Shadows'
    )

    slsf_1_cast_shadows: BoolProperty(
        name='Cast Shadows'
    )

    slsf_1_facegen_detail: BoolProperty(
        name='Facegen Detail'
    )

    slsf_1_Parallax: BoolProperty(
        name='Parallax'
    )

    slsf_1_model_space_normals: BoolProperty(
        name='Model Space Normals'
    )

    slsf_1_non_projective_shadows: BoolProperty(
        name='Non Projective Shadows'
    )

    slsf_1_Landscape: BoolProperty(
        name='Landscape'
    )

    slsf_1_refraction: BoolProperty(
        name='Refraction'
    )

    slsf_1_fire_refraction: BoolProperty(
        name='Fire Refraction'
    )

    slsf_1_eye_environment_mapping: BoolProperty(
        name='Eye Environment Mapping'
    )

    slsf_1_hair_soft_lighting: BoolProperty(
        name='Hair Soft Lighting'
    )

    slsf_1_screendoor_alpha_fade: BoolProperty(
        name='Screendoor Alpha Fade'
    )

    slsf_1_localmap_hide_secret: BoolProperty(
        name='Localmap Hide Secret'
    )

    slsf_1_facegen_rgb_tint: BoolProperty(
        name='Facegen RGB Tint'
    )

    slsf_1_own_emit: BoolProperty(
        name='Own Emit'
    )

    slsf_1_projected_uv: BoolProperty(
        name='Projected UV'
    )

    slsf_1_multiple_textures: BoolProperty(
        name='Multiple Textures'
    )

    slsf_1_remappable_textures: BoolProperty(
        name='Remappable Textures'
    )

    slsf_1_decal: BoolProperty(
        name='Decal'
    )

    slsf_1_dynamic_decal: BoolProperty(
        name='Dynamic Decal'
    )

    slsf_1_parallax_occlusion: BoolProperty(
        name='Parallax Occlusion'
    )

    slsf_1_external_emittance: BoolProperty(
        name='External Emittance'
    )

    slsf_1_soft_effect: BoolProperty(
        name='Soft Effect'
    )

    slsf_1_z_buffer_test: BoolProperty(
        name='ZBuffer Test'
    )

    slsf_2_z_buffer_write: BoolProperty(
        name='ZBuffer Write'
    )

    slsf_2_lod_landscape: BoolProperty(
        name='LOD Landscape'
    )

    slsf_2_lod_objects: BoolProperty(
        name='LOD Objects'
    )

    slsf_2_no_fade: BoolProperty(
        name='No Fade'
    )

    slsf_2_double_sided: BoolProperty(
        name='Double Sided'
    )

    slsf_2_vertex_colors: BoolProperty(
        name='Vertex Colors'
    )

    slsf_2_glow_map: BoolProperty(
        name='Glow Map'
    )

    slsf_2_assume_shadowmask: BoolProperty(
        name='Assume Shadowmask'
    )

    slsf_2_packed_tangent: BoolProperty(
        name='Packed Tangent'
    )

    slsf_2_multi_index_snow: BoolProperty(
        name='Multi Index Snow'
    )

    slsf_2_vertex_lighting: BoolProperty(
        name='Vertex Lighting'
    )

    slsf_2_uniform_scale: BoolProperty(
        name='Uniform Scale'
    )

    slsf_2_fit_slope: BoolProperty(
        name='Fit Slope'
    )

    slsf_2_billboard: BoolProperty(
        name='Billboard'
    )

    slsf_2_no_lod_land_blend: BoolProperty(
        name='No LOD Land Blend'
    )

    slsf_2_env_map_light_fade: BoolProperty(
        name='Envmap Light Fade'
    )

    slsf_2_wireframe: BoolProperty(
        name='Wireframe'
    )

    slsf_2_weapon_blood: BoolProperty(
        name='Weapon Blood'
    )

    slsf_2_hide_on_local_map: BoolProperty(
        name='Hide On Local Map'
    )

    slsf_2_premult_alpha: BoolProperty(
        name='Premult Alpha'
    )

    slsf_2_cloud_lod: BoolProperty(
        name='Cloud Lod'
    )

    slsf_2_anisotropic_lighting: BoolProperty(
        name='Anisotropic Lighting'
    )

    slsf_2_no_transparency_multisampling: BoolProperty(
        name='No Transparency Multisampling'
    )

    slsf_2_unused01: BoolProperty(
        name='Unused01'
    )

    slsf_2_multi_layer_parallax: BoolProperty(
        name='Multi Layer Parallax'
    )

    slsf_2_soft_lighting: BoolProperty(
        name='Soft Lighting'
    )

    slsf_2_rim_lighting: BoolProperty(
        name='Rim Lighting'
    )

    slsf_2_back_lighting: BoolProperty(
        name='Back Lighting'
    )

    slsf_2_unused02: BoolProperty(
        name='Unused02'
    )

    slsf_2_tree_anim: BoolProperty(
        name='Tree Anim'
    )

    slsf_2_effect_lighting: BoolProperty(
        name='Effect Lighting'
    )

    slsf_2_hd_lod_objects: BoolProperty(
        name='HD LOD Objects'
    )


CLASSES = [
    ShaderProps
]


def register():
    register_classes(CLASSES, __name__)

    bpy.types.Material.niftools_shader = bpy.props.PointerProperty(type=ShaderProps)


def unregister():
    del bpy.types.Material.niftools_shader

    unregister_classes(CLASSES, __name__)
