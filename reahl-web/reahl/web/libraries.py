# Copyright 2015, 2016 Reahl Software Services (Pty) Ltd. All rights reserved.
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
""".. versionadded:: 3.2

Reahl uses CSS and JavaScript from other projects. The CSS and JavaScript world
has its own ecosystem of tools that allow you to do various things, for example:

 - Compile your own customised CSS using a CSS preprocessor like `Sass <http://sass-lang.com/>`_\.
 - Manage the versions and interdependencies of such projects.
 - Some code is hosted on Content Delivery Networks (CDNs).
 - Some code is minified.

This module is a start towards supporting such "front-end frameworks"
which Reahl depends upon. Currently, Reahl merely includes the correct
versions of the front-end libraries it needs and a user is not able to
customise these in any way. In the future we hope to extend this
infrastructure to be able to make use of everything the JavaScript /
CSS tool ecosystem offers.

Reahl also contains its own JavaScript and CSS code. Where we do this,
our own code is also managed using this same infrastructure.

If you write your own Widgets that make use of CSS or JavaScript,
creating a :class:`Library` is the way to do it going forward.

"""

import itertools
from collections import OrderedDict

from reahl.component.exceptions import ProgrammerError
from reahl.component.context import ExecutionContext
from reahl.web.fw import PackagedFile, ConcatenatedFile

class LibraryIndex(object):
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

    def __contains__(self, name):
        """An implementation of the `in` operator, so that one can ask whether a library with given name is in this index.

        :param name: The unique name of the Library to check for.
        """
        return name in self.libraries_by_name

    def packaged_files(self):
        return [i for i in itertools.chain(*[library.packaged_files() for library in self])]

    def __iter__(self):
        return iter(self.libraries_by_name.values())
        

class Library(object):
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
    def __init__(self, name):
        self.name = name  #: The unique name of this Library
        self.egg_name = 'reahl-web'  #: The component (egg) that contains the files of this library
        self.shipped_in_directory = ''  #: The directory that contains the files of this library (relative to the egg root)
        self.files = []   #: The JavaScript and CSS files that form part of this library (relative to the `shipped_in_directory`)

    def packaged_files(self):
        return [PackagedFile(self.egg_name, self.shipped_in_directory, file_name) 
                for file_name in self.files]

    def packaged_files222xxxxxFIXMEIAMDEADButPossibleAlternative(self):
        exposed_files = []
        js_files_to_include = [PackagedFile(self.egg_name, self.shipped_in_directory, file_name) 
                               for file_name in self.files
                               if file_name.endswith('.js')]
        if js_files_to_include:
            exposed_files.append(ConcatenatedFile('%s.js' % self.name, js_files_to_include))

        css_files_to_include = [PackagedFile(self.egg_name, self.shipped_in_directory, file_name) 
                               for file_name in self.files
                               if file_name.endswith('.css')]
        if css_files_to_include:
            exposed_files.append(ConcatenatedFile('%s.css' % self.name, css_files_to_include))
        return exposed_files


    def files_of_type(self, extension):
        return [f for f in self.files if f.endswith(extension)]

    def header_only_material(self, rendered_page):
        result = ''
        for file_name in self.files_of_type('.css'):
            result += '\n<link rel="stylesheet" href="/static/%s" type="text/css">' % file_name
        return result

    def footer_only_material(self, rendered_page):
        result = ''
        for file_name in self.files_of_type('.js'):
            result += '\n<script type="text/javascript" src="/static/%s"></script>' % file_name
        return result


    
class JQuery(Library):
    """Version 1.11.2 of `JQuery <https://jquery.com>`_.

    This Library also includes a number of plugins we use internally:

    =================== ==================================
     Plugin              Version
    =================== ==================================
     jquery-migrate      1.2.1
     jquery.cookie       1.0
     jquery.metadata     2.1
     jquery.validate     1.10.0 (a heavily modified version)
     jquery.ba-bbq       1.2.1
     jquery.blockUI      2.70.0
     jquery.form         3.14
    =================== ==================================
    """
    def __init__(self):
        super(JQuery, self).__init__('jquery')
        self.files = ['jquery-1.11.2/jquery-1.11.2.js',
                      'jquery-1.11.2/jquery-1.11.2.min.map']
        self.shipped_in_directory = '/reahl/web/static'
        for i in ['jquery-migrate-1.2.1.js',
                  'jquery.cookie-1.0.js', 
                  'jquery.metadata-2.1.js',
                  'jquery.validate-1.10.0.modified.js',
                  'jquery.ba-bbq-1.2.1.js',
                  'jquery.blockUI-2.70.0.js',
                  'jquery.form-3.14.js']:
            self.add_shipped_plugin('jquery/%s' % i)

    def add_shipped_plugin(self, file_name):
        self.files.append(file_name)

    def document_ready_material(self, rendered_page):
        result = '\n<script type="text/javascript">\n'
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
        result = super(JQuery, self).footer_only_material(rendered_page)
        #from http://ryanpricemedia.com/2008/03/19/jquery-broken-in-internet-explorer-put-your-documentready-at-the-bottom/
        result += self.document_ready_material(rendered_page)
        return result
        
        

        
