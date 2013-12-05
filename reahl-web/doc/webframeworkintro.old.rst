.. Copyright 2011, 2012, 2013 Reahl Software Services (Pty) Ltd. All rights reserved.
 
The Reahl web framework
-----------------------

The Reahl web framework speeds up web application development and
results in high quality web applications.

Its approach is centered around two themes:

Firstly - when something is cumbersome to build, it makes sense to
reuse pre-built parts rather than to build everything you need from
scratch. Most web frameworks make reuse difficult or impossible. Reahl
enables reuse on many different levels and in different ways.

Secondly - usually a lot of the attention of a web application
programmer goes into low-level details regarding web technologies and
the oddities of the web as an application platform.  Reahl presents a
neat set of concepts that abstracts away all of the irrelevant and
complex details not directly related to the problem at hand.

This document introduces the Reahl web framework by explaining its
basic concepts.

A word of warning though: forget what you know about other web
frameworks. Come with an open mind - this is all new (for the web),
and sometimes in subtle ways.


An executive summary
~~~~~~~~~~~~~~~~~~~~

This document explains the fundamentals of the Reahl web framework at
length, enumerating the benefits and subtleties along the way.

This section is a quick summary of what follows - meant only for the
impatient:

Firstly, Reahl programmers write web applications purely in Python,
using classes that implement the concepts explained here. All web
technologies are hidden away behind that.

Anything visual in Reahl is accomplished by means of one or more
Widgets: pre-built visual elements.  A programmer can combine existing
Widgets to form more complex custom Widgets. 

Reahl Widgets are extremely powerful: anything one can implement on
the web can be wrapped into a Widget. Programmers willing to learn
more about Reahl internals and the underlying web technologies can
develop their own basic Widgets if they *really* need to.

Input Widgets accept input from a user, and Button Widgets provide a
way for a user to trigger Events upon which the web application should
react.

When composing a user interface using Widgets, a programmer links
particular Events to individual Buttons, and registers an EventHandler
for each Event. When the user clicks the Button, its associated Event
is said to occur. The simplest form of EventHandler merely states what
method to call upon the occurrence of its Event.

A Reahl programmer can augment any Python object with Fields. Each
Field contains more information about one attribute of the Python
object.  

Upon construction of Input Widgets, each Input Widget is linked to a
corresponding Field.  This allows the Widget to be able to
automatically provide all sorts of behaviour - such as user input
validation and robust reporting of related error messages.

Different kinds of Inputs represent different visual Widgets; the
Fields they are linked to provide information used to perform input
validation for different kinds of "data types".  For example,
TextInput may be linked to an EmailField. 

Each ReahlWebApplication consists of different Views - one View for
each URL a user could visit.  All Views are in turn presented via a
single main window of the web application.

The main window is a Widget which results in a complete web page. It
contains Widgets common to all pages in the web application. The main
window also contains Slots: named placeholders where more Widgets can
be inserted on demand.

An individual View is presented via the main window by inserting extra
Widgets (as specified by the View) into the Slots of the main window.

ReahlWebApplications can be split into modules called Regions.  A
Region is a collection of Views that are packaged together and can be
reused in any number of web applications regardless of what they look
like or what URLs they define.

Most ReahlWebApplications are developed in modular fashion by first
developing a number of Regions, and then assembling them together.


The cornerstones of Reahl user interfaces: Python and Widgets
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The Reahl web framework provides a number of Python classes in terms
of which a programmer can create an entire web application. 

The first of these is the Widget class:

A Widget represents a user interface element - something a user can
see on screen and interact with. In order for a particular Widget to
be able to implement all of its visual elements and associated
behaviour, it may need a blend of many different chunks of technology,
such as its own bit of HTML, CSS, JavaScript and even server-side
logic and extra URLs on the server.

To the user of the Widget, however, all these implementation details
are completely hidden behind a single Python class.

There's no need for a programmer to start building Widgets from
scratch. Most Widgets a programmer would need are shipped with Reahl -
so they can be used directly.

For example, Reahl ships with a Menu Widget. A Menu represents a
choice of options the user can follow to go to different possible
locations in the web application. Menus have simple behaviour: if the
user already is in the location where a particular option would lead,
that option is disabled (and visually indicated as such).

Other Widgets have much more sophisticated behaviour, such as Input
Widgets (discussed later).

Widgets can also contain children Widgets. This allows a programmer to
build a new custom Widget by combining existing Widgets into one.

This is a big deal, because building a Widget from scratch can be
difficult - but combining existing widgets is easy.

Some simple Widgets also mirror HTML elements. And these are so
simple, they make a good example for how a programmer would combine
Widgets into a new, more complex Widget.

.. code-block:: python

   class MyMessage(Div):
      def __init__(self, view):
          super(MyWidget, self).__init__(view)
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
other Widgets shipped with Reahl: Div and P.

Only the simplest of Widgets are like this one - it can render itself
to a browser as HTML.  More useful Widgets typically result in more
complex combinations of HTML, CSS, JavaScript and even dynamically
added server-side URLs and logic.

