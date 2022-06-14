# -*- coding: utf-8 -*-
# Import required libraries
import pandas as pd
import numpy as np
import dash
import pathlib
from dash.dependencies import Input, Output, State
from dash import dcc, html, callback_context
import plotly.graph_objs as go
from utils import get_data, implied_volatility


# Setup the app
app = dash.Dash(
    __name__, meta_tags=[{"name": "viewport", "content": "width=device-width"}]
)
app.title = "Implied Volatility of MINI IBEX"
server = app.server

# get relative data folder
PATH = pathlib.Path(__file__).parent

df_future, df_option = get_data()

first_date = str(df_option.sort_index().index[0])[:10]

df_option['implied_volatility'] = df_option.apply(lambda row: implied_volatility(df_option=row, future_price=df_future.iloc[0]), axis=1)

timestamp_list = df_option.index.unique().to_list()
timestamp_list = [str(i)[:10] for i in timestamp_list]

app.layout = html.Div(
    [
        dcc.Store(id="click-output"),
        html.Div(
            [
                html.Div(
                    [
                        dcc.Markdown(
                            """
                ### Implied Volatility of MINI IBEX Options
                """.replace(
                                "  ", ""
                            ),
                            className="title",
                        ),
                        dcc.Markdown(
                            """MIAX8 - Cloud Technologies""".replace(
                                "  ", ""
                            ),
                            className="subtitle",
                        ),
                    ]
                ),
                html.Div(
                    [
                        html.A(
                            html.Button("GITHUB", className="learn-more-button"),
                            href="https://github.com/Tonarro/practica-tecnologias-cloud-miax",
                            target="_blank",
                        )
                    ],
                    className="info-button",
                ),
                html.Div(
                    [
                        html.Button(
                            "CALL",
                            id="call",
                            style={"display": "inline-block"},
                            n_clicks=0,
                        ),
                        html.Button(
                            "PUT",
                            id="put",
                            style={"display": "inline-block", "marginLeft": "10px"},
                            n_clicks=0,
                        ),
                        dcc.Store(id='intermediate-value'),
                    ],
                    className="page-buttons",
                ),
                html.Div(
                    [
                    dcc.Dropdown(timestamp_list, value=first_date, clearable=False, id='date-dropdown'),
                    html.Div(id='date-output-container')
                    ],
                    className="date-dropdown",
                ),
            ],
            className="four columns sidebar",
        ),
        html.Div(
            [
                html.Div([dcc.Markdown(id="text")], className="text-box"),
                dcc.Graph(id="graph", style={"margin": "0px 20px", "height": "45vh"}),
            ],
            id="page",
            className="eight columns",
        ),
    ],
    className="row flex-display",
    style={"height": "100vh"},
)


@app.callback(
    Output("intermediate-value", "data"),
    Input("call", "n_clicks"),
    Input("put", "n_clicks")
)
def get_last_button(btn_call, btn_put):
    changed_id = [p['prop_id'] for p in callback_context.triggered][0]

    if 'call' in changed_id:
        call_put = 'C'
        call_put_label = 'Call'
    elif 'put' in changed_id:
        call_put = 'P'
        call_put_label = 'Put'
    else:
        call_put = 'C'
        call_put_label = 'Call'

    return {'call_put': call_put, 'call_put_label': call_put_label}


# Make graph
@app.callback(
    Output("graph", "figure"),
    Input("date-dropdown", "value"),
    Input("intermediate-value", "data")
)
def make_graph(date, data):
    call_put = data['call_put']
    call_put_label = data['call_put_label']
    
    strikes = df_option[df_option.call_put == call_put][date:date].loc[:, 'strike'].values
    imp_probs = df_option[df_option.call_put == call_put][date:date].loc[:, 'implied_volatility'].values

    layout = go.Layout(
        title=f"Volatility Skew {date} ({call_put_label})",
        plot_bgcolor="#FFF",  # Sets background color to white
        xaxis=dict(
            title="Strike",
            linecolor="#BCCCDC",  # Sets color of X-axis line
            showgrid=False  # Removes X-axis grid lines
        ),
        yaxis=dict(
            title="Implied Volatility",  
            linecolor="#BCCCDC",  # Sets color of Y-axis line
            showgrid=False,  # Removes Y-axis grid lines    
        )
    )

    fig = go.Figure(data=[go.Scatter(x=strikes, y=imp_probs)], layout=layout)

    # fig.update_layout(transition_duration=50)

    return fig


# Run the Dash app
if __name__ == "__main__":
    app.run_server(host="0.0.0.0", debug=False, port=8080)