"""This script imports Netimmerse/Gamebryo nif files to Blender."""

# ***** BEGIN LICENSE BLOCK *****
#
# Copyright © 2019, NIF File Format Library and Tools contributors.
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

import os
import bpy

import pyffi.spells.nif.fix

from io_scene_niftools.file_io.kf import KFFile
from io_scene_niftools.modules.nif_export import armature
from io_scene_niftools.modules.nif_export.animation.transform import TransformAnimation
from io_scene_niftools.nif_common import NifCommon
from io_scene_niftools.utils import math
from io_scene_niftools.utils.singleton import NifOp, NifData
from io_scene_niftools.utils.logging import NifLog, NifError
from io_scene_niftools.modules.nif_export import scene
from io_scene_niftools.modules.nif_export.block_registry import block_store


class KfaExport(NifCommon):

    def __init__(self, operator, context):
        NifCommon.__init__(self, operator, context)

        # Helper systems
        self.transform_anim = TransformAnimation()

    def execute(self):
        """Main export function."""

        NifLog.info(f"Exporting {NifOp.props.filepath}")

        # extract directory, base name, extension
        directory = os.path.dirname(NifOp.props.filepath)
        filebase, fileext = os.path.splitext(os.path.basename(NifOp.props.filepath))

        if bpy.context.scene.niftools_scene.game == 'NONE':
            raise NifError("You have not selected a game. Please select a game in the scene tab.")

        prefix = ""
        self.version, data = scene.get_version_data()
        NifData.init(data)

        b_armature = math.get_armature()
        # some scenes may not have an armature, so nothing to do here
        if b_armature:
            math.set_bone_orientation(b_armature.data.niftools.axis_forward, b_armature.data.niftools.axis_up)

        NifLog.info("Creating keyframe tree")
        kfa_root = self.transform_anim.export_kfa_root(b_armature)

        # write kfa 
        ext = ".kfa"
        NifLog.info(f"Writing {prefix}{ext} file")
        
        data.roots = []
        # first NiNode 
        data.roots.append(kfa_root)
        
        # remaining NiNodes : corresponding to first bone position computed via NiKeyframeController
        kfc = kfa_root.controller
            
        while kfc != None:
            node_root = block_store.create_block("NiNode")
            # TODO : rotation 
            # node_root.rotation = compute from kfc.data.quaternion_keys[0].value 
            node_root.translation = kfc.data.translations.keys[0].value*NifOp.props.scale_correction 
            # scale to improve 
            node_root.scale = 1.0
            data.roots.append(node_root)
            kfc = kfc.next_controller

        # scale correction for the skeleton
        self.apply_scale(data, round(1 / NifOp.props.scale_correction))

        kfafile = os.path.join(directory, prefix + filebase + ext)
        with open(kfafile, "wb") as stream:
            data.write(stream)

        NifLog.info("Finished successfully")
        return {'FINISHED'}

