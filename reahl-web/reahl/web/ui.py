# Copyright 2013-2022 Reahl Software Services (Pty) Ltd. All rights reserved.
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
import time
from string import Template
import copy
import re
import html
import json
from collections import OrderedDict
from collections.abc import Callable

from reahl.component.decorators import deprecated
from reahl.component.exceptions import IsInstance
from reahl.component.exceptions import ProgrammerError, DomainException
from reahl.component.exceptions import arg_checks
from reahl.component.i18n import Catalogue
from reahl.component.context import ExecutionContext
from reahl.component.modelinterface import ExposedNames, ValidationConstraintList, ValidationConstraint, ExpectedInputNotFound,\
    Field, Event, BooleanField, Choice, UploadedFile, InputParseException, StandaloneFieldIndex, MultiChoiceField, ChoiceField, Action
from reahl.web.csrf import CSRFTokenField
from reahl.web.fw import EventChannel, RemoteMethod, JsonResult, Widget, \
    ValidationException, WidgetResult, WidgetFactory, Url, ErrorWidget, Layout
from reahl.mailutil.rst import RestructuredText

_ = Catalogue('reahl-web')


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
        super().__init__(view)
        self.contents = contents
        self.transform = transform

    def render(self):
        return self.transform(self.contents)

    @classmethod
    def from_restructured_text(cls, view, text, heading_level_start=1):
        return cls(view, RestructuredText(text).as_HTML_fragment(header_start=heading_level_start))
    

class HTMLAttributeValueOption:
    def __init__(self, option_string, is_set, prefix='', delimiter='-', constrain_value_to=None, map_values_using=None):
        if is_set and (constrain_value_to and option_string not in constrain_value_to):
            allowed_strings = ','.join(['"%s"' % i for i in constrain_value_to])
            raise ProgrammerError('"%s" should be one of: %s' % (option_string, allowed_strings))
        self.is_set = is_set
        self.delimiter = delimiter
        self.prefix = prefix
        self.option_string = map_values_using.get(option_string, option_string) if map_values_using else option_string

    def as_html_snippet(self):
        if not self.is_set:
            raise ProgrammerError('Attempt to add %s to html despite it not being set' % self)
        prefix_with_delimiter = '%s%s' % (self.prefix, self.delimiter) if self.prefix else ''
        return '%s%s' % (prefix_with_delimiter, self.option_string)


class HTMLAttribute:
    def __init__(self, name, values):
        super().__init__()
        self.name = name
        self.value = set(values)

    def as_html_snippet(self):
        if not self.value:
            return ''
#        return '''%s='%s\'''' % (self.name, self.as_html_value())
        return '%s="%s"' % (self.name, html.escape(self.as_html_value()))

    def as_html_value(self):
        return ' '.join(sorted(self.value))

    def remove_values(self, values):
        self.value -= set(values)

    def add_values(self, values):
        self.value |= set(values)
        return values


class HTMLAttributeValues:
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
        return attribute.add_values(values)

    def remove_from(self, name, values):
        attribute = self.get(name)
        if attribute:
            attribute.remove_values(values)

    def set_to(self, name, value):
        assert value is not None
        self[name] = HTMLAttribute(name, [value])

    def clear(self, name):
        del self[name]


class AjaxMethod(RemoteMethod):
    def __init__(self, widgets, method_name):
        super().__init__(widgets[0].view, method_name, self.fire_ajax_event, WidgetResult(widgets), immutable=True, method='post')
        self.widgets = widgets

    def cleanup_after_exception(self, input_values, ex):
        self.view.save_last_construction_state()
        self.persist_invalid_input()
        
    def cleanup_after_success(self):
        self.view.save_last_construction_state()
        self.persist_invalid_input()

    @property
    def contained_forms(self):
        return set([widget for widget in self.view.page.contained_widgets() if widget.is_Form])

    def persist_invalid_input(self):
        for form in self.contained_forms:
            form.clear_all_saved_data()
            form.persist_invalid_input()

    def fire_ajax_event(self, *args, **kwargs):
        state = self.view.current_POSTed_state_as_dict_of_lists

        for widget in self.view.page.contained_widgets():
            widget.accept_disambiguated_input(state)

        try:
            for widget in self.widgets:
                widget.fire_on_refresh()
        finally:
            construction_state = {}
            for widget in self.view.page.contained_widgets():
                widget.update_construction_state(construction_state)
            self.view.set_construction_state_from_state_dict(construction_state)

    def as_jquery_parameter(self):
        return {'url':str(self.get_url())}


# Uses: reahl/web/reahl.hashchange.js
class HashChangeHandler:
    def __init__(self, widget, for_fields):
        self.widget = widget
        self.for_fields = for_fields
        self.remote_method = AjaxMethod([widget], 'refresh_%s' % widget.css_id)
        widget.view.add_resource(self.remote_method)

    @property
    def argument_defaults(self):
        field_defaults = self.for_fields.as_input_kwargs() # TODO: should this not sometimes be i.user_input????
        argument_defaults = OrderedDict([(name, default_value or '')
                                        for name, default_value in field_defaults.items()])
        return argument_defaults

    def as_jquery_parameter(self):
        params = self.remote_method.as_jquery_parameter()
        params['params'] = self.argument_defaults
        return params


