.. Copyright 2010, 2013 Reahl Software Services (Pty) Ltd. All rights reserved.
 
Implementation
--------------

The Reahl web server
~~~~~~~~~~~~~~~~~~~~

The Reahl web server implements the Reahl framework and the
abstraction it represents on the platform provided by the HTTP and
HTML standards.

To translate between the low-level standards and the HTTP standard the
web server implements some concepts as defined by the HTTP
standard:

According to the HTTP standard, each URL refers to a particular
Resource. In a webserver, each URL is thus mapped to a Resource, and
the Resource then handles the incoming Request, based on the Request's
HTTP method.

There are several kinds of Resources in Reahl.  One kind is a
ComposedPage.  A ComposedPage Resource is a Resource which can handle
HTTP GET requests - and it renders a page, based on the applicable
Window, with each correct Face rendered where its specified Slot is
located in the Window.

An URL may also refer to a StaticFileResource Resource.  A StaticFileResource is a
file which is sent verbatim back to the web browser, such as an image,
video, css of javascript file.

When an HTTP request is received by the webserver, it first determines
which Resource the request's URL is destined for.  This process
happens in several steps:

First, the the WebApplication is checked for all possible Window and
SlotSpecifications for all parts of the URL given.  From these a
RegionDefaults is constructed which contains the Window and
SlotSpecifications that are applicable to this URL.

Given such a RegionDefaults, a Region is then constructed.  A
Region contains the Window to be used and the actual Faces for each
Slot.  (The RegionDefaults contained only SlotSpecifications that
state which Face must be in which Slot; the Region contains the actual
Faces.)

Given the Region itself, the main Face for it can be
determined. Also, the URL can be split up into two parts: the part
denoting the Region, and the part denoting the relative URL in the
main Face.

Lastly, the main Face is asked for the actual Resource to be used,
given its relative URL.

It is thus the duty of the main Face to determine whether a particular
URL is indeed valid, and, if it is, to which Resource it maps.


If an URL maps directly to, say, an UrlBoundView, the Face would
return a ComposedPage Resource for that View.

But, the URL could also map to an image file, for example, that
relates to a ComposedPage.  Then a StaticFileResource Resource would be
returned.

Similarly, other types of Resources can exist "underneath" a Resource
such as a ComposedPage.



Dealing with server-side Events and Validation
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Events are only triggered in response to a user submitting a Form by
means of clicking on a button.

Forms are necessary holders of Inputs because they are the
infrastructure provided by HTML/HTTP to allow communication of Events
back to the server.

Each Form is linked to something called an RedirectAfterPost. An
RedirectAfterPost is a Resource which enables the server to receive
notifications that Events have been triggered on the browser. Its job
is to determine which Event has been triggered, deal with the data
associated with the Event, and hand the Event over to the Controller.

Since an RedirectAfterPost is a Resource, it has a URL which uniquely
identifies it.  When the Form is rendered, it is rendered so that it
will submit to its own RedirectAfterPost (its action attribute is set to
the URL of its RedirectAfterPost).

When a user clicks on a Button in a browser, the Form containing the
Button is thus submitted to the correct RedirectAfterPost.

Upon an HTTP POST method, the RedirectAfterPost first hands all input
received to its Form for validation.  During validation, the Form
instructs each Input to validate itself. Inputs in turn delegate this
duty to their Fields.  Fields, in turn, consult their Constraints to
be able to do the validation.

All validation errors are collected and stored in the database
together with the input supplied by the user.  The browser is
redirected back to the page where the Form was rendered originally.
This time the Form can be rendered with validation errors for each
field indicated next to its Input.

Should no validation errors occur, however, the Inputs are instructed
to set the marshaled input on the domain objects via their Fields.

Next, the RedirectAfterPost determines which Event has been triggered and
hands control over to the Controller to deal with the Event according
to specification.

If the Controller finds a suitable Transition for the Event and
current View, it will perform the Action of that Transition and
instruct the framework which next relative URL the browser should be
transitioned to.

In order to transition the browser, the HTTPSeeOther response code is
sent back to the browser, stating which URL the browser should load
next.


How widgets are rendered as HTML+JavaScript
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~


Client-side validation
~~~~~~~~~~~~~~~~~~~~~~

When rendered as HTML, Forms and their children Widgets are rendered
with the necessary javascript to ensure input will be validated on the
browser if javascript is enabled.  Similarly the exact same
Constraints used to generate such javascript is also used server-side
to additionally validate input on the server side.  (This is
necessary for many reasons. For example, a client could have its
javascript turned off, bypassing validations performed in
javascript. Or, because the client javascript interpreter is not under
your control, it may be malicious.)




