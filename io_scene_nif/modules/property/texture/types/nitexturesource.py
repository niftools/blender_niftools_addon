from io_scene_nif.modules.property.texture.texture_import import TextureSlots
from io_scene_nif.utility.nif_logging import NifLog


class NiTextureProp:
    __instance = None

    @staticmethod
    def get():
        """ Static access method. """
        if NiTextureProp.__instance is None:
            NiTextureProp()
        return NiTextureProp.__instance

    def __init__(self):
        """ Virtually private constructor. """
        if NiTextureProp.__instance is not None:
            raise Exception("This class is a singleton!")
        else:
            NiTextureProp.__instance = self
            self.texture_holder = TextureSlots()

    def import_nitextureprop_textures(self, n_block, b_mat, n_texture_desc):
        NifLog.debug("Importing {0}".format(n_texture_desc))

        if n_texture_desc.has_base_texture:
            base = n_texture_desc.base_texture
            NifLog.debug("Loading base texture {0}".format(base))
            b_texture = self.texture_holder.create_texture_slot(b_mat, base)
            self.texture_holder.update_diffuse_slot(b_texture)

        if n_texture_desc.has_dark_texture:
            dark = n_texture_desc.dark_texture
            NifLog.debug("Loading dark texture {0}".format(dark))
            b_texture = self.texture_holder.create_texture_slot(b_mat, dark)
            self.texture_holder.update_dark_slot(b_texture)

        if n_texture_desc.has_detail_texture:
            detail = n_texture_desc.detail_texture
            NifLog.debug("Loading detail texture {0}".format(detail))
            b_texture = self.texture_holder.create_texture_slot(b_mat, detail)
            self.texture_holder.update_detail_slot_0(b_texture)

        if n_texture_desc.has_bump_map_texture:
            bump = n_texture_desc.bump_map_texture
            NifLog.debug("Loading bump texture {0}".format(bump))
            b_texture = self.texture_holder.create_texture_slot(b_mat, bump)
            self.texture_holder.update_bump_slot(b_texture)
            # TODO [property][texture][map] See if additional information that useful
            # 'bump_map_texture',
            # 'bump_map_luma_scale',
            # 'bump_map_luma_offset',
            # 'bump_map_matrix'

        if n_texture_desc.has_normal_texture:
            normal = n_texture_desc.normal_texture
            NifLog.debug("Loading normal texture {0}".format(normal))
            b_texture = self.texture_holder.create_texture_slot(b_mat, normal)
            self.texture_holder.update_normal_slot(b_texture)

        if n_texture_desc.has_glow_texture:
            glow = n_texture_desc.glow_texture
            NifLog.debug("Loading glow texture {0}".format(glow))
            b_texture = self.texture_holder.create_texture_slot(b_mat, glow)
            self.texture_holder.update_glow_slot(b_texture)

        if n_texture_desc.has_gloss_texture:
            gloss = n_texture_desc.gloss_texture
            NifLog.debug("Loading gloss texture {0}".format(gloss))
            b_texture = self.texture_holder.create_texture_slot(b_mat, gloss)
            self.texture_holder.update_gloss_slot(b_texture)

        if n_texture_desc.has_decal_0_texture:
            decal_0 = n_texture_desc.decal_0_texture
            NifLog.debug("Loading decal 0 texture {0}".format(decal_0))
            b_texture = self.texture_holder.create_texture_slot(b_mat, decal_0)
            self.texture_holder.update_decal_slot_0(b_texture)

        if n_texture_desc.has_decal_1_texture:
            decal_1 = n_texture_desc.decal_1_texture
            NifLog.debug("Loading decal 1 texture {0}".format(decal_1))
            b_texture = self.texture_holder.create_texture_slot(b_mat, decal_1)
            self.texture_holder.update_decal_slot_1(b_texture)

        if n_texture_desc.has_decal_2_texture:
            decal_2 = n_texture_desc.decal_2_texture
            NifLog.debug("Loading decal 2 texture {0}".format(decal_2))
            b_texture = self.texture_holder.create_texture_slot(b_mat, decal_2)
            self.texture_holder.update_decal_slot_2(b_texture)

        # TODO [property][texture][map] Process unknown type
        # 'has_unknown_2_texture',
        # 'unknown_2_texture',
        # 'unknown_2_float',

        self.import_apply_mode(n_texture_desc, b_texture)

    def import_apply_mode(self, n_texture_desc, b_texture):
        # Blend mode
        if hasattr(n_texture_desc, "apply_mode"):
            b_texture.blend_type = TextureSlots.get_b_blend_type_from_n_apply_mode(n_texture_desc.apply_mode)
        else:
            b_texture.blend_type = "MIX"
