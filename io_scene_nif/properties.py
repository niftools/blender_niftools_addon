'''Nif Properties, adds custom properties via Blender types''' 

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

import bpy
from bpy.props import (PointerProperty,
                       CollectionProperty,
                       FloatVectorProperty,
                       FloatProperty,
                       StringProperty,
                       IntProperty,
                       BoolProperty,
                       EnumProperty,
                       )

from pyffi.formats.nif import NifFormat

def underscore_to_camelcase(s):
    """Take the underscore-separated string s and return a camelCase
    equivalent.  Initial and final underscores are preserved, and medial
    pairs of underscores are turned into a single underscore."""
    def camelcase_words(words):
        first_word_passed = False
        for word in words:
            
            if not word:
                yield "_"
                continue
            if first_word_passed:
                yield word.capitalize()
            else:
                yield word.lower()
            first_word_passed = True
    return ''.join(camelcase_words(s.split('_')))



class NiftoolsMatFlagProps(bpy.types.PropertyGroup):
    '''Adds custom properties to material'''
    
    @classmethod
    def register(cls):
        bpy.types.Material.niftools_alpha = PointerProperty(
                        name='Niftools Material Alpha',
                        description = 'Additional material properties used by the Nif File Format',
                        type=cls,
                        )
        
        cls.alphaflag = IntProperty(
                        name = 'Alpha Flag',
                        default = 0
                        )
        
        cls.textureflag = IntProperty(
                        name = 'Texture Flag',
                        default = 0
                        )

        cls.materialflag = IntProperty(
                        name = 'Material Flag',
                        default = 0
                        )
        
    @classmethod
    def unregister(cls):
        del bpy.types.Material.niftools_alpha

class NiftoolsMaterialProps(bpy.types.PropertyGroup):
    '''Adds custom properties to material'''
    
    @classmethod
    def register(cls):
        bpy.types.Material.niftools = PointerProperty(
                        name='Niftools Materials',
                        description = 'Additional material properties used by the Nif File Format',
                        type=cls,
                        )

        cls.ambient_preview = BoolProperty(
                name='Ambient Preview', description='Allows a viewport preview of the ambient property', default=False)
        
        cls.ambient_color = FloatVectorProperty(
                name='Ambient', subtype='COLOR', default=[1.0,1.0,1.0],min=0.0, max=1.0)
        
        cls.emissive_preview = BoolProperty(
                name='Emissive Preview', description='Allows a viewport preview of the emissive property', default=False)
        
        cls.emissive_color = FloatVectorProperty(
                name='Emissive', subtype='COLOR', default=[0.0,0.0,0.0],min=0.0, max=1.0)
    
    @classmethod
    def unregister(cls):
        del bpy.types.Material.niftools


class NiftoolsBoneProps(bpy.types.PropertyGroup):
    @classmethod
    def register(cls):
        bpy.types.Bone.niftools_bone = PointerProperty(
                        name='Niftools Bone Property',
                        description = 'Additional bone properties used by the Nif File Format',
                        type = cls,
                        )
        cls.boneflags = IntProperty(
                        name = 'Bone Flag',
                        default = 0
                        )
        
    @classmethod
    def unregister(cls):
        del bpy.types.Bone.niftools_bone


