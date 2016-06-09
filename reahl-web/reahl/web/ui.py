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
"""
Basic Widgets and related user interface elements.
"""

from __future__ import print_function, unicode_literals, absolute_import, division
import six

from string import Template
import warnings
import re
import time
import copy
from collections import OrderedDict

from babel import Locale, UnknownLocaleError

from reahl.component.exceptions import ProgrammerError
from reahl.component.eggs import ReahlEgg
from reahl.component.exceptions import IsInstance
from reahl.component.exceptions import ProgrammerError
from reahl.component.exceptions import arg_checks
from reahl.component.i18n import Translator
from reahl.component.py3compat import html_escape
from reahl.component.decorators import deprecated
from reahl.web.fw import WebExecutionContext, EventChannel, RemoteMethod, JsonResult, Widget, \
                          CheckedRemoteMethod, ValidationException, WidgetResult, WidgetFactory, \
                          Url, Bookmark, WidgetList, Layout
from reahl.web.libraries import YuiGridsCss
from reahl.component.modelinterface import ValidationConstraintList, ValidationConstraint, \
                                     PatternConstraint, RemoteConstraint,\
                                     Field, BooleanField, IntegerField, exposed, ConstraintNotFound, Choice, ChoiceGroup, \
                                     Event, Action, FileField, UploadedFile, InputParseException, StandaloneFieldIndex
import collections



_ = Translator('reahl-web')




class LiteralHTML(Widget):
    """The LiteralHTML Widget renders a chunk of HTML as given in
    `contents`. If a single-argument callable is given as `transform`,
    `contents` will first be passed to that callable to possibly
    change the HTML on-the-fly before rendering (the callable should
    return the changed HTML to be rendered).

    :param view: (See :class:`reahl.web.fw.Widget`)
    :param contents: Some literal HTML.
    :keyword transform: If given, it is called passing `contents` to possibly transform contents before rendering.
             The callable should return the final HTML to be rendered.
    """
    def __init__(self, view, contents, transform=(lambda i: i)):
        super(LiteralHTML, self).__init__(view)
        self.contents = contents
        self.transform = transform

    def render(self):
        return self.transform(self.contents)


class HTMLAttributeValueOption(object):
    def __init__(self, option_string, is_set, prefix='', constrain_value_to=None):
        if is_set and (constrain_value_to and option_string not in constrain_value_to):
            allowed_strings = ','.join(['"%s"' % i for i in constrain_value_to])
            raise ProgrammerError('"%s" should be one of: %s' % (option_string, allowed_strings))
        self.is_set = is_set
        self.prefix = prefix
        self.option_string = option_string

    def as_html_snippet(self):
        if not self.is_set:
            raise ProgrammerError('Attempt to add %s to html despite it not being set' % self)
        prefix_with_delimiter = '%s-' % self.prefix if self.prefix else ''
        return '%s%s' % (prefix_with_delimiter, self.option_string)


class HTMLAttribute(object):
    def __init__(self, name, values):
        super(HTMLAttribute, self).__init__()
        self.name = name
        self.value = set(values)

    def as_html_snippet(self):
        if not self.value:
            return ''
#        return '''%s='%s\'''' % (self.name, self.as_html_value())
        return '%s="%s"' % (self.name, html_escape(self.as_html_value()))
        
    def as_html_value(self):
        return ' '.join(sorted(self.value))

    def remove_values(self, values):
        self.value -= set(values)

    def add_values(self, values):
        self.value |= set(values)


class HTMLAttributeValues(object):
    def __init__(self, wrapped):
        self.wrapped = wrapped
        
    def __getitem__(self, name):
        return self.wrapped[name].as_html_value()
        
    def __contains__(self, item):
        return item in self.wrapped.values()


class HTMLAttributeDict(dict):
    @property
    def v(self):
        return HTMLAttributeValues(self)

    def sorted_values(self):
        values = list(self.values())
        sorted_values = []
        if 'name' in self:
            name_value = self['name']
            sorted_values.append(name_value)
            values.remove(name_value)
        if 'id' in self:
            id_value = self['id']
            sorted_values.append(id_value)
            values.remove(id_value)
        sorted_values += sorted(values, key=lambda a: a.name)            
        if 'class' in self:
            class_value = self['class']
            sorted_values.remove(class_value)
            sorted_values.append(class_value)

        return sorted_values

    def as_html_snippet(self):
        html_snippet = ' '.join([attribute.as_html_snippet() for attribute in self.sorted_values()
                                  if attribute.as_html_snippet()])
        if not html_snippet: return ''
        return ' '+html_snippet

    def add_to(self, name, values):
        assert all(value is not None for value in values)
        attribute = self.setdefault(name, HTMLAttribute(name, []))
        attribute.add_values(values)

    def remove_from(self, name, values):
        attribute = self.get(name)
        if attribute:
            attribute.remove_values(values)

    def set_to(self, name, value):
        assert value is not None
        self[name] = HTMLAttribute(name, [value])

    def clear(self, name):
        del self[name]        


#PendingMove: In future this class may be renamed to: reahl.web.attic.layout:PriorityGroup instead
class PriorityGroup(object):
    """A PriorityGroup ensures that only one of the Widgets added to it has primary priority, 
       the others in the group can have secondary priority, or no priority specified. This 
       is used for styling Widgets based on their priority in the PriorityGroup.
    """
    def __init__(self):
        self.widgets = set()
        self.has_primary = False

    def add(self, widget):
        """Adds `widget`, with no priority set."""
        assert widget not in self.widgets, '%s is already added to %s' % (widget, self)
        self.widgets.add(widget)

    def add_secondary(self, widget):
        """Adds `widget`, with secondary priority."""
        self.add(widget)
        widget.set_priority(secondary=True)
        
    def add_primary(self, widget):
        """Adds `widget`, with primary priority."""
        assert not self.has_primary, 'Cannot add more than one widget as primary to %s' % self
        self.add(widget)
        widget.set_priority(primary=True)
        self.has_primary = True


# Uses: reahl/web/reahl.hashchange.js
class HashChangeHandler(object):
    def __init__(self, widget, for_fields):
        self.error_message = _('An error occurred when contacting the server. Please try again later.')
        self.timeout_message = _('The server took too long to respond. Please try again later.')
        self.widget = widget
        self.for_fields = for_fields
        result = WidgetResult(widget)
        method_name = 'refresh_%s' % widget.css_id
        callable_object = lambda *args, **kwargs: None
        self.remote_method = RemoteMethod(method_name, callable_object, result, immutable=True)
        widget.view.add_resource(self.remote_method)

    @property
    def argument_defaults(self):
        i = StandaloneFieldIndex()
        i.update(dict([(field.name, field) for field in self.for_fields]))
        field_defaults = i.as_kwargs()
        argument_defaults = ['%s: "%s"' % (name, default_value or '') \
                             for name, default_value in field_defaults.items()]
        return '{%s}' % ','.join(argument_defaults)

    def as_jquery_parameter(self):
        return '{url:"%s", errorMessage: "%s", timeoutMessage: "%s", params: %s}' % \
               (self.remote_method.get_url(), self.error_message, self.timeout_message, self.argument_defaults)


class HTMLElement(Widget):
    """A Widget that is represented by an HTML element.
    
    :param view: (See :class:`reahl.web.fw.Widget`)
    :param tag_name: The element name used to render tags for this HTMLElement
    :keyword children_allowed: Elements that are not allowed to have children are rendered only with opening tags,
                             others have an opening and closing tag. 
                             (See `HTML5 void elements <http://dev.w3.org/html5/markup/syntax.html#syntax-elements>`_.)
    :keyword css_id: If specified, the HTMLElement will have an id attribute set to this. Mandatory when a Widget has :meth:`query_fields`.
    :keyword read_check: (See :class:`reahl.web.fw.Widget`)
    :keyword write_check: (See :class:`reahl.web.fw.Widget`)
    
    """
    tag_name = 'tag'
    def __init__(self, view, tag_name, children_allowed=False, css_id=None, read_check=None, write_check=None):
        super(HTMLElement, self).__init__(view, read_check=read_check, write_check=write_check)
        self.attribute_sources = []
        self.children_allowed = children_allowed
        self.tag_name = tag_name
        self.constant_attributes = HTMLAttributeDict()
        self.ajax_handler = None
        if css_id:
            self.set_id(css_id)

    def __str__(self):
        css_id_part = '(not set)'
        if self.css_id_is_set:
            css_id_part = self.css_id
        return '<%s %s %s>' % (self.__class__.__name__, self.tag_name, 'id=%s' % css_id_part)

    def enable_refresh(self, *for_fields):
        """Sets this HTMLElement up so that it will refresh itself without reloading its page when it senses that 
           one of the given `query_fields` have changed. If no Fields are specified here, the HTMLElement
           is refreshed when any of its `query_fields` change.

           :arg for_fields: A selection of the `.query_fields` defined on this HTMLElement.

           .. versionchanged:: 3.2
              The `for_fields` arguments were added to allow control over which of an 
              HTMLElement's `query_fields` trigger a refresh.
        """
        if not self.css_id_is_set:
            raise ProgrammerError('%s does not have a css_id set. A fixed css_id is mandatory when a Widget self-refreshes' % self)
        assert all([(field in self.query_fields.values()) for field in for_fields])
        
        self.add_hash_change_handler(for_fields if for_fields else self.query_fields.values())
        
    def is_refresh_enabled(self):
        return self.ajax_handler is not None

    def add_child(self, child):
        assert self.children_allowed, 'You cannot add children to a %s' % type(self)
        return super(HTMLElement, self).add_child(child)

    def add_attribute_source(self, attribute_source):
        self.attribute_sources.append(attribute_source)

    def add_to_attribute(self, name, values):
        """Ensures that the value of the attribute `name` of this HTMLElement includes the words listed in `values` 
           (a list of strings).
        """
        self.constant_attributes.add_to(name, values)
    
    def set_attribute(self, name, value):
        """Sets the value of the attribute `name` of this HTMLElement to the string `value`."""
        self.constant_attributes.set_to(name, value)

    def get_attribute(self, name):
        """Answers the value of the attribute named `name`."""
        return self.attributes[name].as_html_value()

    def has_attribute(self, name):
        """Answers whether this HTMLElement has an attribute named `name`."""
        return name in self.attributes
            
    @property
    def attributes(self):
        """Override this method if you want to change the attributes of this HTMLElement on the fly, based on the state
           of the HTMLElement at the point in time when it is rendered."""
        attributes = HTMLAttributeDict(self.constant_attributes)
        if self.priority == 'secondary':
            attributes.add_to('class', ['reahl-priority-secondary'])
        elif self.priority == 'primary':
            attributes.add_to('class', ['reahl-priority-primary'])
        for attribute_source in self.attribute_sources:
            attribute_source.set_attributes(attributes)
        return attributes
        
    def add_hash_change_handler(self, for_fields):
        assert not self.ajax_handler
        self.ajax_handler = HashChangeHandler(self, for_fields)
        
    def render(self):
        if self.visible:
            rendered = '<%s%s>' % (self.tag_name, self.attributes.as_html_snippet())
            if self.children_allowed:
                rendered += self.render_contents() + ('</%s>' % self.tag_name)
            return rendered
        else:
            return ''

    @property
    def css_id_is_set(self):
        return getattr(self, '_css_id', None) is not None
    def get_css_id(self):
        if not self.css_id_is_set:
            raise ProgrammerError('%s needs a css_id to be set!' % self)
        return self._css_id
    def set_css_id(self, value):
        self._css_id = value
        self.set_attribute('id', value)
    css_id = property(get_css_id, set_css_id)
    
    def contextualise_selector(self, selector, context):
        """Returns a JQuery selector for finding `selector` within the elements matched by `context` (another selector)."""
        context_str = ', "%s"' % context if context else ''
        return '%s%s' % (selector, context_str)

    @property
    def jquery_selector(self):
        """Returns a string (including its " delimeters) which can be used to target this HTMLElement using
           JQuery. By default this uses the id attribute of the HTMLElement, but this property can be overridden to
           not be dependent on the id attribute of the HTMLElement.
        
           :raises ProgrammerError: Raised when accessing `jquery_selector` if the css_id of this HTMLElement is not set.
        """
        return '"#%s"' % (self.css_id)

    def get_js(self, context=None):
        js = []
        if self.is_refresh_enabled():
            js = ['$(%s).hashchange(%s);' % \
                  (self.contextualise_selector(self.jquery_selector, context),
                   self.ajax_handler.as_jquery_parameter())]
        return super(HTMLElement, self).get_js(context=context) + js

    def set_title(self, title):
        """A convenience method to set the "title" attribute of this HTMLElement."""
        self.set_attribute('title', title)

    def set_id(self, css_id):
        """A convenience method to set the "id" attribute of this HTMLElement."""
        self.css_id = css_id

    def append_class(self, css_class):
        """A convenience method to add the word in `css_class` to the "class" attribute of thie HTMLElement."""
        self.add_to_attribute('class', [css_class])


class TextNode(Widget):
    """An `HTML TextNode <http://dev.w3.org/html5/spec-LC/infrastructure.html#text-node>`_. You can, for example,
       use a TextNode to add a snippet of text as a child of a P inbetween its other children (which will all be
       HTMLElements, like Span).

       :param view: (See :class:`reahl.web.fw.Widget`)
       :param value_or_getter: A string which will be used as the text of the TextNode. Pass a no-arg callable instead
                               to delay the computation of what the text of the TextNode should be to the time of 
                               rendering the TextNode. The callable will be called right before the TextNode is rendered,
                               and should return the text that should be used in the TextNode.
       :param html_escape: If True (default), the given `value` will first be HTML-escaped before rendered to the browser.
    """
    def __init__(self, view, value_or_getter, html_escape=True):
        super(TextNode, self).__init__(view)
        self.html_escape = html_escape
        if isinstance(value_or_getter, collections.Callable):
            self.value_getter = value_or_getter
        else:
            def get_value():
                return value_or_getter
            self.value_getter = get_value

    @property
    def value(self):
        return self.value_getter()

    def render(self):
        # Un-escaped quotes are not harmful between tags, where TextNodes live,
        # and even make the HTML source make nicer
        return html_escape(self.value, quote=False) if self.html_escape else self.value


