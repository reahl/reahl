import json

from reahl.web.ui import HTMLWidget, Div, LiteralHTML, HTMLElement
from reahl.web.libraries import PlotlyJS


class RefreshedJS(Div):
    def __init__(self, chart):
        super().__init__(chart.view, css_id='%s-data-container' % chart.css_id)
        self.chart = chart

    def get_js(self, context=None):
        options = { 'chart_id': self.chart.css_id,
                    'json': json.loads(self.chart.figure.to_json())}
        return super().get_js(context=context) + ['$(%s).plotlychartdata(%s);' % (self.jquery_selector,
                                                                                  json.dumps(options))]

class ChartData(Div):
    def __init__(self, chart):
        super().__init__(chart.view, css_id='%s-data' % chart.css_id)
        self.div = self.add_child(RefreshedJS(chart))
        self.enable_refresh()



class Chart(HTMLWidget):
    def __init__(self, view, figure, read_check=None, write_check=None):
        super().__init__(view, read_check=read_check, write_check=write_check)
        self.figure = figure
        containing_div = self.add_child(Div(view, css_id='unique_id'))
        containing_div.append_class('reahl-plotlychart')
        self.set_html_representation(containing_div)
        script = containing_div.add_child(HTMLElement(view, 'script', children_allowed=True))
        script.set_attribute('src', '/static/%s' % PlotlyJS.javascript_filename)
        self.data = containing_div.add_child(ChartData(self))
#        containing_div.add_child(LiteralHTML(view, figure,
#                                             transform=(lambda i: i.to_html(include_plotlyjs='/static/%s' % PlotlyJS.javascript_filename, full_html=False))))
#                                             transform=(lambda i: i.to_html(include_plotlyjs=False, full_html=False))))

    def get_js(self, context=None):
        options = { 'id': self.css_id,
                    'json': json.loads(self.figure.to_json())}
        return super().get_js(context=context) + ['$(%s).plotlychart(%s);' % (self.html_representation.jquery_selector,
                                                                              json.dumps(options))]
