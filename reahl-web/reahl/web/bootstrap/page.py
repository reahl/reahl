# Copyright 2019, 2020 Reahl Software Services (Pty) Ltd. All rights reserved.
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
.. versionadded:: 5.0

The very basic Bootstrap components (ones that do not warrant their own module)

"""



from reahl.component.exceptions import ProgrammerError
from reahl.component.i18n import Catalogue
from reahl.web.fw import Widget
import reahl.web.ui
from reahl.web.ui import Div, Span, P, A, Url, TextNode, HTMLElement, HTMLAttributeValueOption, ErrorWidget
from reahl.web.layout import PageLayout
from reahl.web.bootstrap.forms import ButtonLayout
from reahl.web.bootstrap.ui import Alert
from reahl.web.bootstrap.grid import ColumnLayout, Container


_ = Catalogue('reahl-web')


class ErrorMessageBox(ErrorWidget):
    def __init__(self, view):
        super().__init__(view)
        alert = self.add_child(Alert(view, _('An error occurred:'), 'danger'))
        alert.add_child(HTMLElement(view, 'hr'))
        alert.add_child(P(view, text=self.error_message))
        a = alert.add_child(A(view, Url(self.error_source_href), description='Ok'))
        a.use_layout(ButtonLayout(style='primary'))


class BootstrapHTMLErrorPage(Widget):
    def __init__(self, view, page_class, *widget_args, **widget_kwargs):
        super().__init__(view)
        page = self.add_child(page_class(view, *widget_args, **widget_kwargs))
        if isinstance(page.layout, PageLayout):
            error_container = page.layout.header
            self.error_box = error_container.add_child(ErrorMessageBox(view))
        else:
            error_container = page.body
            self.error_box = error_container.insert_child(0, ErrorMessageBox(view))

    @classmethod
    def get_widget_bookmark_for_error(cls, error_message, error_source_bookmark):
        return ErrorMessageBox.get_widget_bookmark_for_error(error_message, error_source_bookmark)


class HTML5Page(reahl.web.ui.HTML5Page):
    """A web page that may be used as the page of a web application. It ensures that everything needed by
       the framework (linked CSS and JavaScript, etc) is available on such a page.

       .. admonition:: Styling
       
          Renders as an HTML5 page with customised <head> and an empty <body>.
       
       :param view: (See :class:`reahl.web.fw.Widget`)
       :keyword title: (See :class:`reahl.web.ui.HTML5Page`)
       :keyword css_id: (See :class:`reahl.web.ui.HTMLElement`)
       
    """
    @classmethod
    def get_error_page_factory(cls, *widget_args, **widget_kwargs):
        return BootstrapHTMLErrorPage.factory(cls, *widget_args, **widget_kwargs)
    
    def check_form_related_programmer_errors(self):
        super().check_form_related_programmer_errors()
        self.check_grids_nesting()
        
    def check_grids_nesting(self):
        for widget, parents_set in self.parent_widget_pairs(set([])):
            if isinstance(widget.layout, ColumnLayout):
                if not any(isinstance(parent.layout, Container) for parent in parents_set):
                    raise ProgrammerError(('%s does not have a parent with Layout of type %s.' % (widget, Container))+\
                      ' %s has a ColumnLayout, and thus needs to have an anchestor with a Container Layout.' % widget)
