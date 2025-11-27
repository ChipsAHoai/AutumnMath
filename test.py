from nicegui import ui
import plotly.express as px
import pandas as pd
import numpy as np

# ---------------------------------------------------------
# Generate example 96-sample dataset (A1–H12 layout)
# ---------------------------------------------------------
rows = list("ABCDEFGH")
cols = list(range(1, 13))
data = [
    {
        'Row': r,
        'Col': c,
        'Sample': f'{r}{c}',
        'Concentration': np.random.normal(50, 10),  # ng/µL
    }
    for r in rows for c in cols
]
df = pd.DataFrame(data)


# ---------------------------------------------------------
# Create a refreshable plot component
# ---------------------------------------------------------
@ui.refreshable
def show_plot(view_type: str):
    print("REFHRESHING PLOT")
    if view_type == 'Heatmap':
        pivot = df.pivot(index='Row', columns='Col', values='Concentration')
        fig = px.imshow(
            pivot,
            color_continuous_scale='RdYlBu_r',
            labels={'color': 'Concentration (ng/µL)'},
            title='Plate Heatmap (A1–H12)',
        )

    elif view_type == 'Histogram':
        fig = px.histogram(
            df,
            x='Concentration',
            nbins=20,
            title='Concentration Distribution',
            labels={'Concentration': 'ng/µL'},
        )

    elif view_type == 'Boxplot':
        fig = px.box(
            df,
            x='Row',
            y='Concentration',
            title='Concentration by Row',
            labels={'Row': 'Row', 'Concentration': 'ng/µL'},
        )

    elif view_type == 'Scatter':
        df_sorted = df.sort_values(['Row', 'Col'])
        fig = px.scatter(
            df_sorted,
            x='Col',
            y='Concentration',
            color='Row',
            hover_name='Sample',
            title='Scatter by Column',
            labels={'Col': 'Column', 'Concentration': 'ng/µL'},
        )
    elif view_type == 'Scatter by Row':
        df_sorted = df.sort_values(['Row', 'Col'])
        fig = px.scatter(
            df_sorted,
            x='Row',
            y='Concentration',
            color='Col',
            hover_name='Sample',
            title='Scatter by Row',
            labels={'Row': 'Row', 'Concentration': 'ng/µL'},
        )
    else:
        return

    fig.update_layout(margin=dict(l=40, r=40, t=60, b=40))
    ui.plotly(fig).classes('w-full h-[600px]')


# ---------------------------------------------------------
# Page definition
# ---------------------------------------------------------
@ui.page('/')
def page():
    ui.label('96-Sample Library Prep Concentrations').classes('text-2xl font-bold mb-4')

    view_select = ui.select(
        options=['Heatmap', 'Histogram', 'Boxplot', 'Scatter', 'Scatter by Row'],
        value='Boxplot',
        label='Select View',
    )

    # Dynamic plot region
    show_plot(view_select.value)

    # Refresh the plot when selection changes
    view_select.on_value_change(
        lambda e: show_plot.refresh(e.value),  # built-in helper ensures latest value
    )

ui.run()
