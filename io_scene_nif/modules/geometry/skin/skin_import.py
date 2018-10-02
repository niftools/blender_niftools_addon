from pyffi.formats.nif import NifFormat

from io_scene_nif.modules.obj import object_import


class Skin:

    @staticmethod
    def process_geometry_skin(b_obj, n_block, skininst, v_map):
        skindata = skininst.data
        bones = skininst.bones
        bone_weights = skindata.bone_list
        for idx, bone in enumerate(bones):
            # skip empty bones (see pyffi issue #3114079)
            if not bone:
                continue
            vertex_weights = bone_weights[idx].vertex_weights
            groupname = object_import.DICT_NAMES[bone]
            if groupname not in b_obj.vertex_groups.items():
                v_group = b_obj.vertex_groups.new(groupname)
            for skinWeight in vertex_weights:
                vert = skinWeight.index
                weight = skinWeight.weight
                v_group.add([v_map[vert]], weight, 'REPLACE')

        # TODO [geometry]
        # import body parts as vertex groups
        if isinstance(skininst, NifFormat.BSDismemberSkinInstance):
            skinpart_list = []
            bodypart_flag = []
            skinpart = n_block.get_skin_partition()
            for bodypart, skinpartblock in zip(skininst.partitions, skinpart.skin_partition_blocks):
                bodypart_wrap = NifFormat.BSDismemberBodyPartType()
                bodypart_wrap.set_value(bodypart.body_part)
                groupname = bodypart_wrap.get_detail_display()
                # create vertex group if it did not exist yet
                if not (groupname in b_obj.vertex_groups.items()):
                    v_group = b_obj.vertex_groups.new(groupname)
                    skinpart_index = len(skinpart_list)
                    skinpart_list.append((skinpart_index, groupname))
                    bodypart_flag.append(bodypart.part_flag)

                # find vertex indices of this group
                groupverts = [v_map[v_index] for v_index in skinpartblock.vertex_map]
                # create the group
                v_group.add(groupverts, 1, 'ADD')

            b_obj.niftools_part_flags_panel.pf_partcount = len(skinpart_list)
            for i, pl_name in skinpart_list:
                b_obj_partflag = b_obj.niftools_part_flags.add()
                # b_obj.niftools_part_flags.pf_partint = (i)
                b_obj_partflag.name = pl_name
                b_obj_partflag.pf_editorflag = bodypart_flag[i].pf_editor_visible
                b_obj_partflag.pf_startflag = bodypart_flag[i].pf_start_net_boneset