class Title(HTMLElement):
    """The title of an HTML page (the title of a :class:`reahl.web.fw.View` is usually shown via a Title). 

       .. admonition:: Styling
       
          Rendered as a <title> element.
    
       :param view: (See :class:`reahl.web.fw.Widget`)
       :param text: A string for use in a `PEP-292 <http://www.python.org/dev/peps/pep-0292/>`_ template. The final
                    value after substituting this string Template will be used as the value of this Title. The
                    template string may use one placeholder: $current_title which contains the title of the current
                    View.
       :keyword css_id: (See :class:`reahl.web.ui.HTMLElement`)
       
    """
    def __init__(self, view, text, css_id=None):
        super(Title, self).__init__(view, 'title', children_allowed=True, css_id=css_id)
        self.text = Template(text)
        self.add_child(TextNode(view, self.get_current_title))

    def get_current_title(self):
        return self.text.substitute(current_title=self.view.title)


class Link(HTMLElement):
    """A link to an external resource.

       .. admonition:: Styling
   
          Renders as an HTML <link> element.
    
       :param view: (See :class:`reahl.web.fw.Widget`)
       :param rel: The value of the "rel" attribute of this HTMLElement.
       :param href: The value of the "href" attribute of this HTMLElement.
       :keyword _type: The value of the "type" attribute of this HTMLElement.
       :keyword css_id:  (See :class:`reahl.web.ui.HTMLElement`)
       
       .. versionchanged:: 3.2
          Changed _type to be an optional, keyword argument instead of a positional argument.
    """
    def __init__(self, view, rel, href, _type=None, css_id=None):
        super(Link, self).__init__(view, 'link', css_id=css_id)
        self.set_attribute('rel', rel)
        self.set_attribute('href', six.text_type(href))
        if _type is not None:
            self.set_attribute('type', _type)


class Slot(Widget):
    """A Slot is a placeholder area on a page into which different Views can plug different Widgets on the fly.

    Using Slots, one can create a single HTML5page which can be
    re-used by different Views instead of having to create
    similar-looking HTML5Pages for each View in an application. 

    A Slot is added to an HTML5Page to represent an area that will be
    populated later by a View. When a View is served up the framework
    can then populate this empty area with Widgets specific to the
    current View.

    :param view: (See :class:`reahl.web.fw.Widget`)
    :param name: A name for this Slot (must be unique on the page)

    """
    def __init__(self, view, name):
        super(Slot, self).__init__(view)
        self.name = name

    @property
    def available_slots(self):
        return {self.name: self}

    def fill(self, widget):
        self.clear_children()
        self.add_child(widget)


class Meta(HTMLElement):
    def __init__(self, view, name, content):
        super(Meta, self).__init__(view, 'meta', children_allowed=False)
        self.set_attribute('name', name)
        self.set_attribute('content', content)


class Head(HTMLElement):
    """A container for metadata of a View.

       .. admonition:: Styling

          Renders as an HTML <head> element.

       :param view: (See :class:`reahl.web.fw.Widget`)
       :param title: Text for a template to be used as document Title (See also :class:`Title`).
       :param css_id: (See :class:`reahl.web.ui.HTMLElement`)
    """
    def __init__(self, view, title, css_id=None):
        super(Head, self).__init__(view, 'head', children_allowed=True, css_id=css_id)
        self.title = self.add_child(Title(view, title))
        self.add_child(Slot(view, name='reahl_header'))

    def add_css(self, href):
        self.add_child(Link(self.view, 'stylesheet', href, 'text/css'))


class Body(HTMLElement):
    """The content of an HTML document.

       .. admonition:: Styling

          Renders as an HTML <body> element.
    
       :param view: (See :class:`reahl.web.fw.Widget`)
       :keyword css_id: (See :class:`reahl.web.ui.HTMLElement`)
       
    """
    def __init__(self, view, css_id=None):
        super(Body, self).__init__(view, 'body', children_allowed=True, css_id=css_id)
        self.add_child(Slot(self.view, name='reahl_footer'))

    def footer_already_added(self):        
        if len(self.children) > 0:
            last_child = self.children[-1]
            return isinstance(last_child, Slot) and last_child.name == 'reahl_footer'
        return False

    def add_child(self, child):
        existing_footer = None
        if self.footer_already_added():
            existing_footer = self.children.pop()
        super(Body, self).add_child(child)
        if existing_footer:
            self.children.append(existing_footer)
        return child

    def attach_out_of_bound_forms(self, forms):
        self.add_children(forms)


class HTML5Page(HTMLElement):
    """A web page that may be used as the page of a web application. It ensures that everything needed by
       the framework (linked CSS and JavaScript, etc) is available on such a page.

       .. admonition:: Styling
       
          Renders as an HTML5 page with customised <head> and an empty <body>.
       
       :param view: (See :class:`reahl.web.fw.Widget`)
       :keyword title: Text for a template to be used as document Title (See also :class:`Title`).
       :keyword style: Pass a string denoting a predifined set of css styles.
       :keyword css_id: (See :class:`reahl.web.ui.HTMLElement`)
       
    """
    @arg_checks(title=IsInstance(six.string_types))
    def __init__(self, view, title='$current_title', style=None, css_id=None):
        super(HTML5Page, self).__init__(view, 'html', children_allowed=True, css_id=css_id)
        self.append_class('no-js')
        script = self.add_child(HTMLElement(self.view, 'script', children_allowed=True))
        script.add_child(TextNode(self.view, '''
          function switchJSStyle(d, fromStyle, toStyle) {
              var r=d.querySelectorAll("html")[0];
              r.className=r.className.replace(new RegExp("\\\\b" + fromStyle + "\\\\b", "g"),toStyle)
          };
          (function(e){switchJSStyle(e, "no-js", "js")})(document);
        '''))

        self.head = self.add_child(Head(view, title))  #: The Head HTMLElement of this page
        self.body = self.add_child(Body(view))         #: The Body HTMLElement of this page

        if style:
            self.head.add_css(Url('/styles/%s.css' % style))

    def render(self):
        return '<!DOCTYPE html>' + super(HTML5Page, self).render()


@deprecated('Please use reahl.web.layout:PageLayout instead.', '3.1')
class TwoColumnPage(HTML5Page):
    """An HTML5Page with a basic layout: It has a header area which displays at top of two columns. A footer area
       displays below the two columns. The main column is to the right, and larger. The secondary column is to 
       the left, and smaller.
       
       .. admonition:: Styling

          Renders as a page structured using Yui 2, with two template preset columns 
           (main and secondary).

       The TwoColumnPage has the following Slots:

       main
         Used by Views to plug content into the main column.
       secondary
         Used by Views to plug content into the secondary column.
       header
         Used by Views to plug content into the header area.
       footer
         Used by Views to plug content into the footer area.

       :param view: (See :class:`reahl.web.fw.Widget`)
       :param title: Text for a template to be used as document Title (See also :class:`Title`).
       :param style: (See :class:`reahl.web.ui.HTML5Page`)
       :param css_id: (See :class:`reahl.web.ui.HTMLElement`)
    """
    @arg_checks(title=IsInstance(six.string_types))
    def __init__(self, view, title='$current_title', style=None, css_id=None):
        super(TwoColumnPage, self).__init__(view, title=title, style=style, css_id=css_id)
        YuiGridsCss.check_enabled(self)
            
        self.yui_page = self.body.add_child(YuiDoc(view, 'doc', 'yui-t2'))
        self.main.add_child(Slot(view, 'main'))
        self.secondary.add_child(Slot(view, 'secondary'))
        self.header.add_child(Slot(view, 'header'))
        self.footer.add_child(Slot(view, 'footer'))

    tag_name = 'html'  # So deprecation warning does not break

    @property
    def footer(self):
        """The Div used as footer area."""
        return self.yui_page.footer

    @property
    def header(self):
        """The Div used as header area."""
        return self.yui_page.header

    @property
    def main(self):
        """The Div used as main column."""
        return self.yui_page.main_block

    @property
    def secondary(self):
        """The Div used as secondary column."""
        return self.yui_page.secondary_block


# Uses: reahl/web/reahl.ajaxlink.js
class A(HTMLElement):
    """A hyper link.

       .. admonition:: Styling

          Renders as an HTML <a> element.
    
       :param view: (See :class:`reahl.web.fw.Widget`)
       :param href: The URL (or URL fragment) to which the hyperlink leads. 
       :keyword description: The textual description to be shown on the hyperlink.
       :keyword ajax: (Not for general use)
       :keyword read_check: (See :class:`reahl.web.fw.Widget`)
       :keyword write_check: (See :class:`reahl.web.fw.Widget`)
       :keyword css_id: (See :class:`reahl.web.ui.HTMLElement`)
       
    """
    @classmethod
    def from_bookmark(cls, view, bookmark):
        """Creates an A for the given `bookmark` on `view`."""
        if bookmark.is_page_internal:
            raise ProgrammerError('You cannot use page-internal Bookmarks directly, first add it to a Bookmark to a View')
        return cls(view, bookmark.href, description=bookmark.description, ajax=bookmark.ajax, 
                   read_check=bookmark.read_check, write_check=bookmark.write_check)

    @classmethod
    def factory_from_bookmark(cls, bookmark):
        """Creates a :class:`reahl.web.fw.WidgetFactory` for creating an A for the given `bookmark`."""
        if bookmark.is_page_internal:
            raise ProgrammerError('You cannot use page-internal Bookmarks directly, first add it to a Bookmark to a View')
        return WidgetFactory(cls, bookmark.href, description=bookmark.description, ajax=bookmark.ajax,
                             read_check=bookmark.read_check, write_check=bookmark.write_check)

    @arg_checks(href=IsInstance(Url, allow_none=True))
    def __init__(self, view, href, description=None, ajax=False, read_check=None, write_check=None, css_id=None):
        self.href = href
        self.ajax = ajax
        super(A, self).__init__(view, 'a', children_allowed=True, read_check=read_check, write_check=write_check, css_id=css_id)
        if description:
            self.add_child(TextNode(self.view, description))
        if self.ajax:
            self.append_class('reahl-ajaxlink')
        self.active = True

    @property
    def attributes(self):
        attributes = super(A, self).attributes
        if self.active and (not self.disabled) and self.href is not None:
            attributes.set_to('href', six.text_type(self.href))
        return attributes

    def get_js(self, context=None):
        return ['$(%s).ajaxlink();' % self.contextualise_selector('".reahl-ajaxlink"', context)]

    def set_active(self, active):
        """Explicitly sets whether this hyperlink is "active" or not. An active hyperlink cannot be clicked on,
           because conceptually, the user is already at its target.
        
           :param active: A boolean -- send True if active, else False.
        """
        self.active = active


# Uses: reahl/web/reahl.runningonbadge.css
class RunningOnBadge(A):
    """A visual badge proclaiming that a website is "Running on Reahl". Using it on your site
       is a bit of advertising for Reahl!

       .. admonition:: Styling

          Renders as an HTML <a class="runningon"> containing an <img>
              
       :param view: (See :class:`reahl.web.fw.Widget`)
    """
    def __init__(self, view):
        super(RunningOnBadge, self).__init__(view, Url('http://www.reahl.org'))
        self.append_class('runningon')
        self.add_child(Img(view, Url('/static/runningon.png'), alt='Running on Reahl'))


class H(HTMLElement):
    """The heading for a section.

       .. admonition:: Styling

          Renders as an HTML <h1>, <h2> ... , <h6> element, depending on priority.
              
       :param view: (See :class:`reahl.web.fw.Widget`)
       :param priority: The heading level (a value from 1 to 6)
       :keyword text: The text value displayed in the heading (if given)
       :keyword css_id: (See :class:`reahl.web.ui.HTMLElement`)
       
    """
    def __init__(self, view, priority, text=None, css_id=None):
        super(H, self).__init__(view, 'h%s' % priority, children_allowed=True, css_id=css_id)
        if text:
            self.add_child(TextNode(view, text))


class Br(HTMLElement):
    def __init__(self, view):
        super(Br, self).__init__(view, 'br', children_allowed=False)


class P(HTMLElement):
    """A paragraph of text.

       .. admonition:: Styling

          Renders as an HTML <p> element.
    
       :param view: (See :class:`reahl.web.fw.Widget`)
       :keyword text: The text value displayed in the paragraph (if given)
       :keyword css_id: (See :class:`reahl.web.ui.HTMLElement`)
       :keyword html_escape: If `text` is given, by default such text is HTML-escaped. Pass False in here to prevent this from happening.
       
    """
    def __init__(self, view, text=None, css_id=None, html_escape=True):
        super(P, self).__init__(view, 'p', children_allowed=True, css_id=css_id)
        if text:
            self.add_child(TextNode(view, text, html_escape=html_escape))

    @property
    def text(self):
        text = ''
        for child in self.children:
            if isinstance(child, TextNode):
                text += child.value
        return text
    
    def parse_children(self, text):
        pattern = '(?<![{])[{]([0-9]+|%s)[}](?![}])' % Template.idpattern
        last = 0
        for i in re.finditer(pattern, text):
            head = text[last:i.start()]
            last = i.end()
            yield TextNode(self.view, head.replace('{{', '{').replace('}}','}'))
            yield Slot(self.view, i.groups()[0])
        yield TextNode(self.view, text[last:])

    def format(self, *args, **kwargs):
        """A complicated paragraph may consist of many TextNodes interspersed with other Widgets. Creating such a
           paragraph programmatically is cumbersome. Instead, the `text` of a P can be a template resembling
           a `PEP-292 <http://www.python.org/dev/peps/pep-0292/>`_ template. This `format` method works analogously to
           :meth:`string.format`, except that Widgets can be passed in to be substituted into the original P.
           
           :param args: Positional arguments for substituting into the "template P"
           :param kwargs: Named arguments for substituting into the "template P"
        """
        filled_p = self.__class__(self.view)
        for child in self.parse_children(self.text):
            filled_p.add_child(child)

        for i in list(range(0, len(args))):
            filled_p.set_slot(six.text_type(i), args[i])
        for slot_name, widget in kwargs.items():
            filled_p.set_slot(slot_name, widget)
        return filled_p

    def set_slot(self, name, widget):
        self.available_slots[name].fill(widget)


#PendingMove: In future this class may be renamed to: reahl.web.attic.layout:ErrorFeedbackMessage
class ErrorFeedbackMessage(P):
    """A user message indicating some error condition, such as a form validation which failed.

       .. admonition:: Styling
    
          Renders as an HTML <p class="error feedback"> element.
    """
    @property
    def attributes(self):
        attributes = super(ErrorFeedbackMessage, self).attributes
        attributes.add_to('class', ['error', 'feedback'])
        return attributes    