class NiftoolsShaderProps(bpy.types.PropertyGroup):
    @classmethod
    def register(cls):
        bpy.types.Object.niftools_shader = PointerProperty(
                        name='Niftools BsShader Property',
                        description = 'Properties used by the BsShader for the Nif File Format',
                        type = cls,
                        )
        
        cls.bs_shadertype = EnumProperty(
                        name='Shader Type',
                        description = 'Type of property used to display meshes.',
                        items = (('None','None',"",0),
                                 ('BSShaderProperty', 'BS Shader Property',"", 1),
                                 ('BSShaderPPLightingProperty', 'BS Shader PP Lighting Property',"", 2),
                                 ('BSLightingShaderProperty', 'BS Lighting Shader Property', "", 3)),
                        )

        cls.bsspplp_shaderobjtype = EnumProperty(
                        name='BS Shader PP Lighting Object Type',
                        description = 'Type of object linked to shader',
                        items = [(item, item,"", i) for i, item in enumerate(NifFormat.BSShaderType._enumkeys)],
                        default = 'SHADER_DEFAULT'
                        )

        cls.bslsp_shaderobjtype = EnumProperty(
                        name='BS Lighting Shader Object Type',
                        description = 'Type of object linked to shader',
                        items = [(item, item,"", i) for i, item in enumerate(NifFormat.BSLightingShaderPropertyShaderType._enumkeys)],
                        #default = 'SHADER_DEFAULT'
                        )

        
        cls.sf_specular = BoolProperty(
                        name = 'Specular'
                        )
        
        cls.sf_skinned = BoolProperty(
                        name = 'Skinned'
                        )
        
        cls.sf_low_detail = BoolProperty(
                        name = 'Low Detail'
                        )
        
        cls.sf_vertex_alpha = BoolProperty(
                        name = 'Vertex Alpha'
                        )
        
        cls.sf_unknown_1 = BoolProperty(
                        name = 'Unknown 1'
                        )
        
        cls.sf_single_pass = BoolProperty(
                        name = 'Single Pass'
                        )
        
        cls.sf_empty = BoolProperty(
                        name = 'Empty'
                        )
        
        cls.sf_environment_mapping = BoolProperty(
                        name = 'Environment Mapping'
                        )
        
        cls.sf_alpha_texture = BoolProperty(
                        name = 'Alpha Texture'
                        )
        
        cls.sf_unknown_2 = BoolProperty(
                        name = 'Unknown 2'
                        )
        
        cls.sf_face_gen = BoolProperty(
                        name = 'Face Gen'
                        )
        
        cls.sf_parallax_shader_index_15 = BoolProperty(
                        name = 'Parallax Shader Index'
                        )
        
        cls.sf_unknown_3 = BoolProperty(
                        name = 'Unknown 3'
                        )
        
        cls.sf_non_projective_shadows = BoolProperty(
                        name = 'Non-Projective Shadows'
                        )
        
        cls.sf_unknown_4 = BoolProperty(
                        name = 'Unknown 4'
                        )
        
        cls.sf_refraction = BoolProperty(
                        name = 'Refraction'
                        )
        
        cls.sf_fire_refraction = BoolProperty(
                        name = 'Fire Refraction'
                        )
        
        cls.sf_eye_environment_mapping = BoolProperty(
                        name = 'Eye Environment Mapping'
                        )
        
        cls.sf_hair = BoolProperty(
                        name = 'Hair'
                        )
        
        cls.sf_dynamic_alpha = BoolProperty(
                        name = 'Dynamic Alpha'
                        )
        
        cls.sf_localmap_hide_secret = BoolProperty(
                        name = 'Local Map Hide Secret'
                        )
        
        cls.sf_window_environment_mapping = BoolProperty(
                        name = 'Window Environment Mapping'
                        )
        
        cls.sf_tree_billboard = BoolProperty(
                        name = 'Tree Billboard'
                        )
        
        cls.sf_shadow_frustum = BoolProperty(
                        name = 'Shadow Frustum'
                        )
        
        cls.sf_multiple_textures = BoolProperty(
                        name = 'Multiple Textures'
                        )
        
        cls.sf_remappable_textures = BoolProperty(
                        name = 'Remappable Textures'
                        )
        
        cls.sf_decal_single_pass = BoolProperty(
                        name = 'Decal Single Pass'
                        )
        
        cls.sf_dynamic_decal_single_pass = BoolProperty(
                        name = 'Dynamic Decal Single Pass'
                        )
        
        cls.sf_parallax_occulsion = BoolProperty(
                        name = 'Parallax Occlusion'
                        )
        
        cls.sf_external_emittance = BoolProperty(
                        name = 'External Emittance'
                        )
        
        cls.sf_shadow_map = BoolProperty(
                        name = 'Shadow Map'
                        )
        
        cls.sf_z_buffer_test = BoolProperty(
                        name = 'Z Buffer Test'
                        )
        
        cls.slsf_1_specular = BoolProperty(
                        name = 'Specular'
                        )

        cls.slsf_1_skinned = BoolProperty(
                        name = 'Skinned'
                        )
        
        cls.slsf_1_temp_refraction = BoolProperty(
                        name = 'Temp Refraction'
                        )
        
        cls.slsf_1_vertex_alpha = BoolProperty(
                        name = 'Vertex Alpha'
                        )
        
        cls.slsf_1_greyscale_to_paletteColor = BoolProperty(
                        name = 'Greyscale to Palette Color'
                        )
        
        cls.slsf_1_greyscale_to_palettealpha = BoolProperty(
                        name = 'Greyscale to Palette Alpha'
                        )
        
        cls.slsf_1_use_falloff = BoolProperty(
                        name = 'Use Falloff'
                        )
        
        cls.slsf_1_enviroment_mapping = BoolProperty(
                        name = 'Enviroment Mapping'
                        )
        
        cls.slsf_1_recieve_shadows = BoolProperty(
                        name = 'Receive Shadows'
                        )
        
        cls.slsf_1_cast_shadows = BoolProperty(
                        name = 'Cast Shadows'
                        )
        
        cls.slsf_1_facegen_detail = BoolProperty(
                        name = 'Facegen Detail'
                        )
        
        cls.slsf_1_Parallax = BoolProperty(
                        name = 'Parallax'
                        )
        
        cls.slsf_1_model_space_normals = BoolProperty(
                        name = 'Model Space Normals'
                        )
        
        cls.slsf_1_non_projective_shadows = BoolProperty(
                        name = 'Non Projective Shadows'
                        )
        
        cls.slsf_1_Landscape = BoolProperty(
                        name = 'Landscape'
                        )
        
        cls.slsf_1_refraction = BoolProperty(
                        name = 'Refraction'
                        )
        
        cls.slsf_1_fire_refraction = BoolProperty(
                        name = 'Fire Refraction'
                        )
        
        cls.slsf_1_eye_environment_mapping = BoolProperty(
                        name = 'Eye Environment Mapping'
                        )
        
        cls.slsf_1_hair_soft_lighting = BoolProperty(
                        name = 'Hair Soft Lighting'
                        )
        
        cls.slsf_1_screendoor_alpha_fade = BoolProperty(
                        name = 'Screendoor Alpha Fade'
                        )
        
        cls.slsf_1_localmap_hide_secret = BoolProperty(
                        name = 'Localmap Hide Secret'
                        )
        
        cls.slsf_1_facegen_rgb_tint = BoolProperty(
                        name = 'Facegen RGB Tint'
                        )
        
        cls.slsf_1_own_emit = BoolProperty(
                        name = 'Own Emit'
                        )
        
        cls.slsf_1_projected_uv = BoolProperty(
                        name = 'Projected UV'
                        )
        
        cls.slsf_1_multiple_textures = BoolProperty(
                        name = 'Multiple Textures'
                        )

        cls.slsf_1_remappable_textures = BoolProperty(
                        name = 'Remappable Textures'
                        )
        
        cls.slsf_1_decal = BoolProperty(
                        name = 'decal'
                        )
        
        cls.slsf_1_dynamic_decal = BoolProperty(
                        name = 'Dynamic Decal'
                        )
        
        cls.slsf_1_parallax_occlusion = BoolProperty(
                        name = 'Parallax Occlusion'
                        )
        
        cls.slsf_1_external_emittance = BoolProperty(
                        name = 'External Emittance'
                        )
        
        cls.slsf_1_soft_effect = BoolProperty(
                        name = 'Soft Effect'
                        )
        
        cls.slsf_1_z_buffer_test = BoolProperty(
                        name = 'ZBuffer Test'
                        )
        
        cls.slsf_2_z_buffer_write = BoolProperty(
                        name = 'ZBuffer Write'
                        )
        
        cls.slsf_2_lod_landscape = BoolProperty(
                        name = 'LOD Landscape'
                        )
        
        cls.slsf_2_lod_objects = BoolProperty(
                        name = 'LOD Objects'
                        )
        
        cls.slsf_2_no_fade = BoolProperty(
                        name = 'No Fade'
                        )
        
        cls.slsf_2_double_sided = BoolProperty(
                        name = 'Double Sided'
                        )
        
        cls.slsf_2_vertex_colors = BoolProperty(
                        name = 'Vertex Colors'
                        )
        
        cls.slsf_2_glow_map = BoolProperty(
                        name = 'Glow Map'
                        )
        
        cls.slsf_2_assume_shadowmask = BoolProperty(
                        name = 'Assume Shadowmask'
                        )
        
        cls.slsf_2_packed_tangent = BoolProperty(
                        name = 'Packed Tangent'
                        )
        
        cls.slsf_2_multi_index_snow = BoolProperty(
                        name = 'Multi Index Snow'
                        )
        
        cls.slsf_2_vertex_lighting = BoolProperty(
                        name = 'Vertex Lighting'
                        )
        
        cls.slsf_2_uniform_scale = BoolProperty(
                        name = 'Uniform Scale'
                        )
        
        cls.slsf_2_fit_slope = BoolProperty(
                        name = 'Fit Slope'
                        )
        
        cls.slsf_2_billboard = BoolProperty(
                        name = 'Billboard'
                        )
        
        cls.slsf_2_no_lod_land_blend = BoolProperty(
                        name = 'No LOD Land Blend'
                        )
        
        cls.slsf_2_env_map_light_fade = BoolProperty(
                        name = 'Envmap Light Fade'
                        )
        
        cls.slsf_2_wireframe = BoolProperty(
                        name = 'Wireframe'
                        )
        
        cls.slsf_2_weapon_blood = BoolProperty(
                        name = 'Weapon Blood'
                        )
        
        cls.slsf_2_hide_on_local_map = BoolProperty(
                        name = 'Hide On Local Map'
                        )
        
        cls.slsf_2_premult_alpha = BoolProperty(
                        name = 'Premult Alpha'
                        )
        
        cls.slsf_2_cloud_lod = BoolProperty(
                        name = 'Cloud Lod'
                        )
        
        cls.slsf_2_anisotropic_lighting = BoolProperty(
                        name = 'Anisotropic Lighting'
                        )
        
        cls.slsf_2_no_transparency_multisampling = BoolProperty(
                        name = 'No Transparency Multisampling'
                        )
        
        cls.slsf_2_unused01 = BoolProperty(
                        name = 'Unused01'
                        )
        
        cls.slsf_2_multi_layer_parallax = BoolProperty(
                        name = 'Multi Layer Parallax'
                        )
        
        cls.slsf_2_soft_lighting = BoolProperty(
                        name = 'Soft Lighting'
                        )
        
        cls.slsf_2_rim_lighting = BoolProperty(
                        name = 'Rim Lighting'
                        )
        
        cls.slsf_2_back_lighting = BoolProperty(
                        name = 'Back Lighting'
                        )
        
        cls.slsf_2_unused02 = BoolProperty(
                        name = 'Unused02'
                        )
        
        cls.slsf_2_tree_anim = BoolProperty(
                        name = 'Tree Anim'
                        )
        
        cls.slsf_2_effect_lighting = BoolProperty(
                        name = 'Effect Lighting'
                        )
        
        cls.slsf_2_hd_lod_objects = BoolProperty(
                        name = 'HD LOD Objects'
                        )
        
    @classmethod
    def unregister(cls):
        del bpy.types.Object.niftools_shader

