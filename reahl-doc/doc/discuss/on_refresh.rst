# TODO

Why do I need a persisted object to back input and other values on a refreshable widget?
========================================================================================

Because, after our (1) cycle upon post, the on_refresh action is executed and may change data.
Then, the Widget is constructed again in (2), with the intension to use this newly changed data
and possibly render differently. If the data is not persisted, the changes made during (2) will
be lost by the time we recreate the widget for (2).

Why does enable_refresh also call the on_refresh Action?
========================================================

When you refresh a Widget via ajax, the refresh action is executed, so that the Widget can
be rendered based on the data that was possibly changed during the refresh action.

This state, however, is rolled back in the database because an ajax action like that is only
meant to temporarily update the screen. Only when the user clicks on a button, and hence submits
the final result of all ajax interactions should the database state be retained.

However, since the state after each ajax on_refresh action has been aborted, each such calculation
needs to be re-done when the widget is reconstructed upon a submit. When submitting, the state of all
input values chosen as a result of ajax interactions is used to construct the widget - BUT recalculation
is necessary based on these "new" (from a database state perspective) inputs. It may very well be that the
rest of the Widget's construction can be different based on such calculation.