class Div(HTMLElement):
    """A logical grouping of other HTMLElements.

       .. admonition:: Styling

          Renders as an HTML <div> element
    
       :param view: (See :class:`reahl.web.fw.Widget`)
       :keyword css_id: (See :class:`reahl.web.ui.HTMLElement`)
       
    """
    def __init__(self, view, css_id=None):
        super(Div, self).__init__(view, 'div', children_allowed=True, css_id=css_id)



class Nav(HTMLElement):
    """A grouping of HTMLElements that refer to or link to other pages or parts within the current page. 

       .. admonition:: Styling

          Renders as an HTML <nav> element.
    
       :param view: (See :class:`reahl.web.fw.Widget`)
       :keyword css_id: (See :class:`reahl.web.ui.HTMLElement`)
       
    """
    def __init__(self, view, css_id=None):
        super(Nav, self).__init__(view, 'nav', children_allowed=True, css_id=css_id)


class Article(HTMLElement):
    """An independent section of informational content.
    
       .. admonition:: Styling
       
          Renders as an HTML <article> element.
          
       :param view: (See :class:`reahl.web.fw.Widget`)
       :keyword css_id: (See :class:`reahl.web.ui.HTMLElement`)
       
    """
    def __init__(self, view, css_id=None):
        super(Article, self).__init__(view, 'article', children_allowed=True, css_id=css_id)


class Header(HTMLElement):
    """A grouping of elements representing metadata pertaining to a section, such as an :class:`Article`.

       .. admonition:: Styling

          Rendered as an HTML <article> element.
    
       :param view: (See :class:`reahl.web.fw.Widget`)
       :keyword css_id: (See :class:`reahl.web.ui.HTMLElement`)
       
    """
    def __init__(self, view, css_id=None):
        super(Header, self).__init__(view, 'header', children_allowed=True, css_id=css_id)


class Footer(HTMLElement):
    """The footer of a section (such as an :class:`Article`).

       .. admonition:: Styling

          Renders as an HTML <footer> element.
    
       :param view: (See :class:`reahl.web.fw.Widget`)
       :keyword css_id: (See :class:`reahl.web.ui.HTMLElement`)
       
    """
    def __init__(self, view, css_id=None):
        super(Footer, self).__init__(view, 'footer', children_allowed=True, css_id=css_id)


class Li(HTMLElement):
    """A list item.
        
       .. admonition:: Styling

          Renders as an HTML <li> element.

       :param view: (See :class:`reahl.web.fw.Widget`)
       :keyword css_id: (See :class:`reahl.web.ui.HTMLElement`)
       
    """
    def __init__(self, view, css_id=None):
        super(Li, self).__init__(view, 'li', children_allowed=True, css_id=css_id)
        
    
class Ul(HTMLElement):
    """An unordered list. 
    
       .. admonition:: Styling

          Renders as an HTML <ul> element.
    
       :param view: (See :class:`reahl.web.fw.Widget`)
       :keyword css_id: (See :class:`reahl.web.ui.HTMLElement`)
       
    """
    def __init__(self, view, css_id=None):
        super(Ul, self).__init__(view, 'ul', children_allowed=True, css_id=css_id)


class Ol(HTMLElement):
    """An ordered list.

       .. admonition:: Styling

          Renders as an HTML <ol> element.

       :param view: (See :class:`reahl.web.fw.Widget`)
       :keyword css_id: (See :class:`reahl.web.ui.HTMLElement`)

    """
    def __init__(self, view, css_id=None):
        super(Ol, self).__init__(view, 'ol', children_allowed=True, css_id=css_id)


class Img(HTMLElement):
    """An embedded image. 

       .. admonition:: Styling
    
          Renders as an HTML <img> element.
    

       :param view: (See :class:`reahl.web.fw.Widget`)
       :param src: The URL from where the embedded image file should be fetched.
       :keyword alt: Alternative text describing the image.
       :keyword css_id: (See :class:`reahl.web.ui.HTMLElement`)
       
    """
    def __init__(self, view, src=None, alt=None, css_id=None):
        super(Img, self).__init__(view, 'img', css_id=css_id)
        if src is not None:
            self.set_attribute('src', six.text_type(src))
        if alt:
            self.set_attribute('alt', alt)


@deprecated('Please use reahl.web.ui:Div instead', '3.2')
class Panel(Div):
    """A logical container for other Widgets.

       .. admonition:: Styling
       
          Renders as an HTML <div> element.
    """
    pass


@deprecated('Please use reahl.web.layout:PageLayout instead.', '3.1')
class YuiDoc(Div):
    """A Yui 2 #doc div: the container of the #hd, #bd and #ft (see http://developer.yahoo.com/yui/grids/#start)"""
    def __init__(self, view, doc_id, doc_class, css_id=None):
        super(YuiDoc, self).__init__(view, css_id=css_id)
        YuiGridsCss.check_enabled(self)
        self.set_id(doc_id)
        self.append_class(doc_class)
        self.hd = YuiGrid(view)   #:
        self.hd.set_id('hd')
        self.header = self.hd.add_child(Header(view))

        self.bd = Div(view)    #:
        self.bd.set_id('bd')
        self.bd.set_attribute('role', 'main')
        yui_main_wrapper  = self.bd.add_child(Div(view))
        self.secondary_block = self.bd.add_child(YuiBlock(view))    #: the secondary div (see Yui 2 template presents)
        yui_main_wrapper.set_id('yui-main')
        self.main_block = yui_main_wrapper.add_child(YuiBlock(view)) #: the #yui-main div (see Yui 2 template presents)

        self.ft = Div(view)    #:
        self.ft.set_id('ft')
        self.footer = self.ft.add_child(Footer(view))

        self.add_children([self.hd, self.bd, self.ft])


class YuiElement(Div):
    yui_class = None
    
    def __init__(self, view, css_id=None):
        YuiGridsCss.check_enabled(self)
        super (YuiElement, self).__init__(view, css_id=css_id)


    @property
    def attributes(self):
        attributes = super(YuiElement, self).attributes
        attributes.add_to('class', [self.yui_class])
        return attributes


@deprecated('Please use reahl.web.pure:ColumnLayout instead.', '3.1')
class YuiBlock(YuiElement):
    """A Yui 2 block: see http://developer.yahoo.com/yui/grids/#start """
    yui_class = 'yui-b'


@deprecated('Please use reahl.web.pure:ColumnLayout instead.', '3.1')
class YuiGrid(YuiElement):
    """A Yui 2 grid: see http://developer.yahoo.com/yui/grids/#start """
    yui_class = 'yui-g'


@deprecated('Please use reahl.web.pure:ColumnLayout instead.', '3.1')
class YuiUnit(YuiElement):
    """A Yui 2 unit: see http://developer.yahoo.com/yui/grids/#start 
    
       :param view: (See :class:`reahl.web.fw.Widget`)
       :param first: Pass True for the first YuiUnit in a YuiGrid
    """
    yui_class = 'yui-u'
    def __init__(self, view, first=False):
        super(YuiUnit, self).__init__(view)
        self.first = first

    @property
    def attributes(self):
        attributes = super(YuiUnit, self).attributes
        if self.first:
            attributes.add_to('class', ['first'])
        return attributes


class Span(HTMLElement):
    """A logical grouping of other HTMLElements which fits in with text flow.

       .. admonition:: Styling
       
          Renders as an HTML <span> element.
    
       :param view: (See :class:`reahl.web.fw.Widget`)
       :keyword text: Will be added as text content of the Span if given.
       :keyword css_id: (See :class:`reahl.web.ui.HTMLElement`)
       
    """

    def __init__(self, view, text=None, html_escape=True, css_id=None):
        super(Span, self).__init__(view, 'span', children_allowed=True, css_id=css_id)
        if text:
            self.add_child(TextNode(view, text))



# Uses: reahl/web/reahl.form.js
class Form(HTMLElement):
    """A Form is a container for Inputs. Any Input has to belong to a Form. When a user clicks on
       a Button associated with a Form, the Event to which the Button is linked occurs at the 
       server. The value of every Input that is associated with the Form is sent along with the 
       Event to the server.

       .. admonition:: Styling
       
          Renders as an HTML <form class="reahl-form"> element.
       
       :param view: (See :class:`reahl.web.fw.Widget`)
       :param unique_name: A name for this form, unique in the UserInterface where it is used.
       
    """
    is_Form = True
    def __init__(self, view, unique_name, rendered_form=None):
        self.view = view
        self.inputs = OrderedDict()
        self.registered_input_names = {}
        self.set_up_event_channel(unique_name)
        self.set_up_field_validator('%s_validate' % unique_name)
        self.set_up_input_formatter('%s_format' % unique_name)
        self.rendered_form = rendered_form or self
        assert unique_name == self.event_channel.name
        super(Form, self).__init__(view, 'form', children_allowed=True, css_id=unique_name)
        self.set_attribute('data-formatter', six.text_type(self.input_formatter.get_url()))

    def set_up_event_channel(self, event_channel_name):
        self.event_channel = EventChannel(self, self.controller, event_channel_name)
        self.view.add_resource(self.event_channel)

    def set_up_field_validator(self, field_validator_name):
        json_result = JsonResult(BooleanField(true_value='true', false_value='false'),
                                 catch_exception=ValidationConstraint)
        self.field_validator = RemoteMethod(field_validator_name, 
                                          self.validate_single_input,
                                          json_result,
                                          immutable=True)
        self.view.add_resource(self.field_validator)

    def validate_single_input(self, **input_values):
        try:
            name = list(input_values.keys())[0]
            self.inputs[name].validate_input(input_values)
            return True
        except (KeyError, IndexError):
            return False
        except ValidationConstraint:
            raise
        return False

    def set_up_input_formatter(self, input_formatter_name):
        self.input_formatter = RemoteMethod(input_formatter_name, 
                                            self.format_single_input,
                                            JsonResult(Field()),
                                            immutable=True)
        self.view.add_resource(self.input_formatter)

    def format_single_input(self, **input_values):
        try:
            name = list(input_values.keys())[0]
            return self.inputs[name].format_input(input_values)
        except (KeyError, IndexError):
            return ''
        except ValidationException:
            return ''

    @property
    def controller(self):
        return self.view.controller
    
    def contains_file_upload_input(self):
        for i in self.inputs.values():
            if i.is_for_file:
                return True
        return False

    @property
    def attributes(self):
        attributes = super(Form, self).attributes
        attributes.add_to('class', ['reahl-form'])
        attributes.set_to('action', self.action)
        attributes.set_to('method', 'POST')
        attributes.set_to('id', self.css_id)
        if self.contains_file_upload_input():
            attributes.set_to('enctype', 'multipart/form-data')
        return attributes

    @property
    def action(self):
        request = WebExecutionContext.get_context().request
        action = self.event_channel.get_url()
        action.query = request.query_string
        action.make_network_relative()
        return six.text_type(action)
    
    def register_input(self, input_widget):
        assert input_widget not in self.inputs.values(), 'Cannot register the same input twice to this form' #xxx
        proposed_name = input_widget.make_name('')
        name = proposed_name
        clashing_names_count = self.registered_input_names.setdefault(proposed_name, 0)
        if clashing_names_count > 0:
            name = input_widget.make_name(six.text_type(clashing_names_count))
        self.registered_input_names[proposed_name] += 1
        self.inputs[name] = input_widget
        return name

    @property
    def channel_name(self):
        return self.event_channel.name

    @property
    def persisted_exception_class(self):
        config = WebExecutionContext.get_context().config
        return config.web.persisted_exception_class
    @property
    def persisted_userinput_class(self):
        config = WebExecutionContext.get_context().config
        return config.web.persisted_userinput_class
    @property
    def persisted_file_class(self):
        config = WebExecutionContext.get_context().config
        return config.web.persisted_file_class
        
    @property 
    def exception(self):
        """The :class:`reahl.component.exceptions.DomainException` which occurred, if any."""
        return self.persisted_exception_class.get_exception_for_form(self)

    def persist_exception(self, exception):
        self.clear_exception()
        self.persisted_exception_class.new_for_form(self, exception=exception)

    def clear_exception(self):
        self.persisted_exception_class.clear_for_form(self)

    def persist_input(self, input_values):
        self.clear_saved_inputs()
        for input_widget in self.inputs.values():
            input_widget.persist_input(input_values)

    def clear_saved_inputs(self):
        self.persisted_userinput_class.clear_for_form(self)
        self.persisted_exception_class.clear_for_all_inputs(self)
        
    def clear_uploaded_files(self):
        self.persisted_file_class.clear_for_form(self)

    def cleanup_after_exception(self, input_values, ex):
        self.persist_input(input_values)
        self.persist_exception(ex)
        
    def cleanup_after_success(self):
        self.clear_saved_inputs()
        self.clear_exception()
        self.clear_uploaded_files()

    def handle_form_input(self, input_values):
        exception = None
        events = set()
        for input_widget in self.inputs.values():
            try:
                input_widget.accept_input(input_values)
            except ValidationConstraint as ex:
                exception = ex
            events.add(input_widget.get_ocurred_event())
        if exception:
            raise ValidationException()
        events -= {None}
        input_detail = 'Inputs submitted: %s Events detected: %s' % (list(input_values.keys()), list(events))
        if len(events) == 0:
            raise ProgrammerError('Could not detect event. Did the browser submit the button? %s' % input_detail)
        if len(events) > 1:
            raise ProgrammerError('More than one event detected in form submission. %s' % input_detail)
        return events.pop()

    javascript_widget_name = 'form'
    def get_js(self, context=None):
        js = ['$(%s).%s(%s);' % (self.jquery_selector, self.javascript_widget_name, self.get_js_options())]
        return super(Form, self).get_js(context=context) + js 

    def get_js_options(self):
        return ''

    @property
    def jquery_selector(self):
        return '"form[id=%s]"' % self.css_id


class NestedForm(Div):
    """A NestedForm can create the appearance of one Form being visually contained in
       another. Forms are not allowed to be children of other Forms but this restriction does 
       not apply to NestedForms. 

       .. admonition:: Styling
       
          Rendered as an HTML <div class="reahl-nested-form"> element.

       :param view: (See :class:`reahl.web.fw.Widget`)
       :param unique_name: (See :class:`Form`)
       :keyword css_id: (See :class:`reahl.web.ui.HTMLElement`)
       
    """
    def __init__(self, view, unique_name, css_id=None):
        self.out_of_bound_form = self.create_out_of_bound_form(view, unique_name)
        super(NestedForm, self).__init__(view, css_id='%s_nested' % self.out_of_bound_form.css_id)
        self.add_to_attribute('class', ['reahl-nested-form'])
        self.set_id(self.css_id)
        view.add_out_of_bound_form(self.out_of_bound_form)

    @property
    def form(self):
        return self.out_of_bound_form

    def create_out_of_bound_form(self, view, unique_name):
        return Form(view, unique_name, rendered_form=self)

    
