.. Copyright 2016 Reahl Software Services (Pty) Ltd. All rights reserved.


Summary of Bootstrap differences
================================

This section is intended as a quick reference for someone who knows
the previous Widgets and Layouts and who needs to figure out how to
map an older tool to its Bootstrap equivalent.

If that's not you, you can safely skip this section.


The :mod:`reahl.web.bootstrap` package contains equivalent Layouts and
Widgets for all of the Widgets previously supported. The new
Widgets essentially do similar tasks but may look and behave
differently to previous counterparts. In many cases the Widgets also
have a different programming interface and the means by which their
layout is controlled may also be different.

Below follows a more detailed breakdown of changes.

Basic Widgets
-------------

.. |ui| replace:: :mod:`reahl.web.bootstrap.ui`

Simple Widgets are located in |ui|\. These
include Widgets that represent HTML (but styled versions) and a very
small number of equally basic Widgets. 

Whereas the standard :mod:`reahl.web.ui` module includes all basic Widgets, |ui|
excludes basic Widgets that pertain to larger topics that were split out into 
their own modules:

    - :mod:`reahl.web.bootstrap.forms` contains Inputs, Form and related Layouts
    - :mod:`reahl.web.bootstrap.files` contains Inputs for uploading files
    - :mod:`reahl.web.bootstrap.tables` contains Tables and related Widgets and Layouts


The following changes happened here:

    - Before, an Input automatically displayed an error message below 
      itself if it contained invalid input. Bootstrap versions do not.
      Depending on where they are used (via another Widget or a Layout)
      how and where error messages are displayed can differ, hence the
      Input cannot determine this by itself any longer.

    - The |ui| module now only contains
      Widgets corresponding to basic HTML elements or elements that
      are as simple as basic HTML elements in bootstrap-world. More
      complex Widgets are split out into separate modules.

    - Widgets that dealt with Layout of Forms, such as
      :class:`reahl.web.ui.LabelledBlockInput` and
      :class:`reahl.web.ui.LabelledInlineInput` have been
      axed. Instead, when using Bootstrap the layout of Forms are
      controlled using the new
      :class:`~reahl.web.bootstrap.forms.FormLayout` and its subclasses:

         - :class:`~reahl.web.bootstrap.forms.FormLayout`
         - :class:`~reahl.web.bootstrap.forms.GridFormLayout`
         - :class:`~reahl.web.bootstrap.forms.InlineFormLayout`

    - Other Layouts have been added for these basic Widgets:
         - :class:`~reahl.web.bootstrap.forms.ButtonLayout` (for :class:`~reahl.web.bootstrap.forms.Button` or :class:`~reahl.web.bootstrap.ui.A`).
         - :class:`~reahl.web.bootstrap.forms.TableLayout` (for :class:`~reahl.web.bootstrap.tables.Table`)

    
    - Some other Widgets that attempted to deal with styling, or that were mere aliases for HTML elements were removed:
         - :class:`~reahl.web.ui.InputGroup`
         - :class:`~reahl.web.ui.PriorityGroup`
         - :class:`~reahl.web.ui.Panel`
         - :class:`~reahl.web.ui.ErrorLabel`
         - :class:`~reahl.web.ui.LabelOverInput`

    - Instead of a SimpleFileInput, there are two simple kinds of file input:
         - :class:`~reahl.web.bootstrap.files.FileInputButton` (just a button which behaves like a file input)
         - :class:`~reahl.web.bootstrap.files.FileInput` (a stylized version of a standard browser file input)

    - CheckboxInput has been split into two versions:
         - :class:`~reahl.web.bootstrap.forms.PrimitiveCheckboxInput` (just a checkbox)
         - :class:`~reahl.web.bootstrap.forms.CheckboxInput` (a checkbox wrapped in a label)

     
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
   :class:`reahl.web.ui.CueInput`               :class:`reahl.web.bootstrap.forms.CueInput` 
   :class:`reahl.web.ui.ErrorFeedbackMessage`   :class:`reahl.web.bootstrap.ui.Alert` 
   :class:`reahl.web.ui.PopupA`                 :class:`reahl.web.bootstrap.popups.PopupA` (works differently) 
   :mod:`reahl.web.datatable`                   :mod:`reahl.web.bootstrap.tables` 
   :mod:`reahl.web.layout`                      :mod:`reahl.web.bootstrap.grid` 
   :mod:`reahl.web.pager`                       :mod:`reahl.web.bootstrap.pagination` 
  ============================================  ======================================================

Page layout
-----------

In Reahl 3.1, :class:`reahl.web.pure.PageColumnLayout` was used to
create a page with several columns. In Reahl 3.2 the same results can
be achieved by using a :class:`reahl.web.layout.PageLayout` that uses
a :class:`reahl.web.pure.ColumnLayout` for its contents area.

This new arrangement has a Bootstrap equivalent: use 
:class:`reahl.web.bootstrap.grid.PageLayout` in conjunction with a
with :class:`reahl.web.bootstrap.grid.ColumnLayout` for its contents.

Bootstrap's :class:`reahl.web.bootstrap.grid.ResponsiveSize` works
differently to Pure's :class:`reahl.web.pure.UnitSize`: with Pure, you
could state sizes as fractions, eg '1/2'. Bootstrap sizes are
stated as integers and their meaning is always "how many 1/12ths". Ie:
1 is 1/12th, 6 is 6/12ths and so on.

  ============================================  ======================================================
   Pure version                                  Bootstrap version
  ============================================  ======================================================
   :class:`reahl.web.pure.PageColumnLayout`     Not applicable to Bootstrap.

   :class:`reahl.web.layout.PageLayout`         :class:`reahl.web.bootstrap.grid.PageLayout`
   :class:`reahl.web.pure.ColumnLayout`         :class:`reahl.web.bootstrap.grid.ColumnLayout`

   :class:`reahl.web.pure.UnitSize`             :class:`reahl.web.bootstrap.grid.ResponsiveSize` 
  ============================================  ======================================================


Added in (or for) Bootstrap
---------------------------

A small number of classes/modules were added for Bootstrap that do not have simple equivalents:

  =============================================  ==============================================
   Class or package or module                     Contents
  =============================================  ==============================================
   :class:`reahl.web.bootstrap.navbar.Navbar`    A more elaborate header for a site.
   :class:`reahl.web.bootstrap.forms.StaticData` An :class:`~reahl.web.ui.Input` that can only be used for output.
   :mod:`reahl.web.bootstrap.forms.InputGroup`   A composed Input with Widgets before and after it.
   :mod:`reahl.web.holder`                       Creates placeholder background images.
  =============================================  ==============================================



