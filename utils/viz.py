import requests
import panel as pn
from panel.io import hold
from bokeh.models import ColumnDataSource
from bokeh.models.ranges import FactorRange
from bokeh.plotting import figure
from bokeh.transform import jitter
import pandas as pd
import bokeh.palettes as bp
from bokeh.transform import factor_cmap

pn.extension(sizing_mode="stretch_width", template="fast")
pn.state.template.param.update(title="LiberTEM Benchmarks")


def to_dataframe(raw_json_object, run: str):
    header = ["bench_group", "name", "fullname", "raw_time", "run", "run_short"]
    run_full = f"{run} @ {raw_json_object['machine_info']['node']}"
    rows = [
        (bench['group'], bench['name'], bench['fullname'], value, run_full, run)
        for bench in raw_json_object["benchmarks"]
        for value in bench['stats']['data']
    ]
    return pd.DataFrame(rows, columns=header)


dataframes = []
filenames = []
for i in range(6):
    fn = f"{i + 1:05d}.json"
    r = requests.get(
        f"https://raw.githubusercontent.com/LiberTEM/benchmarks/refs/"
        f"heads/main/collected/LiberTEM/LiberTEM/cpu/{fn}"
    )
    df_this = to_dataframe(r.json(), fn)
    filenames.append(fn)
    dataframes.append(df_this)

df = pd.concat(dataframes, ignore_index=True)

# use this as y axis to "dodge" individual runs:
df["y_factor"] = list(zip(df['name'], df['run_short']))

selectable = df["bench_group"].unique().tolist()

select_test = pn.widgets.Select(
    name="Test name",
    value=selectable[0],
    options=selectable,
)
selected_group = select_test.value


def get_data(group_name: str):
    test_data = df.groupby("bench_group").get_group(group_name)
    return test_data


TOOLTIPS = [
    ('Run info', '@run'),
    ('Name', '@name'),
]

HEIGHT_FACTOR = 25

source_data = get_data(selected_group)
categories = list(sorted(source_data["y_factor"].unique().tolist()))
source = ColumnDataSource(data=source_data)
p = figure(
    width=1200,
    height=HEIGHT_FACTOR * len(categories),
    y_range=FactorRange(*categories, group_padding=2, subgroup_padding=0.1),
    title="Test run",
    tooltips=TOOLTIPS,
)
p.sizing_mode = 'stretch_width'
p.scatter(
    x='raw_time',
    y=jitter("y_factor", width=0.02, range=p.y_range),
    source=source,
    alpha=0.6,
    color=factor_cmap(field_name='run_short', palette=bp.Category20[len(filenames)], factors=filenames),
)
p.xaxis.axis_label = "Time (s)"
p.yaxis.axis_label = "Test name"
p.ygrid.grid_line_color = None
bokeh_plot = pn.pane.Bokeh(p)


@hold()
def update_results(e):
    group_name = e.new
    new_data = get_data(group_name)
    categories = list(sorted(new_data["y_factor"].unique().tolist()))
    p.y_range.factors = categories
    p.height = HEIGHT_FACTOR * len(categories)
    source.update(data=new_data)


select_test.param.watch(update_results, "value")

pn.Column(
    select_test,
    bokeh_plot,
).servable()
