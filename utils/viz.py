import requests
import panel as pn
from panel.io import hold
from bokeh.models import ColumnDataSource
from bokeh.plotting import figure
from bokeh.transform import jitter
import pandas as pd

pn.extension(sizing_mode="stretch_width", template="fast")
pn.state.template.param.update(title="LiberTEM Benchmarks")


def to_dataframe(raw_json_object, group: str):
    header = ["name", "fullname", "raw_time", "group", "group_short"]
    group_full = f"{group} @ {raw_json_object['machine_info']['node']}"
    rows = [
        (bench['name'], bench['fullname'], value, group_full, group)
        for bench in raw_json_object["benchmarks"]
        for value in bench['stats']['data']
    ]
    return pd.DataFrame(rows, columns=header)


r = requests.get(
    "https://raw.githubusercontent.com/LiberTEM/benchmarks/refs/"
    "heads/main/collected/LiberTEM/LiberTEM/cpu/00003.json"
)
df = to_dataframe(r.json(), "Current")
test_names = df["name"].unique().tolist()

select_test = pn.widgets.Select(
    name="Test name",
    value=test_names[0],
    options=test_names,
)
current_test = select_test.value


def get_data(test_name: str):
    test_data = df.groupby("name").get_group(test_name)
    return {
        "time": test_data["raw_time"].to_numpy(),
        "test_name": test_data["name"].tolist(),
    }


source = ColumnDataSource(data=get_data(current_test))
p = figure(
    width=800,
    height=300,
    y_range=[current_test],
    title="Test run",
)
p.scatter(x='time', y=jitter("test_name", width=0.6, range=p.y_range), source=source, alpha=0.3)
p.xaxis.axis_label = "Time (s)"
p.yaxis.axis_label = "Test name"
p.ygrid.grid_line_color = None
bokeh_plot = pn.pane.Bokeh(p)


@hold()
def update_results(e):
    test_name = e.new
    new_data = get_data(test_name)
    p.y_range.factors = [test_name]
    source.update(data=new_data)


select_test.param.watch(update_results, "value")

pn.Column(
    select_test,
    bokeh_plot,
).servable()
