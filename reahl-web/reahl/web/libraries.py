# Copyright 2015-2022 Reahl Software Services (Pty) Ltd. All rights reserved.
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
""".. versionadded:: 3.2

Reahl uses CSS and JavaScript from other projects. The CSS and JavaScript world
has its own ecosystem of tools that allow you to do various things, for example:

 - Compile your own customised CSS using a CSS preprocessor like `Sass <http://sass-lang.com/>`_
 - Manage the versions and interdependencies of such projects.
 - Some code is hosted on Content Delivery Networks (CDNs).
 - Some code is minified.

This module is a start towards supporting such "front-end frameworks"
which Reahl depends upon. By default, Reahl merely includes the correct
versions of the front-end libraries it needs.

Reahl also contains its own JavaScript and CSS code. Where we do this,
our own code is also managed using this same infrastructure.

If you write your own Widgets that make use of CSS or JavaScript,
creating a :class:`Library` and configure your site to use it.

"""

import itertools
from collections import OrderedDict

from reahl.component.context import ExecutionContext
from reahl.component.exceptions import ProgrammerError
from reahl.component.decorators import  deprecated
from reahl.web.fw import PackagedFile, ConcatenatedFile


class LibraryIndex:
    """An ordered collection of :class:`Library` instances.

    A LibraryIndex instance is available in the configuration as
    `web.config.frontend_libraries`. All the :class:`Library`
    instances contained in `web.config.frontend_libraries` are
    included on any :class:`~reahl.web.ui.HTML5Page`.

    Libraries in a LibraryIndex are included on a page in the order
    that they appear in the LibraryIndex.

    :param libraries: :class:`Library` instances (in order) to initialise this LibraryIndex with.

    """
    def __init__(self, *libraries):
        self.libraries_by_name = OrderedDict()
        for library in libraries:
            self.add(library)

    def clear(self):
        """Removes all Libraries from the list."""
        self.libraries_by_name.clear()

    def add(self, library):
        """Adds a Library to the end of the list."""
        self.libraries_by_name[library.name] = library
        return library

    def get(self, library_class):
        matching_libraries = [i for i in self.libraries_by_name.values() if isinstance(i, library_class)]
        if not matching_libraries:
            raise ProgrammerError('No library "%s" found in the config.web.frontend_libraries' % library_class)
        elif len(matching_libraries) > 1:
            raise ProgrammerError('More than "%s" found in the config.web.frontend_libraries' % library_class)
        return matching_libraries[0]

    def __contains__(self, name):
        """An implementation of the `in` operator, so that one can ask whether a library with given name is in this index.

        :param name: The unique name of the Library to check for.
        """
        return name in self.libraries_by_name

    def packaged_files(self):
        return [i for i in itertools.chain(*[library.packaged_files() for library in self])]

    def __iter__(self):
        return iter(self.libraries_by_name.values())

    def prepend(self, library):
        new_libraries = [library] + list(self.libraries_by_name.values())
        self.libraries_by_name = OrderedDict()
        for library in new_libraries:
            self.add(library)

    def __str__(self):
        return  '%s(%s)' % (self.__class__.__name__, ','.join(self.libraries_by_name.keys()))

