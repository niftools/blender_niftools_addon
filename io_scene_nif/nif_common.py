"""Helper functions for nif import and export scripts."""

# ***** BEGIN LICENSE BLOCK *****
# 
# Copyright © 2005-2012, NIF File Format Library and Tools contributors.
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

import logging

import bpy

import pyffi
from pyffi.formats.nif import NifFormat

class NifCommon:
    """Abstract base class for import and export. Contains utility functions
    that are commonly used in both import and export.
    """

    VERTEX_RESOLUTION = 1000
    NORMAL_RESOLUTION = 100
    UV_RESOLUTION = 10000
    VCOL_RESOLUTION = 100

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

    USED_EXTRA_SHADER_TEXTURES = {
        'SID_MEIER_S_RAILROADS': (3, 0, 4, 1, 5, 2),
        'CIVILIZATION_IV': (3, 0, 1, 2)}
    """The default ordering of the extra data blocks for different games."""
    
    HAVOK_SCALE = 7.0
    IMPORT_EXTRANODES = True

    # TODO - Find a better way to expose these
    EXPORT_OPTIMIZE_MATERIALS = True
    EXPORT_OB_COLLISION_DO_NOT_USE_BLENDER_PROPERTIES = False
    
    EXPORT_BHKLISTSHAPE = False
    EXPORT_OB_BSXFLAGS = 2
    EXPORT_OB_MASS = 10.0
    EXPORT_OB_SOLID = True
    EXPORT_OB_MOTIONSYSTEM = 7, # MO_SYS_FIXED
    EXPORT_OB_UNKNOWNBYTE1 = 1
    EXPORT_OB_UNKNOWNBYTE2 = 1
    EXPORT_OB_QUALITYTYPE = 1 # MO_QUAL_FIXED
    EXPORT_OB_WIND = 0
    EXPORT_OB_LAYER = 1 # static
    EXPORT_OB_MATERIAL = 9 # wood
    EXPORT_OB_PRN = "NONE" # Todo with location on character. For weapons, rings, helmets, Sheilds ect
    progress_bar = 0
    """Level of the progress bar."""



    def __init__(self, operator, context):
        """Common initialization functions for executing the import/export
        operators:

        - initialize progress bar
        - set logging level
        - set self.context
        - set self.selected_objects
        """
        # print scripts info
        from . import bl_info
        operator.report(
            {'INFO'},
            "Blender NIF Scripts %s"
            " (running on Blender %s, PyFFI %s)"
            % (".".join(str(i) for i in bl_info["version"]),
               bpy.app.version_string,
               pyffi.__version__))

        # copy properties from operator (contains import/export settings)
        self.operator = operator
        self.properties = operator.properties

        # set logging level
        log_level_num = getattr(logging, self.properties.log_level)
        logging.getLogger("niftools").setLevel(log_level_num)
        logging.getLogger("pyffi").setLevel(log_level_num)

        # save context (so it can be used in other methods without argument
        # passing)
        self.context = context

        # get list of selected objects
        # (find and store this list now, as creating new objects adds them
        # to the selection list)
        self.selected_objects = self.context.selected_objects[:]

    def execute(self):
        """Import/export entry point. Default implementation does nothing."""
        return {'FINISHED'}

    def debug(self, message):
        """Report a debug message."""
        self.operator.report({'DEBUG'}, message)

    def info(self, message):
        """Report an informative message."""
        self.operator.report({'INFO'}, message)

    def warning(self, message):
        """Report a warning message."""
        self.operator.report({'WARNING'}, message)

    def error(self, message):
        """Report an error and return ``{'FINISHED'}``. To be called by
        the :meth:`execute` method, as::

            return error('Something went wrong.')

        Blender will raise an exception that is passed to the caller.

        .. seealso::

            The :ref:`error reporting <dev-design-error-reporting>` design.
        """
        self.operator.report({'ERROR'}, message)
        return {'FINISHED'}

    def get_bone_name_for_blender(self, name):
        """Convert a bone name to a name that can be used by Blender: turns
        'Bip01 R xxx' into 'Bip01 xxx.R', and similar for L.

        :param name: The bone name as in the nif file.
        :type name: :class:`str`
        :return: Bone name in Blender convention.
        :rtype: :class:`str`
        """
        if name.startswith("Bip01 L "):
            return "Bip01 " + name[8:] + ".L"
        elif name.startswith("Bip01 R "):
            return "Bip01 " + name[8:] + ".R"
        return name

    def get_bone_name_for_nif(self, name):
        """Convert a bone name to a name that can be used by the nif file:
        turns 'Bip01 xxx.R' into 'Bip01 R xxx', and similar for L.

        :param name: The bone name as in Blender.
        :type name: :class:`str`
        :return: Bone name in nif convention.
        :rtype: :class:`str`
        """
        if name.startswith("Bip01 "):
            if name.endswith(".L"):
                return "Bip01 L " + name[6:-2]
            elif name.endswith(".R"):
                return "Bip01 R " + name[6:-2]
        return name

    def get_extend_from_flags(self, flags):
        if flags & 6 == 4: # 0b100
            return Blender.IpoCurve.ExtendTypes.CONST
        elif flags & 6 == 0: # 0b000
            return Blender.IpoCurve.ExtendTypes.CYCLIC

        self.warning(
            "Unsupported cycle mode in nif, using clamped.")
        return Blender.IpoCurve.ExtendTypes.CONST

    def get_flags_from_extend(self, extend):
        if extend == Blender.IpoCurve.ExtendTypes.CONST:
            return 4 # 0b100
        elif extend == Blender.IpoCurve.ExtendTypes.CYCLIC:
            return 0

        self.warning(
            "Unsupported extend type in blend, using clamped.")
        return 4

    def get_b_ipol_from_n_ipol(self, n_ipol):
        if n_ipol == NifFormat.KeyType.LINEAR_KEY:
            return Blender.IpoCurve.InterpTypes.LINEAR
        elif n_ipol == NifFormat.KeyType.QUADRATIC_KEY:
            return Blender.IpoCurve.InterpTypes.BEZIER
        elif n_ipol == 0:
            # guessing, not documented in nif.xml
            return Blender.IpoCurve.InterpTypes.CONST
        self.warning(
            "Unsupported interpolation mode in nif, using quadratic/bezier.")
        return Blender.IpoCurve.InterpTypes.BEZIER

    def get_n_ipol_from_b_ipol(self, b_ipol):
        if b_ipol == Blender.IpoCurve.InterpTypes.LINEAR:
            return NifFormat.KeyType.LINEAR_KEY
        elif b_ipol == Blender.IpoCurve.InterpTypes.BEZIER:
            return NifFormat.KeyType.QUADRATIC_KEY
        elif b_ipol == Blender.IpoCurve.InterpTypes.CONST:
            return NifFormat.KeyType.CONST_KEY
        self.warning(
            "Unsupported interpolation mode in blend, using quadratic/bezier.")
        return NifFormat.KeyType.QUADRATIC_KEY

    def get_n_apply_mode_from_b_blend_type(self, b_blend_type):
        if b_blend_type == "LIGHTEN":
            return NifFormat.ApplyMode.APPLY_HILIGHT
        elif b_blend_type == "MULTIPLY":
            return NifFormat.ApplyMode.APPLY_HILIGHT2
        elif b_blend_type == "MIX":
            return NifFormat.ApplyMode.APPLY_MODULATE
        self.warning(
            "Unsupported blend type (%s) in material,"
            " using apply mode APPLY_MODULATE" % b_blend_type)
        return NifFormat.ApplyMode.APPLY_MODULATE

    def find_controller(self, niBlock, controller_type):
        """Find a controller."""
        ctrl = niBlock.controller
        while ctrl:
            if isinstance(ctrl, controller_type):
                break
            ctrl = ctrl.next_controller
        return ctrl

    def find_property(self, niBlock, property_type):
        """Find a property."""
        for prop in niBlock.properties:
            if isinstance(prop, property_type):
                return prop
        return None

    def find_extra(self, niBlock, extratype):
        # TODO_3.0 - Optimise
        
        """Find extra data."""
        # pre-10.x.x.x system: extra data chain
        extra = niBlock.extra_data
        while extra:
            if isinstance(extra, extratype):
                break
            extra = extra.next_extra_data
        if extra:
            return extra

        # post-10.x.x.x system: extra data list
        for extra in niBlock.extra_data_list:
            if isinstance(extra, extratype):
                return extra
        return None
