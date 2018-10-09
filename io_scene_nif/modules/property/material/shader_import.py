from pyffi.formats.nif import NifFormat


def import_uv_offset(b_mat, shader_prop):
    for texture_slot in b_mat.texture_slots:
        if texture_slot:
            texture_slot.offset.x = shader_prop.uv_offset.u
            texture_slot.offset.y = shader_prop.uv_offset.v


def import_uv_scale(b_mat, shader_prop):
    for texture_slot in b_mat.texture_slots:
        if texture_slot:
            texture_slot.scale.x = shader_prop.uv_scale.u
            texture_slot.scale.y = shader_prop.uv_scale.v


def import_clamp(b_mat, shader_prop):
    clamp = shader_prop.texture_clamp_mode
    for texture_slot in b_mat.texture_slots:
        if texture_slot:
            if clamp == 3:
                texture_slot.texture.image.use_clamp_x = False
                texture_slot.texture.image.use_clamp_y = False
            if clamp == 2:
                texture_slot.texture.image.use_clamp_x = False
                texture_slot.texture.image.use_clamp_y = True
            if clamp == 1:
                texture_slot.texture.image.use_clamp_x = True
                texture_slot.texture.image.use_clamp_y = False
            if clamp == 0:
                texture_slot.texture.image.use_clamp_x = True
                texture_slot.texture.image.use_clamp_y = True


# TODO [animation][texture] Move to animation module
def import_texture_game_properties(b_mat, shader_prop):
    for texture_slot in b_mat.texture_slots:
        if texture_slot:
            texture_slot.texture.image.use_animation = True
            texture_slot.texture.image.fps = shader_prop.controller.frequency
            texture_slot.texture.image.frame_start = shader_prop.controller.start_time
            texture_slot.texture.image.frame_end = shader_prop.controller.stop_time


def import_shader_types(b_obj, b_prop):
    if isinstance(b_prop, NifFormat.BSShaderPPLightingProperty):
        b_obj.niftools_shader.bs_shadertype = 'BSShaderPPLightingProperty'
        sf_type = NifFormat.BSShaderType._enumvalues.index(b_prop.shader_type)
        b_obj.niftools_shader.bsspplp_shaderobjtype = NifFormat.BSShaderType._enumkeys[sf_type]
        for b_flag_name in b_prop.shader_flags._names:
            sf_index = b_prop.shader_flags._names.index(b_flag_name)
            if b_prop.shader_flags._items[sf_index]._value == 1:
                b_obj.niftools_shader[b_flag_name] = True

    if isinstance(b_prop, NifFormat.BSLightingShaderProperty):
        b_obj.niftools_shader.bs_shadertype = 'BSLightingShaderProperty'
        sf_type = NifFormat.BSLightingShaderPropertyShaderType._enumvalues.index(b_prop.skyrim_shader_type)
        b_obj.niftools_shader.bslsp_shaderobjtype = NifFormat.BSLightingShaderPropertyShaderType._enumkeys[sf_type]
        import_shader_flags(b_obj, b_prop)

    elif isinstance(b_prop, NifFormat.BSEffectShaderProperty):
        b_obj.niftools_shader.bs_shadertype = 'BSEffectShaderProperty'
        b_obj.niftools_shader.bslsp_shaderobjtype = 'Default'
        import_shader_flags(b_obj, b_prop)


def import_shader_flags(b_obj, b_prop):
    for b_flag_name_1 in b_prop.shader_flags_1._names:
        sf_index = b_prop.shader_flags_1._names.index(b_flag_name_1)
        if b_prop.shader_flags_1._items[sf_index]._value == 1:
            b_obj.niftools_shader[b_flag_name_1] = True
    for b_flag_name_2 in b_prop.shader_flags_2._names:
        sf_index = b_prop.shader_flags_2._names.index(b_flag_name_2)
        if b_prop.shader_flags_2._items[sf_index]._value == 1:
            b_obj.niftools_shader[b_flag_name_2] = True