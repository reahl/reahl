.. Copyright 2016 Reahl Software Services (Pty) Ltd. All rights reserved.

How Bootstrap-based Widgets and Layouts differ from previous versions
=====================================================================

This section is intended as a quick reference for someone who knows
the previous Widgets and Layouts and who needs to figure out how to
map an older tool to its Bootstrap equivalent.

If that's not you, you can safely skip to :doc:`forms`.


The :mod:`reahl.web.bootstrap` package contains Layouts and
Widgets equivalent to all of the Widgets previously supported. The new
Widgets essentially do similar tasks but may look and behave
differently to previous counterparts. In many cases the Widgets also
have a different programming interface and the means by which their
layout is controlled may also be different.

Below follows a more detailed breakdown of changes.

Basic Widgets
-------------

Widgets representing HTML or simple Inputs (but styled with Bootstrap)
are located in :mod:`reahl.web.bootstrap.ui`\.

The following changes happened here:

    - Before, an Input automatically displayed an error message below 
      itself if it contained invalid input. Bootstrap versions do not.
      Depending on where they are used (via another Widget or a Layout)
      how and where error messages are displayed can differ, hence the
      Input cannot determine this by itself any longer.

    - The :mod:`~reahl.web.bootstrap.ui` module now only contains Widgets corresponding to similar
      basic HTML elements. Fancier Widgets are split out into separate modules.

    - Widgets that dealt with Layout of Forms, such as
      :class:`reahl.web.ui.LabelledBlockInput` and
      :class:`reahl.web.ui.LabelledInlineInput` have been
      axed. Instead, when using Bootstrap the layout of Forms are
      controlled using the new
      :class:`~reahl.web.bootstrap.ui.FormLayout` and its subclasses:

         - :class:`~reahl.web.bootstrap.ui.FormLayout`
         - :class:`~reahl.web.bootstrap.ui.GridFormLayout`
         - :class:`~reahl.web.bootstrap.ui.InlineFormLayout`

    - Other Layouts have been added for these basic Widgets:
         - :class:`~reahl.web.bootstrap.ui.ButtonLayout` 
	    (for :class:`~reahl.web.bootstrap.ui.Button` or
	    :class:`~reahl.web.bootstrap.ui.A`).
         - :class:`~reahl.web.bootstrap.ui.ChoicesLayout`
	    (for :class:`~reahl.web.bootstrap.ui.PrimitiveCheckboxInput` or
	    :class:`~reahl.web.bootstrap.ui.PrimitiveRadioButtonInput`).
            TODO: perhaps nuke this? At any rate it is not meant for user consumption
         - :class:`~reahl.web.bootstrap.ui.TableLayout`
	    (for :class:`~reahl.web.bootstrap.ui.Table`)

     - Some other Widgets that attempted to deal with styling, or that 
       were mere aliases for HTML elements were removed:
         - :class:`~reahl.web.ui.InputGroup`
         - :class:`~reahl.web.ui.PriorityGroup`
         - :class:`~reahl.web.ui.Panel`
         - :class:`~reahl.web.ui.ErrorLabel`
         - :class:`~reahl.web.ui.LabelOverInput`

     - Instead of a SimpleFileInput, there are two simple kinds of 
       file input:
         - :class:`~reahl.web.bootstrap.ui.FileInputButton`
            (just a button which behaves like a file input)
         - :class:`~reahl.web.bootstrap.ui.FileInput`
            (a stylized version of a standard browser file input)

     - CheckboxInput has been split into two versions:
         - :class:`~reahl.web.bootstrap.ui.PrimitiveCheckboxInput`
	    (just a checkbox)
         - :class:`~reahl.web.bootstrap.ui.CheckboxInput`
	    (a checkbox wrapped in a label)

     - SingleRadioButton has been renamed/split as follows:
         - :class:`~reahl.web.bootstrap.ui.PrimitiveRadioButtonInput`
	    (just a single dot, meant for use in the implementation 
	     of :class:`~reahl.web.bootstrap.ui.RadioButtonInput`)
         - :class:`~reahl.web.bootstrap.ui.RadioButtonInput`
	    (just like the previous :class:`~reahl.web.ui.RadioButtonInput`)

     
