.. Copyright 2013 Reahl Software Services (Pty) Ltd. All rights reserved.
 
Developing your own Widgets
===========================

A programmer should be able to build web applications entirely from
:class:`~reahl.web.fw.Widget`\ s that are available, without ever having to think about the
underlying technologies. That is what Reahl is about. However, it is
possible for programmers to directly use all the lower-level web
technologies in order to create :class:`~reahl.web.fw.Widget`\ s so that others can reap the
benefit of re-use of these :class:`~reahl.web.fw.Widget`\ s.

This is obviously an advanced topic, and a big one which falls
outside the scope of this tutorial. Knowing a little about *what is
possible* on that level is useful though: it gives you a better sense
of how Reahl works, and how it is different from other :class:`~reahl.web.fw.Widget`-sporting
frameworks.

This section explains the gist of what is possible, without the gory
details.


What is a Widget, really
~~~~~~~~~~~~~~~~~~~~~~~~

If you search web designer and web development forums, you will find a
lot of tricks that are presented in order to achieve a certain effect
on a web page. These tricks invariably use a combination of web
technologies: you may have to write a bit of HTML and a bit of CSS and a
bit of JavaScript to make it work. You may also have to provide some
server-side code, exposed via one or more URLs.

Imagine if you can take all the bits of code and URLs in all the
various languages that make up one trick and package it in a way that
not only makes it reusable, but that hides all that stuff and make the
programmer's world consist of Python only.

That is the dream fuelling Reahl :class:`~reahl.web.fw.Widget`\ s. 

To fulfill the dream, the developer of a low-level :class:`~reahl.web.fw.Widget` needs to be
able to use all those web development tricks, and wrap them in
something with the face of a :class:`~reahl.web.fw.Widget` class.

For a start, a :class:`~reahl.web.fw.Widget` is built around its Python class. Server-side
logic goes into the Python class but the Python class is also
responsible for generating some HTML. :class:`~reahl.web.fw.Widget`\ s exist for most basic
HTML elements. Thus, you can easily compose a :class:`~reahl.web.fw.Widget` from other
:class:`~reahl.web.fw.Widget`\ s to achieve the required basic HTML representation wrapped in a
Python class.


Adding JavaScript
~~~~~~~~~~~~~~~~~

.. sidebar:: Behind the scenes

   For most things JavaScript, Reahl uses `JQuery
   <http://jquery.com>`_ and just one small bit of functionality from
   the JQuery UI project: the `Widget Factory
   <http://api.jqueryui.com/jQuery.widget/>`_.

To add JavaScript to the mix, you use something akin to a class, but
written in JavaScript in which you write all code that needs to be
executed in the browser *for your* :class:`~reahl.web.fw.Widget`. This 'JavaScript class' is
instantiated on the browser for the HTML of each instance of your
Python :class:`~reahl.web.fw.Widget` present on a page.

If a :class:`~reahl.web.fw.Widget` needs a 'JavaScript class' to be instantiated on the
browser end, it achieves this by implementing a special method. This
method (`.get_js()`) returns a small snippet of JavaScript code which will
instantiate the JavaScript for that :class:`~reahl.web.fw.Widget` on a page when executed. When
rendering an :class:`~reahl.web.ui.HTML5Page`, the framework collects all these snippets
of JavaScript from all :class:`~reahl.web.fw.Widget`\ s on that page and include them on the
page in a ``<script>`` element. This takes care of instantiating the
JavaScript side of :class:`~reahl.web.fw.Widget`\ s.

For this to work, the code implementing each 'JavaScript class' also
needs to be included somewhere on the page -- this is the code that is
called in the 'instantiating' snippets. Code for such 'JavaScript
classes' is written in a separate `.js` files. Each such `.js` file is
listed in the `.reahlproject` file of the component containing
it. When a web application is started, Reahl builds one `.js` file
that contains all `.js` files of all the components used by your
application and makes the big file available via an URL that is
included in any :class:`~reahl.web.ui.HTML5Page` via a ``<script type="text/javascript">``
element. (This file is thus the bulk of JavaScript code, and it will fetched
once by browsers and then cached for other pages.)

That's really all there is to it... Some more details to make it more
concrete:

.. sidebar:: A word about terminology

   Perhaps confusingly (for Reahl people) this 'JavaScript class' is
   called a "widget" in JQuery UI parlance. It makes sense in their
   world, because a JQuery UI widget is written in JavaScript
   only. Reahl uses this infrastructure to let you build the
   JavaScript side of a Reahl :class:`~reahl.web.fw.Widget`.

Reahl uses the so-called `Widget Factory
<http://api.jqueryui.com/jQuery.widget/>`_ from the JQuery UI project
to simplify the development of the equivalent of a class, but written
in JavaScript. If you don't know the Widget Factory, here's how it
works: the Widget Factory is a function called `widget()`. You call
`widget()` with the name of the `JavaScript class` to be created and
a JavaScript object that contains a function for each method you want
on the 'JavaScript class'. The special function `_create()` is the
constructor of the 'JavaScript class'. 

