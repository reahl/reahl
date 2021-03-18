.. Copyright 2013, 2014, 2016 Reahl Software Services (Pty) Ltd. All rights reserved.
 
Developing your own Widgets
===========================

.. |Widget| replace:: :class:`~reahl.web.fw.Widget`
.. |Div| replace:: :class:`~reahl.web.ui.Div`
.. |Library| replace:: :class:`~reahl.web.libraries.Library`
.. |HTMLElement| replace:: :class:`~reahl.web.ui.HTMLElement`
.. |RemoteMethod| replace:: :class:`~reahl.web.fw.RemoteMethod`

A programmer should be able to build web applications entirely from
|Widget|\s that are available, without ever having to think about the
underlying technologies. That is what Reahl is about. However, it is
possible for programmers to directly use all the lower-level web
technologies in order to create novel |Widget|\s that can be re-used
from Python.

This is obviously an advanced topic, and a big one which falls outside
the scope of this tutorial. Knowing a little about *what is possible*
on that level is useful though: it gives you a better sense of how
Reahl works, and how it is different from other |Widget|\-sporting
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

That is the dream fuelling Reahl |Widget|\s. 

To fulfill the dream, the developer of a low-level |Widget| needs to
be able to use all those web development tricks, and wrap them in
something with the face of a Python |Widget| class.

For a start, a |Widget| is built around its Python class. Server-side
logic goes into the Python class but the Python class is also
responsible for generating some HTML. |Widget|\s already exist for
most basic HTML elements. Thus, you can easily compose a |Widget| from
other |Widget|\s to achieve the required basic HTML representation
wrapped in a Python class.


.. _shipping_js_css:

Shipping JavaScript and CSS code
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

JavaScript and CSS code that works in concert with the Python code of
your |Widget| is written in separate files. Remember, such code must be
sent to the client browser to be executed on that side.

There are two aspects to this problem:

 packaging:
    You need a way to include CSS/JavaScript files to be packaged with your Python egg.

 inclusion on a web page:
    You need a way to include each CSS/JS file on every :class:`~reahl.web.ui.HTML5Page` of your app.

The :mod:`reahl.web.libraries` module includes the tools you need to
fulfill these tasks.

In short, you just put your JavaScript or CSS files somewhere in the
directory of one of your Python packages. Then you create a |Library|
subclass which represents your project's JavaScript and CSS code. (The
frontend-code of your project.)

Lastly, you need to change your configuration to include your new
|Library|. This is done in file file `web.config.py`:

.. code-block:: Python

   from some.module import MyLibrary

   web.frontend_libraries.add(MyLibrary())

Once this is done your CSS and JavaScript will be present on any
:class:`~reahl.web.ui.HTML5Page`.


Adding CSS
~~~~~~~~~~

Adding CSS to your own Widget is really simple. You just include CSS
(as explained above) which uses a CSS selector that will target the
|HTMLELement| representing your |Widget|.

For example, in your Python class you can do this:

.. code-block:: Python

   class MyWidget(Widget):
       def __init__(self, view):
           super(MyWidget, self).__init__(view)
           self.div = self.add_child(Div(view))
           self.div.append_class('mywidget')

Then add CSS by including a CSS file in your |Library| containing:

.. code-block:: CSS

   div.mywidget: { border: 1px solid black; }


JavaScript + Python: a pattern
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. sidebar:: Behind the scenes

   For most things JavaScript, Reahl uses `JQuery
   <http://jquery.com>`_ and just one small bit of functionality from
   the JQuery UI project: the `Widget Factory
   <http://api.jqueryui.com/jQuery.widget/>`_.

JavaScript needs a bit more thought:

Here's how we think of |Widget|\s: The Python class represents the
|Widget| as a whole. The Python class also is responsible for
generating HTML and to handle any server-side logic. 

However, there is a part of that |Widget| that is executed on the
client browser as JavaScript. This JavaScript conceptually also is
part of the |Widget| -- it is its JavaScript half, so to speak.

Wouldn't it be nice if you can create a JavaScript instance in the
browser for each instance of your |Widget| that is present on a page?
Well, it turns out you can.

There are three steps to this: 

 #. write the code for a JavaScript widget (the code re-used by each instance); 

 #. include that code on your pages; and

 #. instantiate a JavaScript instance for each rendered instance of your |Widget| on page load.

Since we've already covered distributing and including JavaScript code
on your pages, let's skip that middle step here. As for the other two:

