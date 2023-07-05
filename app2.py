import dash
from dash import Dash, html, dcc
import dash_bootstrap_components as dbc

app = dash.Dash(__name__, use_pages=True)

app.layout = dbc.Container(
    children=[
        dbc.Row(
            [
                dbc.Col(html.H1(children=["Tweet Performance Dashboard"]), width=8),
                dbc.Col(html.Img(src="./assets/CBI_Logo_24b.png"), width=1),
            ],
            justify="start",
        ),
        html.Div(
            [
                dcc.Link(page["name"] + "  |  ", href=page["path"])
                for page in dash.page_registry.values()
            ]
        ),
        html.Hr(),
        # content of each page
        dash.page_container,
    ]
)

if __name__ == "__main__":
    app.run(debug=True)
