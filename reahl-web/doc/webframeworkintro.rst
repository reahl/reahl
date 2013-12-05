.. Copyright 2010-2013 Reahl Software Services (Pty) Ltd. All rights reserved.
 
The Reahl web framework
-----------------------

The Reahl web framework provides a number of Python classes in terms
of which a programmer can create a web application. 

The idea of these classes is to hide complicated and repetitive
details of the web environment from the programmer - instead enabling
one to work in terms of high-level concepts, such as Widgets and
Events.



The cornerstones of Reahl user interfaces: Python and Widgets
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Much in a Reahl user interface revolves around the Widget class:

A Widget represents a user interface element - something a user can
see on screen and interact with. 

For example, Reahl ships with a Menu Widget. A Menu represents a
choice of options the user can follow to go to different possible
locations in the web application. Menus have simple behaviour: if the
user already is in the location where a particular option would lead,
that option is disabled (and visually indicated as such).

Other Widgets have much more sophisticated behaviour, such as Input
Widgets (discussed later).

Widgets can contain children Widgets. This allows a programmer to
build a new custom Widget by combining existing Widgets into one.

This is a big deal, because building a Widget from scratch can be
difficult - but combining existing Widgets is easy.

Some simple Widgets also mirror HTML elements. And these are so
simple, they make a good example for how a programmer would combine
Widgets into a new, more complex Widget.

.. code-block:: python

   class MyMessage(Div):
      def __init__(self, view):
          super(MyMessage, self).__init__(view)
          self.add_child(P(view, text=u'Hello World!'))

MyMessage is a very simple Widget that does nothing but display a
message.  It will eventually end up being displayed by a browser as
the HTML:

.. code-block:: html

   <div><p>Hello World!</p></div>

All Widgets are ultimately contained in something called a View. This
is why all Widgets are constructed with their View as first
argument.

Note also how the implementation of MyMessage itself just combines
other Widgets that already exist: Div and P.

Only the simplest of Widgets are like this one - it can render itself
to a browser as HTML and nothing more.  More useful Widgets typically
result in more complex combinations of HTML, CSS, JavaScript and even
dynamically added server-side URLs and logic.

The whole point of the Reahl web framework, however, is to *not* have
to think about all that low-level implementation details and rather
think and code in terms of the required results instead.


Dealing with user input
~~~~~~~~~~~~~~~~~~~~~~~

Some Widgets are specifically designed not only for display but also
to receive input from a user.  These are called Input Widgets. 

An important function related to Input Widgets is that the input
received from a user should also be validated. Such validation is not
done by the Input Widget itself, but by something called a Field:

In a typical application, there would be objects that model the
problem domain of the system. Things like Person, Order, or
EmailAndPasswordLoginCredentials. Let's call these sorts of objects "domain objects"
to distinguish them from all the very user-interface specific objects
otherwise talked about.

The purpose of an Input Widget is to display values that are contained
in the attributes of domain objects on a web page, and to allow a user
to change those values and otherwise interact with the domain objects.

Each Input Widget is linked to a Field. The Field provides extra
information about the data held by one attribute on some domain
object. This "meta information" is used by the Input Widget to
accomplish all sorts of things.

For example, an Input Widget can use the Field to render its own label
and to validate what the user types into the input.

Let's say a web application needs its users to be authenticated by
logging in with an email address and a password. One can model such
logins using the EmailAndPasswordLoginCredentials domain object:

.. code-block:: python

    class EmailAndPasswordLoginCredentials(object):
        def __init__(self):
	    self.email = None
	    self.password = None

	def log_in(self):
	    pass # Let's ignore the implementation details of this for now..

This class can be augmented with Fields that describe its attributes
as follows:

.. code-block:: python

    class EmailAndPasswordLoginCredentials(object):
        def __init__(self):
	    self.email = None
	    self.password = None

	    self.fields = FieldIndex(self)
            self.fields.email = EmailField(required=True, label=u'Email')
	    self.fields.password = PasswordField(required=True, label=u'Password')

	def log_in(self):
	    pass # Let's ignore the implementation details of this for now..


Given a domain object with Fields, Input Widgets can be created that
are linked to the Fields of such an object:

.. code-block:: python

    class LoginForm(Form):
        def __init__(self, view, name, login_credentials):
            super(LoginForm, self).__init__(view, name)

            self.add_child(TextInput(self, login_credentials.fields.email))
	    self.add_child(PasswordInput(self, login_credentials.fields.password))

