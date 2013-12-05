.. Copyright 2009-2013 Reahl Software Services (Pty) Ltd. All rights reserved.
 

Reahl - an introduction
-----------------------

Reahl is a framework for building server applications. Reahl also
includes a web framework for building web applications.

The Reahl server framework makes it possible to build various kinds of
reusable components and deal intelligently with, for example:

 - configuration;
 - packaging and distribution of components;
 - the dependencies between components;
 - versioning of components; and
 - migrating database schemas when you upgrade.

Reahl also ships with a number of ready-built components so that you
do not need to start writing every server system from scratch.  (For
example, almost every server system needs concepts such as UserAccounts
for Parties with different Roles that give them access to different
capabilities in the system.)

The Reahl web framework is built on top of this infrastructure and is
also geared for reusability and ease of programming. 

It is relatively easy to build a simple webapp for tutorial
purposes with most web frameworks. However such examples lack many
features that complicate a real world webapp.

The Reahl web framework aims to make a full-blown real world webapp
easy to build, and as such introduces all kinds of concepts that do
not exist in other frameworks - and that takes some learning
initially.

This narrative introduces the Reahl web framework.


The Reahl web framework
~~~~~~~~~~~~~~~~~~~~~~~

The Reahl web framework differs from typical web frameworks in
that it allows one to build web user interslot_contents in one programming
language (currently Python). 

The Reahl programmer builds webapps using Widgets similar to Widgets
one may find in GUI programming toolkits. From this Python code, Reahl
serves web sites composed of standard, accessible HTML, CSS and
Javascript.

The Reahl web framework thus hides a lot of irrelevant details of the
underlying web platform from the programmer. Instead it presents a
neat set of higher-level concepts that are actually relevant to the
programming task at hand.

These higher-level concepts are designed to take into account things
like validation of input, internationalisation, and the security
checks and access control needed for different users of the site.

The Reahl web framework is also geared for building chunks of user
interface that can be re-used in different webapps.



The basics of a Reahl webapp
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

In order to cater for re-usability, a Reahl webapp is constructed
somewhat differently to the typical framework out there.

A Reahl WebApplication has a Window: a web page which contains all the
elements expected to be on every page of the site. For example: a
navigation bar, header and footer.

The Window is incomplete, however. It contains Slots: named
placeholders that can be filled with different content for each
individual page.

A Face is a container for the chunk of web page which should fill a
Slot.

A Reahl programmer develops a number of web pages solely in terms of
which Faces are to be present on each page, and the content of the
Faces - without any knowledge of what the actual surrounding Window
would contain.

This makes it possible to plug whatever has been programmed into many
different webapps with different Windows. 

Such a collection of web pages, written in terms of relevant Faces, is
called a Region.

To assemble an entire web site, a programmer assemblees a Window and one
or more Regions to specific URLs on the site:

.. code-block:: python

   class MySite(ReahlWebApplication):
       def assemble(self):
           my_region_specification = RegionSpecification(MyRegion, u'my_region')
           self.attach_main_window(u'/', MyPage, {})
           self.attach_region(u'/', my_region_specification, {u'main_slot': u'main'})


In the code above, a ReahlWebApplication is created by writing a class which
inherits from ReahlWebApplication.  The site is set up in its 'assemble' method.

MyPage is assembleed as a Window at the root URL of the site ('/').
This means that it will be used as Window for all URLs underneath
'/' in the URL hierarchy as well.

Furthermore, MyRegion is assembleed to a particular URL - in this case
also the root URL of the site. This means that URLs of the WebApplication
underneath '/' will be interpreted by the Region assembleed there.

In the case of MySite, the entire WebApplication thus consists of only one
Region. Real world WebApplications would consist of more than one Region,
assembleed in different places.

When programming a Region, its programmer decides the names of the
Slots the Region will use, independently of which Windows the Region
may be used with.

The Windows the Region are used with may or may not have similarly
named Slots. Hence the programmer also needs to specify which Slot of
the Region is patched into which Slot of the Window when assembleing a
Region.  In this example, what the Region calls 'main_slot' is plugged
into what the Window calls 'main'.




Widgets: the cornerstone of the UI
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

