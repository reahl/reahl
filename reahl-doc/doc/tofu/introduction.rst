.. Copyright 2013, 2014, 2015 Reahl Software Services (Pty) Ltd. All rights reserved.

.. |Fixture| replace::  :class:`~reahl.tofu.Fixture`
.. |scenario| replace::  :class:`~reahl.tofu.scenario`
.. |uses| replace::  :class:`~reahl.tofu.uses`
.. |scope| replace::  :class:`~reahl.tofu.scope`
.. |with_fixtures| replace::  :class:`~reahl.tofu.with_fixtures`


Tofu (reahl-tofu)
-----------------

Tofu provides class-based |Fixture|\s for use in tests. Tofu's |Fixture|\s can be used on
their own with any test framework, but Tofu also provides an extension to `pytest <https://pytest.org>`_
that makes using it with pytest seamless.

.. seealso::

   :doc:`The API documentation <index>`.

.. note::

  Do not confuse Reahl Tofu |Fixture|\s with Django's Fixtures or with
  pytest's Fixtures. They are all related, but work very
  differently.

What is a class-based |Fixture|?
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

A class-based |Fixture| is an object that contains several of related objects that are often used together
in tests.

For example, a shopping cart application may have a lot of tests in which a ShoppingCart, a User and a CreditCard are
routinely used. What's more, the CreditCard used in the tests should be linked to the User:

.. uml::

   object "fixture: MyFixture" as fixture
   object "shopping_cart: ShoppingCart" as shopping_cart
   object "credit_card: CreditCard" as credit_card
   object "user: User" as user
   fixture -- shopping_cart
   fixture -- credit_card
   fixture -- user
   credit_card -right- user

Given the example above, the following assumptions can be made inside tests:

.. code-block:: Python

   assert fixture.user is fixture.credit_card.owner
   assert fixture.shopping_cart.payment_method is fixture.credit_card

A |Fixture| is written as a class, hence it can also contain useful methods re-used by several tests:

.. code-block:: Python

   assert fixture.last_payment_is(fixure.credit_card, 145.42)


How are |Fixture|\s used?
~~~~~~~~~~~~~~~~~~~~~~~~~

A |Fixture| can be used in many ways:

- Inside a `with` statement

    .. code-block:: python

       with MyFixture() as fixture:
        ...

  Used outside of a test framework, using a Fixture inside a `with` statement ensures that its set up and tear down
  logic is executed.

- Supplied to a pytest test function
    .. code-block:: python

        @with_fixtures(MyFixture)
        def test_things(fixture):
         ...

  When using pytest, decorate your test method using a |with_fixtures| decorator in which you list all the |Fixture|
  classes needed by your test method. When your test method is called, each |Fixture| class is first `instantiated`,
  then passed into the method, and finally `torn down` when the method exits.
  The number of |Fixture| classes passed to |with_fixtures| should match the number of arguments of your test function.
  The names of the arguments have no significance, |Fixture| instances are passed as attributes in the order listed
  in |with_fixtures|.

Writing a |Fixture|
~~~~~~~~~~~~~~~~~~~

To write a |Fixture|, inherit a new class from |Fixture|. For each element of the |Fixture|, add a method that
creates the element. Prepend `new_` to the method name to signal that it is a factory method.

.. code-block:: python

   class MyFixture(Fixture):
       def new_user(self):
           return User(name='sam')

Whenever an attribute is accessed on the |Fixture|, it checks whether a `new_`-method exists for that name. If so,
it invokes the method to create the object in question. Subsequent accesses just return the first object so created:

.. code-block:: python

   @with_fixtures(MyFixture)
   def test_fixture_attributes(f):
        assert f.user is f.user     # The first use of .user calls new_user(), the next one just returns the first object
        assert user.name == 'sam'

The ability of a |Fixture| to create an object on first access can greatly simplify a setup where several objects
on the |Fixture| depend on one another:

.. code-block:: python

   class MyFixture(Fixture):
       def new_user(self):
           return User(name='sam')

       def new_credit_card(self):
           return CreditCard('123456224', self.user)

   @with_fixtures(MyFixture)
   def test_interrelated_setup(f):
        assert f.credit_card.owner is f.user  # User is first instantiated when the Fixture calls .user on itself,
                                              # yet, the same .user is returned when accessed again directly on the
                                              # Fixture in a test.


Set-up and tear down logic
~~~~~~~~~~~~~~~~~~~~~~~~~~

If your factory method needs to set up or tear down the object it creates, it can yield the object and perform
tear down after the yield:

.. code-block:: python

   class MyFixture(Fixture):
       def new_shopping_cart(self):
           print('Setting up')
           cart = ChoppingCart()
           yield cart
           print('Tearing down')


You can also explicitly mark certain methods on your |Fixture| to be executed on set up or tear down:

.. code-block:: python

   class MyFixture(Fixture):
       @set_up
       def start_cart_server(self):
           WebServer.start()

       @tear_down
       def stop_cart_server(self):
           WebServer.stop()


Scenarios
~~~~~~~~~

To run the same test for multiple scenarios, create a no-argument method decorated with |scenario| for each scenario
which sets up the data relevant to that scenario:

.. code-block:: python

   class MyFixture(Fixture):
        @scenario
        def out_of_stock(self):
            self.stock_room.set_items(0)
            self.expected_exception = OutOfStock

        @scenario
        def insufficient_funds(self):
            self.credit_card.set_balance(0)
            self.expected_exception = InSufficientFunds

   @with_fixtures(MyFixture)
   def test_purchase_failure(f):
       try:
          f.shopping_cart.checkout()
          assert None, 'Expected an exception to be raised, but did not get one'
       except f.expected_exception:
          pass

The above test will be executed twice. THe first time, a MyFixture is instantiated and set up, then its `out_of_stock`
scenario method is called before it is passed to the test method. On the second run, a new MyFixture is created, set up,
and its `insufficient_funds` method is executed before being passed to the test method.


Interdependencies between Fixtures
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Just like a test method can use one or more |Fixture|\s, a |Fixture| can also use other |Fixture|\s. Decorate your
|Fixture| class with |uses| to specify the other |Fixture|\s it depends on. When your |Fixture| is instantiated,
each |Fixture| it depends on is first instantiated, set up, and then set as an attribute on your |Fixture|. The
attribute is named as per your invocation of |uses|:

.. code-block:: python

   class RoleFixture(Fixture):
        def new_shopper_role(self):
            return Role('shopper')

   @uses(access_control_fixture=RoleFixture)
   class MyFixture(Fixture):
        def new_user(self):
            return User('sam', roles=self.access_control_fixture.shopper_role)




Scope
~~~~~

Most |Fixture|\s live only for the duration of a single test. To deal with resources that are expensive to set up and
tear down, you can make a |Fixture| be set up only once, and be torn down only after all tests have run. Decorate the
|Fixture| with the |scope| decorator:

.. code-block:: python

   @scope('session')
   class WebServerFixture(Fixture):
        @set_up
        def start_web_server(self):
            ...

   @uses(webserver_fixture=WebServerFixture)
   class MyFixture(Fixture):
        ...

