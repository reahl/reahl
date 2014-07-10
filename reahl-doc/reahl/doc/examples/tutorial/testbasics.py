from __future__ import unicode_literals
from __future__ import print_function
from reahl.tofu import test, Fixture

class SimpleFixture(Fixture):
    def new_name(self):
        return 'John'


@test(SimpleFixture)
def fixture_singletons(fixture):
    """Accessing an attribute on the Fixture always brings back the same 
       object, as created by a similarly named new_ method on the fixture."""

    assert fixture.name == 'John'
    assert fixture.name is fixture.name  # ie, the same object is always returned


# ------- dependent setup objects example

class User(object):
    def __init__(self, name):
        self.name = name


class InterestingFixture(SimpleFixture):
    def new_user(self):
        return User(self.name)


@test(InterestingFixture)
def dependent_setup_objects(fixture):
    """Different attributes on a Fixture can reference one another."""
    assert fixture.user.name is fixture.name


# ------- using new_ methods directly

class MoreInterestingFixture(SimpleFixture):
    def new_user(self, name=None):
        return User(name or self.name)


@test(MoreInterestingFixture)
def bypassing_the_singleton(fixture):
    """new_ methods can be supplied with kwargs in order to create test objects that differ from the default."""
    jane = fixture.new_user(name='Jane')
    assert jane.name == 'Jane'
    assert fixture.user is not jane

    other_jane = fixture.new_user(name='Jane')
    assert jane is not other_jane


