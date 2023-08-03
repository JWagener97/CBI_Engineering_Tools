import json
import paho.mqtt.client as mqtt
import time
import pandas as pd

from dash import Dash, dash_table, dcc, html, Input, Output, ctx, State
from dash import callback_context
import dash_bootstrap_components as dbc

Status_df = pd.DataFrame()
Eng_df = pd.DataFrame()
Tel_df = pd.DataFrame()

# MQTT broker settings
global broker_address
global broker_port
global username
global password


broker_address = "10.0.0.45"
broker_port = 1883
topic = "#"

# MQTT broker credentials

username = "sem-rabbitmq"
password = "sem-rabbitmq123"

global mqtt_message
mqtt_message = "NaN"
global mqtt_status
mqtt_status = "MQTT Broker not configured "


# MQTT client callbacks
def on_connect(client, userdata, flags, rc):
    global mqtt_status
    mqtt_status = "Connected to MQTT broker"
    print(mqtt_status)
    client.subscribe(topic)


# MQTT client setup
def on_message(client, userdata, msg):
    global mqtt_message
    mqtt_message = json.loads(msg.payload.decode())
    data_frame_update(mqtt_message)


def on_disconnect(client, userdata, rc):
    global mqtt_status
    mqtt_status = "Disconnected from MQTT broker"
    print(mqtt_status)


# Create MQTT client instance
client = mqtt.Client()

# Set username and password for MQTT broker authentication
client.username_pw_set(username, password)

# Assign callbacks
client.on_connect = on_connect
client.on_message = on_message
client.on_disconnect = on_disconnect

# Connect to MQTT broker
# client.connect(broker_address, broker_port)

# Start MQTT loop
# client.loop_start()


def data_frame_update(msg):
    global Tel_df
    global Status_df
    global Eng_df

    try:
        mess_type = str(msg["TypeId"])
        new_entry = pd.DataFrame([msg])
        match mess_type:
            case "7":  # Status datapacket
                try:
                    new_entry["DevId"] = (
                        new_entry["DevId"].astype(str)
                        + "_"
                        + new_entry["PolePosition"].astype(str)
                    )
                    new_entry.drop(columns=["PolePosition"], inplace=True)
                except:
                    pass
                if len(Status_df) == 0:
                    Status_df = pd.concat([Status_df, new_entry], axis=0)
                else:
                    try:
                        match = not Status_df.merge(new_entry, on="DevId").empty
                        if match == True:
                            filt = Status_df["DevId"] == new_entry.iloc[0]["DevId"]
                            Status_df.loc[filt, Status_df.columns] = new_entry
                        else:
                            Status_df = pd.concat([Status_df, new_entry], axis=0)
                    except:
                        pass
                    try:
                        DevID = Status_df["DevId"]
                        Status_df = Status_df.drop(columns=["DevId"])
                        Status_df.insert(loc=2, column="DevId", value=DevID)
                        Status_df.drop(columns=["TypeId"], inplace=True)
                    except:
                        pass
            case "3":  # Telemtry datapacket
                try:
                    new_entry["DevId"] = (
                        new_entry["DevId"].astype(str)
                        + "_"
                        + new_entry["PolePosition"].astype(str)
                    )
                    new_entry.drop(columns=["PolePosition"], inplace=True)

                except:
                    pass
                if len(Tel_df) == 0:
                    Tel_df = pd.concat([Tel_df, new_entry], axis=0)
                else:
                    try:
                        match = not Tel_df.merge(new_entry, on="DevId").empty
                        if match == True:
                            filt = Tel_df["DevId"] == new_entry.iloc[0]["DevId"]
                            Tel_df.loc[filt, Tel_df.columns] = new_entry
                        else:
                            Tel_df = pd.concat([Tel_df, new_entry], axis=0)
                    except:
                        pass
                try:
                    DevID = Tel_df["DevId"]
                    Tel_df = Tel_df.drop(columns=["DevId"])
                    Tel_df.insert(loc=2, column="DevId", value=DevID)
                    Tel_df.drop(columns=["TypeId"], inplace=True)
                except:
                    pass
            case _:
                pass
    except:
        pass