class CssId:
    invalid_char_re = re.compile(r'([^a-zA-Z0-9_-])')
    @classmethod
    def from_dirty_string(cls, dirty_string):
        return cls(cls.invalid_char_re.sub(lambda m: '-%s-' % ord(m.group(1)), dirty_string))

    def __init__(self, id_string):
        invalid_characters = set(self.invalid_char_re.findall(id_string))
        if invalid_characters:
            raise ProgrammerError('"%s" contains characters that are not valid in a css id: %s' % (id_string, invalid_characters))
        self.id_string = id_string

    def __str__(self):
        return self.id_string

    def __eq__(self, other):
        return self.id_string == other.id_string

    def __hash__(self):
        return hash(self.id_string)


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
        super().__init__(view, read_check=read_check, write_check=write_check)
        self.attribute_sources = []
        self.children_allowed = children_allowed
        self.tag_name = tag_name
        self.constant_attributes = HTMLAttributeDict()
        self.ajax_handler = None
        self.on_refresh = Event()
        if css_id:
            self.set_id(css_id)

    def __str__(self):
        return '<%s %s%s>' % (self.__class__.__name__, self.tag_name, self.attributes.as_html_snippet())

    def enable_refresh(self, *for_fields, **kwargs):
        """Sets this HTMLElement up so that it can be refreshed without reloading the whole page.

           **enable_refresh(self, *for_fields, on_refresh=None)**
        
           A refresh is triggered when:
            - one of the `query_fields` given in `for_fields` change'; or
            - if no `for_fields` are given, when any of its `query_fields` change; or
            - if a :class:`PrimitiveInput` refers to this HTMLElement via its `refresh_widget`.

           :keyword on_refresh: An :class:`~reahl.component.modelinterface.Event` that will be triggered upon refresh, before rerendering.
           :arg for_fields: A selection of the :meth:`~reahl.web.fw.Widget.query_fields` defined on this HTMLElement.

           .. versionchanged:: 3.2
              The `for_fields` arguments were added to allow control over which of an
              HTMLElement's `query_fields` trigger a refresh.

           .. versionchanged:: 5.0
              Added `on_refresh`.   
        """
        on_refresh = kwargs.get('on_refresh', None)

        if not self.css_id_is_set:
            raise ProgrammerError('%s does not have a css_id set. A fixed css_id is mandatory when a Widget self-refreshes' % self)
        assert all([(self.query_fields.contains_instantiated_value(field)) for field in for_fields])

        self.add_hash_change_handler(StandaloneFieldIndex.from_list(for_fields) if for_fields else self.query_fields)
        if on_refresh:
            self.on_refresh = on_refresh
            self.fire_on_refresh()

    @property
    def is_refresh_enabled(self):
        return self.ajax_handler is not None

    def fire_on_refresh(self):
        self.on_refresh.make_occurred()
        self.on_refresh.fire()

    def add_child(self, child):
        assert self.children_allowed, 'You cannot add children to a %s' % type(self)
        return super().add_child(child)

    def add_attribute_source(self, attribute_source):
        self.attribute_sources.append(attribute_source)
        return attribute_source

    def add_to_attribute(self, name, values):
        """Ensures that the value of the attribute `name` of this HTMLElement includes the words listed in `values`
           (a list of strings).
        """
        return self.constant_attributes.add_to(name, values)

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
        return self.ajax_handler

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
        return str(self._css_id)
    def set_css_id(self, value):
        self._css_id = CssId(value)
        self.set_attribute('id', self.css_id)
    css_id = property(get_css_id, set_css_id)

    def generate_random_css_id(self):
        if not self.css_id_is_set:
            self.set_css_id('tmpid-%s-%s' % (id(self), str(time.time()).replace('.', '-')))
        else:
            raise ProgrammerError('%s already has a css_id set, will not overwrite it!' % self)
        return self.css_id

    def contextualise_selector(self, selector, context):
        """Returns a JQuery selector for finding `selector` within the elements matched by `context` (another selector)."""
        context_str = ', "%s"' % context if context else ''
        return '%s%s' % (selector, context_str)

    @property
    def jquery_selector(self):
        """Returns a string (including its " delimiters) which can be used to target this HTMLElement using
           JQuery. By default this uses the id attribute of the HTMLElement, but this property can be overridden to
           not be dependent on the id attribute of the HTMLElement.

           :raises ProgrammerError: Raised when accessing `jquery_selector` if the css_id of this HTMLElement is not set.
        """
        return '"#%s"' % (self.css_id)

    def get_js(self, context=None):
        js = []
        if self.is_refresh_enabled:
            js = ['$(%s).hashchange(%s);' % \
                  (self.contextualise_selector(self.jquery_selector, context),
                   json.dumps(self.ajax_handler.as_jquery_parameter())
                   )]
        return super().get_js(context=context) + js

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
       :keyword html_escape: If True (default), the given `value` will first be HTML-escaped before rendered to the browser.
    """
    def __init__(self, view, value_or_getter, html_escape=True):
        super().__init__(view)
        self.html_escape = html_escape
        if isinstance(value_or_getter, Callable):
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
        return html.escape(self.value, quote=False) if self.html_escape else self.value


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
        super().__init__(view, 'title', children_allowed=True, css_id=css_id)
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
        super().__init__(view, 'link', css_id=css_id)
        self.set_attribute('rel', rel)
        self.set_attribute('href', str(href))
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
        super().__init__(view)
        self.name = name

    @property
    def available_slots(self):
        return {self.name: self}

    def fill(self, widget):
        self.clear_children()
        self.add_child(widget)


class Meta(HTMLElement):
    def __init__(self, view, name, content):
        super().__init__(view, 'meta', children_allowed=False)
        self.set_attribute('name', name)
        self.set_attribute('content', content)


class Head(HTMLElement):
    """A container for metadata of a View.

       .. admonition:: Styling

          Renders as an HTML <head> element.

       :param view: (See :class:`reahl.web.fw.Widget`)
       :param title: Text for a template to be used as document Title (See also :class:`Title`).
       :keyword css_id: (See :class:`reahl.web.ui.HTMLElement`)
    """
    def __init__(self, view, title, css_id=None):
        super().__init__(view, 'head', children_allowed=True, css_id=css_id)
        self.title = self.add_child(Title(view, title))
        self.add_child(Slot(view, name='reahl_header'))

    def add_css(self, href):
        return self.add_child(Link(self.view, 'stylesheet', href, 'text/css'))


class Body(HTMLElement):
    """The content of an HTML document.

       .. admonition:: Styling

          Renders as an HTML <body> element.

       :param view: (See :class:`reahl.web.fw.Widget`)
       :keyword css_id: (See :class:`reahl.web.ui.HTMLElement`)

    """
    def __init__(self, view, css_id=None):
        super().__init__(view, 'body', children_allowed=True, css_id=css_id)
        self.out_of_bound_container = self.add_child(Div(self.view, css_id='_reahl_out_of_bound_container'))
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
        super().add_child(child)
        if existing_footer:
            self.children.append(existing_footer)
        return child

    def attach_out_of_bound_widgets(self, widgets):
        self.out_of_bound_container.add_children(widgets)

    def get_out_of_bound_container(self):
        return self.out_of_bound_container



class PlainHTMLErrorPage(ErrorWidget):
    def __init__(self, view, page_class, *widget_args, **widget_kwargs):
        super().__init__(view)
        page = self.add_child(page_class(view, *widget_args, **widget_kwargs))
        error_div = page.body.insert_child(0, Div(view))
        error_div.add_child(H(view, 1, text=_('An error occurred:')))
        error_div.add_child(P(view, text=self.error_message))
        error_div.add_child(A(view, Url(self.error_source_href), description=_('Ok')))


class HTML5Page(HTMLElement):
    """A web page that may be used as the page of a web application. It ensures that everything needed by
       the framework (linked CSS and JavaScript, etc) is available on such a page.

       .. admonition:: Styling

          Renders as an HTML5 page with customised <head> and an empty <body>.

       :param view: (See :class:`reahl.web.fw.Widget`)
       :keyword title: Text for a template to be used as document Title (See also :class:`Title`).
       :keyword css_id: (See :class:`reahl.web.ui.HTMLElement`)

       .. versionchanged:: 4.0
          Removed style= keyword
    """
    @classmethod
    def get_error_page_factory(cls, *widget_args, **widget_kwargs):
        return PlainHTMLErrorPage.factory(cls, *widget_args, **widget_kwargs)

    @arg_checks(title=IsInstance(str))
    def __init__(self, view, title='$current_title', css_id=None):
        super().__init__(view, 'html', children_allowed=True, css_id=css_id)
        self.append_class('no-js')
        script = self.add_child(HTMLElement(self.view, 'script', children_allowed=True))
        script.add_child(TextNode(self.view, '''
          function switchJSStyle(d, fromStyle, toStyle) {
              var r=d.querySelectorAll("html")[0];
              r.className=r.className.replace(new RegExp("\\\\b" + fromStyle + "\\\\b", "g"),toStyle)
          };
          (function(d) { switchJSStyle(d, "no-js", "js"); })(document);
        ''', html_escape=False))

        self.set_attribute('data-reahl-rendered-state', self.view.current_POSTed_client_side_state) # needed by reahl.hashchange.js
        self.head = self.add_child(Head(view, title))  #: The Head HTMLElement of this page
        self.body = self.add_child(Body(view))         #: The Body HTMLElement of this page

    def render(self):
        return '<!DOCTYPE html>' + super().render()


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
        super().__init__(view, 'a', children_allowed=True, read_check=read_check, write_check=write_check, css_id=css_id)
        if description:
            self.add_child(TextNode(self.view, description))
        if self.ajax:
            self.append_class('reahl-ajaxlink')
        self.active = True

    @property
    def attributes(self):
        attributes = super().attributes
        if self.active and (not self.disabled) and self.href is not None:
            attributes.set_to('href', str(self.href))
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
        super().__init__(view, Url('http://www.reahl.org'))
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
        super().__init__(view, 'h%s' % priority, children_allowed=True, css_id=css_id)
        if text:
            self.add_child(TextNode(view, text))


class Br(HTMLElement):
    """A hard break.

       .. admonition:: Styling

          Renders as an HTML <br> element.

       :param view: (See :class:`reahl.web.fw.Widget`)
    """
    def __init__(self, view):
        super().__init__(view, 'br', children_allowed=False)


class Hr(HTMLElement):
    """An horizontal rule.

       .. admonition:: Styling

          Renders as an HTML <hr> element.

       :param view: (See :class:`reahl.web.fw.Widget`)
    """
    def __init__(self, view):
        super().__init__(view, 'hr', children_allowed=False)


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
        super().__init__(view, 'p', children_allowed=True, css_id=css_id)
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
           :keyword kwargs: Named arguments for substituting into the "template P"
        """
        filled_p = self.__class__(self.view)
        for child in self.parse_children(self.text):
            filled_p.add_child(child)

        for i in list(range(0, len(args))):
            filled_p.set_slot(str(i), args[i])
        for slot_name, widget in kwargs.items():
            filled_p.set_slot(slot_name, widget)
        return filled_p

    def set_slot(self, name, widget):
        self.available_slots[name].fill(widget)


class Small(HTMLElement):
    """A paragraph of text with tag name `small`.

       .. admonition:: Styling

          Renders as an HTML <small> element.

       :param view: (See :class:`reahl.web.fw.Widget`)
       :keyword text: The text value displayed in the paragraph (if given)
       :keyword css_id: (See :class:`reahl.web.ui.HTMLElement`)
       :keyword html_escape: If `text` is given, by default such text is HTML-escaped. Pass False in here to prevent this from happening.

       .. versionadded:: 4.0
    """
    def __init__(self, view, text=None, css_id=None, html_escape=True):
        super().__init__(view, 'small', children_allowed=True, css_id=css_id)
        if text:
            self.add_child(TextNode(view, text, html_escape=html_escape))


class Div(HTMLElement):
    """A logical grouping of other HTMLElements.

       .. admonition:: Styling

          Renders as an HTML <div> element

       :param view: (See :class:`reahl.web.fw.Widget`)
       :keyword css_id: (See :class:`reahl.web.ui.HTMLElement`)

    """
    def __init__(self, view, css_id=None):
        super().__init__(view, 'div', children_allowed=True, css_id=css_id)



class Nav(HTMLElement):
    """A grouping of HTMLElements that refer to or link to other pages or parts within the current page.

       .. admonition:: Styling

          Renders as an HTML <nav> element.

       :param view: (See :class:`reahl.web.fw.Widget`)
       :keyword css_id: (See :class:`reahl.web.ui.HTMLElement`)

    """
    def __init__(self, view, css_id=None):
        super().__init__(view, 'nav', children_allowed=True, css_id=css_id)


class Article(HTMLElement):
    """An independent section of informational content.

       .. admonition:: Styling

          Renders as an HTML <article> element.

       :param view: (See :class:`reahl.web.fw.Widget`)
       :keyword css_id: (See :class:`reahl.web.ui.HTMLElement`)

    """
    def __init__(self, view, css_id=None):
        super().__init__(view, 'article', children_allowed=True, css_id=css_id)


class Header(HTMLElement):
    """A grouping of elements representing metadata pertaining to a section, such as an :class:`Article`.

       .. admonition:: Styling

          Rendered as an HTML <article> element.

       :param view: (See :class:`reahl.web.fw.Widget`)
       :keyword css_id: (See :class:`reahl.web.ui.HTMLElement`)

    """
    def __init__(self, view, css_id=None):
        super().__init__(view, 'header', children_allowed=True, css_id=css_id)


class Footer(HTMLElement):
    """The footer of a section (such as an :class:`Article`).

       .. admonition:: Styling

          Renders as an HTML <footer> element.

       :param view: (See :class:`reahl.web.fw.Widget`)
       :keyword css_id: (See :class:`reahl.web.ui.HTMLElement`)

    """
    def __init__(self, view, css_id=None):
        super().__init__(view, 'footer', children_allowed=True, css_id=css_id)


