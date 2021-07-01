from reahl.web.ui import HTMLWidget, Div, LiteralHTML
from reahl.web.libraries import PlotlyJS
from reahl.component.context import ExecutionContext

class Chart(HTMLWidget):
    def __init__(self, view, figure, read_check=None, write_check=None):
        super().__init__(view, read_check=read_check, write_check=write_check)
        ExecutionContext.get_context().config.web.frontend_libraries.add(PlotlyJS(True))

        containing_div = self.add_child(Div(view))
        self.set_html_representation(containing_div)
        containing_div.add_child(LiteralHTML(view, figure,
#                                             transform=(lambda i: i.to_html(include_plotlyjs='/static/%s' % PlotlyJS.javascript_filename, full_html=False))))
                                             transform=(lambda i: i.to_html(include_plotlyjs=False, full_html=False))))