class NiftoolsSkinPartFlagsPanel(bpy.types.PropertyGroup):
    @classmethod
    def register(cls):
        bpy.types.Object.niftools_part_flags_panel = PointerProperty(
                        name='Niftools Skin Part Flag Panel',
                        description = 'Properties used by the BsShader for the Nif File Format',
                        type = cls,
                        )

        cls.pf_partcount = IntProperty(
                        name = 'Partition count',
                        min = 0,
                        default = 0
                        )
        
    @classmethod
    def unregister(cls):
        del bpy.types.Object.niftools_part_flags_panel

class NiftoolsSkinPartFlags(bpy.types.PropertyGroup):
    
    name  = bpy.props.StringProperty(
                    name = (''),
                    default = ''
                    )

    pf_startflag = bpy.props.BoolProperty(
                    name = ('Start Net Boneset')
                    )
        
    pf_editorflag = bpy.props.BoolProperty(
                    name = ('Editor Visible')
                    )

bpy.utils.register_class(NiftoolsSkinPartFlags)
    
bpy.types.Object.niftools_part_flags = \
        CollectionProperty(type=NiftoolsSkinPartFlags)


class NiftoolsObjectProps(bpy.types.PropertyGroup):
    @classmethod
    def register(cls):
        bpy.types.Object.niftools = PointerProperty(
                        name='Niftools Object Property',
                        description = 'Additional object properties used by the Nif File Format',
                        type = cls,
                        )
        
        cls.nif_version = StringProperty(
                        name = 'Nif Version',
                        )
        
        cls.user_version = IntProperty(
                        name = 'User Version',
                        default = 0
                        )
        
        cls.user_version_2 = IntProperty(
                        name = 'User Version 2',
                        default = 0
                        )
        
        cls.rootnode = EnumProperty(
                        name = 'Nif Root Node',
                        description = 'Type of property used to display meshes.',
                        items = (('NiNode', 'NiNode',"", 0),
                                ('BSFadeNode', 'BSFadeNode',"", 1)),
                        default = 'NiNode',
                        )
        
        cls.bsnumuvset = IntProperty(
                        name = 'BS Num UV Set',
                        default = 0
                        )
        
        cls.longname = StringProperty(
                        name = 'Nif LongName'
                        )

        cls.consistency_flags = EnumProperty(
                        name = 'Consistency Flag',
                        description = 'Controls animation type',
                        items = [(item, item,"", i) for i, item in enumerate(NifFormat.ConsistencyType._enumkeys)],
                        #default = 'SHADER_DEFAULT'
                        )

        cls.objectflags = IntProperty(
                        name = 'Object Flag',
                        description = 'Controls animation and collision',
                        default = 0
                        )

        cls.bsxflags = IntProperty(
                        name = 'BSXFlags',
                        description = 'Controls animation and collision',
                        default = 0 # 2 = Bit 1, enable collision
                        )

        cls.upb = StringProperty(
                        name = 'UPB',
                        description = 'Commands for an optimizer?',
                        default = ''
                        )

        
    @classmethod
    def unregister(cls):
        del bpy.types.Object.niftools   


