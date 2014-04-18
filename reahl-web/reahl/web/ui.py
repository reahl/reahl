# Copyright 2009-2013 Reahl Software Services (Pty) Ltd. All rights reserved.
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

from string import Template
import re
import cgi
import urllib
import itertools

from babel import Locale, UnknownLocaleError
from reahl.component.eggs import ReahlEgg
from reahl.component.exceptions import ProgrammerError, IncorrectArgumentError, arg_checks, IsInstance
from reahl.component.i18n import Translator
from reahl.web.fw import WebExecutionContext, EventChannel, RemoteMethod, JsonResult, Widget, \
                          CheckedRemoteMethod, ValidationException, WidgetResult, WidgetFactory, Url, Bookmark, WidgetList
from reahl.component.modelinterface import ValidationConstraintList, ValidationConstraint, \
                                     PatternConstraint, RemoteConstraint,\
                                     Field, BooleanField, IntegerField, exposed, ConstraintNotFound, Choice, ChoiceGroup, \
                                     Event, Action, FileField, UploadedFile, InputParseException
                                     

_ = Translator(u'reahl-web')


class LiteralHTML(Widget):
    """The LiteralHTML Widget renders a chunk of HTML as given in `contents`. If a single-argument
       callable is given as `transform`, `contents` will first be passed to that callable to possibly
       change the HTML on-the-fly before rendering (the callable should return the changed HTML to be
       rendered).
    """
    def __init__(self, view, contents, transform=(lambda i: i)):
        super(LiteralHTML, self).__init__(view)
        self.contents = contents
        self.transform = transform

    def render(self):
        return self.transform(self.contents)


class HTMLAttribute(object):
    def __init__(self, name, values):
        super(HTMLAttribute, self).__init__()
        self.name = name
        self.value = set(values)

    def as_html_snippet(self):
        if not self.value:
            return u''
#        return u'''%s='%s\'''' % (self.name, self.as_html_value())
        return u'%s="%s"' % (self.name, cgi.escape(self.as_html_value(), True))
        
    def as_html_value(self):
        return u' '.join(sorted(self.value))
    
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
        values = self.values()
        sorted_values = []
        if u'name' in self:
            name_value = self[u'name']
            sorted_values.append(name_value)
            values.remove(name_value)
        if u'id' in self:
            id_value = self[u'id']
            sorted_values.append(id_value)
            values.remove(id_value)
        sorted_values += sorted(values, lambda a, b: cmp(a.name, b.name))            
        if u'class' in self:
            class_value = self[u'class']
            sorted_values.remove(class_value)
            sorted_values.append(class_value)

        return sorted_values

    def as_html_snippet(self):
        html_snippet = u' '.join([attribute.as_html_snippet() for attribute in self.sorted_values()
                                  if attribute.as_html_snippet()])
        if not html_snippet: return u''
        return u' '+html_snippet

    def add_to(self, name, values):
        attribute = self.setdefault(name, HTMLAttribute(name, []))
        attribute.add_values(values)

    def remove_from(self, name, values):
        attribute = self.get(name)
        if attribute:
            attribute.remove_values(values)

    def set_to(self, name, value):
        self[name] = HTMLAttribute(name, [value])

    def clear(self, name):
        del self[name]        


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
        assert widget not in self.widgets, u'%s is already added to %s' % (widget, self)
        self.widgets.add(widget)

    def add_secondary(self, widget):
        """Adds `widget`, with secondary priority."""
        self.add(widget)
        widget.set_priority(secondary=True)
        
    def add_primary(self, widget):
        """Adds `widget`, with primary priority."""
        assert not self.has_primary, u'Cannot add more than one widget as primary to %s' % self
        self.add(widget)
        widget.set_priority(primary=True)
        self.has_primary = True


# Uses: reahl/web/reahl.hashchange.js
class HashChangeHandler(object):
    def __init__(self, widget):
        self.error_message = _(u'An error occurred when contacting the server. Please try again later.')
        self.timeout_message = _(u'The server took too long to respond. Please try again later.')
        self.widget = widget
        result = WidgetResult(widget)
        method_name = u'refresh_%s' % widget.css_id
        callable_object = lambda *args, **kwargs: None
        self.remote_method = RemoteMethod(method_name, callable_object, result, immutable=True)
        widget.view.add_resource(self.remote_method)

    @property
    def argument_defaults(self):
        field_defaults = self.widget.query_fields.as_kwargs()
        argument_defaults = [u'%s: "%s"' % (name, default_value or u'') \
                             for name, default_value in field_defaults.items()]
        return u'{%s}' % u','.join(argument_defaults)

    def as_jquery_parameter(self):
        return u'{url:"%s", errorMessage: "%s", timeoutMessage: "%s", params: %s}' % \
               (self.remote_method.get_url(), self.error_message, self.timeout_message, self.argument_defaults)


class HTMLElement(Widget):
    """A Widget that is represented by an HTML element.
    
    :param view: (See :class:`reahl.web.fw.Widget`)
    :param tag_name: The element name used to render tags for this HTMLElement
    :param children_allowed: Elements that are not allowed to have children are rendered only with opening tags,
                             others have an opening and closing tag. 
                             (See `HTML5 void elements <http://dev.w3.org/html5/markup/syntax.html#syntax-elements>`_.)
    :param css_id: If specified, the HTMLElement will have an id attribute set to this. Mandatory when a Widget has :meth:`query_fields`.
    :param wrapper_widget: Inputs are Widgets that are not HTMLElements. Such an Input acts as "wrapper_widget" for the 
                           HTMLElement representing it in HTML. This `wrapper_widget` (the Input) dictates some of the
                           attributes its HTML representative should have.
    :param read_check: (See :class:`reahl.web.fw.Widget`)
    :param write_check: (See :class:`reahl.web.fw.Widget`)
    """
    def __init__(self, view, tag_name, children_allowed=False, css_id=None, wrapper_widget=None, read_check=None, write_check=None):
        super(HTMLElement, self).__init__(view, read_check=read_check, write_check=write_check)
        self.wrapper_widget = wrapper_widget
        if wrapper_widget:
            if not isinstance(wrapper_widget, Input):
                raise ProgrammerError(u'Only Inputs can be wrappers, got a %s instead' % wrapper_widget)
            wrapper_widget.set_wrapped_widget(self)

        self.children_allowed = children_allowed
        self.tag_name = tag_name
        self.constant_attributes = HTMLAttributeDict()
        self.ajax_handlers = []
        if css_id:
            self.set_id(css_id)

    def enable_refresh(self):
        """Sets this HTMLElement up so that it will refresh itself without reloading its page when it senses that 
           one of its `query_fields` have changed.
        """
        if not self.css_id_is_set:
            raise ProgrammerError(u'%s does not have a css_id set. A fixed css_id is mandatory when a Widget self-refreshes' % self)
        self.add_hash_change_handler()
        
    def add_child(self, child):
        assert self.children_allowed, u'You cannot add children to a %s' % type(self)
        return super(HTMLElement, self).add_child(child)

    def add_to_attribute(self, name, values):
        """Ensures that the value of the attribute `name` of this HTMLElement includes the words listed in `values` 
           (a list of strings).
        """
        self.constant_attributes.add_to(name, values)
    
    def set_attribute(self, name, value):
        """Sets the value of the attribute `name` of this HTMLElement to the string `value`."""
        self.constant_attributes.set_to(name, value)

    def has_attribute(self, name):
        """Answers whether this HTMLElement has an attribute named `name`."""
        return self.attributes.has_key(name)
            
    @property
    def attributes(self):
        """Override this method if you want to change the attributes of this HTMLElement on the fly, based on the state
           of the HTMLElement at the point in time when it is rendered."""
        attributes = HTMLAttributeDict(self.constant_attributes)
        if self.priority == u'secondary':
            attributes.add_to(u'class', [u'reahl-priority-secondary'])
        elif self.priority == u'primary':
            attributes.add_to(u'class', [u'reahl-priority-primary'])
        if self.wrapper_widget:
            attributes = self.wrapper_widget.get_wrapped_html_attributes(attributes)
        return attributes
        
    def add_hash_change_handler(self):
        handler = HashChangeHandler(self)
        self.ajax_handlers.append( handler )
        
    def render(self):
        if self.visible:
            rendered = u'<%s%s>' % (self.tag_name, self.attributes.as_html_snippet())
            if self.children_allowed:
                rendered += self.render_contents() + (u'</%s>' % self.tag_name)
            return rendered
        else:
            return u''

    @property
    def css_id_is_set(self):
        return getattr(self, u'_css_id', None) is not None
    def get_css_id(self):
        if not self.css_id_is_set:
            raise ProgrammerError('%s needs a css_id to be set!' % self)
        return self._css_id
    def set_css_id(self, value):
        self._css_id = value
        self.set_attribute(u'id', value)
    css_id = property(get_css_id, set_css_id)
     
    def contextualise_selector(self, selector, context):
        """Returns a JQuery selector for finding `selector` within the elements matched by `context` (another selector)."""
        context_str = u', "%s"' % context if context else u''
        return u'%s%s' % (selector, context_str)

    @property
    def jquery_selector(self):
        """Returns a string (including its " delimeters) which can be used to target this HTMLElement using
           JQuery. By default this uses the id attribute of the HTMLElement, but this property can be overridden to
           not be dependent on the id attribute of the HTMLElement.
        
           :raises ProgrammerError: Raised when accessing `jquery_selector` if the css_id of this HTMLElement is not set.
        """
        return u'"#%s"' % (self.css_id)

    def handlers_as_jquery(self):
        return u'[%s]' % (u','.join(handler.as_jquery_parameter() for handler in self.ajax_handlers))

    def get_js(self, context=None):
        js = []
        if self.ajax_handlers:
            js = [u'$(%s).hashchange({hashChangeHandlers: %s});' % \
                  (self.contextualise_selector(self.jquery_selector, context),
                   self.handlers_as_jquery())]
        return super(HTMLElement, self).get_js(context=context) + js

    def set_title(self, title):
        """A convenience method to set the "title" attribute of this HTMLElement."""
        self.set_attribute(u'title', title)

    def set_id(self, css_id):
        """A convenience method to set the "id" attribute of this HTMLElement."""
        self.css_id = css_id

    def append_class(self, css_class):
        """A convenience method to add the word in `css_class` to the "class" attribute of thie HTMLElement."""
        self.add_to_attribute(u'class', [css_class])


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
        if callable(value_or_getter):
            self.value_getter = value_or_getter
        else:
            def get_value():
                return value_or_getter
            self.value_getter = get_value

    @property
    def value(self):
        return self.value_getter()

    def render(self):
        if self.html_escape:
            return cgi.escape(self.value)
        return self.value