class Li(HTMLElement):
    """A list item.

       .. admonition:: Styling

          Renders as an HTML <li> element.

       :param view: (See :class:`reahl.web.fw.Widget`)
       :keyword css_id: (See :class:`reahl.web.ui.HTMLElement`)

    """
    def __init__(self, view, css_id=None):
        super().__init__(view, 'li', children_allowed=True, css_id=css_id)


class Ul(HTMLElement):
    """An unordered list.

       .. admonition:: Styling

          Renders as an HTML <ul> element.

       :param view: (See :class:`reahl.web.fw.Widget`)
       :keyword css_id: (See :class:`reahl.web.ui.HTMLElement`)

    """
    def __init__(self, view, css_id=None):
        super().__init__(view, 'ul', children_allowed=True, css_id=css_id)


class Ol(HTMLElement):
    """An ordered list.

       .. admonition:: Styling

          Renders as an HTML <ol> element.

       :param view: (See :class:`reahl.web.fw.Widget`)
       :keyword css_id: (See :class:`reahl.web.ui.HTMLElement`)

    """
    def __init__(self, view, css_id=None):
        super().__init__(view, 'ol', children_allowed=True, css_id=css_id)


class Img(HTMLElement):
    """An embedded image.

       .. admonition:: Styling

          Renders as an HTML <img> element.


       :param view: (See :class:`reahl.web.fw.Widget`)
       :keyword src: The URL from where the embedded image file should be fetched.
       :keyword alt: Alternative text describing the image.
       :keyword css_id: (See :class:`reahl.web.ui.HTMLElement`)

    """
    def __init__(self, view, src=None, alt=None, css_id=None):
        super().__init__(view, 'img', css_id=css_id)
        if src is not None:
            self.set_attribute('src', str(src))
        if alt:
            self.set_attribute('alt', alt)


class Span(HTMLElement):
    """A logical grouping of other HTMLElements which fits in with text flow.

       .. admonition:: Styling

          Renders as an HTML <span> element.

       :param view: (See :class:`reahl.web.fw.Widget`)
       :keyword text: Will be added as text content of the Span if given.
       :keyword css_id: (See :class:`reahl.web.ui.HTMLElement`)

    """

    def __init__(self, view, text=None, html_escape=True, css_id=None):
        super().__init__(view, 'span', children_allowed=True, css_id=css_id)
        if text:
            self.add_child(TextNode(view, text, html_escape=html_escape))


class ConcurrentChange(ValidationConstraint):
    def __init__(self, form):
        super().__init__(error_message=_('Some data changed since you opened this page, please reset input to try again.'))
        self.form = form
        self.failed = False

    @property
    def passed(self):
        return not self.failed

    def validate_input(self, unparsed_input):
        if unparsed_input != self.form.get_concurrency_hash_digest():
            self.failed = True
            if ExecutionContext.get_context().config.web.debug_concurrency_hash:
                self.error_message = Template('Failing concurrency check: submitted[%s] != calculated[%s]' % (unparsed_input, self.form.get_concurrency_hash_digest()))
            raise self


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

       .. versionchanged:: 4.0
          Added create_error_label.
    """
    is_Form = True

    def __init__(self, view, unique_name, rendered_form=None):
        self.view = view
        self.inputs = OrderedDict()
        self.set_up_event_channel(unique_name)
        self.set_up_field_validator('%s_validate' % unique_name)
        self.set_up_input_formatter('%s_format' % unique_name)
        self.rendered_form = rendered_form or self
        assert unique_name == self.event_channel.name
        super().__init__(view, 'form', children_allowed=True, css_id=unique_name)
        self.set_attribute('data-formatter', str(self.input_formatter.get_url()))

        class DelayedConcurrencyDigestValue(DelegatedAttributes):
            def __init__(self, digest_input):
                super().__init__()
                self.digest_input = digest_input

            def set_attributes(self, attributes):
                super().set_attributes(attributes)
                digest = self.digest_input.form.get_concurrency_hash_digest()
                attributes.set_to('value', digest)

        self.hash_inputs = self.add_child(Div(self.view, css_id='%s_hashes' % unique_name))
        self._reahl_csrf_token = ExecutionContext.get_context().session.get_csrf_token()
        self.hash_inputs.add_child(HiddenInput(self, self.fields._reahl_csrf_token, ignore_concurrent_change=True, ignore_persist_on_exception=True))
        self.database_digest_input = self.hash_inputs.add_child(HiddenInput(self, self.fields._reahl_database_concurrency_digest, ignore_concurrent_change=True))
        # the digest input will have a value when:
        #  (1) you're busy with an ajax call, after being internally redirected (because AjaxMethod.fire_ajax_event will have inputted the browser value); or
        #  (2) you're busy submitting and you saved its value because of an validation exception (and prepare_input read the value from saved inputs due to the exception)
        #
        # If (1), we want to maintain the value it originally had, so we want to use the POSTed value (a)
        # If (2), we want to update the value (b) to what it would have been if computed from the original database as if it displayed the 
        #  set of inputs that were being displayed at the time of the exception (these could be different from what was there at initial 
        #  rendering because of ajax that may have happened since then)
        #
        # If the digest does not have a value, its not ajax, so we update (as opposed to maintain the POSTed value)
        # If there is an exception we know that we're in case (2), so we update (as opposed to maintain the POSTed value)
        if self.exception or (not self.database_digest_input.value):
            # (b)
            self.database_digest_input.add_attribute_source(DelayedConcurrencyDigestValue(self.database_digest_input))
        else:
            # (a)
            pass # maintain the POSTed value

    @property
    def ancestral_coactive_widgets(self):
        return super().ancestral_coactive_widgets + [self.hash_inputs]

    @property
    def coactive_widgets(self):
        return super().coactive_widgets + [self.hash_inputs]

    fields = ExposedNames()
    fields._reahl_database_concurrency_digest = lambda i: Field().with_validation_constraint(ConcurrentChange(i))
    fields._reahl_csrf_token = lambda i: CSRFTokenField(i._reahl_csrf_token)

    events = ExposedNames()
    events.reset = lambda i: Event(label=_('Reset input'), action=Action(i.clear_view_data))

    def clear_view_data(self):
        self.clear_all_saved_data()
        
    def set_up_event_channel(self, event_channel_name):
        self.event_channel = EventChannel(self, self.controller, event_channel_name)
        self.view.add_resource(self.event_channel)

    def set_up_field_validator(self, field_validator_name):
        json_result = JsonResult(BooleanField(true_value='true', false_value='false'),
                                 catch_exception=ValidationConstraint)
        self.field_validator = RemoteMethod(self.view,
                                          field_validator_name,
                                          self.validate_single_input,
                                          json_result,
                                          immutable=True)
        self.view.add_resource(self.field_validator)

    def validate_single_input(self, **input_names_and_value):
        input_values = {k: [v] for k, v in input_names_and_value.items()}
        try:
            name = list(input_values.keys())[0]
            self.inputs[name].validate_input(input_values)
            return True
        except (KeyError, IndexError):
            return False
        except ValidationConstraint:
            raise

    def set_up_input_formatter(self, input_formatter_name):
        self.input_formatter = RemoteMethod(self.view,
                                            input_formatter_name,
                                            self.format_single_input,
                                            JsonResult(Field()),
                                            immutable=True)
        self.view.add_resource(self.input_formatter)

    def format_single_input(self, **input_names_and_value):
        input_values = {k: [v] for k, v in input_names_and_value.items()}
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
        attributes = super().attributes
        attributes.add_to('class', ['reahl-form'])
        attributes.set_to('action', self.action)
        attributes.set_to('method', 'POST')
        attributes.set_to('id', self.css_id)
        if self.contains_file_upload_input():
            attributes.set_to('enctype', 'multipart/form-data')
        return attributes

    @property
    def action(self):
        request = ExecutionContext.get_context().request
        action = self.event_channel.get_url()
        action.query = request.query_string
        action.make_network_relative()
        return str(action)

    def register_input(self, input_widget):
        assert input_widget not in self.inputs.values(), 'Cannot register the same input twice to this form' 
        assert input_widget.name not in self.inputs, 'Cannot add an input with same name as another'
        self.inputs[input_widget.name] = input_widget

    @property
    def channel_name(self):
        return self.event_channel.name

    @property
    def persisted_exception_class(self):
        config = ExecutionContext.get_context().config
        return config.web.persisted_exception_class
    @property
    def persisted_userinput_class(self):
        config = ExecutionContext.get_context().config
        return config.web.persisted_userinput_class
    @property
    def persisted_file_class(self):
        config = ExecutionContext.get_context().config
        return config.web.persisted_file_class

    def create_error_label(self, input_widget):
        """Creates a label containing the current validation error message for the given Input."""
        label = Label(self.view, text=input_widget.validation_error.message, for_input=input_widget)
        label.append_class('error')
        return label

    @property
    def exception(self):
        """The :class:`reahl.component.exceptions.DomainException` which occurred during submission of the Form, if any."""
        return self.persisted_exception_class.get_exception_for_form(self)

    def persist_exception(self, exception):
        self.clear_exception()
        self.persisted_exception_class.save_exception_for_form(self, exception=exception)

    def clear_exception(self):
        self.persisted_exception_class.clear_for_form_except_inputs(self)

    def persist_input(self, input_values):
        self.clear_saved_inputs()
        for input_widget in self.inputs.values():
            if input_widget.can_write():
                input_widget.persist_input(input_values)

    def persist_invalid_input(self):
        self.clear_saved_inputs()
        for some_input in self.inputs.values():
            field = some_input.bound_field
            if field.input_status == 'invalidly_entered':
                some_input.enter_value(field.as_user_input_value())

    def clear_saved_inputs(self):
        self.persisted_userinput_class.clear_for_form(self)
        self.persisted_exception_class.clear_for_all_inputs(self)

    def clear_uploaded_files(self):
        self.persisted_file_class.clear_for_form(self)

    def cleanup_after_exception(self, input_values, ex):
        self.persist_input(input_values)
        self.persist_exception(ex)

    def cleanup_after_success(self):
        self.clear_all_saved_data()

    def clear_all_saved_data(self):
        self.clear_saved_inputs()
        self.clear_exception()
        self.clear_uploaded_files()

    def handle_form_input(self, input_values):
        exceptions = []
        events = set()
        for input_widget in self.inputs.values():
            try:
                input_widget.accept_input(input_values)
            except ValidationConstraint as ex:
                exceptions.append(ex)
            events.add(input_widget.get_ocurred_event())
        if exceptions:
            raise ValidationException.for_failed_validations(exceptions)
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
        return super().get_js(context=context) + js

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

    """
    def __init__(self, view, unique_name):
        self.out_of_bound_form = self.create_out_of_bound_form(view, unique_name)
        super().__init__(view, css_id='%s_nested' % self.out_of_bound_form.css_id)
        self.add_to_attribute('class', ['reahl-nested-form'])
        self.set_id(self.css_id)
        view.add_out_of_bound_widget(self.out_of_bound_form)

    @property
    def coactive_widgets(self):
        return super().coactive_widgets + [self.view.page.get_out_of_bound_container()]

    @property
    def form(self):
        return self.out_of_bound_form

    def create_out_of_bound_form(self, view, unique_name):
        return Form(view, unique_name, rendered_form=self)


