"""This script contains classes to help import animations."""

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

from pyffi.formats.nif import NifFormat
from io_scene_nif.materialsys.material_export import Material
from io_scene_nif.utility.nif_global import NifOp

class PropertyHelper():
    
    def __init__(self, parent):
        self.object_property = ObjectProperty(parent)
        self.material_property = Material(parent)
        
        
class ObjectProperty():
    
    def __init__(self, parent):
        self.nif_export = parent
        
    def export_vertex_color_property(self, block_parent, flags=1,
                                     vertex_mode=0, lighting_mode=1):
        """Create a vertex color property, and attach it to an existing block
        (typically, the root of the nif tree).
    
        @param block_parent: The block to which to attach the new property.
        @param flags: The C{flags} of the new property.
        @param vertex_mode: The C{vertex_mode} of the new property.
        @param lighting_mode: The C{lighting_mode} of the new property.
        @return: The new property block.
        """
        # create new vertex color property block
        vcolprop = self.nif_export.objecthelper.create_block("NiVertexColorProperty")
    
        # make it a property of the parent
        block_parent.add_property(vcolprop)
    
        # and now export the parameters
        vcolprop.flags = flags
        vcolprop.vertex_mode = vertex_mode
        vcolprop.lighting_mode = lighting_mode
    
        return vcolprop
    
    def export_z_buffer_property(self, block_parent,
                                 flags=15, function=3):
        """Create a z-buffer property, and attach it to an existing block
        (typically, the root of the nif tree).

        @param block_parent: The block to which to attach the new property.
        @param flags: The C{flags} of the new property.
        @param function: The C{function} of the new property.
        @return: The new property block.
        """
        # create new z-buffer property block
        zbuf = self.nif_export.objecthelper.create_block("NiZBufferProperty")

        # make it a property of the parent
        block_parent.add_property(zbuf)

        # and now export the parameters
        zbuf.flags = flags
        zbuf.function = function

        return zbuf
    
    def export_alpha_property(self, flags=0x00ED, threshold=0):
        """Return existing alpha property with given flags, or create new one
        if an alpha property with required flags is not found."""
        # search for duplicate
        for block in self.nif_export.dict_blocks:
            if isinstance(block, NifFormat.NiAlphaProperty) \
               and block.flags == flags and block.threshold == threshold:
                return block
        # no alpha property with given flag found, so create new one
        alphaprop = self.nif_export.objecthelper.create_block("NiAlphaProperty")
        alphaprop.flags = flags
        alphaprop.threshold = threshold
        return alphaprop

    def export_specular_property(self, flags = 0x0001):
        """Return existing specular property with given flags, or create new one
        if a specular property with required flags is not found."""
        # search for duplicate
        for block in self.nif_export.dict_blocks:
            if isinstance(block, NifFormat.NiSpecularProperty) \
               and block.flags == flags:
                return block
        # no specular property with given flag found, so create new one
        specprop = self.nif_export.objecthelper.create_block("NiSpecularProperty")
        specprop.flags = flags
        return specprop

    def export_wireframe_property(self, flags = 0x0001):
        """Return existing wire property with given flags, or create new one
        if an wire property with required flags is not found."""
        # search for duplicate
        for block in self.nif_export.dict_blocks:
            if isinstance(block, NifFormat.NiWireframeProperty) \
               and block.flags == flags:
                return block

        # no wire property with given flag found, so create new one
        wireprop = self.nif_export.objecthelper.create_block("NiWireframeProperty")
        wireprop.flags = flags
        return wireprop

    def export_stencil_property(self):
        """Return existing stencil property with given flags, or create new one
        if an identical stencil property."""
        # search for duplicate
        for block in self.nif_export.dict_blocks:
            if isinstance(block, NifFormat.NiStencilProperty):
                # all these blocks have the same setting, no further check
                # is needed
                return block
        # no stencil property found, so create new one
        stencilprop = self.nif_export.objecthelper.create_block("NiStencilProperty")
        if NifOp.props.game == 'FALLOUT_3':
            stencilprop.flags = 19840
        return stencilprop
    
    
