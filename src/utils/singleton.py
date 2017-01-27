# coding:utf-8

def singleton_sublime(cls):
    '''
    After decoration, the cls is no longer a class,
    but a callable instance that every time we call it
    like instance() will return the unique created instance
    itself

    So it means the instance has been created whiling decorating
    :param cls:
    :return:
    '''
    instance = cls()
    instance.__call__ = lambda: instance
    return instance


def singleton(cls):
    '''
    the decorator returns the function _singleton,
    so the parameters of the function are the parameters of the class
    :param cls:
    :return:
    '''
    instance = {}

    def _singleton(*args, **kwargs):
        key = (cls,)
        for arg in args:
            key += (arg,)
        for kwarg_tuple in kwargs.items():
            key += kwarg_tuple
        if key not in instance:
            instance[key] = cls(*args, **kwargs)

        return instance[key]

    return _singleton