class FieldSet(HTMLElement):
    """A visual grouping of HTMLElements inside a Form.

       .. admonition:: Styling

          Rendered as an HTML <fieldset> element.
    
       :param view: (See :class:`reahl.web.fw.Widget`)
       :keyword label_text: If given, the FieldSet will have a label containing this text.
       :keyword legend_text: If given, the FieldSet will have a Legend containing this text.
       :keyword css_id: (See :class:`reahl.web.ui.HTMLElement`)

       .. versionchanged: 3.2
          Deprecated label_text and instead added legend_text: FieldSets should have Legends, not Labels.
    """
    def __init__(self, view, legend_text=None, label_text=None, css_id=None):
        super(FieldSet, self).__init__(view, 'fieldset', children_allowed=True, css_id=css_id)
        if label_text:
            warnings.warn('DEPRECATED: label_text=. Please use legend_text= instead.',
                          DeprecationWarning, stacklevel=1)
            self.label = self.add_child(Label(view, text=label_text))
        if legend_text:
            self.legend = self.add_child(Legend(view, text=legend_text))


class Legend(HTMLElement):
    """A caption for an :class:`reahl.web.ui.HTMLElement`.

    .. versionadded: 3.2

    .. admonition:: Styling

       Rendered as an HTML <legend> element.
    
    :param view: (See :class:`reahl.web.fw.Widget`)
    :keyword text: If given, the Legend containing this text.
    :keyword css_id: (See :class:`reahl.web.ui.HTMLElement`)
       
    """
    def __init__(self, view, text=None, css_id=None):
        super(Legend, self).__init__(view, 'legend', children_allowed=True, css_id=css_id)
        if text:
            self.text_node = self.add_child(TextNode(view, text))
            

#PendingMove: In future this class may be renamed to: reahl.web.attic.layout:InputGroup
class InputGroup(FieldSet):
    __doc__ = FieldSet.__doc__


class DelegatedAttributes(object):
    def set_attributes(self, attributes):
        pass


class AccessRightAttributes(DelegatedAttributes):
    def __init__(self, widget, disabled_class='disabled'):
        super(AccessRightAttributes, self).__init__()
        self.widget = widget
        self.disabled_class = disabled_class

    @property
    def disabled(self):
        return self.widget.disabled

    def set_attributes(self, attributes):
        super(AccessRightAttributes, self).set_attributes(attributes)

        if self.disabled and self.disabled_class:
            attributes.add_to('class', [self.disabled_class])


class ValidationStateAttributes(DelegatedAttributes):
    def __init__(self, input_widget, error_class='error', success_class='valid'):
        super(ValidationStateAttributes, self).__init__()
        self.input_widget = input_widget
        self.error_class = error_class
        self.success_class = success_class

    @property
    def has_validation_error(self):
        return self.input_widget.get_input_status() == 'invalidly_entered'

    @property
    def is_validly_entered(self):
        return self.input_widget.get_input_status() == 'validly_entered'

    @property
    def wrapped_html_input(self):
        return self.input_widget.wrapped_html_widget

    @property
    def view(self):
        return self.input_widget.view
        
    def set_attributes(self, attributes):
        super(ValidationStateAttributes, self).set_attributes(attributes)

        if self.has_validation_error and self.error_class:
            attributes.add_to('class', [self.error_class]) 
        elif self.is_validly_entered and self.success_class:
            attributes.add_to('class', [self.success_class]) 



class HTMLWidget(Widget):
    def __init__(self, view, read_check=None, write_check=None):
        super(HTMLWidget, self).__init__(view, read_check=read_check, write_check=write_check)
        self.html_representation = None

    def enable_refresh(self, *for_fields):
        self.html_representation.query_fields.update(self.query_fields)
        self.html_representation.enable_refresh(*for_fields)
        
    def set_html_representation(self, widget):
        self.html_representation = widget
        
    def append_class(self, css_class):
        """Adds the word `css_class` to the "class" attribute of the HTMLElement which represents this Widget in HTML to the user."""
        self.html_representation.append_class(css_class)

    @property
    def css_id_is_set(self):
        """Returns True if the "id" attribute of the HTMLElement which represents this Widget in HTML is set."""
        return self.html_representation.css_id_is_set
        
    @property
    def css_id(self):
        """Returns the "id" attribute of the HTMLElement which represents this Widget in HTML."""
        return self.html_representation.css_id

    def set_id(self, value):
        """Set the "id" attribute of the HTMLElement which represents this Widget in HTML to the user."""
        self.html_representation.set_id(value)

    def set_title(self, value):
        """Set the the "title" attribute of the HTMLElement which represents this Widget in HTML to the user."""
        self.html_representation.set_title(value)

    def add_to_attribute(self, name, values):
        """Ensures that the value of the attribute `name` of the HTMLElement which represents this Widget in
           HTML to the user includes the words listed in `values` (a list of strings).
        """
        self.html_representation.add_to_attribute(name, values)

    def set_attribute(self, name, value):
        """Sets the value of the attribute `name` of the HTMLElement which represents this Widget in HTML to the user
           to the string `value`.
        """
        self.html_representation.set_attribute(name, value)

    def add_attribute_source(self, attribute_source):
        return self.html_representation.add_attribute_source(attribute_source)



class Input(HTMLWidget):
    """A Widget that proxies data between a user and the web application.

       :param form: The :class:`Form` with which this Input is associated.
       :param bound_field: The :class:`reahl.component.modelinterface.Field` which validates and marshalls user
                     input given via this Input.
    """
    is_Input = True

    @arg_checks(form=IsInstance(Form), bound_field=IsInstance(Field))
    def __init__(self, form, bound_field):
        self.form = form
        self.bound_field = bound_field
        super(Input, self).__init__(form.view, read_check=bound_field.can_read, write_check=bound_field.can_write)

    def can_write(self):
        return (not self.write_check) or self.write_check()

    @property
    def validation_error(self):
        return self.bound_field.validation_error

    @property
    def label(self):
        return self.bound_field.label

    @property
    def required(self):
        return self.bound_field.required

    @property
    def value(self):
        if self.get_input_status() == 'defaulted' or self.disabled:
            return self.bound_field.as_input()
        return self.bound_field.user_input

    def get_input_status(self):
        return self.bound_field.input_status

    @property
    def includes_label(self):
        """If True, the Label of this Input forms part of the input itself."""
        return False




class WrappedInput(Input):
    def __init__(self, input_widget):
        super(WrappedInput, self).__init__(input_widget.form, input_widget.bound_field)
        self.input_widget = input_widget

    @property
    def name(self):
        return self.input_widget.name

    @property
    def includes_label(self):
        return self.input_widget.includes_label

    @property
    def html_control(self):
        return self.input_widget.html_control
        

class PrimitiveInput(Input):
    is_for_file = False
    append_error = True
    registers_with_form = True
    add_default_attribute_source = True
    
    def __init__(self, form, bound_field, name=None):
        super(PrimitiveInput, self).__init__(form, bound_field)
        self.name = name
        if self.registers_with_form:
            self.name = form.register_input(self) # bound_field must be set for this registration to work
        
        self.prepare_input()

        html_widget = None
        if (type(self) is not PrimitiveInput) and ('create_html_input' in type(self).__dict__):
            warnings.warn('DEPRECATED: %s. %s' % (self.create_html_input, 'Please use .create_html_widget instead.'),
                          DeprecationWarning, stacklevel=5)
            html_widget = self.create_html_input()
        self.set_html_representation(self.add_child(html_widget or self.create_html_widget()))

        if self.append_error and (self.get_input_status() == 'invalidly_entered'):
            label = Label(self.view, text=self.validation_error.message, for_input=self)
            label.append_class('error')
            self.add_child(label)

    def __str__(self):
        return '<%s name=%s>' % (self.__class__.__name__, self.name)

    @property
    def html_control(self):
        return self.html_representation

    @deprecated('Please override create_html_widget() instead', '3.2')
    def create_html_input(self):
        """Override this in subclasses to create the HTMLElement that represents this Input in HTML to the user."""
        pass

    def create_html_widget(self):
        """Override this in subclasses to create the HTMLElement that represents this Input in HTML to the user.
           .. versionadded: 3.2
        """
        html_widget = HTMLElement(self.view, 'input')
        if self.add_default_attribute_source:
            html_widget.add_attribute_source(ValidationStateAttributes(self))
        if self.name:
            html_widget.set_attribute('name', self.name)
        if self.disabled:
            html_widget.set_attribute('disabled', 'disabled')
        return html_widget

    def make_name(self, discriminator):
        return '%s%s' % (self.bound_field.variable_name, discriminator)

    @property
    def channel_name(self):
        return self.form.channel_name

    @property
    def jquery_selector(self):
        return '''$('input[name=%s][form="%s"]')''' % (self.name, self.form.css_id)

    def validate_input(self, input_values):
        value = self.get_value_from_input(input_values)
        self.bound_field.set_user_input(value)

    def format_input(self, input_values):
        value = self.get_value_from_input(input_values)
        try:
            return self.bound_field.format_input(value)
        except InputParseException:
            return ''

    def accept_input(self, input_values):
        value = self.get_value_from_input(input_values)
        self.bound_field.from_input(value)

    def get_ocurred_event(self):
        return None

    def get_value_from_input(self, input_values):
        """Obtains the value received for this Input from the browser, given a :class:`cgi.FieldStorage`
           containing name, value pairs of user input as sent by the browser.
           Override this method if your Input needs special handling to obtain its value.
        """
        try:
            return input_values[self.name]
        except KeyError:
            if self.disabled:
                return ''
            raise ProgrammerError('Could not find a value for expected input %s (named %s) on form %s' % \
                                  (self, self.name, self.form))

    @property
    def persisted_userinput_class(self):
        return self.form.persisted_userinput_class

    def prepare_input(self):
        previously_entered_value = None
        if self.registers_with_form:
            previously_entered_value = self.persisted_userinput_class.get_previously_entered_for_form(self.form, self.name)

        if previously_entered_value is not None:
            self.bound_field.set_user_input(previously_entered_value, ignore_validation=True)
        else:
            self.bound_field.clear_user_input()

    def persist_input(self, input_values):
        input_value = self.get_value_from_input(input_values)
        self.enter_value(input_value)

    def enter_value(self, input_value):
        if self.registers_with_form:
            self.persisted_userinput_class.save_input_value_for_form(self.form, self.name, input_value)


class InputTypeInput(PrimitiveInput):
    render_value_attribute = True
    def __init__(self, form, bound_field, input_type, name=None):
        self.input_type = input_type
        super(InputTypeInput, self).__init__(form, bound_field, name=name)

    def create_html_widget(self):
        html_widget = super(InputTypeInput, self).create_html_widget()
        html_widget.set_attribute('type', self.input_type)
        html_widget.set_attribute('form', self.form.css_id)
        if self.render_value_attribute:
            html_widget.set_attribute('value', self.value)
        self.add_validation_constraints_to(html_widget)
        return html_widget

    def validation_constraints_to_render(self):
        return self.bound_field.validation_constraints

    def add_validation_constraints_to(self, html_widget):
        validation_constraints = self.validation_constraints_to_render()
        html5_validations = ['pattern', 'required', 'maxlength', 'minlength', 'accept', 'minvalue', 'maxvalue', 'remote']
        for validation_constraint in validation_constraints:
            if validation_constraint.is_remote:
                html_widget.set_attribute(validation_constraint.name, six.text_type(self.form.field_validator.get_url()))
            elif validation_constraint.name in html5_validations:
                html_widget.set_attribute(validation_constraint.name, validation_constraint.parameters)
            elif validation_constraint.name != '':
                html_widget.set_attribute('data-%s' % validation_constraint.name, validation_constraint.parameters or 'true')
        def map_name(name):
            if name in html5_validations:
                return name
            else:
                return 'data-%s' % name
        error_messages = validation_constraints.as_json_messages(map_name, ['', RemoteConstraint.name])
        if error_messages:
            html_widget.set_attribute('class', error_messages)
        try:
            title = validation_constraints.get_constraint_named('pattern').message
            html_widget.set_attribute('title', validation_constraints.get_constraint_named('pattern').message)
        except ConstraintNotFound:
            pass


class TextArea(PrimitiveInput):
    """A muli-line Input for plain text.

       .. admonition:: Styling

          Represented in HTML as a <textarea> element.

       :param form: (See :class:`~reahl.web.ui.Input`)
       :param bound_field: (See :class:`~reahl.web.ui.Input`)
       :param rows: The number of rows that this Input should have.
       :param columns: The number of columns that this Input should have.
    """
    def __init__(self, form, bound_field, rows=None, columns=None):
        self.rows = rows
        self.columns = columns
        super(TextArea, self).__init__(form, bound_field)

    def create_html_widget(self):
        html_text_area = HTMLElement(self.view, 'textarea', children_allowed=True)
        if self.add_default_attribute_source:
            html_text_area.add_attribute_source(ValidationStateAttributes(self))
        html_text_area.set_attribute('name', self.name)
        if self.disabled:
            html_text_area.set_attribute('disabled', 'disabled')


        self.text = html_text_area.add_child(TextNode(self.view, self.get_value))

        if self.rows:
            html_text_area.set_attribute('rows', six.text_type(self.rows))
        if self.columns:
            html_text_area.set_attribute('cols', six.text_type(self.columns))

        return html_text_area

    def get_value(self):
        return self.value


class Option(PrimitiveInput):
    registers_with_form = False
    def __init__(self, select_input, choice):
        self.choice = choice
        self.select_input = select_input
        super(Option, self).__init__(select_input.form, select_input.bound_field)

    @property
    def label(self):
        return self.choice.label

    @property
    def value(self):
        return self.choice.as_input()

    @property
    def selected(self):
        if self.bound_field.allows_multiple_selections:
            return self.value in self.select_input.value
        else:
            return self.value == self.select_input.value
    
    def create_html_widget(self):
        option = HTMLElement(self.view, 'option', children_allowed=True)
        option.add_child(TextNode(self.view, self.label))
        option.set_attribute('value', self.value)
        if self.selected:
            option.set_attribute('selected', 'selected')
        return option