class Title(HTMLElement):
    """The title of an HTML page (the title of a :class:`reahl.web.fw.View` is usually shown via a Title). 

       .. admonition:: Styling
       
          Rendered as a <title> element.
    
       :param view: (See :class:`reahl.web.fw.Widget`)
       :param text: A string for use in a `PEP-292 <http://www.python.org/dev/peps/pep-0292/>` template. The final
                    value after substituting this string Template will be used as the value of this Title. The
                    template string may use one placeholder: $current_title which contains the title of the current
                    View.
       :param css_id: (See :class:`HTMLElement`)
    """
    def __init__(self, view, text, css_id=None):
        super(Title, self).__init__(view, u'title', children_allowed=True, css_id=css_id)
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
       :param _type: The value of the "type" attribute of this HTMLElement.
       :param css_id:  (See :class:`HTMLElement`)
    """
    def __init__(self, view, rel, href, _type, css_id=None):
        super(Link, self).__init__(view, u'link', css_id=css_id)
        self.set_attribute(u'rel', rel)
        self.set_attribute(u'href', unicode(href))
        self.set_attribute(u'type', _type)


class Slot(Widget):
    """A Slot is a placeholder into which Views can plug Widgets on the fly."""
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
        super(Meta, self).__init__(view, u'meta', children_allowed=False)
        self.set_attribute(u'name', name)
        self.set_attribute(u'content', content)


class Head(HTMLElement):
    """A container for metadata of a View.

       .. admonition:: Styling

          Renders as an HTML <head> element.

       :param view: (See :class:`reahl.web.fw.Widget`)
       :param title: Text for a template to be used as document Title (See also :class:`Title`).
       :param css_id: (See :class:`HTMLElement`)
    """
    def __init__(self, view, title, css_id=None):
        super(Head, self).__init__(view, u'head', children_allowed=True, css_id=css_id)
        self.title = self.add_child(Title(view, title))
        self.add_child(Slot(view, name=u'reahl_header'))

    def add_css(self, href):
        self.add_child(Link(self.view, u'stylesheet', href, u'text/css'))


class Body(HTMLElement):
    """The content of an HTML document.

       .. admonition:: Styling

          Renders as an HTML <body> element.
    
       :param view: (See :class:`reahl.web.fw.Widget`)
       :param css_id: (See :class:`HTMLElement`)
    """
    def __init__(self, view, css_id=None):
        super(Body, self).__init__(view, 'body', children_allowed=True, css_id=css_id)
        self.add_child(Slot(self.view, name=u'reahl_footer'))

    def footer_already_added(self):        
        if len(self.children) > 0:
            last_child = self.children[-1]
            return isinstance(last_child, Slot) and last_child.name == u'reahl_footer'
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
       :param title: Text for a template to be used as document Title (See also :class:`Title`).
       :param style: Pass a string denoting a predifined set of css styles.
       :param css_id: (See :class:`HTMLElement`)
    """
    def __init__(self, view, title=u'$current_title', style=None, css_id=None):
        super(HTML5Page, self).__init__(view, u'html', children_allowed=True, css_id=css_id)
        self.head = self.add_child(Head(view, title))  #: The Head HTMLElement of this page
        self.body = self.add_child(Body(view))         #: The Body HTMLElement of this page

        if style:
            self.head.add_css(Url(u'/styles/%s.css' % style))

    def render(self):
        return u'<!DOCTYPE html>' + super(HTML5Page, self).render()


class TwoColumnPage(HTML5Page):
    """An HTML5Page with a basic layout: It has a header area which displays at top of two columns. A footer area
       displays below the two columns. The main column is to the right, and larger. The secondary column is to 
       the left, and smaller.
       
       .. admonition:: Styling

          Renders as a page structured using `Yui 2, with two template preset columns 
          <http://developer.yahoo.com/yui/grids/#start>`_ (main and secondary).

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
       :param css_id: (See :class:`HTMLElement`)
    """
    @arg_checks(title=IsInstance(basestring))
    def __init__(self, view, title=u'$current_title', style=None, css_id=None):
        super(TwoColumnPage, self).__init__(view, title=title, style=style, css_id=css_id)
            
        self.yui_page = self.body.add_child(YuiDoc(view, u'doc', u'yui-t2'))
        self.main.add_child(Slot(view, u'main'))
        self.secondary.add_child(Slot(view, u'secondary'))
        self.header.add_child(Slot(view, u'header'))
        self.footer.add_child(Slot(view, u'footer'))
        
    @property
    def footer(self):
        """The Panel used as footer area."""
        return self.yui_page.footer

    @property
    def header(self):
        """The Panel used as header area."""
        return self.yui_page.header

    @property
    def main(self):
        """The Panel used as main column."""
        return self.yui_page.main_block

    @property
    def secondary(self):
        """The Panel used as secondary column."""
        return self.yui_page.secondary_block
    
    
# Uses: reahl/web/reahl.ajaxlink.js
class A(HTMLElement):
    """A hyper link.

       .. admonition:: Styling

          Renders as an HTML <a> element.
    
       :param view: (See :class:`reahl.web.fw.Widget`)
       :param href: The URL (or URL fragment) to which the hyperlink leads. 
       :param description: The textual description to be shown on the hyperlink.
       :param ajax: (Not for general use)
       :param read_check: (See :class:`reahl.web.fw.Widget`)
       :param write_check: (See :class:`reahl.web.fw.Widget`)
       :param css_id: (See :class:`HTMLElement`)
    """
    @classmethod
    def from_bookmark(cls, view, bookmark):
        """Creates an A for the given `bookmark` on `view`."""
        return cls(view, bookmark.href, description=bookmark.description, ajax=bookmark.ajax, 
                   read_check=bookmark.read_check, write_check=bookmark.write_check)

    @classmethod
    def factory_from_bookmark(cls, bookmark):
        """Creates a :class:`reahl.web.fw.WidgetFactory` for creating an A for the given `bookmark`."""
        return WidgetFactory(cls, bookmark.href, description=bookmark.description, ajax=bookmark.ajax,
                             read_check=bookmark.read_check, write_check=bookmark.write_check)

    @arg_checks(href=IsInstance(Url, allow_none=True))
    def __init__(self, view, href, description=None, ajax=False, read_check=None, write_check=None, css_id=None):
        self.href = href
        self.ajax = ajax
        super(A, self).__init__(view, u'a', children_allowed=True, read_check=read_check, write_check=write_check, css_id=css_id)
        if description:
            self.add_child(TextNode(self.view, description))
        if self.ajax:
            self.append_class(u'reahl-ajaxlink')
        self.active = True

    @property
    def attributes(self):
        attributes = super(A, self).attributes
        if self.active and (not self.disabled) and self.href is not None:
            attributes.set_to(u'href', unicode(self.href))
        return attributes

    def get_js(self, context=None):
        return [u'$(%s).ajaxlink();' % self.contextualise_selector(u'".reahl-ajaxlink"', context)]

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
        super(RunningOnBadge, self).__init__(view, Url(u'http://www.reahl.org'))
        self.append_class(u'runningon')
        self.add_child(Img(view, Url(u'/static/runningon.png'), alt=u'Running on Reahl'))


class H(HTMLElement):
    """The heading for a section.

       .. admonition:: Styling

          Renders as an HTML <h1>, <h2> ... , <h6> element, depending on priority.
              
       :param view: (See :class:`reahl.web.fw.Widget`)
       :param priority: The heading level (a value from 1 to 6)
       :param text: The text value displayed in the heading (if given)
       :param css_id: (See :class:`HTMLElement`)
    """
    def __init__(self, view, priority, text=None, css_id=None):
        super(H, self).__init__(view, u'h%s' % priority, children_allowed=True, css_id=css_id)
        if text:
            self.add_child(TextNode(view, text))

