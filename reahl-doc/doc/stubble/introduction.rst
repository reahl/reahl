.. Copyright 2013, 2014 Reahl Software Services (Pty) Ltd. All rights reserved.

Stubble (reahl-stubble)
=======================

Introduction
^^^^^^^^^^^^

Stubble is a set of tools which can be used to simplify Python unit
testing code by means of the responsible use of so-called "stub"
classes.

.. seealso::

   :doc:`The API documentation <index>`.

Stubble includes several special classes that can be used
to stub out (and restore) sys.stdout or to mock methods on a class
temporarily.

Stubble allows you to write arbitrary classes for use as stubs instead
of real classes while testing.  This can be dangerous in a test, since
your ad-hoc stub classes may implement interfaces that are not
representative of the real classes they stand in for.

However, Stubble lets you link a stub class loosely to the real class
which it is a stub for.  This information is then used to ensure that
tests will break if there is a discrepancy between the interface
supported by your stub class and that of the real class it stands in
for.

Stubble also includes some support for stubbing a Python egg and its
associated meta information when you are using setuptools.

(More information is provided in the Overview below.)




Stub classes
^^^^^^^^^^^^

What stub classes are
---------------------

A stub class is a class you use in a test as a substitute for another
class.  Here are a few reasons for wanting to use such stub classes:

- You may need to provide an instance of, say, MyBulkyRealClass in a
  test fixture.  But constructing such an instance may be difficult,
  cumbersome, or outright impossible.  For example: your test code may
  only need to call a single method on the provided MyBulkyRealClass
  instance - but merely in order to construct the needed instance, you
  have to construct a forest of other instances.  This is
  unnecessary.  Another example is where you need to construct an
  instance of a GUI library object, such as a Window...but, the GUI
  toolkit you are using may not allow instantiation of such objects
  outside of its control.

  In both these examples, it would have been much easier to just
  create a simple class containing the single method which would be
  called by your testing code - possibly even with an implementation
  hard-coded for this particular scenario.

- You may want to decouple the unit tests of different modules: you
  don't really want to have the unit tests of one module fail because
  of errors in another module.  By using stub classes for real classes
  in other modules, the unit tests of the module being tested are not
  dependent on the actual other module, just on its expected interface.

- You may want to monitor certain things in a test, such as the values
  of parameters that were passed to a particular method call.  Or, you
  may want to hard-code a special implementation for a particular
  method specifically for your test scenario.

The careful use of stub classes can greatly simplify and speed up the
writing of unit test code.


Prerequisites for examples
--------------------------

This section shows by example how the stub classes in Stubble can be
used.  The examples all assume the following real class::

  class RealClass(object):
      b = 123

      def foo(self, a):
          print('i am the real foo')

      def bar(self):
          print('i am the real bar')


Basic functionality
-------------------

Any class can be a Stubble-enabled stub.  To create a stub class, you
just prepend the class with a descriptor like this::

  from reahl.stubble import stubclass

  @stubclass(RealClass)
  class Stub(object):
      def foo(self, a):
          'i am a fake foo'

The class ``Stub`` is now declared as being a stub **of RealClass**.
When Python encounters the declaration, it will check *each* method
declared on this class and make sure that:

  - There is a similarly named method on the real class; and
  - the corresponding method on the real class has the exact same
    signature as declared by the stub.

If any of these conditions are not met, an exception is raised.

The simplest solution is usually to derive stub classes from
``object``.  But, sometimes it is useful to derive from the real class
which is being stubbed.

The main reason for *not* deriving from the real class is usually that
parameters (or other side-effects) needed for the __init__ of the real
class are cumbersome to provide (or unwanted).

But, sometimes, you want to inherit from the real class, to inherit
some its real behaviour, but also override some of it::

  from reahl.stubble import stubclass

  @stubclass(RealClass)
  class Stub(RealClass):
      def foo(self, a):
          self.foo_called = True


Exempt methods
--------------

Not all methods on a stub class need to be strictly checked against
those in the real class - utility methods you use in the test, for
instance.  To mark a method as being *exempt* from the checking, you
can use a decorator on that method::

  from reahl.stubble import stubclass, exempt

  @stubclass(RealClass)
  class Stub(object):
      @exempt
      def my_own_method(self):
          print('i am my own method')


Attributes
----------

At first it was thought important to let Stubble do strict checking on
any class attribute similarly to what it does for methods.  In
practice we found that it is a bit bothersome to do that.  But if you
really want to, you can do the following::

  from reahl.stubble import stubclass

  @stubclass(RealClass, check_attributes_also=True)
  class Stub(object):
      b = 'a value'

This would additionally check that RealClass has an attribute "b" and
fail if it does not have one.



EasterEggs
^^^^^^^^^^

