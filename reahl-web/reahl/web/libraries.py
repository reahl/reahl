
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
        for file_name in self.files_of_type('.js'):
            result += '\n<script type="text/javascript" src="/static/%s"></script>' % file_name
        for file_name in self.files_of_type('.css'):
            result += '\n<link rel="stylesheet" href="/static/%s" type="text/css">' % file_name
        return result

    def footer_only_material(self, rendered_page):
        return ''



class JQuery(Library):
    def __init__(self):
        super(JQuery, self).__init__('jquery')
        self.files = ['jquery-1.8.1.js']
        self.shipped_in_directory = '/reahl/web/static/%s' % self.name
        for i in ['jquery.cookie-1.0.js', 
                  'jquery.metadata-2.1.js',
                  'jquery.validate-1.10.0.modified.js',
                  'jquery.ba-bbq-1.2.1.js',
                  'jquery.blockUI-2.43.js',
                  'jquery.form-3.14.js']:
            self.add_shipped_plugin(i)

    def add_shipped_plugin(self, file_name):
        self.files.append(file_name)

    def header_only_material(self, rendered_page):
        return super(JQuery, self).header_only_material(rendered_page) +\
            self.document_ready_material(rendered_page)

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
        #from http://ryanpricemedia.com/2008/03/19/jquery-broken-in-internet-explorer-put-your-documentready-at-the-bottom/
        return '<!--[if IE 6]>' + self.document_ready_material(rendered_page) +  '<![endif]-->'
        
        

        
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


class IE9(Library):
    def __init__(self):
        super(IE9, self).__init__('IE9')
        self.shipped_in_directory = '/reahl/web/static'
        self.files = ['IE9.js']

    def header_only_material(self, rendered_page):
        # From: http://remysharp.com/2009/01/07/html5-enabling-script/ 
        result  = '\n<!--[if lt IE 9]>'
        result  += '<script src="/static/html5shiv-printshiv-3.6.3.js" type="text/javascript"></script>'
        result  += '<![endif]-->'
        # From: http://code.google.com/p/ie7-js/ 
        # Not sure if this does not perhaps interfere with Normalize reset stuff? 
        result  += '\n<!--[if lte IE 9]>'  
        result  += '<script src="/static/IE9.js" type="text/javascript"></script>'
        result  += '<![endif]-->'  
        return result
