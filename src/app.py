# -*- coding: utf-8 -*-
# Import required libraries
from distutils.log import debug
import pandas as pd
import numpy as np
import dash
import pathlib
from dash.dependencies import Input, Output, State
from dash import dcc, html, callback_context
import plotly.graph_objs as go
from utils import scan_dynamodb
from datetime import datetime


# Setup the app
app = dash.Dash(
    __name__, meta_tags=[{"name": "viewport", "content": "width=device-width"}]
)
app.title = "Implied Volatility of MINI IBEX"
server = app.server

# get relative data folder
PATH = pathlib.Path(__file__).parent

count, items = scan_dynamodb('MINI_IBEX_VOL')

all_options = {}

for i in items:
    all_options[i['DATE']] = pd.Series(list(set([dat['expiration_date']for dat in i['DATA']]))).sort_values().values.tolist()

first_date = list(all_options.keys())[-1]


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
                            """MIAX8 - Cloud Technologies - [Antonio Bernal](https://www.linkedin.com/in/bernal-antonio/)""".replace(
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
                    html.Label(['Date']),
                    dcc.Dropdown(
                        options=[{'label': k, 'value': k} for k in all_options.keys()],
                        value=first_date,
                        clearable=False,
                        id='date-dropdown'
                        ),
                    html.Div(id='date-output-container')
                    ],
                    className="date-dropdown",
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
                    html.Label(['Expiration Date']),
                    dcc.Dropdown(clearable=False,
                    id='exp-date-dropdown'
                    ),
                    html.Div(id='exp_date-output-container')
                    ],
                    className="date-dropdown",
                ),
            ],
            className="four columns sidebar",
        ),
        html.Div(
            [
                html.Div([dcc.Markdown(id="text")], className="text-box"),
                dcc.Graph(id="graph",
                style={"margin": "0px 20px", "height": "45vh"}
                ),
            ],
            id="page",
            className="eight columns",
        ),
    ],
    className="row flex-display",
    style={"height": "100vh"},
)


@app.callback(
    Output('exp-date-dropdown', 'options'),
    Input('date-dropdown', 'value'))
def set_exp_date_options(selected_index):
    return [{'label': i, 'value': i} for i in all_options[selected_index]]


@app.callback(
    Output('exp-date-dropdown', 'value'),
    Input('exp-date-dropdown', 'options'))
def set_exp_date_value(available_options):
    return available_options[0]['value']


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
    Input("exp-date-dropdown", "value"),
    State("date-dropdown", "value"),
    Input("intermediate-value", "data")
)
def make_graph(exp_date, date, data):
    call_put = data['call_put']
    call_put_label = data['call_put_label']

    df_option = [i['DATA'] for i in items if i['DATE'] == date][0]
    df_option = pd.DataFrame(df_option)

    df_option.implied_volatility = df_option.implied_volatility.apply(lambda x: float(x))
    df_option.strike = df_option.strike.apply(lambda x: float(x))
    df_option.price = df_option.price.apply(lambda x: float(x))
    df_option.expiration_date = df_option.expiration_date.apply(lambda x: datetime.strptime(x, '%Y-%m-%d'))
    df_option.index = df_option.expiration_date.values
    
    strikes = df_option[df_option.call_put == call_put][exp_date:exp_date].loc[:, 'strike'].values
    imp_probs = df_option[df_option.call_put == call_put][exp_date:exp_date].loc[:, 'implied_volatility'].values

    layout = go.Layout(
        title=f"Volatility Skew {exp_date} ({call_put_label}) - {date}",
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