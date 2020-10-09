"""Unit testing that the decorator utility"""

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


import nose
from nose.tools import raises

from io_scene_nif.utils.util_decorator import overload_method


class Foo(object):

    @overload_method(any)
    def bah(self, a):
        print(f"params - object: {a}")
        return a

    @overload_method(str)
    def bah(self, bar: str) -> int:
        print(f"params - string: {bar}")
        convert = int(bar)
        print(f"return - int: {convert:d}")
        return convert

    @overload_method(float)
    def bah(self, bar: float) -> str:
        print(f"params - float: {bar}")
        convert = str(int(bar))
        print(f"return - str: {convert:s}")
        return convert

    @overload_method(float, int)
    def bah(self, s, t):
        print(f"params - float, int: {s}, {t}")
        convert = int(s) + int(t)
        print(f"return - int: {convert:d}")
        return convert


class TestDispatachDecorator:

    @classmethod
    def setup_class(cls):
        cls.foo = Foo()
        cls.i = 1
        cls.f = 1.234

    def test_str_overload(self):
        """Test the loading of string type"""
        s = str(self.i)
        out = self.foo.bah(s)
        nose.tools.assert_is_instance(out, int)
        nose.tools.assert_equal(out, self.i)

    def test_float_overload(self):
        """Test the loading of float"""
        s = str(self.i)
        out = self.foo.bah(self.f)
        nose.tools.assert_is_instance(out, str)
        nose.tools.assert_equal(out, s)

    def test_multi_param_overload(self):
        """Test selection with multiple params"""
        f = 1.234
        out = self.foo.bah(f, self.i)
        nose.tools.assert_is_instance(out, int)
        nose.tools.assert_equal(out, int(f) + self.i)

    @raises(TypeError)
    def test_no_overload(self):
        """Test base case as required to default case"""

        class Bar:
            pass

        obj = Bar()
        self.foo.bah(obj)