class OptGroup(HTMLElement):
    def __init__(self, view, label, options, css_id=None):
        super(OptGroup, self).__init__(view, 'optgroup', children_allowed=True, css_id=css_id)
        self.set_attribute('label', label)
        for option in options:
            self.add_child(option)


class SelectInput(PrimitiveInput):
    """An Input that lets the user select an :class:`reahl.component.modelinterface.Choice` from a dropdown
       list of valid ones.

       .. admonition:: Styling

          Represented in HTML as a <select> element which can contain <option> and <optgroup> children.

       :param form: (See :class:`~reahl.web.ui.Input`)
       :param bound_field: (See :class:`~reahl.web.ui.Input`)
    """
    def create_html_widget(self):
        html_select = HTMLElement(self.view, 'select', children_allowed=True)
        if self.add_default_attribute_source:
            html_select.add_attribute_source(ValidationStateAttributes(self))
        html_select.set_attribute('name', self.name)
        if self.disabled:
            html_select.set_attribute('disabled', 'disabled')

        for choice_or_group in self.bound_field.grouped_choices:
            options = [Option(self, choice) for choice in choice_or_group.choices]
            if isinstance(choice_or_group, Choice):
                html_select.add_children(options)
            else:
                html_select.add_child(OptGroup(self.view, choice_or_group.label, options))

        html_select.set_attribute('form', self.form.css_id)
        if self.bound_field.allows_multiple_selections:
            html_select.set_attribute('multiple', 'multiple')

        return html_select

    def is_selected(self, choice):
        if self.bound_field.allows_multiple_selections:
            return choice.as_input() in self.value
        else:
            return self.value == choice.as_input()

    def get_value_from_input(self, input_values):
        if self.bound_field.allows_multiple_selections:
            return input_values.get(self.name, '')
        else:
            return super(SelectInput, self).get_value_from_input(input_values)


class SingleRadioButton(InputTypeInput):
    registers_with_form = False

    def __init__(self, radio_button_input, choice):
        self.choice = choice
        self.radio_button_input = radio_button_input
        super(SingleRadioButton, self).__init__(radio_button_input.form, radio_button_input.bound_field, 
                                                'radio', name=radio_button_input.name)

    def create_html_widget(self):
        span = Span(self.view)
        span.set_attribute('class', 'reahl-radio-button')
        span.add_child(self.create_button_input())
        span.add_child(TextNode(self.view, self.label))
        return span

    @property
    def html_control(self):
        return self.html_representation.children[0]

    def create_button_input(self):
        button = super(SingleRadioButton, self).create_html_widget()
        if self.checked:
            button.set_attribute('checked', 'checked')
        return button

    @property
    def label(self):
        return self.choice.label

    @property
    def value(self):
        return self.choice.as_input()

    @property
    def checked(self):
        return self.radio_button_input.value == self.value



class RadioButtonInput(PrimitiveInput):
    """An Input that lets the user select an :class:`reahl.component.modelinterface.Choice` from a list of valid ones
       shown as radio buttons.

       .. admonition:: Styling

          Represented in HTML as a <div class="reahl-radio-button-input"> element which
          contains an <input type="radio">, wrapped in a <span class="reahl-radio-button"> for each valid
          :class:`reahl.component.modelinterface.Choice`.

       :param form: (See :class:`~reahl.web.ui.Input`)
       :param bound_field: (See :class:`~reahl.web.ui.Input`)
    """

    def create_html_widget(self):
        main_element = self.create_main_element()
        main_element.append_class('reahl-radio-button-input')
        for choice in self.bound_field.flattened_choices:
            self.add_button_for_choice_to(main_element, choice)
        return main_element

    @property
    def html_control(self):
        return None

    def get_value_from_input(self, input_values):
        return input_values.get(self.name, '')

    def create_main_element(self):
        return Div(self.view)

    def add_button_for_choice_to(self, widget, choice):
        widget.add_child(SingleRadioButton(self, choice))



# Uses: reahl/web/reahl.textinput.js
class TextInput(InputTypeInput):
    """A single line Input for typing plain text.

       .. admonition:: Styling

          Represented in HTML by an <input type="text" class="reahl-textinput"> element.

       :param form: (See :class:`~reahl.web.ui.Input`)
       :param bound_field: (See :class:`~reahl.web.ui.Input`)
       :keyword fuzzy: If True, the typed input will be dealt with as "fuzzy input". Fuzzy input is
                     when a user is allowed to type almost free-form input for structured types of input,
                     such as a date. The assumption is that the `bound_field` used should be able to parse
                     such "fuzzy input". If fuzzy=True, the typed value will be changed on the fly to
                     the system's interpretation of what the user originally typed as soon as the TextInput
                     looses focus.
       :keyword placeholder: If given a string, placeholder is displayed in the TextInput if the TextInput 
                     is empty in order to provide a hint to the user of what may be entered into the TextInput. 
                     If given True instead of a string, the label of the TextInput is used.

       .. versionchanged:: 3.2
          Added `placeholder`.
    """
    def __init__(self, form, bound_field, fuzzy=False, placeholder=False):
        super(TextInput, self).__init__(form, bound_field, 'text')
        self.append_class('reahl-textinput')
        if placeholder:
            placeholder_text = self.label if placeholder is True else placeholder
            self.set_attribute('placeholder', placeholder_text)

        if fuzzy:
            self.append_class('fuzzy')

    def get_js(self, context=None):
        js = ['$(%s).textinput();' % self.html_representation.contextualise_selector('".reahl-textinput"', context)]
        return super(TextInput, self).get_js(context=context) + js



class PasswordInput(InputTypeInput):
    """A PasswordInput is a single line text input, but it does not show what the user is typing.

       .. admonition:: Styling

          Represented in HTML by a <input type="password"> element.

       :param form: (See :class:`~reahl.web.ui.Input`)
       :param bound_field: (See :class:`~reahl.web.ui.Input`)
    """
    render_value_attribute = False
    def __init__(self, form, bound_field):
        super(PasswordInput, self).__init__(form, bound_field, 'password')


class CheckboxInput(InputTypeInput):
    """A checkbox.

       .. admonition:: Styling

          Represented in HTML by an <input type="checkbox"> element.

       :param form: (See :class:`~reahl.web.ui.Input`)
       :param bound_field: (See :class:`~reahl.web.ui.Input`)
    """
    render_value_attribute = False
    def __init__(self, form, bound_field):
        super(CheckboxInput, self).__init__(form, bound_field, 'checkbox')

    def create_html_widget(self):
        checkbox_widget = super(CheckboxInput, self).create_html_widget()
        if self.value == self.bound_field.true_value:
            checkbox_widget.set_attribute('checked', 'checked')
        return checkbox_widget
        
    def validation_constraints_to_render(self):
        applicable_constraints = ValidationConstraintList()
        if self.required:
            validation_constraints = super(CheckboxInput, self).validation_constraints_to_render()
            validation_constraint = validation_constraints.get_constraint_named('required')
            applicable_constraints.append(validation_constraint)
        return applicable_constraints

    def get_value_from_input(self, input_values):
        if self.name in input_values:
            return self.bound_field.true_value
        return self.bound_field.false_value




class ButtonInput(PrimitiveInput):
    def __init__(self, form, event):
        super(ButtonInput, self).__init__(form, event)
        if not self.controller.has_event_named(event.name):
            raise ProgrammerError('no Event/Transition available for name %s' % event.name)
        try:
            event.validate_default()
        except ValidationConstraint as ex:
            message = 'Arguments for %s are not valid: %s' % (event, ex)
            message += '\n(did you forget to call .with_arguments() on an Event sent to a ButtonInput?)'
            raise ProgrammerError(message)

    def create_html_widget(self):
        html_widget = super(ButtonInput, self).create_html_widget()
        html_widget.set_attribute('type', 'submit')
        html_widget.set_attribute('form', self.form.css_id)
        html_widget.set_attribute('value', self.value)
        return html_widget

    def is_event(self, input_name):
        return input_name.find('?') > 0

    def canonicalise_input(self, input_name):
        [name_part, query_part] = input_name.split('?')
        if self.name.startswith('%s?' % name_part):
            incoming_arguments = '?%s' % query_part
            canonical_input = self.bound_field.unparse_input(self.bound_field.parse_input(incoming_arguments))
            return '%s%s' % (name_part, canonical_input)
        return None

    def get_value_from_input(self, input_values):
        canonicalised_inputs = [self.canonicalise_input(i) for i in input_values.keys()
                                                           if self.is_event(i)]

        if self.name in canonicalised_inputs:
            return self.query_encoded_arguments
        else:
            return ''

    @property
    def query_encoded_arguments(self):
        return self.bound_field.as_input() or '?'

    def make_name(self, discriminator):
        return 'event.%s%s%s' % (self.bound_field.name, discriminator, self.query_encoded_arguments)

    @property
    def label(self):
        return self.bound_field.label

    @property
    def value(self):
        return self.label

    def get_ocurred_event(self):
        if self.bound_field.occurred:
            return self.bound_field
        return None


#PendingMove: In future this class may be renamed to: reahl.web.attic.layout:Button instead
class Button(Span):
    """A button.

       .. admonition:: Styling

          Represented in HTML by an <input type="submit"> element, wrapped in a <span class="reahl-button">.

       :param form: (See :class:`~reahl.web.ui.Input`)
       :param event: The :class:`~reahl.web.component.modelinterface.Event` that will fire when the user clicks on this ButtonInput.
       :keyword css_id: (See :class:`reahl.web.ui.HTMLElement`)

    """
    def __init__(self, form, event, css_id=None):
        super(Button, self).__init__(form.view, css_id=css_id)
        self.html_input = self.add_child(ButtonInput(form, event))

    @property
    def attributes(self):
        attributes = super(Button, self).attributes
        attributes.add_to('class', ['reahl-button'])
        return attributes


class Label(HTMLElement):
    """A label for an Input.

       If `for_input` is given, the Label will only be visible if for_input is visible.

       .. admonition:: Styling

          Rendered as an HTML <label> element.

       :param view: (See :class:`reahl.web.fw.Widget`)
       :keyword text: If given, used as the text for the label.
       :keyword for_input: If given, the :class:`~reahl.web.ui.Input` to which this Label applies (its `.label` is also used as text).
       :keyword css_id: (See :class:`reahl.web.ui.HTMLElement`)

       .. versionchanged:: 3.2
          Added the for_input keyword argument.
    """
    def __init__(self, view, text=None, for_input=None, css_id=None):
        super(Label, self).__init__(view, 'label', children_allowed=True, css_id=css_id)
        self.for_input = for_input
        if self.for_input and self.for_input.html_control and not self.for_input.html_control.css_id_is_set:
            self.for_input.html_control.set_id('tmpid-%s-%s' % (id(self), time.time()))
        if text or for_input:
            self.text_node = self.add_child(TextNode(view, text or for_input.label))

    @property
    def visible(self):
        if self.for_input:
            return self.for_input.visible
        else:
            return super(Label, self).visible

    @property
    def attributes(self):
        attributes = super(Label, self).attributes
        if self.for_input and self.for_input.html_control:
            attributes.set_to('for', self.for_input.html_control.css_id)
        return attributes


@deprecated('Please use Label(for_input=) instead.', '3.2')
class InputLabel(Label):
    """A label for the Input given in `html_input`.

       .. admonition:: Styling

          Rendered as an HTML <label> element.

       :param html_input: The :class:`~reahl.web.ui.Input` labelled by this Label.
       :keyword text: If given, used as the text for the label rather than the default value (`html_input.label`).
       :keyword css_id: (See :class:`reahl.web.ui.HTMLElement`)

    """
    def __init__(self, html_input, text=None, css_id=None):
        super(InputLabel, self).__init__(html_input.view, text=text, for_input=html_input, css_id=css_id)



@deprecated('Please use Label() instead, and add css class error', '3.2')
class ErrorLabel(Label):
    def __init__(self, html_input, text=None, css_id=None):
        super(ErrorLabel, self).__init__(html_input.view, text=text, for_input=html_input, css_id=css_id)
    """If an :class:`~reahl.web.ui.Input` fails validation, an ErrorLabel is automatically rendered after it containing
       the specific validation error message.

       .. admonition:: Styling

          Rendered as an HTML <label class="error"> element.

       :param html_input: The :class:`~reahl.web.ui.Input` labelled by this Label.
       :keyword text: If given, used as the text for the label rather than the default value (`html_input.label`).
       :keyword css_id: (See :class:`reahl.web.ui.HTMLElement`)

    """
    @property
    def attributes(self):
        attributes = super(ErrorLabel, self).attributes
        attributes.add_to('class', ['error'])
        return attributes


#PendingMove: In future this class may be renamed to: reahl.web.attic.layout:LabelledInlineInput instead
# Uses: reahl/web/reahl.labelledinput.css
class LabelledInlineInput(Span):
    """A Widget that wraps around a given Input, adding a Label to the Input. Adheres to text flow.

       .. admonition:: Styling

          Rendered as a <span class="reahl-labelledinput"> containing the <label> followed by
          another <span> which contains the `html_input`. If the current input is not valid, it will also have
          class reahl-state-error.

       :param html_input: (See :class:`InputLabel`)
       :param css_id: (See :class:`reahl.web.ui.HTMLElement`)
    """
    def __init__(self, html_input, css_id=None):
        view = html_input.view
        super(LabelledInlineInput, self).__init__(view, css_id=css_id)
        self.label = self.add_child(self.make_label(html_input))
        self.inner_span = self.add_child(Span(view))
        self.html_input = self.inner_span.add_child(html_input)

    def make_label(self, for_input):
        return Label(self.view, for_input=for_input)

    @property
    def visible(self):
        return self.html_input.visible

    @property
    def attributes(self):
        attributes = super(LabelledInlineInput, self).attributes
        attributes.add_to('class', ['reahl-labelledinput'])
        if self.html_input.get_input_status() == 'invalidly_entered':
            attributes.add_to('class', ['reahl-state-error'])
        return attributes


