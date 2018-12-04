Programmatic arguments
----------------------

If you pass a value to a keyword argument of |define_view| that is *not* a |Field|,
it is passed unchanged though to a matching keyword argument to the `.assemble` 
of your |UrlBoundView|.

For example, the `.assemble()` of a particular |UrlBoundView| may need
access to a :class:`~reahl.web.fw.Bookmark` which is computed inside
the `.assemble()` of its |UserInterface|.

.. code::

   edit = self.define_view('/edit', view_class=EditView, address_id=IntegerField(), some_bookmark=a_bookmark)


.. code::

   def assemble(self, address_id=None, some_bookmark=None):

           
Multiple possible destinations
------------------------------

In cases where there are multiple |Transition|\ s possible, things get
tricky:

At the time of defining the |Event| or placing the |Button| the exact
target |UrlBoundView| that will be transitioned to is not known yet. The
target |UrlBoundView| transitioned to will depend on the |Transition|
chosen -- something only known when the |Event| occurs. So be sure to
specify all possible arguments to all possible target  |UrlBoundView|\s  of all
possible |Transition|\ s from the |UrlBoundView| on which the |Button| is placed!