List of equivalent Widgets
--------------------------

  Aside from the basic Widgets above, here is a list of old Widgets,
  and what the Bootstrap equivalent is.  The old versions of these
  Widgets will disappear in Reahl 4.0:

  ============================================  ======================================================
   Old version                                   Bootstrap version
  ============================================  ======================================================
   :class:`reahl.web.ui.FileUploadInput`        :class:`reahl.web.bootstrap.files.FileUploadInput` 
   :class:`reahl.web.ui.SlidingPanel`           :class:`reahl.web.bootstrap.carousel.Carousel` 
   :class:`reahl.web.ui.TabbedPanel`            :class:`reahl.web.bootstrap.tabbedpanel.TabbedPanel` 
   :class:`reahl.web.ui.Menu`                   :class:`reahl.web.bootstrap.navs.Nav` (and related classes) 
   :class:`reahl.web.ui.CueInput`               :class:`reahl.web.bootstrap.ui.CueInput` | TODO: to be moved out of ui
   :class:`reahl.web.ui.ErrorFeedbackMessage`   :class:`reahl.web.bootstrap.ui.Alert` | TODO: needs to be moved
   :class:`reahl.web.ui.PopupA`                 :class:`reahl.web.bootstrap.popups.PopupA` (works differently) 
   :mod:`reahl.web.datatable`                   :mod:`reahl.web.bootstrap.datatable` 
   :mod:`reahl.web.layout`                      :mod:`reahl.web.bootstrap.grid` 
   :mod:`reahl.web.pager`                       :mod:`reahl.web.bootstrap.pagination` 
  ============================================  ======================================================

Page layout
-----------

In Reahl 3.1, :class:`reahl.web.pure.PageColumnLayout` was used to
create a page with several columns. In Reahl 3.2 the same results can
be achieved by using a :class:`reahl.web.layout.PageLayout` that uses
a :class:`reahl.web.pure.ColumnLayout` for its contents area.

This new arrangement works for the Bootstrap versions as well, but
with :class:`reahl.web.pure.ColumnLayout` used instead of
:class:`reahl.web.pure.ColumnLayout`.

Bootstrap's :class:`reahl.web.bootstrap.grid.ResponsiveSize` works
differently to Pure's :class:`reahl.web.pure.UnitSize`: with Pure, you
could state sizes as fractions, eg '1/2'. Bootstrap sizes are
stated as integers and their meaning is always "how many 1/12ths". Ie:
1 is 1/12th, 6 is 6/12ths and so on.

  ============================================  ======================================================
   Old version                                   Bootstrap version
  ============================================  ======================================================
   :class:`reahl.web.pure.PageColumnLayout`     Deprecated. Use :class:`reahl.web.layout.PageLayout` instead

   :class:`reahl.web.layout.PageLayout`         :class:`reahl.web.layout.PageLayout`
   :class:`reahl.web.pure.ColumnLayout`         :class:`reahl.web.bootstrap.ColumnLayout`

   :class:`reahl.web.pure.UnitSize`             :class:`reahl.web.bootstrap.grid.ResponsiveSize` 
  ============================================  ======================================================


Added in (or for) Bootstrap
---------------------------

  A small number of classes/modules were added for Bootstrap that do not have simple equivalents:

  ============================================= ==============================================
   Class or package or module                    Contents
  ============================================= ==============================================
   :class:`reahl.web.bootstrap.navbar.Navbar`   A more elaborate header for a site.
   :mod:`reahl.web.bootstrap.inputgroup`        Bootstrap input groups.
   :mod:`reahl.web.holder`                      Creates placeholder background images.
  ============================================= ==============================================