class Br(HTMLElement):
    def __init__(self, view):
        super(Br, self).__init__(view, u'br', children_allowed=False)

class P(HTMLElement):
    """A paragraph of text.

       .. admonition:: Styling

          Renders as an HTML <p> element.
    
       :param view: (See :class:`reahl.web.fw.Widget`)
       :keyword text: The text value displayed in the paragraph (if given)
       :keyword css_id: (See :class:`HTMLElement`)
       :keyword html_escape: If `text` is given, by default such text is HTML-escaped. Pass False in here to prevent this from happening.
    """
    def __init__(self, view, text=None, css_id=None, html_escape=True):
        super(P, self).__init__(view, u'p', children_allowed=True, css_id=css_id)
        if text:
            self.add_child(TextNode(view, text, html_escape=html_escape))

    @property
    def text(self):
        text = u''
        for child in self.children:
            if isinstance(child, TextNode):
                text += child.value
        return text
    
    def parse_children(self, text):
        pattern = u'(?<![{])[{]([0-9]+|%s)[}](?![}])' % Template.idpattern
        last = 0
        for i in re.finditer(pattern, text):
            head = text[last:i.start()]
            last = i.end()
            yield TextNode(self.view, head.replace(u'{{', u'{').replace(u'}}',u'}'))
            yield Slot(self.view, i.groups()[0])
        yield TextNode(self.view, text[last:])

    def format(self, *args, **kwargs):
        """A complicated paragraph may consist of many TextNodes interspersed with other Widgets. Creating such a
           paragraph programmatically can be cumbersome. Instead, the `text` of a P can be a template resembling
           a `PEP-292 <http://www.python.org/dev/peps/pep-0292/>` template. This `format` method works analogously to
           :meth:`string.format`, except that Widgets can be passed in to be substituted into the original P.
           
           :param args: Positional arguments for substituting into the "template P"
           :param kwargs: Named arguments for substituting into the "template P"
        """
        filled_p = self.__class__(self.view)
        for child in self.parse_children(self.text):
            filled_p.add_child(child)

        for i in range(0,len(args)):
            filled_p.set_slot(str(i), args[i])
        for slot_name, widget in kwargs.items():
            filled_p.set_slot(slot_name, widget)
        return filled_p

    def set_slot(self, name, widget):
        self.available_slots[name].fill(widget)


class ErrorFeedbackMessage(P):
    """A user message indicating some error condition, such as a form validation which failed.

       .. admonition:: Styling
    
          Renders as an HTML <p class="error feedback"> element.
    """
    @property
    def attributes(self):
        attributes = super(ErrorFeedbackMessage, self).attributes
        attributes.add_to(u'class', [u'error', u'feedback'])
        return attributes    


class Div(HTMLElement):
    """A logical grouping of other HTMLElements.

       .. admonition:: Styling

          Renders as an HTML <div> element
    
       :param view: (See :class:`reahl.web.fw.Widget`)
       :param css_id: (See :class:`HTMLElement`)
    """
    def __init__(self, view, css_id=None):
        super(Div, self).__init__(view, u'div', children_allowed=True, css_id=css_id)



class Nav(HTMLElement):
    """A grouping of HTMLElements that refer to or link to other pages or parts within the current page. 

       .. admonition:: Styling

          Renders as an HTML <nav> element.
    
       :param view: (See :class:`reahl.web.fw.Widget`)
       :param css_id: (See :class:`HTMLElement`)
    """
    def __init__(self, view, css_id=None):
        super(Nav, self).__init__(view, u'nav', children_allowed=True, css_id=css_id)


class Article(HTMLElement):
    """An independent section of informational content.
    
       .. admonition:: Styling
       
          Renders as an HTML <article> element.
          
       :param view: (See :class:`reahl.web.fw.Widget`)
       :param css_id: (See :class:`HTMLElement`)
    """
    def __init__(self, view, css_id=None):
        super(Article, self).__init__(view, u'article', children_allowed=True, css_id=css_id)


class Header(HTMLElement):
    """A grouping of elements representing metadata pertaining to a section, such as an :class:`Article`.

       .. admonition:: Styling

          Rendered as an HTML <article> element.
    
       :param view: (See :class:`reahl.web.fw.Widget`)
       :param css_id: (See :class:`HTMLElement`)
    """
    def __init__(self, view, css_id=None):
        super(Header, self).__init__(view, u'header', children_allowed=True, css_id=css_id)


class Footer(HTMLElement):
    """The footer of a section (such as an :class:`Article`).

       .. admonition:: Styling

          Renders as an HTML <footer> element.
    
       :param view: (See :class:`reahl.web.fw.Widget`)
       :param css_id: (See :class:`HTMLElement`)
    """
    def __init__(self, view, css_id=None):
        super(Footer, self).__init__(view, u'footer', children_allowed=True, css_id=css_id)


class Li(HTMLElement):
    """A list item.
        
       .. admonition:: Styling

          Renders as an HTML <li> element.

       :param view: (See :class:`reahl.web.fw.Widget`)
       :param css_id: (See :class:`HTMLElement`)
    """
    def __init__(self, view, css_id=None):
        super(Li, self).__init__(view, u'li', children_allowed=True, css_id=css_id)
        
    
class Ul(HTMLElement):
    """An unordered list. 
    
       .. admonition:: Styling

          Renders as an HTML <ul> element.
    
       :param view: (See :class:`reahl.web.fw.Widget`)
       :param css_id: (See :class:`HTMLElement`)
    """
    def __init__(self, view, css_id=None):
        super(Ul, self).__init__(view, u'ul', children_allowed=True, css_id=css_id)


    
class Img(HTMLElement):
    """An embedded image. 

       .. admonition:: Styling
    
          Renders as an HTML <img> element.
    

       :param view: (See :class:`reahl.web.fw.Widget`)
       :param src: The URL from where the embedded image file should be fetched.
       :param alt: Alternative text describing the image.
       :param css_id: (See :class:`HTMLElement`)
    """
    def __init__(self, view, src, alt=None, css_id=None):
        super(Img, self).__init__(view, u'img', css_id=css_id)
        self.set_attribute(u'src', unicode(src))
        if alt:
            self.set_attribute(u'alt', alt)


class Panel(Div):
    """A logical container for other Widgets.

       .. admonition:: Styling
       
          Renders as an HTML <div> element.
    """
    pass


class YuiDoc(Div):
    """A Yui 2 #doc div: the container of the #hd, #bd and #ft ( see http://developer.yahoo.com/yui/grids/#start )"""
    def __init__(self, view, doc_id, doc_class, css_id=None):
        super(YuiDoc, self).__init__(view, css_id=css_id)
        self.set_id(doc_id)
        self.append_class(doc_class)
        self.hd = YuiGrid(view)   #:
        self.hd.set_id(u'hd')
        self.header = self.hd.add_child(Header(view))

        self.bd = Div(view)    #:
        self.bd.set_id(u'bd')
        self.bd.set_attribute(u'role', u'main')
        yui_main_wrapper  = self.bd.add_child(Div(view))
        self.secondary_block = self.bd.add_child(YuiBlock(view))    #: the secondary div (see Yui 2 template presents)
        yui_main_wrapper.set_id(u'yui-main')
        self.main_block = yui_main_wrapper.add_child(YuiBlock(view)) #: the #yui-main div (see Yui 2 template presents)

        self.ft = Div(view)    #:
        self.ft.set_id(u'ft')
        self.footer = self.ft.add_child(Footer(view))

        self.add_children([self.hd, self.bd, self.ft])


class YuiElement(Panel):
    yui_class = None

    @property
    def attributes(self):
        attributes = super(YuiElement, self).attributes
        attributes.add_to(u'class', [self.yui_class])
        return attributes


class YuiBlock(YuiElement):
    """A Yui 2 block: see http://developer.yahoo.com/yui/grids/#start """
    yui_class = u'yui-b'


class YuiGrid(YuiElement):
    """A Yui 2 grid: see http://developer.yahoo.com/yui/grids/#start """
    yui_class = u'yui-g'


class YuiUnit(YuiElement):
    """A Yui 2 unit: see http://developer.yahoo.com/yui/grids/#start 
    
       :param view: (See :class:`reahl.web.fw.Widget`)
       :param first: Pass True for the first YuiUnit in a YuiGrid
    """
    yui_class = u'yui-u'
    def __init__(self, view, first=False):
        super(YuiUnit, self).__init__(view)
        self.first = first

    @property
    def attributes(self):
        attributes = super(YuiUnit, self).attributes
        if self.first:
            attributes.add_to(u'class', [u'first'])
        return attributes


class Span(HTMLElement):
    """A logical grouping of other HTMLElements which fits in with text flow.

       .. admonition:: Styling
       
          Renders as an HTML <span> element.
    
       :param view: (See :class:`reahl.web.fw.Widget`)
       :param text: Will be added as text content of the Span if given.
       :param css_id: (See :class:`HTMLElement`)
    """

    def __init__(self, view, text=None, css_id=None):
        super(Span, self).__init__(view, u'span', children_allowed=True, css_id=css_id)
        if text:
            self.add_child(TextNode(view, text))