Setuptools provide (amongst others) support for Python eggs.  Python
eggs are somewhat similar to OSGI bundles: they are components which
consist (mainly) of Python code, but also have metadata associated
with them.  Amongst other things, this allows components to publish
their interfaces, and it allows components to specify how they can be
extended by 3rd parties.  Setuptools also includes a method (the
ResourceManager API) by which packages can request the contents of
"files" regardless of how these files have been packaged or where they
are physically located.

To help here, Stubble provides the EasterEgg. EasterEggs are not real
Python eggs. A correctly initialised global EasterEgg instance is
constructed as ``reahl.stubble.easter_egg``.  It should suffice for most
purposes, but you *can* construct additional instances if needed.

Just be sure to always add your EasterEggs to
``pkg_resources.working_set``  (or similar), else they won't have any
effect.  Also, each added EasterEgg should be named uniquely (or it
won't be added).



Stub entry points
-----------------

If you work with setuptools you may be testing code to which you want
to supply stub objects via the setuptools entry point mechanism.

EasterEgg has two methods for adding stub classes as entry points,
exemplified here::

  reahl.stubble.easter_egg.add_entry_point_from_line(group_name,
                        'test1 = examples.setuptools:StubClass1')
  reahl.stubble.easter_egg.add_entry_point(group_name, 'test2', StubClass2)

Actual code under test would now probably do something like this (and be
oblivious to the fact that the provided classes are stubs)::

  #  (we just print out each class it finds...)
  for i in pkg_resources.iter_entry_points(group_name):
      print(i.load())


Where you tear down test fixtures after a test run, you should clear
the fake entry points registered with the easter_egg::

  reahl.stubble.easter_egg.clear()


Stubbed resources
-----------------

The EasterEgg can also be used for testing code that makes use of the
ResourceManager API in setuptools.  You can put the real files that
the ResourceManager API should provide in a directory somewhere - and
then specify that location as the EasterEgg's module_path::

  reahl.stubble.easter_egg.location = '/some/where'

(By default, this path is os.getcwd())


Intercepting calls
^^^^^^^^^^^^^^^^^^

Stubble includes a number of classes that can be used as context
managers to temporarily intercept calls to code that may not even be
under your control. This is done by swapping certain methods out
temporarily for special ones that are restored after a particular
block of code finished executing.

See:
 - :class:`reahl.stubble.intercept.SystemOutStub`
 - :class:`reahl.stubble.intercept.CallMonitor`
 - :class:`reahl.stubble.intercept.MonitoredCall`
 - :class:`reahl.stubble.intercept.InitMonitor`
 - :func:`reahl.stubble.intercept.replaced`


Experimental features
^^^^^^^^^^^^^^^^^^^^^

The simple functionality of Stubble explained so far is really what it
is all about.  But, having started off as an experiment, Stubble
provides several interesting experimental features.  However
interesting some of these may sound, they are not really used at all in
practice... sometimes because they're just theoretically nice ideas
with little use in practice; sometimes because they're nice ideas that
proved too difficult to implement transparently.

They're provided as part of Stubble for interest's sake.  Maybe a
skilled Python programmer out there feels like the challenge...


Impostors
---------

Passing a stub class instead of the real class to code that is being
tested works well in most cases.  The notable exception is when the
code actually checks the type of the class itself, such as with
``isinstance`` or ``issubclass``, etc.

Ideally speaking, you'd want a stub that pretends in all respects to
be the real thing to the code being tested.  Impostors are an attempt
at such stub classes.

To make your stub class an Impostor, you have to let it derive from
``reahl.stubble.Impostor``::

  from reahl.stubble import Impostor, stubclass

  @stubclass(RealClass)
  class Stub(Impostor):
      pass


With such a declaration, you gain the dubious benefit expressed in the
code::

  assert not issubclass(Stub, RealClass)  #issubclass catches Impostors out
  s = Stub()
  assert isinstance(s, RealClass)         #but the foolery works well here


The value derived from this is debatable... most often you get more
benefit by deriving your stub class from the real class it is a stub
for.


Delegation
----------

Delegation is actually a more useful idea than Impostors.  It arose
from the problem sometimes encounters where the programmer does not
have control over the creation of the instance that has to be stubbed.

For example, a GUI framework may create a bunch of instances for you,
and you just want to *replace* one node in this object forest with a
special kind of stub *instance*.  Also, you actually would only want
to override a single method, but have the rest of the behaviour
delegated to the real instance "as usual".

Delegation (in this context) is the strategy of creating a stub class
whose instance is 'superimposed' upon an instance of a real class.

A delegate is declared like this::

  from reahl.stubble import stubclass, Delegate

  @stubclass(RealClass)
  class Stub(Delegate):

      shadowed = ['foo', 'aa']

      def foo(self, a):
          print('i am a fake foo')


And instance of it is then created like this::

  real_instance = RealClass()  # first we need an instance to delegate to
  s = Stub(real_instance)      # the stub instance


Our stub instance how has the following interesting behaviour::

  assert isinstance(s, RealClass)  # Delegates act like Impostors do
  s.foo(1)                         # calls the fake
  s.bar()                          # calls the real

  try:
      s.aa                         # breaks regardless of
                                   # whether or not aa is on real_instance
  except:
      pass

  s.aa = 123                              # `aa` is set on the fake
  assert s.aa == 123                      # `aa` is read from the fake
  assert not hasattr(real_instance, 'aa')  # see, it was not set there


The unsolved problem with Delegation
------------------------------------

At present, although such Delegates would have been nice to have, their
implementation (which is a bit tricky) has a serious flaw which will
make Delegates behave contrary to what you'd expect in certain
circumstances.

The problem is when one shadows attributes or methods that are
accessed by the real class itself from within code delegated to.  An
example illustrates best::

  from reahl.stubble import stubclass, Delegate

  class AnotherRealClass(object):
      def foo(self):
          self.aa = 123

  real_instance = AnotherRealClass()

  @stubclass(AnotherRealClass)
  class Stub(Delegate):
    shadowed = ['aa']

  s = Stub(real_instance)

The behaviour we would expect here is that, upon calling s.foo, the
real foo is called, which sets 'aa' on the stub, even though the
setting of 'aa' happens in real code::


  s.foo()

  try:
      #this expected behaviour would have been tested
      # like this:
      assert s.aa == 123
      assert not hasattr(real_instance, 'aa')
  except:
      pass

But alas, we cannot do that... The variable is in fact set on the real
class.

The same problem manifests itself if you call a method which is
delegated to the real class, and the real class in turn tries to call
a method which is being shadowed on the stub.

This problem severely limits the use of Delegates and can cause bugs
in tests that are very difficult to find -- hence Delegates are not
used in practice.

Up for a challenge?
~~~~~~~~~~~~~~~~~~~

Anyone interested in giving it a bash: the one solution is to change
reahl.stubble.Delegate.__init__, so it changes the __class__ of 'real' to a
substitute with a __getattribute__ which can do the necessary voodoo.

That's the solution in theory only.  In practice, object layout
differences prevent this particular solution...  But, you may know
better.



Dealing with Instance variables
-------------------------------

In Python, it is very difficult to check anything when it comes to
instance variables... simply because the class does not have any
information about which instance variables it will have.

Some people use __slots__ as a way to specify instance variables for
this reason.  *However*, that is **not** what __slots__ is intended
for.  \__slots__ is an optimisation feature which, if used for other
reasons will behave contrary to your expectations.

Such as in this example originally posted on comp.lang.python
by Blair Hall on Apr 10 2003 (I modified it a bit, though...)::

  class A(object):
      def __init__(self):
          pass

  class B(A):
      __slots__ = ('z',)
      def __init__(self):
          super(B, self).__init__()

  # now, if you used __slots__ thinking that, since 'c' is not
  # in B.__slots__ and that the code above would complain,
  # you're in for a surprise...
  b = B()
  b.c = 3     # passes


Using __slots__ also interferes with a number of other pythonic
flexibilities, so its use is not really recommended unless really
necessary.

If you *are*, however, interested in checking instance variables too,
other conventions are possible.  For example:

 - Always initialise all your instance variables in __init__
   (even if they are == None), so you can expect your class invariant
   to include 'instances of this class has all those attributes')
 - Always put class variables in the class for each variable
   instances of it would have (the class variable values also serve as
   handy default values for unset instance variables).

Using the latter approach, stubble could be used to check attributes
by your either specifying a default value for the attribute in the
stub class, or by using reahl.stubble.checkedinstance::

  from reahl.stubble import stubclass, checkedinstance

  class RealClassFollowingConventions(object):
      a = None
      b = None

  @stubclass(RealClassFollowingConventions, check_attributes_also=True)
  class Stub(object):
      a = 'asd'
      b = checkedinstance()


- (remove either a or b in the real class to see it complain)
- (PS: the difference between a and b below is that for b we do not
   give a default value, we just state that it should be in both)

For the stubborn, who insist on using __slots__, and who even insist
on using it as a checked list of allowed attributes, stubble deals in
the following drug (remove 'aa' from __slots__ to see it complain)::

  from reahl.stubble import stubclass, slotconstrained

  class StubbornRealClass(object):
      __slots__ = ('aa')

  @stubclass(StubbornRealClass)
  class Stub(object):
      aa = slotconstrained()

  s = Stub()
  try:
      s.aa                  #even though declared as class attributes,
                            # these behave like instance attributes,
                            # so its not there if not set
  except AttributeError, e:
      pass

  s.aa = 123                #as usual
  assert s.aa == 123        #as usual