class Library:
    """A frontend-library: a collection of CSS and JavaScript code that can be used with Reahl.

    To create your own Library, subclass from this class and set its
    attributes to indicate which files to include as part of it and
    where to find them.

    To use a library, add it to the `web.config.frontend_libraries`
    config setting. The CSS and JavaScript files of all such
    configured libraries are automatically included in any
    :class:`~reahl.web.ui.HTML5Page`.

    :param name: A unique name for this Library.
    """
    active = True
    @classmethod
    def get_instance(cls):
        return ExecutionContext.get_context().config.web.frontend_libraries.get(cls)

    def __init__(self, name):
        self.name = name  #: The unique name of this Library
        self.egg_name = 'reahl-web'  #: The component (egg) that contains the files of this library
        self._shipped_in_directory = ''  #: Deprecated since 6.1: The directory that contains the files of this library (relative to the egg root)
        self.shipped_in_package = ''  #: The package that contains the files of this library
        self.files = []   #: The JavaScript and CSS files that form part of this library (relative to the `shipped_in_package`)

    def __getattr__(self, name):
        if name == 'shipped_in_package':
            return self.shipped_in_directory.replace('/', '.')
        else:
            return super.__getattr__(name)
    @property
    def shipped_in_directory(self):
        return self._shipped_in_directory
    @shipped_in_directory.setter
    @deprecated('Use shipped_in_package with dotted notation instead', '6.1')
    def shipped_in_directory(self, value):
        self._shipped_in_directory = value

    def packaged_files(self):
        return [PackagedFile(self.egg_name, self.shipped_in_package, file_name)
                for file_name in self.files]

    def packaged_files222xxxxxFIXMEIAMDEADButPossibleAlternative(self):
        exposed_files = []
        js_files_to_include = [PackagedFile(self.egg_name, self.shipped_in_package, file_name)
                               for file_name in self.files
                               if file_name.endswith('.js')]
        if js_files_to_include:
            exposed_files.append(ConcatenatedFile('%s.js' % self.name, js_files_to_include))

        css_files_to_include = [PackagedFile(self.egg_name, self.shipped_in_package, file_name)
                               for file_name in self.files
                               if file_name.endswith('.css')]
        if css_files_to_include:
            exposed_files.append(ConcatenatedFile('%s.css' % self.name, css_files_to_include))
        return exposed_files

    def files_of_type(self, extension):
        return [f for f in self.files if f.endswith(extension)]

    def header_only_material(self, rendered_page):
        result = ''
        if self.active:
            for file_name in self.files_of_type('.css'):
                result += '\n<link rel="stylesheet" href="/static/%s" type="text/css">' % file_name
        return result

    def footer_only_material(self, rendered_page):
        result = ''
        if self.active:
            for file_name in self.files_of_type('.js'):
                result += '\n<script type="text/javascript" src="/static/%s"></script>' % file_name
        return result

    def inline_material(self):
        result = ''
        for file_name in self.files_of_type('.js'):
            result += '\n<script type="text/javascript" src="/static/%s"></script>' % file_name
        return result

    
class JQuery(Library):
    """Version 3.6.1 of `JQuery <https://jquery.com>`_.

    This Library also includes a number of plugins we use internally:

    =================== ==================================
     Plugin              Version
    =================== ==================================
     jquery.validate     1.19.5 (a heavily modified version) (https://github.com/jquery-validation/jquery-validation/releases/tag/1.19.5)
     jquery.ba-bbq       1.3pre
     jquery.blockUI      2.70.0 (https://github.com/malsup/blockui/releases)
     jquery.form         4.3.0 (https://github.com/jquery-form/form/releases)
    =================== ==================================
    """
    def __init__(self):
        super().__init__('jquery')
        self.files = ['jquery-3.6.1/jquery-3.6.1.min.js',
                      'jquery-3.6.1/jquery-3.6.1.min.map']
        self.shipped_in_package = 'reahl.web.static'
        for i in ['jquery.validate-1.19.5.modified.js',
                  'jquery.ba-bbq-1.3pre.js',
                  'jquery.blockUI-2.70.0.js',
                  'jquery.form-4.3.0.js']:
            self.add_shipped_plugin('jquery/%s' % i)

    def add_shipped_plugin(self, file_name):
        self.files.append(file_name)
        return file_name

    def document_ready_material(self, rendered_page):
        result = '\n<script id="reahl-jqueryready" type="text/javascript">\n'
        result += 'jQuery(document).ready(function($){\n'
        result += '$(\'body\').addClass(\'enhanced\');\n'
        js = set()
        js.update(rendered_page.get_js())
        for item in sorted(js):
            result += item+'\n'
        result += '\n});'
        result += '\n</script>\n'
        return result

    def footer_only_material(self, rendered_page):
        result = super().footer_only_material(rendered_page)
        #from http://ryanpricemedia.com/2008/03/19/jquery-broken-in-internet-explorer-put-your-documentready-at-the-bottom/
        result += self.document_ready_material(rendered_page)
        return result


class JQueryUI(Library):
    """A heavily customised subset of version 1.13.2 of `JQuery UI <https://jqueryui.com>`_.
    
   Only contains the `Widget Factory <http://api.jqueryui.com/jQuery.widget/>`_ and :tabbable, :focusable Selector.
    """
    def __init__(self):
        super().__init__('jqueryui')
        self.shipped_in_package = 'reahl.web.static'
        self.files = ['jquery-ui-1.13.2.custom/jquery-ui.min.js']


class HTML5Shiv(Library):
    """Version 3.7.3 of `html5shiv <https://github.com/aFarkas/html5shiv>`_.
    
    """
    def __init__(self):
        super().__init__('html5shiv')
        self.shipped_in_package = 'reahl.web.static'
        self.files = ['html5shiv-printshiv-3.7.3.js']

    def footer_only_material(self, rendered_page):
        # From: http://remysharp.com/2009/01/07/html5-enabling-script/ 
        result  = '\n<!--[if lt IE 9]>'
        result  += super().footer_only_material(rendered_page)
        result  += '<![endif]-->'
        return result