# Uses: reahl/web/reahl.form.js
class Form(HTMLElement):
    """All Inputs have to belong to a Form. When a user clicks on a Button associated with a Form, 
       the Event to which the Button is linked occurs at the server. All the values of the Inputs 
       that are associated with the Form are sent with the Event to the server.

       .. admonition:: Styling
       
          Renders as an HTML <form class="reahl-form"> element.
       
       :param view: (See :class:`reahl.web.fw.Widget`)
       :param unique_name: A name for this form, unique in the UserInterface where it is used.
       :param css_id: (See :class:`HTMLElement`)
    """
    def __init__(self, view, unique_name, rendered_form=None):
        self.view = view
        self.inputs = {}
        self.set_up_event_channel(unique_name)
        self.set_up_field_validator(u'%s_validate' % unique_name)
        self.set_up_input_formatter(u'%s_format' % unique_name)
        self.rendered_form = rendered_form or self
        assert unique_name == self.event_channel.name
        super(Form, self).__init__(view, u'form', children_allowed=True, css_id=unique_name)
        self.set_attribute(u'data-formatter', unicode(self.input_formatter.get_url()))

    def set_up_event_channel(self, event_channel_name):
        self.event_channel = EventChannel(self, self.controller, event_channel_name)
        self.view.add_resource(self.event_channel)

    def set_up_field_validator(self, field_validator_name):
        json_result = JsonResult(BooleanField(true_value=u'true', false_value=u'false'),
                                 catch_exception=ValidationConstraint)
        self.field_validator = RemoteMethod(field_validator_name, 
                                          self.validate_single_input,
                                          json_result,
                                          immutable=True)
        self.view.add_resource(self.field_validator)

    def get_forms(self):
        return [self]

    def validate_single_input(self, **input_values):
        try:
            name = input_values.keys()[0]
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
            name = input_values.keys()[0]
            return self.inputs[name].format_input(input_values)
        except (KeyError, IndexError):
            return u''
        except ValidationException:
            return u''

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
        attributes.add_to(u'class', [u'reahl-form'])
        attributes.set_to(u'action', self.action)
        attributes.set_to(u'method', u'POST')
        attributes.set_to(u'id', self.css_id)
        if self.contains_file_upload_input():
            attributes.set_to(u'enctype', u'multipart/form-data')
        return attributes

    @property
    def action(self):
        request = WebExecutionContext.get_context().request
        action = self.event_channel.get_url()
        action.query = request.query_string
        action.make_network_relative()
        return unicode(action)
    
    def register_input(self, input_widget):
        self.inputs[input_widget.name] = input_widget

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
            except ValidationConstraint, ex:
                exception = ex
            events.add(input_widget.get_ocurred_event())
        if exception:
            raise ValidationException()
        events -= set([None])
        if not len(events) == 1:
                raise ProgrammerError(u'there should always be one and only one event per form submission. Inputs submitted: %s Events detected: %s' % (input_values.keys(), events))
        return events.pop()
       
    def get_js(self, context=None):
        js = [u'$(%s).form();' % self.jquery_selector]
#        js = [u'$(%s).validate({meta: "validate"});' % self.jquery_selector]
#        js = [u'$("#%s").validate();' % self.event_channel.name]
        return super(Form, self).get_js(context=context) + js 

    @property
    def jquery_selector(self):
        return u'"form[id=%s]"' % self.css_id


class NestedForm(Div):
    """Forms may not be children of other Forms. A NestedForm may be the child of another Form, which
       means that visually, it will be rendered inside the other Form.

       .. admonition:: Styling
       
          Rendered as an HTML <div class="reahl-nested-form"> element.

       :param view: (See :class:`reahl.web.fw.Widget`)
       :param unique_name: (See :class:`Form`)
       :param css_id: (See :class:`HTMLElement`)
    """
    def __init__(self, view, unique_name, css_id=None):
        self.out_of_bound_form = Form(view, unique_name, rendered_form=self)
        super(NestedForm, self).__init__(view, css_id=u'%s_nested' % self.out_of_bound_form.css_id)
        self.add_to_attribute(u'class', [u'reahl-nested-form'])
        self.set_id(self.css_id)
        view.add_out_of_bound_form(self.out_of_bound_form)

    @property
    def form(self):
        return self.out_of_bound_form

    
class FieldSet(HTMLElement):
    def __init__(self, view, label_text=None, css_id=None):
        super(FieldSet, self).__init__(view, u'fieldset', children_allowed=True, css_id=css_id)
        if label_text:
            self.label = self.add_child(Label(view, text=label_text))
    

class InputGroup(FieldSet):
    """A visual grouping of HTMLElements inside a Form.

       .. admonition:: Styling

          Rendered as an HTML <fieldset> element.
    
       :param view: (See :class:`reahl.web.fw.Widget`)
       :param label_text: If given, the FieldSet will have a label containing this text.
       :param css_id: (See :class:`HTMLElement`)
    """
    pass



class Input(Widget):
    """A Widget that proxies data between a user and the web application.
    
       :param form: The :class:`Form` with which this Input is associated.
       :param bound_field: The :class:`reahl.component.modelinterface.Field` which validates and marshalls user 
                     input given via this Input.
    """
    input_type = None
    is_for_file = False
    
    @arg_checks(form=IsInstance(Form), bound_field=IsInstance(Field))
    def __init__(self, form, bound_field):
        self.form = form
        self.bound_field = bound_field
        self.register(form) # bound_field must be set for this registration to work
        super(Input, self).__init__(form.view, read_check=bound_field.can_read, write_check=bound_field.can_write)
        self.add_wrapped_input()

    def set_wrapped_widget(self, wrapped_widget):
        self.wrapped_widget = wrapped_widget
        
    def append_class(self, css_class):
        """Adds the word `css_class` to the "class" attribute of the HTMLElement which represents this Input in HTML to the user."""
        self.wrapped_widget.append_class(css_class)

    def set_id(self, value):
        """Set the "id" attribute of the HTMLElement which represents this Input in HTML to the user."""
        self.wrapped_widget.set_id(value)

    def set_title(self, value):
        """Set the the "title" attribute of the HTMLElement which represents this Input in HTML to the user."""
        self.wrapped_widget.set_title(value)

    def add_to_attribute(self, name, values):
        """Ensures that the value of the attribute `name` of the HTMLElement which represents this Input in 
           HTML to the user includes the words listed in `values` (a list of strings).
        """
        self.wrapped_widget.add_to_attribute(name, values)
    
    def set_attribute(self, name, value):
        """Sets the value of the attribute `name` of the HTMLElement which represents this Input in HTML to the user
           to the string `value`.
        """
        self.wrapped_widget.set_attribute(name, value)

    def can_write(self):
        return (not self.write_check) or self.write_check()

    def add_wrapped_input(self):
        self.wrapped_html_input = self.add_child(self.create_html_input())
        
    def create_html_input(self):
        """Override this in subclasses to create the HTMLElement that represents this Input in HTML to the user."""
        return HTMLElement(self.view, u'input', wrapper_widget=self)
    
    def get_wrapped_html_attributes(self, attributes):
        """Sets the HTML attributes which should be present on the HTMLElement that represents this Input
           in HTML to the user.
        """
        if self.wrapped_html_input.tag_name == u'input':
            attributes.set_to(u'type', self.input_type)
            attributes.set_to(u'value', self.value)
            attributes.set_to(u'form', self.form.css_id)
            self.add_validation_constraints_to_attributes(attributes, self.bound_field.validation_constraints)

        if self.wrapped_html_input.tag_name == u'select':
            attributes.set_to(u'form', self.form.css_id)

        attributes.set_to(u'name', self.name)
        if self.get_input_status() == u'invalidly_entered':
            attributes.add_to(u'class', [u'error'])
        if self.disabled:
            attributes.set_to(u'disabled', u'disabled')
        return attributes
        
    def register(self, form):
        form.register_input(self)
        
    def render(self):
        self.prepare_input()
        normal_output = super(Input, self).render()
        error_output = u''
        if self.get_input_status() == u'invalidly_entered':
            validation_error = self.bound_field.validation_error
            error_label = ErrorLabel(self, validation_error.message)
            error_output = error_label.render()
        return normal_output + error_output

    @property
    def name(self):
        return self.bound_field.variable_name

    @property
    def label(self):
        return self.bound_field.label

    @property
    def required(self):
        return self.bound_field.required
    
    @property
    def value(self):
        if self.get_input_status() == u'defaulted' or self.disabled:
            return self.bound_field.as_input()
        return self.bound_field.user_input
    
    @property
    def channel_name(self):
        return self.form.channel_name

    @property
    def jquery_selector(self):
        return u'''$('input[name=%s][form="%s"]')''' % (self.name, self.form.css_id)

    def get_input_status(self):
        return self.bound_field.input_status
        
    def add_validation_constraints_to_attributes(self, attributes, validation_constraints):
        html5_validations = [u'pattern', u'required', u'maxlength', u'minlength', u'accept', u'minvalue', u'maxvalue', u'remote']
        for validation_constraint in validation_constraints:
            if validation_constraint.is_remote:
                attributes.set_to(validation_constraint.name, unicode(self.form.field_validator.get_url()))
            elif validation_constraint.name in html5_validations:
                attributes.set_to(validation_constraint.name, validation_constraint.parameters)
            elif validation_constraint.name != u'':
                attributes.set_to(u'data-%s' % validation_constraint.name, validation_constraint.parameters)
        def map_name(name):
            if name in html5_validations:
                return name
            else:
                return u'data-%s' % name
        error_messages = validation_constraints.as_json_messages(map_name, [u'', RemoteConstraint.name])
        if error_messages:
            attributes.add_to(u'class', [error_messages])
        try:
            title = validation_constraints.get_constraint_named(u'pattern').message
            attributes.set_to(u'title', validation_constraints.get_constraint_named(u'pattern').message)
        except ConstraintNotFound:
            pass

    def validate_input(self, input_values):
        value = self.get_value_from_input(input_values)
        self.bound_field.set_user_input(value)

    def format_input(self, input_values):
        value = self.get_value_from_input(input_values)
        try:
            return self.bound_field.format_input(value)
        except InputParseException:
            return u''

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
                return u''
            raise ProgrammerError(u'Could not find a value for expected input %s (named %s) on form %s' % \
                                  (self, self.name, self.form))

    @property
    def persisted_userinput_class(self):
        return self.form.persisted_userinput_class

    def prepare_input(self):
        previously_entered_value = self.persisted_userinput_class.get_previously_entered_for_form(self.form, self.name)
        if previously_entered_value is not None:
            self.bound_field.set_user_input(previously_entered_value, ignore_validation=True)
        else:
            self.bound_field.clear_user_input()

    def persist_input(self, input_values):
        input_value = self.get_value_from_input(input_values)
        self.enter_value(input_value)

    def enter_value(self, input_value):
        self.persisted_userinput_class.save_input_value_for_form(self.form, self.name, input_value)