class NiftoolsObjectCollisionProps(bpy.types.PropertyGroup):
    '''Group of Havok related properties, which gets attached to objects through a property pointer.'''
    @classmethod
    def register(cls):

        # physics
        bpy.types.Object.nifcollision = PointerProperty(
                        name='Niftools Collision Property',
                        description = 'Additional collision properties used by the Nif File Format',
                        type = cls,
                        )
        
        cls.motion_system = EnumProperty(
                        name='Motion System',
                        description = 'Havok Motion System settings for bhkRigidBody(t)',
                        items = [(item, item,"", i) for i, item in enumerate(NifFormat.MotionSystem._enumkeys)],
                        # default = 'MO_SYS_FIXED',
                        
                        )
           
        cls.oblivion_layer = EnumProperty(
                        name = 'Oblivion Layer',
                        description = 'Mesh color, used in Editor',
                        items = [(item, item,"", i) for i, item in enumerate(NifFormat.OblivionLayer._enumkeys)],
                        # default = 'OL_STATIC',
                        )

        cls.deactivator_type = EnumProperty(
                        name = 'Deactivator Type',
                        description = 'Motion deactivation setting',
                        items = [(item, item,"", i) for i, item in enumerate(NifFormat.DeactivatorType._enumkeys)],
                        )

        cls.solver_deactivation = EnumProperty(
                        name = 'Solver Deactivation',
                        description = 'Motion deactivation setting',
                        items = [(item, item,"", i) for i, item in enumerate(NifFormat.SolverDeactivation._enumkeys)],
                        )
          
        cls.quality_type = EnumProperty(
                        name = 'Quality Type',
                        description = 'Determines quality of motion',
                        items = [(item, item,"", i) for i, item in enumerate(NifFormat.MotionQuality._enumkeys)],
                        # default = 'MO_QUAL_FIXED',
                        )
        
        cls.col_filter = IntProperty(
                        name = 'Col Filter',
                        description = 'Flags for bhkRigidBody(t)',
                        default = 0
                        )

        cls.max_linear_velocity = FloatProperty(
                        name = 'Max Linear Velocity',
                        description = 'Linear velocity limit for bhkRigidBody(t)',
                        default = 0
                        )

        cls.max_angular_velocity = FloatProperty(
                        name = 'Max Angular Velocity',
                        description = 'Angular velocity limit for bhkRigidBody(t)',
                        default = 0
                        )
        
        cls.havok_material = EnumProperty(
                        name = 'Havok Material',
                        description = 'The Shapes material',
                        items = [(item, item,"", i) for i, item in enumerate(NifFormat.HavokMaterial._enumkeys)],
                        # default = 'HAV_MAT_WOOD'
                        )
                        
        cls.export_bhklist = BoolProperty(
                        name = 'Export BHKList',
                        description = 'None',
                        default = False
                        )
        
        cls.use_blender_properties = BoolProperty(
                        name = 'Use Blender Properties',
                        description = 'Whether or not to export collision settings via blender properties',
                        default = False,
                        )
    @classmethod
    def unregister(cls):
        del bpy.types.Object.nifcollision


