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
from utils import scan_dynamodb, unixTimeMillis, unixToDatetime
from datetime import datetime
from scipy.interpolate import griddata


# Setup the app
app = dash.Dash(
    __name__, meta_tags=[{"name": "viewport", "content": "width=device-width"}]
)
app.title = "Implied Volatility of MINI IBEX"
server = app.server

# get relative data folder
PATH = pathlib.Path(__file__).parent

COLORS = ['#cde11d', '#5ec962', '#21918c', '#3b528b', '#440154']

count, items = scan_dynamodb('MINI_IBEX_VOL')

items = sorted(items, key=lambda d: d['DATE'])

all_options = {}

for i in items:
    all_options[i['DATE']] = pd.Series(list(set([dat['expiration_date']for dat in i['DATA']]))).sort_values().values.tolist()

first_date = list(all_options.keys())[-1]

MAX_DATES_MULTI_DROPDOWN = 5

MAX_ROWS_SLIDER = 10

date_list_slider = list(all_options.keys())[-MAX_ROWS_SLIDER:]

first_last_dls = [date_list_slider[0], date_list_slider[-1]]

slider_marks = {unixTimeMillis(i): {'label':i} if i in first_last_dls else {'label':i, "style": {"display": "none"}} for i in date_list_slider}


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

                html.Div([
                    dcc.Tabs(id="tabs", value='Skew', children=[
                        dcc.Tab(label='Skew', value='Skew', children=[


                            html.Div([
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


                        ]),
                        dcc.Tab(label='Skew Comparison', value='Skew Comparison', children=[

                            
                            html.Div([
                                html.Label(['Date']),
                                dcc.Dropdown(
                                    options=[{'label': k, 'value': k} for k in list(all_options.keys())],
                                    value=list(all_options.keys())[-MAX_DATES_MULTI_DROPDOWN:],
                                    multi=True,
                                    clearable=False,
                                    id='date-dropdown-2'
                                    ),
                                html.Div(id='warning')
                                ],
                                className="date-dropdown-2",
                            ),
                            html.Div(
                                [
                                    html.Button(
                                        "CALL",
                                        id="call-2",
                                        style={"display": "inline-block"},
                                        n_clicks=0,
                                    ),
                                    html.Button(
                                        "PUT",
                                        id="put-2",
                                        style={"display": "inline-block", "marginLeft": "10px"},
                                        n_clicks=0,
                                    ),
                                    dcc.Store(id='intermediate-value-2'),
                                ],
                                className="page-buttons",
                            ),
                            html.Div(
                                [
                                html.Label(['Expiration Date']),
                                dcc.Dropdown(clearable=False,
                                id='exp-date-dropdown-2'
                                ),
                                html.Div(id='exp_date-output-container-2')
                                ],
                                className="date-dropdown",
                            ),


        ]),
        dcc.Tab(label='Skew Surface', value = 'Skew Surface', children=[
            html.Div([
                html.Label(['Date']),
                dcc.Slider(list(slider_marks.keys())[0], list(slider_marks.keys())[-1],
                    step=None,
                    marks=slider_marks,
                    value=list(slider_marks.keys())[-1],
                    id='slider'
                )
            ],
            className="date-slider",),
            html.Div(
                [
                    html.Button(
                        "CALL",
                        id="call-3",
                        style={"display": "inline-block"},
                        n_clicks=0,
                    ),
                    html.Button(
                        "PUT",
                        id="put-3",
                        style={"display": "inline-block", "marginLeft": "10px"},
                        n_clicks=0,
                    ),
                    dcc.Store(id='intermediate-value-3'),
                ],
                className="page-buttons",
            ),
        ]),
    ])
])


            ],
            className="four columns sidebar",
        ),
        html.Div(
            [
                dcc.Graph(id="graph",
                style={"margin": "4% 4%", "height": "90%", "width": "90%"}
                ),
            ],
            id="page",
            className="eight columns",
        ),
    ],
    className="row flex-display",
    style={"height": "100vh"},
)