class IE9(Library):
    """Version 2.1(beta4) of `IE9.js <https://code.google.com/archive/p/ie7-js/>`_.
    """
    def __init__(self):
        super().__init__('IE9')
        self.shipped_in_package = 'reahl.web.static'
        self.files = ['IE9.js']

    def footer_only_material(self, rendered_page):
        # From: http://code.google.com/p/ie7-js/ 
        # Not sure if this does not perhaps interfere with Normalize reset stuff? 
        result  = '\n<!--[if lte IE 9]>'
        result  += super().footer_only_material(rendered_page)
        result  += '<![endif]-->'
        return result


class Reahl(Library):
    """JavaScript and CSS that is part of Reahl itself.
    """
    def __init__(self):
        super().__init__('reahl')
        self.shipped_in_package = 'reahl.web.static'
        self.files = ['reahl.csrf.js',
                      'reahl.hashchange.js',
                      'reahl.ajaxlink.js',
                      'reahl.primitiveinput.js',
                      'reahl.textinput.js',
                      'reahl.validate.js',
                      'reahl.form.js',
                      'reahl.plotlychart.js',
                      'reahl.css',
                      'reahl.runningonbadge.css',
                      'runningon.png'
                      ]


class Holder(Library):
    """Version 2.9.9 of `Holder <http://imsky.github.io/holder/>`_.
    """
    def __init__(self):
        super().__init__('holder')
        self.shipped_in_package = 'reahl.web.holder'
        self.files = ['holder-2.9.9.js']


class Bootstrap4(Library):
    """Version 4.6.2 of `Bootstrap <http://getbootstrap.com/>`_.
    """
    def __init__(self):
        super().__init__('bootstrap4')
        self.shipped_in_package = 'reahl.web.static'
        self.files = [
                      'bootstrap-4.6.2/css/bootstrap.css',
                      'bootstrap-4.6.2/css/reahl-patch.css',
                      'bootstrap-4.6.2/css/bootstrap.css.map',
                      'bootstrap-4.6.2/js/bootstrap.min.js',
                      'bootstrap-4.6.2/js/bootstrap.min.js.map'
                      ]


    def header_only_material(self, rendered_page):
        return '<meta charset="utf-8">'\
               '<meta name="viewport" content="width=device-width, initial-scale=1, shrink-to-fit=no">' +\
               super().header_only_material(rendered_page) 


class ReahlBootstrap4Additions(Library):
    """Reahl specific JavaScript and CSS for use with :class:`Bootstrap4`.
    """
    def __init__(self):
        super().__init__('bootstrap4.reahladditions')
        self.shipped_in_package = 'reahl.web.bootstrap'
        self.files = [
                      'reahl.bootstrapform.js',
                      'reahl.pagination.js',
                      'reahl.files.js',
                      'reahl.files.css',
                      'reahl.bootstrappopupa.js',
                      'reahl.carousel.css',
                      'reahl.bootstrapcueinput.js',
                      'reahl.bootstrapfileuploadli.js',
                      'reahl.bootstrapfileuploadpanel.js',
                      'reahl.datatable.css'
                      ]


class Popper(Library):
    """Version 1.16.1 (umd) of `Popper <https://popper.js.org/>`_.
    """
    def __init__(self):
        super().__init__('popper')
        self.shipped_in_package = 'reahl.web.static'
        self.files = [
            'popper-1.16.1/popper.min.js' #make sure it is the umd edition
        ]


class Underscore(Library):
    """Version 1.13.6 of `Underscore.js <https://underscorejs.org>`_.
    """
    def __init__(self):
        super().__init__('underscore')
        self.shipped_in_package = 'reahl.web.static'
        self.files = [
            'underscore-umd-min.1.13.6.js'
        ]
    def footer_only_material(self, rendered_page):
        return super().footer_only_material(rendered_page) + '<script>var underscore = _;</script>'


class JsCookie(Library):
    """Version 3.0.1 of `js-cookie <https://github.com/js-cookie/js-cookie>`_.
    """
    def __init__(self):
        super().__init__('js-cookie')
        self.shipped_in_package = 'reahl.web.static'
        self.files = [
            'js-cookie-3.0.1/js.cookie.min.js' #this is the UMD version
        ]


class PlotlyJS(Library):
    """Version 2.16.4 of `plotly.js <https://github.com/plotly/plotly.js/>`_.
    """
    javascript_filename = 'plotly-2.16.4.min.js'
    def __init__(self):
        self.active = False
        super().__init__('plotly.js')
        self.shipped_in_package = 'reahl.web.static'
        self.files = [
            self.javascript_filename
        ]