class NiftoolsConstraintProps(bpy.types.PropertyGroup):
    @classmethod
    def register(cls):
        bpy.types.Object.niftools_constraint = PointerProperty(
						name='Niftools Constraint Property',
						description = 'Additional constraint properties used by the Nif File Format',
						type = cls
						)

        cls.LHMaxFriction = FloatProperty(
						name = 'LHMaxFriction',
						description = 'Havok limited hinge max friction.',
						)
        cls.tau = FloatProperty(
                        name = 'tau',
                        description = 'Havok limited hinge max friction.',
                        )
        cls.damping = FloatProperty(
                        name = 'damping',
                        description = 'Havok limited hinge max friction.',
                        )

    @classmethod
    def unregister(cls):
        del bpy.types.Object.niftools_constraint


def register():
    bpy.utils.register_class(NiftoolsMaterialProps)
    bpy.utils.register_class(NiftoolsObjectProps)
    bpy.utils.register_class(NiftoolsObjectCollisionProps)


def unregister():
    bpy.utils.unregister_class(NiftoolsMaterialProps)
    bpy.utils.unregister_class(NiftoolsObjectProps)
    bpy.utils.unregister_class(NiftoolsObjectCollisionProps)
    bpy.utils.unregister_class(NiftoolsSkinPartFlags)