class FormLayout(Layout):
    """A simple Layout for adding inputs to Forms or elements inside Forms.

       .. versionadded:: 5.0
    """
    def add_input(self, html_input):
        """Adds an input to the Form.

           :param html_input: The Input to add.
        """
        input_container = self.widget.add_child(Div(self.view))

        if not html_input.includes_label:
            input_container.add_child(Label(self.view, for_input=html_input))
        input_container.add_child(html_input)

        if html_input.get_input_status() == 'invalidly_entered':
            input_container.add_child(P(self.view, text=html_input.validation_error.message))

        return html_input

    def add_alert_for_domain_exception(self, exception, form=None, unique_name=''):
        """Adds a formatted error message to the Form.

           :param exception: The Exception that should be displayed.
           :keyword form: The Form to which this exception relates (default is this Layout's .widget).
           :keyword unique_name: If more than one alert is added to the same Form, unique_name distinguishes between them.
        """
        form = form or self.widget
        alert = self.widget.add_child(Div(self.widget.view))
        alert.append_class('errors')
        alert.add_child(P(self.view, text=exception.as_user_message()))
        if exception.detail_messages:
            alert.add_child(Hr(self.widget.view))
            ul = alert.add_child(Ul(self.widget.view))
            for detail_message in exception.detail_messages:
                ul.add_child(Li(self.widget.view)).add_child(TextNode(self.widget.view, detail_message))
            reset_form = alert.add_child(NestedForm(self.widget.view, 'reset_%s%s' % (form.channel_name, unique_name)))
            reset_form.form.define_event_handler(form.events.reset)
            reset_form.add_child(ButtonInput(reset_form.form, form.events.reset))


class FieldSet(HTMLElement):
    """A visual grouping of HTMLElements inside a Form.

       .. admonition:: Styling

          Rendered as an HTML <fieldset> element.

       :param view: (See :class:`reahl.web.fw.Widget`)
       :keyword legend_text: If given, the FieldSet will have a Legend containing this text.
       :keyword css_id: (See :class:`reahl.web.ui.HTMLElement`)

       .. versionchanged:: 3.2
          Deprecated label_text and instead added legend_text: FieldSets should have Legends, not Labels.

       .. versionchanged:: 4.0
          Removed label_text that was deprecated.
    """
    def __init__(self, view, legend_text=None, css_id=None):
        super().__init__(view, 'fieldset', children_allowed=True, css_id=css_id)
        self.legend = None
        if legend_text:
            self.legend = self.add_child(Legend(view, text=legend_text))


class Legend(HTMLElement):
    """A caption for an :class:`reahl.web.ui.HTMLElement`.

    .. versionadded:: 3.2

    .. admonition:: Styling

       Rendered as an HTML <legend> element.

    :param view: (See :class:`reahl.web.fw.Widget`)
    :keyword text: If given, the Legend containing this text.
    :keyword css_id: (See :class:`reahl.web.ui.HTMLElement`)

    """
    def __init__(self, view, text=None, css_id=None):
        super().__init__(view, 'legend', children_allowed=True, css_id=css_id)
        if text:
            self.text_node = self.add_child(TextNode(view, text))


class DelegatedAttributes:
    def set_attributes(self, attributes):
        pass


class AccessRightAttributes(DelegatedAttributes):
    def __init__(self, widget, disabled_class='disabled'):
        super().__init__()
        self.widget = widget
        self.disabled_class = disabled_class

    @property
    def disabled(self):
        return self.widget.disabled

    def set_attributes(self, attributes):
        super().set_attributes(attributes)

        if self.disabled and self.disabled_class:
            attributes.add_to('class', [self.disabled_class])


class ValidationStateAttributes(DelegatedAttributes):
    def __init__(self, input_widget, error_class='error', success_class='valid'):
        super().__init__()
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
        super().set_attributes(attributes)

        if self.has_validation_error and self.error_class:
            attributes.add_to('class', [self.error_class])
        elif self.is_validly_entered and self.success_class:
            attributes.add_to('class', [self.success_class])


class HTMLWidget(Widget):
    def __init__(self, view, read_check=None, write_check=None):
        super().__init__(view, read_check=read_check, write_check=write_check)
        self.html_representation = None

    def enable_refresh(self, *for_fields):
        self.html_representation.query_fields.update_from_other(self.query_fields)
        self.html_representation.enable_refresh(*for_fields)

    @property
    def is_refresh_enabled(self):
        return self.html_representation.is_refresh_enabled

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
        return self.html_representation.add_to_attribute(name, values)

    def set_attribute(self, name, value):
        """Sets the value of the attribute `name` of the HTMLElement which represents this Widget in HTML to the user
           to the string `value`.
        """
        self.html_representation.set_attribute(name, value)

    def add_attribute_source(self, attribute_source):
        return self.html_representation.add_attribute_source(attribute_source)



class Input(HTMLWidget):
    """A Widget that proxies data between a user and the web application.

       :keyword form: The :class:`Form` with which this Input is associated.
       :keyword bound_field: The :class:`reahl.component.modelinterface.Field` which validates and marshalls user
                     input given via this Input.

       .. versionchanged:: 4.0
          Made .validation_error part of the public API of Input.
    """
    is_Input = True

    @arg_checks(form=IsInstance(Form), bound_field=IsInstance(Field))
    def __init__(self, form, bound_field):
        self.form = form
        self.bound_field = bound_field
        super().__init__(form.view, read_check=bound_field.can_read, write_check=bound_field.can_write)

    def can_write(self):
        return (not self.write_check) or self.write_check()

    @property
    def label(self):
        return self.bound_field.label

    @property
    def required(self):
        return self.bound_field.required

    @property
    def value(self):
        return self.bound_field.as_user_input_value(self.get_input_status())

    @property
    def original_database_value(self):
        return self.bound_field.get_initial_value_as_user_input()

    def get_input_status(self):
        return self.bound_field.input_status

    @property
    def validation_error(self):
        """The failing ValidationConstraint if the current value entered into this Input is invalid, else None."""
        return self.bound_field.validation_error

    @property
    def includes_label(self):
        """If True, the Label of this Input forms part of the input itself."""
        return False


