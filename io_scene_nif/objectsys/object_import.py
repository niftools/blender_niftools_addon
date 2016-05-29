"""This script contains helper methods to export objects."""

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
import mathutils

from pyffi.formats.nif import NifFormat

from io_scene_nif.utility import nif_utils
from io_scene_nif.collisionsys.collision_import import BoundBox
from io_scene_nif.utility.nif_logging import NifLog

class NiObject():     
    
    @staticmethod
    def import_extra_data(b_obj, root_block):
        for n_extra in root_block.get_extra_datas():
            if isinstance(n_extra, NifFormat.BSBound):
                b_bbox = BoundBox.import_bsbound(n_extra)
                b_bbox.parent = b_obj
            
            elif isinstance(n_extra, NifFormat.BSXFlags):
                # get bsx flags so we can attach it to collision object
                b_obj.niftools.bsxflags = n_extra.integer_data
            
            elif isinstance(n_extra, NifFormat.NiStringExtraData):
                if n_extra.name.decode() == "UPB":
                    b_obj.niftools.upb = n_extra.string_data.decode()
            
            elif isinstance(n_extra, NifFormat.BSInvMarker):
                    b_obj.niftools_bs_invmarker.add()
                    b_obj.niftools_bs_invmarker[0].name = n_extra.name.decode()
                    b_obj.niftools_bs_invmarker[0].bs_inv_x = n_extra.rotation_x
                    b_obj.niftools_bs_invmarker[0].bs_inv_y = n_extra.rotation_y
                    b_obj.niftools_bs_invmarker[0].bs_inv_z = n_extra.rotation_z
                    b_obj.niftools_bs_invmarker[0].bs_inv_zoom = n_extra.zoom
                    
            else:
                NifLog.warn("{0} Block currently unsupported for import".format(n_extra))
            