One of the goals of the Reahl web framework is to enable a programmer
to express a web application using a single programming language.

Core to the this aim is the concept of a Widget.

A Widget is a Python class which represents a user interface element.
An example of a Widget is a Menu. A Menu can render itself as HTML for
display by a web browser.

If a Menu is part of the Window of a site, the same Menu will be
displayed on each web page of the site. However, a Menu can display
itself differently depending on, for example, which web page is being
displayed. In the case of a Menu, it may render slightly different
HTML to indicate visually which of its items are currently active.

Some Widgets hide sophisticated behaviour behind this simple
usage. For example, an EmailInput Widget will ensure - using
JavaScript in the browser - that the user actually inputs a valid
email address. If not, it will display an appropriate error
message. But the same checks will also happen on the server side, in
case the client has disabled JavaScript, or if the client JavaScript
engine cannot be trusted.

All of this sophisticated behaviour happens without the programmer
having to do anything except decide to use an EmailInput Widget.

Reahl ships with a number of such Widgets which have been carefully
built for the programmer just to use. An example illustrates the
importance of this fine grained re-use:

Web designers will always have new tricks to be able to accomplish
certain things not catered for by standard HTML. For a long time one
such trick was to be able to have an input that could fit into a
visual space too small to also include a label for the input.  To save
space, designers display the label of the input inside the input -
where a user would type the actual input. When the user clicks inside
the input to start typing, the label would disappear.