The whole point of the Reahl web framework, however, is to *not* have
to think about all that low-level implementation details and rather
think and code in terms of the required results instead.


What you have just gained
~~~~~~~~~~~~~~~~~~~~~~~~~

The concept of using Widgets to build user interfaces is certainly not
new - there are even several web frameworks that support this. But,
implementing Widgets on the web is difficult and web Widgets are often
limited in terms of what they can do. Reahl Widgets have no
limitations because the Reahl web framework was specifically built to
enable this concept of Widgets.  This means a wider and richer set of
Widgets for use in web applications.

Implementing anything on the web usually means that in addition to a
programming language, a programmer also needs to understand a wide
variety of technologies: HTML, CSS, JavaScript and often also various
configuration files in XML, some templating language and JavaScript
libraries.

In any one web application bits of code for all these various
technologies may lie scattered amongst several files and directories.

It is cumbersome to keep up with these technologies and the associated
techniques for getting some effects right. Even if a programmer
manages to build something using these technologies - there may still
be subtle issues with the result that the programmer is unaware of:
security issues, browser incompatibilities, inaccessible HTML and so
on.

Assuming a programmer gets all possible issues sorted out - on the
next web application (or sometimes next screen or new browser) the
same plans will have to be programmed from scratch again.

When writing a web application using Reahl, the programmer deals with
one language only: Python.  Almost all of the nasty web technologies
are hidden away.

The Widget concept in Reahl gives a programmer a lot. Widgets are
reusable and (with enough knowledge) a programmer can write any
conceivable Widget necessary. 

Once. And re-use it in many places.

And, when the programmer comes across a better way of implementing
that Widget (or to add features to it), then there's a single place to
go and change.  All existing locations where the changed Widget is
used will make use of this improvement with no extra effort.

Reahl also ships with a number of Widgets that can be used out of the
box. The shipped Reahl Widgets are carefully designed to:

 - make them accessible
 - make them search-engine friendly
 - make their look customisable with simple CSS; and
 - make them work on all major browsers

Reahl ships with very powerful Widgets representing things like
Inputs, Calendars, Tabs and more. Programmers new to Reahl can easily
combine these into complicated "windows". And, programmers who are
willing to learn more can build their own powerful Widgets.  There
literally is nothing visual on a web application that a programmer
cannot wrap into a Reahl Widget.



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

(All attributes of a EmailAndPasswordLoginCredentials instance are initialised when
created - just a convention we like to follow.)

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

Note that LoginForm needs a login_credentials domain object to be
passed to it upon construction.  The correct login_credentials
instance is thus to be supplied by the creator of the LoginForm.


What you have just gained
~~~~~~~~~~~~~~~~~~~~~~~~~

In the LoginForm example above, it is very simple to understand that
one can add a TextInput or PasswordInput to a Form. Almost equally
simple is the idea of an EmailField and a PasswordField.

These Widgets and Fields (all of which ship with Reahl) have
sophisticated behaviour when used together. With the short example
given, this behaviour is in place without a programmer having to lift
a finger more.

For example: Assume a user types something into the TextInput which is
not a valid email address.  As soon as the user leaves the input, an
error message will immediately be displayed via JavaScript on the
browser.  This error message will be very specific. The message will
be something like "Email should be a valid email address".  The
specific label "Email" will be used, because that is how the
programmer specified the label on the EmailField linked to the
Input. The TextInput further will check any input against a regular
expression for valid email addresses - because it was specifically an
EmailField that was linked to the TextInput.

When the error message appears, the Input Widget will also be
indicated visually as being in error.

The programmer did not code a single line of JavaScript or regular
expression to accomplish this.

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
that should be called when the Event is detected.  (There are more
interesting EventHandlers though...)

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


What you have just gained
~~~~~~~~~~~~~~~~~~~~~~~~~

Typically, a programmer would need to attend to a fair number of
things to be able to validate user input and execute server-side code
in response to user actions.  There's a long list of such potential
implementation details ranging from database transaction handling to
really human-unfriendly XML files somewhere (depending on the
framework).

A Reahl programmer can think in terms of *what* happens in the
application being built. Reahl takes care of *how* that is
implemented.  The code above is the only thing necessary - all in one
place, and simple to understand and read.

Notice also how an Event and the Widget's reaction to it are defined
separately from an actual Button.  This allows the programmer to
attach more than one Button to the same Event: Another small way to
write something once, and use it multiple times.  This feature comes
in handy in more complicated scenarios where multiple Widgets can set
off the same Event.

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

Reahl ships with predefined Widgets suitable for use as a main
window. The TwoColumnPage is one such Widget, which represents a page
with header area at the top, footer area at the bottom, and large
(main) and small (secondary) columns inbetween.

The main window is attached at the '/' URL. This means that it will
be the main window for all URLs visited underneath '/' as well.

This example application has two Views: one at '/' and another at
'/page2'. Each View has a title as specified (as the second argument
to define_view), but the Views are both empty apart from that.

Note that TwoColumnPage is smart enough to use the title of the
current View as the contents of the browser's title bar.


What you have just gained
~~~~~~~~~~~~~~~~~~~~~~~~~