class TextArea(Input):
    """A muli-line Input for plain text.

       .. admonition:: Styling
    
          Represented in HTML as a <textarea> element.
    
       :param form: (See :class:`Input`)
       :param bound_field: (See :class:`Input`)
       :param rows: The number of rows that this Input should have.
       :param columns: The number of columns that this Input should have.
    """
    def __init__(self, form, bound_field, rows=None, columns=None):
        self.rows = rows
        self.columns = columns
        super(TextArea, self).__init__(form, bound_field)

    def create_html_input(self):
        html_text_area = HTMLElement(self.view, u'textarea', children_allowed=True, wrapper_widget=self)
        self.text = html_text_area.add_child(TextNode(self.view, self.get_value))
        return html_text_area

    def get_value(self):
        return self.value
        
    def get_wrapped_html_attributes(self, attributes):
        attributes = super(TextArea, self).get_wrapped_html_attributes(attributes)
        if self.rows:
            attributes.set_to(u'rows', unicode(self.rows))
        if self.columns:
            attributes.set_to(u'cols', unicode(self.columns))
        return attributes


class Option(HTMLElement):
    def __init__(self, view, value, label, selected=False, css_id=None):
        super(Option, self).__init__(view, u'option', children_allowed=True, css_id=css_id)
        self.add_child(TextNode(view, label))
        self.set_attribute(u'value', value)
        if selected:
            self.set_attribute(u'selected', u'selected')


class OptGroup(HTMLElement):
    def __init__(self, view, label, options, css_id=None):
        super(OptGroup, self).__init__(view, u'optgroup', children_allowed=True, css_id=css_id)
        self.set_attribute(u'label', label)
        for option in options:
            self.add_child(option)
    
    
class SelectInput(Input):
    """An Input that lets the user select an :class:`reahl.component.modelinterface.Choice` from a dropdown 
       list of valid ones.

       .. admonition:: Styling
       
          Represented in HTML as a <select> element which can contain <option> and <optgroup> children.
    
       :param form: (See :class:`Input`)
       :param bound_field: (See :class:`Input`)
    """
    def create_html_input(self):
        html_select = HTMLElement(self.view, u'select', children_allowed=True, wrapper_widget=self)
        for choice_or_group in self.bound_field.grouped_choices:
            options = [self.make_option(choice) for choice in choice_or_group.choices]
            if isinstance(choice_or_group, Choice):
                html_select.add_children(options)
            else:
                html_select.add_child(OptGroup(self.view, choice_or_group.label, options))
        return html_select

    def make_option(self, choice):
        selected = self.bound_field.is_selected(choice)
        return Option(self.view, choice.as_input(), choice.label, selected=selected)

    def get_wrapped_html_attributes(self, attributes):
        attributes = super(SelectInput, self).get_wrapped_html_attributes(attributes)
        if self.bound_field.allows_multiple_selections:
            attributes.set_to(u'multiple', u'multiple')
        return attributes

    def get_value_from_input(self, input_values):
        if self.bound_field.allows_multiple_selections:
            return input_values.get(self.name, u'')
        else:
            return super(SelectInput, self).get_value_from_input(input_values)


class SingleRadioButton(Span):
    def __init__(self, form, value, label, checked=False, wrapper_widget=None, css_id=None):
        super(SingleRadioButton, self).__init__(form.view, css_id=css_id)
        self.form = form
        self.set_attribute(u'class', u'reahl-radio-button')
        button = self.add_child(HTMLElement(self.view, u'input', wrapper_widget=wrapper_widget))
        button.set_attribute(u'type', u'radio')
        button.set_attribute(u'value', value)
        button.set_attribute(u'form', form.css_id)
        if checked:
            button.set_attribute(u'checked', u'checked')
        self.add_child(TextNode(self.view, label))


class RadioButtonInput(Input):
    """An Input that lets the user select an :class:`reahl.component.modelinterface.Choice` from a list of valid ones
       shown as radio buttons.
       
       .. admonition:: Styling
       
          Represented in HTML as a <div class="reahl-radio-button-input"> element which
          contains an <input type="radio">, wrapped in a <span class="reahl-radio-button"> for each valid
          :class:`reahl.component.modelinterface.Choice`.
    
       :param form: (See :class:`Input`)
       :param bound_field: (See :class:`Input`)
    """
    def create_html_input(self):
        outer_div = Panel(self.view)
        outer_div.set_attribute(u'class', u'reahl-radio-button-input')
        for choice in self.bound_field.flattened_choices:
            button = SingleRadioButton(self.form, choice.as_input(), choice.label, checked=self.bound_field.is_selected(choice), wrapper_widget=self)
            outer_div.add_child(button)
        self.set_wrapped_widget(outer_div)
        return outer_div

    def get_value_from_input(self, input_values):
        return input_values.get(self.name, u'')

    
# Uses: reahl/web/reahl.textinput.js
class TextInput(Input):
    """A single line Input for typing plain text.

       .. admonition:: Styling
    
          Represented in HTML by an <input type="text" class="reahl-textinput"> element.
    
       :param form: (See :class:`Input`)
       :param bound_field: (See :class:`Input`)
       :param fuzzy: If True, the typed input will be dealt with as "fuzzy input". Fuzzy input is
                     when a user is allowed to type almost free-form input for structured types of input, 
                     such as a date. The assumption is that the `bound_field` used should be able to parse
                     such "fuzzy input". If fuzzy=True, the typed value will be changed on the fly to
                     the system's interpretation of what the user originally typed as soon as the TextInput
                     looses focus.
    """
    input_type = u'text'
    def __init__(self, form, bound_field, fuzzy=False):
        super(TextInput, self).__init__(form, bound_field)
        self.append_class(u'reahl-textinput')
        
        if fuzzy:
            self.append_class(u'fuzzy')

    def get_js(self, context=None):
        js = [u'$(%s).textinput();' % self.wrapped_widget.contextualise_selector(u'".reahl-textinput"', context)]
        return super(TextInput, self).get_js(context=context) + js


class PasswordInput(Input):
    """A PasswordInput is a single line text input, but it does not show what the user is typing.

       .. admonition:: Styling
    
          Represented in HTML by a <input type="password"> element.
    
       :param form: (See :class:`Input`)
       :param bound_field: (See :class:`Input`)
    """
    input_type = u'password'

    def get_wrapped_html_attributes(self, attributes):
        attributes = super(PasswordInput, self).get_wrapped_html_attributes(attributes)
        attributes.clear(u'value')
        return attributes

    
class CheckboxInput(Input):
    """A checkbox. 
    
       .. admonition:: Styling
          
          Represented in HTML by an <input type="checkbox"> element.

       :param form: (See :class:`Input`)
       :param bound_field: (See :class:`Input`)
    """
    input_type = u'checkbox'

    def add_validation_constraints_to_attributes(self, attributes, validation_constraints):
        applicable_constraints = ValidationConstraintList()
        if self.required:
            validation_constraint = validation_constraints.get_constraint_named(u'required')
            applicable_constraints.append(validation_constraint)
        super(CheckboxInput, self).add_validation_constraints_to_attributes(attributes, applicable_constraints)
                                                   
    def get_wrapped_html_attributes(self, attributes):
        attributes = super(CheckboxInput, self).get_wrapped_html_attributes(attributes)
        attributes.clear(u'value')
        if self.value == self.bound_field.true_value:
            attributes.set_to(u'checked', u'checked')
        return attributes

    def get_value_from_input(self, input_values):
        if self.name in input_values:
            return self.bound_field.true_value
        return self.bound_field.false_value


