# --------------------------------------------------------------------------
# nif4.py: a python interface for reading, writing, and printing
#          NetImmerse 4.0.0.2 files (.nif & .kf)
# --------------------------------------------------------------------------
# ***** BEGIN BSD LICENSE BLOCK *****
#
# Copyright (c) 2005, NIF File Format Library and Tools
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
# ***** END BSD LICENCE BLOCK *****
# --------------------------------------------------------------------------
# Notes:
#
# - This file was generated from a database, and as a result, the code
#   is highly unoptimized.
# - Not all of the known code blocks are recognized. However, it should
#   process most static models. See 'read' member of the 'NIF' class for a
#   list of supported block types.
# - Happy modding!
#

import struct


MAX_ARRAYDUMPSIZE = 8 # we shall not dump arrays that have more elements than this number

MAX_STRLEN = 256 # reading/writing strings longer than this number will raise an exception

MAX_ARRAYSIZE = 1048576 # reading/writing arrays that have more elements than this number will raise an exception

MAX_HEXDUMP = 128 # number of bytes that should be dumped if something goes wrong (set to 0 to turn off hex dumping)

#
# A simple custom exception class
#
class NIFError(Exception):
    def __init__(self, value):
        self.value = value
    def __str__(self):
        return repr(self.value)



#
# List of three vertex indices.
#
class face:
    # constructor
    def __init__(self):
        # First vertex index.
        self.v1 = 0
        # Second vertex index.
        self.v2 = 0
        # Third vertex index.
        self.v3 = 0



    # read from file
    def read(self, file):
        self.v1, = struct.unpack('<H', file.read(2))
        self.v2, = struct.unpack('<H', file.read(2))
        self.v3, = struct.unpack('<H', file.read(2))



    # write to file
    def write(self, file):
        file.write(struct.pack('<H', self.v1))
        file.write(struct.pack('<H', self.v2))
        file.write(struct.pack('<H', self.v3))



    # dump to screen
    def __str__(self):
        s = ''
        s += 'v1' + ': %i\n'%self.v1
        s += 'v2' + ': %i\n'%self.v2
        s += 'v3' + ': %i\n'%self.v3
        return s



#
# List of block indices.
#
class indexlist:
    # constructor
    def __init__(self):
        # Number of block indices.
        self.num_indices = 0
        # The list of block indices.
        self.indices = [ None ] * self.num_indices
        for count in range(self.num_indices): self.indices[count] = -1



    # read from file
    def read(self, file):
        self.num_indices, = struct.unpack('<I', file.read(4))
        if (self.num_indices > MAX_ARRAYSIZE): raise NIFError('array size unreasonably large (size %i)'%self.num_indices)
        self.indices = [ None ] * self.num_indices
        for count in range(self.num_indices): self.indices[count] = -1
        for count in range(self.num_indices):
            self.indices[count], = struct.unpack('<i', file.read(4))



    # write to file
    def write(self, file):
        file.write(struct.pack('<I', self.num_indices))
        if (self.num_indices > MAX_ARRAYSIZE): raise NIFError('array size unreasonably large (size %i)'%self.num_indices)
        for count in range(self.num_indices):
            file.write(struct.pack('<i', self.indices[count]))



    # dump to screen
    def __str__(self):
        s = ''
        s += 'num_indices' + ': %i\n'%self.num_indices
        if (self.num_indices <= MAX_ARRAYDUMPSIZE):
            for count in range(self.num_indices):
                s += 'indices' + '[%i]'%count + ': %i\n'%self.indices[count]
        else:
            s += 'indices: array[%i]\n'%self.num_indices
        return s



#
# A visibility animation key.
#
class keyvis:
    # constructor
    def __init__(self):
        # Key time.
        self.time = 0.0
        # Visibility flag.
        self.is_visible = 0



    # read from file
    def read(self, file):
        self.time, = struct.unpack('<f', file.read(4))
        self.is_visible, = struct.unpack('<B', file.read(1))



    # write to file
    def write(self, file):
        file.write(struct.pack('<f', self.time))
        file.write(struct.pack('<b', self.is_visible))



    # dump to screen
    def __str__(self):
        s = ''
        s += 'time' + ': %f\n'%self.time
        s += 'is_visible' + ': %i\n'%self.is_visible
        return s



#
# Group of vertex indices of vertices that match.
#
class matchgroup:
    # constructor
    def __init__(self):
        # Number of vertices in this group.
        self.num_vertices = 0
        # The vertex indices.
        self.vertex_indices = [ None ] * self.num_vertices
        for count in range(self.num_vertices): self.vertex_indices[count] = 0



    # read from file
    def read(self, file):
        self.num_vertices, = struct.unpack('<H', file.read(2))
        if (self.num_vertices > MAX_ARRAYSIZE): raise NIFError('array size unreasonably large (size %i)'%self.num_vertices)
        self.vertex_indices = [ None ] * self.num_vertices
        for count in range(self.num_vertices): self.vertex_indices[count] = 0
        for count in range(self.num_vertices):
            self.vertex_indices[count], = struct.unpack('<H', file.read(2))



    # write to file
    def write(self, file):
        file.write(struct.pack('<H', self.num_vertices))
        if (self.num_vertices > MAX_ARRAYSIZE): raise NIFError('array size unreasonably large (size %i)'%self.num_vertices)
        for count in range(self.num_vertices):
            file.write(struct.pack('<H', self.vertex_indices[count]))



    # dump to screen
    def __str__(self):
        s = ''
        s += 'num_vertices' + ': %i\n'%self.num_vertices
        if (self.num_vertices <= MAX_ARRAYDUMPSIZE):
            for count in range(self.num_vertices):
                s += 'vertex_indices' + '[%i]'%count + ': %i\n'%self.vertex_indices[count]
        else:
            s += 'vertex_indices: array[%i]\n'%self.num_vertices
        return s



#
# Morph data keyframe.
#
class morphframe:
    # constructor
    def __init__(self):
        # Key time.
        self.time = 0.0
        # Key data.
        self.data = 0.0
        # Forward tangent.
        self.forward = 0.0
        # Backward tangent.
        self.backward = 0.0



    # read from file
    def read(self, file):
        self.time, = struct.unpack('<f', file.read(4))
        self.data, = struct.unpack('<f', file.read(4))
        self.forward, = struct.unpack('<f', file.read(4))
        self.backward, = struct.unpack('<f', file.read(4))



    # write to file
    def write(self, file):
        file.write(struct.pack('<f', self.time))
        file.write(struct.pack('<f', self.data))
        file.write(struct.pack('<f', self.forward))
        file.write(struct.pack('<f', self.backward))



    # dump to screen
    def __str__(self):
        s = ''
        s += 'time' + ': %f\n'%self.time
        s += 'data' + ': %f\n'%self.data
        s += 'forward' + ': %f\n'%self.forward
        s += 'backward' + ': %f\n'%self.backward
        return s



#
# A quaternion.
#
class quaternion:
    # constructor
    def __init__(self):
        # The w-coordinate.
        self.w = 0.0
        # The x-coordinate.
        self.x = 0.0
        # The y-coordinate.
        self.y = 0.0
        # The z-coordinate.
        self.z = 0.0



    # read from file
    def read(self, file):
        self.w, = struct.unpack('<f', file.read(4))
        self.x, = struct.unpack('<f', file.read(4))
        self.y, = struct.unpack('<f', file.read(4))
        self.z, = struct.unpack('<f', file.read(4))



    # write to file
    def write(self, file):
        file.write(struct.pack('<f', self.w))
        file.write(struct.pack('<f', self.x))
        file.write(struct.pack('<f', self.y))
        file.write(struct.pack('<f', self.z))



    # dump to screen
    def __str__(self):
        s = ''
        s += 'w' + ': %f\n'%self.w
        s += 'x' + ': %f\n'%self.x
        s += 'y' + ': %f\n'%self.y
        s += 'z' + ': %f\n'%self.z
        return s



#
# Red, green, blue color triple.
#
class rgb:
    # constructor
    def __init__(self):
        # Red.
        self.r = 0.0
        # Green.
        self.g = 0.0
        # Blue.
        self.b = 0.0



    # read from file
    def read(self, file):
        self.r, = struct.unpack('<f', file.read(4))
        self.g, = struct.unpack('<f', file.read(4))
        self.b, = struct.unpack('<f', file.read(4))



    # write to file
    def write(self, file):
        file.write(struct.pack('<f', self.r))
        file.write(struct.pack('<f', self.g))
        file.write(struct.pack('<f', self.b))



    # dump to screen
    def __str__(self):
        s = ''
        s += 'r' + ': %f\n'%self.r
        s += 'g' + ': %f\n'%self.g
        s += 'b' + ': %f\n'%self.b
        return s



#
# A red, green, blue, alpha color quad.
#
class rgba:
    # constructor
    def __init__(self):
        # Red component.
        self.r = 0.0
        # Green component.
        self.g = 0.0
        # Blue component.
        self.b = 0.0
        # Alpha.
        self.a = 0.0



    # read from file
    def read(self, file):
        self.r, = struct.unpack('<f', file.read(4))
        self.g, = struct.unpack('<f', file.read(4))
        self.b, = struct.unpack('<f', file.read(4))
        self.a, = struct.unpack('<f', file.read(4))



    # write to file
    def write(self, file):
        file.write(struct.pack('<f', self.r))
        file.write(struct.pack('<f', self.g))
        file.write(struct.pack('<f', self.b))
        file.write(struct.pack('<f', self.a))



    # dump to screen
    def __str__(self):
        s = ''
        s += 'r' + ': %f\n'%self.r
        s += 'g' + ': %f\n'%self.g
        s += 'b' + ': %f\n'%self.b
        s += 'a' + ': %f\n'%self.a
        return s



#
# A color animation key.
#
class keyrgba:
    # constructor
    def __init__(self):
        # The key time.
        self.time = 0.0
        # The key color.
        self.color = rgba()



    # read from file
    def read(self, file):
        self.time, = struct.unpack('<f', file.read(4))
        self.color = rgba()
        self.color.read(file)



    # write to file
    def write(self, file):
        file.write(struct.pack('<f', self.time))
        self.color.write(file)



    # dump to screen
    def __str__(self):
        s = ''
        s += 'time' + ': %f\n'%self.time
        s += 'color' + ':\n'
        s += str(self.color) + '\n'
        return s



#
# A string type.
#
class string:
    # constructor
    def __init__(self):
        # The string length.
        self.length = 0
        # The string itself.
        self.value = ' ' * self.length



    # read from file
    def read(self, file):
        self.length, = struct.unpack('<I', file.read(4))
        if (self.length > MAX_ARRAYSIZE): raise NIFError('array size unreasonably large (size %i)'%self.length)
        self.value = ' ' * self.length
        if (self.length > MAX_STRLEN): raise NIFError('string unreasonably long (size %i)'%self.length)
        self.value, = struct.unpack('<%us'%self.length, file.read(self.length))



    # write to file
    def write(self, file):
        file.write(struct.pack('<I', self.length))
        if (self.length > MAX_ARRAYSIZE): raise NIFError('array size unreasonably large (size %i)'%self.length)
        file.write(struct.pack('<%us'%self.length, self.value))



    # dump to screen
    def __str__(self):
        s = ''
        s += 'length' + ': %i\n'%self.length
        s += 'value' + ': %s\n'%self.value
        return s



#
# A string animation key - Used to identify animation groups and trigger
# sounds.
#
class keystring:
    # constructor
    def __init__(self):
        # Time in the overall animation that this textual note takes effect.
        self.time = 0.0
        # Note text.
        self.name = string()



    # read from file
    def read(self, file):
        self.time, = struct.unpack('<f', file.read(4))
        self.name = string()
        self.name.read(file)



    # write to file
    def write(self, file):
        file.write(struct.pack('<f', self.time))
        self.name.write(file)



    # dump to screen
    def __str__(self):
        s = ''
        s += 'time' + ': %f\n'%self.time
        s += 'name' + ':\n'
        s += str(self.name) + '\n'
        return s



#
# Tension, bias, continuity.
#
class tbc:
    # constructor
    def __init__(self):
        # Tension.
        self.t = 0.0
        # Bias.
        self.b = 0.0
        # Continuity.
        self.c = 0.0



    # read from file
    def read(self, file):
        self.t, = struct.unpack('<f', file.read(4))
        self.b, = struct.unpack('<f', file.read(4))
        self.c, = struct.unpack('<f', file.read(4))



    # write to file
    def write(self, file):
        file.write(struct.pack('<f', self.t))
        file.write(struct.pack('<f', self.b))
        file.write(struct.pack('<f', self.c))



    # dump to screen
    def __str__(self):
        s = ''
        s += 't' + ': %f\n'%self.t
        s += 'b' + ': %f\n'%self.b
        s += 'c' + ': %f\n'%self.c
        return s



#
# A float animation key.
#
class keyfloat:
    # constructor
    def __init__(self, init_arg):
        # Type of key.
        self.key_type = init_arg
        # Time.
        self.time = 0.0
        # Float value.
        self.value = 0.0
        # Forward tangent.
        self.forward = 0.0
        # Backward tangent.
        self.backward = 0.0
        # Tension, bias, continuity.
        self.tbc = tbc()



    # read from file
    def read(self, file):
        self.time, = struct.unpack('<f', file.read(4))
        self.value, = struct.unpack('<f', file.read(4))
        self.forward = 0.0
        if (self.key_type == 2):
            self.forward, = struct.unpack('<f', file.read(4))
        self.backward = 0.0
        if (self.key_type == 2):
            self.backward, = struct.unpack('<f', file.read(4))
        self.tbc = tbc()
        if (self.key_type == 3):
            self.tbc.read(file)



    # write to file
    def write(self, file):
        file.write(struct.pack('<f', self.time))
        file.write(struct.pack('<f', self.value))
        if (self.key_type == 2):
            file.write(struct.pack('<f', self.forward))
        if (self.key_type == 2):
            file.write(struct.pack('<f', self.backward))
        if (self.key_type == 3):
            self.tbc.write(file)



    # dump to screen
    def __str__(self):
        s = ''
        s += 'time' + ': %f\n'%self.time
        s += 'value' + ': %f\n'%self.value
        if (self.key_type == 2):
            s += 'forward' + ': %f\n'%self.forward
        if (self.key_type == 2):
            s += 'backward' + ': %f\n'%self.backward
        if (self.key_type == 3):
            s += 'tbc' + ':\n'
            s += str(self.tbc) + '\n'
        return s



#
# A rotation animation sub key - possibly separate x, y, and z key sets.
#
class rotationsubkey:
    # constructor
    def __init__(self):
        # Number of keys in this sub-group.
        self.sub_key_count = 0
        # Key type - always 1 (linear) or 2 (quadtratic)
        self.key_type = 0
        # Possibly axis-specific animation keys.
        self.unknown_keys = [ None ] * self.sub_key_count
        for count in range(self.sub_key_count): self.unknown_keys[count] = keyfloat(self.key_type)



    # read from file
    def read(self, file):
        self.sub_key_count, = struct.unpack('<I', file.read(4))
        self.key_type, = struct.unpack('<I', file.read(4))
        if (self.sub_key_count > MAX_ARRAYSIZE): raise NIFError('array size unreasonably large (size %i)'%self.sub_key_count)
        self.unknown_keys = [ None ] * self.sub_key_count
        for count in range(self.sub_key_count): self.unknown_keys[count] = keyfloat(self.key_type)
        for count in range(self.sub_key_count):
            self.unknown_keys[count].read(file)



    # write to file
    def write(self, file):
        file.write(struct.pack('<I', self.sub_key_count))
        file.write(struct.pack('<I', self.key_type))
        if (self.sub_key_count > MAX_ARRAYSIZE): raise NIFError('array size unreasonably large (size %i)'%self.sub_key_count)
        for count in range(self.sub_key_count):
            self.unknown_keys[count].write(file)



    # dump to screen
    def __str__(self):
        s = ''
        s += 'sub_key_count' + ': %i\n'%self.sub_key_count
        s += 'key_type' + ': %i\n'%self.key_type
        if (self.sub_key_count <= MAX_ARRAYDUMPSIZE):
            for count in range(self.sub_key_count):
                s += 'unknown_keys' + '[%i]'%count + ':\n'
                s += str(self.unknown_keys[count]) + '\n'
        else:
            s += 'unknown_keys: array[%i]\n'%self.sub_key_count
        return s



#
# A rotation animation key.
#
class keyrotation:
    # constructor
    def __init__(self, init_arg):
        # Type of rotation key.
        self.rotation_type = init_arg
        # Key time.
        self.time = 0.0
        # Rotation quaternion - linear interpolation.
        self.quat = quaternion()
        # Quaternion plus Tension, bias, and continuity.
        self.tbc = tbc()
        # Three rotation key groups of an unknown type. Each group possibly
        # corresponds to axis-specific rotations for  x, y, or z respectively.
        self.sub_keys = [ None ] * 3
        for count in range(3): self.sub_keys[count] = rotationsubkey()



    # read from file
    def read(self, file):
        self.time, = struct.unpack('<f', file.read(4))
        self.quat = quaternion()
        if (self.rotation_type != 4):
            self.quat.read(file)
        self.tbc = tbc()
        if (self.rotation_type == 3):
            self.tbc.read(file)
        if (3 > MAX_ARRAYSIZE): raise NIFError('array size unreasonably large (size %i)'%3)
        self.sub_keys = [ None ] * 3
        for count in range(3): self.sub_keys[count] = rotationsubkey()
        if (self.rotation_type == 4):
            for count in range(3):
                self.sub_keys[count].read(file)



    # write to file
    def write(self, file):
        file.write(struct.pack('<f', self.time))
        if (self.rotation_type != 4):
            self.quat.write(file)
        if (self.rotation_type == 3):
            self.tbc.write(file)
        if (3 > MAX_ARRAYSIZE): raise NIFError('array size unreasonably large (size %i)'%3)
        if (self.rotation_type == 4):
            for count in range(3):
                self.sub_keys[count].write(file)



    # dump to screen
    def __str__(self):
        s = ''
        s += 'time' + ': %f\n'%self.time
        if (self.rotation_type != 4):
            s += 'quat' + ':\n'
            s += str(self.quat) + '\n'
        if (self.rotation_type == 3):
            s += 'tbc' + ':\n'
            s += str(self.tbc) + '\n'
        if (self.rotation_type == 4):
            if (3 <= MAX_ARRAYDUMPSIZE):
                for count in range(3):
                    s += 'sub_keys' + '[%i]'%count + ':\n'
                    s += str(self.sub_keys[count]) + '\n'
            else:
                s += 'sub_keys: array[%i]\n'%3
        return s



