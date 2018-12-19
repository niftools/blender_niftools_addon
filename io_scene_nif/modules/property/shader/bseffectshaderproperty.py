
class BSEffectShaderProperty:

    def __init__(self, b_mat):
        self.b_mat = b_mat

    def import_bseffectshaderproperty(self, bsEffectShaderProperty):

        # diffuse
        texture = bsEffectShaderProperty.source_texture.decode()
        if texture:
            self.import_image_texture(self.b_mat, texture)

        # glow
        texture = bsEffectShaderProperty.greyscale_texture.decode()
        if texture:
            self.import_image_texture(self.b_mat, texture)

        if hasattr(bsEffectShaderProperty, 'uv_offset'):
            self.b_mat = self.import_uv_offset(self.b_mat, bsEffectShaderProperty)

        if hasattr(bsEffectShaderProperty, 'uv_scale'):
            self.b_mat = self.import_uv_scale(self.b_mat, bsEffectShaderProperty)

        self.b_mat = self.import_texture_game_properties(self.b_mat, bsEffectShaderProperty)
