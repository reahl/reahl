


from reahl.web.libraries import Library



class Bootstrap4(Library):
    def __init__(self):
        super(Bootstrap4, self).__init__('bootstrap4')
        self.shipped_in_directory = '/reahl/web/static'
        self.files = [
                      'bootstrap-4.0.0-alpha/css/bootstrap.css',
                      'bootstrap-4.0.0-alpha/css/bootstrap.css.map',
                      'bootstrap-4.0.0-alpha/js/bootstrap.js'
                      ]


    def header_only_material(self, rendered_page):
        return '<meta http-equiv="x-ua-compatible" content="ie=edge">'\
               '<meta name="viewport" content="width=device-width, initial-scale=1">' +\
               super(Bootstrap4, self).header_only_material(rendered_page) 



class ReahlBootstrap4Additions(Library):
    def __init__(self):
        super(ReahlBootstrap4Additions, self).__init__('bootstrap4.reahladditions')
        self.shipped_in_directory = '/reahl/web/bootstrap'
        self.files = [
                      'pagination.js'
                      ]






