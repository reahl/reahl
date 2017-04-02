import wrapt
import pytest
import inspect

# scope
# scenarios
# dependencies between fixtures
# changing name and sig of test method

def tst(*fixture_classes):
    def catch_wrapped(f):
        signature = inspect.signature(f)
        adapted_args = list(signature.parameters.keys())[len(fixture_classes):]

        code = 'def adapter(%s): pass' % (','.join(adapted_args))
        l = {}
        g = globals().copy()
        exec(code, g, l)
        adapter = l['adapter']

        @wrapt.decorator(adapter=adapter)
        def the_test(wrapped, instance, args, kwargs):
            return wrapped(*([fixture_class.instance() for fixture_class in fixture_classes]), *args, **kwargs)
        return pytest.mark.parameterized('fup', [1, 2, 3])(the_test(f))

    return catch_wrapped


class Fuxture(object):
    scope = 'func'
    deps  = []
    _instance = None

    @classmethod
    def instance(cls):
        if not cls._instance:
            cls._instance = cls()
        return cls._instance
    


class MyFux(Fuxture):
    scope = 'session'


@pytest.fixture
def frob():
    return 'koos'


@tst(Fuxture)
def test_shit(fup, frob):
    'The shit works'
    assert frob == 'koos'
    assert fup.scope == 'session'

    
def test_shat():
    'The shat works'
    assert True


    
@pytest.fixture(params=[1, 2])
def frobnitz(request):
    return 'koos %s' % request.param


#@tst(Fuxture)
#def test_shitty(fup, frobnitz):
#    assert frobnitz == 'koos'

