.. Copyright 2018 Reahl Software Services (Pty) Ltd. All rights reserved.

.. |Transition| replace:: :class:`~reahl.web.fw.Transition`
.. |Event| replace:: :class:`~reahl.component.modelinterface.Event`
.. |ButtonInput| replace:: :class:`~reahl.web.ui.ButtonInput`
.. |UrlBoundView| replace:: :class:`~reahl.web.fw.UrlBoundView`

Multiple possible destinations
==============================

.. sidebar:: Examples in this section

   - web.xxxx

   Get a copy of an example by running:

   .. code-block:: bash

      reahl example <examplename>


Multiple possible destinations
------------------------------

In cases where there are multiple |Transition|\ s possible, things get
tricky:

At the time of defining the |Event| or placing the |ButtonInput| the exact
target |UrlBoundView| that will be transitioned to is not known yet. The
target |UrlBoundView| transitioned to will depend on the |Transition|
chosen -- something only known when the |Event| occurs. So be sure to
specify all possible arguments to all possible target  |UrlBoundView|\s  of all
possible |Transition|\ s from the |UrlBoundView| on which the |ButtonInput| is placed!