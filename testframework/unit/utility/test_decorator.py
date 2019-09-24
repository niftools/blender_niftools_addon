import nose

from io_scene_nif.utility.nif_decorator import overload_method


class Foo(object):

    @overload_method(any)
    def bah(self, a):
        print('params - object: {}'.format(a))
        return a

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

    def test_no_overload(self):
        """Test base case as required to default case"""

        class Bar:
            pass

        obj = Bar()
        out = self.foo.bah(obj)
        nose.tools.assert_is_instance(out, Bar)
        nose.tools.assert_equal(out, obj)
