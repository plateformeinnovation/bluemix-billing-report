# coding:utf-8

def singleton(cls):
    '''
    After decoration, the cls is no longer a class,
    but a callable instance that every time we call it
    like instance() will return the unique created instance
    itself
    :param cls:
    :return:
    '''
    instance = cls()
    instance.__call__ = lambda: instance
    return instance