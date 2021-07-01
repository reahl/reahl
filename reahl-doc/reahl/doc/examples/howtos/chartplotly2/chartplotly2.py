
from reahl.web.fw import UserInterface, Widget
from reahl.web.ui import HTMLWidget
from reahl.web.plotly.charts import Chart
from reahl.web.bootstrap.ui import Div
from reahl.web.bootstrap.page import HTML5Page
from reahl.web.bootstrap.forms import Form, FormLayout, SelectInput
from reahl.component.modelinterface import ChoiceField, Choice, IntegerField, exposed

import plotly.graph_objects as go


class ChangingChart(HTMLWidget):
    def __init__(self, view):
        super().__init__(view)
        self.set_html_representation(self.add_child(Div(view)))
        self.set_id('changing-chart')
        self.enable_refresh()

    def make_chart(self, factor):
        fig = self.create_line_chart_figure(factor)
        self.html_representation.add_child(Chart(self.view, fig))

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


class ChartForm(Form):
    def __init__(self, view):
        self.factor = 1
        super().__init__(view, 'chartform')
        self.use_layout(FormLayout())

        chart = ChangingChart(view)
        self.layout.add_input(SelectInput(self, self.fields.factor, refresh_widget=chart))
        chart.make_chart(self.factor)

        self.add_child(chart)

    @exposed
    def fields(self, fields):
        fields.factor = ChoiceField([Choice(i, IntegerField(label=str(i))) for i in range(1, 10)])


class GraphPage(HTML5Page):
    def __init__(self, view):
        super().__init__(view)

        self.body.add_child(ChartForm(view))



class DynamicPlotlyUI(UserInterface):
    def assemble(self):
        self.define_view('/', title='Home', page=GraphPage.factory())

