from reahl.web.ui import HTMLWidget, Div, LiteralHTML, HTMLElement
from reahl.web.libraries import PlotlyJS
from reahl.component.context import ExecutionContext


class Chart(HTMLWidget):
    def __init__(self, view, figure, read_check=None, write_check=None):
        super().__init__(view, read_check=read_check, write_check=write_check)
        #ExecutionContext.get_context().config.web.frontend_libraries.add(PlotlyJS(True))
        script_html = PlotlyJS(True).header_only_material(None)
        self.script_coactive_widget = view.add_out_of_bound_widget(LiteralHTML(view, script_html))

        containing_div = self.add_child(Div(view))
        self.set_html_representation(containing_div)
        containing_div.add_child(LiteralHTML(view, figure,
#                                             transform=(lambda i: i.to_html(include_plotlyjs='/static/%s' % PlotlyJS.javascript_filename, full_html=False))))
                                             transform=(lambda i: i.to_html(include_plotlyjs=False, full_html=False))))

    @property
    def coactive_widgets(self):
        return super().coactive_widgets + [self.script_coactive_widget]

