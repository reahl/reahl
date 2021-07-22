
from reahl.web.fw import UserInterface
from reahl.web.ui import HTML5Page, HTMLWidget, Div, LiteralHTML
from reahl.web.plotly import Chart

import plotly.graph_objects as go

class GraphPage(HTML5Page):
    def __init__(self, view):
        super().__init__(view)

        fig1 = self.create_bar_chart_figure()
        self.body.add_child(Chart(view, fig1, 'bar'))

        fig2 = self.create_line_chart_figure()
        self.body.add_child(Chart(view, fig2, 'line'))

    def create_line_chart_figure(self):
        x = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=x, y=[1000, 1500, 1360, 1450, 1470, 1500, 1700], name='first line'))
        fig.add_trace(go.Scatter(x=x, y=[100, 200, 300, 450, 530, 570, 600, 640, 630, 690, ], name='second line'))
        fig.update_layout(
            title="Line chart",
            hovermode="x unified",
            xaxis_title="X Axis Title",
            yaxis_title="Y Axis Title"
        )
        return fig

    def create_bar_chart_figure(self):
        fig = go.Figure()
        fig.add_trace(go.Bar(y=[2, 3, 1], x=['foo', 'bar', 'baz']))
        fig.update_layout(
            title="Bar chart",
            xaxis_title="X Axis Title",
            yaxis_title="Y Axis Title"
        )
        return fig


class PlotlyUI(UserInterface):
    def assemble(self):
        self.define_view('/', title='Home', page=GraphPage.factory())