Doing this well requires a fair amount of web design knowledge, the
right HTML, the right CSS and the right JavaScript.  (See:
http://www.alistapart.com/articles/makingcompactformsmoreaccessible )

A Reahl programmer only needs to use the LabelOverInput Widget and all
is taken care of. 

This is one example of how a Reahl programmer has less to understand
and maintain.


A simple Window
~~~~~~~~~~~~~~~~~

A Window is the visual framework all pages of the web site will
share. It is almost analogous to the window of a GUI program. 

Anything visual in Reahl is built by composing a complex Widget from
simpler ones. The core Widget class in Reahl is a Widget which will
render itself as absolutely nothing by default. But, it (like any
Widget) may have one or more children Widgets, and rendering the
parent Widget will also render its children Widgets.

Complex Widgets can thus be composed by adding children Widgets to
them.

This is also how one can create a Widget which the webapp can use as
Window:

.. code-block:: python

   class MyPage(HTML5Page):
      def __init__(self, face):
          super(MyPage, self).__init__(face)
          self.add_child(MyMenu(face))
          self.add_child(Slot(u'main'))

The HTML5Page Widget ships with Reahl and represents an empty page. It
includes all sorts of non-visual things like dynamically included
JavaScript and CSS to enable Reahl Widgets.

A Slot is also just a special-purpose Widget and it can be added as a
child Widget like any other.

Thus, assembleing a Window on a web site using the MyPage Widget
means that all pages of the web site will be HTML5 pages with the same
Menu, followed by a single Slot, called 'main'.

Note that the Window itself is a concept hidden from the
programmer. The programmer merely supplies the Widget used to
represent the Window visually.


Regions: chunks of half-specified webapps
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Each Region is a bit like a mini-webapp, but with some important
differences. These differences ensure that Regions can be re-used in
different webapps.

A Region contains a number of different "pages", each referred to by
an URL. Each "page" of a Region is called a View. 

The important differences between the Views of a Region and pages of 
a webapp are that:
 - A Region's URLs are relative to the Region, regardless of where the
   Region may be assembleed on a site; and
 - Views are not complete HTML pages as would be expected for a 
   WebApplication - a View is collection of Faces.

To understand the relative URLs, let's assume that MyRegion contains
two Views, one with relative URL '/one' and another with relative URL
'/two'. Since MyRegion is assembleed to the root URL of MySite, the
WebApplication's '/one' URL would result in the relevant View of MyRegion.

We could have assembleed MyRegion somewhere else in the URL hierarchy of
the WebApplication. Consider the following alternative:

.. code-block:: python

   self.attach_region(u'/abc', my_region_specification, {u'main_slot': u'main'})

If that was the case, the View would be found at the URL '/abc/one' on
the WebApplication instead.

Relative URLs are one part of the story. The other is that a View is
not a complete HTML page. If it were complete, it would not be
re-usable between different sites with different visual structure.

Each View needs to supply only a statement of which Faces it needs in
which Slots of its Slots.  When fused with a particular Window, the
webapp has all the information it needs to create its pages.


Programming a Region
~~~~~~~~~~~~~~~~~~~~

Each Region is written as a Python class. This class can supply
a method called 'assemble'.  In this method, the Region creates
its Views:

.. code-block:: python

   class MyRegion(Region):
       def assemble(self):
           one_page = UrlBoundView(self, u'/one', _(u'This as page one'), 
                                  {u'main_slot': Face.for_widget(OneWidget)})
           other_page = UrlBoundView(self, u'/two', _(u'This is page two'), 
                                    {u'main_slot': Face.for_widget(TwoWidget)})
           self.define_view_instances([one_page, other_page])


When each View is created, it should be passed a dictionary which
contains all the Slot names it defines, and how each name maps to a
Face class. In the simple case of MyRegion the View only has one Face,
but that need not be the case.

The View is also passed its own title, and in the simplest case, its
URL (relative to its Region, of course).

The Face.for_widget method automatically creates a new Face class
which will have as contents a single Widget of the Widget class
requested.

Note that the actual Faces and Widgets are not constructed at this
point. The View only keeps track of which type of Face it will need.

Using that information, the Reahl framework will create the Faces and
Widgets if and when necessary.


Dealing with user input: data
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Some Widgets are specifically designed not only for display but also to
receive input from a user.  These are called Inputs. Input Widgets can
only be used as the children Widgets of a Form Widget.

In a typical application, there would be objects that model the
problem domain of the system. Things like Person, Order, or
EmailAndPasswordLoginCredentials. These sorts of objects are called domain objects to
distinguish them from all the very user-interface specific objects
mostly dealt with by a web framework.

The purpose of an Input is to display values of domain objects on a
web page, and to allow a user to change those values and otherwise
interact with the domain objects.

To be able to display or change data, Inputs are linked to these
domain objects using Fields.

A Field provides extra information about the data held by some
attribute on some domain object, and this description is used by the
Reahl framework to accomplish all sorts of things.

Each Input Widget is linked to a Field. It uses the field to render
its own label and to validate what the user types in the input.

The Field can also be used to marshal user input (which comes in as a
unicode string) into a programming language object, such as to an
Integer or Date object. 

Let's say MyWebApplication needs its users to log in on the webapp. We can
model such logins by the EmailAndPasswordLoginCredentials class:

.. code-block:: python

    class EmailAndPasswordLoginCredentials(object):
        def __init__(self):
	    self.email = None
	    self.password = None

	def log_in(self):
	    pass # Let's ignore the implementation details of this for now..

(All attributes of a EmailAndPasswordLoginCredentials are initialised to None
when created - just a convention we like to follow.)

This class can be augmented with Fields as follows:

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


To understand what Fields can do for a Domain object, consider what a
programmer would be able to do with the class above:

.. code-block:: python

    login = EmailAndPasswordLoginCredentials()
    print login.fields.email.label                     # prints 'Email'
    print login.fields.email.required                  # prints True
    print login.email                                  # prints None
    login.fields.email.from_input(u'someone@home.org')
    print login.email                                  # prints <EmailAddress(someone@home.org)>

Not that a programmer ever would need to do any of that... but the
Reahl web framework does.  And to enable the Reahl web framework to
have such access to Fields, a programmer must always pass a Field to
an Input Widget upon creation:

.. code-block:: python

    class LoginForm(Form):
        def __init__(self, face, event_channel_name):
            super(LoginForm, self).__init__(face, event_channel_name)

	    login_credentials = self.region.login_credentials
            self.add_child(TextInput(self, login_credentials.fields.email))
	    self.add_child(PasswordInput(self, login_credentials.fields.password))

Note that LoginForm is programmed to expect a .login_credentials domain
object on its Region.  It is standard practice in Reahl programming to
store domain objects on the current Region because they are shared
between the different Widgets and possibly Faces on a Region.  The
next section will make that clearer.


Dealing with user input: interaction
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Our LoginForm example is not very useful at this stage, because it
contains no Buttons which the user could click to actually log in.

Buttons are special because several things need to happen when a user
clicks on a Button: First, the input typed by the user must be
validated. Then, some action should happen on the server side which
presumably uses that input. After this (and assuming all went well),
the browser needs to be redirected to some (possibly different) web
page to show the results.

.. note::
   To the impatient: yes, of course, Widgets that make use of Ajax do
   things differently. However - they are still linked to Fields as
   and Events described here.

In relatively complex webapps dealing with such interaction makes the
code of the webapp hard to follow. A programmer struggles to clearly
see the network of how user interactions cause transitions between web
pages.

The Reahl web framework deals with this spaghetti-problem by
associating each Region with a Controller.  It is the responsibility
of the Controlelr to determine how the system should react to a
particular Event.

The Region Controller in turn implements a finite state machine which
models the dialogue between the user and the system:

Each View in the Region is seen as a state: the coarse-grained state
of the user interface at a possible instance in time.  Each Button the
user can click is linked to a named Event. The system reacts to Events
differently, depending on which the current View is.

For example: if the user is on the LoginView, and the user triggers
the 'log_in' Event, the system should log the user in and then perhaps
transition the browser to the WelcomeView.

Triggering the 'log_in' Event is clearly not allowed while in
WelcomeView - it would not make sense.

From such detail, one can draw a diagram showing how a user could be
transitioned between different Views, depending on all possible
allowed Events the user can trigger in the many different Views.


An example shows how this diagram is programmed in Reahl:

.. code-block:: python

   class MyRegion(Region):
       def assemble(self):
           self.login_credentials = EmailAndPasswordLoginCredentials()

           login_page = UrlBoundView(self, u'/login', _(u'Log in please'), 
                                     {u'main_slot': Face.for_widget(LoginForm)})
           welcome_page = UrlBoundView(self, u'/welcome', _(u'Welcome'), 
                                       {u'main_slot': Face.for_widget(WelcomeWidget)})
           self.define_view_instances([login_page, welcome_page])

	   self.define_transition(Event(u'log_in'), login_page, welcome_page, 
                               action=self.login_credentials.log_in)


Here, define_transition specified that when the 'log_in' Event happens
while in the login_page View, the method self.login_credentials.log_in
should be called, and then the browser should be transitioned to the
welcome_page.

The rest of the puzzle is simply the addition of the Button Widget on
the LoginForm:

.. code-block:: python

    class LoginForm(Form):
        def __init__(self, face, event_channel_name):
            super(LoginForm, self).__init__(face, event_channel_name)

	    login_credentials = self.region.login_credentials
            self.add_child(TextInput(self, login_credentials.fields.email))
	    self.add_child(PasswordInput(self, login_credentials.fields.password))
	    self.add_child(Button(self, self.get_event_named(u'login_event'), u'Log in'))

Note how all Input Widgets are always created with their Form as first
argument.  Buttons are created also with reference to the Event the
Button should trigger when clicked and its label.


Some loose concepts
~~~~~~~~~~~~~~~~~~~

For no other reason, but to be able to write out the complete example
used so far, a few more concepts need to be explained.

The first is that of a Bookmark.  Remember Regions are programmed without
knowledge of where they will be assembleed in future webapps. This also
means that they cannot hard-code URLs in links. Instead wherever one
needs to link to a particular View of a Region, a Bookmark should be
used.

Bookmarks are obtained by asking for a bookmark from a
RegionSpecification for an URL relative to that Region:

.. code-block:: python

   my_region_specification = RegionSpecification(MyRegion, u'my_region')
   bookmark = my_region_specification.get_bookmark(relative_path=u'log_in')

Bookmarks are relevant in MySite, because it includes a Menu and Menus
are constructed from a list of Bookmarks.

In fact, in the example, a seperate MyMenu class is not even
necessary. Inside the constructor of MyPage, one could do something
like this instead:

.. code-block:: python

   my_menu = Menu.from_bookmarks(bookmarks)
   self.add_child(my_menu)

The only trouble is that to be able to get those bookmarks, one would
need access to my_region_specification.  And that leads to the next
missing concept: Region and Window arguments.

For real world webapps, it is often necessary to be able to specify a
Region with arguments - so that any Widget can easily access arbitrary
information specific to a particular Region.  This mechanism can be
used to give access to my_region_specification from within MyPage.

First, my_region_specification needs to be passed as a keyword
argument when assembleing the Window:

.. code-block:: python

   my_region_specification = RegionSpecification(MyRegion, u'my_region')
   self.attach_main_window(u'/', MyPage, {}, my_region_spec=my_region_specification)

The keyword argument may be named anything. But, the Widget using it
needs to know what it was named.  With the argument as in the example
above, MyPage can get to it as follows:

.. code-block:: python

   my_region_spec = self.region.kwargs[u'my_region_spec']
   bookmarks = [my_region_spec.get_bookmark(relative_path=u'/login'),
                my_region_spec.get_bookmark(relative_path=u'/welcome')]
   my_menu = Menu.from_bookmarks(bookmarks)
   self.add_child(my_menu)

Note how arguments specified for the Window are accessed from the
Widget's self.region.  The Window has its own Region, used by all
Widgets in the Window.  Arguments can be passed to any
RegionSpecification in a similar way.

With this code, our Menu will result in a navigation bar with links to
the login and welcome Views, respectively.  (It is not very useful
to include the welcome view in a navigation bar - but at this stage
those are all the Views we have to be able to show off a Menu of sorts.)


Complete example
~~~~~~~~~~~~~~~~

Below then, is a complete example of everything explained so far:

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


    class LoginForm(Form):
        def __init__(self, face, event_channel_name):
            super(LoginForm, self).__init__(face, event_channel_name)

	    login_credentials = self.region.login_credentials
            self.add_child(TextInput(self, login_credentials.fields.email))
	    self.add_child(PasswordInput(self, login_credentials.fields.password))
	    self.add_child(Button(self, self.get_event_named(u'login_event'), u'Log in'))


    class WelcomeWidget(Widget):
        def __init__(self, face):
	    self.add_child(P(face, text=u'Welcome to the site, you have logged in'))


    class MyRegion(Region):
        def assemble(self):
            self.login_credentials = EmailAndPasswordLoginCredentials()

            login_page = UrlBoundView(self, u'/login', _(u'Log in please'), 
                                      {u'main_slot': Face.for_widget(LoginForm)})
            welcome_page = UrlBoundView(self, u'/welcome', _(u'Welcome'), 
                                        {u'main_slot': Face.for_widget(WelcomeWidget)})
            self.define_view_instances([login_page, welcome_page])

	    self.define_transition(Event(u'log_in'), login_page, welcome_page, 
                                action=self.login_credentials.log_in)


    class MyPage(HTML5Page):
       def __init__(self, face):
           super(MyPage, self).__init__(face)
	   my_region_spec = self.region.kwargs[u'my_region_spec']
	   bookmarks = [my_region_spec.get_bookmark(relative_path=u'log_in'),
	                my_region_spec.get_bookmark(relative_path=u'welcome')]
	   my_menu = HMenu.from_bookmarks(bookmarks)
           self.add_child(my_menu)
           self.add_child(Slot(u'main'))


    class MySite(ReahlWebApplication):
        def assemble(self):
            my_region_specification = RegionSpecification(MyRegion, u'my_region')
            self.attach_main_window(u'/', MyPage, {}, my_region_spec=my_region_specification)
            self.attach_region(u'/', my_region_specification, {u'main_slot': u'main'})



View Preconditions
~~~~~~~~~~~~~~~~~~

One difference between the Region Controller and other finite state
machines is that its current state (current View) is not 100% in its
own control.  Each time the user enters a URL in a browser, the user
forces the current state to be the View associated with that new URL.
The same thing happens if a user clicks on a link or requests the
browser to go to a bookmarked URL. Using links and URLs a user can
jump between different "places" in the webapp, thus transitioning
from any particular View in one Face to any View in another.

This freedom the user has can cause problems: It may be that a View is
bookmarked which is not valid according to the Controller.  For
example, a page on which you can log in is not a valid View if you
are already logged in.

To deal with such anomalies certain Preconditions are checked for the
requested View, on each request to view a page.  Such Preconditions may
be added to Views by a programmer.  Each Precondition is associated
with a particular action that should be taken to remedy the situation.
Currently two such actions exist: Redirect and Detour.

For example, if you are logged in, but visit /login, its Precondition
could Redirect the browser to /logoutfirst instead.

A Redirect merely redirects the browser to another View.  A Detour
does the same, but its adds to that behaviour.  A Detour redirects the
user to another page, or number of pages with the idea that after the
user completed some steps there, the user should be returned to a
specific place (possibly from where the Detour started).

For example: say a user wants to add a beneficiary on an online
banking application.  The bank may require that a "one time pin" sent
to the user's cellphone be entered before this action is allowed - but
only if the user has not done so already in the past 5 minutes.

At the /addBeneficiary page, a Detour can be added to /enterOneTimePin
which will be triggered only if a one time pin has not been entered in
the last 5 minutes.  Assuming the user visits /assBeneficiary and the
Detour is triggered, the user will be redirected to
/enterOneTimePin. On that View, upon entering the pin the browser will
be returned to /addBeneficiary so that the user can continue with the
intended task.

Here's how a Detour could be incorporated into the simple login
example:

.. code-block:: python

   class MyRegion(Region):
       def assemble(self):
           self.login_credentials = EmailAndPasswordLoginCredentials()

           login_page = UrlBoundView(self, u'/login', _(u'Log in please'), 
                                     {u'main_slot': Face.for_widget(LoginForm)})
           welcome_page = UrlBoundView(self, u'/welcome', _(u'Welcome'), 
                                       {u'main_slot': Face.for_widget(WelcomeWidget)})
           logoutfirst_page = UrlBoundView(self, u'/logoutfirst', _(u'Log out please'), 
                                           {u'main_slot': Face.for_widget(LogoutFirstForm)})
           self.define_view_instances([login_page, welcome_page, logoutfirst_page])

           is_logged_out = Precondition(lambda: not self.web_session.is_logged_in(),
                                        Detour(logoutfirst_page, login_page))
           login_page.add_precondition(is_logged_out)

	   self.define_transition(Event(u'log_in'), login_page, welcome_page, 
                               action=self.login_credentials.log_in)


The effect of adding is_logged_out to the login_page above is that,
should the user currently be logged in, but visit /login, the browser
will immediately be redirected to /logoutfirst. Then, after completing
actions there (perhaps as simple as clicking on a "Logout" Button),
the browser will be redirected back to /login.


----------------------------------------

        













Managing the appearance and behaviour of a Face
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Faces are designed to be re-usable in different WebApps or different
Regions or Slots in a WebApp.  The code for a Face is thus totally
agnostic to the context in which it will be used.

Just like a webapp can have different pages, a Face can also present
different Views of itself to the user, depending on various
Conditions.

Each Face has a Controller. The Face uses its Controller in order to
determine which View should be displayed to the user (in other words,
to determine which View is the current View of the Face).

UrlBoundViews are Views which are linked to URLs that are interpreted
as being relative to the Face regardless of where the Face appears on
the site. Just like a browser has a current URL, each Face maintains
its own current relative URL.

If a Face has UrlBoundViews, its current View would be the
UrlBoundView matching its current relative URL.

However, a Controller could determine the current View for its Face
regardless of the current relative URL of the Face.  This decision
could be based on an arbitrary Condition.  For example, the Controller
may choose between two Views depending on whether the current user is
authenticated or not.

A programmer starts building a Face by configuring its Controller.
This means, specifying the Views and the Conditions to be used to
decide which View is the current View.

Controlling the system response upon the ocurrence of user-initiated
events is also the job of the Controller.

To do this, the Controller implements a finite state machine which
models the dialogue between the user and the system. In this FSM,
Views act as states. 

To specify behaviour, the programmer can add Transitions to the
Controller.  Each Transition states how the system should react if its
associated Event happens, while on a particular View. The system
reacts by (a) performing some method call (called an action), and (b)
by transitioning the Face to a (possibly) different View.

In a typical cycle, a user would request a particular web page using a
browser. On this page, a Face would first display one of its Views to
the user. Then, the user would trigger an Event by, eg, clicking on a
displayed Button (more on Events later). The triggered Event is
received by the Controller - and the Controller determines which
Transition to follow given the current View, the specific Event
triggered, and possible other Conditions. It then performs the action
of the chosen Transition, and changes the Face to the next View as
specified by the Transition.

A Face can also be associated with domain objects: programming
language objects representing the problem domain.

The action of a Transition is typically a method called on one of the
domain objects of the Face.

The Face thus implements the model-view-controller design pattern.  It
has domain objects (the model), a Controller, and Views.

To the Controller each View is a state in a finite state machine which
models the valid language the user can use to communicate with the
system.  The Controller is set up with Transitions and Events like any
finite state machine. It uses this information to determine what to do
upon the occurrence of an Event, and how to transition the Face from
one View to another.




What the browser's URL means
~~~~~~~~~~~~~~~~~~~~~~~~~~~~


Composing a View with re-usable Widgets
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Each View of a Face has a main Widget.  The main Widget of a Face in
turn is defined as being the main Widget of the current View of the
Face.

To render a Face for inclusion in the HTML rendition of a Window,
the Face's main Widget is rendered. The main Widget is really the root
of a whole Widget hierarchy which can be rendered as HTML so that the
user can see and interact with the Widgets.


How Widgets are linked to the domain
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~


To be able to validate input supplied by the user, Constraints can be
added to a Field.  There are many different Constraints, for example:
RequiredConstraint makes it mandatory for the user to give a value for
that field (ie, where this Field is linked to a Widget the user will
not be allowed to supply an empty value). Another example is the
MinLengthConstraint which ensures that the input string supplied by
the user is longer than a minimum number of characters.

Inputs are Widgets specifically tailored to get input from a
user. Widgets and Inputs are user-interface-level infrastructure:
their responsibility is to render a display to the user and receive
user input.

Fields and Constraints are domain-level infrastructure. They provide
metadata and logic about the domain-level concepts regardless of how
these concepts will be displayed.

Fields and Constraints are linked to Widgets and Inputs to be able to
display data on the web, get input from a remote user and validate
and marshal such input.

A Form is a widget corresponding to an HTML Form. It can have Widgets
as children, some of which can be Inputs.  Each Input Widget holds
onto to a particular Field which in turn is linked to a particular
attribute of a domain object.  The Input uses the Field to validate
its input and to marshal between unicode input/output vs the python
object such input represents.

The Input elements in a Form correspond to Fields, and when the form
is submitted, their input will be dealt with by their Fields.
Similarly, Buttons are Widgets that are associated with server-side
Events.  Events are domain-level concepts like Fields, but they have a
different purpose: the server needs to react if an Event
occurs. 

As explained before, the Controller of the relevant Face determines
exactly how the server reacts to the firing of an Event.



The UserSession
~~~~~~~~~~~~~~~

In a multi-user, server based system there is the concept of a
UserSession.  A UserSession keeps track of who the current user is,
whether this person is logged on, how long the user has been logged in
for, etc.

On the web, for example, many frameworks keep track of the user's
"session data" and each framework has some way of doing this. It
enables the server to relate subsequent HTTP requests to one sitting
as it were.  However, the idea of a UserSession can apply to a non
web-based server or even standalone program as well.

In Reahl, the programmer need not be aware of such low-level
concepts.  Reahl automatically maintains a UserSession, but the
programmer only expresses code in terms of Faces, Widgets, Events,
etc.  The Reahl framework takes care of implementing these
higher-level concepts in terms of the underlying technology.

Knowledge of the UserSession is useful, however.  It can be used to
log a user into the system. Reahl has two levels of authentication: a
user may be merely authenticated or securely authenticated.  The first
level of authentication means that a user has logged in somehow, but
that we cannot trust the communication channels to the user. These
channels may be prone to man-in-the-middle attacks and to those
listening in.  When the user's session is also secure, it means that
we can be sure that the communication is safe.
