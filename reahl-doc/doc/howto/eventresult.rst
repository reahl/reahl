.. Copyright 2022 Reahl Software Services (Pty) Ltd. All rights reserved.

.. |define_view| replace:: :meth:`~reahl.web.fw.UserInterface.enable_refresh`
.. |UserInterface| replace:: :class:`~reahl.web.fw.UserInterface`
.. |UrlBoundView| replace:: :class:`~reahl.web.fw.UrlBoundView`
.. |ButtonInput| replace:: :class:`~reahl.web.ui.ButtonInput`
.. |assemble| replace:: :meth:`~reahl.web.fw.UrlBoundView.assemble`
.. |Field| replace:: :class:`~reahl.component.modelinterface.Field`
.. |Event| replace:: :class:`~reahl.component.modelinterface.Event`
.. |Action| replace:: :class:`~reahl.component.modelinterface.Action`
.. |Bookmark| replace:: :class:`~reahl.web.fw.Bookmark`
.. |with_returned_argument| replace:: :meth:`~reahl.component.modelinterface.Event.with_returned_argument`
.. |with_arguments| replace:: :meth:`~reahl.component.modelinterface.Event.with_arguments`

Providing values to the arguments of an Event on the fly
========================================================

:doc:`As explained in the tutorial example
<../tutorial/parameterised>`, when transitioning to an |UrlBoundView|
which is parameterised, the |Event| used to specify the transition has
arguments matching those of the destination |UrlBoundview| and also
values for these arguments.

|Event| argument values are supplied where the |Event| is passed to a |ButtonInput| by calling the
|with_arguments| method.

Sometimes, however, those argument values are not yet known at this time:

In this example an Address is added on the '/add' view, and the user is transitioned after that to
the '/review' view. The '/review' view needs an argument: the id of the added address to review.

When the |ButtonInput| is rendered on the '/add' view, the new Address is not yet saved to the
database, and thus its id is not known. Only once the user clicks on 'Save' do we know the
id of the new Address.

In this case, instead of passing the |ButtonInput| an |Event| |with_arguments|, pass an
|Event| |with_returned_argument| :

.. literalinclude:: ../../reahl/doc/examples/howtos/eventresult/eventresult.py
   :pyobject: AddressForm

Declare the `save` |Event| with an `address_id` argument and return the new Address' id
from the method executed by the |Action| of the `save` |Event|:

.. literalinclude:: ../../reahl/doc/examples/howtos/eventresult/eventresult.py
   :pyobject: Address


Also parameterise the '/review' |UrlBoundView| to require a matching `address_id` argument:

.. literalinclude:: ../../reahl/doc/examples/howtos/eventresult/eventresult.py
   :pyobject: AddressBookUI


