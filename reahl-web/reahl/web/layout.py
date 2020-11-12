# Copyright 2015-2020 Reahl Software Services (Pty) Ltd. All rights reserved.
#
#    This file is part of Reahl.
#
#    Reahl is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation; version 3 of the License.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
"""
.. versionadded:: 3.2

Utilities to deal with layout.


"""


from reahl.component.exceptions import arg_checks, IsInstance
from reahl.web.fw import Layout
from reahl.web.ui import Div, HTML5Page, Slot, Header, Footer


class PageLayout(Layout):
    """A PageLayout creates a basic skeleton inside an :class:`reahl.web.ui.HTML5Page`, and optionally
       applies specified :class:`~reahl.web.fw.Layout`\s to parts of this skeleton.

       The skeleton consists of a :class:`~reahl.web.ui.Div` called the `document` of the page, which
       contains three sub-sections inside of it:
       
         - the `.header` -- the page header area where menus and banners go;
         - the `.contents` of the page -- the main area to which the main content will be added; and
         - the `.footer` -- the page footer where links and legal notices go.    

       :keyword document_layout: A :class:`~reahl.web.fw.Layout` that will be applied to `.document`.
       :keyword contents_layout: A :class:`~reahl.web.fw.Layout` that will be applied to `.contents`.
       :keyword header_layout: A :class:`~reahl.web.fw.Layout` that will be applied to `.header`.
       :keyword footer_layout: A :class:`~reahl.web.fw.Layout` that will be applied to `.footer`.

       .. admonition:: Styling
       
          Adds a <div id="doc"> to the <body> of the page, which contains:

           - a <header id="hd">
           - a <div id="contents">
           - a <footer id="ft">

       .. versionadded:: 3.2

    """
    @arg_checks(document_layout=IsInstance(Layout, allow_none=True), contents_layout=IsInstance(Layout, allow_none=True),
                header_layout=IsInstance(Layout, allow_none=True), footer_layout=IsInstance(Layout, allow_none=True))
    def __init__(self, document_layout=None, contents_layout=None, header_layout=None, footer_layout=None):
        super().__init__()
        self.header = None    #: The :class:`reahl.web.ui.Header` of the page.
        self.contents = None  #: The :class:`reahl.web.ui.Div` containing the contents.
        self.footer = None    #: The :class:`reahl.web.ui.Footer` of the page.
        self.document = None  #: The :class:`reahl.web.ui.Div` containing the entire page.
        self.header_layout = header_layout   #: A :class:`reahl.web.fw.Layout` to be used for the header of the page.
        self.contents_layout = contents_layout #: A :class:`reahl.web.fw.Layout` to be used for the contents div of the page.
        self.footer_layout = footer_layout   #: A :class:`reahl.web.fw.Layout` to be used for the footer of the page.
        self.document_layout = document_layout #: A :class:`reahl.web.fw.Layout` to be used for the document of the page.

    @arg_checks(widget=IsInstance(HTML5Page))
    def apply_to_widget(self, widget):
        super().apply_to_widget(widget)

    def customise_widget(self):
        self.document = self.widget.body.add_child(Div(self.view))
        self.document.set_id('doc')
        if self.document_layout:
            self.document.use_layout(self.document_layout)
        
        self.header = self.document.add_child(Header(self.view))
        self.header.add_child(Slot(self.view, 'header'))
        self.header.set_id('hd')
        if self.header_layout:
            self.header.use_layout(self.header_layout)

        self.contents = self.document.add_child(Div(self.view))
        if self.contents_layout:
            self.contents.use_layout(self.contents_layout)

        self.contents.set_id('bd')
        self.contents.set_attribute('role', 'main')
        
        self.footer = self.document.add_child(Footer(self.view))
        self.footer.add_child(Slot(self.view, 'footer'))
        self.footer.set_id('ft')
        if self.footer_layout:
            self.footer.use_layout(self.footer_layout)