#PendingMove: In future this class may be renamed to: reahl.web.attic.layout:LabelledBlockInput
# Uses: reahl/web/reahl.labelledinput.css
class LabelledBlockInput(Div):
    """A Widget that wraps around a given Input, adding a Label to the Input. Labels and their corresponding Inputs
       are arranged in columns. Successive LabelledBlockInputs are positioned underneath one another. This has the
       effect that the Labels and Inputs of successive LabelledBlockInputs line up.

       .. admonition:: Styling

          Rendered as a <div class="reahl-labelledinput"> containing two <div> elements: one with the Label
          in it, and the other with `html_input` itself. If the current input is not valid, it will also have
          class reahl-state-error.

       :param html_input: (See :class:`InputLabel`)
       :param css_id: (See :class:`reahl.web.ui.HTMLElement`)
    """
    def __init__(self, html_input, css_id=None):
        view = html_input.view
        super(LabelledBlockInput, self).__init__(view, css_id=css_id)
        self.html_input = html_input

        if YuiGridsCss.is_enabled():
            self.append_class('yui-g')
            self.label_part = self.add_child(YuiUnit(view, first=True))
            self.input_part = self.add_child(YuiUnit(view))
        else:
            from reahl.web.pure import ColumnLayout, UnitSize
            self.use_layout(ColumnLayout(('label', UnitSize('1/4')), ('input', UnitSize('3/4'))))
            self.label_part = self.layout.columns['label']
            self.input_part = self.layout.columns['input']

        self.label = self.label_part.add_child(Label(self.view, for_input=html_input))
        self.input_part.add_child(html_input)

    @property
    def visible(self):
        return self.html_input.visible

    @property
    def attributes(self):
        attributes = super(LabelledBlockInput, self).attributes
        attributes.add_to('class', ['reahl-labelledinput'])
        if self.html_input.get_input_status() == 'invalidly_entered':
            attributes.add_to('class', ['reahl-state-error'])
        return attributes


#PendingMove: In future this class may be renamed to: reahl.web.attic.layout:CueInput instead
# Uses: reahl/web/reahl.cueinput.js
class CueInput(Div):
    """A Widget that wraps around a given Input, adding a Label to the Input and a "cue" - a hint that
       appears only when the Input has focus. The intention of the cue is to give the user a hint as to
       what to input into the Input.

       Successive CueInputs are arranged underneath each other, with their labels, Inputs and Cue's lined up.

       .. admonition:: Styling

          Rendered as a <div class="reahl-cueinput reahl-labelledinput"> containing two <div> elements: one with the Label
          in it, and the other with two more <div> elements. The first of these contains the `html_input` itself. The
          last contains the `cue_widget`. If the current input is not valid, it will also have
          class reahl-state-error.

       :param html_input: (See :class:`InputLabel`)
       :param css_id: (See :class:`reahl.web.ui.HTMLElement`)
    """
    def __init__(self, html_input, cue_widget, css_id=None):
        view = html_input.view
        super(CueInput, self).__init__(view, css_id=css_id)
        self.html_input = html_input

        if YuiGridsCss.is_enabled():
            self.append_class('yui-g')
            self.label_part = self.add_child(YuiUnit(view, first=True))
            self.input_wrapper = self.add_child(YuiGrid(view))
            self.input_part = self.input_wrapper.add_child(YuiUnit(view, first=True))
            self.cue_part = self.input_wrapper.add_child(YuiUnit(view))
        else:
            from reahl.web.pure import ColumnLayout, UnitSize
            self.use_layout(ColumnLayout(('label', UnitSize('1/4')), ('input', UnitSize('1/2')), ('cue', UnitSize('1/4'))))
            self.label_part = self.layout.columns['label']
            self.input_part = self.layout.columns['input']
            self.cue_part = self.layout.columns['cue']

        self.label = self.label_part.add_child(Label(self.view, for_input=html_input))
        self.input_part.add_child(self.html_input)
        self.cue_part.append_class('reahl-cue')
        self.cue_part.add_child(cue_widget)
        cue_widget.set_attribute('hidden', 'true')


    @property
    def visible(self):
        return self.html_input.visible

    @property
    def attributes(self):
        attributes = super(CueInput, self).attributes
        attributes.add_to('class', ['reahl-cueinput', 'reahl-labelledinput'])
        if self.html_input.get_input_status() == 'invalidly_entered':
            attributes.add_to('class', ['reahl-state-error'])
        return attributes

    def get_js(self, context=None):
        js = ['$(%s).cueinput();' % self.contextualise_selector('".reahl-cueinput"', context)]
        return super(CueInput, self).get_js(context=context) + js


#PendingMove: In future this class may be renamed to: reahl.web.attic.layout:LabelOverInput instead
# Uses: reahl/web/reahl.labeloverinput.js
# Uses: reahl/web/reahl.labeloverinput.css
class LabelOverInput(LabelledInlineInput):
    """A :class:`LabelledInlineWidget` that shows the Label superimposed over the Input itself.
       The label is only visible while the Input is empty.

       .. admonition:: Styling

          Rendered like a :class:`LabelledInlineWidget` with reahl-labeloverinput appended to the class
          of the containing <div> element.

       :param html_input: (See :class:`InputLabel`)
       :param css_id: (See :class:`reahl.web.ui.HTMLElement`)
    """
    @property
    def attributes(self):
        attributes = super(LabelOverInput, self).attributes
        attributes.add_to('class', ['reahl-labeloverinput'])
        return attributes

    def make_label(self, for_input):
        class AutoHideLabel(Label):
            @property
            def attributes(self):
                attributes = super(AutoHideLabel, self).attributes
                if self.for_input.value != '':
                    attributes.set_to('hidden', 'true')
                return attributes
        return AutoHideLabel(self.view, for_input=for_input)

    def get_js(self, context=None):
        js = ['$(%s).labeloverinput();' % self.contextualise_selector('".reahl-labeloverinput"', context)]
        return super(LabelOverInput, self).get_js(context=context) + js


class ActiveStateAttributes(DelegatedAttributes):
    def __init__(self, widget, active_class='active', inactive_class=None):
        super(ActiveStateAttributes, self).__init__()
        self.widget = widget
        self.active_class = active_class
        self.inactive_class = inactive_class

    def set_attributes(self, attributes):
        super(ActiveStateAttributes, self).set_attributes(attributes)

        if self.widget.is_active and self.active_class:
            attributes.add_to('class', [self.active_class])
        elif not self.widget.is_active and self.inactive_class:
            attributes.add_to('class', [self.inactive_class])


#PendingMove: In future this class may be renamed to: reahl.web.attic.menu:MenuItem instead
class MenuItem(object):
    """One item in a Menu.

       .. admonition:: Styling

          Rendered as a <li> element. When active, includes class="active".

       Normally, a programmer would not instantiate this class directly, rather use :meth:`MenuItem.from_bookmark`.

       :param view: (See :class:`reahl.web.fw.Widget`)
       :param a: The :class:`A` to use as link.
       :keyword active_regex: If the href of `a` matches this regex, the MenuItem is deemed active.
       :keyword exact_match: (See :meth:`reahl.web.fw.Url.is_currently_active`)
       :keyword css_id: (See :class:`reahl.web.ui.HTMLElement`)

       .. versionchanged:: 3.2
          Deprecated css_id keyword argument.
    """
    @classmethod
    def from_bookmark(cls, view, bookmark, active_regex=None):
        """Creates a MenuItem from a given Bookmark.

          :param view: (See :class:`reahl.web.fw.Widget`)
          :param bookmark: The :class:`reahl.web.fw.Bookmark` for which to create the MenuItem.
          :param active_regex: (See :class:`MenuItem`)
        """
        return cls(view, A.from_bookmark(view, bookmark), active_regex=active_regex, exact_match=bookmark.exact)

    def __init__(self, view, a, active_regex=None, exact_match=False, css_id=None):
        super(MenuItem, self).__init__()
        self.view = view
        self.exact_match = exact_match
        self.a = a
        self.widget = None
        self.active_regex = active_regex
        self.force_active = False
        self.is_active_callable = self.default_is_active
        if css_id:
            self.set_id(css_id)
            warnings.warn('DEPRECATED: Passing a css_id upon construction. ' \
                          'This ability will be removed in future versions.',
                          DeprecationWarning, stacklevel=2)
    
    def set_active(self):
        self.force_active = True

    def determine_is_active_using(self, is_active_callable):
        self.is_active_callable = is_active_callable

    @property
    def is_active(self):
        return self.is_active_callable()
            
    def default_is_active(self):
        if self.force_active:
            return True
        if not self.active_regex:
            return self.a.href and self.a.href.is_currently_active(exact_path=self.exact_match)
        return re.match(self.active_regex, self.view.relative_path)


class SubMenu(MenuItem):
    """A MenuItem that can contains another complete Menu itself.

       .. admonition:: Styling

          Rendered as a <li> element that contains a :class:`Menu` (see the latter for how it is rendered).

       :param view: (See :class:`reahl.web.fw.Widget`)
       :param title: Text to use as a title for this SubMenu.
       :param menu: The :class:`Menu` contained inside this SubMenu.
       :keyword css_id: (See :class:`reahl.web.ui.HTMLElement`)

    """
    def __init__(self, view, title, menu, query_arguments={}, css_id=None):
        if query_arguments:
            a = A.from_bookmark(view, Bookmark.for_widget(title, query_arguments=query_arguments).on_view(view))
        else:
            a = A(view, None, description=title)
        super(SubMenu, self).__init__(view, a, css_id=css_id)
        self.title = title
        self.menu = menu

#PendingMove: In future this class may be renamed to: reahl.web.attic.menu:Menu instead
# Uses: reahl/web/reahl.menu.css
class Menu(HTMLWidget):
    add_reahl_styling = True
    """A visual menu that lists a number of Views to which the user can choose to go to.

       .. admonition:: Styling

          Rendered as a <ul class="reahl-menu"> element that contains a <li> for each MenuItem.

       :param view: (See :class:`reahl.web.fw.Widget`)
       :keyword a_list: (Deprecated) A list of :class:`A` instances to which each :class:`MenuItem` will lead.
       :keyword css_id: (Deprecated) (See :class:`reahl.web.ui.HTMLElement`)

       .. versionchanged:: 3.2
          Deprecated use of `a_list` and changed it temporarily to a keyword argument for backwards compatibility.
          Deprecated css_id keyword argument.
          Deprecated the `from_xxx` methods and added `with_xxx` replacements to be used after construction.
          Deprecated `add_item` and replaced it with `add_submenu`.
          Added a number of `add_xxx` methods for adding items from different sources.
    """
    def __init__(self, view, a_list=None, add_reahl_styling=None, css_id=None):
        super(Menu, self).__init__(view)
        if add_reahl_styling is not None:
            self.add_reahl_styling = add_reahl_styling
        self.menu_items = []
        self.create_html_representation()
        if css_id:
            warnings.warn('DEPRECATED: Passing a css_id upon construction. ' \
                          'Instead, please construct, supply a layout and THEN do .set_id().',
                          DeprecationWarning, stacklevel=2)
            self.set_id(css_id)
        if a_list is not None:
            warnings.warn('DEPRECATED: Passing an a_list upon construction. ' \
                          'Please construct, then use .with_a_list() instead.',
                          DeprecationWarning, stacklevel=2)
            self.with_a_list(a_list)

    @classmethod
    @deprecated('Please use :meth:`with_languages` instead on an already created instance.', '3.2')
    def from_languages(cls, view):
        """Constructs a Menu which contains a MenuItem for each locale supported by all the components
           in this application.

           :param view: (See :class:`reahl.web.fw.Widget`)
        """
        menu = cls(view)
        return menu.with_languages()

    @classmethod
    @deprecated('Please use :meth:`with_bookmarks` instead on an already created instance.', '3.2')
    def from_bookmarks(cls, view, bookmark_list):
        """Creates a Menu with a MenuItem for each Bookmark given in `bookmark_list`."""
        menu = cls(view)
        return menu.with_bookmarks(bookmark_list)


    def create_html_representation(self):
        ul = self.add_child(Ul(self.view))
        self.set_html_representation(ul)
        if self.add_reahl_styling:
            ul.append_class('reahl-menu')
        return ul

    def with_bookmarks(self, bookmark_list):
        """Populates this Menu with a MenuItem for each Bookmark given in `bookmark_list`.
           
           Answers the same Menu.

           .. versionadded: 3.2
        """
        for bookmark in bookmark_list:
            self.add_bookmark(bookmark)
        return self

    def with_languages(self):
        """Populates this Menu with a MenuItem for each available language.
           
           Answers the same Menu.

           .. versionadded: 3.2
        """
        current_url = Url.get_current_url()
        context = WebExecutionContext.get_context()
        supported_locales = ReahlEgg.get_languages_supported_by_all(context.config.reahlsystem.root_egg)
        for locale in supported_locales:
            try:
                language_name = Locale.parse(locale).display_name
            except UnknownLocaleError:
                language_name = locale
            
            bookmark = self.view.as_bookmark(description=language_name, locale=locale)
            bookmark.exact = True
            self.add_bookmark(bookmark)
        return self

    def with_a_list(self, a_list):
        """Populates this Menu with a MenuItem for each :class:`A` in `a_list`.
           
           Answers the same Menu.

           .. versionadded: 3.2
        """
        for a in a_list:
            self.add_a(a)
        return self

    def add_bookmark(self, bookmark):
        """Adds a MenuItem for the given :class:`Bookmark` to this Menu'.

           Answers the added MenuItem.

           .. versionadded: 3.2
        """
        return self.add_item(MenuItem.from_bookmark(self.view, bookmark))

    def add_a(self, a):
        """Adds an :class:`A` as a MenuItem.
           
           Answers the added MenuItem.

           .. versionadded: 3.2
        """
        return self.add_item(MenuItem(self.view, a))

    def add_item(self, item):
        """Adds MenuItem `item` to this Menu.

           .. versionchanged:: 3.2
              Deprecated adding submenus via this method. For sub menus, please use :meth:`add_submenu` instead.
        """
        self.menu_items.append(item)

        if isinstance(item, SubMenu):
            warnings.warn('DEPRECATED: calling add_item() with a SubMenu instance. Please use .add_submenu() instead.',
                          DeprecationWarning, stacklevel=2)
            item = self.add_html_for_submenu(item)
        else:
            self.add_html_for_item(item)
        return item

    def add_html_for_item(self, item):
        li = self.html_representation.add_child(Li(self.view))
        li.add_child(item.a)
        if self.add_reahl_styling:
            li.add_attribute_source(ActiveStateAttributes(item))
        item.widget = li
        return li

    def add_submenu(self, title, menu, query_arguments={}, **kwargs):
        """Adds 'menu` as a sub menu to this menu with the given `title`.

           Answers the added MenuItem.

           .. versionadded: 3.2
        """
        submenu = SubMenu(self.view, title, menu, query_arguments=query_arguments)
        self.menu_items.append(submenu)
        self.add_html_for_submenu(submenu, **kwargs)
        return submenu

    def add_html_for_submenu(self, submenu, add_dropdown_handle=False):
        li = self.add_html_for_item(submenu)
        if add_dropdown_handle:
            li.add_child(TextNode(self.view, '&nbsp;', html_escape=False))
            dropdown_handle = li.add_child(A(self.view, None, description='▼'))
            dropdown_handle.append_class('dropdown-handle')
        li.add_child(submenu.menu)
        submenu.widget = li
        return li


