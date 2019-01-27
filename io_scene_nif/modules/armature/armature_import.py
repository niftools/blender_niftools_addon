'''Script to import/export all the skeleton related objects.'''

# ***** BEGIN LICENSE BLOCK *****
# 
# Copyright © 2005-2015, NIF File Format Library and Tools contributors.
# All rights reserved.
# 
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions
# are met:
# 
#   * Redistributions of source code must retain the above copyright
#     notice, this list of conditions and the following disclaimer.
# 
#   * Redistributions in binary form must reproduce the above
#     copyright notice, this list of conditions and the following
#     disclaimer in the documentation and/or other materials provided
#     with the distribution.
# 
#   * Neither the name of the NIF File Format Library and Tools
#     project nor the names of its contributors may be used to endorse
#     or promote products derived from this software without specific
#     prior written permission.
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
import mathutils

from pyffi.formats.nif import NifFormat

from io_scene_nif.modules import armature
from io_scene_nif.utility import nif_utils
from io_scene_nif.utility.nif_logging import NifLog
from io_scene_nif.utility.nif_global import NifOp


class Armature():
    
    def __init__(self, parent):
        self.nif_import = parent
        
    def import_armature(self, niArmature):
        """Scans an armature hierarchy, and returns a whole armature.
        This is done outside the normal node tree scan to allow for positioning
        of the bones before skins are attached."""
        armature_name = self.nif_import.import_name(niArmature)

        b_armatureData = bpy.data.armatures.new(armature_name)
        # b_armatureData.show_names = True
        # b_armatureData.show_axes = True
        b_armatureData.draw_type = 'STICK'
        b_armature = bpy.data.objects.new(armature_name, b_armatureData)
        b_armature.select = True
        b_armature.show_x_ray = True
        
        #Link object to scene
        scn = bpy.context.scene
        scn.objects.link(b_armature)
        scn.objects.active = b_armature
        
        # make armature editable and create bones
        bpy.ops.object.mode_set(mode='EDIT',toggle=False)
        niChildBones = [child for child in niArmature.children
                        if self.is_bone(child)]
        for niBone in niChildBones:
            self.import_bone(niBone, b_armatureData, niArmature)

        #fix the bone length
        for bone in b_armatureData.edit_bones:
            #don't change Bip01
            if bone.parent:
                if bone.children:
                    childheads = mathutils.Vector()
                    for child in bone.children:
                        childheads += child.head
                    bone_length = (bone.head - childheads/len(bone.children)).length
                    if bone_length < 0.01:
                        bone_length = 0.25
                # end of a chain
                else:
                    bone_length = bone.parent.length
                bone.length = bone_length
        bpy.ops.object.mode_set(mode='OBJECT',toggle=False)

        # The armature has been created in editmode,
        # now we are ready to set the bone keyframes.
        if NifOp.props.animation:
            self.nif_import.animationhelper.armature_animation.import_armature_animation(b_armature)
            
        # constraints (priority)
        # must be done outside edit mode hence after calling
        for bone_name, b_posebone in b_armature.pose.bones.items():
            # find bone nif block
            if bone_name.startswith("InvMarker"):
                bone_name = "InvMarker"
            niBone = self.nif_import.dict_blocks[bone_name]
            # store bone priority, if applicable
            if niBone.name in self.nif_import.dict_bone_priorities:
                # TODO: Still use constraints to store priorities? Maybe use a property instead.
                constr = b_posebone.constraints.new('TRANSFORM')
                constr.name = "priority:%i" % self.nif_import.dict_bone_priorities[niBone.name]
        return b_armature  

    def import_bone(self, n_block, b_armature_data, n_armature):
        """Adds a bone to the armature in edit mode."""
        # check that n_block is indeed a bone
        if not self.is_bone(n_block):
            return None
        
        # bone name
        bone_name = self.nif_import.import_name(n_block)
        # create a new bone
        b_edit_bone = b_armature_data.edit_bones.new(bone_name)
        #Sets active so edit bones are marked selected after import
        b_armature_data.edit_bones.active = b_edit_bone
        # get the nif bone's armature space matrix
        # (under the hood all bone space matrixes are multiplied together)
        n_bind = nif_utils.import_matrix(n_block, relative_to=n_armature)
        #get transformation in blender's coordinate space
        b_bind = nif_utils.nif_bind_to_blender_bind(n_bind)
        #the following is a workaround because blender can no longer set matrices to bones directly
        tail, roll = nif_utils.mat3_to_vec_roll(b_bind.to_3x3())
        b_edit_bone.head = b_bind.to_translation()
        b_edit_bone.tail = tail + b_edit_bone.head
        b_edit_bone.roll = roll
        # import and parent bone children
        for n_child in n_block.children:
            if self.is_bone(n_child):
                b_child_bone = self.import_bone(n_child, b_armature_data, n_armature)
                b_child_bone.parent = b_edit_bone
        return b_edit_bone

        
    def append_armature_modifier(self, b_obj, b_armature):
        """Append an armature modifier for the object."""
        armature_name = b_armature.name
        b_mod = b_obj.modifiers.new(armature_name,'ARMATURE')
        b_mod.object = b_armature
        b_mod.use_bone_envelopes = False
        b_mod.use_vertex_groups = True


    def mark_armatures_bones(self, niBlock):
        """Mark armatures and bones by peeking into NiSkinInstance blocks."""
        # case where we import skeleton only,
        # or importing an Oblivion or Fallout 3 skeleton:
        # do all NiNode's as bones
        if NifOp.props.skeleton == "SKELETON_ONLY" or (
            self.nif_import.data.version in (0x14000005, 0x14020007) and
            (os.path.basename(NifOp.props.filepath).lower()
             in ('skeleton.nif', 'skeletonbeast.nif'))):

            if not isinstance(niBlock, NifFormat.NiNode):
                raise nif_utils.NifError(
                    "cannot import skeleton: root is not a NiNode")
            # for morrowind, take the Bip01 node to be the skeleton root
            if self.nif_import.data.version == 0x04000002:
                skelroot = niBlock.find(block_name='Bip01',
                                        block_type=NifFormat.NiNode)
                if not skelroot:
                    skelroot = niBlock
            else:
                skelroot = niBlock
            if skelroot not in self.nif_import.dict_armatures:
                self.nif_import.dict_armatures[skelroot] = []
            NifLog.info("Selecting node '%s' as skeleton root".format(skelroot.name))
            # add bones
            for bone in skelroot.tree():
                if bone is skelroot:
                    continue
                if not isinstance(bone, NifFormat.NiNode):
                    continue
                if self.nif_import.is_grouping_node(bone):
                    continue
                if bone not in self.nif_import.dict_armatures[skelroot]:
                    self.nif_import.dict_armatures[skelroot].append(bone)
            return # done!

        # attaching to selected armature -> first identify armature and bones
        elif NifOp.props.skeleton == "GEOMETRY_ONLY" and not self.nif_import.dict_armatures:
            skelroot = niBlock.find(
                            block_name=self.nif_import.selected_objects[0].name)
            if not skelroot:
                raise nif_utils.NifError("nif has no armature '%s'" % 
                                    self.nif_import.selected_objects[0].name)
            NifLog.debug("Identified '{0}' as armature".format(skelroot.name))
            self.nif_import.dict_armatures[skelroot] = []
            for bone_name in self.nif_import.selected_objects[0].data.bones.keys():
                # blender bone naming -> nif bone naming
                nif_bone_name = armature.get_bone_name_for_nif(bone_name)
                # find a block with bone name
                bone_block = skelroot.find(block_name=nif_bone_name)
                # add it to the name list if there is a bone with that name
                if bone_block:
                    NifLog.info("Identified nif block '{0}' with bone '{1}' in selected armature".format(nif_bone_name, bone_name))
                    self.nif_import.dict_names[bone_block] = bone_name
                    self.nif_import.dict_armatures[skelroot].append(bone_block)
                    self.complete_bone_tree(bone_block, skelroot)

        # search for all NiTriShape or NiTriStrips blocks...
        if isinstance(niBlock, NifFormat.NiTriBasedGeom):
            # yes, we found one, get its skin instance
            if niBlock.is_skin():
                NifLog.debug("Skin found on block '{0}'".format(niBlock.name))
                # it has a skin instance, so get the skeleton root
                # which is an armature only if it's not a skinning influence
                # so mark the node to be imported as an armature
                skininst = niBlock.skin_instance
                skelroot = skininst.skeleton_root
                if NifOp.props.skeleton == "EVERYTHING":
                    if skelroot not in self.nif_import.dict_armatures:
                        self.nif_import.dict_armatures[skelroot] = []
                        NifLog.debug("'{0}' is an armature".format(skelroot.name))
                elif NifOp.props.skeleton == "GEOMETRY_ONLY":
                    if skelroot not in self.nif_import.dict_armatures:
                        raise nif_utils.NifError(
                            "nif structure incompatible with '%s' as armature:"
                            " node '%s' has '%s' as armature"
                            % (self.nif_import.selected_objects[0].name, niBlock.name,
                               skelroot.name))

                for boneBlock in skininst.bones:
                    # boneBlock can be None; see pyffi issue #3114079
                    if not boneBlock:
                        continue
                    if boneBlock not in self.nif_import.dict_armatures[skelroot]:
                        self.nif_import.dict_armatures[skelroot].append(boneBlock)
                        NifLog.debug("'{0}' is a bone of armature '{1}'".format(boneBlock.name, skelroot.name))
                    # now we "attach" the bone to the armature:
                    # we make sure all NiNodes from this bone all the way
                    # down to the armature NiNode are marked as bones
                    self.complete_bone_tree(boneBlock, skelroot)

                # mark all nodes as bones if asked
                if self.nif_import.IMPORT_EXTRANODES:
                    # add bones
                    for bone in skelroot.tree():
                        if bone is skelroot:
                            continue
                        if not isinstance(bone, NifFormat.NiNode):
                            continue
                        if isinstance(bone, NifFormat.NiLODNode):
                            # LOD nodes are never bones
                            continue
                        if self.nif_import.is_grouping_node(bone):
                            continue
                        if bone not in self.nif_import.dict_armatures[skelroot]:
                            self.nif_import.dict_armatures[skelroot].append(bone)
                            NifLog.debug("'{0}' marked as extra bone of armature '{1}'".format(bone.name, skelroot.name))
                            # we make sure all NiNodes from this bone
                            # all the way down to the armature NiNode
                            # are marked as bones
                            self.complete_bone_tree(bone, skelroot)

        # continue down the tree
        for child in niBlock.get_refs():
            if not isinstance(child, NifFormat.NiAVObject): continue # skip blocks that don't have transforms
            self.mark_armatures_bones(child)

    def complete_bone_tree(self, bone, skelroot):
        """Make sure that the bones actually form a tree all the way
        down to the armature node. Call this function on all bones of
        a skin instance.
        """
        # we must already have marked this one as a bone
        assert skelroot in self.nif_import.dict_armatures # debug
        assert bone in self.nif_import.dict_armatures[skelroot] # debug
        # get the node parent, this should be marked as an armature or as a bone
        boneparent = bone._parent
        if boneparent != skelroot:
            # parent is not the skeleton root
            if boneparent not in self.nif_import.dict_armatures[skelroot]:
                # neither is it marked as a bone: so mark the parent as a bone
                self.nif_import.dict_armatures[skelroot].append(boneparent)
                # store the coordinates for realignement autodetection 
                NifLog.debug("'{0}' is a bone of armature '{1}'".format(boneparent.name, skelroot.name))
            # now the parent is marked as a bone
            # recursion: complete the bone tree,
            # this time starting from the parent bone
            self.complete_bone_tree(boneparent, skelroot)

    def is_bone(self, niBlock):
        """Tests a NiNode to see if it's a bone."""
        if not niBlock :
            return False
        for bones in self.nif_import.dict_armatures.values():
            if niBlock in bones:
                return True
        return False

    def is_armature_root(self, niBlock):
        """Tests a block to see if it's an armature."""
        if isinstance(niBlock, NifFormat.NiNode):
            return  niBlock in self.nif_import.dict_armatures
        return False
        
    def get_closest_bone(self, niBlock, skelroot):
        """Detect closest bone ancestor."""
        par = niBlock._parent
        while par:
            if par == skelroot:
                return None
            if self.is_bone(par):
                return par
            par = par._parent
        return par


    def get_blender_object(self, niBlock):
        """Retrieves the Blender object or Blender bone matching the block."""
        if self.is_bone(niBlock):
            bone_name = self.nif_import.dict_names[niBlock]
            armatureName = None
            for armatureBlock, boneBlocks in self.nif_import.dict_armatures.items():
                if niBlock in boneBlocks:
                    armatureName = self.nif_import.dict_names[armatureBlock]
                    break
                else:
                    raise nif_utils.NifError("cannot find bone '%s'" % bone_name)
            armatureObject = bpy.types.Object(armatureName)
            return armatureObject.data.bones[bone_name]
        else:
            return bpy.types.Object(self.nif_import.dict_names[niBlock])


    def store_names(self):
        """Stores the original, long object names so that they can be
        re-exported. In order for this to work it is necessary to mantain the
        imported names unaltered. Since the text buffer is cleared on each
        import only the last import will be exported correctly."""
        # clear the text buffer, or create new buffer
        try:
            namestxt = bpy.data.texts["FullNames"]
            namestxt.clear()
        except KeyError:
            namestxt = bpy.data.texts.new("FullNames")
            
        # write the names to the text buffer
        for block, shortname in self.nif_import.dict_names.items():
            block_name = block.name.decode()
            if block_name and shortname != block_name:
                namestxt.write('%s;%s\n' % (shortname, block_name))
                
                