#
# Texture description.
#
class texture:
    # constructor
    def __init__(self):
        # Texture source block index.
        self.source = -1
        # 0=clamp S clamp T, 1=clamp S wrap T, 2=wrap S clamp T, 3=wrap S wrap T
        self.clamp_mode = 0
        # 0=nearest, 1=bilinear, 2=trilinear, 3=..., 4=..., 5=...
        self.filter_mode = 0
        # Texture set? Usually 0.
        self.texture_set = 0
        # 0?
        self.ps2_l = 0
        # 0xFFB5?
        self.ps2_k = 0
        # Unknown, 0 or 0x0101?
        self.unknown = 0



    # read from file
    def read(self, file):
        self.source, = struct.unpack('<i', file.read(4))
        self.clamp_mode, = struct.unpack('<I', file.read(4))
        self.filter_mode, = struct.unpack('<I', file.read(4))
        self.texture_set, = struct.unpack('<I', file.read(4))
        self.ps2_l, = struct.unpack('<H', file.read(2))
        self.ps2_k, = struct.unpack('<H', file.read(2))
        self.unknown, = struct.unpack('<H', file.read(2))



    # write to file
    def write(self, file):
        file.write(struct.pack('<i', self.source))
        file.write(struct.pack('<I', self.clamp_mode))
        file.write(struct.pack('<I', self.filter_mode))
        file.write(struct.pack('<I', self.texture_set))
        file.write(struct.pack('<H', self.ps2_l))
        file.write(struct.pack('<H', self.ps2_k))
        file.write(struct.pack('<H', self.unknown))



    # dump to screen
    def __str__(self):
        s = ''
        s += 'source' + ': %i\n'%self.source
        s += 'clamp_mode' + ': %i\n'%self.clamp_mode
        s += 'filter_mode' + ': %i\n'%self.filter_mode
        s += 'texture_set' + ': %i\n'%self.texture_set
        s += 'ps2_l' + ': %i\n'%self.ps2_l
        s += 'ps2_k' + ': %i\n'%self.ps2_k
        s += 'unknown' + ': %i\n'%self.unknown
        return s



#
# A UV data group.
#
class uvgroup:
    # constructor
    def __init__(self):
        # Number of keys.
        self.num_keys = 0
        # The UV data key type.  Always set to type 2 (quadratic) in all official
        # files.
        self.key_type = 0
        # The UV data keys.
        self.uv_keys = [ None ] * self.num_keys
        for count in range(self.num_keys): self.uv_keys[count] = keyfloat(self.key_type)



    # read from file
    def read(self, file):
        self.num_keys, = struct.unpack('<I', file.read(4))
        self.key_type = 0
        if (self.num_keys != 0):
            self.key_type, = struct.unpack('<I', file.read(4))
        if (self.num_keys > MAX_ARRAYSIZE): raise NIFError('array size unreasonably large (size %i)'%self.num_keys)
        self.uv_keys = [ None ] * self.num_keys
        for count in range(self.num_keys): self.uv_keys[count] = keyfloat(self.key_type)
        for count in range(self.num_keys):
            self.uv_keys[count].read(file)



    # write to file
    def write(self, file):
        file.write(struct.pack('<I', self.num_keys))
        if (self.num_keys != 0):
            file.write(struct.pack('<I', self.key_type))
        if (self.num_keys > MAX_ARRAYSIZE): raise NIFError('array size unreasonably large (size %i)'%self.num_keys)
        for count in range(self.num_keys):
            self.uv_keys[count].write(file)



    # dump to screen
    def __str__(self):
        s = ''
        s += 'num_keys' + ': %i\n'%self.num_keys
        if (self.num_keys != 0):
            s += 'key_type' + ': %i\n'%self.key_type
        if (self.num_keys <= MAX_ARRAYDUMPSIZE):
            for count in range(self.num_keys):
                s += 'uv_keys' + '[%i]'%count + ':\n'
                s += str(self.uv_keys[count]) + '\n'
        else:
            s += 'uv_keys: array[%i]\n'%self.num_keys
        return s



#
# A 2-dimensional vector, used for UV coordinates.
#
class vec2:
    # constructor
    def __init__(self):
        # First coordinate.
        self.u = 0.0
        # Second coordinate.
        self.v = 0.0



    # read from file
    def read(self, file):
        self.u, = struct.unpack('<f', file.read(4))
        self.v, = struct.unpack('<f', file.read(4))



    # write to file
    def write(self, file):
        file.write(struct.pack('<f', self.u))
        file.write(struct.pack('<f', self.v))



    # dump to screen
    def __str__(self):
        s = ''
        s += 'u' + ': %f\n'%self.u
        s += 'v' + ': %f\n'%self.v
        return s



#
# A vector in 3D space.
#
class vec3:
    # constructor
    def __init__(self):
        # First coordinate.
        self.x = 0.0
        # Second coordinate.
        self.y = 0.0
        # Third coordinate.
        self.z = 0.0



    # read from file
    def read(self, file):
        self.x, = struct.unpack('<f', file.read(4))
        self.y, = struct.unpack('<f', file.read(4))
        self.z, = struct.unpack('<f', file.read(4))



    # write to file
    def write(self, file):
        file.write(struct.pack('<f', self.x))
        file.write(struct.pack('<f', self.y))
        file.write(struct.pack('<f', self.z))



    # dump to screen
    def __str__(self):
        s = ''
        s += 'x' + ': %f\n'%self.x
        s += 'y' + ': %f\n'%self.y
        s += 'z' + ': %f\n'%self.z
        return s



#
# A vector animation key.
#
class keyvec3:
    # constructor
    def __init__(self, init_arg):
        # Key type.
        self.key_type = init_arg
        # Key time.
        self.time = 0.0
        # Position.
        self.pos = vec3()
        # Forward tangent.
        self.forward = vec3()
        # Backward tangent.
        self.backward = vec3()
        # Tension, bias, continuity.
        self.tbc = tbc()



    # read from file
    def read(self, file):
        self.time, = struct.unpack('<f', file.read(4))
        self.pos = vec3()
        self.pos.read(file)
        self.forward = vec3()
        if (self.key_type == 2):
            self.forward.read(file)
        self.backward = vec3()
        if (self.key_type == 2):
            self.backward.read(file)
        self.tbc = tbc()
        if (self.key_type == 3):
            self.tbc.read(file)



    # write to file
    def write(self, file):
        file.write(struct.pack('<f', self.time))
        self.pos.write(file)
        if (self.key_type == 2):
            self.forward.write(file)
        if (self.key_type == 2):
            self.backward.write(file)
        if (self.key_type == 3):
            self.tbc.write(file)



    # dump to screen
    def __str__(self):
        s = ''
        s += 'time' + ': %f\n'%self.time
        s += 'pos' + ':\n'
        s += str(self.pos) + '\n'
        if (self.key_type == 2):
            s += 'forward' + ':\n'
            s += str(self.forward) + '\n'
        if (self.key_type == 2):
            s += 'backward' + ':\n'
            s += str(self.backward) + '\n'
        if (self.key_type == 3):
            s += 'tbc' + ':\n'
            s += str(self.tbc) + '\n'
        return s



#
# A 3x3 rotation matrix; M^T M=identity, det(M)=1.
#
class mat3x3:
    # constructor
    def __init__(self):
        # First row.
        self.x = vec3()
        # Second row.
        self.y = vec3()
        # Third row.
        self.z = vec3()



    # read from file
    def read(self, file):
        self.x = vec3()
        self.x.read(file)
        self.y = vec3()
        self.y.read(file)
        self.z = vec3()
        self.z.read(file)



    # write to file
    def write(self, file):
        self.x.write(file)
        self.y.write(file)
        self.z.write(file)



    # dump to screen
    def __str__(self):
        s = ''
        s += 'x' + ':\n'
        s += str(self.x) + '\n'
        s += 'y' + ':\n'
        s += str(self.y) + '\n'
        s += 'z' + ':\n'
        s += str(self.z) + '\n'
        return s



#
# Bounding box.
#
class bbox:
    # constructor
    def __init__(self):
        # Usually 1.
        self.unknown = 0
        # Translation vector.
        self.translation = vec3()
        # Rotation matrix.
        self.rotation = mat3x3()
        # Radius, per direction.
        self.radius = vec3()



    # read from file
    def read(self, file):
        self.unknown, = struct.unpack('<I', file.read(4))
        self.translation = vec3()
        self.translation.read(file)
        self.rotation = mat3x3()
        self.rotation.read(file)
        self.radius = vec3()
        self.radius.read(file)



    # write to file
    def write(self, file):
        file.write(struct.pack('<I', self.unknown))
        self.translation.write(file)
        self.rotation.write(file)
        self.radius.write(file)



    # dump to screen
    def __str__(self):
        s = ''
        s += 'unknown' + ': %i\n'%self.unknown
        s += 'translation' + ':\n'
        s += str(self.translation) + '\n'
        s += 'rotation' + ':\n'
        s += str(self.rotation) + '\n'
        s += 'radius' + ':\n'
        s += str(self.radius) + '\n'
        return s



#
# Geometry morphing data component.
#
class morphblock:
    # constructor
    def __init__(self, init_arg):
        # Number of vertices.
        self.num_vertices = init_arg
        # Number of frames.
        self.num_frames = 0
        # Should be 2.
        self.key_type = 0
        # The morphing keyframes.
        self.frames = [ None ] * self.num_frames
        for count in range(self.num_frames): self.frames[count] = morphframe()
        # Morph vectors.
        self.vectors = [ None ] * self.num_vertices
        for count in range(self.num_vertices): self.vectors[count] = vec3()



    # read from file
    def read(self, file):
        self.num_frames, = struct.unpack('<I', file.read(4))
        self.key_type, = struct.unpack('<I', file.read(4))
        if (self.num_frames > MAX_ARRAYSIZE): raise NIFError('array size unreasonably large (size %i)'%self.num_frames)
        self.frames = [ None ] * self.num_frames
        for count in range(self.num_frames): self.frames[count] = morphframe()
        for count in range(self.num_frames):
            self.frames[count].read(file)
        if (self.num_vertices > MAX_ARRAYSIZE): raise NIFError('array size unreasonably large (size %i)'%self.num_vertices)
        self.vectors = [ None ] * self.num_vertices
        for count in range(self.num_vertices): self.vectors[count] = vec3()
        for count in range(self.num_vertices):
            self.vectors[count].read(file)



    # write to file
    def write(self, file):
        file.write(struct.pack('<I', self.num_frames))
        file.write(struct.pack('<I', self.key_type))
        if (self.num_frames > MAX_ARRAYSIZE): raise NIFError('array size unreasonably large (size %i)'%self.num_frames)
        for count in range(self.num_frames):
            self.frames[count].write(file)
        if (self.num_vertices > MAX_ARRAYSIZE): raise NIFError('array size unreasonably large (size %i)'%self.num_vertices)
        for count in range(self.num_vertices):
            self.vectors[count].write(file)



    # dump to screen
    def __str__(self):
        s = ''
        s += 'num_frames' + ': %i\n'%self.num_frames
        s += 'key_type' + ': %i\n'%self.key_type
        if (self.num_frames <= MAX_ARRAYDUMPSIZE):
            for count in range(self.num_frames):
                s += 'frames' + '[%i]'%count + ':\n'
                s += str(self.frames[count]) + '\n'
        else:
            s += 'frames: array[%i]\n'%self.num_frames
        if (self.num_vertices <= MAX_ARRAYDUMPSIZE):
            for count in range(self.num_vertices):
                s += 'vectors' + '[%i]'%count + ':\n'
                s += str(self.vectors[count]) + '\n'
        else:
            s += 'vectors: array[%i]\n'%self.num_vertices
        return s



#
# A weighted vertex.
#
class weightedvertex:
    # constructor
    def __init__(self):
        # The vertex index, in the mesh.
        self.index = 0
        # The vertex weight - between 0.0 and 1.0
        self.weight = 0.0



    # read from file
    def read(self, file):
        self.index, = struct.unpack('<H', file.read(2))
        self.weight, = struct.unpack('<f', file.read(4))



    # write to file
    def write(self, file):
        file.write(struct.pack('<H', self.index))
        file.write(struct.pack('<f', self.weight))



    # dump to screen
    def __str__(self):
        s = ''
        s += 'index' + ': %i\n'%self.index
        s += 'weight' + ': %f\n'%self.weight
        return s



#
# Skinning data component.
#
class skinblock:
    # constructor
    def __init__(self):
        # Rotation offset of the skin from this bone in bind position.
        self.rotation_offset = mat3x3()
        # Translation offset of the skin from this bone in bind position.
        self.translation_offset = vec3()
        # Scale offset of the skin from this bone in bind position. (Assumption -
        # this is always 1.0 so far)
        self.scale_offset = 0.0
        # This has been verified not to be a normalized quaternion.  They may or may
        # not be related to each other so their specification as an array of 4
        # floats may be misleading.
        self.unknown_4_floats = [ None ] * 4
        for count in range(4): self.unknown_4_floats[count] = 0.0
        # Number of weighted vertices.
        self.num_vertices = 0
        # The vertex weights.
        self.vertex_weights = [ None ] * self.num_vertices
        for count in range(self.num_vertices): self.vertex_weights[count] = weightedvertex()



    # read from file
    def read(self, file):
        self.rotation_offset = mat3x3()
        self.rotation_offset.read(file)
        self.translation_offset = vec3()
        self.translation_offset.read(file)
        self.scale_offset, = struct.unpack('<f', file.read(4))
        if (4 > MAX_ARRAYSIZE): raise NIFError('array size unreasonably large (size %i)'%4)
        self.unknown_4_floats = [ None ] * 4
        for count in range(4): self.unknown_4_floats[count] = 0.0
        for count in range(4):
            self.unknown_4_floats[count], = struct.unpack('<f', file.read(4))
        self.num_vertices, = struct.unpack('<H', file.read(2))
        if (self.num_vertices > MAX_ARRAYSIZE): raise NIFError('array size unreasonably large (size %i)'%self.num_vertices)
        self.vertex_weights = [ None ] * self.num_vertices
        for count in range(self.num_vertices): self.vertex_weights[count] = weightedvertex()
        for count in range(self.num_vertices):
            self.vertex_weights[count].read(file)



    # write to file
    def write(self, file):
        self.rotation_offset.write(file)
        self.translation_offset.write(file)
        file.write(struct.pack('<f', self.scale_offset))
        if (4 > MAX_ARRAYSIZE): raise NIFError('array size unreasonably large (size %i)'%4)
        for count in range(4):
            file.write(struct.pack('<f', self.unknown_4_floats[count]))
        file.write(struct.pack('<H', self.num_vertices))
        if (self.num_vertices > MAX_ARRAYSIZE): raise NIFError('array size unreasonably large (size %i)'%self.num_vertices)
        for count in range(self.num_vertices):
            self.vertex_weights[count].write(file)



    # dump to screen
    def __str__(self):
        s = ''
        s += 'rotation_offset' + ':\n'
        s += str(self.rotation_offset) + '\n'
        s += 'translation_offset' + ':\n'
        s += str(self.translation_offset) + '\n'
        s += 'scale_offset' + ': %f\n'%self.scale_offset
        if (4 <= MAX_ARRAYDUMPSIZE):
            for count in range(4):
                s += 'unknown_4_floats' + '[%i]'%count + ': %f\n'%self.unknown_4_floats[count]
        else:
            s += 'unknown_4_floats: array[%i]\n'%4
        s += 'num_vertices' + ': %i\n'%self.num_vertices
        if (self.num_vertices <= MAX_ARRAYDUMPSIZE):
            for count in range(self.num_vertices):
                s += 'vertex_weights' + '[%i]'%count + ':\n'
                s += str(self.vertex_weights[count]) + '\n'
        else:
            s += 'vertex_weights: array[%i]\n'%self.num_vertices
        return s



#
# A generic controlled block with extra data.
#
class AControlled:
    # constructor
    def __init__(self):
        # Extra data block index.
        self.extra_data = -1
        # Controller block index.
        self.controller = -1



    # read from file
    def read(self, file):
        self.extra_data, = struct.unpack('<i', file.read(4))
        self.controller, = struct.unpack('<i', file.read(4))



    # write to file
    def write(self, file):
        file.write(struct.pack('<i', self.extra_data))
        file.write(struct.pack('<i', self.controller))



    # dump to screen
    def __str__(self):
        s = ''
        s += 'extra_data' + ': %i\n'%self.extra_data
        s += 'controller' + ': %i\n'%self.controller
        return s



#
# A generic time controller block.
#
class AController:
    # constructor
    def __init__(self):
        # Index of the next controller.
        self.next_controller = -1
        # Controller flags (usually 0x000C).
        self.flags = 0
        # Frequency (is usually 1.0).
        self.frequency = 0.0
        # Phase (usually 0.0).
        self.phase = 0.0
        # Controller start time.
        self.start_time = 0.0
        # Controller stop time.
        self.stop_time = 0.0
        # Controller target node (block index of the parent of this controller).
        self.target_node = -1



    # read from file
    def read(self, file):
        self.next_controller, = struct.unpack('<i', file.read(4))
        self.flags, = struct.unpack('<H', file.read(2))
        self.frequency, = struct.unpack('<f', file.read(4))
        self.phase, = struct.unpack('<f', file.read(4))
        self.start_time, = struct.unpack('<f', file.read(4))
        self.stop_time, = struct.unpack('<f', file.read(4))
        self.target_node, = struct.unpack('<i', file.read(4))



    # write to file
    def write(self, file):
        file.write(struct.pack('<i', self.next_controller))
        file.write(struct.pack('<H', self.flags))
        file.write(struct.pack('<f', self.frequency))
        file.write(struct.pack('<f', self.phase))
        file.write(struct.pack('<f', self.start_time))
        file.write(struct.pack('<f', self.stop_time))
        file.write(struct.pack('<i', self.target_node))



    # dump to screen
    def __str__(self):
        s = ''
        s += 'next_controller' + ': %i\n'%self.next_controller
        s += 'flags' + ': 0x%04X\n'%self.flags
        s += 'frequency' + ': %f\n'%self.frequency
        s += 'phase' + ': %f\n'%self.phase
        s += 'start_time' + ': %f\n'%self.start_time
        s += 'stop_time' + ': %f\n'%self.stop_time
        s += 'target_node' + ': %i\n'%self.target_node
        return s



