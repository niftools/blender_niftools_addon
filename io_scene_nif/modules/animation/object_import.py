"""This script contains classes to help import object animations."""

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

import bpy
from pyffi.formats.nif import NifFormat

from io_scene_nif.modules.animation import animation_export
from io_scene_nif.modules.object.block_registry import block_store
from io_scene_nif.utility import nif_utils
from io_scene_nif.utility.util_global import NifOp
from io_scene_nif.utility.util_logging import NifLog


class ObjectAnimation:

    def __init__(self, parent):
        self.animationhelper = parent

    def import_visibility(self, n_node, b_obj):
        """Import vis controller for blender object."""

        n_vis_ctrl = nif_utils.find_controller(n_node, NifFormat.NiVisController)
        if not (n_vis_ctrl and n_vis_ctrl.data):
            return
        NifLog.info("Importing vis controller")

        b_obj_action = self.animationhelper.create_action(b_obj, b_obj.name + "-Anim")

        fcurves = self.animationhelper.create_fcurves(b_obj_action, "hide", (0,), n_vis_ctrl.flags)
        for key in n_vis_ctrl.data.keys:
            self.animationhelper.add_key(fcurves, key.time, (key.value,), "CONSTANT")

    def import_morph_controller(self, n_node, b_obj, v_map):
        """Import NiGeomMorpherController as shape keys for blender object."""

        n_morphCtrl = nif_utils.find_controller(n_node, NifFormat.NiGeomMorpherController)
        if n_morphCtrl:
            b_mesh = b_obj.data
            morphData = n_morphCtrl.data
            if morphData.num_morphs:
                b_obj_action = self.animationhelper.create_action(b_obj, b_obj.name + "-Morphs")
                fps = bpy.context.scene.render.fps
                # get name for base key
                keyname = morphData.morphs[0].frame_name.decode()
                if not keyname:
                    keyname = 'Base'

                # insert base key at frame 1, using relative keys
                sk_basis = b_obj.shape_key_add(keyname)

                # get base vectors and import all morphs
                baseverts = morphData.morphs[0].vectors

                for idxMorph in range(1, morphData.num_morphs):
                    # get name for key
                    keyname = morphData.morphs[idxMorph].frame_name.decode()
                    if not keyname:
                        keyname = 'Key %i' % idxMorph
                    NifLog.info("Inserting key '{0}'".format(keyname))
                    # get vectors
                    morph_verts = morphData.morphs[idxMorph].vectors
                    self.morph_mesh(b_mesh, baseverts, morph_verts, v_map)
                    shape_key = b_obj.shape_key_add(keyname, from_mix=False)

                    # first find the keys
                    # older versions store keys in the morphData
                    morph_data = morphData.morphs[idxMorph]
                    # newer versions store keys in the controller
                    if not morph_data.keys:
                        try:
                            if n_morphCtrl.interpolators:
                                morph_data = n_morphCtrl.interpolators[idxMorph].data.data
                            elif n_morphCtrl.interpolator_weights:
                                morph_data = n_morphCtrl.interpolator_weights[idxMorph].interpolator.data.data
                        except KeyError:
                            NifLog.info("Unsupported interpolator '{0}'".format(type(n_morphCtrl.interpolator_weights[idxMorph].interpolator)))
                            continue
                    # TODO [animation] can we create the fcurve manually - does not seem to work here?
                    # as b_obj.data.shape_keys.animation_data is read-only

                    # FYI shape_key = b_mesh.shape_keys.key_blocks[-1]
                    # set keyframes
                    for key in morph_data.keys:
                        shape_key.value = key.value
                        shape_key.keyframe_insert(data_path="value", frame=round(key.time * fps))

                    # fcurves = (b_obj.data.shape_keys.animation_data.action.fcurves[-1], )
                    # # set extrapolation to fcurves
                    # self.nif_import.animation_helper.set_extrapolation(n_morphCtrl.flags, fcurves)
                    # # get the interpolation mode
                    # interp = self.nif_import.animation_helper.get_b_interp_from_n_interp( morph_data.interpolation)
                    # TODO [animation] set interpolation once low level access works
