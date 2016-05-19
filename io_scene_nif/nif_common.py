"""Helper functions for nif import and export scripts."""

# ***** BEGIN LICENSE BLOCK *****
# 
# Copyright © 2005-2015, NIF File Format Library and Tools contributors.
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
import re

import pyffi
from pyffi.formats.nif import NifFormat
from io_scene_nif.utility.nif_logging import NifLog
from io_scene_nif.utility.nif_global import NifGlobal

class NifCommon:
    """Abstract base class for import and export. Contains utility functions
    that are commonly used in both import and export.
    """
    
    # dictionary of bones that belong to a certain armature
    # maps NIF armature name to list of NIF bone name
    dict_armatures = {}
    # dictionary of bones, maps Blender bone name to matrix that maps the
    # NIF bone matrix on the Blender bone matrix
    # B' = X * B, where B' is the Blender bone matrix, and B is the NIF bone matrix
    dict_bones_extra_matrix = {}

    # dictionary of bones, maps Blender bone name to matrix that maps the
    # NIF bone matrix on the Blender bone matrix
    # Recall from the import script
    #   B' = X * B,
    # where B' is the Blender bone matrix, and B is the NIF bone matrix,
    # both in armature space. So to restore the NIF matrices we need to do
    #   B = X^{-1} * B'
    # Hence, we will restore the X's, invert them, and store those inverses in the
    # following dictionary.
    dict_bones_extra_matrix_inv = {}

    # dictionary mapping bhkRigidBody objects to objects imported in Blender; 
    # we use this dictionary to set the physics constraints (ragdoll etc)
    dict_havok_objects = {}
    
    # dictionary of names, to map NIF blocks to correct Blender names
    dict_names = {}

    # dictionary of bones, maps Blender name to NIF block
    dict_blocks = {}
    
    # keeps track of names of exported blocks, to make sure they are unique
    dict_block_names = []

    # bone animation priorities (maps NiNode name to priority number);
    # priorities are set in import_kf_root and are stored into the name
    # of a NULL constraint (for lack of something better) in
    # import_armature
    dict_bone_priorities = {}

    # dictionary of materials, to reuse materials
    dict_materials = {}
    
    # dictionary of texture files, to reuse textures
    dict_textures = {}
    dict_mesh_uvlayers = []

    VERTEX_RESOLUTION = 1000
    NORMAL_RESOLUTION = 100

    EXTRA_SHADER_TEXTURES = [
        "EnvironmentMapIndex",
        "NormalMapIndex",
        "SpecularIntensityIndex",
        "EnvironmentIntensityIndex",
        "LightCubeMapIndex",
        "ShadowTextureIndex"]
    """Names (ordered by default index) of shader texture slots for
    Sid Meier's Railroads and similar games.
    """
    
    HAVOK_SCALE = 6.996

    def __init__(self, operator, context):
        """Common initialization functions for executing the import/export operators: """
        
        NifGlobal.init(operator, context)
        
        # copy properties from operator (contains import/export settings)
        self.operator = operator
        self.properties = operator.properties
        
        # save context (so it can be used in other methods without argument passing)
        self.context = context     
        
        # print scripts info
        from . import bl_info
        niftools_ver = (".".join(str(i) for i in bl_info["version"]))
        
        NifLog.info("Executing - Niftools : Blender Nif Plugin v{0} (running on Blender {1}, PyFFI {2})".format(niftools_ver,
                                                                                                bpy.app.version_string,
                                                                                                pyffi.__version__))

        # find and store this list now of selected objects as creating new objects adds them to the selection list
        self.selected_objects = self.context.selected_objects[:]


    def get_bone_name_for_blender(self, name):
        """Convert a bone name to a name that can be used by Blender: turns
        'Bip01 R xxx' into 'Bip01 xxx.R', and similar for L.

        :param name: The bone name as in the nif file.
        :type name: :class:`str`
        :return: Bone name in Blender convention.
        :rtype: :class:`str`
        """
        if isinstance(name, bytes):
            name = name.decode()
        if name.startswith("Bip01 L "):
            return "Bip01 " + name[8:] + ".L"
        elif name.startswith("Bip01 R "):
            return "Bip01 " + name[8:] + ".R"
        elif name.startswith("NPC L ") and name.endswith("]"):
            name = name.replace("NPC L", "NPC")
            name = name.replace("[L", "[")
            name = name.replace("]", "].L")
            return name
        elif name.startswith("NPC R ") and name.endswith("]"):
            name = name.replace("NPC R", "NPC")
            name = name.replace("[R", "[")
            name = name.replace("]", "].R")
            return name

        return name

    def get_bone_name_for_nif(self, name):
        """Convert a bone name to a name that can be used by the nif file:
        turns 'Bip01 xxx.R' into 'Bip01 R xxx', and similar for L.

        :param name: The bone name as in Blender.
        :type name: :class:`str`
        :return: Bone name in nif convention.
        :rtype: :class:`str`
        """
        if isinstance(name, bytes):
            name = name.decode()
        if name.startswith("Bip01 "):
            if name.endswith(".L"):
                return "Bip01 L " + name[6:-2]
            elif name.endswith(".R"):
                return "Bip01 R " + name[6:-2]
        elif name.startswith("NPC ") and name.endswith("].L"):
            name = name.replace("NPC ", "NPC L")
            name = name.replace("[", "[L")
            name = name.replace("].L", "]")
            return name
        elif name.startswith("NPC ") and name.endswith("].R"):
            name = name.replace("NPC ", "NPC R")
            name = name.replace("[", "[R")
            name = name.replace("].R", "]")
            return name

        return name

    def get_extend_from_flags(self, flags):
        if flags & 6 == 4: # 0b100
            return Blender.IpoCurve.ExtendTypes.CONST
        elif flags & 6 == 0: # 0b000
            return Blender.IpoCurve.ExtendTypes.CYCLIC

        NifLog.warn("Unsupported cycle mode in nif, using clamped.")
        return Blender.IpoCurve.ExtendTypes.CONST

    def get_b_ipol_from_n_ipol(self, n_ipol):
        if n_ipol == NifFormat.KeyType.LINEAR_KEY:
            return Blender.IpoCurve.InterpTypes.LINEAR
        elif n_ipol == NifFormat.KeyType.QUADRATIC_KEY:
            return Blender.IpoCurve.InterpTypes.BEZIER
        elif n_ipol == 0:
            # guessing, not documented in nif.xml
            return Blender.IpoCurve.InterpTypes.CONST
        
        NifLog.warn("Unsupported interpolation mode ({0}) in nif, using quadratic/bezier.".format(n_ipol))
        return Blender.IpoCurve.InterpTypes.BEZIER

    def get_n_ipol_from_b_ipol(self, b_ipol):
        if b_ipol == Blender.IpoCurve.InterpTypes.LINEAR:
            return NifFormat.KeyType.LINEAR_KEY
        elif b_ipol == Blender.IpoCurve.InterpTypes.BEZIER:
            return NifFormat.KeyType.QUADRATIC_KEY
        elif b_ipol == Blender.IpoCurve.InterpTypes.CONST:
            return NifFormat.KeyType.CONST_KEY
        
        NifLog.warn("Unsupported interpolation mode ({0}) in blend, using quadratic/bezier.".format(b_ipol))
        return NifFormat.KeyType.QUADRATIC_KEY

    def get_n_apply_mode_from_b_blend_type(self, b_blend_type):
        if b_blend_type == "LIGHTEN":
            return NifFormat.ApplyMode.APPLY_HILIGHT
        elif b_blend_type == "MULTIPLY":
            return NifFormat.ApplyMode.APPLY_HILIGHT2
        elif b_blend_type == "MIX":
            return NifFormat.ApplyMode.APPLY_MODULATE
        
        NifLog.warn("Unsupported blend type ({0}) in material, using apply mode APPLY_MODULATE".format(b_blend_type))
        return NifFormat.ApplyMode.APPLY_MODULATE