#PendingMove: In future this class may be renamed to: reahl.web.attic.menu:HorizontalLayout
class HorizontalLayout(Layout):
    """A Layout that causes Widgets to be displayed horizontally.

       .. admonition:: Styling

          Adds class reahl-horizontal to its Widget.

       (Only works for :class:`Menu` and subclasses.)

    """
    def customise_widget(self):
        super(HorizontalLayout, self).customise_widget()
        self.widget.html_representation.append_class('reahl-horizontal')


#PendingMove: In future this class may be renamed to: reahl.web.attic.menu:VerticalLayout
class VerticalLayout(Layout):
    """A Layout that causes Widgets to be displayed vertically.

       .. admonition:: Styling

          Adds class reahl-vertical to its Widget.

       (Only works for :class:`Menu` and subclasses.)

    """
    def customise_widget(self):
        super(VerticalLayout, self).customise_widget()
        self.widget.html_representation.append_class('reahl-vertical')


# Uses: reahl/web/reahl.hmenu.css
@deprecated('Please use Menu(view, layout=HorizontalLayout()) instead.', '3.1')
class HMenu(Menu):
    """A Menu, with items displayed next to each other.

       .. admonition:: Styling

          Rendered as a <ul class="reahl-menu reahl-horizontal">

       :param view: (See :class:`reahl.web.fw.Widget`)
       :param a_list: (See :class:`Menu`)
       :keyword css_id: (See :class:`reahl.web.ui.HTMLElement`)

    """
    def __init__(self, view, a_list, css_id=None):
        super(HMenu, self).__init__(view, a_list, css_id=css_id)
        self.use_layout(HorizontalLayout())


@deprecated('Please use Menu(view, layout=VerticalLayout()) instead.', '3.1')
class VMenu(Menu):
    """A Menu, with items displayed underneath each other.

       .. admonition:: Styling

          Rendered as a <ul class="reahl-menu reahl-vertical">

       :param view: (See :class:`reahl.web.fw.Widget`)
       :param a_list: (See :class:`Menu`)
       :keyword css_id: (See :class:`reahl.web.ui.HTMLElement`)

    """
    def __init__(self, view, a_list, css_id=None):
        super(VMenu, self).__init__(view, a_list, css_id=css_id)
        self.use_layout(VerticalLayout())


#PendingMove: In future this class may be renamed to: reahl.web.attic.tabbedpanel:Tab
class Tab(object):
    """One Tab in a :class:`TabbedPanel`.

       .. admonition:: Styling

          Rendered like a :class:`MenuItem`, with the <a> containing `title`.

       :param view: (See :class:`reahl.web.fw.Widget`)
       :param title: Text that is displayed inside the Tab itself.
       :param tab_key: A name for this tag identifying it uniquely amongst other Tabs in the same :class:`TabbedPanel`.
       :param contents_factory: A :class:`WidgetFactory` specifying how to create the contents of this Tab, once selected.
       :keyword css_id: (Deprecated)

       .. versionchanged: 3.2
          Deprecated css_id keyword argument.
    """
    def __init__(self, view, title, tab_key, contents_factory, css_id=None):
        super(Tab, self).__init__()
        self.title = title
        self.tab_key = tab_key
        self.contents_factory = contents_factory
        self.view = view
        self.panel = None

    def get_bookmark(self, view):
        return Bookmark.for_widget(self.title, query_arguments=self.query_arguments).on_view(view)

    @property
    def query_arguments(self):
        return {'tab': self.tab_key}

    @property
    def contents(self):
        return self.contents_factory.create(self.view)

    def set_panel(self, tabbed_panel):
        self.panel = tabbed_panel

    @property
    def is_open(self):
        return self.panel.is_currently_open(self)

    @property
    def is_active(self):
        return self.is_open

    def add_to_menu(self, menu):
        menu_item = menu.add_bookmark(self.get_bookmark(self.view))
        menu_item.determine_is_active_using(lambda: self.is_active)
        return menu_item


#PendingMove: In future this class may be renamed to: reahl.web.attic.tabbedpanel:MultiTab
class MultiTab(Tab):
    """A composite tab. Instead of a single choice for the user, clicking on a MultiTab
       results in a dropdown menu with more choices for the user.

       .. admonition:: Styling

          Rendered like a :class:`Tab`, but with more contents. The usual <a> containing the title
          is followed by an &nbsp; and an <a class="dropdown-handle">. This is followed by a
          normal :class:`VMenu`.

       :param view: (See :class:`reahl.web.fw.Widget`)
       :param title: (See :class:`Tab`)
       :param tab_key: (See :class:`Tab`)
       :param contents_factory: (See :class:`Tab`)
       :keyword css_id: (Deprecated)

       .. versionchanged: 3.2
          Deprecated css_id keyword argument.
    """
    def __init__(self, view, title, tab_key, contents_factory, css_id=None):
        if css_id:
            self.set_id(css_id)
            warnings.warn('DEPRECATED: Passing a css_id upon construction. ' \
                          'This ability will be removed in future versions.',
                          DeprecationWarning, stacklevel=2)
        self.tabs = []
        self.menu = Menu(view).use_layout(VerticalLayout())
        super(MultiTab, self).__init__(view, title, tab_key, contents_factory)
        
    def add_tab(self, tab):
        tab.add_to_menu(self.menu)
        self.tabs.append(tab)
        tab.set_panel(self.panel)
        return tab

    @property
    def first_tab(self):
        return self.tabs[0]

    @property
    def current_sub_tab(self):
        open_tab = [tab for tab in self.tabs
                      if tab.is_open]
        if len(open_tab) == 1:
            return open_tab[0]
        return self.first_tab

    @property
    def is_active(self):
        return self.is_open or self.current_sub_tab.is_open

    @property
    def contents(self):
        if self.is_open:
            return super(MultiTab, self).contents
        else:
            return self.current_sub_tab.contents

    def set_panel(self, tabbed_panel):
        super(MultiTab, self).set_panel(tabbed_panel)
        for tab in self.tabs:
            tab.set_panel(tabbed_panel)

    def add_to_menu(self, menu):
        menu_item = menu.add_submenu(self.title, self.menu, query_arguments=self.query_arguments, add_dropdown_handle=True)
        menu_item.determine_is_active_using(lambda: self.is_active)
        return menu_item


#PendingMove: In future this class may be renamed to: reahl.web.attic.tabbedpanel:TabbedPanel
# Uses: reahl/web/reahl.tabbedpanel.css
# Uses: reahl/web/reahl.tabbedpanel.js
class TabbedPanel(Div):
    """A Div sporting different Tabs which the user can select to change what is displayed. The contents
       of a TabbedPanel are changed when the user clicks on a different Tab without refreshing the entire
       page, provided that JavaScript is available on the user agent.

       .. admonition:: Styling

          Rendered as a <div class="reahl-tabbedpanel"> which contains two children: an :class:`HMenu`
          containing instances of :class:`Tab` for MenuItems, followed by a <div> that will be populated
          by the current contents of the TabbedPanel.

       :param view: (See :class:`reahl.web.fw.Widget`)
       :param css_id: (Deprecated) (See :class:`reahl.web.ui.HTMLElement`)
       
       .. versionchanged: 3.2
          Deprecated use css_id keyword argument.
    """
    def __init__(self, view, css_id):
        super(TabbedPanel, self).__init__(view, css_id=css_id)
        self.append_class('reahl-tabbedpanel')
        self.tabs = []
        self.menu = self.add_child(Menu(view).use_layout(HorizontalLayout()))
        self.content_panel = self.add_child(Div(view))
        self.enable_refresh()
        if css_id:
            warnings.warn('DEPRECATED: Passing css_id upon construction. '  \
                          'Instead, construct, then call .set_id().',
                          DeprecationWarning, stacklevel=2)

    @exposed
    def query_fields(self, fields):
        fields.tab = Field(required=False, default=None)

    @property
    def active_tab_set(self):
        return self.tab is not None

    def set_active(self, tab):
        self.tab = tab.tab_key

    def is_currently_open(self, tab):
        return tab.tab_key == self.tab

    def add_tab(self, tab):
        """Adds the Tab `tab` to this TabbedPanel."""
        if not self.active_tab_set:
            self.set_active(tab)
        tab.set_panel(self)

        self.tabs.append(tab)
        tab.add_to_menu(self.menu)

        self.add_pane_for(tab)
        return tab

    def add_pane_for(self, tab):
        if tab.is_active:
            self.content_panel.add_child(tab.contents)


#PendingMove: In future this class may be renamed to: reahl.web.attic.slidingpanel:SlidingPanel
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


class SimpleFileInput(InputTypeInput):
    """An Input for selecting a single file which will be uploaded once the user clicks on any :class:`Button`
       associated with the same :class:`Form` as this Input.
    
       .. admonition:: Styling
          
          Represented in HTML by an <input type="file"> element. Can have attribute multiple set,
          if allowed by the `bound_field`.

       :param form: (See :class:`~reahl.web.ui.Input`)
       :param bound_field: (See :class:`~reahl.web.ui.Input`, must be of type :class:`reahl.component.modelinterface.FileField`
    """
    is_for_file = True

    def __init__(self, form, bound_field):
        super(SimpleFileInput, self).__init__(form, bound_field, 'file')

    def create_html_widget(self):
        file_input = super(SimpleFileInput, self).create_html_widget()
        if self.allow_multiple:
            file_input.set_attribute('multiple', 'multiple')
        return file_input

    def get_value_from_input(self, input_values):
        field_storages = input_values.getall(self.name)

        return [UploadedFile(six.text_type(field_storage.filename), field_storage.file.read(), six.text_type(field_storage.type))
                 for field_storage in field_storages
                 if field_storage not in ('', b'')]

    @property
    def allow_multiple(self):
        return self.bound_field.allow_multiple

    @property
    def value(self):
        return ''

    @property
    def persisted_exception_class(self):
        return self.form.persisted_exception_class

    def prepare_input(self):
        previous_exception = self.persisted_exception_class.get_exception_for_input(self.form, self.name)
        if previous_exception is not None:
            self.bound_field.validation_error = previous_exception
            self.bound_field.input_status = 'invalidly_entered'

    def persist_input(self, input_values):
        if self.get_input_status() == 'invalidly_entered':
            self.persisted_exception_class.new_for_form(self.form, input_name=self.name, exception=self.bound_field.validation_error)


# Uses: reahl/web/reahl.fileuploadli.js
class FileUploadLi(Li):
    def __init__(self, form, remove_event, persisted_file, css_id=None):
        super(FileUploadLi, self).__init__(form.view, css_id=css_id)
        self.set_attribute('class', 'reahl-file-upload-li')
        self.add_child(Button(form, remove_event.with_arguments(filename=persisted_file.filename)))
        self.add_child(Span(self.view, persisted_file.filename))

    def get_js(self, context=None):
        return ['$(".reahl-file-upload-li").fileuploadli();']



# Uses: reahl/web/reahl.fileuploadpanel.js
class FileUploadPanel(Div):
    def __init__(self, file_upload_input, css_id=None):
        super(FileUploadPanel, self).__init__(file_upload_input.view, css_id=css_id)
        self.set_attribute('class', 'reahl-file-upload-panel')
        self.file_upload_input = file_upload_input

        self.add_nested_form()
        self.add_uploaded_list()
        self.add_upload_controls()

    def add_nested_form(self):
        self.upload_form = self.add_child(NestedForm(self.view, '%s-%s-upload' % (self.input_form.css_id, self.bound_field.name)))
        self.upload_form.define_event_handler(self.events.upload_file)
        self.upload_form.define_event_handler(self.events.remove_file)

    @property
    def name(self):
        return self.bound_field.variable_name
        
    def add_uploaded_list(self):
        ul = self.upload_form.add_child(Ul(self.view))
        for persisted_file in self.persisted_file_class.get_persisted_for_form(self.input_form, self.name):
            ul.add_child(FileUploadLi(self.upload_form.form, self.events.remove_file, persisted_file))

    def add_upload_controls(self):
        controls_panel = self.upload_form.add_child(Div(self.view))
        controls_panel.add_child(SimpleFileInput(self.upload_form.form, self.fields.uploaded_file))
        controls_panel.add_child(Button(self.upload_form.form, self.events.upload_file))
        
    @property
    def persisted_file_class(self):
        return self.file_upload_input.persisted_file_class

    @property
    def input_form(self):
        return self.file_upload_input.form
        
    @property
    def bound_field(self):
        return self.file_upload_input.bound_field

    @exposed
    def events(self, events):
        events.upload_file = Event(label=_('Upload'), action=Action(self.upload_file))
        events.remove_file = Event(label=_('Remove'), 
                                   action=Action(self.remove_file, ['filename']),
                                   filename=Field(required=True))
            
    @exposed
    def fields(self, fields):
        fields.uploaded_file = self.bound_field.unbound_copy()
        fields.uploaded_file.disallow_multiple()
        fields.uploaded_file.make_optional()
        fields.uploaded_file.label = _('Add file')
        fields.uploaded_file.add_validation_constraint(UniqueFilesConstraint(self.input_form, self.bound_field.name))

    def attach_jq_widget(self, selector, widget_name, **options):
        def js_repr(value):
            if isinstance(value, six.string_types):
                return '"%s"' % value
            return value
        option_args = ','.join(['%s: %s' % (name, js_repr(value)) for name, value in options.items()])
        return '$(%s).%s({%s});' % (selector, widget_name, option_args)

    def get_js(self, context=None):
        selector = self.contextualise_selector('"#%s .reahl-file-upload-panel"' % self.input_form.css_id, context)
        unique_names_constraint = self.fields.uploaded_file.get_validation_constraint_of_class(UniqueFilesConstraint)
        js = self.attach_jq_widget(selector, 'fileuploadpanel', 
                    form_id=self.upload_form.form.css_id, 
                    nested_form_id=self.upload_form.css_id,
                    input_form_id=self.input_form.css_id,
                    errorMessage=_('an error occurred, please try again later.'),
                    removeLabel=self.events.remove_file.label,
                    cancelLabel=_('Cancel'),
                    duplicateValidationErrorMessage=unique_names_constraint.message,
                    waitForUploadsMessage=_('Please try again when all files have finished uploading.'))
        return super(FileUploadPanel, self).get_js(context=context) + [js]

    def remove_file(self, filename):
        self.persisted_file_class.remove_persisted_for_form(self.input_form, self.name, filename)

    def upload_file(self):
        if self.uploaded_file is not None:
            self.persisted_file_class.add_persisted_for_form(self.input_form, self.name, self.uploaded_file)