class ButtonInput(Input):
    input_type = u'submit'
    def __init__(self, form, event):
        super(ButtonInput, self).__init__(form, event)
        if not self.controller.has_event_named(event.name):
            raise ProgrammerError(u'no Event/Transition available for name %s' % event.name)
        try:
            event.validate_default()
        except ValidationConstraint, ex:
            message = u'Arguments for %s are not valid: %s' % (event, ex)
            message += u'\n(did you forget to call .with_arguments() on an Event sent to a ButtonInput?)'
            raise ProgrammerError(message)

    def is_event(self, input_name):
        return input_name.find('?') > 0
    
    def canonicalise_input(self, input_name):
        [name_part, query_part] = input_name.split('?')
        if self.name.startswith(u'%s?' % name_part):
            incoming_arguments = u'?%s' % query_part
            canonical_input = self.bound_field.unparse_input(self.bound_field.parse_input(incoming_arguments))
            return u'%s%s' % (name_part, canonical_input)
        return None
 
    def get_value_from_input(self, input_values):
        canonicalised_inputs = [self.canonicalise_input(i) for i in input_values.keys() 
                                                           if self.is_event(i)]

        if self.name in canonicalised_inputs:
            return self.query_encoded_arguments
        else:
            return u''

    @property
    def query_encoded_arguments(self):
        return self.bound_field.as_input() or u'?'

    @property
    def name(self):
        return u'event.%s%s' % (self.bound_field.name, self.query_encoded_arguments)

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
   

class Button(Span):    
    """A button. 

       .. admonition:: Styling
    
          Represented in HTML by an <input type="submit"> element, wrapped in a <span class="reahl-button">.
    
       :param form: (See :class:`Input`)
       :param event: The :class:`reahl.web.fw.Event` that will fire when the user clicks on this ButtonInput.
       :param css_id: (See :class:`HTMLElement`)
    """
    def __init__(self, form, event, css_id=None):
        super(Button, self).__init__(form.view, css_id=css_id)
        self.html_input = self.add_child(ButtonInput(form, event))

    @property
    def attributes(self):
        attributes = super(Button, self).attributes
        attributes.add_to(u'class', [u'reahl-button'])
        return attributes


class Label(HTMLElement):
    def __init__(self, view, text=None, css_id=None):
        super(Label, self).__init__(view, u'label', children_allowed=True, css_id=css_id)
        if text:
            self.text_node = self.add_child(TextNode(view, text))

        
class InputLabel(Label):
    """A label for the Input given in `html_input`.

       .. admonition:: Styling
    
          Rendered as an HTML <label> element.

       :param html_input: The :class:`Input` labelled by this Label.
       :param text: If given, used as the text for the label rather than the default value (`html_input.label`).
       :param css_id: (See :class:`HTMLElement`)
    """
    def __init__(self, html_input, text=None, css_id=None):
        view = html_input.view
        self.html_input = html_input
        super(InputLabel, self).__init__(view, text=text or self.html_input.label, css_id=css_id)

    @property
    def visible(self):
        return self.html_input.visible

    @property
    def attributes(self):
        attributes = super(InputLabel, self).attributes
        attributes.set_to(u'for', self.html_input.name)
        return attributes


class ErrorLabel(InputLabel):
    """If an :class:`Input` fails validation, an ErrorLabel is automatically rendered after it containing
       the specific validation error message.

       .. admonition:: Styling
       
          Rendered as an HTML <label class="error"> element.

       :param html_input: (See :class:`InputLabel`)
       :param text: (See :class:`InputLabel`)
       :param css_id: (See :class:`HTMLElement`)
    """
    @property
    def attributes(self):
        attributes = super(ErrorLabel, self).attributes
        attributes.add_to(u'class', [u'error'])
        return attributes


# Uses: reahl/web/reahl.labelledinput.css
class LabelledInlineInput(Span):
    """A Widget that wraps around a given Input, adding a Label to the Input. Adheres to text flow.
    
       .. admonition:: Styling
    
          Rendered as a <span class="reahl-labelledinput"> containing the <label> followed by
          another <span> which contains the `html_input`. If the current input is not valid, it will also have 
          class reahl-state-error.

       :param html_input: (See :class:`InputLabel`)
       :param css_id: (See :class:`HTMLElement`)
    """
    label_class = InputLabel
    def __init__(self, html_input, css_id=None):
        view = html_input.view
        super(LabelledInlineInput, self).__init__(view, css_id=css_id)
        self.label = self.add_child(self.label_class(html_input))
        self.inner_span = self.add_child(Span(view))
        self.html_input = self.inner_span.add_child(html_input)
    
    @property
    def visible(self):
        return self.html_input.visible

    @property
    def attributes(self):
        attributes = super(LabelledInlineInput, self).attributes
        attributes.add_to(u'class', [u'reahl-labelledinput'])
        if self.html_input.get_input_status() == u'invalidly_entered':
            attributes.add_to(u'class', [u'reahl-state-error'])
        return attributes

# Uses: reahl/web/reahl.labelledinput.css
class LabelledBlockInput(YuiGrid):
    """A Widget that wraps around a given Input, adding a Label to the Input. Labels and their corresponding Inputs
       are arranged in columns. Successive LabelledBlockInputs are positioned underneath one another. This has the 
       effect that the Labels and Inputs of successive LabelledBlockInputs line up.
    
       .. admonition:: Styling
       
          Rendered as a <div class="reahl-labelledinput"> containing two <div> elements: one with the Label
          in it, and the other with `html_input` itself. If the current input is not valid, it will also have 
          class reahl-state-error.

       :param html_input: (See :class:`InputLabel`)
       :param css_id: (See :class:`HTMLElement`)
    """
    label_class = InputLabel
    def __init__(self, html_input, css_id=None):
        view = html_input.view
        super(LabelledBlockInput, self).__init__(view, css_id=css_id)
        self.html_input = html_input
        self.label_part = self.add_child(YuiUnit(view, first=True))
        self.label = self.label_part.add_child(self.label_class(html_input))
        self.input_part = self.add_child(YuiUnit(view))
        self.input_part.add_child(html_input)
    
    @property
    def visible(self):
        return self.html_input.visible

    @property
    def attributes(self):
        attributes = super(LabelledBlockInput, self).attributes
        attributes.add_to(u'class', [u'reahl-labelledinput'])
        if self.html_input.get_input_status() == u'invalidly_entered':
            attributes.add_to(u'class', [u'reahl-state-error'])
        return attributes


# Uses: reahl/web/reahl.cueinput.js
class CueInput(YuiGrid):
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
       :param css_id: (See :class:`HTMLElement`)
    """
    label_class = InputLabel
    def __init__(self, html_input, cue_widget, css_id=None):
        view = html_input.view
        super(CueInput, self).__init__(view, css_id=css_id)
        self.html_input = html_input

        self.label_part = self.add_child(YuiUnit(view, first=True))
        self.label = self.label_part.add_child(self.label_class(html_input))

        self.input_wrapper = self.add_child(YuiGrid(view))
        self.input_part = self.input_wrapper.add_child(YuiUnit(view, first=True))
        self.input_part.add_child(self.html_input)

        self.cue_part = self.input_wrapper.add_child(YuiUnit(view))
        self.cue_part.append_class(u'reahl-cue')
        self.cue_part.add_child(cue_widget)
        cue_widget.set_attribute(u'hidden', u'true')
        
    
    @property
    def visible(self):
        return self.html_input.visible

    @property
    def attributes(self):
        attributes = super(CueInput, self).attributes
        attributes.add_to(u'class', [u'reahl-cueinput', u'reahl-labelledinput'])
        if self.html_input.get_input_status() == u'invalidly_entered':
            attributes.add_to(u'class', [u'reahl-state-error'])
        return attributes

    def get_js(self, context=None):
        js = [u'$(%s).cueinput();' % self.contextualise_selector(u'".reahl-cueinput"', context)]
        return super(CueInput, self).get_js(context=context) + js


class AutoHideLabel(InputLabel):
    @property
    def attributes(self):
        attributes = super(AutoHideLabel, self).attributes
        if self.html_input.value != u'':
            attributes.set_to(u'hidden', u'true')
        return attributes


# Uses: reahl/web/reahl.labeloverinput.js
# Uses: reahl/web/reahl.labeloverinput.css
class LabelOverInput(LabelledInlineInput):
    """A :class:`LabelledInlineWidget` that shows the Label superimposed over the Input itself. 
       The label is only visible while the Input is empty.
    
       .. admonition:: Styling
       
          Rendered like a :class:`LabelledInlineWidget` with reahl-labeloverinput appended to the class 
          of the containing <div> element.

       :param html_input: (See :class:`InputLabel`)
       :param css_id: (See :class:`HTMLElement`)
    """
    label_class = AutoHideLabel
    @property
    def attributes(self):
        attributes = super(LabelOverInput, self).attributes
        attributes.add_to(u'class', [u'reahl-labeloverinput'])
        return attributes
        
    def get_js(self, context=None):
        js = [u'$(%s).labeloverinput();' % self.contextualise_selector(u'".reahl-labeloverinput"', context)]
        return super(LabelOverInput, self).get_js(context=context) + js


    


class MenuItem(Li):
    """One item in a Menu.
    
       .. admonition:: Styling
       
          Rendered as a <li> element. When active, includes class="active".

       Normally, a programmer would not instantiate this class directly, rather use :meth:`MenuItem.from_bookmark`.
       
       :param view: (See :class:`reahl.web.fw.Widget`)
       :param a: The :class:`A` to use as link.
       :param active_regex: If the href of `a` matches this regex, the MenuItem is deemed active.
       :param exact_match: (See :meth:`reahl.web.fw.Url.is_currently_active`)
       :param css_id: (See :class:`HTMLElement`)
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
        super(MenuItem, self).__init__(view, css_id=css_id)
        self.exact_match = exact_match
        self.a = self.add_child(a)
        self.active_regex = active_regex

    @property
    def is_active(self):
        if not self.active_regex:
            return self.a.href and self.a.href.is_currently_active(exact_path=self.exact_match)
        return re.match(self.active_regex, self.view.relative_path)

    @property
    def attributes(self):
        attributes = super(MenuItem, self).attributes
        if self.is_active:
            attributes.add_to(u'class', [u'active'])
        return attributes


