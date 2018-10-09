
class BSShaderProperty:

    def __init__(self, b_mat_texslot, bs_shader_prop):
        self.b_mat_texslot = b_mat_texslot
        self.bs_shader_prop = bs_shader_prop

    def import_bsshaderproperty(self):

        # diffuse
        texture = self.bs_shader_prop.texture_set.textures[0].decode()
        if texture:
            self.import_image_texture(self.b_mat_texslot, texture)

        # normal
        texture = self.bs_shader_prop.texture_set.textures[1].decode()
        if texture:
            self.import_image_texture(self.b_mat_texslot, texture)

        # glow
        texture = self.bs_shader_prop.texture_set.textures[2].decode()
        if texture:
            self.import_image_texture(self.b_mat_texslot, texture)

        # detail
        texture = self.bs_shader_prop.texture_set.textures[3].decode()
        if texture:
            self.import_image_texture(self.b_mat_texslot, texture)

        if len(self.bs_shader_prop.texture_set.textures) > 6:
            # decal
            texture = self.bs_shader_prop.texture_set.textures[6].decode()
            if texture:
                self.import_image_texture(self.b_mat_texslot, texture)

            # gloss
            texture = self.bs_shader_prop.texture_set.textures[7].decode()
            if texture:
                self.import_image_texture(self.b_mat_texslot, texture)

        if hasattr(self.bs_shader_prop, 'texture_clamp_mode'):
            self.b_mat_texslot = self.import_clamp(self.b_mat_texslot, self.bs_shader_prop)
        if hasattr(self.bs_shader_prop, 'uv_offset'):
            self.b_mat_texslot = self.import_uv_offset(self.b_mat_texslot, self.bs_shader_prop)
        if hasattr(self.bs_shader_prop, 'uv_scale'):
            self.b_mat_texslot = self.import_uv_scale(self.b_mat_texslot, self.bs_shader_prop)