#
# A generic extra data block.
#
class AExtraData:
    # constructor
    def __init__(self):
        # Block number of the next extra data block.
        self.extra_data = -1



    # read from file
    def read(self, file):
        self.extra_data, = struct.unpack('<i', file.read(4))



    # write to file
    def write(self, file):
        file.write(struct.pack('<i', self.extra_data))



    # dump to screen
    def __str__(self):
        s = ''
        s += 'extra_data' + ': %i\n'%self.extra_data
        return s



#
# A generic named controlled block with extra data.
#
class ANamed:
    # constructor
    def __init__(self):
        # Name of this block.
        self.name = string()
        # Block index to an extra data block.
        self.extra_data = -1
        # Block index for the time controller block.
        self.controller = -1



    # read from file
    def read(self, file):
        self.name = string()
        self.name.read(file)
        self.extra_data, = struct.unpack('<i', file.read(4))
        self.controller, = struct.unpack('<i', file.read(4))



    # write to file
    def write(self, file):
        self.name.write(file)
        file.write(struct.pack('<i', self.extra_data))
        file.write(struct.pack('<i', self.controller))



    # dump to screen
    def __str__(self):
        s = ''
        s += 'name' + ':\n'
        s += str(self.name) + '\n'
        s += 'extra_data' + ': %i\n'%self.extra_data
        s += 'controller' + ': %i\n'%self.controller
        return s



#
# Generic node block.
#
class ANode(ANamed):
    # constructor
    def __init__(self):
        ANamed.__init__(self)
        # Some flags; commonly 0x000C or 0x000A.
        self.flags = 0
        # The translation vector.
        self.translation = vec3()
        # The rotation part of the transformation matrix.
        self.rotation = mat3x3()
        # Scaling part (only scalar is supported).
        self.scale = 0.0
        # Velocity part. Always (0,0,0).
        self.velocity = vec3()
        # List of node properties.
        self.properties = indexlist()
        # Do we have a bounding box?
        self.has_bounding_box = 0
        # The bounding box.
        self.bounding_box = bbox()



    # read from file
    def read(self, file):
        ANamed.read(self, file)
        self.flags, = struct.unpack('<H', file.read(2))
        self.translation = vec3()
        self.translation.read(file)
        self.rotation = mat3x3()
        self.rotation.read(file)
        self.scale, = struct.unpack('<f', file.read(4))
        self.velocity = vec3()
        self.velocity.read(file)
        self.properties = indexlist()
        self.properties.read(file)
        self.has_bounding_box, = struct.unpack('<I', file.read(4))
        self.bounding_box = bbox()
        if (self.has_bounding_box != 0):
            self.bounding_box.read(file)



    # write to file
    def write(self, file):
        ANamed.write(self, file)
        file.write(struct.pack('<H', self.flags))
        self.translation.write(file)
        self.rotation.write(file)
        file.write(struct.pack('<f', self.scale))
        self.velocity.write(file)
        self.properties.write(file)
        file.write(struct.pack('<I', self.has_bounding_box))
        if (self.has_bounding_box != 0):
            self.bounding_box.write(file)



    # dump to screen
    def __str__(self):
        s = ''
        s += ANamed.__str__(self)
        s += 'flags' + ': 0x%04X\n'%self.flags
        s += 'translation' + ':\n'
        s += str(self.translation) + '\n'
        s += 'rotation' + ':\n'
        s += str(self.rotation) + '\n'
        s += 'scale' + ': %f\n'%self.scale
        s += 'velocity' + ':\n'
        s += str(self.velocity) + '\n'
        s += 'properties' + ':\n'
        s += str(self.properties) + '\n'
        s += 'has_bounding_box' + ': %i\n'%self.has_bounding_box
        if (self.has_bounding_box != 0):
            s += 'bounding_box' + ':\n'
            s += str(self.bounding_box) + '\n'
        return s



#
# Light source.
#
class ALight(ANode):
    # constructor
    def __init__(self):
        ANode.__init__(self)
        # Unknown. Always 1. Light type?
        self.unknown1 = 0
        # Unknown. Always non-zero.
        self.unknown2 = 0
        # Dimmer.
        self.dimmer = 0.0
        # Ambient color.
        self.ambient_color = rgb()
        # Diffuse color.
        self.diffuse_color = rgb()
        # Specular color.
        self.specular_color = rgb()



    # read from file
    def read(self, file):
        ANode.read(self, file)
        self.unknown1, = struct.unpack('<I', file.read(4))
        self.unknown2, = struct.unpack('<I', file.read(4))
        self.dimmer, = struct.unpack('<f', file.read(4))
        self.ambient_color = rgb()
        self.ambient_color.read(file)
        self.diffuse_color = rgb()
        self.diffuse_color.read(file)
        self.specular_color = rgb()
        self.specular_color.read(file)



    # write to file
    def write(self, file):
        ANode.write(self, file)
        file.write(struct.pack('<I', self.unknown1))
        file.write(struct.pack('<I', self.unknown2))
        file.write(struct.pack('<f', self.dimmer))
        self.ambient_color.write(file)
        self.diffuse_color.write(file)
        self.specular_color.write(file)



    # dump to screen
    def __str__(self):
        s = ''
        s += ANode.__str__(self)
        s += 'unknown1' + ': %i\n'%self.unknown1
        s += 'unknown2' + ': %i\n'%self.unknown2
        s += 'dimmer' + ': %f\n'%self.dimmer
        s += 'ambient_color' + ':\n'
        s += str(self.ambient_color) + '\n'
        s += 'diffuse_color' + ':\n'
        s += str(self.diffuse_color) + '\n'
        s += 'specular_color' + ':\n'
        s += str(self.specular_color) + '\n'
        return s



#
# Generic node block for grouping.
#
class AParentNode(ANode):
    # constructor
    def __init__(self):
        ANode.__init__(self)
        # List of child node block indices.
        self.children = indexlist()
        # List of node effects.
        self.effects = indexlist()



    # read from file
    def read(self, file):
        ANode.read(self, file)
        self.children = indexlist()
        self.children.read(file)
        self.effects = indexlist()
        self.effects.read(file)



    # write to file
    def write(self, file):
        ANode.write(self, file)
        self.children.write(file)
        self.effects.write(file)



    # dump to screen
    def __str__(self):
        s = ''
        s += ANode.__str__(self)
        s += 'children' + ':\n'
        s += str(self.children) + '\n'
        s += 'effects' + ':\n'
        s += str(self.effects) + '\n'
        return s



#
# A generic property block.
#
class AProperty(ANamed):
    # constructor
    def __init__(self):
        ANamed.__init__(self)
        # Property flags.
        self.flags = 0



    # read from file
    def read(self, file):
        ANamed.read(self, file)
        self.flags, = struct.unpack('<H', file.read(2))



    # write to file
    def write(self, file):
        ANamed.write(self, file)
        file.write(struct.pack('<H', self.flags))



    # dump to screen
    def __str__(self):
        s = ''
        s += ANamed.__str__(self)
        s += 'flags' + ': 0x%04X\n'%self.flags
        return s



#
# Unknown.
#
class AvoidNode(AParentNode):
    # constructor
    def __init__(self):
        self.block_type = mystring("AvoidNode")
        AParentNode.__init__(self)



    # read from file, excluding type string
    def read(self, file):
        AParentNode.read(self, file)



    # write to file, including type string
    def write(self, file):
        self.block_type.write(file)
        AParentNode.write(self, file)



    # dump to screen
    def __str__(self):
        s = ''
        s += str(self.block_type)
        s += AParentNode.__str__(self)
        return s



#
# Time controller for transparency.
#
class NiAlphaController(AController):
    # constructor
    def __init__(self):
        self.block_type = mystring("NiAlphaController")
        AController.__init__(self)
        # Alpha controller data index.
        self.data = 0



    # read from file, excluding type string
    def read(self, file):
        AController.read(self, file)
        self.data, = struct.unpack('<I', file.read(4))



    # write to file, including type string
    def write(self, file):
        self.block_type.write(file)
        AController.write(self, file)
        file.write(struct.pack('<I', self.data))



    # dump to screen
    def __str__(self):
        s = ''
        s += str(self.block_type)
        s += AController.__str__(self)
        s += 'data' + ': %i\n'%self.data
        return s



#
# Transparency. Flags 0x00ED.
#
class NiAlphaProperty(AProperty):
    # constructor
    def __init__(self):
        self.block_type = mystring("NiAlphaProperty")
        AProperty.__init__(self)
        # Unknown: 0.
        self.unknown = 0



    # read from file, excluding type string
    def read(self, file):
        AProperty.read(self, file)
        self.unknown, = struct.unpack('<B', file.read(1))



    # write to file, including type string
    def write(self, file):
        self.block_type.write(file)
        AProperty.write(self, file)
        file.write(struct.pack('<b', self.unknown))



    # dump to screen
    def __str__(self):
        s = ''
        s += str(self.block_type)
        s += AProperty.__str__(self)
        s += 'unknown' + ': %i\n'%self.unknown
        return s



#
# Ambient light source.
#
class NiAmbientLight(ALight):
    # constructor
    def __init__(self):
        self.block_type = mystring("NiAmbientLight")
        ALight.__init__(self)



    # read from file, excluding type string
    def read(self, file):
        ALight.read(self, file)



    # write to file, including type string
    def write(self, file):
        self.block_type.write(file)
        ALight.write(self, file)



    # dump to screen
    def __str__(self):
        s = ''
        s += str(self.block_type)
        s += ALight.__str__(self)
        return s



#
# Unknown.
#
class NiAutoNormalParticles(ANode):
    # constructor
    def __init__(self):
        self.block_type = mystring("NiAutoNormalParticles")
        ANode.__init__(self)
        # Auto normal particles data index.
        self.data = -1
        # Unknown.
        self.unknown = -1



    # read from file, excluding type string
    def read(self, file):
        ANode.read(self, file)
        self.data, = struct.unpack('<i', file.read(4))
        self.unknown, = struct.unpack('<i', file.read(4))



    # write to file, including type string
    def write(self, file):
        self.block_type.write(file)
        ANode.write(self, file)
        file.write(struct.pack('<i', self.data))
        file.write(struct.pack('<i', self.unknown))



    # dump to screen
    def __str__(self):
        s = ''
        s += str(self.block_type)
        s += ANode.__str__(self)
        s += 'data' + ': %i\n'%self.data
        s += 'unknown' + ': %i\n'%self.unknown
        return s



#
# Unknown.
#
class NiBillboardNode(AParentNode):
    # constructor
    def __init__(self):
        self.block_type = mystring("NiBillboardNode")
        AParentNode.__init__(self)



    # read from file, excluding type string
    def read(self, file):
        AParentNode.read(self, file)



    # write to file, including type string
    def write(self, file):
        self.block_type.write(file)
        AParentNode.write(self, file)



    # dump to screen
    def __str__(self):
        s = ''
        s += str(self.block_type)
        s += AParentNode.__str__(self)
        return s



#
# Node for animated objects without armature.
#
class NiBSAnimationNode(AParentNode):
    # constructor
    def __init__(self):
        self.block_type = mystring("NiBSAnimationNode")
        AParentNode.__init__(self)



    # read from file, excluding type string
    def read(self, file):
        AParentNode.read(self, file)



    # write to file, including type string
    def write(self, file):
        self.block_type.write(file)
        AParentNode.write(self, file)



    # dump to screen
    def __str__(self):
        s = ''
        s += str(self.block_type)
        s += AParentNode.__str__(self)
        return s



#
# Unknown.
#
class NiBSParticleNode(AParentNode):
    # constructor
    def __init__(self):
        self.block_type = mystring("NiBSParticleNode")
        AParentNode.__init__(self)



    # read from file, excluding type string
    def read(self, file):
        AParentNode.read(self, file)



    # write to file, including type string
    def write(self, file):
        self.block_type.write(file)
        AParentNode.write(self, file)



    # dump to screen
    def __str__(self):
        s = ''
        s += str(self.block_type)
        s += AParentNode.__str__(self)
        return s



#
# Camera object.
#
class NiCamera(ANode):
    # constructor
    def __init__(self):
        self.block_type = mystring("NiCamera")
        ANode.__init__(self)
        # Frustrum left.
        self.frustum_left = 0.0
        # Frustrum right.
        self.frustum_right = 0.0
        # Frustrum top.
        self.frustum_top = 0.0
        # Frustrum bottom.
        self.frustum_bottom = 0.0
        # Frustrum near.
        self.frustum_near = 0.0
        # Frustrum far.
        self.frustum_far = 0.0
        # Viewport left.
        self.viewport_left = 0.0
        # Viewport right.
        self.viewport_right = 0.0
        # Viewport top.
        self.viewport_top = 0.0
        # Viewport bottom.
        self.viewport_bottom = 0.0
        # Level of detail adjust.
        self.lod_adjust = 0.0
        # Unknown.
        self.unknown1 = -1
        # Unknown.
        self.unknown2 = 0



    # read from file, excluding type string
    def read(self, file):
        ANode.read(self, file)
        self.frustum_left, = struct.unpack('<f', file.read(4))
        self.frustum_right, = struct.unpack('<f', file.read(4))
        self.frustum_top, = struct.unpack('<f', file.read(4))
        self.frustum_bottom, = struct.unpack('<f', file.read(4))
        self.frustum_near, = struct.unpack('<f', file.read(4))
        self.frustum_far, = struct.unpack('<f', file.read(4))
        self.viewport_left, = struct.unpack('<f', file.read(4))
        self.viewport_right, = struct.unpack('<f', file.read(4))
        self.viewport_top, = struct.unpack('<f', file.read(4))
        self.viewport_bottom, = struct.unpack('<f', file.read(4))
        self.lod_adjust, = struct.unpack('<f', file.read(4))
        self.unknown1, = struct.unpack('<i', file.read(4))
        self.unknown2, = struct.unpack('<I', file.read(4))



    # write to file, including type string
    def write(self, file):
        self.block_type.write(file)
        ANode.write(self, file)
        file.write(struct.pack('<f', self.frustum_left))
        file.write(struct.pack('<f', self.frustum_right))
        file.write(struct.pack('<f', self.frustum_top))
        file.write(struct.pack('<f', self.frustum_bottom))
        file.write(struct.pack('<f', self.frustum_near))
        file.write(struct.pack('<f', self.frustum_far))
        file.write(struct.pack('<f', self.viewport_left))
        file.write(struct.pack('<f', self.viewport_right))
        file.write(struct.pack('<f', self.viewport_top))
        file.write(struct.pack('<f', self.viewport_bottom))
        file.write(struct.pack('<f', self.lod_adjust))
        file.write(struct.pack('<i', self.unknown1))
        file.write(struct.pack('<I', self.unknown2))



    # dump to screen
    def __str__(self):
        s = ''
        s += str(self.block_type)
        s += ANode.__str__(self)
        s += 'frustum_left' + ': %f\n'%self.frustum_left
        s += 'frustum_right' + ': %f\n'%self.frustum_right
        s += 'frustum_top' + ': %f\n'%self.frustum_top
        s += 'frustum_bottom' + ': %f\n'%self.frustum_bottom
        s += 'frustum_near' + ': %f\n'%self.frustum_near
        s += 'frustum_far' + ': %f\n'%self.frustum_far
        s += 'viewport_left' + ': %f\n'%self.viewport_left
        s += 'viewport_right' + ': %f\n'%self.viewport_right
        s += 'viewport_top' + ': %f\n'%self.viewport_top
        s += 'viewport_bottom' + ': %f\n'%self.viewport_bottom
        s += 'lod_adjust' + ': %f\n'%self.lod_adjust
        s += 'unknown1' + ': %i\n'%self.unknown1
        s += 'unknown2' + ': %i\n'%self.unknown2
        return s



#
# Color data for material color controller.
#
class NiColorData:
    # constructor
    def __init__(self):
        self.block_type = mystring("NiColorData")
        # Number of color keys.
        self.num_keys = 0
        # The key type.  Always 1 in all official files.
        self.key_type = 0
        # The color keys.
        self.keys = [ None ] * self.num_keys
        for count in range(self.num_keys): self.keys[count] = keyrgba()



    # read from file, excluding type string
    def read(self, file):
        self.num_keys, = struct.unpack('<I', file.read(4))
        self.key_type, = struct.unpack('<I', file.read(4))
        if (self.num_keys > MAX_ARRAYSIZE): raise NIFError('array size unreasonably large (size %i)'%self.num_keys)
        self.keys = [ None ] * self.num_keys
        for count in range(self.num_keys): self.keys[count] = keyrgba()
        for count in range(self.num_keys):
            self.keys[count].read(file)



    # write to file, including type string
    def write(self, file):
        self.block_type.write(file)
        file.write(struct.pack('<I', self.num_keys))
        file.write(struct.pack('<I', self.key_type))
        if (self.num_keys > MAX_ARRAYSIZE): raise NIFError('array size unreasonably large (size %i)'%self.num_keys)
        for count in range(self.num_keys):
            self.keys[count].write(file)



    # dump to screen
    def __str__(self):
        s = ''
        s += str(self.block_type)
        s += 'num_keys' + ': %i\n'%self.num_keys
        s += 'key_type' + ': %i\n'%self.key_type
        if (self.num_keys <= MAX_ARRAYDUMPSIZE):
            for count in range(self.num_keys):
                s += 'keys' + '[%i]'%count + ':\n'
                s += str(self.keys[count]) + '\n'
        else:
            s += 'keys: array[%i]\n'%self.num_keys
        return s



#
# Directional light source.
#
class NiDirectionalLight(ALight):
    # constructor
    def __init__(self):
        self.block_type = mystring("NiDirectionalLight")
        ALight.__init__(self)



    # read from file, excluding type string
    def read(self, file):
        ALight.read(self, file)



    # write to file, including type string
    def write(self, file):
        self.block_type.write(file)
        ALight.write(self, file)



    # dump to screen
    def __str__(self):
        s = ''
        s += str(self.block_type)
        s += ALight.__str__(self)
        return s



#
# Unknown.
#
class NiDitherProperty(AProperty):
    # constructor
    def __init__(self):
        self.block_type = mystring("NiDitherProperty")
        AProperty.__init__(self)



    # read from file, excluding type string
    def read(self, file):
        AProperty.read(self, file)



    # write to file, including type string
    def write(self, file):
        self.block_type.write(file)
        AProperty.write(self, file)



    # dump to screen
    def __str__(self):
        s = ''
        s += str(self.block_type)
        s += AProperty.__str__(self)
        return s



#
# Texture flipping controller.
#
class NiFlipController(AController):
    # constructor
    def __init__(self):
        self.block_type = mystring("NiFlipController")
        AController.__init__(self)
        # 0?
        self.unknown_int_1 = 0
        # 0?
        self.unknown_int_2 = 0
        # Time between two flips.
        # delta = (start_time - stop_time) / sources.num_indices
        self.delta = 0.0
        # The texture source indices.
        self.sources = indexlist()



    # read from file, excluding type string
    def read(self, file):
        AController.read(self, file)
        self.unknown_int_1, = struct.unpack('<I', file.read(4))
        self.unknown_int_2, = struct.unpack('<I', file.read(4))
        self.delta, = struct.unpack('<f', file.read(4))
        self.sources = indexlist()
        self.sources.read(file)



    # write to file, including type string
    def write(self, file):
        self.block_type.write(file)
        AController.write(self, file)
        file.write(struct.pack('<I', self.unknown_int_1))
        file.write(struct.pack('<I', self.unknown_int_2))
        file.write(struct.pack('<f', self.delta))
        self.sources.write(file)



    # dump to screen
    def __str__(self):
        s = ''
        s += str(self.block_type)
        s += AController.__str__(self)
        s += 'unknown_int_1' + ': %i\n'%self.unknown_int_1
        s += 'unknown_int_2' + ': %i\n'%self.unknown_int_2
        s += 'delta' + ': %f\n'%self.delta
        s += 'sources' + ':\n'
        s += str(self.sources) + '\n'
        return s



#
# Possibly the 1D position along a 3D path.
#
class NiFloatData:
    # constructor
    def __init__(self):
        self.block_type = mystring("NiFloatData")
        # Number of keys.
        self.num_keys = 0
        # The key type, usually 2.
        self.key_type = 0
        # The keys.
        self.keys = [ None ] * self.num_keys
        for count in range(self.num_keys): self.keys[count] = keyfloat(self.key_type)



    # read from file, excluding type string
    def read(self, file):
        self.num_keys, = struct.unpack('<I', file.read(4))
        self.key_type, = struct.unpack('<I', file.read(4))
        if (self.num_keys > MAX_ARRAYSIZE): raise NIFError('array size unreasonably large (size %i)'%self.num_keys)
        self.keys = [ None ] * self.num_keys
        for count in range(self.num_keys): self.keys[count] = keyfloat(self.key_type)
        for count in range(self.num_keys):
            self.keys[count].read(file)



    # write to file, including type string
    def write(self, file):
        self.block_type.write(file)
        file.write(struct.pack('<I', self.num_keys))
        file.write(struct.pack('<I', self.key_type))
        if (self.num_keys > MAX_ARRAYSIZE): raise NIFError('array size unreasonably large (size %i)'%self.num_keys)
        for count in range(self.num_keys):
            self.keys[count].write(file)



    # dump to screen
    def __str__(self):
        s = ''
        s += str(self.block_type)
        s += 'num_keys' + ': %i\n'%self.num_keys
        s += 'key_type' + ': %i\n'%self.key_type
        if (self.num_keys <= MAX_ARRAYDUMPSIZE):
            for count in range(self.num_keys):
                s += 'keys' + '[%i]'%count + ':\n'
                s += str(self.keys[count]) + '\n'
        else:
            s += 'keys: array[%i]\n'%self.num_keys
        return s



#
# Time controller for geometry morphing.
#
class NiGeomMorpherController(AController):
    # constructor
    def __init__(self):
        self.block_type = mystring("NiGeomMorpherController")
        AController.__init__(self)
        # Geometry morphing data index.
        self.data = 0
        # Unknown byte (always zero?).
        self.unknown = 0



    # read from file, excluding type string
    def read(self, file):
        AController.read(self, file)
        self.data, = struct.unpack('<I', file.read(4))
        self.unknown, = struct.unpack('<B', file.read(1))



    # write to file, including type string
    def write(self, file):
        self.block_type.write(file)
        AController.write(self, file)
        file.write(struct.pack('<I', self.data))
        file.write(struct.pack('<b', self.unknown))



    # dump to screen
    def __str__(self):
        s = ''
        s += str(self.block_type)
        s += AController.__str__(self)
        s += 'data' + ': %i\n'%self.data
        s += 'unknown' + ': %i\n'%self.unknown
        return s



#
# Unknown.
#
class NiGravity(AControlled):
    # constructor
    def __init__(self):
        self.block_type = mystring("NiGravity")
        AControlled.__init__(self)
        # Unknown.
        self.unknown1 = 0.0
        # Unknown.
        self.unknown2 = 0.0
        # Unknown.
        self.unknown3 = 0
        # Unknown.
        self.unknown4 = 0.0
        # Unknown.
        self.unknown5 = 0.0
        # Unknown.
        self.unknown6 = 0.0
        # Unknown.
        self.unknown7 = 0.0
        # Unknown.
        self.unknown8 = 0.0
        # Unknown.
        self.unknown9 = 0.0



    # read from file, excluding type string
    def read(self, file):
        AControlled.read(self, file)
        self.unknown1, = struct.unpack('<f', file.read(4))
        self.unknown2, = struct.unpack('<f', file.read(4))
        self.unknown3, = struct.unpack('<I', file.read(4))
        self.unknown4, = struct.unpack('<f', file.read(4))
        self.unknown5, = struct.unpack('<f', file.read(4))
        self.unknown6, = struct.unpack('<f', file.read(4))
        self.unknown7, = struct.unpack('<f', file.read(4))
        self.unknown8, = struct.unpack('<f', file.read(4))
        self.unknown9, = struct.unpack('<f', file.read(4))



    # write to file, including type string
    def write(self, file):
        self.block_type.write(file)
        AControlled.write(self, file)
        file.write(struct.pack('<f', self.unknown1))
        file.write(struct.pack('<f', self.unknown2))
        file.write(struct.pack('<I', self.unknown3))
        file.write(struct.pack('<f', self.unknown4))
        file.write(struct.pack('<f', self.unknown5))
        file.write(struct.pack('<f', self.unknown6))
        file.write(struct.pack('<f', self.unknown7))
        file.write(struct.pack('<f', self.unknown8))
        file.write(struct.pack('<f', self.unknown9))



    # dump to screen
    def __str__(self):
        s = ''
        s += str(self.block_type)
        s += AControlled.__str__(self)
        s += 'unknown1' + ': %f\n'%self.unknown1
        s += 'unknown2' + ': %f\n'%self.unknown2
        s += 'unknown3' + ': %i\n'%self.unknown3
        s += 'unknown4' + ': %f\n'%self.unknown4
        s += 'unknown5' + ': %f\n'%self.unknown5
        s += 'unknown6' + ': %f\n'%self.unknown6
        s += 'unknown7' + ': %f\n'%self.unknown7
        s += 'unknown8' + ': %f\n'%self.unknown8
        s += 'unknown9' + ': %f\n'%self.unknown9
        return s



#
# A time controller block for animation key frames.
#
class NiKeyframeController(AController):
    # constructor
    def __init__(self):
        self.block_type = mystring("NiKeyframeController")
        AController.__init__(self)
        # Keyframe controller data index.
        self.data = -1



    # read from file, excluding type string
    def read(self, file):
        AController.read(self, file)
        self.data, = struct.unpack('<i', file.read(4))



    # write to file, including type string
    def write(self, file):
        self.block_type.write(file)
        AController.write(self, file)
        file.write(struct.pack('<i', self.data))



    # dump to screen
    def __str__(self):
        s = ''
        s += str(self.block_type)
        s += AController.__str__(self)
        s += 'data' + ': %i\n'%self.data
        return s



#
# Keyframes for mesh animation.
#
class NiKeyframeData:
    # constructor
    def __init__(self):
        self.block_type = mystring("NiKeyframeData")
        # Number of rotation keyframes.
        self.num_rotations = 0
        # Rotation key type.
        self.rotation_type = 0
        # The rotation keys.
        self.rotations = [ None ] * self.num_rotations
        for count in range(self.num_rotations): self.rotations[count] = keyrotation(self.rotation_type)
        # Number of translation keys.
        self.num_translations = 0
        # The type of translation keys.
        self.translation_type = 0
        # The translation keys.
        self.translations = [ None ] * self.num_translations
        for count in range(self.num_translations): self.translations[count] = keyvec3(self.translation_type)
        # Number of scale keys.
        self.num_scales = 0
        # Scale key type.
        self.scale_type = 0
        # The scale keys.
        self.scales = [ None ] * self.num_scales
        for count in range(self.num_scales): self.scales[count] = keyfloat(self.scale_type)



    # read from file, excluding type string
    def read(self, file):
        self.num_rotations, = struct.unpack('<I', file.read(4))
        self.rotation_type = 0
        if (self.num_rotations != 0):
            self.rotation_type, = struct.unpack('<I', file.read(4))
        if (self.num_rotations > MAX_ARRAYSIZE): raise NIFError('array size unreasonably large (size %i)'%self.num_rotations)
        self.rotations = [ None ] * self.num_rotations
        for count in range(self.num_rotations): self.rotations[count] = keyrotation(self.rotation_type)
        for count in range(self.num_rotations):
            self.rotations[count].read(file)
        self.num_translations, = struct.unpack('<I', file.read(4))
        self.translation_type = 0
        if (self.num_translations != 0):
            self.translation_type, = struct.unpack('<I', file.read(4))
        if (self.num_translations > MAX_ARRAYSIZE): raise NIFError('array size unreasonably large (size %i)'%self.num_translations)
        self.translations = [ None ] * self.num_translations
        for count in range(self.num_translations): self.translations[count] = keyvec3(self.translation_type)
        for count in range(self.num_translations):
            self.translations[count].read(file)
        self.num_scales, = struct.unpack('<I', file.read(4))
        self.scale_type = 0
        if (self.num_scales != 0):
            self.scale_type, = struct.unpack('<I', file.read(4))
        if (self.num_scales > MAX_ARRAYSIZE): raise NIFError('array size unreasonably large (size %i)'%self.num_scales)
        self.scales = [ None ] * self.num_scales
        for count in range(self.num_scales): self.scales[count] = keyfloat(self.scale_type)
        for count in range(self.num_scales):
            self.scales[count].read(file)



    # write to file, including type string
    def write(self, file):
        self.block_type.write(file)
        file.write(struct.pack('<I', self.num_rotations))
        if (self.num_rotations != 0):
            file.write(struct.pack('<I', self.rotation_type))
        if (self.num_rotations > MAX_ARRAYSIZE): raise NIFError('array size unreasonably large (size %i)'%self.num_rotations)
        for count in range(self.num_rotations):
            self.rotations[count].write(file)
        file.write(struct.pack('<I', self.num_translations))
        if (self.num_translations != 0):
            file.write(struct.pack('<I', self.translation_type))
        if (self.num_translations > MAX_ARRAYSIZE): raise NIFError('array size unreasonably large (size %i)'%self.num_translations)
        for count in range(self.num_translations):
            self.translations[count].write(file)
        file.write(struct.pack('<I', self.num_scales))
        if (self.num_scales != 0):
            file.write(struct.pack('<I', self.scale_type))
        if (self.num_scales > MAX_ARRAYSIZE): raise NIFError('array size unreasonably large (size %i)'%self.num_scales)
        for count in range(self.num_scales):
            self.scales[count].write(file)



    # dump to screen
    def __str__(self):
        s = ''
        s += str(self.block_type)
        s += 'num_rotations' + ': %i\n'%self.num_rotations
        if (self.num_rotations != 0):
            s += 'rotation_type' + ': %i\n'%self.rotation_type
        if (self.num_rotations <= MAX_ARRAYDUMPSIZE):
            for count in range(self.num_rotations):
                s += 'rotations' + '[%i]'%count + ':\n'
                s += str(self.rotations[count]) + '\n'
        else:
            s += 'rotations: array[%i]\n'%self.num_rotations
        s += 'num_translations' + ': %i\n'%self.num_translations
        if (self.num_translations != 0):
            s += 'translation_type' + ': %i\n'%self.translation_type
        if (self.num_translations <= MAX_ARRAYDUMPSIZE):
            for count in range(self.num_translations):
                s += 'translations' + '[%i]'%count + ':\n'
                s += str(self.translations[count]) + '\n'
        else:
            s += 'translations: array[%i]\n'%self.num_translations
        s += 'num_scales' + ': %i\n'%self.num_scales
        if (self.num_scales != 0):
            s += 'scale_type' + ': %i\n'%self.scale_type
        if (self.num_scales <= MAX_ARRAYDUMPSIZE):
            for count in range(self.num_scales):
                s += 'scales' + '[%i]'%count + ':\n'
                s += str(self.scales[count]) + '\n'
        else:
            s += 'scales: array[%i]\n'%self.num_scales
        return s



#
# Time controller for material color.
#
class NiMaterialColorController(AController):
    # constructor
    def __init__(self):
        self.block_type = mystring("NiMaterialColorController")
        AController.__init__(self)
        # Material color controller data block index.
        self.data = -1



    # read from file, excluding type string
    def read(self, file):
        AController.read(self, file)
        self.data, = struct.unpack('<i', file.read(4))



    # write to file, including type string
    def write(self, file):
        self.block_type.write(file)
        AController.write(self, file)
        file.write(struct.pack('<i', self.data))



    # dump to screen
    def __str__(self):
        s = ''
        s += str(self.block_type)
        s += AController.__str__(self)
        s += 'data' + ': %i\n'%self.data
        return s



#
# Describes the material shading properties.
#
class NiMaterialProperty(AProperty):
    # constructor
    def __init__(self):
        self.block_type = mystring("NiMaterialProperty")
        AProperty.__init__(self)
        # How much the material reflects ambient light.
        self.ambient_color = rgb()
        # How much the material reflects diffuse light.
        self.diffuse_color = rgb()
        # How much light the material reflects in a specular manner.
        self.specular_color = rgb()
        # How much light the material emits.
        self.emissive_color = rgb()
        # The material\'s glossiness.
        self.glossiness = 0.0
        # The material transparency (1=non-transparant). Refer to a NiAlphaProperty
        # block in this material's parent NiTriShape block, when alpha is not 1.
        self.alpha = 0.0



    # read from file, excluding type string
    def read(self, file):
        AProperty.read(self, file)
        self.ambient_color = rgb()
        self.ambient_color.read(file)
        self.diffuse_color = rgb()
        self.diffuse_color.read(file)
        self.specular_color = rgb()
        self.specular_color.read(file)
        self.emissive_color = rgb()
        self.emissive_color.read(file)
        self.glossiness, = struct.unpack('<f', file.read(4))
        self.alpha, = struct.unpack('<f', file.read(4))



    # write to file, including type string
    def write(self, file):
        self.block_type.write(file)
        AProperty.write(self, file)
        self.ambient_color.write(file)
        self.diffuse_color.write(file)
        self.specular_color.write(file)
        self.emissive_color.write(file)
        file.write(struct.pack('<f', self.glossiness))
        file.write(struct.pack('<f', self.alpha))



    # dump to screen
    def __str__(self):
        s = ''
        s += str(self.block_type)
        s += AProperty.__str__(self)
        s += 'ambient_color' + ':\n'
        s += str(self.ambient_color) + '\n'
        s += 'diffuse_color' + ':\n'
        s += str(self.diffuse_color) + '\n'
        s += 'specular_color' + ':\n'
        s += str(self.specular_color) + '\n'
        s += 'emissive_color' + ':\n'
        s += str(self.emissive_color) + '\n'
        s += 'glossiness' + ': %f\n'%self.glossiness
        s += 'alpha' + ': %f\n'%self.alpha
        return s



#
# Geometry morphing data.
#
class NiMorphData:
    # constructor
    def __init__(self):
        self.block_type = mystring("NiMorphData")
        # Number of morphing blocks.
        self.num_morphs = 0
        # Number of vertices.
        self.num_vertices = 0
        # This byte is always 1 in all official files.
        self.unknown_byte = 0
        # The geometry morphing blocks.
        self.morphs = [ None ] * self.num_morphs
        for count in range(self.num_morphs): self.morphs[count] = morphblock(self.num_vertices)



    # read from file, excluding type string
    def read(self, file):
        self.num_morphs, = struct.unpack('<I', file.read(4))
        self.num_vertices, = struct.unpack('<I', file.read(4))
        self.unknown_byte, = struct.unpack('<B', file.read(1))
        if (self.num_morphs > MAX_ARRAYSIZE): raise NIFError('array size unreasonably large (size %i)'%self.num_morphs)
        self.morphs = [ None ] * self.num_morphs
        for count in range(self.num_morphs): self.morphs[count] = morphblock(self.num_vertices)
        for count in range(self.num_morphs):
            self.morphs[count].read(file)



    # write to file, including type string
    def write(self, file):
        self.block_type.write(file)
        file.write(struct.pack('<I', self.num_morphs))
        file.write(struct.pack('<I', self.num_vertices))
        file.write(struct.pack('<b', self.unknown_byte))
        if (self.num_morphs > MAX_ARRAYSIZE): raise NIFError('array size unreasonably large (size %i)'%self.num_morphs)
        for count in range(self.num_morphs):
            self.morphs[count].write(file)



    # dump to screen
    def __str__(self):
        s = ''
        s += str(self.block_type)
        s += 'num_morphs' + ': %i\n'%self.num_morphs
        s += 'num_vertices' + ': %i\n'%self.num_vertices
        s += 'unknown_byte' + ': %i\n'%self.unknown_byte
        if (self.num_morphs <= MAX_ARRAYDUMPSIZE):
            for count in range(self.num_morphs):
                s += 'morphs' + '[%i]'%count + ':\n'
                s += str(self.morphs[count]) + '\n'
        else:
            s += 'morphs: array[%i]\n'%self.num_morphs
        return s



#
# The standard node block.
#
class NiNode(AParentNode):
    # constructor
    def __init__(self):
        self.block_type = mystring("NiNode")
        AParentNode.__init__(self)



    # read from file, excluding type string
    def read(self, file):
        AParentNode.read(self, file)



    # write to file, including type string
    def write(self, file):
        self.block_type.write(file)
        AParentNode.write(self, file)



    # dump to screen
    def __str__(self):
        s = ''
        s += str(self.block_type)
        s += AParentNode.__str__(self)
        return s



#
# Unknown.
#
class NiParticleColorModifier(AControlled):
    # constructor
    def __init__(self):
        self.block_type = mystring("NiParticleColorModifier")
        AControlled.__init__(self)
        # Color data index.
        self.color_data = -1



    # read from file, excluding type string
    def read(self, file):
        AControlled.read(self, file)
        self.color_data, = struct.unpack('<i', file.read(4))



    # write to file, including type string
    def write(self, file):
        self.block_type.write(file)
        AControlled.write(self, file)
        file.write(struct.pack('<i', self.color_data))



    # dump to screen
    def __str__(self):
        s = ''
        s += str(self.block_type)
        s += AControlled.__str__(self)
        s += 'color_data' + ': %i\n'%self.color_data
        return s



#
# Unknown.
#
class NiParticleGrowFade(AControlled):
    # constructor
    def __init__(self):
        self.block_type = mystring("NiParticleGrowFade")
        AControlled.__init__(self)
        # Unknown.
        self.unknown1 = 0.0
        # Unknown.
        self.unknown2 = 0.0



    # read from file, excluding type string
    def read(self, file):
        AControlled.read(self, file)
        self.unknown1, = struct.unpack('<f', file.read(4))
        self.unknown2, = struct.unpack('<f', file.read(4))



    # write to file, including type string
    def write(self, file):
        self.block_type.write(file)
        AControlled.write(self, file)
        file.write(struct.pack('<f', self.unknown1))
        file.write(struct.pack('<f', self.unknown2))



    # dump to screen
    def __str__(self):
        s = ''
        s += str(self.block_type)
        s += AControlled.__str__(self)
        s += 'unknown1' + ': %f\n'%self.unknown1
        s += 'unknown2' + ': %f\n'%self.unknown2
        return s



#
# Unknown.
#
class NiParticleRotation(AControlled):
    # constructor
    def __init__(self):
        self.block_type = mystring("NiParticleRotation")
        AControlled.__init__(self)
        # Unknown.
        self.unknown1 = 0
        # Unknown.
        self.unknown2 = [ None ] * 4
        for count in range(4): self.unknown2[count] = 0.0



    # read from file, excluding type string
    def read(self, file):
        AControlled.read(self, file)
        self.unknown1, = struct.unpack('<B', file.read(1))
        if (4 > MAX_ARRAYSIZE): raise NIFError('array size unreasonably large (size %i)'%4)
        self.unknown2 = [ None ] * 4
        for count in range(4): self.unknown2[count] = 0.0
        for count in range(4):
            self.unknown2[count], = struct.unpack('<f', file.read(4))



    # write to file, including type string
    def write(self, file):
        self.block_type.write(file)
        AControlled.write(self, file)
        file.write(struct.pack('<b', self.unknown1))
        if (4 > MAX_ARRAYSIZE): raise NIFError('array size unreasonably large (size %i)'%4)
        for count in range(4):
            file.write(struct.pack('<f', self.unknown2[count]))



    # dump to screen
    def __str__(self):
        s = ''
        s += str(self.block_type)
        s += AControlled.__str__(self)
        s += 'unknown1' + ': %i\n'%self.unknown1
        if (4 <= MAX_ARRAYDUMPSIZE):
            for count in range(4):
                s += 'unknown2' + '[%i]'%count + ': %f\n'%self.unknown2[count]
        else:
            s += 'unknown2: array[%i]\n'%4
        return s



#
# Time controller for a path.
#
class NiPathController(AController):
    # constructor
    def __init__(self):
        self.block_type = mystring("NiPathController")
        AController.__init__(self)
        # Unknown, always 1?
        self.unknown1 = 0
        # Unknown, always 0?
        self.unknown2 = 0
        # Unknown, always 0?
        self.unknown3 = 0
        # Unknown, always 0?
        self.unknown4 = 0
        # Path controller data index (position data). ?
        self.pos_data = -1
        # Path controller data index (float data). ?
        self.float_data = -1



    # read from file, excluding type string
    def read(self, file):
        AController.read(self, file)
        self.unknown1, = struct.unpack('<I', file.read(4))
        self.unknown2, = struct.unpack('<I', file.read(4))
        self.unknown3, = struct.unpack('<I', file.read(4))
        self.unknown4, = struct.unpack('<H', file.read(2))
        self.pos_data, = struct.unpack('<i', file.read(4))
        self.float_data, = struct.unpack('<i', file.read(4))



    # write to file, including type string
    def write(self, file):
        self.block_type.write(file)
        AController.write(self, file)
        file.write(struct.pack('<I', self.unknown1))
        file.write(struct.pack('<I', self.unknown2))
        file.write(struct.pack('<I', self.unknown3))
        file.write(struct.pack('<H', self.unknown4))
        file.write(struct.pack('<i', self.pos_data))
        file.write(struct.pack('<i', self.float_data))



    # dump to screen
    def __str__(self):
        s = ''
        s += str(self.block_type)
        s += AController.__str__(self)
        s += 'unknown1' + ': %i\n'%self.unknown1
        s += 'unknown2' + ': %i\n'%self.unknown2
        s += 'unknown3' + ': %i\n'%self.unknown3
        s += 'unknown4' + ': %i\n'%self.unknown4
        s += 'pos_data' + ': %i\n'%self.pos_data
        s += 'float_data' + ': %i\n'%self.float_data
        return s



#
# A texture.
#
class NiPixelData:
    # constructor
    def __init__(self):
        self.block_type = mystring("NiPixelData")
        # Unknown. Is usually 0.
        self.unknown1 = 0
        # 0x000000ff
        self.rmask = 0
        # 0x0000ff00
        self.gmask = 0
        # 0x00ff0000
        self.bmask = 0
        # 0xff000000 or 0x00000000
        self.amask = 0
        # Bits per pixel, 24 or 32.
        self.bpp = 0
        # Unknown.
        self.unknown2 = [ None ] * 8
        for count in range(8): self.unknown2[count] = 0
        # Unknown, usually -1.
        self.unknown3 = -1
        # Number of mipmaps in the texture.
        self.num_mipmaps = 0
        # Bytes per pixel (BPP/8).
        self.bytespp = 0
        # Mipmap descriptions (width, height, offset).
        self.mipmaps = [ [ None ] * 3 ] * self.num_mipmaps
        for count in range(self.num_mipmaps):
            for count2 in range(3):
                self.mipmaps[count][count2] = 0
        # Number of bytes that make up all mipmaps.
        self.data_size = 0
        # The mipmaps themselves.
        self.data = [ None ] * self.data_size
        for count in range(self.data_size): self.data[count] = 0



    # read from file, excluding type string
    def read(self, file):
        self.unknown1, = struct.unpack('<I', file.read(4))
        self.rmask, = struct.unpack('<I', file.read(4))
        self.gmask, = struct.unpack('<I', file.read(4))
        self.bmask, = struct.unpack('<I', file.read(4))
        self.amask, = struct.unpack('<I', file.read(4))
        self.bpp, = struct.unpack('<I', file.read(4))
        if (8 > MAX_ARRAYSIZE): raise NIFError('array size unreasonably large (size %i)'%8)
        self.unknown2 = [ None ] * 8
        for count in range(8): self.unknown2[count] = 0
        for count in range(8):
            self.unknown2[count], = struct.unpack('<B', file.read(1))
        self.unknown3, = struct.unpack('<i', file.read(4))
        self.num_mipmaps, = struct.unpack('<I', file.read(4))
        self.bytespp, = struct.unpack('<I', file.read(4))
        if (self.num_mipmaps > MAX_ARRAYSIZE): raise NIFError('array size unreasonably large (size %i)'%self.num_mipmaps)
        if (3 > MAX_ARRAYSIZE): raise NIFError('array size unreasonably large (size %i)'%3)
        self.mipmaps = [ [ None ] * 3 ] * self.num_mipmaps
        for count in range(self.num_mipmaps):
            for count2 in range(3):
                self.mipmaps[count][count2] = 0
        for count in range(self.num_mipmaps):
            for count2 in range(3):
                self.mipmaps[count][count2], = struct.unpack('<I', file.read(4))
        self.data_size, = struct.unpack('<I', file.read(4))
        if (self.data_size > MAX_ARRAYSIZE): raise NIFError('array size unreasonably large (size %i)'%self.data_size)
        self.data = [ None ] * self.data_size
        for count in range(self.data_size): self.data[count] = 0
        for count in range(self.data_size):
            self.data[count], = struct.unpack('<B', file.read(1))



    # write to file, including type string
    def write(self, file):
        self.block_type.write(file)
        file.write(struct.pack('<I', self.unknown1))
        file.write(struct.pack('<I', self.rmask))
        file.write(struct.pack('<I', self.gmask))
        file.write(struct.pack('<I', self.bmask))
        file.write(struct.pack('<I', self.amask))
        file.write(struct.pack('<I', self.bpp))
        if (8 > MAX_ARRAYSIZE): raise NIFError('array size unreasonably large (size %i)'%8)
        for count in range(8):
            file.write(struct.pack('<b', self.unknown2[count]))
        file.write(struct.pack('<i', self.unknown3))
        file.write(struct.pack('<I', self.num_mipmaps))
        file.write(struct.pack('<I', self.bytespp))
        if (self.num_mipmaps > MAX_ARRAYSIZE): raise NIFError('array size unreasonably large (size %i)'%self.num_mipmaps)
        if (3 > MAX_ARRAYSIZE): raise NIFError('array size unreasonably large (size %i)'%3)
        for count in range(self.num_mipmaps):
            for count2 in range(3):
                file.write(struct.pack('<I', self.mipmaps[count][count2]))
        file.write(struct.pack('<I', self.data_size))
        if (self.data_size > MAX_ARRAYSIZE): raise NIFError('array size unreasonably large (size %i)'%self.data_size)
        for count in range(self.data_size):
            file.write(struct.pack('<b', self.data[count]))



    # dump to screen
    def __str__(self):
        s = ''
        s += str(self.block_type)
        s += 'unknown1' + ': %i\n'%self.unknown1
        s += 'rmask' + ': %i\n'%self.rmask
        s += 'gmask' + ': %i\n'%self.gmask
        s += 'bmask' + ': %i\n'%self.bmask
        s += 'amask' + ': %i\n'%self.amask
        s += 'bpp' + ': %i\n'%self.bpp
        if (8 <= MAX_ARRAYDUMPSIZE):
            for count in range(8):
                s += 'unknown2' + '[%i]'%count + ': %i\n'%self.unknown2[count]
        else:
            s += 'unknown2: array[%i]\n'%8
        s += 'unknown3' + ': %i\n'%self.unknown3
        s += 'num_mipmaps' + ': %i\n'%self.num_mipmaps
        s += 'bytespp' + ': %i\n'%self.bytespp
        s += 'mipmaps: array[%i][%i]\n'%(self.num_mipmaps,3)
        s += 'data_size' + ': %i\n'%self.data_size
        if (self.data_size <= MAX_ARRAYDUMPSIZE):
            for count in range(self.data_size):
                s += 'data' + '[%i]'%count + ': %i\n'%self.data[count]
        else:
            s += 'data: array[%i]\n'%self.data_size
        return s



#
# Unknown.
#
class NiPlanarCollider(AControlled):
    # constructor
    def __init__(self):
        self.block_type = mystring("NiPlanarCollider")
        AControlled.__init__(self)
        # Unknown.
        self.unknown = [ None ] * 16
        for count in range(16): self.unknown[count] = 0.0



    # read from file, excluding type string
    def read(self, file):
        AControlled.read(self, file)
        if (16 > MAX_ARRAYSIZE): raise NIFError('array size unreasonably large (size %i)'%16)
        self.unknown = [ None ] * 16
        for count in range(16): self.unknown[count] = 0.0
        for count in range(16):
            self.unknown[count], = struct.unpack('<f', file.read(4))



    # write to file, including type string
    def write(self, file):
        self.block_type.write(file)
        AControlled.write(self, file)
        if (16 > MAX_ARRAYSIZE): raise NIFError('array size unreasonably large (size %i)'%16)
        for count in range(16):
            file.write(struct.pack('<f', self.unknown[count]))



    # dump to screen
    def __str__(self):
        s = ''
        s += str(self.block_type)
        s += AControlled.__str__(self)
        if (16 <= MAX_ARRAYDUMPSIZE):
            for count in range(16):
                s += 'unknown' + '[%i]'%count + ': %f\n'%self.unknown[count]
        else:
            s += 'unknown: array[%i]\n'%16
        return s



#
# Position data.
#
class NiPosData:
    # constructor
    def __init__(self):
        self.block_type = mystring("NiPosData")
        # Number of position keys.
        self.num_keys = 0
        # Position key type.
        self.key_type = 0
        # The position keys.
        self.keys = [ None ] * self.num_keys
        for count in range(self.num_keys): self.keys[count] = keyvec3(self.key_type)



    # read from file, excluding type string
    def read(self, file):
        self.num_keys, = struct.unpack('<I', file.read(4))
        self.key_type, = struct.unpack('<I', file.read(4))
        if (self.num_keys > MAX_ARRAYSIZE): raise NIFError('array size unreasonably large (size %i)'%self.num_keys)
        self.keys = [ None ] * self.num_keys
        for count in range(self.num_keys): self.keys[count] = keyvec3(self.key_type)
        for count in range(self.num_keys):
            self.keys[count].read(file)



    # write to file, including type string
    def write(self, file):
        self.block_type.write(file)
        file.write(struct.pack('<I', self.num_keys))
        file.write(struct.pack('<I', self.key_type))
        if (self.num_keys > MAX_ARRAYSIZE): raise NIFError('array size unreasonably large (size %i)'%self.num_keys)
        for count in range(self.num_keys):
            self.keys[count].write(file)



    # dump to screen
    def __str__(self):
        s = ''
        s += str(self.block_type)
        s += 'num_keys' + ': %i\n'%self.num_keys
        s += 'key_type' + ': %i\n'%self.key_type
        if (self.num_keys <= MAX_ARRAYDUMPSIZE):
            for count in range(self.num_keys):
                s += 'keys' + '[%i]'%count + ':\n'
                s += str(self.keys[count]) + '\n'
        else:
            s += 'keys: array[%i]\n'%self.num_keys
        return s



#
# Unknown.
#
class NiRotatingParticles(ANode):
    # constructor
    def __init__(self):
        self.block_type = mystring("NiRotatingParticles")
        ANode.__init__(self)
        # Rotating particles data index.
        self.data = -1
        # Unknown (always -1?).
        self.unknown = -1



    # read from file, excluding type string
    def read(self, file):
        ANode.read(self, file)
        self.data, = struct.unpack('<i', file.read(4))
        self.unknown, = struct.unpack('<i', file.read(4))



    # write to file, including type string
    def write(self, file):
        self.block_type.write(file)
        ANode.write(self, file)
        file.write(struct.pack('<i', self.data))
        file.write(struct.pack('<i', self.unknown))



    # dump to screen
    def __str__(self):
        s = ''
        s += str(self.block_type)
        s += ANode.__str__(self)
        s += 'data' + ': %i\n'%self.data
        s += 'unknown' + ': %i\n'%self.unknown
        return s



#
# Keyframe animation data node?
#
class NiSequenceStreamHelper(ANamed):
    # constructor
    def __init__(self):
        self.block_type = mystring("NiSequenceStreamHelper")
        ANamed.__init__(self)



    # read from file, excluding type string
    def read(self, file):
        ANamed.read(self, file)



    # write to file, including type string
    def write(self, file):
        self.block_type.write(file)
        ANamed.write(self, file)



    # dump to screen
    def __str__(self):
        s = ''
        s += str(self.block_type)
        s += ANamed.__str__(self)
        return s



#
# Unknown.
#
class NiShadeProperty(AProperty):
    # constructor
    def __init__(self):
        self.block_type = mystring("NiShadeProperty")
        AProperty.__init__(self)



    # read from file, excluding type string
    def read(self, file):
        AProperty.read(self, file)



    # write to file, including type string
    def write(self, file):
        self.block_type.write(file)
        AProperty.write(self, file)



    # dump to screen
    def __str__(self):
        s = ''
        s += str(self.block_type)
        s += AProperty.__str__(self)
        return s



#
# Skinning data.
#
class NiSkinData:
    # constructor
    def __init__(self):
        self.block_type = mystring("NiSkinData")
        # The overall rotation offset of the skin from this bone in the bind
        # position.
        # (This is a guess, it has always been the identity matrix so far)
        self.overall_rotation_offset = mat3x3()
        # The overall translation offset of the skin from this bone in the bind
        # position. (This is a guess, it has always been (0.0, 0.0, 0.0) so far)
        self.overall_translation_offset = vec3()
        # The scale offset of the skin from this bone in the bind position. (This is
        # an assumption - it has always been 1.0 so far)
        self.scale_offset = 0.0
        # Number of bones.
        self.num_bones = 0
        # This may be an index.  It has always been -1 so far.
        self.unknown_index_ = -1
        # Contains offset data for each node that this skin is influenced by.
        self.bone_list = [ None ] * self.num_bones
        for count in range(self.num_bones): self.bone_list[count] = skinblock()



    # read from file, excluding type string
    def read(self, file):
        self.overall_rotation_offset = mat3x3()
        self.overall_rotation_offset.read(file)
        self.overall_translation_offset = vec3()
        self.overall_translation_offset.read(file)
        self.scale_offset, = struct.unpack('<f', file.read(4))
        self.num_bones, = struct.unpack('<I', file.read(4))
        self.unknown_index_, = struct.unpack('<i', file.read(4))
        if (self.num_bones > MAX_ARRAYSIZE): raise NIFError('array size unreasonably large (size %i)'%self.num_bones)
        self.bone_list = [ None ] * self.num_bones
        for count in range(self.num_bones): self.bone_list[count] = skinblock()
        for count in range(self.num_bones):
            self.bone_list[count].read(file)



    # write to file, including type string
    def write(self, file):
        self.block_type.write(file)
        self.overall_rotation_offset.write(file)
        self.overall_translation_offset.write(file)
        file.write(struct.pack('<f', self.scale_offset))
        file.write(struct.pack('<I', self.num_bones))
        file.write(struct.pack('<i', self.unknown_index_))
        if (self.num_bones > MAX_ARRAYSIZE): raise NIFError('array size unreasonably large (size %i)'%self.num_bones)
        for count in range(self.num_bones):
            self.bone_list[count].write(file)



    # dump to screen
    def __str__(self):
        s = ''
        s += str(self.block_type)
        s += 'overall_rotation_offset' + ':\n'
        s += str(self.overall_rotation_offset) + '\n'
        s += 'overall_translation_offset' + ':\n'
        s += str(self.overall_translation_offset) + '\n'
        s += 'scale_offset' + ': %f\n'%self.scale_offset
        s += 'num_bones' + ': %i\n'%self.num_bones
        s += 'unknown_index_' + ': %i\n'%self.unknown_index_
        if (self.num_bones <= MAX_ARRAYDUMPSIZE):
            for count in range(self.num_bones):
                s += 'bone_list' + '[%i]'%count + ':\n'
                s += str(self.bone_list[count]) + '\n'
        else:
            s += 'bone_list: array[%i]\n'%self.num_bones
        return s



#
# Skinning instance.
#
class NiSkinInstance:
    # constructor
    def __init__(self):
        self.block_type = mystring("NiSkinInstance")
        # Skinning data reference.
        self.data = -1
        # Armature root node.
        self.skeleton_root = -1
        # List of all armature bones.
        self.bones = indexlist()



    # read from file, excluding type string
    def read(self, file):
        self.data, = struct.unpack('<i', file.read(4))
        self.skeleton_root, = struct.unpack('<i', file.read(4))
        self.bones = indexlist()
        self.bones.read(file)



    # write to file, including type string
    def write(self, file):
        self.block_type.write(file)
        file.write(struct.pack('<i', self.data))
        file.write(struct.pack('<i', self.skeleton_root))
        self.bones.write(file)



    # dump to screen
    def __str__(self):
        s = ''
        s += str(self.block_type)
        s += 'data' + ': %i\n'%self.data
        s += 'skeleton_root' + ': %i\n'%self.skeleton_root
        s += 'bones' + ':\n'
        s += str(self.bones) + '\n'
        return s



#
# Describes texture source and properties.
#
class NiSourceTexture(ANamed):
    # constructor
    def __init__(self):
        self.block_type = mystring("NiSourceTexture")
        ANamed.__init__(self)
        # Is the texture external (for Morrowind, always 1)?
        self.use_external = 0
        # The external texture file name.
        self.file_name = string()
        # Unknown.
        self.unknown1 = 0
        # Pixel data block index.
        self.pixel_data = -1
        # 0=palettised, 1=16-bit, 2=32-bit, 3=compressed, 4=bumpmap, 5=default
        self.pixel_layout = 0
        # 0=no, 1=yes, 2=default
        self.use_mipmaps = 0
        # 0=ignore texture alpha channel and use material alpha setting
        # 1=binary (?)
        # 2=smooth (?)
        # 3=texture alpha channel overides the material alpha setting
        self.alpha_format = 0
        # Unknown, usually 1.
        self.unknown2 = 0



    # read from file, excluding type string
    def read(self, file):
        ANamed.read(self, file)
        self.use_external, = struct.unpack('<B', file.read(1))
        self.file_name = string()
        if (self.use_external == 1):
            self.file_name.read(file)
        self.unknown1 = 0
        if (self.use_external == 0):
            self.unknown1, = struct.unpack('<B', file.read(1))
        self.pixel_data = -1
        if (self.use_external == 0):
            self.pixel_data, = struct.unpack('<i', file.read(4))
        self.pixel_layout, = struct.unpack('<I', file.read(4))
        self.use_mipmaps, = struct.unpack('<I', file.read(4))
        self.alpha_format, = struct.unpack('<I', file.read(4))
        self.unknown2, = struct.unpack('<B', file.read(1))



    # write to file, including type string
    def write(self, file):
        self.block_type.write(file)
        ANamed.write(self, file)
        file.write(struct.pack('<b', self.use_external))
        if (self.use_external == 1):
            self.file_name.write(file)
        if (self.use_external == 0):
            file.write(struct.pack('<b', self.unknown1))
        if (self.use_external == 0):
            file.write(struct.pack('<i', self.pixel_data))
        file.write(struct.pack('<I', self.pixel_layout))
        file.write(struct.pack('<I', self.use_mipmaps))
        file.write(struct.pack('<I', self.alpha_format))
        file.write(struct.pack('<b', self.unknown2))



    # dump to screen
    def __str__(self):
        s = ''
        s += str(self.block_type)
        s += ANamed.__str__(self)
        s += 'use_external' + ': %i\n'%self.use_external
        if (self.use_external == 1):
            s += 'file_name' + ':\n'
            s += str(self.file_name) + '\n'
        if (self.use_external == 0):
            s += 'unknown1' + ': %i\n'%self.unknown1
        if (self.use_external == 0):
            s += 'pixel_data' + ': %i\n'%self.pixel_data
        s += 'pixel_layout' + ': %i\n'%self.pixel_layout
        s += 'use_mipmaps' + ': %i\n'%self.use_mipmaps
        s += 'alpha_format' + ': %i\n'%self.alpha_format
        s += 'unknown2' + ': %i\n'%self.unknown2
        return s



#
# Gives specularity to NiTriShape. Flags 0x0001.
#
class NiSpecularProperty(AProperty):
    # constructor
    def __init__(self):
        self.block_type = mystring("NiSpecularProperty")
        AProperty.__init__(self)



    # read from file, excluding type string
    def read(self, file):
        AProperty.read(self, file)



    # write to file, including type string
    def write(self, file):
        self.block_type.write(file)
        AProperty.write(self, file)



    # dump to screen
    def __str__(self):
        s = ''
        s += str(self.block_type)
        s += AProperty.__str__(self)
        return s



#
# Apparently commands for an optimizer instructing it to keep things it
# would normally discard.
# Also refers to NiNode blocks (through their name) in animation .kf files.
#
class NiStringExtraData(AExtraData):
    # constructor
    def __init__(self):
        self.block_type = mystring("NiStringExtraData")
        AExtraData.__init__(self)
        # The number of bytes left in the record.  Equals the length of the following
        # string + 4.
        self.bytes_remaining = 0
        # The string.
        self.string_data = string()



    # read from file, excluding type string
    def read(self, file):
        AExtraData.read(self, file)
        self.bytes_remaining, = struct.unpack('<I', file.read(4))
        self.string_data = string()
        self.string_data.read(file)



    # write to file, including type string
    def write(self, file):
        self.block_type.write(file)
        AExtraData.write(self, file)
        file.write(struct.pack('<I', self.bytes_remaining))
        self.string_data.write(file)



    # dump to screen
    def __str__(self):
        s = ''
        s += str(self.block_type)
        s += AExtraData.__str__(self)
        s += 'bytes_remaining' + ': %i\n'%self.bytes_remaining
        s += 'string_data' + ':\n'
        s += str(self.string_data) + '\n'
        return s



#
# Extra data, used to name different animation sequences.
#
class NiTextKeyExtraData(AExtraData):
    # constructor
    def __init__(self):
        self.block_type = mystring("NiTextKeyExtraData")
        AExtraData.__init__(self)
        # Unknown.  Always equals zero in all official files.
        self.unknown_int = 0
        # Number of text keys in this data block.
        self.num_text_keys = 0
        # List of textual notes and at which time they take effect.  Used for
        # designating the start and stop of animations and the triggering of sounds.
        self.text_keys = [ None ] * self.num_text_keys
        for count in range(self.num_text_keys): self.text_keys[count] = keystring()



    # read from file, excluding type string
    def read(self, file):
        AExtraData.read(self, file)
        self.unknown_int, = struct.unpack('<I', file.read(4))
        self.num_text_keys, = struct.unpack('<I', file.read(4))
        if (self.num_text_keys > MAX_ARRAYSIZE): raise NIFError('array size unreasonably large (size %i)'%self.num_text_keys)
        self.text_keys = [ None ] * self.num_text_keys
        for count in range(self.num_text_keys): self.text_keys[count] = keystring()
        for count in range(self.num_text_keys):
            self.text_keys[count].read(file)



    # write to file, including type string
    def write(self, file):
        self.block_type.write(file)
        AExtraData.write(self, file)
        file.write(struct.pack('<I', self.unknown_int))
        file.write(struct.pack('<I', self.num_text_keys))
        if (self.num_text_keys > MAX_ARRAYSIZE): raise NIFError('array size unreasonably large (size %i)'%self.num_text_keys)
        for count in range(self.num_text_keys):
            self.text_keys[count].write(file)



    # dump to screen
    def __str__(self):
        s = ''
        s += str(self.block_type)
        s += AExtraData.__str__(self)
        s += 'unknown_int' + ': %i\n'%self.unknown_int
        s += 'num_text_keys' + ': %i\n'%self.num_text_keys
        if (self.num_text_keys <= MAX_ARRAYDUMPSIZE):
            for count in range(self.num_text_keys):
                s += 'text_keys' + '[%i]'%count + ':\n'
                s += str(self.text_keys[count]) + '\n'
        else:
            s += 'text_keys: array[%i]\n'%self.num_text_keys
        return s



#
# Unknown.
#
class NiTextureEffect(ANode):
    # constructor
    def __init__(self):
        self.block_type = mystring("NiTextureEffect")
        ANode.__init__(self)
        # Unknown.
        self.has_unknown1 = 0
        # Unknown.
        self.unknown1 = 0
        # Unknown: (1,0,0,0), (1,0,0,0), (1,0,0,0)
        self.unknown2 = [ None ] * 12
        for count in range(12): self.unknown2[count] = 0.0
        # Unknown: (2,3,2,2) or (2,0,2,2)
        self.unknown3 = [ None ] * 4
        for count in range(4): self.unknown3[count] = 0
        # Source texture index.
        self.source_texture = -1
        # Unknown: 0?
        self.unknown4 = 0
        # Unknown: (1,0,0,0)?
        self.unknown5 = [ None ] * 4
        for count in range(4): self.unknown5[count] = 0.0
        # 0?
        self.ps2_l = 0
        # 0xFFB5?
        self.ps2_k = 0
        # Unknown: 0.
        self.unknown6 = 0



    # read from file, excluding type string
    def read(self, file):
        ANode.read(self, file)
        self.has_unknown1, = struct.unpack('<I', file.read(4))
        self.unknown1 = 0
        if (self.has_unknown1 != 0):
            self.unknown1, = struct.unpack('<I', file.read(4))
        if (12 > MAX_ARRAYSIZE): raise NIFError('array size unreasonably large (size %i)'%12)
        self.unknown2 = [ None ] * 12
        for count in range(12): self.unknown2[count] = 0.0
        for count in range(12):
            self.unknown2[count], = struct.unpack('<f', file.read(4))
        if (4 > MAX_ARRAYSIZE): raise NIFError('array size unreasonably large (size %i)'%4)
        self.unknown3 = [ None ] * 4
        for count in range(4): self.unknown3[count] = 0
        for count in range(4):
            self.unknown3[count], = struct.unpack('<I', file.read(4))
        self.source_texture, = struct.unpack('<i', file.read(4))
        self.unknown4, = struct.unpack('<B', file.read(1))
        if (4 > MAX_ARRAYSIZE): raise NIFError('array size unreasonably large (size %i)'%4)
        self.unknown5 = [ None ] * 4
        for count in range(4): self.unknown5[count] = 0.0
        for count in range(4):
            self.unknown5[count], = struct.unpack('<f', file.read(4))
        self.ps2_l, = struct.unpack('<H', file.read(2))
        self.ps2_k, = struct.unpack('<H', file.read(2))
        self.unknown6, = struct.unpack('<H', file.read(2))



    # write to file, including type string
    def write(self, file):
        self.block_type.write(file)
        ANode.write(self, file)
        file.write(struct.pack('<I', self.has_unknown1))
        if (self.has_unknown1 != 0):
            file.write(struct.pack('<I', self.unknown1))
        if (12 > MAX_ARRAYSIZE): raise NIFError('array size unreasonably large (size %i)'%12)
        for count in range(12):
            file.write(struct.pack('<f', self.unknown2[count]))
        if (4 > MAX_ARRAYSIZE): raise NIFError('array size unreasonably large (size %i)'%4)
        for count in range(4):
            file.write(struct.pack('<I', self.unknown3[count]))
        file.write(struct.pack('<i', self.source_texture))
        file.write(struct.pack('<b', self.unknown4))
        if (4 > MAX_ARRAYSIZE): raise NIFError('array size unreasonably large (size %i)'%4)
        for count in range(4):
            file.write(struct.pack('<f', self.unknown5[count]))
        file.write(struct.pack('<H', self.ps2_l))
        file.write(struct.pack('<H', self.ps2_k))
        file.write(struct.pack('<H', self.unknown6))



    # dump to screen
    def __str__(self):
        s = ''
        s += str(self.block_type)
        s += ANode.__str__(self)
        s += 'has_unknown1' + ': %i\n'%self.has_unknown1
        if (self.has_unknown1 != 0):
            s += 'unknown1' + ': %i\n'%self.unknown1
        if (12 <= MAX_ARRAYDUMPSIZE):
            for count in range(12):
                s += 'unknown2' + '[%i]'%count + ': %f\n'%self.unknown2[count]
        else:
            s += 'unknown2: array[%i]\n'%12
        if (4 <= MAX_ARRAYDUMPSIZE):
            for count in range(4):
                s += 'unknown3' + '[%i]'%count + ': %i\n'%self.unknown3[count]
        else:
            s += 'unknown3: array[%i]\n'%4
        s += 'source_texture' + ': %i\n'%self.source_texture
        s += 'unknown4' + ': %i\n'%self.unknown4
        if (4 <= MAX_ARRAYDUMPSIZE):
            for count in range(4):
                s += 'unknown5' + '[%i]'%count + ': %f\n'%self.unknown5[count]
        else:
            s += 'unknown5: array[%i]\n'%4
        s += 'ps2_l' + ': %i\n'%self.ps2_l
        s += 'ps2_k' + ': %i\n'%self.ps2_k
        s += 'unknown6' + ': %i\n'%self.unknown6
        return s



#
# Describes an object's textures.
#
class NiTexturingProperty(AProperty):
    # constructor
    def __init__(self):
        self.block_type = mystring("NiTexturingProperty")
        AProperty.__init__(self)
        # 0=replace, 1=decal, 2=modulate, 3=hilight, 4=hilight2
        self.apply_mode = 0
        # Is always 7.
        self.texture_count = 0
        # Do we have a base texture?
        self.has_base_texture = 0
        # The base texture.
        self.base_texture = texture()
        # Do we have a dark texture?
        self.has_dark_texture = 0
        # The dark texture.
        self.dark_texture = texture()
        # Do we have a detail texture?
        self.has_detail_texture = 0
        # The detail texture.
        self.detail_texture = texture()
        # Do we have a gloss texture?
        self.has_gloss_texture = 0
        # The gloss texture.
        self.gloss_texture = texture()
        # Do we have a glow texture?
        self.has_glow_texture = 0
        # The glowing texture.
        self.glow_texture = texture()
        # Do we have a bump map texture? (Unsupported in Morrowind.)
        self.has_bump_map_texture = 0
        # The bump map texture.
        self.bump_map_texture = texture()
        # ?
        self.luma_scale = 0.0
        # ?
        self.luma_offset = 0.0
        # ?
        self.matrix = [ [ None ] * 2 ] * 2
        for count in range(2):
            for count2 in range(2):
                self.matrix[count][count2] = 0.0
        # Do we have a decal texture?
        self.has_decal_texture = 0
        # The decal texture.
        self.decal_texture = texture()



    # read from file, excluding type string
    def read(self, file):
        AProperty.read(self, file)
        self.apply_mode, = struct.unpack('<I', file.read(4))
        self.texture_count, = struct.unpack('<I', file.read(4))
        self.has_base_texture, = struct.unpack('<I', file.read(4))
        self.base_texture = texture()
        if (self.has_base_texture != 0):
            self.base_texture.read(file)
        self.has_dark_texture, = struct.unpack('<I', file.read(4))
        self.dark_texture = texture()
        if (self.has_dark_texture != 0):
            self.dark_texture.read(file)
        self.has_detail_texture, = struct.unpack('<I', file.read(4))
        self.detail_texture = texture()
        if (self.has_detail_texture != 0):
            self.detail_texture.read(file)
        self.has_gloss_texture, = struct.unpack('<I', file.read(4))
        self.gloss_texture = texture()
        if (self.has_gloss_texture != 0):
            self.gloss_texture.read(file)
        self.has_glow_texture, = struct.unpack('<I', file.read(4))
        self.glow_texture = texture()
        if (self.has_glow_texture != 0):
            self.glow_texture.read(file)
        self.has_bump_map_texture, = struct.unpack('<I', file.read(4))
        self.bump_map_texture = texture()
        if (self.has_bump_map_texture != 0):
            self.bump_map_texture.read(file)
        self.luma_scale = 0.0
        if (self.has_bump_map_texture != 0):
            self.luma_scale, = struct.unpack('<f', file.read(4))
        self.luma_offset = 0.0
        if (self.has_bump_map_texture != 0):
            self.luma_offset, = struct.unpack('<f', file.read(4))
        if (2 > MAX_ARRAYSIZE): raise NIFError('array size unreasonably large (size %i)'%2)
        if (2 > MAX_ARRAYSIZE): raise NIFError('array size unreasonably large (size %i)'%2)
        self.matrix = [ [ None ] * 2 ] * 2
        for count in range(2):
            for count2 in range(2):
                self.matrix[count][count2] = 0.0
        if (self.has_bump_map_texture != 0):
            for count in range(2):
                for count2 in range(2):
                    self.matrix[count][count2], = struct.unpack('<f', file.read(4))
        self.has_decal_texture, = struct.unpack('<I', file.read(4))
        self.decal_texture = texture()
        if (self.has_decal_texture != 0):
            self.decal_texture.read(file)



    # write to file, including type string
    def write(self, file):
        self.block_type.write(file)
        AProperty.write(self, file)
        file.write(struct.pack('<I', self.apply_mode))
        file.write(struct.pack('<I', self.texture_count))
        file.write(struct.pack('<I', self.has_base_texture))
        if (self.has_base_texture != 0):
            self.base_texture.write(file)
        file.write(struct.pack('<I', self.has_dark_texture))
        if (self.has_dark_texture != 0):
            self.dark_texture.write(file)
        file.write(struct.pack('<I', self.has_detail_texture))
        if (self.has_detail_texture != 0):
            self.detail_texture.write(file)
        file.write(struct.pack('<I', self.has_gloss_texture))
        if (self.has_gloss_texture != 0):
            self.gloss_texture.write(file)
        file.write(struct.pack('<I', self.has_glow_texture))
        if (self.has_glow_texture != 0):
            self.glow_texture.write(file)
        file.write(struct.pack('<I', self.has_bump_map_texture))
        if (self.has_bump_map_texture != 0):
            self.bump_map_texture.write(file)
        if (self.has_bump_map_texture != 0):
            file.write(struct.pack('<f', self.luma_scale))
        if (self.has_bump_map_texture != 0):
            file.write(struct.pack('<f', self.luma_offset))
        if (2 > MAX_ARRAYSIZE): raise NIFError('array size unreasonably large (size %i)'%2)
        if (2 > MAX_ARRAYSIZE): raise NIFError('array size unreasonably large (size %i)'%2)
        if (self.has_bump_map_texture != 0):
            for count in range(2):
                for count2 in range(2):
                    file.write(struct.pack('<f', self.matrix[count][count2]))
        file.write(struct.pack('<I', self.has_decal_texture))
        if (self.has_decal_texture != 0):
            self.decal_texture.write(file)



    # dump to screen
    def __str__(self):
        s = ''
        s += str(self.block_type)
        s += AProperty.__str__(self)
        s += 'apply_mode' + ': %i\n'%self.apply_mode
        s += 'texture_count' + ': %i\n'%self.texture_count
        s += 'has_base_texture' + ': %i\n'%self.has_base_texture
        if (self.has_base_texture != 0):
            s += 'base_texture' + ':\n'
            s += str(self.base_texture) + '\n'
        s += 'has_dark_texture' + ': %i\n'%self.has_dark_texture
        if (self.has_dark_texture != 0):
            s += 'dark_texture' + ':\n'
            s += str(self.dark_texture) + '\n'
        s += 'has_detail_texture' + ': %i\n'%self.has_detail_texture
        if (self.has_detail_texture != 0):
            s += 'detail_texture' + ':\n'
            s += str(self.detail_texture) + '\n'
        s += 'has_gloss_texture' + ': %i\n'%self.has_gloss_texture
        if (self.has_gloss_texture != 0):
            s += 'gloss_texture' + ':\n'
            s += str(self.gloss_texture) + '\n'
        s += 'has_glow_texture' + ': %i\n'%self.has_glow_texture
        if (self.has_glow_texture != 0):
            s += 'glow_texture' + ':\n'
            s += str(self.glow_texture) + '\n'
        s += 'has_bump_map_texture' + ': %i\n'%self.has_bump_map_texture
        if (self.has_bump_map_texture != 0):
            s += 'bump_map_texture' + ':\n'
            s += str(self.bump_map_texture) + '\n'
        if (self.has_bump_map_texture != 0):
            s += 'luma_scale' + ': %f\n'%self.luma_scale
        if (self.has_bump_map_texture != 0):
            s += 'luma_offset' + ': %f\n'%self.luma_offset
        if (self.has_bump_map_texture != 0):
            s += 'matrix: array[%i][%i]\n'%(2,2)
        s += 'has_decal_texture' + ': %i\n'%self.has_decal_texture
        if (self.has_decal_texture != 0):
            s += 'decal_texture' + ':\n'
            s += str(self.decal_texture) + '\n'
        return s



#
# Describes a mesh, built from triangles.
#
class NiTriShape(ANode):
    # constructor
    def __init__(self):
        self.block_type = mystring("NiTriShape")
        ANode.__init__(self)
        # Data index (NiTriShapeData).
        self.data = -1
        # Skin instance index.
        self.skin_instance = -1



    # read from file, excluding type string
    def read(self, file):
        ANode.read(self, file)
        self.data, = struct.unpack('<i', file.read(4))
        self.skin_instance, = struct.unpack('<i', file.read(4))



    # write to file, including type string
    def write(self, file):
        self.block_type.write(file)
        ANode.write(self, file)
        file.write(struct.pack('<i', self.data))
        file.write(struct.pack('<i', self.skin_instance))



    # dump to screen
    def __str__(self):
        s = ''
        s += str(self.block_type)
        s += ANode.__str__(self)
        s += 'data' + ': %i\n'%self.data
        s += 'skin_instance' + ': %i\n'%self.skin_instance
        return s



#
# Mesh data: vertices, vertex normals, etc.
#
class NiTriShapeData:
    # constructor
    def __init__(self):
        self.block_type = mystring("NiTriShapeData")
        # Number of vertices.
        self.num_vertices = 0
        # Is the vertex array present? (Always non-zero.)
        self.has_vertices = 0
        # The mesh vertices.
        self.vertices = [ None ] * self.num_vertices
        for count in range(self.num_vertices): self.vertices[count] = vec3()
        # Do we have lighting normals? These are essential for proper lighting: if
        # not present, the model will only be influenced by ambient light.
        self.has_normals = 0
        # The lighting normals.
        self.normals = [ None ] * self.num_vertices
        for count in range(self.num_vertices): self.normals[count] = vec3()
        # Center of the mesh.
        self.center = vec3()
        # Radius of the mesh.
        self.radius = 0.0
        # Do we have vertex colours? These are used to fine-tune the lighting of the
        # model.
        self.has_vertex_colors = 0
        # The vertex colors.
        self.vertex_colors = [ None ] * self.num_vertices
        for count in range(self.num_vertices): self.vertex_colors[count] = rgba()
        # Number of UV texture sets.
        self.num_uv_sets = 0
        # Do we have UV coordinates?
        self.has_uv = 0
        # The UV texture coordinates.
        self.uv_sets = [ [ None ] * self.num_vertices ] * self.num_uv_sets
        for count in range(self.num_uv_sets):
            for count2 in range(self.num_vertices):
                self.uv_sets[count][count2] = vec2()
        # Number of faces.
        self.num_faces = 0
        # Num Faces, times three.
        self.num_faces_x3 = 0
        # The mesh faces, as a list of triples of vertex indices.
        self.faces = [ None ] * self.num_faces
        for count in range(self.num_faces): self.faces[count] = face()
        # Number of vertex matching groups.
        self.num_match_groups = 0
        # The matching vertex groups.
        self.match_groups = [ None ] * self.num_match_groups
        for count in range(self.num_match_groups): self.match_groups[count] = matchgroup()



    # read from file, excluding type string
    def read(self, file):
        self.num_vertices, = struct.unpack('<H', file.read(2))
        self.has_vertices, = struct.unpack('<I', file.read(4))
        if (self.num_vertices > MAX_ARRAYSIZE): raise NIFError('array size unreasonably large (size %i)'%self.num_vertices)
        self.vertices = [ None ] * self.num_vertices
        for count in range(self.num_vertices): self.vertices[count] = vec3()
        if (self.has_vertices != 0):
            for count in range(self.num_vertices):
                self.vertices[count].read(file)
        self.has_normals, = struct.unpack('<I', file.read(4))
        if (self.num_vertices > MAX_ARRAYSIZE): raise NIFError('array size unreasonably large (size %i)'%self.num_vertices)
        self.normals = [ None ] * self.num_vertices
        for count in range(self.num_vertices): self.normals[count] = vec3()
        if (self.has_normals != 0):
            for count in range(self.num_vertices):
                self.normals[count].read(file)
        self.center = vec3()
        self.center.read(file)
        self.radius, = struct.unpack('<f', file.read(4))
        self.has_vertex_colors, = struct.unpack('<I', file.read(4))
        if (self.num_vertices > MAX_ARRAYSIZE): raise NIFError('array size unreasonably large (size %i)'%self.num_vertices)
        self.vertex_colors = [ None ] * self.num_vertices
        for count in range(self.num_vertices): self.vertex_colors[count] = rgba()
        if (self.has_vertex_colors != 0):
            for count in range(self.num_vertices):
                self.vertex_colors[count].read(file)
        self.num_uv_sets, = struct.unpack('<H', file.read(2))
        self.has_uv, = struct.unpack('<I', file.read(4))
        if (self.num_uv_sets > MAX_ARRAYSIZE): raise NIFError('array size unreasonably large (size %i)'%self.num_uv_sets)
        if (self.num_vertices > MAX_ARRAYSIZE): raise NIFError('array size unreasonably large (size %i)'%self.num_vertices)
        self.uv_sets = [ [ None ] * self.num_vertices ] * self.num_uv_sets
        for count in range(self.num_uv_sets):
            for count2 in range(self.num_vertices):
                self.uv_sets[count][count2] = vec2()
        if (self.has_uv != 0):
            for count in range(self.num_uv_sets):
                for count2 in range(self.num_vertices):
                    self.uv_sets[count][count2].read(file)
        self.num_faces, = struct.unpack('<H', file.read(2))
        self.num_faces_x3, = struct.unpack('<I', file.read(4))
        if (self.num_faces > MAX_ARRAYSIZE): raise NIFError('array size unreasonably large (size %i)'%self.num_faces)
        self.faces = [ None ] * self.num_faces
        for count in range(self.num_faces): self.faces[count] = face()
        for count in range(self.num_faces):
            self.faces[count].read(file)
        self.num_match_groups, = struct.unpack('<H', file.read(2))
        if (self.num_match_groups > MAX_ARRAYSIZE): raise NIFError('array size unreasonably large (size %i)'%self.num_match_groups)
        self.match_groups = [ None ] * self.num_match_groups
        for count in range(self.num_match_groups): self.match_groups[count] = matchgroup()
        for count in range(self.num_match_groups):
            self.match_groups[count].read(file)



    # write to file, including type string
    def write(self, file):
        self.block_type.write(file)
        file.write(struct.pack('<H', self.num_vertices))
        file.write(struct.pack('<I', self.has_vertices))
        if (self.num_vertices > MAX_ARRAYSIZE): raise NIFError('array size unreasonably large (size %i)'%self.num_vertices)
        if (self.has_vertices != 0):
            for count in range(self.num_vertices):
                self.vertices[count].write(file)
        file.write(struct.pack('<I', self.has_normals))
        if (self.num_vertices > MAX_ARRAYSIZE): raise NIFError('array size unreasonably large (size %i)'%self.num_vertices)
        if (self.has_normals != 0):
            for count in range(self.num_vertices):
                self.normals[count].write(file)
        self.center.write(file)
        file.write(struct.pack('<f', self.radius))
        file.write(struct.pack('<I', self.has_vertex_colors))
        if (self.num_vertices > MAX_ARRAYSIZE): raise NIFError('array size unreasonably large (size %i)'%self.num_vertices)
        if (self.has_vertex_colors != 0):
            for count in range(self.num_vertices):
                self.vertex_colors[count].write(file)
        file.write(struct.pack('<H', self.num_uv_sets))
        file.write(struct.pack('<I', self.has_uv))
        if (self.num_uv_sets > MAX_ARRAYSIZE): raise NIFError('array size unreasonably large (size %i)'%self.num_uv_sets)
        if (self.num_vertices > MAX_ARRAYSIZE): raise NIFError('array size unreasonably large (size %i)'%self.num_vertices)
        if (self.has_uv != 0):
            for count in range(self.num_uv_sets):
                for count2 in range(self.num_vertices):
                    self.uv_sets[count][count2].write(file)
        file.write(struct.pack('<H', self.num_faces))
        file.write(struct.pack('<I', self.num_faces_x3))
        if (self.num_faces > MAX_ARRAYSIZE): raise NIFError('array size unreasonably large (size %i)'%self.num_faces)
        for count in range(self.num_faces):
            self.faces[count].write(file)
        file.write(struct.pack('<H', self.num_match_groups))
        if (self.num_match_groups > MAX_ARRAYSIZE): raise NIFError('array size unreasonably large (size %i)'%self.num_match_groups)
        for count in range(self.num_match_groups):
            self.match_groups[count].write(file)



    # dump to screen
    def __str__(self):
        s = ''
        s += str(self.block_type)
        s += 'num_vertices' + ': %i\n'%self.num_vertices
        s += 'has_vertices' + ': %i\n'%self.has_vertices
        if (self.has_vertices != 0):
            if (self.num_vertices <= MAX_ARRAYDUMPSIZE):
                for count in range(self.num_vertices):
                    s += 'vertices' + '[%i]'%count + ':\n'
                    s += str(self.vertices[count]) + '\n'
            else:
                s += 'vertices: array[%i]\n'%self.num_vertices
        s += 'has_normals' + ': %i\n'%self.has_normals
        if (self.has_normals != 0):
            if (self.num_vertices <= MAX_ARRAYDUMPSIZE):
                for count in range(self.num_vertices):
                    s += 'normals' + '[%i]'%count + ':\n'
                    s += str(self.normals[count]) + '\n'
            else:
                s += 'normals: array[%i]\n'%self.num_vertices
        s += 'center' + ':\n'
        s += str(self.center) + '\n'
        s += 'radius' + ': %f\n'%self.radius
        s += 'has_vertex_colors' + ': %i\n'%self.has_vertex_colors
        if (self.has_vertex_colors != 0):
            if (self.num_vertices <= MAX_ARRAYDUMPSIZE):
                for count in range(self.num_vertices):
                    s += 'vertex_colors' + '[%i]'%count + ':\n'
                    s += str(self.vertex_colors[count]) + '\n'
            else:
                s += 'vertex_colors: array[%i]\n'%self.num_vertices
        s += 'num_uv_sets' + ': %i\n'%self.num_uv_sets
        s += 'has_uv' + ': %i\n'%self.has_uv
        if (self.has_uv != 0):
            s += 'uv_sets: array[%i][%i]\n'%(self.num_uv_sets,self.num_vertices)
        s += 'num_faces' + ': %i\n'%self.num_faces
        s += 'num_faces_x3' + ': %i\n'%self.num_faces_x3
        if (self.num_faces <= MAX_ARRAYDUMPSIZE):
            for count in range(self.num_faces):
                s += 'faces' + '[%i]'%count + ':\n'
                s += str(self.faces[count]) + '\n'
        else:
            s += 'faces: array[%i]\n'%self.num_faces
        s += 'num_match_groups' + ': %i\n'%self.num_match_groups
        if (self.num_match_groups <= MAX_ARRAYDUMPSIZE):
            for count in range(self.num_match_groups):
                s += 'match_groups' + '[%i]'%count + ':\n'
                s += str(self.match_groups[count]) + '\n'
        else:
            s += 'match_groups: array[%i]\n'%self.num_match_groups
        return s



#
# Time controller for texture coordinates.
#
class NiUVController(AController):
    # constructor
    def __init__(self):
        self.block_type = mystring("NiUVController")
        AController.__init__(self)
        # Always 0?
        self.unknown = 0
        # Texture coordinate controller data index.
        self.data = -1



    # read from file, excluding type string
    def read(self, file):
        AController.read(self, file)
        self.unknown, = struct.unpack('<H', file.read(2))
        self.data, = struct.unpack('<i', file.read(4))



    # write to file, including type string
    def write(self, file):
        self.block_type.write(file)
        AController.write(self, file)
        file.write(struct.pack('<H', self.unknown))
        file.write(struct.pack('<i', self.data))



    # dump to screen
    def __str__(self):
        s = ''
        s += str(self.block_type)
        s += AController.__str__(self)
        s += 'unknown' + ': %i\n'%self.unknown
        s += 'data' + ': %i\n'%self.data
        return s



#
# Texture coordinate data.
#
class NiUVData:
    # constructor
    def __init__(self):
        self.block_type = mystring("NiUVData")
        # Four UV data groups.  Perhaps the first two control x and y.
        # The existence of the second two is a guess - there are always two zero
        # values following the first two in all official files.
        self.uv_groups = [ None ] * 4
        for count in range(4): self.uv_groups[count] = uvgroup()



    # read from file, excluding type string
    def read(self, file):
        if (4 > MAX_ARRAYSIZE): raise NIFError('array size unreasonably large (size %i)'%4)
        self.uv_groups = [ None ] * 4
        for count in range(4): self.uv_groups[count] = uvgroup()
        for count in range(4):
            self.uv_groups[count].read(file)



    # write to file, including type string
    def write(self, file):
        self.block_type.write(file)
        if (4 > MAX_ARRAYSIZE): raise NIFError('array size unreasonably large (size %i)'%4)
        for count in range(4):
            self.uv_groups[count].write(file)



    # dump to screen
    def __str__(self):
        s = ''
        s += str(self.block_type)
        if (4 <= MAX_ARRAYDUMPSIZE):
            for count in range(4):
                s += 'uv_groups' + '[%i]'%count + ':\n'
                s += str(self.uv_groups[count]) + '\n'
        else:
            s += 'uv_groups: array[%i]\n'%4
        return s