class SubMenu(MenuItem):
    """A MenuItem that can contain another complete Menu itself.
    
       .. admonition:: Styling
       
          Rendered as a <li> element that contains a :class:`Menu` (see the latter for how it is rendered).

       :param view: (See :class:`reahl.web.fw.Widget`)
       :param title: Text to use as a title for this SubMenu.
       :param menu: The :class:`Menu` contained inside this SubMenu.
       :param css_id: (See :class:`HTMLElement`)
    """
    def __init__(self, view, title, menu, css_id=None):
        super(SubMenu, self).__init__(view, A(view, None, description=title), css_id=css_id)
        self.add_child(menu)


# Uses: reahl/web/reahl.menu.css
class Menu(Ul):
    """A visual menu that lists a number of Views to which the user can choose to go to.

       .. admonition:: Styling
       
          Rendered as a <ul class="reahl-menu"> element that contains a <li> for each MenuItem.

       :param view: (See :class:`reahl.web.fw.Widget`)
       :param a_list: A list of :class:`A` instances to which each :class:`MenuItem` will lead.
       :param css_id: (See :class:`HTMLElement`)
    """
    @classmethod
    def from_languages(cls, view):
        """Constructs a Menu which contains a MenuItem for each locale supported by all the components
           in this application.

           :param view: (See :class:`reahl.web.fw.Widget`)
        """
        menu = cls(view, [])
        current_url = Url.get_current_url()
        context = WebExecutionContext.get_context()
        supported_locales = ReahlEgg.get_languages_supported_by_all(context.config.reahlsystem.root_egg)
        for locale in supported_locales:
            try:
                language_name = Locale.parse(locale).display_name
            except UnknownLocaleError:
                language_name = locale
            a = A(view, current_url.with_new_locale(locale), description=language_name)
            menu.add_item(MenuItem(view, a, exact_match=True))
        return menu

    @classmethod
    def from_bookmarks(cls, view, bookmark_list):
        """Creates a Menu with a MenuItem for each Bookmark given in `bookmark_list`."""
        menu = cls(view, [])
        for bookmark in bookmark_list:
            a = A.from_bookmark(view, bookmark)
            menu.add_item(MenuItem(view, a, exact_match=bookmark.exact))
        return menu

    def __init__(self, view, a_list, css_id=None):
        super(Menu, self).__init__(view, css_id=css_id)
        self.append_class(u'reahl-menu')
        self.set_items_from(a_list)

    def set_items_from(self, a_list):
        self.menu_items = [MenuItem(self.view, a) for a in a_list]
        self.add_children(self.menu_items)

    def add_item(self, item):
        """Adds MenuItem `item` to this Menu."""
        self.add_child(item)
        self.menu_items.append(item)


# Uses: reahl/web/reahl.hmenu.css
class HMenu(Menu):
    """A Menu, with items displayed next to each other.

       .. admonition:: Styling
       
          Rendered as a <ul class="reahl-menu reahl-horizontal">

       :param view: (See :class:`reahl.web.fw.Widget`)
       :param a_list: (See :class:`Menu`)
       :param css_id: (See :class:`HTMLElement`)
    """
    @property
    def attributes(self):
        attributes = super(HMenu, self).attributes
        attributes.add_to(u'class', [u'reahl-horizontal'])
        return attributes


class VMenu(Menu):
    """A Menu, with items displayed underneath each other.

       .. admonition:: Styling
       
          Rendered as a <ul class="reahl-menu reahl-vertical">

       :param view: (See :class:`reahl.web.fw.Widget`)
       :param a_list: (See :class:`Menu`)
       :param css_id: (See :class:`HTMLElement`)
    """
    @property
    def attributes(self):
        attributes = super(VMenu, self).attributes
        attributes.add_to(u'class', [u'reahl-vertical'])
        return attributes