class JQueryUI(Library):
    """A heavily customised subset of version 1.10.3 of `JQuery UI <https://jqueryui.com>`_.
    
    .. warning:: 
    
       This Library will be trimmed in future to only contain
       the `Widget Factory <http://api.jqueryui.com/jQuery.widget/>`_.
    """
    def __init__(self):
        super(JQueryUI, self).__init__('jqueryui')
        self.shipped_in_directory = '/reahl/web/static'
        self.files = ['jquery-ui-1.10.3.custom.js']



class HTML5Shiv(Library):
    """Version 3.6.3 of `html5shiv <https://github.com/aFarkas/html5shiv>`_.
    
    """
    def __init__(self):
        super(HTML5Shiv, self).__init__('html5shiv')
        self.shipped_in_directory = '/reahl/web/static'
        self.files = ['html5shiv-printshiv-3.6.3.js']

    def footer_only_material(self, rendered_page):
        # From: http://remysharp.com/2009/01/07/html5-enabling-script/ 
        result  = '\n<!--[if lt IE 9]>'
        result  += super(HTML5Shiv, self).footer_only_material(rendered_page)
        result  += '<![endif]-->'
        return result


class IE9(Library):
    """Version 2.1(beta4) of `IE9.js <https://code.google.com/archive/p/ie7-js/>`_.
    """
    def __init__(self):
        super(IE9, self).__init__('IE9')
        self.shipped_in_directory = '/reahl/web/static'
        self.files = ['IE9.js']

    def footer_only_material(self, rendered_page):
        # From: http://code.google.com/p/ie7-js/ 
        # Not sure if this does not perhaps interfere with Normalize reset stuff? 
        result  = '\n<!--[if lte IE 9]>'
        result  += super(IE9, self).footer_only_material(rendered_page)
        result  += '<![endif]-->'
        return result


class Reahl(Library):
    """JavaScript and CSS that is part of Reahl itself.
    """
    def __init__(self):
        super(Reahl, self).__init__('reahl')
        self.shipped_in_directory = '/reahl/web/static'
        self.files = ['reahl.hashchange.js',
                      'reahl.ajaxlink.js',
                      'reahl.textinput.js',
                      'reahl.validate.js',
                      'reahl.css',
                      'reahl.runningonbadge.css',
                      'runningon.png'
                      ]


class Holder(Library):
    """Version 2.9.0 of `Holder <http://imsky.github.io/holder/>`_.
    """
    def __init__(self):
        super(Holder, self).__init__('holder')
        self.shipped_in_directory = '/reahl/web/holder'
        self.files = ['holder-2.9.0.js']


class Bootstrap4(Library):
    """Version 4.0.0 alpha 2 of `Bootstrap <http://getbootstrap.com/>`_.
    """
    def __init__(self):
        super(Bootstrap4, self).__init__('bootstrap4')
        self.shipped_in_directory = '/reahl/web/static'
        self.files = [
                      'bootstrap-4.0.0-alpha.2/css/bootstrap.css',
                      'bootstrap-4.0.0-alpha.2/css/bootstrap.css.map',
                      'bootstrap-4.0.0-alpha.2/js/bootstrap.js'
                      ]


    def header_only_material(self, rendered_page):
        return '<meta http-equiv="x-ua-compatible" content="ie=edge">'\
               '<meta name="viewport" content="width=device-width, initial-scale=1">' +\
               super(Bootstrap4, self).header_only_material(rendered_page) 



class ReahlBootstrap4Additions(Library):
    """Reahl specific JavaScript and CSS for use with :class:`Bootstrap4`.
    """
    def __init__(self):
        super(ReahlBootstrap4Additions, self).__init__('bootstrap4.reahladditions')
        self.shipped_in_directory = '/reahl/web/bootstrap'
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

class Tether(Library):
    """Version 1.1.1 of `Tether <http://github.hubspot.com/tether/>`_.
    """
    def __init__(self):
        super(Tether, self).__init__('tether')
        self.shipped_in_directory = '/reahl/web/static'
        self.files = [
                      'tether.1.1.1/css/tether.css',
                      'tether.1.1.1/css/tether-theme-arrows.css',
                      'tether.1.1.1/css/tether-theme-arrows-dark.css',
                      'tether.1.1.1/css/tether-theme-basic.css',
                      'tether.1.1.1/js/tether.js'
                      ]