# TAB 1 FUNCTIONS

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



# TAB 2 FUNCTIONS

@app.callback(
    Output('date-dropdown-2', 'options'),
    Output('warning', 'children'),
    Input('date-dropdown-2', 'value'))
def update_multi_options(selected_index):
    options = [{'label': k, 'value': k} for k in list(all_options.keys())]
    input_warning = None

    if len(selected_index) >= MAX_DATES_MULTI_DROPDOWN:
        input_warning = html.P(id="warning", children=f"Limit of {MAX_DATES_MULTI_DROPDOWN} reached", style={"color": "red"})
        options = [{"label": option["label"], "value": option["value"], "disabled": True} for option in options]

    return options, input_warning


@app.callback(
    Output('exp-date-dropdown-2', 'options'),
    Input('date-dropdown-2', 'value'))
def set_exp_date_options_2(selected_index):
    if type(selected_index) == 'str':
        return [{'label': i, 'value': i} for i in all_options[selected_index]]
    else:
        aux = pd.Series(list(set([i for ind in selected_index for i in all_options[ind]]))).sort_values().values.tolist()
        return [{'label': i, 'value': i} for i in aux]


@app.callback(
    Output('exp-date-dropdown-2', 'value'),
    Input('exp-date-dropdown-2', 'options'))
def set_exp_date_value_2(available_options):
    return available_options[0]['value']


@app.callback(
    Output("intermediate-value-2", "data"),
    Input("call-2", "n_clicks"),
    Input("put-2", "n_clicks")
)
def get_last_button_2(btn_call, btn_put):
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


# TAB 3 FUNCTIONS

@app.callback(
    Output("intermediate-value-3", "data"),
    Input("call-3", "n_clicks"),
    Input("put-3", "n_clicks")
)
def get_last_button_3(btn_call, btn_put):
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



