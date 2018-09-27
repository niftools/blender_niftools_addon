import functools


def overload_method(*types):
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
