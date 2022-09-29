
from reahl.web.fw import UserInterface
from reahl.web.plotly import Chart

from reahl.web.bootstrap.page import HTML5Page
from reahl.web.bootstrap.forms import Form, FormLayout, SelectInput
from reahl.component.modelinterface import ChoiceField, Choice, IntegerField, ExposedNames

import plotly.graph_objects as go


class ChartForm(Form):
    def __init__(self, view):
        super().__init__(view, 'chartform')
        self.factor = 1
        self.use_layout(FormLayout())

        select_input = self.layout.add_input(SelectInput(self, self.fields.factor))  # Creating the input, sets self.factor
        chart = self.create_chart(self.factor)
        select_input.set_refresh_widgets([chart.contents])

    def create_chart(self, factor):
        fig = self.create_line_chart_figure(factor)
        return self.add_child(Chart(self.view, fig, 'changing-chart'))

    fields = ExposedNames()
    fields.factor = lambda i: ChoiceField([Choice(c, IntegerField(label=str(c))) for c in range(1, 10)])

    def create_line_chart_figure(self, factor):
        x = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=x, y=[1000, 1500, 1360, 1450, 1470, 1500, 1700], name='first line'))
        fig.add_trace(go.Scatter(x=x, y=[i*factor for i in [100, 200, 300, 450, 530, 570, 600, 640, 630, 690, ]], name='second line'))
        fig.update_layout(
            title="Line chart",
            hovermode="x unified",
            xaxis_title="X Axis Title",
            yaxis_title="Y Axis Title"
        )
        return fig


class GraphPage(HTML5Page):
    def __init__(self, view):
        super().__init__(view)
        self.body.add_child(ChartForm(view))


class DynamicPlotlyUI(UserInterface):
    def assemble(self):
        self.define_view('/', title='Home', page=GraphPage.factory())