# GRAPH
@app.callback(
    Output("graph", "figure"),
    Input('tabs', 'value'),
    Input("exp-date-dropdown", "value"),
    State("date-dropdown", "value"),
    Input("intermediate-value", "data"),
    Input("exp-date-dropdown-2", "value"),
    State("date-dropdown-2", "value"),
    Input("intermediate-value-2", "data"),
    Input('slider', 'value'),
    Input("intermediate-value-3", "data")
)
def make_graph(tab, exp_date, date, data, exp_date2, date2, data2, date3, data3):
    if tab == 'Skew':
        exp_date_main = exp_date
        date_main = date
        data_main = data

        call_put = data_main['call_put']
        call_put_label = data_main['call_put_label']

        layout = go.Layout(
            title=f"Volatility Skew {exp_date_main} ({call_put_label}) - {date_main}",
            plot_bgcolor="#FFF",  # Sets background color to white
            hovermode="x",
            hoverdistance=100, # Distance to show hover label of data point
            spikedistance=1000, # Distance to show spike 
            xaxis=dict(
                title="Strike",
                linecolor="#BCCCDC",  # Sets color of X-axis line
                showgrid=False,  # Removes X-axis grid lines
                showspikes=True, # Show spike line for X-axis
                # Format spike
                spikethickness=2,
                spikedash="dot",
                spikecolor="#999999",
                spikemode="across",
            ),
            yaxis=dict(
                title="Implied Volatility",  
                linecolor="#BCCCDC",  # Sets color of Y-axis line
                showgrid=False,  # Removes Y-axis grid lines    
            )
        )
    
    elif tab == 'Skew Comparison':
        exp_date_main = exp_date2
        date_main = date2
        data_main = data2

        call_put = data_main['call_put']
        call_put_label = data_main['call_put_label']

        layout = go.Layout(
            title=f"Volatility Skew Comparison {exp_date_main} ({call_put_label})",
            plot_bgcolor="#FFF", # Sets background color to white
            hovermode="x",
            hoverdistance=100, # Distance to show hover label of data point
            spikedistance=1000, # Distance to show spike 
            xaxis=dict(
                title="Strike",
                linecolor="#BCCCDC",  # Sets color of X-axis line
                showgrid=False,  # Removes X-axis grid lines
                showspikes=True, # Show spike line for X-axis
                # Format spike
                spikethickness=2,
                spikedash="dot",
                spikecolor="#999999",
                spikemode="across",
            ),
            yaxis=dict(
                title="Implied Volatility",  
                linecolor="#BCCCDC",  # Sets color of Y-axis line
                showgrid=False,  # Removes Y-axis grid lines    
            )
        )
    
    elif tab == 'Skew Surface':
        date_main = unixToDatetime(date3)
        data_main = data3

        call_put = data_main['call_put']
        call_put_label = data_main['call_put_label']

        layout = go.Layout(
            title=f"Volatility Skew Surface ({call_put_label}) - {date_main}",
            plot_bgcolor="#FFF", # Sets background color to white
            scene = dict(
                xaxis = dict(
                    title="Strike",  
                    linecolor="#BCCCDC",  # Sets color of X-axis line
                    showgrid=False,
                    showbackground=False,
                    ),
                yaxis = dict(
                    title="Time to Maturity (Days)",  
                    linecolor="#BCCCDC",  # Sets color of Y-axis line
                    showgrid=False,
                    showbackground=False,
                    ),
                zaxis = dict(
                    title="Implied Volatility",  
                    linecolor="#BCCCDC",  # Sets color of Z-axis line
                    showgrid=False,
                    showbackground=False,
                    ),
            ),
            autosize=True,
            # width=1000,
            # height=1000,
            margin=dict(l=65, r=50, b=65, t=90)
        )


    fig = go.Figure()

    if not isinstance(date_main, list):
        date_main = [date_main]

    i_color = 0

    for date in date_main:
        
        df_option = [i['DATA'] for i in items if i['DATE'] == date][0]
        
        df_option = pd.DataFrame(df_option)

        df_option.implied_volatility = df_option.implied_volatility.apply(lambda x: float(x))
        df_option.strike = df_option.strike.apply(lambda x: float(x))
        df_option.price = df_option.price.apply(lambda x: float(x))
        df_option.expiration_date = df_option.expiration_date.apply(lambda x: datetime.strptime(x, '%Y-%m-%d'))
        df_option.index = df_option.expiration_date.values
        
        if tab != 'Skew Surface':
            strikes = df_option[df_option.call_put == call_put][exp_date_main:exp_date_main].loc[:, 'strike'].values
            imp_probs = df_option[df_option.call_put == call_put][exp_date_main:exp_date_main].loc[:, 'implied_volatility'].values

            if tab == 'Skew':
                i_color = 2

            fig.add_trace(go.Scatter(
                x=strikes,
                y=imp_probs,
                name=date,
                line=dict(
                    color=COLORS[i_color],
                    width=2
                )
            ))

            i_color += 1
        
        else:
            strikes = df_option[df_option.call_put == call_put].loc[:, 'strike'].values
            imp_probs = df_option[df_option.call_put == call_put].loc[:, 'implied_volatility'].values

            df_option['today'] = datetime.today()
            df_option['delta_days'] = (df_option.expiration_date - df_option.today).dt.days
            delta_days = df_option[df_option.call_put == call_put].loc[:, 'delta_days']

            x = strikes
            y = delta_days
            z = imp_probs

            xi = np.linspace(x.min(), x.max(), 100)
            yi = np.linspace(y.min(), y.max(), 100)

            X,Y = np.meshgrid(xi,yi)

            Z = griddata((x,y),z,(X,Y), method='cubic')

            fig.add_trace(go.Surface(x=X, y=Y, z=Z, colorscale='Viridis'))


    fig.update_layout(layout)

    if tab != 'Skew Surface':
        fig.update_traces(mode="markers+lines")


    return fig


# Run the Dash app
if __name__ == "__main__":
    app.run_server(host="0.0.0.0", debug=False, port=8080)