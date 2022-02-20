#!/usr/bin/env python
# coding: utf-8

# In[1]:


import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import plotly.express as px
import plotly.graph_objects as go

from jupyter_dash import JupyterDash
from dash import dcc
from dash import html
from dash.dependencies import Input, Output
from dash import html

from dash import dash_table
from dash import html

# def generate_table(dataframe, max_rows=10):
#     return html.Table([
#         html.Thead(
#             html.Tr([html.Th(col) for col in dataframe.columns])
#         ),
#         html.Tbody([
#             html.Tr([
#                 html.Td(dataframe.iloc[i][col]) for col in dataframe.columns
#             ]) for i in range(min(len(dataframe), max_rows))
#         ])
#     ])


app = JupyterDash(__name__)
server = app.server

app.layout = html.Div([
    html.H1("Impermanent Loss Calculator"),
    html.H5('Start Price', style={'display':'inline-block','margin-right':20}),
    dcc.Input(id='start_price', type='number', value=100, placeholder=100,style={'display':'inline-block'}),
    dcc.Checklist(
        id="hedges",
        options=[
            {'label': 'Power Perp Hedge', 'value': "pp"},
            {'label': 'Delta Hedge LP', 'value': "dlp"},
            {'label': 'Delta Hedge Power Perp', 'value': "dpp"},
        ],
        value=["pp", "dlp", "dpp"],
        labelStyle={'display': 'inline-block', 'margin-right':50,},
    ),
    html.H5('Power Perp Funding Daily Pct', style={'display':'inline-block','margin-top':5,'margin-bottom':5}),
    dcc.Slider(
        min=0, 
        max=3,
        marks={str(i): str(i) for i in np.arange(0, 3, 1)},
        id = 'pp_funding',
        step=0.01,
        value=0,
        tooltip={"placement": "bottom", "always_visible": True},
    ),    
    html.H5('Delta Hedge Funding Daily Pct', style={'display':'inline-block','margin-top':5,'margin-bottom':5}),
    dcc.Slider(
        min=0, 
        max=0.75,
        marks={str(i): str(i) for i in np.arange(0, 0.75, .1)},
        id = 'delta_funding',
        step=0.01,
        value=0,
        tooltip={"placement": "bottom", "always_visible": True},
    ),    
    html.H5('Liquidity Pool Rewards APR', style={'display':'inline-block','margin-top':5,'margin-bottom':5}),
    dcc.Slider(
        min=0, 
        max=5,
        marks={str(i): str(i) for i in np.arange(0, 3, 1)},
        id = 'lp_apr',
        step=0.01,
        value=0.30,
        tooltip={"placement": "bottom", "always_visible": True},
    ),
    html.H5('Days Farmed', style={'display':'inline-block','margin-top':5,'margin-bottom':5}),
    dcc.Slider(
        min=0, 
        max=365,
        marks={str(i): str(i) for i in np.arange(0, 365, 30)},
        id = 'days',
        step=1,
        value=0,
        tooltip={"placement": "bottom", "always_visible": True},
    ),
    dash_table.DataTable(
        id="yield_table",
        columns=["LP Yield", "Power Perp Funding", "Delta Hedge Funding", "Final APR"],
        style_data={
            'whiteSpace': 'normal',
            'height': 'auto'
        },
        page_action="none"
    ),
    dcc.Graph(id='graph2'),
],    style={'margin-left': 150, 'margin-right': 150},
)

@app.callback(
    Output('graph2', 'figure'),
    [
        Input("start_price", "value"),
        Input("pp_funding", "value"),
        Input("delta_funding", "value"),
        Input("lp_apr", "value"),
        Input("days", "value"),
        Input("hedges", "value"),
    ]
)
def update_figure2(start_price, pp_funding, delta_funding, lp_apr, days, checklist):#, power_perp_funding, spot_funding):
    df = pd.DataFrame()

    new_price =  np.arange(0, start_price*2)
    power_perp_sizing = 1/(4*start_price)
    ret = new_price/start_price-1
    il = 2*start_price*(np.sqrt(ret+1) - 1 - 0.5*(ret))
    lp = start_price+new_price+il
    power_perp_pnl = (new_price**2-start_price**2)*power_perp_sizing
    delta = (start_price-new_price)
    op = 2*start_price
    
    power_perp_funding_pnl = -pp_funding/100*days*start_price**2*power_perp_sizing
    delta_funding_pnl = -delta_funding/100*days*start_price


    new_lp = lp * (1+lp_apr/365)**days
    
    df["Spot Pair"] = ((start_price + new_price)/op-1)*100
    df["LP Position"] = (new_lp/op-1)*100
    # Janky and stupid I know
    if 'pp' in checklist and not 'dlp' in checklist and not 'dpp' in checklist:
        df["final_position"] = new_lp + power_perp_pnl + power_perp_funding_pnl
    if 'pp' in checklist and 'dlp' in checklist and 'dpp' not in checklist:
        df["final_position"] = new_lp + power_perp_pnl + 0.5*delta + power_perp_funding_pnl + 0.5*delta_funding_pnl
    if 'pp' in checklist and 'dlp' in checklist and 'dpp' in checklist:
        df["final_position"] = new_lp + power_perp_pnl + 1.5*delta + power_perp_funding_pnl + 1.5*delta_funding_pnl
    if 'dlp' in checklist and not 'pp' in checklist:
        df["final_position"] = new_lp + delta + delta_funding_pnl

    df["final_position"] = (df.final_position/op-1)*100
        
    fig = px.line(df)
    
    return fig.update_layout(
        title="Token1 vs. USDC",
        xaxis_title="Final Price",
        yaxis_title="PNL per 1 LP Position",
    )

# @app.callback(
#     Output('yield_table', 'style_data_conditional'),
#     [
#         Input("start_price", "value"),
#         Input("pp_funding", "value"),
#         Input("delta_funding", "value"),
#         Input("lp_apr", "value"),
#         Input("hedges", "value"),
#     ]
# )
# def update_table(start_price, pp_funding, delta_funding, lp_apr, checklist):
#     return [
#         {
#             "LP Yield": 0.1, 
#             "Power Perp Funding": 0.1, 
#             "Delta Hedge Funding": 0.1, 
#             "Final APR": 0.1
#         }
#     ]

if __name__ == "__main__":
    app.run_server()


# In[ ]:




