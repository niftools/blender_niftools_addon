"""This script contains helper methods allow decoration of mehods."""

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

import functools

from bpy.utils import register_class, unregister_class

from io_scene_niftools.utils.logging import NifLog


def overload_method(*types):
    """Allows method overloading to enable polymorphic behaviour"""

    def register(func):
        name = func.__name__
        mm = overload_method.registry.get(name)
        if mm is None:
            @functools.wraps(func)
            def wrapper(self, *args):
                t = tuple(arg.__class__ for arg in args)
                f = wrapper.typemap.get(t)
                if f is None:
                    print(str(t))
                    raise TypeError("no match")
                return f(self, *args)

            wrapper.typemap = {}
            mm = overload_method.registry[name] = wrapper
        if types in mm.typemap:
            raise TypeError("duplicate registration")
        mm.typemap[types] = func
        return mm

    return register


overload_method.registry = {}


def register_classes(cls_list, mod_name):
    NifLog.debug(f"Registering Classes for module: {mod_name}")
    for clz in cls_list:
        register_class(clz)
    NifLog.debug(f"Registered Classes: {[c.__name__ for c in cls_list]}")


def unregister_classes(cls_list, mod_name):
    NifLog.debug(f"Unregistering Classes for module: {mod_name} ")
    for clz in cls_list:
        unregister_class(clz)
    NifLog.debug(f"Unregistered Classes: {[c.__name__ for c in cls_list]}")


def register_modules(module_list, mod_name):
    NifLog.debug("Registering submodules for: " + mod_name)
    for mod in module_list:
        mod.register()
    NifLog.debug(f"Registered the following submodules: {[m.__name__ for m in module_list]}")


def unregister_modules(module_list, mod_name):
    NifLog.debug(f"Unregistering submodules for: {mod_name}")
    for mod in module_list:
        mod.unregister()

    NifLog.debug(f"Unregistered the following submodules: {[m.__name__ for m in module_list]}")
