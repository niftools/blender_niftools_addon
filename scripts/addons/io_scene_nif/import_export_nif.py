"""Helper functions for nif import and export scripts."""

# ***** BEGIN LICENSE BLOCK *****
# 
# Copyright © 2005-2011, NIF File Format Library and Tools contributors.
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

class NifImportExport:
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

    # Oblivion(and FO3) collision settings dicts for Anglicized names
    # on Object Properties for havok items
    OB_LAYER = [
        "Unidentified", "Static", "AnimStatic", "Transparent", "Clutter",
        "Weapon", "Projectile", "Spell", "Biped", "Props",
        "Water", "Trigger", "Terrain", "Trap", "NonCollidable",
        "CloudTrap", "Ground", "Portal", "Stairs", "CharController",
        "AvoidBox", "?", "?", "CameraPick", "ItemPick",
        "LineOfSight", "PathPick", "CustomPick1", "CustomPick2", "SpellExplosion",
        "DroppingPick", "Other", "Head", "Body", "Spine1",
        "Spine2", "LUpperArm", "LForeArm", "LHand", "LThigh",
        "LCalf", "LFoot",  "RUpperArm", "RForeArm", "RHand",
        "RThigh", "RCalf", "RFoot", "Tail", "SideWeapon",
        "Shield", "Quiver", "BackWeapon", "BackWeapon?", "PonyTail",
        "Wing", "Null"]

    MOTION_SYS = [
        "Invalid", "Dynamic", "Sphere", "Sphere Inertia", "Box",
        "Box Stabilized", "Keyframed", "Fixed", "Thin BOx", "Character"]

    HAVOK_MATERIAL = [
        "Stone", "Cloth", "Dirt", "Glass", "Grass",
        "Metal", "Organic", "Skin", "Water", "Wood",
        "Heavy Stone", "Heavy Metal", "Heavy Wood", "Chain", "Snow",
        "Stone Stairs", "Cloth Stairs", "Dirt Stairs", "Glass Stairs",
        "Grass Stairs", "Metal Stairs",
        "Organic Stairs", "Skin Stairs", "Water Stairs", "Wood Stairs",
        "Heavy Stone Stairs",
        "Heavy Metal Stairs", "Heavy Wood Stairs", "Chain Stairs",
        "Snow Stairs", "Elevator", "Rubber"]

    QUALITY_TYPE = [
        "Invalid", "Fixed", "Keyframed", "Debris", "Moving",
        "Critical", "Bullet", "User", "Character", "Keyframed Report"]

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

        # initialize progress bar
        self.msg_progress("Initializing", progbar=0)

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

    def msg_progress(self, message, progbar=None):
        """Message wrapper for the Blender progress bar.

        .. deprecated:: 2.6.0

            Use :meth:`info` instead.
        """
        # update progress bar level
        if progbar is None:
            if self.progress_bar > 0.89:
                # reset progress bar
                self.progress_bar = 0
                # TODO draw the progress bar
                #Blender.Window.DrawProgressBar(0, message)
            self.progress_bar += 0.1
        else:
            self.progress_bar = progbar
        # TODO draw the progress bar
        #Blender.Window.DrawProgressBar(self.progress_bar, message)

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
        :type name: :class:`bytes`
        :return: Bone name in nif convention.
        :rtype: :class:`bytes`
        """
        if name.startswith(b"Bip01 "):
            if name.endswith(b".L"):
                return b"Bip01 L " + name[6:-2]
            elif name.endswith(b".R"):
                return b"Bip01 R " + name[6:-2]
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

    def get_b_blend_type_from_n_apply_mode(self, n_apply_mode):
        if n_apply_mode == NifFormat.ApplyMode.APPLY_MODULATE:
            return "MIX"
        elif textProperty.apply_mode == NifFormat.ApplyMode.APPLY_REPLACE:
            return "MIX"
        elif textProperty.apply_mode == NifFormat.ApplyMode.APPLY_DECAL:
            return "MIX"
        elif textProperty.apply_mode == NifFormat.ApplyMode.APPLY_HILIGHT:
            return "LIGHTEN"
        elif textProperty.apply_mode == NifFormat.ApplyMode.APPLY_HILIGHT2:
            return "MULTIPLY"
        self.warning(
            "Unknown apply mode (%i) in material,"
            " using blend type 'MIX'" % n_apply_mode)
        return "MIX"

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

    def isinstance_blender_object(self, b_obj):
        """Unfortunately, isinstance(b_obj, Blender.Object.Object) does not
        work because the Object class is not exposed in the API.
        This method provides an alternative check.
        """
        # lame and slow, but functional
        return b_obj in bpy.data.objects

