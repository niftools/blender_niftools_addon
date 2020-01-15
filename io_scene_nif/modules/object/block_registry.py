"""This module contains helper methods to block_store objects between nif and blender objects."""

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

from pyffi.formats.nif import NifFormat

from io_scene_nif.modules import armature
from io_scene_nif.utility import nif_utils
from io_scene_nif.utility.util_logging import NifLog


class BlockRegistry:

    def __init__(self):
        self._block_to_obj = {}

    @property
    def block_to_obj(self): 
        return self._block_to_obj

    @block_to_obj.setter
    def block_to_obj(self, value):
        self._block_to_obj = value

    def register_block(self, block, b_obj=None):
        """Helper function to register a newly created block in the list of
        exported blocks and to associate it with a Blender object.

        @param block: The nif block.
        @param b_obj: The Blender object.
        @return: C{block}"""
        if b_obj is None:
            NifLog.info("Exporting {0} block".format(block.__class__.__name__))
        else:
            NifLog.info("Exporting {0} as {1} block".format(b_obj, block.__class__.__name__))
        self._block_to_obj[block] = b_obj
        return block

    def create_block(self, block_type, b_obj=None):
        """Helper function to create a new block, register it in the list of
        exported blocks, and associate it with a Blender object.

        @param block_type: The nif block type (for instance "NiNode").
        @type block_type: C{str}
        @param b_obj: The Blender object.
        @return: The newly created block."""
        try:
            block = getattr(NifFormat, block_type)()
        except AttributeError:
            raise nif_utils.NifError("'{0}': Unknown block type (this is probably a bug).".format(block_type))
        return self.register_block(block, b_obj)

    @staticmethod
    def store_longname(b_obj, n_name):
        """Save original name as object property, for export"""
        if b_obj.name != n_name:
            b_obj.niftools.longname = n_name
            NifLog.debug("Stored long name for {0}".format(b_obj.name))

    @staticmethod
    def import_name(n_block):
        """Get name of n_block, ready for blender but not necessarily unique.

        :param n_block: A named nif block.
        :type n_block: :class:`~pyffi.formats.nif.NifFormat.NiObjectNET`
        """
        if n_block is None:
            return ""

        NifLog.debug("Importing name for {0} block from {1}".format(n_block.__class__.__name__, n_block.name))

        n_name = n_block.name.decode()

        # if name is empty, create something non-empty
        if not n_name:
            n_name = "noname"
        n_name = armature.get_bone_name_for_blender(n_name)

        return n_name


block_store = BlockRegistry()