class WrappedInput(Input):
    def __init__(self, input_widget):
        super().__init__(input_widget.form, input_widget.bound_field)
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
    """A simple HTML control.

       :param form: (See :class:`~reahl.web.ui.Input`)
       :param bound_field: (See :class:`~reahl.web.ui.Input`)
       :keyword registers_with_form: (for internal use)
       :keyword refresh_widget: An :class:`HTMLElement` that will be refreshed when the value of this input changes.
       :keyword ignore_concurrent_change: If True, don't check for possible concurrent changes by others to this input (just override such changes).

       .. versionchanged:: 5.0
          Added `refresh_widget`

       .. versionchanged:: 5.0
          Added `ignore_concurrent_change`

       .. versionchanged:: 5.0
          Removed `name` kwarg.
    """
    is_for_file = False
    is_contained = False

    @arg_checks(form=IsInstance(Form), bound_field=IsInstance(Field))
    def __init__(self, form, bound_field, registers_with_form=True, refresh_widget=None, ignore_concurrent_change=False):
        super().__init__(form, bound_field.in_namespace(form.channel_name) if registers_with_form else bound_field)

        self.ignore_concurrent_change = ignore_concurrent_change

        self.registers_with_form = registers_with_form
        if self.registers_with_form:
            form.register_input(self) # bound_field must be set for this registration to work
            self.prepare_input()

        self.set_html_representation(self.add_child(self.create_html_widget()))
        if self.html_control:
            self.html_control.set_id(self.make_html_control_css_id())
        else:
            self.set_id(self.make_html_control_css_id())

        if not self.is_contained:
            self.add_to_attribute('class', ['reahl-primitiveinput'])
            self.add_input_data_attributes()

        self.refresh_widgets=[]
        if refresh_widget:
            self.set_refresh_widgets([refresh_widget])
            
    @deprecated('Use set_refresh_widgets instead', '6.1')
    def set_refresh_widget(self, refresh_widget):
        """
        Instructs this :class:`PrimitiveInput` to refresh the given widget when its value changes.

        The `refresh_widget` has to have a css_id, and also needs to have refreshing enabled.

        :param refresh_widget: An :class:`HTMLWidget` or :class:`HTMLElement`.

        .. versionadded:: 5.2
        """
        self.set_refresh_widgets([refresh_widget])

    def set_refresh_widgets(self, refresh_widgets):
        """
        Instructs this :class:`PrimitiveInput` to refresh all the given widgets when its value changes.

        All the `refresh_widgets` have to have a css_id, and also needs to have refreshing enabled.

        :param refresh_widgets: A list of :class:`HTMLWidget` or :class:`HTMLElement`.

        .. versionadded:: 6.1
        """
        for widget in refresh_widgets:
            if not widget.is_refresh_enabled:
                raise ProgrammerError(
                    '%s is not set to refresh. You can only refresh widgets on which enable_refresh() was called.' % refresh_widget)
        if self.refresh_widgets:
            raise ProgrammerError('The refresh widgets on %s have already been set' % self)
        self.refresh_widgets = refresh_widgets
        self.set_attribute('data-refresh-widget-ids', ','.join(['#%s'%w.css_id for w in self.refresh_widgets]))
        if self.html_control:
            css_id = self.html_control.css_id
        else:
            css_id = self.css_id
        self.ajax_refresh_method = AjaxMethod(refresh_widgets, 'refresh_widgets_%s' % css_id)
        self.view.add_resource(self.ajax_refresh_method)

    def make_html_control_css_id(self):
        return str(CssId.from_dirty_string('id-%s' % (self.name)))

    def add_input_data_attributes(self):
        if isinstance(self.bound_field, BooleanField):
            self.set_attribute('data-is-boolean', '')
            self.set_attribute('data-true-boolean-value', self.bound_field.true_value)
            self.set_attribute('data-false-boolean-value', self.bound_field.false_value)
        
    def __str__(self):
        return '<%s name=%s>' % (self.__class__.__name__, self.name)

    @property
    def name(self):
        return self.bound_field.name_in_input

    def get_concurrency_hash_strings(self):
        if not self.ignore_concurrent_change:
            if ExecutionContext.get_context().config.web.debug_concurrency_hash:
                yield '%s[%s]' % (self.name, self.original_database_value)
            else:
                yield self.original_database_value

    @property
    def html_control(self):
        return self.html_representation

    def create_html_widget(self):
        """Override this in subclasses to create the HTMLElement that represents this Input in HTML to the user.

           .. versionadded:: 3.2
        """
        self.not_implemented()

    @property
    def channel_name(self):
        return self.form.channel_name

    @property
    def jquery_selector(self):
        return '''$('input[name="%s"][form="%s"]')''' % (self.name, self.form.css_id)

    def get_js(self, context=None):
        if self.refresh_widgets:
            jquery_options = json.dumps(self.ajax_refresh_method.as_jquery_parameter())
        else:
            jquery_options = ''
        js = ['$(%s).primitiveinput(%s);' %
              (self.html_representation.contextualise_selector('".reahl-primitiveinput"', context),
                jquery_options
               )]
        return super().get_js(context=context) + js

    @property
    def validation_constraints(self):
        return self.bound_field.validation_constraints

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

    def accept_disambiguated_input(self, disambiguated_input):
        super().accept_disambiguated_input(disambiguated_input)
        if self.registers_with_form:
            self.bound_field.from_disambiguated_input(disambiguated_input, ignore_validation=True)

    def update_construction_state(self, disambiguated_input):
        super().update_construction_state(disambiguated_input)
        if self.registers_with_form:
            self.bound_field.update_valid_value_in_disambiguated_input(disambiguated_input)

    def get_ocurred_event(self):
        return None

    def get_value_from_input(self, input_values):
        """Obtains the value received for this Input from the browser, given a :class:`cgi.FieldStorage`
           containing name, value pairs of user input as sent by the browser.
           Override this method if your Input needs special handling to obtain its value.

           .. versionchanged:: 4.2
              Raises ExpectedInputNotFound instead of ProgrammerError
        """
        try:
            return input_values[self.name][0]
        except KeyError:
            if self.disabled:
                return ''
            raise ExpectedInputNotFound(self.name, input_values)

    @property
    def persisted_userinput_class(self):
        return self.form.persisted_userinput_class

    def prepare_input(self):
        field_data_store = ExecutionContext.get_context().global_field_values = getattr(ExecutionContext.get_context(), 'global_field_values', {})
        self.bound_field.activate_global_field_data_store(field_data_store)

        construction_state = self.view.get_construction_state()
        if construction_state:
            self.bound_field.from_disambiguated_input(construction_state, ignore_validation=True, ignore_access=True)

        previously_entered_value = self.persisted_userinput_class.get_previously_entered_for_form(self.form, self.name, self.bound_field.entered_input_type)

        if previously_entered_value is not None:
            self.bound_field.set_user_input(previously_entered_value, ignore_validation=True)
        else:
            self.bound_field.clear_user_input()

    def persist_input(self, input_values):
        input_value = self.get_value_from_input(input_values)
        self.enter_value(input_value)

    def clear_entered_value(self):
        if self.registers_with_form:
            self.persisted_userinput_class.clear_saved_input_value_for_form(self.form, self.name)

    def enter_value(self, input_value):
        if self.registers_with_form:
            self.persisted_userinput_class.save_input_value_for_form(self.form, self.name, input_value, self.bound_field.entered_input_type)


class HTMLInputElement(HTMLElement):
    def __init__(self, input_widget, input_type, render_value_attribute=True):
        self.input_type = input_type
        self.render_value_attribute = render_value_attribute
        super().__init__(input_widget.view, 'input')
        self.set_attributes(input_widget)

    def set_attributes(self, input_widget):
        if input_widget.name:
            self.set_attribute('name', input_widget.name)
        if input_widget.disabled:
            self.set_attribute('disabled', 'disabled')
        self.set_attribute('type', self.input_type)
        self.set_attribute('form', input_widget.form.css_id)
        if self.render_value_attribute:
            self.set_attribute('value', input_widget.value)
        self.add_validation_constraints_from(input_widget)
        return input_widget

    def validation_constraints_to_render(self, input_widget):
        return ValidationConstraintList([constraint for constraint in input_widget.validation_constraints if constraint.name])

    def add_validation_constraints_from(self, input_widget):
        html5_validations = ['pattern', 'required', 'maxlength', 'minlength', 'accept', 'minvalue', 'maxvalue']

        def jquery_rule_attribute_name_for(validation_constraint):
            if validation_constraint.is_remote or validation_constraint.name in html5_validations:
                return validation_constraint.name
            return 'data-rule-%s' % validation_constraint.name

        def jquery_validate_parameters_for(validation_constraint):
            if validation_constraint.is_remote:
                return str(input_widget.form.field_validator.get_url())
            elif validation_constraint.name in html5_validations:
                return validation_constraint.parameters
            return validation_constraint.parameters or 'true'

        for validation_constraint in self.validation_constraints_to_render(input_widget):
            self.set_attribute(jquery_rule_attribute_name_for(validation_constraint),
                                      jquery_validate_parameters_for(validation_constraint))
            if not validation_constraint.is_remote:
                validation_message_name = 'data-msg-%s' % validation_constraint.name
                self.set_attribute(validation_message_name, validation_constraint.message)
            if validation_constraint.name == 'pattern':
                self.set_attribute('title', html.escape(validation_constraint.message))


class TextArea(PrimitiveInput):
    """A muli-line Input for plain text.

       .. admonition:: Styling

          Represented in HTML as a <textarea> element.

       :param form: (See :class:`~reahl.web.ui.Input`)
       :param bound_field: (See :class:`~reahl.web.ui.Input`)
       :keyword rows: The number of rows that this Input should have.
       :keyword columns: The number of columns that this Input should have.
       :keyword refresh_widget: (See :class:`~reahl.web.ui.PrimitiveInput`)
       :keyword ignore_concurrent_change: (See :class:`~reahl.web.ui.PrimitiveInput`)

       .. versionchanged:: 5.0
          Added `ignore_concurrent_change`
    """
    def __init__(self, form, bound_field, rows=None, columns=None, refresh_widget=None, ignore_concurrent_change=False):
        self.rows = rows
        self.columns = columns
        super().__init__(form, bound_field, refresh_widget=refresh_widget, ignore_concurrent_change=ignore_concurrent_change)

    def create_html_widget(self):
        html_text_area = HTMLElement(self.view, 'textarea', children_allowed=True)
        html_text_area.set_attribute('name', self.name)
        if self.disabled:
            html_text_area.set_attribute('disabled', 'disabled')


        self.text = html_text_area.add_child(TextNode(self.view, self.get_value))

        if self.rows:
            html_text_area.set_attribute('rows', str(self.rows))
        if self.columns:
            html_text_area.set_attribute('cols', str(self.columns))

        return html_text_area

    def get_value(self):
        return self.value


