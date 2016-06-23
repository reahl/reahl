# Copyright 2013-2016 Reahl Software Services (Pty) Ltd. All rights reserved.
# -*- encoding: utf-8 -*-
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

from reahl.component.modelinterface import exposed, IntegerField
from reahl.web.fw import Bookmark
from reahl.web.ui import Div, A, Span


#AppliedPendingMove: In future this class may be renamed to: reahl.web.attic.slidingpanel:SlidingPanel
# Uses: reahl/web/reahl.slidingpanel.css
# Uses: reahl/web/reahl.slidingpanel.js
class SlidingPanel(Div):
    """A Div which contains a number of other Panels, only one of which is displayed at a time.
       It sports controls that can be clicked by a user to advance the displayed content to the
       next or previous Div. Advancing is done by visually sliding in the direction indicated
       by the user if JavaScript is available. The panels advance once every 10 seconds if no
       user action is detected.

       .. admonition:: Styling

          Rendered as a <div class="reahl-slidingpanel"> which contains three children: a <div class="viewport">
          flanked on either side by an <a> (the controls for forcing it to transition left or right). The
          labels passed as `next` and `prev` are embedded in <span> tags inside the <a> tags.
          The :class:`Div` instances added to the :class:`SlidingPanel` are marked with a ``class="contained"``.

          For a SlidingPanel to function property, you need to specify a height and width to
          ``div.reahl-slidingpanel div.viewport``.

       :param view: (See :class:`reahl.web.fw.Widget`)
       :keyword css_id: (See :class:`reahl.web.ui.HTMLElement`)
       :keyword next: Text to put in the link clicked to slide to the next panel.
       :keyword prev: Text to put in the link clicked to slide to the previous panel.
    """
    def __init__(self, view, css_id=None, next='>', prev='<'):
        super(SlidingPanel, self).__init__(view, css_id=css_id)
        self.append_class('reahl-slidingpanel')
        self.container = Div(view)
        self.container.append_class('viewport')
        self.prev = self.add_child(A.from_bookmark(view, self.get_bookmark(index=self.previous_index, description='')))
        self.prev.add_child(Span(view, text=prev))
        self.add_child(self.container)
        self.next = self.add_child(A.from_bookmark(view, self.get_bookmark(index=self.next_index, description='')))
        self.next.add_child(Span(view, text=next))

    def add_panel(self, panel):
        """Adds `panel` to the list of :class:`Div` instances that share the same visual space."""
        panel.append_class('contained')
        self.container.add_child(panel)
        if self.max_panel_index != self.index:
            panel.add_to_attribute('style', ['display: none;'])
        self.prev.href = self.get_bookmark(index=self.previous_index).href
        self.next.href = self.get_bookmark(index=self.next_index).href

        return panel

    @property
    def max_panel_index(self):
        return len(self.container.children)-1

    @property
    def previous_index(self):
        if self.index == 0:
            return self.max_panel_index
        return self.index-1

    @property
    def next_index(self):
        if self.index == self.max_panel_index:
            return 0
        return self.index+1

    def get_bookmark(self, index=None, description=None):
        description = ('%s' % index) if description is None else description
        return Bookmark.for_widget(description, query_arguments={'index': index}).on_view(self.view)

    @exposed
    def query_fields(self, fields):
        fields.index = IntegerField(required=False, default=0)

    def get_js(self, context=None):
        selector = self.contextualise_selector(self.jquery_selector, context)
        return ['$(%s).slidingpanel();' % selector]

    @property
    def jquery_selector(self):
        return '".reahl-slidingpanel"'