The same Field can also be used on many different Input Widgets from
different places in a web application.

The Widgets and Fields have sophisticated behaviour when used
together. With the short example given, the following can happen:

Assume a user types something into the TextInput which is not a valid
email address.  As soon as the user leaves the input, an error message
will immediately be displayed via JavaScript on the browser.  This
error message will be very specific. The message will be something
like "Email should be a valid email address".  The specific label
"Email" will be used, because that is how the programmer specified the
label on the EmailField linked to the Input. The TextInput further
will check any input against a regular expression for valid email
addresses - because it was specifically an EmailField that was linked
to the TextInput.

When the error message appears, the Input Widget will also be
indicated visually as being in error.

A user could still bypass these validations by turning off the
browser's JavaScript capabilities.  For this reason the exact same
checks will also be performed server-side. And, the checks will result
in exactly the same error messages.

Error messages are also quite specific. Different error messages are
given for different error conditions. For example, "Email is required"
would be the message a user gets if nothing is typed in at all.
(Because that's how all this is specified in the Field).

User interfaces usually contain a lot of duplication: An attribute of
a particular domain object is often displayed (or input) in different
places in the user interface. But, because the programmer has one
domain object and one Field describing the rules for its attributes -
there is no need to specify how it should be validated on each of the
different places where it appears.


Reacting to user-initiated events
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The LoginForm example is not very useful at this stage, because it
contains no Buttons which the user could click to actually log in.

Reahl provides the concepts of Events and EventHandlers to deal with
actions initiated by a user.  

When a user clicks on a Button, the Reahl web framework is notified of
this by means of an Event. For it to be able to deal with a particular
Event, an EventHandler needs to be registered.

The simplest kind of EventHandler merely supplies a server-side method
that should be called when the Event is detected.

Just like Inputs are linked to Fields - each Button is linked to a
named Event.  That is simply a way of stating that the given Event
(and thus its EventHandler) will be triggered when the user clicks on
the Button associated with the Event.

In code, this looks simpler than in a wordy explanation:

.. code-block:: python

    class LoginForm(Form):
        def __init__(self, view, name, login_credentials):
            super(LoginForm, self).__init__(view, name)

            self.add_child(TextInput(self, login_credentials.fields.email))
            self.add_child(PasswordInput(self, login_credentials.fields.password))

            log_in_event = Event(u'login_event')
            self.add_event(log_in_event, action=login_credentials.log_in)
            self.login_button = Button(self, log_in_event, u'Log in')

With this example, when a user clicks on the Button (labelled "Log
in"), the .log_in() method of the login_credentials object will be
called.

Note though that the email and password Fields of that same object
just so happen to be linked to the two Input Widgets of the LoginForm
as well.

The effect of this is that the relevant attributes of the
login_credentials object will first be populated with the new input
received from the user before .log_in() is actually called.

The "action" of an EventHandler never takes arguments. User input is
automatically sent along with any related Event and dealt with via
domain objects, Inputs and Fields before the relevant action is
invoked.

This way of dealing with user actions is very simple but has its
limitations.  Reahl provides some modifications to EventHandlers and
even special EventHandlers that allow a programmer to easily deal with
more complex web applications.


Different Views of the same main window
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Like many GUI applications, every ReahlWebApplication (another of the
Python classes of Reahl) has a main window.  This is basically
everything a user sees *inside* a browser's window frame.

The main window is nothing but a Widget of your choice - pre-built or
of your own design.

An example main window could contain a header and footer and Menu (aka
navigation bar) - the stuff that's always there while the user is in
the web application.

Apart from the main window, a ReahlWebApplication consists of a number
of Views - each of which uniquely represents some "location" you can
be at in the web application.  If the user types an URL into the
browser's location bar, the browser takes the user to one such View in
a ReahlWebApplication. Each time the URL changes in the browser, the
user sees a different View.

But, a View cannot be presented to a user on its own. It has to be
presented as part of the application's main window: the user thus sees
different Views of the same main window.

Before an explanation of how the look of a window can change so
conveniently to suit different Views, it is time for a first (but
quite empty) ReahlWebApplication.


Example: A first ReahlWebApplication
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

To build a ReahlWebApplication, a programmer creates a class which
inherits from ReahlWebApplication and supplies a custom "assemble"
method in which the details of the web application are given:

.. code-block:: python

   class MyWebApp(ReahlWebApplication):
       def assemble(self):
           self.attach_main_window(u'/', TwoColumnPage)
           self.define_view(u'/', title=u'Hello World')
           self.define_view(u'/page2', title=u'Page 2')

There are predefined Widgets suitable for use as a main window. The
TwoColumnPage is one such Widget, which represents a page with header
area at the top, footer area at the bottom, and large (main) and small
(secondary) columns inbetween.

The main window is attached at the '/' URL. This means that it will
be the main window for all URLs visited underneath '/' as well.

This example application has two Views: one at '/' and another at
'/page2'. Each View has a title as specified (as the second argument
to define_view), but the Views are both empty apart from that.

Note that TwoColumnPage is smart enough to use the title of the
current View as the contents of the browser's title bar.

Note also that individual Views contain no knowledge of the actual
window they will be displayed in.

This means that a View can be developed and re-used in different web
applications that use entirely different main windows.


More about main windows and Views
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

As stated, a main window is always displayed *for a particular*
View. The View adds some content to the main window, thus changing the
main window to some extent.

This is accomplished by using a special kind of Widget, called a Slot.
The main window can contain Slots - each with its own name.  The Slots
on a window are placeholders that can be filled by a View being
displayed.

Each View is merely a statement saying which additional Widgets must be
plugged into which Slots of the main window. This mapping is specified
using the name of the Slot.

Lets expand our example to display some content on each View:

.. code-block:: python

   class MyWebApp(ReahlWebApplication):
       def assemble(self):
           self.attach_main_window(u'/', TwoColumnPage)

           p1 = self.define_view(u'/', title=u'Hello World')
           p1.set_slot(u'main', P.factory(text=u'This is page one'))

           p2 = self.define_view(u'/page2', title=u'Page 2')
           p2.set_slot(u'main', P.factory(text=u'This is page two'))


Note how .set_slot is used on each added view to add a Factory for the
Widget which should go into the Slot named 'main' - in this case.
TwoColumnPage contains a number of Slots for use of which 'main' is
one.

Factory is a recurring theme in Reahl programming. Remember a web
application is viewed by many people at the same time. Thus, (for
example) different instances are needed of the same View (and thus the
Widgets it contains) for different people. This is why an actual
Widget is never created in .assemble() - the programmer only specifies
how Widgets of a View would be constructed by means of a Factory.
Such a Factory contains all information necessary to create the
Widget.

The same actually goes for the Views themselves and the Widget used as
a main window - p1 and p1 above are not Views, they are also ViewFactories.

Note also the usage of the .factory() method to obtain a factory for a
particular kind of Widget.  All Widgets are constructed taking a View
as first argument.  At the time of assembling the ReahlWebApplication
such a View is not yet available.  The .factory() method takes the
arguments the actual Widget would have taken except for its View.


Conquering complexity and enabling reuse
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Big, complex programs are always split into smaller pieces of some
kind.  Splitting a program into smaller manageable chunks makes the
application as a whole easier to understand and maintain. But, it also
has another use: these modules are normally reusable in different
programs.

With what's been explained so far a Reahl programmer can do this at a
finely-grained level by means of Widgets.

More is needed though. Reahl also provides a way to collect a number
of related Views together in a module.  These modules are called
Regions:

A Region, logically speaking, is merely a chunk of web
application. Regions can be packaged and distributed as separate
entities.  And, Regions can be attached to your web application by
literally grafting the tree represented by the URLs of all Views
contained in the Region onto particular URLs of a web application.

For example: Lets assume that someone supplies a MagazineRegion -
intended to provide a place where users can peruse articles that form
part of a Magazine.

To the author of the Region, the Region may contain Views at '/' and
'/manage'. (Let's assume on '/' users would see a list of all articles
of the magazine, and on '/manage' special users are able to add more
articles etc.

If a programmer attaches the Region onto the URL '/reading' on a
particular web application, those Views will be accessible via
'/reading/' and '/reading/manage', respectively on the web
application.

Note how the URLs of Views of a Region are relative to the Region.

This is necessary, because the Region cannot contain knowledge of
where it will be grafted onto (potentially many) different websites.

Similarly, the Region also needs to have its own names for Slots.
Different main windows have different Slots in them. The Region is
developed without this knowledge precisely because it should be able
to work with any given main window.

At the time of attaching a Region to a ReahlWebApplication, the
programmer specifies all this hitherto unknown information:

.. code-block:: python

   class MyWebApp(ReahlWebApplication):
       def assemble(self):
           self.attach_main_window(u'/', TwoColumnPage)

           magazine = MagazineRegion.factory(u'magazine_region', directory_name=u'my_magazine')
           self.attach_region(u'/reading', magazine, {u'maincontent': u'main'})
           
           # ... and the rest of assemble ...


Of course, the author of the Region decides what Slot names the Region
would supply Widgets for. The author of the web application needs this
information to know where the Region's elements will appear on the
main window.  In this example, what the Region calls "maincontent"
will be plugged into the Slot of the main window called "main".

The MagazineRegion's factory() method also shows two other interesting
facts:

Each Region should have a name which is unique in your web
application. That's the first argument to its .factory().

And, Regions (Widgets too, actually), may take parameters in the form
of keyword arguments.  These are supplied to the Factory as well. What
they're called, of course, again depends the author of the Region
itself.  Our example region needs a directory_name argument - the name
of the collection of articles it will allow users to peruse.

Developing a Region is not much different from developing a simple
ReahlWebApplication. Here is an extract from a Region which allows
users to go through the process of registering on a web application.

.. code-block:: python

   class RegistrationRegion(Region):
       def assemble(self):
           register_slots={}
           register = self.define_view(u'/register', title=u'Register with us')
	   register.set_slot(u'main_slot': RegisterWidget.factory())

           congrats = self.define_view(u'/congrats', title=u'Congratulations')
           congrats.set_slot(u'main_slot', CongratsWidget.factory())


Managing relativity
~~~~~~~~~~~~~~~~~~~

Everything inside a Region is relative in order to make the Region
reusable in different contexts: Regions have to be built with no
information of the context they will be used in.

This relativity is actually not a strange concept: the functions and
methods of a programming language are also written without any
knowledge of where they will be called from. They also have different
names inside of them for variables passed in from the calling context.

Web developers are typically not used to this sort of relativity.
They typically work in terms of absolute URLs, links, templates etc.

Reahl provides concepts that allow a web programmer to forget about
all those implementation details and to think in terms of a level
above those implementation details.

To get away from URLs, Reahl provides the concept of a Bookmark:

A Bookmark is a way to refer to a specific View. It also contains meta
information about the View, such as its title.  Bookmarks
transparently take care of Views that are relative.

To get a Bookmark for a specific View, a RegionFactory can be asked
for a Bookmark to that View using the .get_bookmark() method. The
parameters to this method varies, depending on the actual Region.

The simplest .get_bookmark() method would take the URL of a View
*relative* to its Region:

.. code-block:: python

   class MyWebApp(ReahlWebApplication):
       def assemble(self):
           self.attach_main_window(u'/', TwoColumnPage)

           registration = RegistrationRegion.factory(u'registration')
           self.attach_region(u'/register', registration, {u'main_slot': u'main'})

           bookmark_to_register = registration.get_bookmark(relative_path=u'/register')


Better, more abstract ways of finding bookmarks can be supplied by
Regions though. For example, a GalleryRegion may support finding a
Bookmark for a particular photo:

.. code-block:: python

   bookmark_to_photo = gallery_region.get_bookmark(for_photo=photo)


Finding a Bookmark for a View is important, because many Widgets are
consumers of Bookmarks.  For example, a Menu can be constructed from a
list of Bookmarks:

.. code-block:: python

   my_menu = Menu.from_bookmarks(view, [registration_bookmark, gallery_bookmark])


Making it look distinctive
~~~~~~~~~~~~~~~~~~~~~~~~~~

Reahl Widgets include everything necessary to enable their
functionality. However, customers do not want their web applications
to look like those of their competition! Customers want the look of their
web applications to be customised to their own specifications.

Reahl Widgets include very little CSS to govern their look.  But they
do include CSS - mainly for important internal layout of the Widgets
where necessary. 

More CSS is needed to style the look and feel of Widgets, and this
still needs to be supplied by a programmer.  (One day perhaps we'd be
able to hide that better as well, but it is not today.)


Gaining more from Reahl
~~~~~~~~~~~~~~~~~~~~~~~

This document serves as an introduction to the Reahl web framework.

The Reahl web framework is different. Hopefully the reader would grasp
just what the Reahl web framework is after reading this introduction.

There are many more aspects of Reahl which enables programmers to deal
with more and more advanced requirements.

These advanced topics are dealt with in further chapters.

    