Write code for a JavaScript widget
""""""""""""""""""""""""""""""""""

.. sidebar:: A word about terminology

   Perhaps confusingly (for Reahl people) this 'JavaScript widget' is
   called a "widget" in JQuery UI parlance. It makes sense in their
   world, because a JQuery UI widget is written in JavaScript
   only. Reahl uses this infrastructure to let you build the
   JavaScript *side* of a Reahl |Widget|.

What works quite well with such code is to put the JavaScript half of
your |Widget| into what JQuery UI calls a "JavaScript widget". This is
something that is very much like a class in JavaScript that is attached
to an |HTMLElement| which represents your |Widget| in the browser DOM.

Here is an example of how we do it:

.. code-block:: JavaScript

   (function($) {
   "use strict";

   $.widget("mywidgetjs", {
       options: {
          message: 'a default message to show'
       },

       // This is like __init__ for your JavaScript half. It will be called to initialise each instance.
       _create: function() {
           // in the scope of such a "method" the following holds:
           //     the variable "this" is the javascript widget's instance... just like Python's self:
           this.anothermethod();

           //     this.options is the options the widget was constructed with:
           alert(this.options.message);

           //     and this.element is a Jquery Query on the element to which the JavaScript widget was attached:
           this.element.addClass("mywidget");
       },
       anothermethod: function() {
       }
   });

   $.extend($.mywidgetjs, {
       version: "1.8"
   });

   })(jQuery);


Instantiating JavaScript instances
""""""""""""""""""""""""""""""""""

Your |Widget| must be represented in HTML by some |HTMLElement|. Let's
assume it is a :class:`~reahl.web.ui.Div` for argument's sake.

If you give such a |Div| a css class, say 'mywidget', you can
instantiate its JavaScript half (done in the previous section) using
JavaScript like this:

.. code-block:: JavaScript

   $("div.mywidget").mywidgetjs("{message:'Hello there'}")

Reahl has a mechanism by which a |Widget| can register such a
small JavaScript snippet for execution on page load. The Python class
of your |Widget| only needs to implement a
:meth:`reahl.web.fw.Widget.get_js` method. Reahl collects all such
JavaScript snippets for all |Widget|\s on a page and makes sure they
are executed at page load time.

Here is an example:

.. code-block:: Python

   class MyWidget(Widget):
       def __init__(self, view):
           super(MyWidget, self).__init__(view)
           self.div = self.add_child(Div(view))
           self.div.append_class('mywidget')

       def get_js(self, context=None):
           my_snippets = ['''$("div.mywidget").mywidgetjs("{message:'Hello there'}")''']
           return super(MyWidget, self).get_js(context=context) + my_snippets


Different instances with different options
""""""""""""""""""""""""""""""""""""""""""

If you have several MyWidgets on a page, our example so far will
create a JavaScript widget instance for each of them because it uses a
JQuery selector that will find them all ("div.mywidget").

This is very economical because Reahl will ensure that the JavaScript
snippet is only included once on the page, not once per MyWidget
instance.

However, if you need to send different options to different Widget
instances, you may have to choose a different selector that will
target each instance individually. For example:

.. code-block:: Python

   class MyWidget(Widget):
       def __init__(self, view, unique_name, message):
           super(MyWidget, self).__init__(view)
           self.div = self.add_child(Div(view))
           self.div.set_id(unique_name)
           self.message = message

       def get_js(self, context=None):
           my_snippets = ['''$("div#%s").mywidgetjs("{message:'%s'}")''' \
                             % (self.unique_name, self.message)]
           return super(MyWidget, self).get_js(context=context) + my_snippets



Adding server-side URLs
~~~~~~~~~~~~~~~~~~~~~~~

.. |SubResource| replace:: :class:`~reahl.web.fw.SubResource`
.. |View| replace:: :class:`~reahl.web.fw.View`

Let's assume you are working on a web application that allows users to
store and browse Photos online. Perhaps you'd like to show smaller
"thumbnail" versions of photos on some overview page of sorts. You
would need a Thumbnail |Widget| for this.

In order to show a small picture, the HTML for a Thumbnail |Widget|
would need to include an `<img>` element, and the `src` attribute of that
element needs an URL to be available on the server from where it will
fetch a shrinked version of the original image. Users of your
Thumbnail |Widget| do not want to know about this though: it is
web-implementation details that should be hidden.

When a |Widget| is instantiated, it can register a so-called
|SubResource| with its current |View|. A |SubResource| represents an
URL controlled by your |Widget|. What it does is up to you.  Reahl
already includes different kinds of |SubResource|\s to be able to deal
with forms, validation, ajax and all manner of things. A
|RemoteMethod|, for example exposes a method on a Python instance on
the server -- but it can be invoked by POSTing to its URL.

In the example above, you may use a |RemoteMethod| which queries the
database for the thumbnail version of a given photo -- and then
returns the thumbnail as a .png file.

The bottom line here is that the |Widget| creates its own
|SubResource| so that users of the |Widget| need to be aware of this
extra server-side URL that is needed to make things work.  The
|Widget| also can use the URL of the |SubResource| it created in
places like the `src` of an :class:`~reahl.web.ui.Img`. All of these
implementation details is thus hidden from the programmer who just
needs to instantiate the |Widget| without concern for its extra hidden
URLs.

|SubResource| URLs can also be parameterised, just like a |View| can be
parameterised by passing parameters via its Url.