Web applications present many different web pages to users. All of
these pages have important common elements. By developing one main
window per web application the programmer ensures that there is only
one place where these common elements are specified. That also means
one place to change if the main layout of the web application needs to
be changed.

However, the big deal here is that individual Views contain no
knowledge of the actual window they will be displayed in.

This means that a View can be developed and re-used in different web
applications that use entirely different main windows.

Reahl also ships with Widgets suitable for use as a main window - such
as the TwoColumnPage above.  When using these Widgets the main layout
of a web application's pages is already sorted out for the programmer.

This sort of layout of web pages is a tricky subject and difficult to
do in standards-compliant, accessible ways while catering for browser
incompatibilities.

By using something like TwoColumnPage the programmer in effect only
states what is needed. How that is accomplished is done by
TwoColumnPage.


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

           p1_slots={u'main': P.factory(text=u'This is page one')}
           self.define_view(u'/', title=u'Hello World', slot_definitions=p1_slots)

           p2_slots={u'main': P.factory(text=u'This is page two')}
           self.define_view(u'/page2', title=u'Page 2', slot_definitions=p2_slots)


Note how an extra parameter to the .define_view() method allows
one to specify a Factory for the Widget which should go into the Slot
named 'main' - in this case.  TwoColumnPage contains a number of Slots
for use of which 'main' is one.

Factory is a recurring theme in Reahl programming. Remember a web
application is viewed by many people at the same time. Thus, (for
example) different instances are needed of the same View (and thus the
Widgets it contains) for different people. This is why an actual
Widget is never created in .assemble() - the programmer only specifies
how Widgets of a View would be constructed by means of a Factory.
Such a Factory contains all information necessary to create the
Widget.

The same actually goes for the Views themselves and the Widget used as
a main window - albeit behind the scenes.

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
application. Regions can be packaged and shipped as separate entities.
And, Regions can be attached to your web application by literally
grafting the tree represented by the URLs of all Views contained in
the Region onto particular URLs of a web application.

For example: Lets assume that someone supplies a MagazineRegion -
intended to provide a place where users can peruse articles that form
part of a Magazine.

To the author of the Region, the Region may contain Views at '/' and
'/manage'. (Let's assume on '/' users would see a list of all articles
of the magazine, and on '/manage' special users are able to add more
articles etc.

If the programmer attaches the Region onto the URL '/reading' on a
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

Developing a Region is not much different from developing a
ReahlWebApplication. Here is an extract from a Region which allows
users to go through the process of registering on a web application.

.. code-block:: python

   class RegistrationRegion(Region):
       def assemble(self):
           register_slots={u'main_slot': RegisterWidget.factory()}
           self.define_view(u'/register', title=u'Register with us', slot_definitions=register_slots)

           congrats_slots={u'main_slot': CongratsWidget.factory()}
           self.define_view(u'/congrats', title=u'Congratulations', slot_definitions=congrats_slots)


What you have just gained
~~~~~~~~~~~~~~~~~~~~~~~~~

Simple examples would never be able to demonstrate the need for a
construct such as Region. Every programming language typically has an
analogous construct though - with the same goal:

A programmer needs the concept of a Region to be able to split a large
real world web application into smaller parts.  Added to that - such
smaller parts can be reused in totally different web applications.

In fact, Reahl includes a number of such re-usable Regions for common
functionality one would not want to be bothered with when developing a
new web application.  For instance, assume multiple users would need
to register and log into your web application.

You could opt to develop that functionality and the user interface
for it from scratch, or you could opt to just use a suitable Region
shipped with Reahl.

Web frameworks typically do not allow reuse on this level. Content
management systems have "plugins" that compare - but web frameworks do
not.  However, Content management systems typically do not have the
flexibility of a web framework.

Reahl gives you the best of both these worlds.


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
all those implementation details and learn to think in terms of a
level above those implementation details.

To get away from URLs, Reahl provides the concept of a Bookmark:

A Bookmark is a way to refer to a specific View. It also contains meta
information about the View, such as its title.  Bookmarks
transparently take care of Views that are relative.

To get a Bookmark for a specific View, a RegionFactory can be asked
for a Bookmark to that View using the .get_bookmark() method. Exactly
how this is done depends on the actual Region.

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
to look like that of their competition! Customers want the look of their
web applications to be customised to their own specifications.

For this reason, Reahl Widgets include very little CSS to govern their
look.  In addition to developing a web application, a programmer (or
better yet - a web designer) should also supply a CSS stylesheet.

This is the only bit of web technology that developers of Reahl are
directly exposed to.  And Reahl helps with this task: each type of
Widget has documentation stating how its look can be tailored using
CSS which will work on all major browsers.


Gaining more from Reahl
~~~~~~~~~~~~~~~~~~~~~~~

This document serves as an introduction to the Reahl web framework.

The Reahl web framework is different. Hopefully the reader would grasp
just what the Reahl web framework is after reading this introduction.
(Now is a good time to go and read the "Executive summary" to
double-check your understanding!)

There are many more aspects of Reahl which enables programmers to deal
with more and more advanced requirements.

These advanced topics are dealt with in further chapters.

    




