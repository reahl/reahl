



# If an uncaught error occurs, the user is sent to an error page that displays the message.
#  scenarios:
#    - where the view is defined by page= (ie, no page defined on the UI)
#    - where UserInterface.define_page() was called in its assemble() 
#    - where we explicitly call UserInterface.define_error_view()