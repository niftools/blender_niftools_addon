import nose

from io_scene_nif.utility.nif_decorator import overload_method


class Foo(object):

    @overload_method(str)
    def bah(self, bar: str) -> int:
        print('params - string: {}'.format(bar))
        convert = int(bar)
        print('return - int: {}'.format(convert))
        return convert

    @overload_method(float)
    def bah(self, bar: float) -> str:
        print('params - float: {}'.format(bar))
        convert = str(int(bar))
        print('return - str: {}'.format(convert))
        return convert

    @overload_method(float, int)
    def bah(self, s, t):
        print('params - float, int: {}, {}'.format(s, t))
        convert = int(s) + int(t)
        print('return - int: {}'.format(convert))
        return convert


class TestDispatachDecorator:

    @classmethod
    def setup_class(cls):
        cls.foo = Foo()
        cls.i = 1
        cls.f = 1.234

    def test_str_overload(self):
        s = str(self.i)
        out = self.foo.bah(s)
        nose.tools.assert_is_instance(out, int)
        nose.tools.assert_equal(out, self.i)

    def test_float_overload(self):
        s = str(self.i)
        out = self.foo.bah(self.f)
        nose.tools.assert_is_instance(out, str)
        nose.tools.assert_equal(out, s)

    def test_multi_param_overload(self):
        f = 1.234
        out = self.foo.bah(f, self.i)
        nose.tools.assert_is_instance(out, int)
        nose.tools.assert_equal(out, int(f) + self.i)
