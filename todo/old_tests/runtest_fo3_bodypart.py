"""Automated body part tests for the blender nif scripts."""

# ***** BEGIN LICENSE BLOCK *****
# 
# BSD License
# 
# Copyright (c) 2005-2011, NIF File Format Library and Tools
# All rights reserved.
# 
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions
# are met:
# 1. Redistributions of source code must retain the above copyright
#    notice, this list of conditions and the following disclaimer.
# 2. Redistributions in binary form must reproduce the above copyright
#    notice, this list of conditions and the following disclaimer in the
#    documentation and/or other materials provided with the distribution.
# 3. The name of the NIF File Format Library and Tools project may not be
#    used to endorse or promote products derived from this software
#    without specific prior written permission.
# 
# THIS SOFTWARE IS PROVIDED BY THE AUTHOR ``AS IS'' AND ANY EXPRESS OR
# IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED WARRANTIES
# OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE DISCLAIMED.
# IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR ANY DIRECT, INDIRECT,
# INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT
# NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE,
# DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY
# THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
# (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF
# THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
#
# ***** END LICENSE BLOCK *****

from itertools import izip

from nif_test import TestSuite
from pyffi.formats.nif import NifFormat
import Blender
import bpy

class BodyPartTestSuite(TestSuite):
    def run(self):
        # create a mesh
        self.info("creating mesh")
        mesh_data = Blender.Mesh.Primitives.Monkey()
        mesh_numverts = len(mesh_data.vertices)
        mesh_obj = self.context.scene.objects.new(mesh_data, "Monkey")
        # create an armature
        self.info("creating armature")
        arm_data = Blender.Armature.Armature("Scene Root")
        arm_data.drawAxes = True
        arm_data.envelopes = False
        arm_data.vertexGroups = True
        arm_data.draw_type = 'STICK'
        arm_obj = self.context.scene.objects.new(arm_data, "Scene Root")
        arm_data.makeEditable()
        bone = Blender.Armature.Editbone()
        arm_data.bones["Bone"] = bone
        arm_data.update()
        # skin the mesh
        self.info("attaching mesh to armature")
        mesh_data.addVertGroup("Bone")
        mesh_data.assignVertsToGroup("Bone", list(range(mesh_numverts)), 1,
                                     Blender.Mesh.AssignModes.REPLACE)
        arm_obj.makeParentDeform([mesh_obj])
        # set body part
        self.info("creating body part vertex group")
        mesh_data.addVertGroup("BP_HEAD")
        mesh_data.assignVertsToGroup("BP_HEAD", list(range(mesh_numverts)), 1,
                                     Blender.Mesh.AssignModes.REPLACE)
        # export (do not advance layer, we will export this again)
        nif_export = self.test(
            filename='test/nif/fo3/_bodypart1.nif',
            config=dict(
                game='FALLOUT_3', EXPORT_SMOOTHOBJECTSEAMS=True,
                EXPORT_FLATTENSKIN=True),
            selection=['Scene Root'],
            next_layer=False)
        # check body part
        self.info("checking for body parts")
        skininst = nif_export.root_blocks[0].find(
            block_type = NifFormat.BSDismemberSkinInstance)
        if not skininst:
            raise ValueError("no body parts found")
        self.info("checking number of body parts")
        if skininst.num_partitions != 1:
            raise ValueError("bad number of body parts")
        if skininst.skin_partition.num_skin_partition_blocks != skininst.num_partitions:
            raise ValueError("num skin partitions do not match num body parts")
        self.info("checking body part indices")
        if skininst.partitions[0].body_part != NifFormat.BSDismemberBodyPartType.BP_HEAD:
            raise ValueError("bad body part type in skin partition")

        # remove a vertex from the body part vertex group
        self.info("removing vertex from vertex group")
        mesh_data.removeVertsFromGroup("BP_HEAD", [0])
        # try to export again, this must fail!
        self.info("check that export fails")
        try:
            nif_export = self.test(
                filename='test/nif/fo3/_bodypart2.nif',
                config=dict(
                    game='FALLOUT_3', EXPORT_SMOOTHOBJECTSEAMS=True,
                    EXPORT_FLATTENSKIN=True),
                selection=['Scene Root'])
        except ValueError:
            pass
        else:
            raise RuntimeError("expected ValueError")
        # add selected vertices from mesh to another group
        self.info("export failed: adding selected vertices to new group")
        mesh_data.addVertGroup("BP_HEAD2")
        mesh_data.assignVertsToGroup("BP_HEAD2",
                                     [vert.index for vert in mesh_data.vertices
                                      if vert.sel],
                                     1, Blender.Mesh.AssignModes.REPLACE)
        # now export must succeed
        nif_export = self.test(
            filename='test/nif/fo3/_bodypart3.nif',
            config=dict(
                game='FALLOUT_3', EXPORT_SMOOTHOBJECTSEAMS=True,
                EXPORT_FLATTENSKIN=True),
            selection=['Scene Root'],
            next_layer=False)

        # check body part
        self.info("checking for body parts")
        skininst = nif_export.root_blocks[0].find(
            block_type = NifFormat.BSDismemberSkinInstance)
        if not skininst:
            raise ValueError("no body parts found")
        self.info("checking number of body parts")
        if skininst.num_partitions != 2:
            raise ValueError("bad number of body parts")
        if skininst.skin_partition.num_skin_partition_blocks != skininst.num_partitions:
            raise ValueError("num skin partitions do not match num body parts")
        self.info("checking body part indices")
        if skininst.partitions[0].body_part != NifFormat.BSDismemberBodyPartType.BP_HEAD:
            raise ValueError("bad body part type in skin partition")
        if skininst.partitions[1].body_part != NifFormat.BSDismemberBodyPartType.BP_HEAD2:
            raise ValueError("bad body part type in skin partition")

        # export without body parts
        nif_export = self.test(
            filename='test/nif/fo3/_bodypart4.nif',
            config=dict(
                game='FALLOUT_3', EXPORT_SMOOTHOBJECTSEAMS=True,
                EXPORT_FLATTENSKIN=True, EXPORT_FO3_BODYPARTS=False),
            selection=['Scene Root'])
        # check that skinning is exported without body parts
        self.info("checking that there are no body parts")
        if nif_export.root_blocks[0].find(
            block_type=NifFormat.BSDismemberSkinInstance):
            raise ValueError("body part found even though they were disabled on export")
        if not nif_export.root_blocks[0].find(
            block_type=NifFormat.NiSkinInstance):
            raise ValueError("no skinning exported")

suite = BodyPartTestSuite("bodypart")
suite.run()