class ContainedInput(PrimitiveInput):
    is_contained = True
    def __init__(self, containing_input, choice, refresh_widget=None):
        self.choice = choice
        self.containing_input = containing_input
        super().__init__(containing_input.form, choice.field, registers_with_form=False, refresh_widget=refresh_widget)

    def make_html_control_css_id(self):
        return str(CssId.from_dirty_string('id-%s-%s' % (self.containing_input.name, self.value)))

    def get_input_status(self):
        return 'defaulted'

    @property
    def validation_constraints(self):
        return self.containing_input.validation_constraints

    @property
    def validation_error(self):
        return self.containing_input.validation_error

    def validate_input(self, input_values):
        return self.containing_input.validate_input(input_values)

    def format_input(self, input_values):
        return self.containing_input.format_input(input_values)

    def accept_input(self, input_values):
        return self.containing_input.format_input(input_values)

    def get_ocurred_event(self):
        return self.containing_input.get_ocurred_event()

    def get_value_from_input(self, input_values):
        return self.containing_input.get_value_from_input(input_values)

    def prepare_input(self):
        return self.containing_input.prepare_input()

    def persist_input(self, input_values):
        return self.containing_input.persist_input(input_values)

    def enter_value(self, input_value):
        return self.containing_input.enter_value(input_value)


class Option(ContainedInput):
    def __init__(self, containing_input, choice):
        self.choice = choice
        self.containing_input = containing_input
        super().__init__(containing_input, choice)

    @property
    def selected(self):
        if self.containing_input.bound_field.allows_multiple_selections:
            return self.value in self.containing_input.value
        else:
            return self.value == self.containing_input.value

    def create_html_widget(self):
        option = HTMLElement(self.view, 'option', children_allowed=True)
        option.add_child(TextNode(self.view, self.label))
        option.set_attribute('value', self.value)
        if self.selected:
            option.set_attribute('selected', 'selected')
        if self.disabled:
            option.set_attribute('disabled', 'disabled')
        return option


class OptGroup(HTMLElement):
    def __init__(self, view, label, options, css_id=None):
        super().__init__(view, 'optgroup', children_allowed=True, css_id=css_id)
        self.set_attribute('label', label)
        for option in options:
            self.add_child(option)


class SelectInput(PrimitiveInput):
    """An Input that lets the user select an :class:`reahl.component.modelinterface.Choice` from a dropdown
       list of valid ones if used with a ChoiceField, or many choices if used with a MultiChoiceField.

       .. admonition:: Styling

          Represented in HTML as a <select> element which can contain <option> and <optgroup> children.

       :param form: (See :class:`~reahl.web.ui.Input`)
       :keyword refresh_widget: (See :class:`~reahl.web.ui.PrimitiveInput`)
       :keyword size: Number of rows in the list that should be visible at one time, if the associated field allows multiple selections.

       .. versionchanged: 6.1
          Added keyword parameter size

    """
    def __init__(self, form, bound_field, size=None, refresh_widget=None, ignore_concurrent_change=False):
        self.size = size
        super().__init__(form, bound_field, refresh_widget=refresh_widget, ignore_concurrent_change=ignore_concurrent_change)

    def create_html_widget(self):
        html_select = HTMLElement(self.view, 'select', children_allowed=True)
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
            if self.size:
                html_select.set_attribute('size', '%s' % self.size)

        return html_select

    def is_selected(self, choice):
        if self.bound_field.allows_multiple_selections:
            return choice.as_input() in self.value
        else:
            return self.value == choice.as_input()

    def get_value_from_input(self, input_values):
        if self.bound_field.allows_multiple_selections:
            return input_values.get(self.name, [])
        else:
            return super().get_value_from_input(input_values)


class SingleChoice(ContainedInput):
    def __init__(self, containing_input, choice):
        self.choice = choice
        self.containing_input = containing_input
        super().__init__(containing_input, choice)

    @property
    def name(self):
        return self.containing_input.name

    @property
    def choice_type(self):
        return self.containing_input.choice_type

    @property
    def html_control(self):
        return self.html_representation.children[0]

    def create_html_widget(self):
        label = Label(self.view)
        label.add_child(self.create_button_input())
        label.add_child(TextNode(self.view, self.label))
        return label

    def create_button_input(self):
        button = HTMLInputElement(self, self.containing_input.choice_type)
        if self.checked:
            button.set_attribute('checked', 'checked')
        return button

    @property
    def checked(self):
        return self.containing_input.is_choice_selected(self.value)


class RadioButtonSelectInput(PrimitiveInput):
    """An Input that lets the user select an :class:`reahl.component.modelinterface.Choice` from a list of valid ones
       shown as radio buttons.

       .. admonition:: Styling

          Represented in HTML as a <div class="reahl-radio-button-input"> element which
          contains an <input type="radio">, wrapped in a <span class="reahl-radio-button"> for each valid
          :class:`reahl.component.modelinterface.Choice`.

       :param form: (See :class:`~reahl.web.ui.Input`)
       :param bound_field: (See :class:`~reahl.web.ui.Input`)
       :keyword refresh_widget: (See :class:`~reahl.web.ui.PrimitiveInput`)
       :keyword ignore_concurrent_change: (See :class:`~reahl.web.ui.PrimitiveInput`)

       .. versionchanged:: 4.0
          Renamed from RadioButtonInput

       .. versionchanged:: 5.0
          Added `refresh_widget`

       .. versionchanged:: 5.0
          Added `ignore_concurrent_change`

    """

    choice_type = 'radio'

    @arg_checks(bound_field=IsInstance(ChoiceField))
    def __init__(self, form, bound_field, refresh_widget=None, ignore_concurrent_change=False):
        super().__init__(form, bound_field, refresh_widget=refresh_widget, ignore_concurrent_change=ignore_concurrent_change)

    def is_choice_selected(self, value):
        if self.bound_field.allows_multiple_selections:
            return value in self.value
        return self.value == value

    def create_html_widget(self):
        main_element = self.create_main_element()
        main_element.append_class('reahl-radio-button-input')
        for choice in self.bound_field.flattened_choices:
            self.add_choice_to(main_element, choice)
        return main_element

    @property
    def html_control(self):
        return None

    def get_value_from_input(self, input_values):
        return input_values.get(self.name, [''])[0]

    def create_main_element(self):
        return Div(self.view)

    def add_choice_to(self, widget, choice):
        return widget.add_child(SingleChoice(self, choice))


