# deps: panel, bokeh, pygments, pandas, requests

import datetime
import copy
import difflib
import json

import requests
import panel as pn
from panel.io import hold
from bokeh.models import ColumnDataSource
from bokeh.models.ranges import FactorRange
from bokeh.plotting import figure
from bokeh.transform import jitter
from bokeh.resources import INLINE
import pandas as pd
import bokeh.palettes as bp
from bokeh.transform import factor_cmap

pn.extension(sizing_mode="stretch_width", template="fast")
pn.state.template.param.update(title="LiberTEM Benchmarks")

# TODO
# - [ ] sticky axis? 
# - [ ] better visualization after zooming in!
# - [ ] better scalability -> need an overview for many benchmarks; more compact view somehow?



def to_dataframe(raw_json_object, run: str):
    header = ["commit", "bench_group", "name", "fullname", "raw_time", "run", "run_short"]
    short_commit = raw_json_object['commit_info']['id'][:8]
    run_full = f"{run} / {short_commit}"
    rows = [
        (
            raw_json_object['commit_info']['id'][:8],
            bench['group'],
            bench['name'],
            bench['fullname'],
            value,
            run_full,
            run
        )
        for bench in raw_json_object["benchmarks"]
        for value in bench['stats']['data']
    ]
    return pd.DataFrame(rows, columns=header)


def _version_set(version_list):
    return set(tuple(x) for x in version_list)


def _sort_data(raw_data):
    return list(sorted(raw_data, key=lambda bs: datetime.datetime.fromisoformat(bs[0]["datetime"])))


def _filtered_machine_info(machine_info):
    filtered = copy.deepcopy(machine_info)
    # dependency versions are handled outside:
    del filtered['freeze']
    # node will be different in most runs:
    del filtered['node']

    # frequency is measured in a dubious way and as such not relevant:
    filtered['cpu'].pop('hz_advertised_friendly', None)
    filtered['cpu'].pop('hz_advertised', None)
    filtered['cpu'].pop('hz_actual', None)
    filtered['cpu'].pop('hz_actual_friendly', None)
    return filtered


def _json_diff(a, b, name_a=None, name_b=None):
    astr = json.dumps(a, indent=2)
    bstr = json.dumps(b, indent=2)
    return "".join(
        difflib.unified_diff(
            [x + "\n" for x in astr.split("\n")],
            [x + "\n" for x in bstr.split("\n")],
            fromfile=name_a,
            tofile=name_b,
        )
    )


def get_version_info(raw_data):
    raw_data_sorted = _sort_data(raw_data)
    previous = None
    previous_fn = None
    previous_mi = None
    changes = {}
    mi_changes = {}
    for bs, filename in raw_data_sorted:
        m_i = _filtered_machine_info(bs['machine_info'])
        if previous is None:
            # this is the first benchmark run we are looking at, so nothing to
            # compare here:
            previous = bs
            previous_mi = m_i
            previous_fn = filename
            continue
        this_set = _version_set(bs['machine_info']['freeze'])
        prev_set = _version_set(previous['machine_info']['freeze'])
        if this_set != prev_set:
            # something changed, note down what:
            changes[(previous_fn, filename)] = {
                'minus': list(sorted(prev_set - this_set, key=lambda v: v[0])),
                'plus': list(sorted(this_set - prev_set, key=lambda v: v[0])),
            }

        if m_i != previous_mi:
            # machine info changed, make a diff:
            mi_changes[(previous_fn, filename)] = {
                'old_mi': previous_mi,
                'new_mi': m_i,
                'diff': _json_diff(previous_mi, m_i, name_a=previous_fn, name_b=filename),
            }

        previous = bs
        previous_fn = filename
        previous_mi = m_i
    return changes, mi_changes


def load_data():
    dataframes = []
    filenames = []
    raw_data = []
    fn_to_commit = {}
    for i in range(6):
        fn = f"{i + 1:05d}.json"
        r = requests.get(
            f"https://raw.githubusercontent.com/LiberTEM/benchmarks/refs/"
            f"heads/main/collected/LiberTEM/LiberTEM/cpu/{fn}"
        )
        raw_json = r.json()
        raw_data.append((raw_json, fn))
        df_this = to_dataframe(raw_json, fn)
        filenames.append(fn)
        fn_to_commit[fn] = raw_json['commit_info']['id']
        dataframes.append(df_this)

    df = pd.concat(dataframes, ignore_index=True)
    # use this as y axis to "dodge" individual runs:
    df["y_factor"] = list(zip(df['name'], df['run']))

    version_info, machine_info_diff = get_version_info(raw_data)

    return df, version_info, machine_info_diff, filenames, fn_to_commit

df, version_info, machine_info_diff, filenames, fn_to_commit = load_data()

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
    ('Time', '@raw_time{0.000000}'),
    ('Commit', '@commit'),
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
    color=factor_cmap(
        field_name='run_short',
        palette=bp.Category20[len(filenames)],
        factors=filenames
    ),
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


def _format_version_info(version_info):
    parts = ["# Version changes summary"]
    for (old_fn, new_fn), changes in version_info.items():
        parts.append(f"## {old_fn} → {new_fn}")
        old = ["```diff"] + [f"- {name}@({version})" for (name, version) in changes['minus']] + []
        new = [] + [f"+ {name}@({version})" for (name, version) in changes['plus']] + ["```"]
        parts.append("\n".join(old))
        parts.append("\n".join(new))
    return "\n".join(parts)



def _format_machine_diff(machine_info_diff):
    parts = ["# Machine differences summary"]
    for (old_fn, new_fn), changes in machine_info_diff.items():
        parts.append(f"## {old_fn} → {new_fn}")
        diff = ["```diff"] + [changes['diff']] + ["```"]
        parts.append("\n".join(diff))
    return "\n".join(parts)


version_info_md = pn.pane.Markdown(object=_format_version_info(version_info))
machine_info_md = pn.pane.Markdown(object=_format_machine_diff(machine_info_diff))

app = pn.Column(
    select_test,
    bokeh_plot,
    version_info_md,
    machine_info_md,
).servable()

# app.save('test.html', resources=INLINE)