#
# Property of vertex colors.
#
class NiVertexColorProperty(AProperty):
    # constructor
    def __init__(self):
        self.block_type = mystring("NiVertexColorProperty")
        AProperty.__init__(self)
        # 0=ignore, 1=emissive, 2=ambient/diffuse
        self.vertex_mode = 0
        # 0=emissive, 1=ambient/diffuse?
        self.lighting_mode = 0



    # read from file, excluding type string
    def read(self, file):
        AProperty.read(self, file)
        self.vertex_mode, = struct.unpack('<I', file.read(4))
        self.lighting_mode, = struct.unpack('<I', file.read(4))



    # write to file, including type string
    def write(self, file):
        self.block_type.write(file)
        AProperty.write(self, file)
        file.write(struct.pack('<I', self.vertex_mode))
        file.write(struct.pack('<I', self.lighting_mode))



    # dump to screen
    def __str__(self):
        s = ''
        s += str(self.block_type)
        s += AProperty.__str__(self)
        s += 'vertex_mode' + ': %i\n'%self.vertex_mode
        s += 'lighting_mode' + ': %i\n'%self.lighting_mode
        return s



#
# Not used in skinning.
# Unsure of use - perhaps for morphing animation or gravity.
#
class NiVertWeightsExtraData(AExtraData):
    # constructor
    def __init__(self):
        self.block_type = mystring("NiVertWeightsExtraData")
        AExtraData.__init__(self)
        # Number of bytes in this data block.
        self.num_bytes = 0
        # Number of vertices.
        self.num_vertices = 0
        # The vertex weights.
        self.weight = [ None ] * self.num_vertices
        for count in range(self.num_vertices): self.weight[count] = 0.0



    # read from file, excluding type string
    def read(self, file):
        AExtraData.read(self, file)
        self.num_bytes, = struct.unpack('<I', file.read(4))
        self.num_vertices, = struct.unpack('<H', file.read(2))
        if (self.num_vertices > MAX_ARRAYSIZE): raise NIFError('array size unreasonably large (size %i)'%self.num_vertices)
        self.weight = [ None ] * self.num_vertices
        for count in range(self.num_vertices): self.weight[count] = 0.0
        for count in range(self.num_vertices):
            self.weight[count], = struct.unpack('<f', file.read(4))



    # write to file, including type string
    def write(self, file):
        self.block_type.write(file)
        AExtraData.write(self, file)
        file.write(struct.pack('<I', self.num_bytes))
        file.write(struct.pack('<H', self.num_vertices))
        if (self.num_vertices > MAX_ARRAYSIZE): raise NIFError('array size unreasonably large (size %i)'%self.num_vertices)
        for count in range(self.num_vertices):
            file.write(struct.pack('<f', self.weight[count]))



    # dump to screen
    def __str__(self):
        s = ''
        s += str(self.block_type)
        s += AExtraData.__str__(self)
        s += 'num_bytes' + ': %i\n'%self.num_bytes
        s += 'num_vertices' + ': %i\n'%self.num_vertices
        if (self.num_vertices <= MAX_ARRAYDUMPSIZE):
            for count in range(self.num_vertices):
                s += 'weight' + '[%i]'%count + ': %f\n'%self.weight[count]
        else:
            s += 'weight: array[%i]\n'%self.num_vertices
        return s



#
# Time controller for visibility.
#
class NiVisController(AController):
    # constructor
    def __init__(self):
        self.block_type = mystring("NiVisController")
        AController.__init__(self)
        # Visibility controller data block index.
        self.data = -1



    # read from file, excluding type string
    def read(self, file):
        AController.read(self, file)
        self.data, = struct.unpack('<i', file.read(4))



    # write to file, including type string
    def write(self, file):
        self.block_type.write(file)
        AController.write(self, file)
        file.write(struct.pack('<i', self.data))



    # dump to screen
    def __str__(self):
        s = ''
        s += str(self.block_type)
        s += AController.__str__(self)
        s += 'data' + ': %i\n'%self.data
        return s



#
# Visibility data for a controller.
#
class NiVisData:
    # constructor
    def __init__(self):
        self.block_type = mystring("NiVisData")
        # Number of keys.
        self.num_keys = 0
        # The visibility keys.
        self.keys = [ None ] * self.num_keys
        for count in range(self.num_keys): self.keys[count] = keyvis()



    # read from file, excluding type string
    def read(self, file):
        self.num_keys, = struct.unpack('<I', file.read(4))
        if (self.num_keys > MAX_ARRAYSIZE): raise NIFError('array size unreasonably large (size %i)'%self.num_keys)
        self.keys = [ None ] * self.num_keys
        for count in range(self.num_keys): self.keys[count] = keyvis()
        for count in range(self.num_keys):
            self.keys[count].read(file)



    # write to file, including type string
    def write(self, file):
        self.block_type.write(file)
        file.write(struct.pack('<I', self.num_keys))
        if (self.num_keys > MAX_ARRAYSIZE): raise NIFError('array size unreasonably large (size %i)'%self.num_keys)
        for count in range(self.num_keys):
            self.keys[count].write(file)



    # dump to screen
    def __str__(self):
        s = ''
        s += str(self.block_type)
        s += 'num_keys' + ': %i\n'%self.num_keys
        if (self.num_keys <= MAX_ARRAYDUMPSIZE):
            for count in range(self.num_keys):
                s += 'keys' + '[%i]'%count + ':\n'
                s += str(self.keys[count]) + '\n'
        else:
            s += 'keys: array[%i]\n'%self.num_keys
        return s



#
# Unknown.
#
class NiWireframeProperty(AProperty):
    # constructor
    def __init__(self):
        self.block_type = mystring("NiWireframeProperty")
        AProperty.__init__(self)



    # read from file, excluding type string
    def read(self, file):
        AProperty.read(self, file)



    # write to file, including type string
    def write(self, file):
        self.block_type.write(file)
        AProperty.write(self, file)



    # dump to screen
    def __str__(self):
        s = ''
        s += str(self.block_type)
        s += AProperty.__str__(self)
        return s



#
# Unknown. Enables alpha channel Z-buffering?
#
class NiZBufferProperty(AProperty):
    # constructor
    def __init__(self):
        self.block_type = mystring("NiZBufferProperty")
        AProperty.__init__(self)



    # read from file, excluding type string
    def read(self, file):
        AProperty.read(self, file)



    # write to file, including type string
    def write(self, file):
        self.block_type.write(file)
        AProperty.write(self, file)



    # dump to screen
    def __str__(self):
        s = ''
        s += str(self.block_type)
        s += AProperty.__str__(self)
        return s



#
# Node for collision mesh.
#
class RootCollisionNode(AParentNode):
    # constructor
    def __init__(self):
        self.block_type = mystring("RootCollisionNode")
        AParentNode.__init__(self)



    # read from file, excluding type string
    def read(self, file):
        AParentNode.read(self, file)



    # write to file, including type string
    def write(self, file):
        self.block_type.write(file)
        AParentNode.write(self, file)



    # dump to screen
    def __str__(self):
        s = ''
        s += str(self.block_type)
        s += AParentNode.__str__(self)
        return s



#
# Customized string class
#
class mystring(string):
    def __init__(self, s):
        self.length = len(s)
        self.value = s



#
# NIF file header
#
class NiHeader:
    # constructor
    def __init__(self):
        # Morrowind files read: "NetImmerse File Format, Version 4.0.0.2"
        # (followed by a line feed (0x0A) which we however do not store)
        self.headerstr = "NetImmerse File Format, Version 4.0.0.2"
        # Morrowind files say: 0x04000002
        self.version = 0x04000002
        # number of blocks
        self.nblocks = 0



    # read from file
    def read(self, file):
        # find the header (method taken from Brandano's import script)
        file.seek(0)
        try:
            tmp, = struct.unpack('<100s', file.read(100))
        except:
            pass # if file is less than 100 bytes long...
        # roughly check if it's a nif file
        if (tmp[0:22] != "NetImmerse File Format") and (tmp[0:20] != "Gamebryo File Format"):
            raise NIFError("Invalid header: not a NIF file")
        # if it is a nif file, this will get the header
        headerstr_len = tmp.find('\x0A')
        if (headerstr_len < 0):
            raise NIFError("Invalid header: not a NIF file.")
        file.seek(0)
        self.headerstr, dummy, self.version, = struct.unpack('<%isci'%headerstr_len, file.read(headerstr_len + 5))
        assert(dummy == '\x0A') # debug
        if (self.version == 0x04000002): # morrowind
            assert(self.headerstr == "NetImmerse File Format, Version 4.0.0.2");
            self.nblocks, = struct.unpack('<i', file.read(4))
        else:
            raise NIFError("Unsupported NIF format (%s; 0x%X)."%(self.headerstr, self.version))



    # write to file
    def write(self, file):
        if (self.headerstr.find('\x0A') >= 0):
            raise NIFError("Cannot write NIF file header (invalid character).")
        file.write(struct.pack('<%iscii'%len(self.headerstr), self.headerstr, '\x0A', self.version, self.nblocks))



    # dump to screen
    def __str__(self):
        s = 'header:  ' + '%s'%self.headerstr + '\n'
        s += 'version: ' + '%i'%self.version + '\n'
        s += 'nblocks: ' + '%i'%self.nblocks + '\n'
        return s



#
# NIF file footer
#
class NiFooter:
    # constructor
    def __init__(self):
        # usually 1
        self.dunno1 = 1
        # usually 0
        self.dunno2 = 0



    # read from file
    def read(self, file):
        self.dunno1, self.dunno2 = struct.unpack('<ii', file.read(8))
        #assert((self.dunno1 == 1) and (self.dunno2 == 0)) # ?



    # write to file
    def write(self, file):
        file.write(struct.pack('<ii', self.dunno1, self.dunno2))



    # dump to screen
    def __str__(self):
        s = 'dunno1: ' + '%i'%self.dunno1 + '\n'
        s += 'dunno2: ' + '%i'%self.dunno2 + '\n'
        return s

#
# The NIF base class
#
class NIF:
    def __init__(self):
        self.header = NiHeader()
        self.blocks = []
        self.footer = NiFooter()



    def read(self, file):
        # read header
        self.header.read(file)
        # read all the blocks
        self.blocks = []
        for block_id in range(self.header.nblocks):
            # each block starts with a string, describing the type of the block,

            # so first we read this string
            block_id_str = mystring('')
            try:
                block_pos = file.tell()
                block_id_str.read(file)
            except NIFError:
                # something to investigate! hex dump
                try:
                    hexdump(file, block_pos)
                except:
                    pass
                raise NIFError("failed to get next block (does not start with a string)")

            # check the string
            if (0): pass
            elif (block_id_str.value == "AvoidNode"): this_block = AvoidNode()
            elif (block_id_str.value == "NiAlphaController"): this_block = NiAlphaController()
            elif (block_id_str.value == "NiAlphaProperty"): this_block = NiAlphaProperty()
            elif (block_id_str.value == "NiAmbientLight"): this_block = NiAmbientLight()
            elif (block_id_str.value == "NiAutoNormalParticles"): this_block = NiAutoNormalParticles()
            elif (block_id_str.value == "NiBillboardNode"): this_block = NiBillboardNode()
            elif (block_id_str.value == "NiBSAnimationNode"): this_block = NiBSAnimationNode()
            elif (block_id_str.value == "NiBSParticleNode"): this_block = NiBSParticleNode()
            elif (block_id_str.value == "NiCamera"): this_block = NiCamera()
            elif (block_id_str.value == "NiColorData"): this_block = NiColorData()
            elif (block_id_str.value == "NiDirectionalLight"): this_block = NiDirectionalLight()
            elif (block_id_str.value == "NiDitherProperty"): this_block = NiDitherProperty()
            elif (block_id_str.value == "NiFlipController"): this_block = NiFlipController()
            elif (block_id_str.value == "NiFloatData"): this_block = NiFloatData()
            elif (block_id_str.value == "NiGeomMorpherController"): this_block = NiGeomMorpherController()
            elif (block_id_str.value == "NiGravity"): this_block = NiGravity()
            elif (block_id_str.value == "NiKeyframeController"): this_block = NiKeyframeController()
            elif (block_id_str.value == "NiKeyframeData"): this_block = NiKeyframeData()
            elif (block_id_str.value == "NiMaterialColorController"): this_block = NiMaterialColorController()
            elif (block_id_str.value == "NiMaterialProperty"): this_block = NiMaterialProperty()
            elif (block_id_str.value == "NiMorphData"): this_block = NiMorphData()
            elif (block_id_str.value == "NiNode"): this_block = NiNode()
            elif (block_id_str.value == "NiParticleColorModifier"): this_block = NiParticleColorModifier()
            elif (block_id_str.value == "NiParticleGrowFade"): this_block = NiParticleGrowFade()
            elif (block_id_str.value == "NiParticleRotation"): this_block = NiParticleRotation()
            elif (block_id_str.value == "NiPathController"): this_block = NiPathController()
            elif (block_id_str.value == "NiPixelData"): this_block = NiPixelData()
            elif (block_id_str.value == "NiPlanarCollider"): this_block = NiPlanarCollider()
            elif (block_id_str.value == "NiPosData"): this_block = NiPosData()
            elif (block_id_str.value == "NiRotatingParticles"): this_block = NiRotatingParticles()
            elif (block_id_str.value == "NiSequenceStreamHelper"): this_block = NiSequenceStreamHelper()
            elif (block_id_str.value == "NiShadeProperty"): this_block = NiShadeProperty()
            elif (block_id_str.value == "NiSkinData"): this_block = NiSkinData()
            elif (block_id_str.value == "NiSkinInstance"): this_block = NiSkinInstance()
            elif (block_id_str.value == "NiSourceTexture"): this_block = NiSourceTexture()
            elif (block_id_str.value == "NiSpecularProperty"): this_block = NiSpecularProperty()
            elif (block_id_str.value == "NiStringExtraData"): this_block = NiStringExtraData()
            elif (block_id_str.value == "NiTextKeyExtraData"): this_block = NiTextKeyExtraData()
            elif (block_id_str.value == "NiTextureEffect"): this_block = NiTextureEffect()
            elif (block_id_str.value == "NiTexturingProperty"): this_block = NiTexturingProperty()
            elif (block_id_str.value == "NiTriShape"): this_block = NiTriShape()
            elif (block_id_str.value == "NiTriShapeData"): this_block = NiTriShapeData()
            elif (block_id_str.value == "NiUVController"): this_block = NiUVController()
            elif (block_id_str.value == "NiUVData"): this_block = NiUVData()
            elif (block_id_str.value == "NiVertexColorProperty"): this_block = NiVertexColorProperty()
            elif (block_id_str.value == "NiVertWeightsExtraData"): this_block = NiVertWeightsExtraData()
            elif (block_id_str.value == "NiVisController"): this_block = NiVisController()
            elif (block_id_str.value == "NiVisData"): this_block = NiVisData()
            elif (block_id_str.value == "NiWireframeProperty"): this_block = NiWireframeProperty()
            elif (block_id_str.value == "NiZBufferProperty"): this_block = NiZBufferProperty()
            elif (block_id_str.value == "RootCollisionNode"): this_block = RootCollisionNode()
            else:
                # something to investigate! hex dump
                try:
                    hexdump(file, block_pos)
                except:
                    pass
                btype = ""
                for c in block_id_str.value:
                    if (ord(c) >= 32) and (ord(c) <= 127):
                        btype += c
                    else:
                        btype += "."
                raise NIFError("unknown block type (%s)"%btype)

            # read the data
            try:
                this_block.read(file)
            except:
                # we failed to read: dump what we did read, and do a hex dump
                print "%s data dump:"%block_id_str.value
                try:
                    print this_block
                except:
                    pass # we do not care about errors during dumping
                try:
                    hexdump(file, block_pos)
                except:
                    pass # we do not care about errors during dumping
                raise

             # and store it
            self.blocks.append(this_block)
        # read the footer
        block_pos = file.tell()
        try:
            self.footer.read(file)
        except:
            # we failed to read the footer: hex dump
            try:
                hexdump(file, block_pos)
            except:
                pass # we do not care about errors during dumping
            raise



    # writing all the data
    def write(self, file):
        if (self.header.nblocks != len(self.blocks)):
            raise NIFError("Invalid NIF object: wrong number of blocks specified in header.")
        self.header.write(file)
        for block in self.blocks:
            block.write(file)
        self.footer.write(file)



    # dump all the data
    def __str__(self):
        s = str(self.header) + '\n'
        count = 0
        for block in self.blocks:
            s += "\n%i\n"%count
            s += str(block);
            count += 1
        s += str(self.footer)
        return s



#
# a hexdump function
#
def hexdump(file, pos):
    if (MAX_HEXDUMP <= 0): return
    file.seek(0, 2) # seek end
    num_bytes = file.tell() - pos
    if (num_bytes > MAX_HEXDUMP): num_bytes = MAX_HEXDUMP
    file.seek(pos)
    print "hex dump (at position 0x%08X, %i bytes):"%(pos,num_bytes)
    count = num_bytes
    cur_pos = pos
    while (count > 0):
       if (count >= 16):
           num = 16
       else:
           num = count
       bytes = struct.unpack("<%iB"%num, file.read(num))
       hexstr = '0x%08X: '%cur_pos
       for b in bytes:
           hexstr += '%02X '%b
       for b in bytes:
           if (b >= 32) and (b <= 127):
               hexstr += chr(b)
           else:
               hexstr += '.'
       print hexstr
       count -= num
       cur_pos += num
    return # comment this line for float dump
    num_floats = (num_bytes / 4) - 1
    if (num_floats <= 0): return
    for ofs in range(1): # set range(4) to have a more complete analysis
        print "float dump (at position 0x%08X, %i floats):"%(pos+ofs,num_floats)
        file.seek(pos+ofs)
        bytes = struct.unpack("<%iB"%(num_floats * 4), file.read(num_floats * 4))
        file.seek(pos+ofs)
        floats = struct.unpack('<%if'%num_floats, file.read(num_floats * 4))
        for i in range(num_floats):
            print '%02i: '%i, '(%02X %02X %02X %02X)'%(bytes[i*4], bytes[i*4+1], bytes[i*4+2], bytes[i*4+3]), floats[i]