# Uses: reahl/web/reahl.textinput.js
class TextInput(PrimitiveInput):
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
       :keyword placeholder: If given, a placeholder is displayed in the TextInput if the TextInput
                     is empty in order to provide a hint to the user of what may be entered into the TextInput.
                     If given a string, that string is used.
                     If given True instead of a string, use:
                     - default of the field when the field is not required
                     - else, the label.
       :keyword refresh_widget: (See :class:`~reahl.web.ui.PrimitiveInput`)
       :keyword ignore_concurrent_change: (See :class:`~reahl.web.ui.PrimitiveInput`)

       .. versionchanged:: 3.2
          Added `placeholder`.

       .. versionchanged:: 5.0
          Added `refresh_widget`

       .. versionchanged:: 5.0
          Added `ignore_concurrent_change`

       .. versionchanged:: 6.1
          Changed `placeholder to display the default of the field under certain conditions`

    """
    def __init__(self, form, bound_field, fuzzy=False, placeholder=False, refresh_widget=None, ignore_concurrent_change=False):
        super().__init__(form, bound_field, refresh_widget=refresh_widget, ignore_concurrent_change=ignore_concurrent_change)
        self.append_class('reahl-textinput')
        if placeholder:
            placeholder_text = placeholder
            if placeholder is True:
                if not self.value and not self.bound_field.required and self.bound_field.default:
                    placeholder_text = self.bound_field.default
                else:
                    placeholder_text = self.label
            self.set_attribute('placeholder', placeholder_text)
            self.set_attribute('aria-label', placeholder_text)

        if fuzzy:
            self.append_class('fuzzy')

    def get_js(self, context=None):
        js = ['$(%s).textinput();' % self.html_representation.contextualise_selector('".reahl-textinput"', context)]
        return super().get_js(context=context) + js

    def create_html_widget(self):
        return HTMLInputElement(self, 'text')


class PasswordInput(PrimitiveInput):
    """A PasswordInput is a single line text input, but it does not show what the user is typing.

       .. admonition:: Styling

          Represented in HTML by a <input type="password"> element.

       :param form: (See :class:`~reahl.web.ui.Input`)
       :param bound_field: (See :class:`~reahl.web.ui.Input`)
       :keyword placeholder: If given a string, placeholder is displayed in the TextInput if the TextInput
                     is empty in order to provide a hint to the user of what may be entered into the TextInput.
                     If given True instead of a string, the label of the TextInput is used.
       :keyword refresh_widget: (See :class:`~reahl.web.ui.PrimitiveInput`)
       :keyword ignore_concurrent_change: (See :class:`~reahl.web.ui.PrimitiveInput`)

       .. versionchanged:: 5.0
          Added `refresh_widget`

       .. versionchanged:: 5.0
          Added `ignore_concurrent_change`

       .. versionchanged:: 6.1
          Added `placeholder`
    """
    def __init__(self, form, bound_field, placeholder=None, refresh_widget=None, ignore_concurrent_change=False):
        super().__init__(form, bound_field, refresh_widget=refresh_widget, ignore_concurrent_change=ignore_concurrent_change)
        if placeholder:
            placeholder_text = self.label if placeholder is True else placeholder
            self.set_attribute('placeholder', placeholder_text)
            self.set_attribute('aria-label', placeholder_text)

    def create_html_widget(self):
        return HTMLInputElement(self, 'password', render_value_attribute=False)


class HiddenInput(PrimitiveInput):
    def __init__(self, form, bound_field, ignore_concurrent_change=False, ignore_persist_on_exception=False):
        self.ignore_persist_on_exception = ignore_persist_on_exception
        super().__init__(form, bound_field, ignore_concurrent_change=ignore_concurrent_change)

    def create_html_widget(self):
        return HTMLInputElement(self, 'hidden')

    def persist_input(self, input_values):
        if not self.ignore_persist_on_exception:
            super().persist_input(input_values)

    def update_construction_state(self, disambiguated_input):
        if not self.ignore_persist_on_exception:
            super().update_construction_state(disambiguated_input)


class CheckboxInput(PrimitiveInput):
    """A single checkbox that represent a true or false value.

       .. admonition:: Styling

          Represented in HTML by an <input type="checkbox"> element.

       :param form: (See :class:`~reahl.web.ui.Input`)
       :param bound_field: (See :class:`~reahl.web.ui.Input`)
       :keyword name: An optional name for this input (overrides the default)
       :keyword refresh_widget: (See :class:`~reahl.web.ui.PrimitiveInput`)
       :keyword ignore_concurrent_change: (See :class:`~reahl.web.ui.PrimitiveInput`)

       .. versionchanged:: 5.0
          Added `name` and `refresh_widget`

       .. versionchanged:: 5.0
          Added `ignore_concurrent_change`
    """
    choice_type = 'checkbox'

    @arg_checks(bound_field=IsInstance(BooleanField))
    def __init__(self, form, bound_field, refresh_widget=None, ignore_concurrent_change=False):
        super().__init__(form, bound_field, refresh_widget=refresh_widget, ignore_concurrent_change=ignore_concurrent_change)

    @property
    def checked(self):
        return self.value == self.bound_field.true_value

    def create_html_widget(self):
        checkbox_widget = HTMLInputElement(self, self.choice_type, render_value_attribute=False)
        if self.checked:
            checkbox_widget.set_attribute('checked', 'checked')
        return checkbox_widget

    @property
    def validation_constraints(self):
        applicable_constraints = ValidationConstraintList()
        if self.required:
            validation_constraints = super().validation_constraints
            validation_constraint = validation_constraints.get_constraint_named('required')
            applicable_constraints.append(validation_constraint)
        return applicable_constraints

    def get_value_from_input(self, input_values):
        if self.name in input_values:
            return self.bound_field.true_value
        return self.bound_field.false_value


class CheckboxSelectInput(PrimitiveInput):
    """An Input that lets the user select more than one :class:`reahl.component.modelinterface.Choice` from a
       list of valid ones shown as checkboxes.

       :param form: (See :class:`~reahl.web.ui.Input`)
       :param bound_field: (See :class:`~reahl.web.ui.Input`)
       :keyword refresh_widget: (See :class:`~reahl.web.ui.PrimitiveInput`)
       :keyword ignore_concurrent_change: (See :class:`~reahl.web.ui.PrimitiveInput`)

       .. versionadded:: 4.0

       .. versionchanged:: 5.0
          Added `refresh_widget`

       .. versionchanged:: 5.0
          Added `ignore_concurrent_change`
    """
    choice_type = 'checkbox'
    allowed_field_types = [MultiChoiceField]

    def __init__(self, form, bound_field, refresh_widget=None, ignore_concurrent_change=False):
        if not isinstance(bound_field, *self.allowed_field_types):
            raise ProgrammerError('%s is not allowed to be used with %s' % (bound_field.__class__, self.__class__))
        self.added_choices = []
        super().__init__(form, bound_field, refresh_widget=refresh_widget, ignore_concurrent_change=ignore_concurrent_change)

    @property
    def html_control(self):
        # Note: seems like the html_control is only used ever to target this thing via css_id
        #       when you do <label for=> and for use in jquery selectors that target this input.
        #       Feels wrong in this case to use added_choices[0], should rather be the enclosing
        #       Div, which is not an html control. Naming issue? Also a single test breaks if
        #       we do change this: reahl/web_dev/bootstrap/test_popup.py
        return self.added_choices[0] if not self.bound_field.allows_multiple_selections else None

    @property
    def includes_label(self):
        return False

    @property
    def jquery_selector(self):
        return '%s.closest("div")' % self.html_control.jquery_selector

    def create_html_widget(self):
        main_element = self.create_main_element()
        for choice in self.bound_field.flattened_choices:
            self.added_choices.append(self.add_choice_to(main_element, choice))
        return main_element

    def is_choice_selected(self, value):
        if self.value is None:
            return False
        return value in self.value

    def get_value_from_input(self, input_values):
        if self.bound_field.allows_multiple_selections:
            return input_values.get(self.name, [])
        else:
            return input_values.get(self.name, [''])[0]

    def create_main_element(self):
        main_element = Div(self.view)
        main_element.append_class('reahl-checkbox-input')
        return main_element

    def add_choice_to(self, widget, choice):
        return widget.add_child(SingleChoice(self, choice))


class ButtonInput(PrimitiveInput):
    """A button on a Form.

       .. admonition:: Styling

          Rendered as an HTML <input type="submit"> element.

       :param form: (See :class:`reahl.web.ui.PrimitiveInput`)
       :param event: The :class:`reahl.component.modelinterface.Event` that will be triggered server-side when the user clicks on the button.
       :keyword ignore_concurrent_change: (See :class:`~reahl.web.ui.PrimitiveInput`)

       .. versionchanged:: 5.0
          Added `ignore_concurrent_change`

    """
    def __init__(self, form, event, ignore_concurrent_change=False):
        super().__init__(form, event, ignore_concurrent_change=ignore_concurrent_change)
        if not self.controller.has_event_named(event.name):
            raise ProgrammerError('no Event/Transition available for name %s' % event.name)
        try:
            event.validate_default()
        except ValidationConstraint as ex:
            message = 'Arguments for %s are not valid: %s' % (event, ex)
            message += '\n(did you forget to call .with_arguments() on an Event sent to a ButtonInput?)'
            raise ProgrammerError(message)

    @property
    def name(self):
        return 'event.%s%s' % (super().name, self.query_encoded_arguments)

    @property
    def validation_constraints(self):
        return ValidationConstraintList([])

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

    @property
    def label(self):
        return self.bound_field.label

    @property
    def value(self):
        return self.label

    def get_ocurred_event(self):
        if self.bound_field.occurred:
            return self.bound_field.out_of_namespace()
        return None

    def create_html_widget(self):
        return HTMLInputElement(self, 'submit')

    def prepare_input(self):
        pass  # We don't save what is submitted via buttons and don't have to fill in saved details
    

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
        super().__init__(view, 'label', children_allowed=True, css_id=css_id)
        self.for_input = for_input
        if text or for_input:
            self.text_node = self.add_child(TextNode(view, text or for_input.label))

    @property
    def visible(self):
        if self.for_input:
            return self.for_input.visible
        else:
            return super().visible

    @property
    def attributes(self):
        attributes = super().attributes
        if self.for_input and self.for_input.html_control:
            attributes.set_to('for', self.for_input.html_control.css_id)
        return attributes


class ActiveStateAttributes(DelegatedAttributes):
    def __init__(self, widget, attribute_name='class', active_value='active', inactive_value=None):
        super().__init__()
        self.widget = widget
        self.attribute_name = attribute_name
        self.active_value = active_value
        self.inactive_value = inactive_value

    def set_attributes(self, attributes):
        super().set_attributes(attributes)

        if self.widget.is_active and self.active_value:
            attributes.add_to(self.attribute_name, [self.active_value])
        elif not self.widget.is_active and self.inactive_value:
            attributes.add_to(self.attribute_name, [self.inactive_value])


class SimpleFileInput(PrimitiveInput):
    """An Input for selecting a single file which will be uploaded once the user clicks on any :class:`Button`
       associated with the same :class:`Form` as this Input.

       .. admonition:: Styling

          Represented in HTML by an <input type="file"> element. Can have attribute multiple set,
          if allowed by the `bound_field`.

       :param form: (See :class:`~reahl.web.ui.Input`)
       :param bound_field: (See :class:`~reahl.web.ui.Input`, must be of type :class:`reahl.component.modelinterface.FileField`
       :keyword name: (See :class:`~reahl.web.ui.PrimitiveInput`)
       :keyword refresh_widget: (See :class:`~reahl.web.ui.PrimitiveInput`)

       .. versionchanged:: 5.0
          Added `name` and `refresh_widget`
    """
    is_for_file = True

    def __init__(self, form, bound_field, refresh_widget=None):
        super().__init__(form, bound_field, refresh_widget=refresh_widget)

    def create_html_widget(self):
        file_input = HTMLInputElement(self, 'file')
        if self.allow_multiple:
            file_input.set_attribute('multiple', 'multiple')
        return file_input

    def get_value_from_input(self, input_values):
        field_storages = input_values.get(self.name, [])

        return [UploadedFile(str(field_storage.filename), field_storage.file.read(), str(field_storage.type))
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
            self.persisted_exception_class.save_exception_for_form(self.form, input_name=self.name, exception=self.bound_field.validation_error)


class UniqueFilesConstraint(ValidationConstraint):
    name = 'uniquefiles'
    def __init__(self, form=None, input_name=None, error_message=None):
        error_message = error_message or _('uploaded files should all have different names')
        super().__init__(error_message=error_message)
        self.form = form
        self.input_name = input_name

    def validate_input(self, unparsed_input):
        assert (self.form is not None) and (self.field is not None)
        config = ExecutionContext.get_context().config
        persisted_file_class = config.web.persisted_file_class
        for f in unparsed_input:
            if persisted_file_class.is_uploaded_for_form(self.form, self.input_name, f.filename):
                raise self

    def __reduce__(self):
        reduced = super().__reduce__()
        pickle_dict = reduced[2]
        del pickle_dict['form']
        return reduced


class Caption(HTMLElement):
    """An HTML caption element.

       .. admonition:: Styling

          Renders as an HTML <caption> element.

       :param view: (See :class:`reahl.web.fw.Widget`)
       :keyword text: Text to be displayed inside the caption element.
       :keyword css_id: (See :class:`reahl.web.ui.HTMLElement`)

    """
    def __init__(self, view, text=None, css_id=None):
        super().__init__(view, 'caption', children_allowed=True, css_id=css_id)
        if text is not None:
            self.add_child(TextNode(view, text))


class Col(HTMLElement):
    """An HTML col element, defines a column in a table.

       :param view: (See :class:`reahl.web.fw.Widget`)
       :keyword span: The number of columns spanned by this column.
       :keyword css_id: (See :class:`reahl.web.ui.HTMLElement`)

    """
    def __init__(self, view, span=None, css_id=None):
        super().__init__(view, 'col', children_allowed=False, css_id=css_id)
        if span:
            self.set_attribute('span', span)


class ColGroup(HTMLElement):
    """An HTML colgroup element, defines a group of columns in a table.

       :param view: (See :class:`reahl.web.fw.Widget`)
       :keyword span: The number of columns spanned by this group.
       :keyword css_id: (See :class:`reahl.web.ui.HTMLElement`)

    """
    def __init__(self, view, span=None, css_id=None):
        super().__init__(view, 'colgroup', children_allowed=True, css_id=css_id)
        if span:
            self.set_attribute('span', span)

Colgroup = ColGroup

class Thead(HTMLElement):
    """An HTML thead element. Contains the header of the table columns.

       :param view: (See :class:`reahl.web.fw.Widget`)
       :keyword css_id: (See :class:`reahl.web.ui.HTMLElement`)

    """
    def __init__(self, view, css_id=None):
        super().__init__(view, 'thead', children_allowed=True, css_id=css_id)


class Tfoot(HTMLElement):
    """An HTML tfoot element. Contains the footer of the table columns.

       :param view: (See :class:`reahl.web.fw.Widget`)
       :keyword css_id: (See :class:`reahl.web.ui.HTMLElement`)

    """
    def __init__(self, view, css_id=None):
        super().__init__(view, 'tfoot', children_allowed=True, css_id=css_id)


class Tbody(HTMLElement):
    """An HTML tbody element. Contains the rows with data in the table.

       :param view: (See :class:`reahl.web.fw.Widget`)
       :keyword css_id: (See :class:`reahl.web.ui.HTMLElement`)

    """
    def __init__(self, view, css_id=None):
        super().__init__(view, 'tbody', children_allowed=True, css_id=css_id)


class Tr(HTMLElement):
    """An HTML tr element represents one row of data in a table.

       :param view: (See :class:`reahl.web.fw.Widget`)
       :keyword css_id: (See :class:`reahl.web.ui.HTMLElement`)

    """
    def __init__(self, view, css_id=None):
        super().__init__(view, 'tr',children_allowed=True, css_id=css_id)


class Cell(HTMLElement):
    def __init__(self, view, html_tag_name, rowspan=None, colspan=None, css_id=None):
        super().__init__(view, html_tag_name, children_allowed=True, css_id=css_id)
        if rowspan:
            self.set_attribute('rowspan', str(rowspan))
        if colspan:
            self.set_attribute('colspan', str(colspan))


class Th(Cell):
    """An HTML th element - a single cell heading for a column of a table.

       :param view: (See :class:`reahl.web.fw.Widget`)
       :keyword rowspan: The number of rows this table cell should span.
       :keyword colspan: The number of columns this table cell should span.
       :keyword css_id: (See :class:`reahl.web.ui.HTMLElement`)

    """
    def __init__(self, view,  rowspan=None, colspan=None, css_id=None):
        super().__init__(view, 'th', rowspan=rowspan, colspan=colspan, css_id=css_id)


class Td(Cell):
    """An HTML td element - a single cell of data inside a row of a table.

       :param view: (See :class:`reahl.web.fw.Widget`)
       :keyword rowspan: The number of rows this table cell should span.
       :keyword colspan: The number of columns this table cell should span.
       :keyword css_id: (See :class:`reahl.web.ui.HTMLElement`)

    """
    def __init__(self, view, rowspan=None, colspan=None, css_id=None):
        super().__init__(view, 'td', rowspan=rowspan, colspan=colspan, css_id=css_id)


class DynamicColumn:
    """DynamicColumn defines a logical column of a table, specifying how its heading will be
       rendered, and how the cell in this column will be displayed for each data item in the
       table.

       :param make_heading_or_string: A string to be used as heading for this column, or \
              a single-argument callable that will be called (passing the current view) in \
              order to compute a Widget to be displayed as heading of the column.
       :param make_widget: A callable that takes two arguments: the current view, and an item \
              of data of the current table row. It will be called to compute a Widget \
              to be displayed in the current column for the given data item.
       :keyword make_footer_widget: A callable that takes two arguments: the current view, and \
              an item representing a row of footer data. It will be called to compute \
              a Widget to be displayed in the footer column representing the footer item. \
       :keyword sort_key: If specified, this value will be passed to sort() for sortable tables.

       .. versionchanged:: 5.0
            Added `make_footer_widget`.
    """
    def __init__(self, make_heading_or_string, make_widget, make_footer_widget=None, sort_key=None):
        if isinstance(make_heading_or_string, str):
            def make_span(view):
                return Span(view, text=make_heading_or_string)
            self.make_heading_widget = make_span
        else:
            self.make_heading_widget = make_heading_or_string

        self.make_widget = make_widget
        self.make_footer_widget = make_footer_widget
        self.sort_key = sort_key

    def heading_as_widget(self, view):
        return self.make_heading_widget(view)

    def as_widget(self, view, item):
        return self.make_widget(view, item)

    @property
    def has_footer(self):
        return self.make_footer_widget is not None

    def footer_as_widget(self, view, item):
        if self.make_footer_widget:
            return self.make_footer_widget(view, item)
        else:
            return Widget(view)

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
        :keyword footer_label: If specified, this text will be put in a footer row for each footer \
              item in this column.              
        :keyword sort_key: If specified, this value will be passed to sort() for sortable tables.

        .. versionchanged:: 5.0
            Added `footer_label`.
    """
    def __init__(self, field, attribute_name, footer_label=None, sort_key=None):
        make_footer_widget = self.make_footer if footer_label else None
        super().__init__(field.label, self.make_text_node, make_footer_widget=make_footer_widget, sort_key=sort_key)
        self.field = field
        self.attribute_name = attribute_name
        self.footer_label = footer_label

    def make_text_node(self, view, item):
        field = self.field.copy()
        field.bind(self.attribute_name, item)
        return TextNode(view, field.as_input())

    def make_footer(self, view, item):
        return TextNode(view, self.footer_label)


class Table(HTMLElement):
    """An HTML table element: data displayed on columns and rows.

       :param view: (See :class:`reahl.web.fw.Widget`)
       :keyword caption_text: If text is given here, a caption will be added to the table containing the caption text.
       :keyword summary:  A textual summary of the contents of the table which is not displayed visually, \
                but may be used by a user agent for accessibility purposes.
       :keyword css_id: (See :class:`reahl.web.ui.HTMLElement`)

    """
    def __init__(self, view, caption_text=None, summary=None, css_id=None):
        super().__init__(view, 'table', children_allowed=True, css_id=css_id)
        self.has_data = False
        if caption_text:
            self.add_child(Caption(view, text=caption_text))
        if summary:
            self.set_attribute('summary', '%s' % summary)

    def with_data(self, columns, items, footer_items=None):
        """Populate the table with the given data. Data is arranged into columns as
           defined by the list of :class:`DynamicColumn` or :class:`StaticColumn` instances passed in.

           :param columns: The :class:`DynamicColumn` instances that define the contents of the table.
           :param items: A list containing objects represented in each row of the table.
           :keyword footer_items: If given a footer is added. A list containing objects represented in each footer row of the table.

           .. versionchanged:: 5.0
              Added `footer_items`.
        """
        if self.has_data:
            raise ProgrammerError('This table has already been populated.')
        self.has_data = True
        self.create_header_columns(columns)
        self.create_body_rows(columns, items)
        if footer_items is not None:
            self.create_footer_rows(columns, footer_items)
        return self

    def create_header_columns(self, columns):
        table_header = self.get_or_create_header()
        header_tr = table_header.add_child(Tr(self.view))
        for column_number, column in enumerate(columns):
            column_th = header_tr.add_child(Th(self.view))
            column_th.add_child(column.heading_as_widget(self.view))

    def get_or_create_header(self):
        return self.thead or self.add_child(Thead(self.view))

    @property
    def thead(self):
        for child in self.contained_widgets():
            if isinstance(child, Thead):
                return child
        return None

    def create_body_rows(self, columns, items):
        body = self.add_child(Tbody(self.view))
        for item in items:
            row = body.add_child(Tr(self.view))
            for column in columns:
                row_td = row.add_child(Td(self.view))
                row_td.add_child(column.as_widget(self.view, item))

    def create_footer_rows(self, columns, items):
        footer = self.add_child(Tfoot(self.view))
        for item in items:
            row = footer.add_child(Tr(self.view))
            footer_columns = [(columns.index(column), column) for column in columns if column.has_footer]
            next_index = 0
            for index, column in footer_columns:
                if index > next_index:
                    row.add_child(Td(self.view, colspan=index-next_index))
                next_index = index + 1
                row_td = row.add_child(Td(self.view))
                row_td.add_child(column.footer_as_widget(self.view, item))
                
 