app = Dash(__name__, external_stylesheets=[dbc.themes.DARKLY])
app.layout = html.Div(
    children=[
        # Input boxes in a horizontal row
        html.Div(
            children=[
                html.Div(
                    [
                        dcc.Dropdown(
                            [
                                {
                                    "label": html.Span(
                                        ["45"],
                                        style={"color": "white", "font-size": 20},
                                    ),
                                    "value": "45",
                                },
                                {
                                    "label": html.Span(
                                        ["UAT"],
                                        style={"color": "white", "font-size": 20},
                                    ),
                                    "value": "UAT",
                                },
                                {
                                    "label": html.Span(
                                        ["Production"],
                                        style={"color": "white", "font-size": 20},
                                    ),
                                    "value": "Production",
                                },
                                {
                                    "label": html.Span(
                                        ["Custom"],
                                        style={"color": "white", "font-size": 20},
                                    ),
                                    "value": "Custom",
                                },
                            ],
                            value="45",
                            id="Mqtt-dropdown",
                            style={"background-color": "rgb(0, 0, 0)"},
                        ),
                    ],
                    style={
                        "display": "inline-block",
                        "width": "20%",
                    },
                ),
                html.Div(
                    [
                        html.Button(
                            id="btn-nclicks-2",
                            n_clicks=0,
                            style={"fontSize": 25},
                        ),  # Button with custom style
                        html.Div(id="container-button"),
                    ],
                    style={"display": "inline-block", "width": "20%", "margin": "20px"},
                ),
            ],
        ),
        html.Div(id="text-box-container"),  # Placeholder for the text box
        html.Hr(),
        html.Div(
            style={"width": "25%", "display": "inline-block"},
            children=[
                "Message Type",
                dcc.Dropdown(
                    [
                        {
                            "label": html.Span(
                                ["Status"],
                                style={"color": "white", "font-size": 20},
                            ),
                            "value": "Status",
                        },
                        {
                            "label": html.Span(
                                ["Telemetry"],
                                style={"color": "white", "font-size": 20},
                            ),
                            "value": "Telemetry",
                        },
                    ],
                    value="Telemetry",
                    id="table-dropdown",
                    style={"background-color": "rgb(0, 0, 0)"},
                ),
            ],
        ),
        html.Div(
            style={"width": "100%", "display": "inline-block"},
            children=[
                dcc.Interval(id="interval", interval=1000, n_intervals=0),
                dash_table.DataTable(
                    id="table",
                    data=Tel_df.to_dict("records"),
                    style_header={
                        "backgroundColor": "rgb(30, 30, 30)",
                        "color": "white",
                    },
                    style_data={
                        "backgroundColor": "rgb(0, 0, 0)",
                        "color": "white",
                    },
                ),
            ],
        ),
    ]
)


@app.callback(
    Output("text-box-container", "children"), [Input("Mqtt-dropdown", "value")]
)
def update_text_box(selected_value):
    if selected_value == "Custom":
        return (
            html.Div(
                [
                    # Broker address
                    html.Div(
                        [
                            html.Label("Broker Address"),
                            dcc.Input(
                                id="broker-address-input",
                                type="text",
                                placeholder="Enter broker address",
                                value="",
                                style={"width": "100%"},
                            ),
                        ],
                        style={
                            "display": "inline-block",
                            "width": "20%",
                            "margin": "10px",
                        },
                    ),
                    # Broker port
                    html.Div(
                        [
                            html.Label("Broker Port"),
                            dcc.Input(
                                id="broker-port-input",
                                type="text",
                                placeholder="Enter broker port",
                                value="",
                                style={"width": "100%"},
                            ),
                        ],
                        style={
                            "display": "inline-block",
                            "width": "20%",
                            "margin": "10px",
                        },
                    ),
                    # Username
                    html.Div(
                        [
                            html.Label("Username"),
                            dcc.Input(
                                id="username-input",
                                type="text",
                                placeholder="Enter username",
                                value="",
                                style={"width": "100%"},
                            ),
                        ],
                        style={
                            "display": "inline-block",
                            "width": "20%",
                            "margin": "10px",
                        },
                    ),
                    # Password
                    html.Div(
                        [
                            html.Label("Password"),
                            dcc.Input(
                                id="password-input",
                                type="password",
                                placeholder="Enter password",
                                value="",
                                style={"width": "100%"},
                            ),
                        ],
                        style={
                            "display": "inline-block",
                            "width": "20%",
                            "margin": "10px",
                        },
                    ),
                ]
            ),
        )
    else:
        return None


@app.callback(
    Output("table", "data"),
    Input("interval", "n_intervals"),
    Input("table-dropdown", "value"),
)
def updateTable(n, value):
    global Tel_df
    global Status_df
    match value:
        case "Status":
            temp = Status_df
            try:
                temp.sort_values(by="DevId", ascending=True, inplace=True)
            except:
                pass
            return temp.to_dict("records")
        case "Telemetry":
            temp = Tel_df
            try:
                temp.sort_values(by="DevId", ascending=True, inplace=True)
            except:
                pass
            return temp.to_dict("records")


@app.callback(
    Output("btn-nclicks-2", "children"),
    Input("btn-nclicks-2", "n_clicks"),
    State("btn-nclicks-2", "children"),
)
def displayClick(n_clicks, current_label):
    global mqtt_status
    bool_disabled = n_clicks % 2
    if bool_disabled:
        msg = mqtt_status
        # Start MQTT loop
        client.connect(broker_address, broker_port)
        client.loop_start()
        new_label = f"Disconnect"
    else:
        msg = mqtt_status
        client.disconnect()  # disconnect gracefully
        client.loop_stop()  # stops network loop
        new_label = f"Connect"
    return new_label


if __name__ == "__main__":
    app.run(debug=True)
