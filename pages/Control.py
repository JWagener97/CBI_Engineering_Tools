import dash
from dash import dcc, html, dash_table
import dash_bootstrap_components as dbc
import pandas as pd


dash.register_page(__name__, path="/")

# Page 1 data
df = pd.read_csv(r"./Data/GUI.csv")

layout = dbc.Container(
    [
        dbc.Label("Click a cell in the table:"),
        dash_table.DataTable(
            df.to_dict("records"), [{"name": i, "id": i} for i in df.columns], id="tbl"
        ),
        dbc.Alert(id="tbl_out"),
    ]
)
