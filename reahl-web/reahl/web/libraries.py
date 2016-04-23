
import itertools
from collections import OrderedDict

from reahl.component.exceptions import ProgrammerError
from reahl.component.context import ExecutionContext
from reahl.web.fw import PackagedFile, ConcatenatedFile

class LibraryIndex(object):
    def __init__(self, *libraries):
        self.libraries_by_name = OrderedDict()
        for library in libraries:
            self.add(library)

    def clear(self):
        self.libraries_by_name.clear()

    def add(self, library):
        self.libraries_by_name[library.name] = library

    def __contains__(self, name):
        return name in self.libraries_by_name

    def packaged_files(self):
        return [i for i in itertools.chain(*[library.packaged_files() for library in self])]

    def __iter__(self):
        return iter(self.libraries_by_name.values())
        
    def use_deprecated_yui(self):
        if 'pure' in self:
            del self.libraries_by_name['pure']
        if 'yuigridscss' not in self:
            self.add(YuiGridsCss())

    def enable_experimental_bootstrap(self):
        from reahl.web.bootstrap.libraries import Tether, Bootstrap4, ReahlBootstrap4Additions
        if 'pure' in self:
            del self.libraries_by_name['pure']
        self.add(Tether())
        self.add(Bootstrap4())
        self.add(ReahlBootstrap4Additions())
        

class Library(object):
    def __init__(self, name):
        self.name = name
        self.files = []
        self.shipped_in_directory = ''
        self.egg_name = 'reahl-web'
        self.egg_relative_static_root = 'reahl/web/static'

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
    def __init__(self):
        super(JQueryUI, self).__init__('jqueryui')
        self.shipped_in_directory = '/reahl/web/static'
        self.files = ['jquery-ui-1.10.3.custom.js']



class Pure(Library):
    def __init__(self):
        super(Pure, self).__init__('pure')
        self.shipped_in_directory = '/reahl/web/static/pure-release-0.5.0'
        self.files = ['base.css', 'grids.css', 'grids-responsive.css']


class YuiGridsCss(Library):
    @classmethod
    def is_enabled(cls):
        frontend_libraries = ExecutionContext.get_context().config.web.frontend_libraries
        return 'yuigridscss' in frontend_libraries

    @classmethod
    def check_enabled(cls, calling_object):
        if not cls.is_enabled():
            raise ProgrammerError('YuiGridsCss not enabled in current configuration. For %s to work, add the line: \n'\
                                  '"web.frontend_libraries.use_deprecated_yui()"\n in your web.config.py'\
                                   % calling_object.__class__.__name__)

    def __init__(self):
        super(YuiGridsCss, self).__init__('yuigridscss')
        self.shipped_in_directory = '/reahl/web/static'
        self.files = ['reset-fonts-grids.css']


class HTML5Shiv(Library):
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
    def __init__(self):
        super(Reahl, self).__init__('reahl')

    def header_only_material(self, rendered_page):
        return '\n<link rel="stylesheet" href="/static/reahl.css" type="text/css">' 

    def footer_only_material(self, rendered_page):
        return '\n<script type="text/javascript" src="/static/reahl.js"></script>'



class Holder(Library):
    def __init__(self):
        super(Holder, self).__init__('holder')
        self.shipped_in_directory = '/reahl/web/holder'
        self.files = ['holder-2.9.0.js']