What the Widget Factory does is to add a function to the JQuery
object which will create an instance of your 'JavaScript class' for
each HTML element selected by a normal JQuery selection.

For an example, have a look at the implementation of :class:`~reahl.web.ui.LabelOverInput`. A
:class:`~reahl.web.ui.LabelOverInput` looks like an :class:`~reahl.web.ui.Input` with its label printed where you'd
expect a user to type some input. When a user clicks there to supply
some input, the label disappears. The HTML for :class:`~reahl.web.ui.LabelOverInput` is
basically a `<span>` that contains a `<label>` as well as another
`<span>` that wraps the actual `<input>` at stake.

To make this plan work, the :class:`~reahl.web.ui.LabelOverInput` needs some CSS for
positioning the `<label>` on top of the `<input>`. It also needs some
JavaScript to make the label appear and disappear at the right moments.

Here is the 'JavaScript class' for :class:`~reahl.web.ui.LabelOverInput`:

.. literalinclude:: ../../../reahl-web/reahl/web/reahl.labeloverinput.js
   :language: js

In the code sample only one method is needed: `_create()`. This method
is the constructor of our 'JavaScript class'. The variable `this` is
bound to an instance of our JavaScript class inside the
functions. Similarly, `this.element` refers to the HTML element to
which this instance of the JavaScript class is bound (the outer
`<span>`, which represents a complete :class:`~reahl.web.ui.LabelOverInput` in HTML).

On the Python side, the :class:`~reahl.web.fw.Widget` needs the `.get_js()` method that
should return a small line of JavaScript needed to instantiate the
'JavaScript class', browser side. Using Jquery and the JQuery UI
widget function, this is something small, like:

.. code-block:: python

    def get_js(self, context=None):
        return ['$(".myclass").labeloverinput();']

The Python implementation of :class:`~reahl.web.ui.LabelledInlineInput` does not illustrate
how the HTML is composed, since it inherits all of that from
:class:`~reahl.web.ui.LabelledInlineInput`. It does illustrate attaching of JavaScript well
though, since adding an HTML class attribute, JavaScript and CSS is
all it really does:

.. literalinclude:: ../../../reahl-web/reahl/web/ui.py
   :pyobject: LabelOverInput



Adding CSS
~~~~~~~~~~

Sometimes it is necessary to make some CSS also part of the
implementation of a :class:`~reahl.web.fw.Widget`. While the end-user may want to add
site-specific CSS to deal with the fonts, colors and sizes of an item,
sometimes the client-side functionality depends on a little bit of CSS.

The :class:`~reahl.web.ui.LabelOverInput` above is again an example of that. It needs some
CSS to help hide its label. CSS is attached in a similar way to how
JavaScript is attached. It is written in a file for that :class:`~reahl.web.fw.Widget`, and
registered in a `.reahlproject` from where the framework can pick up
all the bits of CSS for a web application and serve it up as one file.

To attach the CSS to the HTML, the CSS would also have to reference
the class attribute of a piece of HTML. The CSS for :class:`~reahl.web.ui.LabelOverInput` is
as follows:

.. literalinclude:: ../../../reahl-web/reahl/web/reahl.labeloverinput.css
   :language: css



Adding server-side URLs
~~~~~~~~~~~~~~~~~~~~~~~

Let's assume you are working on a web application that allows users to
store and browse Photos online. Perhaps you'd like to show smaller
"thumbnail" versions of photos on some overview page of sorts. You
would need a Thumbnail :class:`~reahl.web.fw.Widget` for this.

In order to show a small picture, the HTML for a Thumbnail :class:`~reahl.web.fw.Widget`
would need to include an `<img>` element, and the `src` attribute of that
element needs an URL to be available on the server from where it will
fetch a shrinked version of the original image. Users of your
Thumbnail :class:`~reahl.web.fw.Widget` do not want to know about this though: it is
low-level stuff -- it must just happen.

When a :class:`~reahl.web.fw.Widget` is instantiated, it can register so-called :class:`~reahl.web.fw.SubResource`\ s
with the framework. A :class:`~reahl.web.fw.SubResource` can be a static file which is
reachable via an URL, or a method that can be called server-side by
visiting (or posting to) an URL, for example. The URLs of the
:class:`~reahl.web.fw.SubResource`\ s of a particular instance of a :class:`~reahl.web.fw.Widget` will all be made
available underneath the URL of all the  :class:`~reahl.web.fw.View`\ s  on which the :class:`~reahl.web.fw.Widget` is
used: If a :class:`~reahl.web.fw.Widget` appears on a :class:`~reahl.web.fw.View` with URL '/a/b', the URL for a
:class:`~reahl.web.fw.SubResource` of a :class:`~reahl.web.fw.Widget` will be something like
'/a/b/__my_small_pic'. (Each :class:`~reahl.web.fw.SubResource` has to have a unique name
from which its URL is derived.)

:class:`~reahl.web.fw.SubResource` URLs can also be parameterised, just like a :class:`~reahl.web.fw.View` can be
parameterised. This has the effect that the :class:`~reahl.web.fw.SubResource` is only
created once its URL is actually accessed.

