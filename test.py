import dash
import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output, State

# Create the Dash app
app = dash.Dash(__name__)

# Define the layout
app.layout = html.Div(
    [
        dcc.Dropdown(
            id="dropdown",
            options=[
                {"label": "Option 1", "value": "option1"},
                {"label": "Option 2", "value": "option2"},
                {"label": "Option 3", "value": "option3"},
            ],
            value="option1",  # Default selected value
        ),
        html.Div(id="text-box-container"),  # Placeholder for the text box
        html.Div(id="output-container"),  # Placeholder for the output
    ]
)


@app.callback(Output("text-box-container", "children"), [Input("dropdown", "value")])
def update_text_box(selected_value):
    if selected_value == "option1":
        return dcc.Input(
            id="text-box",
            type="text",
            value="",
            placeholder="Enter text for Option 1...",
        )
    elif selected_value == "option2":
        return dcc.Input(
            id="text-box",
            type="text",
            value="",
            placeholder="Enter text for Option 2...",
        )
    elif selected_value == "option3":
        return dcc.Input(
            id="text-box",
            type="text",
            value="",
            placeholder="Enter text for Option 3...",
        )
    else:
        return None


@app.callback(
    Output("output-container", "children"),
    [Input("text-box", "value")],
    prevent_initial_call=True,
)
def display_input_text(value):
    return f"Input: {value}"


if __name__ == "__main__":
    app.run_server(debug=True)
