"""This module contains helper methods to export skin partitions from pyffi"""
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

import logging
import pyffi
from pyffi.formats.nif import NifFormat


def update_skin_partition(self,
                        maxbonesperpartition=4, maxbonespervertex=4,
                        verbose=0, stripify=True, stitchstrips=False,
                        padbones=False,
                        triangles=None, trianglepartmap=None,
                        maximize_bone_sharing=False,
                        part_sort_order=[]):
    """Recalculate skin partition data.

    :deprecated: Do not use the verbose argument.
    :param maxbonesperpartition: Maximum number of bones in each partition.
        The num_bones field will not exceed this number.
    :param maxbonespervertex: Maximum number of bones per vertex.
        The num_weights_per_vertex field will be exactly equal to this number.
    :param verbose: Ignored, and deprecated. Set pyffi's log level instead.
    :param stripify: If true, stripify the partitions, otherwise use triangles.
    :param stitchstrips: If stripify is true, then set this to true to stitch
        the strips.
    :param padbones: Enforces the numbones field to be equal to
        maxbonesperpartition. Also ensures that the bone indices are unique
        and sorted, per vertex. Raises an exception if maxbonespervertex
        is not equal to maxbonesperpartition (in that case bone indices cannot
        be unique and sorted). This options is required for Freedom Force vs.
        the 3rd Reich skin partitions.
    :param triangles: The triangles of the partition (if not specified, then
        this defaults to C{self.data.get_triangles()}.
    :param trianglepartmap: Maps each triangle to a partition index. Faces with
        different indices will never appear in the same partition. If the skin
        instance is a BSDismemberSkinInstance, then these indices are used as
        body part types, and the partitions in the BSDismemberSkinInstance are
        updated accordingly. Note that the faces are counted relative to
        L{triangles}.
    :param maximize_bone_sharing: Maximize bone sharing between partitions.
        This option is useful for Fallout 3.
    :param part_sort_order: List of body part numbers in the order in which
        they should appear, e.g. [5, 3, 6]. The first entry is counted. When
        maximize_bone_sharing is true, sorts the parts within the shared bones,
        and sorts the shared bone lists based on its first body part.
    """
    logger = logging.getLogger("pyffi.nif.nitribasedgeom")

    # if trianglepartmap not specified, map everything to index 0
    if trianglepartmap is None:
        trianglepartmap = repeat(0)

    # shortcuts relevant blocks
    if not self.skin_instance:
        # no skin, nothing to do
        return
    self._validate_skin()
    geomdata = self.data
    skininst = self.skin_instance
    skindata = skininst.data

    # get skindata vertex weights
    logger.debug("Getting vertex weights.")
    weights = self.get_vertex_weights()

    # count minimum and maximum number of bones per vertex
    minbones = min(len(weight) for weight in weights)
    maxbones = max(len(weight) for weight in weights)
    if minbones <= 0:
        noweights = [v for v, weight in enumerate(weights)
                     if not weight]
        #raise ValueError(
        logger.warn(
            'bad NiSkinData: some vertices have no weights %s'
            % noweights)
    logger.info("Counted minimum of %i and maximum of %i bones per vertex"
                % (minbones, maxbones))

    # reduce bone influences to meet maximum number of bones per vertex
    logger.info("Imposing maximum of %i bones per vertex." % maxbonespervertex)
    lostweight = 0.0
    for weight in weights:
        if len(weight) > maxbonespervertex:
            # delete bone influences with least weight
            weight.sort(key=lambda x: x[1], reverse=True) # sort by weight
            # save lost weight to return to user
            lostweight = max(
                lostweight, max(
                    [x[1] for x in weight[maxbonespervertex:]]))
            del weight[maxbonespervertex:] # only keep first elements
            # normalize
            totalweight = sum([x[1] for x in weight]) # sum of all weights
            for x in weight: x[1] /= totalweight
            maxbones = maxbonespervertex
        # sort by again by bone (relied on later when matching vertices)
        weight.sort(key=lambda x: x[0])

    # reduce bone influences to meet maximum number of bones per partition
    # (i.e. maximum number of bones per triangle)
    logger.info(
        "Imposing maximum of %i bones per triangle (and hence, per partition)."
        % maxbonesperpartition)

    if triangles is None:
        triangles = geomdata.get_triangles()

    for tri in triangles:
        while True:
            # find the bones influencing this triangle
            tribones = []
            for t in tri:
                tribones.extend([bonenum for bonenum, boneweight in weights[t]])
            tribones = set(tribones)
            # target met?
            if len(tribones) <= maxbonesperpartition:
                break
            # no, need to remove a bone

            # sum weights for each bone to find the one that least influences
            # this triangle
            tribonesweights = {}
            for bonenum in tribones: tribonesweights[bonenum] = 0.0
            nono = set() # bones with weight 1 cannot be removed
            for skinweights in [weights[t] for t in tri]:
                # skinweights[0] is the first skinweight influencing vertex t
                # and skinweights[0][0] is the bone number of that bone
                if len(skinweights) == 1: nono.add(skinweights[0][0])
                for bonenum, boneweight in skinweights:
                    tribonesweights[bonenum] += boneweight

            # select a bone to remove
            # first find bones we can remove

            # restrict to bones not in the nono set
            tribonesweights = [
                x for x in list(tribonesweights.items()) if x[0] not in nono]
            if not tribonesweights:
                raise ValueError(
                    "cannot remove anymore bones in this skin; "
                    "increase maxbonesperpartition and try again")
            # sort by vertex weight sum the last element of this list is now a
            # candidate for removal
            tribonesweights.sort(key=lambda x: x[1], reverse=True)
            minbone = tribonesweights[-1][0]

            # remove minbone from all vertices of this triangle and from all
            # matching vertices
            for t in tri:
                for tt in [t]: #match[t]:
                    # remove bone
                    weight = weights[tt]
                    for i, (bonenum, boneweight) in enumerate(weight):
                        if bonenum == minbone:
                            # save lost weight to return to user
                            lostweight = max(lostweight, boneweight)
                            del weight[i]
                            break
                    else:
                        continue
                    # normalize
                    totalweight = sum([x[1] for x in weight])
                    for x in weight:
                        x[1] /= totalweight

    # split triangles into partitions
    logger.info("Creating partitions")
    parts = []
    # keep creating partitions as long as there are triangles left
    while triangles:
        # create a partition
        part = [set(), [], None] # bones, triangles, partition index
        usedverts = set()
        addtriangles = True
        # keep adding triangles to it as long as the flag is set
        while addtriangles:
            # newtriangles is a list of triangles that have not been added to
            # the partition, similar for newtrianglepartmap
            newtriangles = []
            newtrianglepartmap = []
            for tri, partindex in zip(triangles, trianglepartmap):
                # find the bones influencing this triangle
                tribones = []
                for t in tri:
                    tribones.extend([
                        bonenum for bonenum, boneweight in weights[t]])
                tribones = set(tribones)
                # if part has no bones,
                # or if part has all bones of tribones and index coincides
                # then add this triangle to this part
                if ((not part[0])
                    or ((part[0] >= tribones) and (part[2] == partindex))):
                    part[0] |= tribones
                    part[1].append(tri)
                    usedverts |= set(tri)
                    # if part was empty, assign it the index
                    if part[2] is None:
                        part[2] = partindex
                else:
                    newtriangles.append(tri)
                    newtrianglepartmap.append(partindex)
            triangles = newtriangles
            trianglepartmap = newtrianglepartmap

            # if we have room left in the partition
            # then add adjacent triangles
            addtriangles = False
            newtriangles = []
            newtrianglepartmap = []
            if len(part[0]) < maxbonesperpartition:
                for tri, partindex in zip(triangles, trianglepartmap):
                    # if triangle is adjacent, and has same index
                    # then check if it can be added to the partition
                    if (usedverts & set(tri)) and (part[2] == partindex):
                        # find the bones influencing this triangle
                        tribones = []
                        for t in tri:
                            tribones.extend([
                                bonenum for bonenum, boneweight in weights[t]])
                        tribones = set(tribones)
                        # and check if we exceed the maximum number of allowed
                        # bones
                        if len(part[0] | tribones) <= maxbonesperpartition:
                            part[0] |= tribones
                            part[1].append(tri)
                            usedverts |= set(tri)
                            # signal another try in adding triangles to
                            # the partition
                            addtriangles = True
                        else:
                            newtriangles.append(tri)
                            newtrianglepartmap.append(partindex)
                    else:
                        newtriangles.append(tri)
                        newtrianglepartmap.append(partindex)
                triangles = newtriangles
                trianglepartmap = newtrianglepartmap

        parts.append(part)

    logger.info("Created %i small partitions." % len(parts))

    # merge all partitions
    logger.info("Merging partitions.")
    merged = True # signals success, in which case do another run
    while merged:
        merged = False
        # newparts is to contain the updated merged partitions as we go
        newparts = []
        # addedparts is the set of all partitions from parts that have been
        # added to newparts
        addedparts = set()
        # try all combinations
        for a, parta in enumerate(parts):
            if a in addedparts:
                continue
            newparts.append(parta)
            addedparts.add(a)
            for b, partb in enumerate(parts):
                if b <= a:
                    continue
                if b in addedparts:
                    continue
                # if partition indices are the same, and bone limit is not
                # exceeded, merge them
                if ((parta[2] == partb[2])
                    and (len(parta[0] | partb[0]) <= maxbonesperpartition)):
                    parta[0] |= partb[0]
                    parta[1] += partb[1]
                    addedparts.add(b)
                    merged = True # signal another try in merging partitions
        # update partitions to the merged partitions
        parts = newparts

    # write the NiSkinPartition
    logger.info("Skin has %i partitions." % len(parts))

    # if skin partition already exists, use it
    if skindata.skin_partition != None:
        skinpart = skindata.skin_partition
        skininst.skin_partition = skinpart
    elif skininst.skin_partition != None:
        skinpart = skininst.skin_partition
        skindata.skin_partition = skinpart
    else:
    # otherwise, create a new block and link it
        skinpart = NifFormat.NiSkinPartition()
        skindata.skin_partition = skinpart
        skininst.skin_partition = skinpart

    # set number of partitions
    skinpart.num_skin_partition_blocks = len(parts)
    skinpart.skin_partition_blocks.update_size()

    # maximize bone sharing, if requested
    if maximize_bone_sharing:
        logger.info("Maximizing shared bones.")
        # new list of partitions, sorted to maximize bone sharing
        newparts = []
        # as long as there are parts to add
        while parts:
            # current set of partitions with shared bones
            # starts a new set of partitions with shared bones
            sharedparts = [parts.pop()]
            sharedboneset = sharedparts[0][0]
            # go over all other partitions, and try to add them with
            # shared bones
            oldparts = parts[:]
            parts = []
            for otherpart in oldparts:
                # check if bones can be added
                if len(sharedboneset | otherpart[0]) <= maxbonesperpartition:
                    # ok, we can share bones!
                    # update set of shared bones
                    sharedboneset |= otherpart[0]
                    # add this other partition to list of shared parts
                    sharedparts.append(otherpart)
                    # update bone set in all shared parts
                    for sharedpart in sharedparts:
                        sharedpart[0] = sharedboneset
                else:
                    # not added to sharedparts,
                    # so we must keep it for the next iteration
                    parts.append(otherpart)
            # update list of partitions
            newparts.extend(sharedparts)

        # store update
        parts = newparts

    # sort the parts based on the given list
    if part_sort_order:
        # build a map of body parts to sorted order
        body_part_order_map = {}
        sorted_index = 0
        for body_part_number in part_sort_order:
            if body_part_number in body_part_order_map:
                continue
            else:
                body_part_order_map[body_part_number] = sorted_index
                sorted_index += 1
        # assign an sorted index to any number that was missed
        for part in parts:
            if part[2] in body_part_order_map:
                continue
            else:
                body_part_order_map[part[2]] = sorted_index
                sorted_index += 1
        # order by the index associated with the body part
        if maximize_bone_sharing:
            # first sort within the bonesets
            shared_boneset_start = 0
            shared_boneset_end = 1
            bone_sharing_lists = []
            while shared_boneset_end <= len(parts):
                added = True
                bones = parts[shared_boneset_start][0]
                while added and shared_boneset_end < len(parts):
                    added = False
                    if len(bones | parts[shared_boneset_end][0]) == len(bones):
                        shared_boneset_end += 1
                        added = True
                    else:
                        break
                parts[shared_boneset_start:shared_boneset_end] = sorted(
                            parts[shared_boneset_start:shared_boneset_end],
                            key = lambda part: body_part_order_map[part[2]])
                bone_sharing_lists.append([list(range(shared_boneset_start,
                            shared_boneset_end)),
                            body_part_order_map[parts[shared_boneset_start][2]]])
                shared_boneset_start = shared_boneset_end
                shared_boneset_end = shared_boneset_start + 1
            # then sort the bonesets based on their first entry's body part
            bone_sharing_lists = sorted(bone_sharing_lists,
                        key = lambda x: x[1])
            bone_sharing_lists = [entry[0] for entry in bone_sharing_lists]
            # flatten the indices into a list of the old indices
            new_part_indices = [index for sublist in bone_sharing_lists for index in sublist]
            parts = [parts[i] for i in new_part_indices]
        else:
            parts = sorted(parts,
                        key = lambda part: body_part_order_map[part[2]])

    # for Fallout 3, set dismember partition indices
    if isinstance(skininst, NifFormat.BSDismemberSkinInstance):
        skininst.num_partitions = len(parts)
        skininst.partitions.update_size()
        lastpart = None
        for bodypart, part in zip(skininst.partitions, parts):
            bodypart.body_part = part[2]
            if (lastpart is None) or (lastpart[0] != part[0]):
                # start new bone set, if bones are not shared
                bodypart.part_flag.pf_start_net_boneset = 1
            else:
                # do not start new bone set
                bodypart.part_flag.pf_start_net_boneset = 0
            # caps are invisible
            bodypart.part_flag.pf_editor_visible = (part[2] < 100
                                                 or part[2] >= 1000)
            # store part for next iteration
            lastpart = part

    for skinpartblock, part in zip(skinpart.skin_partition_blocks, parts):
        # get sorted list of bones
        bones = sorted(list(part[0]))
        triangles = part[1]
        logger.info("Optimizing triangle ordering in partition %i"
                    % parts.index(part))
        # optimize triangles for vertex cache and calculate strips
        triangles = pyffi.utils.vertex_cache.get_cache_optimized_triangles(
            triangles)
        strips = pyffi.utils.vertex_cache.stable_stripify(
            triangles, stitchstrips=stitchstrips)
        triangles_size = 3 * len(triangles)
        strips_size = len(strips) + sum(len(strip) for strip in strips)
        vertices = []
        # decide whether to use strip or triangles as primitive
        if stripify is None:
            stripifyblock = (
                strips_size < triangles_size
                and all(len(strip) < 65536 for strip in strips))
        else:
            stripifyblock = stripify
        if stripifyblock:
            # stripify the triangles
            # also update triangle list
            numtriangles = 0
            # calculate number of triangles and get sorted
            # list of vertices
            # for optimal performance, vertices must be sorted
            # by strip
            for strip in strips:
                numtriangles += len(strip) - 2
                for t in strip:
                    if t not in vertices:
                        vertices.append(t)
        else:
            numtriangles = len(triangles)
            # get sorted list of vertices
            # for optimal performance, vertices must be sorted
            # by triangle
            for tri in triangles:
                for t in tri:
                    if t not in vertices:
                        vertices.append(t)
        # set all the data
        skinpartblock.num_vertices = len(vertices)
        skinpartblock.num_triangles = numtriangles
        if not padbones:
            skinpartblock.num_bones = len(bones)
        else:
            if maxbonesperpartition != maxbonespervertex:
                raise ValueError(
                    "when padding bones maxbonesperpartition must be "
                    "equal to maxbonespervertex")
            # freedom force vs. the 3rd reich needs exactly 4 bones per
            # partition on every partition block
            skinpartblock.num_bones = maxbonesperpartition
        if stripifyblock:
            skinpartblock.num_strips = len(strips)
        else:
            skinpartblock.num_strips = 0
        # maxbones would be enough as num_weights_per_vertex but the Gamebryo
        # engine doesn't like that, it seems to want exactly 4 even if there
        # are fewer
        skinpartblock.num_weights_per_vertex = maxbonespervertex
        skinpartblock.bones.update_size()
        for i, bonenum in enumerate(bones):
            skinpartblock.bones[i] = bonenum
        for i in range(len(bones), skinpartblock.num_bones):
            skinpartblock.bones[i] = 0 # dummy bone slots refer to first bone
        skinpartblock.has_vertex_map = True
        skinpartblock.vertex_map.update_size()
        for i, v in enumerate(vertices):
            skinpartblock.vertex_map[i] = v
        skinpartblock.has_vertex_weights = True
        skinpartblock.vertex_weights.update_size()
        for i, v in enumerate(vertices):
            for j in range(skinpartblock.num_weights_per_vertex):
                if j < len(weights[v]):
                    skinpartblock.vertex_weights[i][j] = weights[v][j][1]
                else:
                    skinpartblock.vertex_weights[i][j] = 0.0
        if stripifyblock:
            skinpartblock.has_faces = True
            skinpartblock.strip_lengths.update_size()
            for i, strip in enumerate(strips):
                skinpartblock.strip_lengths[i] = len(strip)
            skinpartblock.strips.update_size()
            for i, strip in enumerate(strips):
                for j, v in enumerate(strip):
                    skinpartblock.strips[i][j] = vertices.index(v)
        else:
            skinpartblock.has_faces = True
            # clear strip lengths array
            skinpartblock.strip_lengths.update_size()
            # clear strips array
            skinpartblock.strips.update_size()
            skinpartblock.triangles.update_size()
            for i, (v_1,v_2,v_3) in enumerate(triangles):
                skinpartblock.triangles[i].v_1 = vertices.index(v_1)
                skinpartblock.triangles[i].v_2 = vertices.index(v_2)
                skinpartblock.triangles[i].v_3 = vertices.index(v_3)
        skinpartblock.has_bone_indices = True
        skinpartblock.bone_indices.update_size()
        for i, v in enumerate(vertices):
            # the boneindices set keeps track of indices that have not been
            # used yet
            boneindices = set(range(skinpartblock.num_bones))
            for j in range(len(weights[v])):
                skinpartblock.bone_indices[i][j] = bones.index(weights[v][j][0])
                boneindices.remove(skinpartblock.bone_indices[i][j])
            for j in range(len(weights[v]),skinpartblock.num_weights_per_vertex):
                if padbones:
                    # if padbones is True then we have enforced
                    # num_bones == num_weights_per_vertex so this will not trigger
                    # a KeyError
                    skinpartblock.bone_indices[i][j] = boneindices.pop()
                else:
                    skinpartblock.bone_indices[i][j] = 0

        # sort weights
        for i, v in enumerate(vertices):
            vweights = []
            for j in range(skinpartblock.num_weights_per_vertex):
                vweights.append([
                    skinpartblock.bone_indices[i][j],
                    skinpartblock.vertex_weights[i][j]])
            if padbones:
                # by bone index (for ffvt3r)
                vweights.sort(key=lambda w: w[0])
            else:
                # by weight (for fallout 3, largest weight first)
                vweights.sort(key=lambda w: -w[1])
            for j in range(skinpartblock.num_weights_per_vertex):
                skinpartblock.bone_indices[i][j] = vweights[j][0]
                skinpartblock.vertex_weights[i][j] = vweights[j][1]

    return lostweight