class UniqueFilesConstraint(ValidationConstraint):
    name = 'uniquefiles'
    def __init__(self, form=None, input_name=None, error_message=None):
        error_message = error_message or _('uploaded files should all have different names')
        super(UniqueFilesConstraint, self).__init__(error_message=error_message)
        self.form = form
        self.input_name = input_name

    def validate_input(self, unparsed_input):
        assert (self.form is not None) and (self.field is not None)
        config = WebExecutionContext.get_context().config
        persisted_file_class = config.web.persisted_file_class
        for f in unparsed_input:
            if persisted_file_class.is_uploaded_for_form(self.form, self.input_name, f.filename):
                raise self

    def __reduce__(self):
        reduced = super(UniqueFilesConstraint, self).__reduce__()
        pickle_dict = reduced[2]
        del pickle_dict['form']
        return reduced


#PendingMove: In future this class may be renamed to: reahl.web.attic.fileupload:FileUploadInput
class FileUploadInput(PrimitiveInput):
    """An Input which allows a user to choose several files for uploding to a server. As each file is
       chosen, the file is uploaded to the server in the background (if JavaScript is enabled on the user
       agent). A file being uploaded can be cancelled and uploaded files can be removed from the list.
        
       .. admonition:: Styling
          
          Represented in HTML by a <div class="reahl-file-upload-panel"> with three children:
           - a :class:`NestedForm`,
           - an <ul> which contains a <li class="reahl-file-upload-li"> for each file that was uploaded
             (or is still being uploaded), and
           - a <div> which contains a :class:`SimpleFileInput` and a :class:`Button`.

          While a file is being uploaded, its <li class="reahl-file-upload-li"> contains a cancel button
          of type :class:`Button`, and a <span> containing the name of the file. These elements are followed
          by a <progress> element.
          
          Once a file has been uploaded, its <li class="reahl-file-upload-li"> is changed. The <progress>
          element is removed, and cancel button is replaced with a Remove button.
          
          Should an error occur while uploading the file, the <progress> element is replaced with a
          <label class="error> containing an error message.

       :param form: (See :class:`~reahl.web.ui.Input`)
       :param bound_field: (See :class:`~reahl.web.ui.Input`, must be of type :class:`reahl.component.modelinterface.FileField`
    """
    @property
    def persisted_file_class(self):
        config = WebExecutionContext.get_context().config
        return config.web.persisted_file_class

    @property
    def html_control(self):
        return None

    def create_html_widget(self):
        return FileUploadPanel(self)

    def get_value_from_input(self, input_values):
        return [UploadedFile(f.filename, f.file_obj.read(), f.mime_type)
                 for f in self.persisted_file_class.get_persisted_for_form(self.form, self.name)]

    def enter_value(self, input_value):
        pass


#PendingMove: In future this class may be renamed to: reahl.web.attic.clientside:DialogButton
class DialogButton(object):
    def __init__(self, label):
        self.label = label

    def callback_js(self):
        return ''
        
    def as_jquery(self):
        return '"%s": function() { %s }' % (self.label, self.callback_js())


#PendingMove: In future this class may be renamed to: reahl.web.attic.clientside:CheckCheckboxButton
class CheckCheckboxButton(DialogButton):
    def __init__(self, label, checkbox):
        super(CheckCheckboxButton, self).__init__(label)
        self.checkbox_to_check = checkbox
        
    def callback_js(self):
        return '''$(%s).attr("checked", true);''' %  self.checkbox_to_check.jquery_selector


#PendingMove: In future this class may be renamed to: reahl.web.attic.clientside:PopupA
# Uses: reahl/web/reahl.popupa.js
class PopupA(A):
    # Implements:
    # http://blog.nemikor.com/category/jquery-ui/jquery-ui-dialog/
    # ... with buttons added
    def __init__(self, view, target_bookmark, show_for_selector, close_button=True, css_id=None):
        super(PopupA, self).__init__(view, target_bookmark.href, target_bookmark.description, css_id=css_id)
        self.set_title(target_bookmark.description)
        self.append_class('reahl-popupa')
        self.show_for_selector = show_for_selector
        self.buttons = []
        if close_button:
            self.add_button(DialogButton(_('Close')))
        
    def add_button(self, button):
        self.buttons.append(button)

    def buttons_as_jquery(self):
        return ', '.join([button.as_jquery() for button in self.buttons])

    @property
    def jquery_selector(self):
        return '"a.reahl-popupa[href=\'%s\']"' % self.href

    def get_js(self, context=None):
        selector = self.contextualise_selector(self.jquery_selector, context)
        return ['$(%s).popupa({showForSelector: "%s", buttons: { %s }  });' % \
              (selector, self.show_for_selector, self.buttons_as_jquery())]


class Caption(HTMLElement):
    """An HTML caption element.

       .. admonition:: Styling

          Renders as an HTML <caption> element.
    
       :param view: (See :class:`reahl.web.fw.Widget`)
       :keyword text: Text to be displayed inside the caption element.
       :keyword css_id: (See :class:`reahl.web.ui.HTMLElement`)
       
    """
    def __init__(self, view, text=None, css_id=None):
        super(Caption, self).__init__(view, 'caption', children_allowed=True, css_id=css_id)
        if text is not None:
            self.add_child(TextNode(view, text))


class Col(HTMLElement):
    """An HTML col element, defines a column in a table.

       :param view: (See :class:`reahl.web.fw.Widget`)
       :keyword span: The number of columns spanned by this column.
       :keyword css_id: (See :class:`reahl.web.ui.HTMLElement`)
       
    """
    def __init__(self, view, span=None, css_id=None):
        super(Col, self).__init__(view, 'col', children_allowed=False, css_id=css_id)
        if span:
            self.set_attribute('span', span)


class ColGroup(HTMLElement):
    """An HTML colgroup element, defines a group of columns in a table.

       :param view: (See :class:`reahl.web.fw.Widget`)
       :keyword span: The number of columns spanned by this group.
       :keyword css_id: (See :class:`reahl.web.ui.HTMLElement`)
       
    """
    def __init__(self, view, span=None, css_id=None):
        super(ColGroup, self).__init__(view, 'colgroup', children_allowed=True, css_id=css_id)
        if span:
            self.set_attribute('span', span)

Colgroup = ColGroup

class Thead(HTMLElement):
    """An HTML thead element. Contains the header of the table columns.

       :param view: (See :class:`reahl.web.fw.Widget`)
       :keyword css_id: (See :class:`reahl.web.ui.HTMLElement`)
       
    """
    def __init__(self, view, css_id=None):
        super(Thead, self).__init__(view, 'thead', children_allowed=True, css_id=css_id)


class Tfoot(HTMLElement):
    """An HTML tfoot element. Contains the footer of the table columns.

       :param view: (See :class:`reahl.web.fw.Widget`)
       :keyword css_id: (See :class:`reahl.web.ui.HTMLElement`)
       
    """
    def __init__(self, view, css_id=None):
        super(Tfoot, self).__init__(view, 'tfoot', children_allowed=True, css_id=css_id)


class Tbody(HTMLElement):
    """An HTML tbody element. Contains the rows with data in the table.

       :param view: (See :class:`reahl.web.fw.Widget`)
       :keyword css_id: (See :class:`reahl.web.ui.HTMLElement`)
       
    """
    def __init__(self, view, css_id=None):
        super(Tbody, self).__init__(view, 'tbody', children_allowed=True, css_id=css_id)


class Tr(HTMLElement):
    """An HTML tr element represents one row of data in a table.

       :param view: (See :class:`reahl.web.fw.Widget`)
       :keyword css_id: (See :class:`reahl.web.ui.HTMLElement`)
       
    """
    def __init__(self, view, css_id=None):
        super(Tr, self).__init__(view, 'tr',children_allowed=True, css_id=css_id)


class Cell(HTMLElement):
    def __init__(self, view, html_tag_name, rowspan=None, colspan=None, css_id=None):
        super(Cell, self).__init__(view, html_tag_name, children_allowed=True, css_id=css_id)
        if rowspan:
            self.set_attribute('rowspan', rowspan)
        if colspan:
            self.set_attribute('colspan', colspan)


class Th(Cell):
    """An HTML th element - a single cell heading for a column of a table.

       :param view: (See :class:`reahl.web.fw.Widget`)
       :keyword rowspan: The number of rows this table cell should span.
       :keyword colspan: The number of columns this table cell should span.
       :keyword css_id: (See :class:`reahl.web.ui.HTMLElement`)
       
    """
    def __init__(self, view,  rowspan=None, colspan=None, css_id=None):
        super(Th, self).__init__(view, 'th', rowspan=rowspan, colspan=colspan, css_id=css_id)


class Td(Cell):
    """An HTML td element - a single cell of data inside a row of a table.

       :param view: (See :class:`reahl.web.fw.Widget`)
       :keyword rowspan: The number of rows this table cell should span.
       :keyword colspan: The number of columns this table cell should span.
       :keyword css_id: (See :class:`reahl.web.ui.HTMLElement`)
       
    """
    def __init__(self, view, rowspan=None, colspan=None, css_id=None):
        super(Td, self).__init__(view, 'td', rowspan=rowspan, colspan=colspan, css_id=css_id)


class DynamicColumn(object):
    """DynamicColumn defines a logical column of a table, specifying how its heading will be 
       rendered, and how the cell in this column will be displayed for each data item in the 
       table.

       :param make_heading_or_string: A string to be used as heading for this column, or \
              a single-argument callable that will be called (passing the current view) in \
              order to compute a Widget to be displayed as heading of the column.
       :param make_widget: A callable that takes two arguments: the current view, and an item \
              of data of the current table row. It will be called to compute a Widget \
              to be displayed in the current column for the given data item.
       :keyword sort_key: If specified, this value will be passed to sort() for sortable tables. 
    """
    def __init__(self, make_heading_or_string, make_widget, sort_key=None):
        if isinstance(make_heading_or_string, six.string_types):
            def make_span(view):
                return Span(view, text=make_heading_or_string)
            self.make_heading_widget = make_span
        else:
            self.make_heading_widget = make_heading_or_string

        self.make_widget = make_widget
        self.sort_key = sort_key

    def heading_as_widget(self, view):
        return self.make_heading_widget(view)

    def as_widget(self, view, item):
        return self.make_widget(view, item)
        
    def with_overridden_heading_widget(self, make_heading_widget):
        new_column = copy.copy(self)
        new_column.make_heading_widget = make_heading_widget
        return new_column


class StaticColumn(DynamicColumn):
    """StaticColumn defines a column whose heading and contents are derived from the given field.

       :param field: The :class:`Field` that defines the heading for this column, and which \
              will also be used to get the data to be displayed for each row in this column.
       :param attribute_name: The name of the attribute to which `field` should be bound to \
              on each data item when rendering this column.
       :keyword sort_key: If specified, this value will be passed to sort() for sortable tables. 
    """
    def __init__(self, field, attribute_name, sort_key=None):
        super(StaticColumn, self).__init__(field.label, self.make_text_node, sort_key=sort_key)
        self.field = field
        self.attribute_name = attribute_name
    
    def make_text_node(self, view, item):
        field = self.field.copy()
        field.bind(self.attribute_name, item)
        return TextNode(view, field.as_input())    


class Table(HTMLElement):
    """An HTML table element: data displayed on columns and rows.

       :param view: (See :class:`reahl.web.fw.Widget`)
       :keyword caption_text: If text is given here, a caption will be added to the table containing the caption text.
       :keyword summary:  A textual summary of the contents of the table which is not displayed visually, \
                but may be used by a user agent for accessibility purposes.
       :keyword css_id: (See :class:`reahl.web.ui.HTMLElement`)
       
    """
    def __init__(self, view, caption_text=None, summary=None, css_id=None):
        super(Table, self).__init__(view, 'table', children_allowed=True, css_id=css_id)
        if caption_text:
            self.add_child(Caption(view, text=caption_text))
        if summary:
            self.set_attribute('summary', '%s' % summary)

    @deprecated('Please use with_data instead.', '3.2')
    @classmethod
    def from_columns(cls, view, columns, items, caption_text=None, summary=None, css_id=None):
        """Creates a table populated with rows, columns, header and footer, with one row per provided item. The table is
           defined by the list of :class:`DynamicColumn` or :class:`StaticColumn` instances passed in.  

           :param view: (See :class:`reahl.web.fw.Widget`)
           :param columns: The :class:`DynamicColumn` instances that define the contents of the table.
           :param items: A list containing objects represented in each row of the table.
           :keyword caption_text: If given, a :class:`reahl.web.ui.Caption` is added with this text.
           :keyword summary: If given, a `summary` attribute is added to the table containing this text.
           :keyword css_id: (See :class:`reahl.web.ui.HTMLElement`)
           
        """
        table = cls(view, caption_text=caption_text, summary=summary, css_id=css_id)
        table.create_header_columns(columns)
        table.create_rows(columns, items)
        return table

    def with_data(self, columns, items):
        """Populate the table with the given data. Data is arranged into columns as
           defined by the list of :class:`DynamicColumn` or :class:`StaticColumn` instances passed in.  

           :param columns: The :class:`DynamicColumn` instances that define the contents of the table.
           :param items: A list containing objects represented in each row of the table.
        """
        if self.thead:
            raise ProgrammerError('This table has already been populated.')
        self.create_header_columns(columns)
        self.create_rows(columns, items)
        return self

    def create_header_columns(self, columns):
        table_header = self.add_child(Thead(self.view))
        header_tr = table_header.add_child(Tr(self.view))
        for column_number, column in enumerate(columns):
            column_th = header_tr.add_child(Th(self.view))
            column_th.add_child(column.heading_as_widget(self.view))

    @property
    def thead(self):
        for child in self.contained_widgets():
            if isinstance(child, Thead):
                return child
        return None

    def create_rows(self, columns, items):
        body = self.add_child(Tbody(self.view))
        for item in items:
            row = body.add_child(Tr(self.view))
            for column in columns:
                row_td = row.add_child(Td(self.view))
                row_td.add_child(column.as_widget(self.view, item))

