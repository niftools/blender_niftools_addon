"""This script contains classes to help export properties."""

# ***** BEGIN LICENSE BLOCK *****
#
# Copyright © 2013, NIF File Format Library and Tools contributors.
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

from io_scene_nif.modules.obj import block_registry
from io_scene_nif.modules.obj.block_registry import BlockRegistry
from io_scene_nif.modules.property.material.material_export import Material
from io_scene_nif.utility.nif_global import NifOp


class PropertyHelper:
    
    def __init__(self, parent):
        self.object_property = ObjectProperty(parent)
        self.material_property = Material(parent)
        
        
class ObjectProperty:
    
    def __init__(self, parent):
        self.nif_export = parent
        
    def export_vertex_color_property(self, block_parent, flags=1, vertex_mode=0, lighting_mode=1):
        """Create a vertex color property, and attach it to an existing block
        (typically, the root of the nif tree).
    
        @param block_parent: The block to which to attach the new property.
        @param flags: The C{flags} of the new property.
        @param vertex_mode: The C{vertex_mode} of the new property.
        @param lighting_mode: The C{lighting_mode} of the new property.
        @return: The new property block.
        """
        # create new vertex color property block
        vcol_prop = BlockRegistry.create_block("NiVertexColorProperty")
    
        # make it a property of the parent
        block_parent.add_property(vcol_prop)
    
        # and now export the parameters
        vcol_prop.flags = flags
        vcol_prop.vertex_mode = vertex_mode
        vcol_prop.lighting_mode = lighting_mode
    
        return vcol_prop
    
    def export_z_buffer_property(self, block_parent, flags=15, func=3):
        """Create a z-buffer property, and attach it to an existing block
        (typically, the root of the nif tree).

        @param block_parent: The block to which to attach the new property.
        @param flags: The C{flags} of the new property.
        @param func: The C{function} of the new property.
        @return: The new property block.
        """
        # create new z-buffer property block
        zbuf = BlockRegistry.create_block("NiZBufferProperty")

        # make it a property of the parent
        block_parent.add_property(zbuf)

        # and now export the parameters
        zbuf.flags = flags
        zbuf.function = func

        return zbuf

    # TODO [material][property] Move this to new form property processing
    def export_alpha_property(self, flags=0x00ED, threshold=0):
        """Return existing alpha property with given flags, or create new one
        if an alpha property with required flags is not found."""
        # search for duplicate
        for block in block_registry.block_to_obj:
            if isinstance(block, NifFormat.NiAlphaProperty) and block.flags == flags and block.threshold == threshold:
                return block

        # no alpha property with given flag found, so create new one
        alpha_prop = BlockRegistry.create_block("NiAlphaProperty")
        alpha_prop.flags = flags
        alpha_prop.threshold = threshold
        return alpha_prop

    def export_specular_property(self, flags=0x0001):
        """Return existing specular property with given flags, or create new one
        if a specular property with required flags is not found."""
        # search for duplicate
        for block in block_registry.block_to_obj:
            if isinstance(block, NifFormat.NiSpecularProperty) and block.flags == flags:
                return block

        # no specular property with given flag found, so create new one
        spec_prop = BlockRegistry.create_block("NiSpecularProperty")
        spec_prop.flags = flags
        return spec_prop

    def export_wireframe_property(self, flags=0x0001):
        """Return existing wire property with given flags, or create new one
        if an wire property with required flags is not found."""
        # search for duplicate
        for block in block_registry.block_to_obj:
            if isinstance(block, NifFormat.NiWireframeProperty) and block.flags == flags:
                return block

        # no wire property with given flag found, so create new one
        wire_prop = BlockRegistry.create_block("NiWireframeProperty")
        wire_prop.flags = flags
        return wire_prop

    def export_stencil_property(self):
        """Return existing stencil property with given flags, or create new one
        if an identical stencil property."""
        # search for duplicate
        for block in block_registry.block_to_obj:
            if isinstance(block, NifFormat.NiStencilProperty):
                # all these blocks have the same setting, no further check
                # is needed
                return block

        # no stencil property found, so create new one
        stencil_prop = BlockRegistry.create_block("NiStencilProperty")
        if NifOp.props.game == 'FALLOUT_3':
            stencil_prop.flags = 19840
        return stencil_prop