class Tab(MenuItem):
    """One Tab in a :class:`TabbedPanel`.

       .. admonition:: Styling
       
          Rendered like a :class:`MenuItem`, with the <a> containing `title`.

       :param view: (See :class:`reahl.web.fw.Widget`)
       :param title: Text that is displayed inside the Tab itself.
       :param tab_key: A name for this tag identifying it uniquely amongst other Tabs in the same :class:`TabbedPanel`.
       :param contents_factory: A :class:`WidgetFactory` specifying how to create the contents of this Tab, once selected.
       :param css_id: (See :class:`HTMLElement`)
    """
    def __init__(self, view, title, tab_key, contents_factory, css_id=None):
        self.title = title
        self.tab_key = tab_key
        self.contents_factory = contents_factory
        self.force_active = False
        a = A.from_bookmark(view, self.get_bookmark())
        super(Tab, self).__init__(view, a, css_id=css_id)
        
    def get_bookmark(self):
        query_arguments={'tab': self.tab_key}
        return Bookmark(u'', u'', description=self.title, query_arguments=query_arguments, ajax=True)

    @property
    def is_active(self):
        return super(Tab, self).is_active or self.force_active

    def add_content_to_panel(self, panel):
        panel.add_child(self.contents_factory.create(self.view))


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
       :param css_id: (See :class:`HTMLElement`)
    """
    def __init__(self, view, title, tab_key, contents_factory, css_id=None):
        self.tab_key = tab_key
        self.contents_factory = contents_factory
        super(MultiTab, self).__init__(view, title, tab_key, contents_factory, css_id=css_id)
        self.add_child(TextNode(view, u'&nbsp;', html_escape=False))
        dropdown_handle = self.add_child(A(view, None, description=u'▼'))
        dropdown_handle.append_class(u'dropdown-handle')
        self.menu = self.add_child(VMenu(view, []))
    
    def add_tab(self, tab):
        self.menu.add_item(tab)

    @property
    def first_tab(self):
        return self.menu.menu_items[0]
        
    @property
    def current_sub_tab(self):
        active_tab = [tab for tab in self.menu.menu_items 
                      if tab.is_active]
        if len(active_tab) == 1:
            return active_tab[0]
        return self.first_tab

    def add_content_to_panel(self, panel):
        if super(MultiTab, self).is_active:
            super(MultiTab, self).add_content_to_panel(panel)
        else:
            self.current_sub_tab.add_content_to_panel(panel)

    @property
    def is_active(self):
        return super(MultiTab, self).is_active or self.current_sub_tab.is_active


# Uses: reahl/web/reahl.tabbedpanel.css
# Uses: reahl/web/reahl.tabbedpanel.js
class TabbedPanel(Panel):
    """A Panel sporting different Tabs which the user can select to change what is displayed. The contents
       of a TabbedPanel are changed when the user clicks on a different Tab without refreshing the entire
       page, provided that JavaScript is available on the user agent.
    
       .. admonition:: Styling

          Rendered as a <div class="reahl-tabbedpanel"> which contains two children: an :class:`HMenu` 
          containing instances of :class:`Tab` for MenuItems, followed by a <div> that will be populated
          by the current contents of the TabbedPanel.

       :param view: (See :class:`reahl.web.fw.Widget`)
       :param css_id: (See :class:`HTMLElement`)
    """
    def __init__(self, view, css_id):
        super(TabbedPanel, self).__init__(view, css_id=css_id)
        self.append_class(u'reahl-tabbedpanel')
        self.tabs = self.add_child(HMenu(view, []))
        self.content_panel = self.add_child(Panel(view))
        self.enable_refresh()

    @exposed
    def query_fields(self, fields):
        fields.tab = Field(required=False, default=None)

    @property
    def active_tab_set(self):
        return self.tab is not None
        
    def set_active(self, tab):
        tab.force_active = True
        self.tab = tab.tab_key

    def add_tab(self, tab):
        """Adds the Tab `tab` to this TabbedPanel."""
        self.tabs.add_item(tab)
        if not self.active_tab_set:
            self.set_active(tab)

        if tab.is_active:
            tab.add_content_to_panel(self.content_panel)    


# Uses: reahl/web/reahl.slidingpanel.css
# Uses: reahl/web/reahl.slidingpanel.js
class SlidingPanel(Panel):
    """A Panel which contains a number of other Panels, only one of which is displayed at a time.
       It sports controls that can be clicked by a user to advance the displayed content to the
       next or previous Panel. Advancing is done by visually sliding in the direction indicated
       by the user if JavaScript is available. The panels advance once every 10 seconds if no
       user action is detected.
    
       .. admonition:: Styling

          Rendered as a <div class="reahl-slidingpanel"> which contains three children: a <div class="viewport">
          flanked on either side by an <a> (the controls for forcing it to transition left or right).
          The :class:`Panel` instances added to the :class:`SlidingPanel` are marked with a ``class="contained"``.

          For a SlidingPanel to function property, you need to specify a height and width to 
          ``div.reahl-slidingpanel div.viewport``.

       :param view: (See :class:`reahl.web.fw.Widget`)
       :keyword css_id: (See :class:`HTMLElement`)
       :keyword next: Text to put in the link clicked to slide to the next panel.
       :keyword prev: Text to put in the link clicked to slide to the previous panel.
    """
    def __init__(self, view, css_id=None, next=u'>', prev=u'<'):
        super(SlidingPanel, self).__init__(view, css_id=css_id)
        self.append_class(u'reahl-slidingpanel')
        self.container = Panel(view)
        self.container.append_class(u'viewport')
        self.prev = self.add_child(A.from_bookmark(view, self.get_bookmark(index=self.previous_index, description=prev)))
        self.add_child(self.container)
        self.next = self.add_child(A.from_bookmark(view, self.get_bookmark(index=self.next_index, description=next)))

    def add_panel(self, panel):
        """Adds `panel` to the list of :class:`Panel` instances that share the same visual space."""
        panel.append_class(u'contained')
        self.container.add_child(panel)
        if self.max_panel_index != self.index:
            panel.add_to_attribute(u'style', [u'display: none;'])
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
        description = (u'%s' % index) if description is None else description
        return Bookmark.for_widget(description, query_arguments={u'index': index})
        
    @exposed
    def query_fields(self, fields):
        fields.index = IntegerField(required=False, default=0)

    def get_js(self, context=None):
        selector = self.contextualise_selector(self.jquery_selector, context)
        return [u'$(%s).slidingpanel();' % selector]

    @property
    def jquery_selector(self):
        return u'".reahl-slidingpanel"'


class SimpleFileInput(Input):
    """An Input for selecting a single file which will be uploaded once the user clicks on any :class:`Button`
       associated with the same :class:`Form` as this Input.
    
       .. admonition:: Styling
          
          Represented in HTML by an <input type="file"> element. Can have attribute multiple set,
          if allowed by the `bound_field`.

       :param form: (See :class:`Input`)
       :param bound_field: (See :class:`Input`, must be of type :class:`reahl.component.modelinterface.FileField`
    """
    input_type = u'file'
    is_for_file = True
    def create_html_input(self):
        add_file = HTMLElement(self.view, u'input', wrapper_widget=self)
        if self.bound_field.allow_multiple:
            add_file.set_attribute(u'multiple', u'multiple')
        return add_file

    def get_value_from_input(self, input_values):
        field_storages = input_values.getall(self.name)

        def file_size(field_storage):
            field_storage.file.seek(0, 2)
            size = field_storage.file.tell()
            field_storage.file.seek(0)
            return size
        return [UploadedFile(unicode(field_storage.filename), field_storage.file, unicode(field_storage.type), file_size(field_storage)) 
                 for field_storage in field_storages
                 if field_storage != u'']

    @property
    def value(self):
        return u''

    @property
    def persisted_exception_class(self):
        return self.form.persisted_exception_class

    def prepare_input(self):
        previous_exception = self.persisted_exception_class.get_exception_for_input(self.form, self.name)
        if previous_exception is not None:
            self.bound_field.validation_error = previous_exception
            self.bound_field.input_status = u'invalidly_entered'

    def persist_input(self, input_values):
        if self.get_input_status() == u'invalidly_entered':
            self.persisted_exception_class.new_for_form(self.form, input_name=self.name, exception=self.bound_field.validation_error)


# Uses: reahl/web/reahl.fileuploadli.js
class FileUploadLi(Li):
    def __init__(self, form, remove_event, persisted_file, css_id=None):
        super(FileUploadLi, self).__init__(form.view, css_id=css_id)
        self.set_attribute(u'class', u'reahl-file-upload-li')
        self.add_child(Button(form, remove_event.with_arguments(filename=persisted_file.filename)))
        self.add_child(Span(self.view, persisted_file.filename))


    def get_js(self, context=None):
        return [u'$(".reahl-file-upload-li").fileuploadli();']


# Uses: reahl/web/reahl.fileuploadpanel.js
class FileUploadPanel(Panel):
    def __init__(self, file_upload_input, css_id=None):
        super(FileUploadPanel, self).__init__(file_upload_input.view, css_id=css_id)
        self.set_attribute(u'class', u'reahl-file-upload-panel')
        self.file_upload_input = file_upload_input

        self.add_nested_form()
        self.add_uploaded_list()
        self.add_upload_controls()

    def add_nested_form(self):
        self.upload_form = self.add_child(NestedForm(self.view, u'%s-%s-upload' % (self.input_form.css_id, self.bound_field.name)))
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
        controls_panel = self.upload_form.add_child(Panel(self.view))
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
                                   action=Action(self.remove_file, [u'filename']),
                                   filename=Field(required=True))
            
    @exposed
    def fields(self, fields):
        fields.uploaded_file = self.bound_field.unbound_copy()
        fields.uploaded_file.disallow_multiple()
        fields.uploaded_file.add_validation_constraint(UniqueFilesConstraint(self.input_form, self.bound_field.name))

    def attach_jq_widget(self, selector, widget_name, **options):
        def js_repr(value):
            if type(value) in [str, unicode]:
                return u'"%s"' % value
            return value
        option_args = u','.join([u'%s: %s' % (name, js_repr(value)) for name, value in options.items()])
        return u'$(%s).%s({%s});' % (selector, widget_name, option_args)

    def get_js(self, context=None):
        selector = self.contextualise_selector(u'"#%s .reahl-file-upload-panel"' % self.input_form.css_id, context)
        unique_names_constraint = self.fields.uploaded_file.get_validation_constraint_of_class(UniqueFilesConstraint)
        js = self.attach_jq_widget(selector, u'fileuploadpanel', 
                    form_id=self.upload_form.form.css_id, 
                    nested_form_id=self.upload_form.css_id,
                    input_form_id=self.input_form.css_id,
                    errorMessage=_(u'an error occurred, please try again later.'),
                    removeLabel=self.events.remove_file.label,
                    cancelLabel=_(u'Cancel'),
                    duplicateValidationErrorMessage=unique_names_constraint.message,
                    waitForUploadsMessage=_(u'Please try again when all files have finished uploading.'))
        return super(FileUploadPanel, self).get_js(context=context) + [js]

    def remove_file(self, filename):
        self.persisted_file_class.remove_persisted_for_form(self.input_form, self.name, filename)

    def upload_file(self):
        if self.uploaded_file is not None:
            self.persisted_file_class.add_persisted_for_form(self.input_form, self.name, self.uploaded_file)


class UniqueFilesConstraint(ValidationConstraint):
    name = 'uniquefiles'
    def __init__(self, form=None, input_name=None, error_message=None):
        error_message = error_message or _(u'uploaded files should all have different names')
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


class FileUploadInput(Input):
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

       :param form: (See :class:`Input`)
       :param bound_field: (See :class:`Input`, must be of type :class:`reahl.component.modelinterface.FileField`
    """

    @property
    def persisted_file_class(self):
        config = WebExecutionContext.get_context().config
        return config.web.persisted_file_class

    def create_html_input(self):
        return FileUploadPanel(self)

    def get_value_from_input(self, input_values):
        return [UploadedFile(f.filename, f.file_obj, f.content_type, f.size) 
                 for f in self.persisted_file_class.get_persisted_for_form(self.form, self.name)]

    def enter_value(self, input_value):
        pass


class DialogButton(object):
    def __init__(self, label):
        self.label = label

    def callback_js(self):
        return u''
        
    def as_jquery(self):
        return u'"%s": function() { %s }' % (self.label, self.callback_js())


class CheckCheckboxButton(DialogButton):
    def __init__(self, label, checkbox):
        super(CheckCheckboxButton, self).__init__(label)
        self.checkbox_to_check = checkbox
        
    def callback_js(self):
        return u'''$(%s).attr("checked", true);''' %  self.checkbox_to_check.jquery_selector

        
# Uses: reahl/web/reahl.popupa.js
class PopupA(A):
    # Implements:
    # http://blog.nemikor.com/category/jquery-ui/jquery-ui-dialog/
    # ... with buttons added
    def __init__(self, view, target_bookmark, show_for_selector, close_button=True, css_id=None):
        super(PopupA, self).__init__(view, target_bookmark.href, target_bookmark.description, css_id=css_id)
        self.set_title(target_bookmark.description)
        self.append_class(u'reahl-popupa')
        self.show_for_selector = show_for_selector
        self.buttons = []
        if close_button:
            self.add_button(DialogButton(_(u'Close')))
        
    def add_button(self, button):
        self.buttons.append(button)

    def buttons_as_jquery(self):
        return u', '.join([button.as_jquery() for button in self.buttons])

    @property
    def jquery_selector(self):
        return u'"a.reahl-popupa[href=\'%s\']"' % self.href

    def get_js(self, context=None):
        selector = self.contextualise_selector(self.jquery_selector, context)
        return [u'$(%s).popupa({showForSelector: "%s", buttons: { %s }  });' % \
              (selector, self.show_for_selector, self.buttons_as_jquery())]

