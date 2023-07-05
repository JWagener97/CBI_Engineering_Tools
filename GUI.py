import dash
from dash.dependencies import Output, Input
from dash import dcc
from dash import html
from dash.dependencies import Output, Input
import plotly.graph_objs as go
from plotly.subplots import make_subplots
import paho.mqtt.client as mqtt
from datetime import datetime
import csv
import pandas as pd
import serial
import atexit



# File settings
output_file = "GUI.csv"
# CSV Header 
header = ["Timestamp", "Volt_RMS", "Current_RMS", "Real_Power","PF","RAW_Packet"]


def compare_last_line(csv_file, new_data):
    last_row = ""
    with open(csv_file, "r") as file:
        reader = csv.reader(file)
        for row in reader:
            last_row = row
    return last_row == new_data

# MQTT broker settings
broker_address = "10.0.0.45"
broker_port = 1883
topic = "us/01973988"

# MQTT broker credentials
username = "sem-rabbitmq"
password = "sem-rabbitmq123"


#parsing function
def parse(dec_pl):

    Time = dec_pl.split(",")[1]
    Time = (Time.split(":")[-1])
    timestamp = int(Time)
    Time = datetime.now()
    Time = Time

    V_rms = dec_pl.split(",")[3]
    V_rms = float(V_rms.split(":")[-1])

    I_rms = dec_pl.split(",")[4]
    I_rms = float(I_rms.split(":")[-1])

    if (I_rms == 0):
        I_rms = 0.00000000000000000000000000000000001

    Real_Power = dec_pl.split(",")[6]
    Real_Power = float(Real_Power.split(":")[-1])

    PF =  Real_Power / (V_rms * I_rms)
            
    data = [Time,V_rms,I_rms,Real_Power,PF,dec_pl]

    if V_rms == -1:
        return None
     
    return data

app = dash.Dash(__name__)
colors = {
    'background': 'black',
    'text': '#7FDBFF'
}
app.layout = html.Div(className="app-body",style={'backgroundColor': colors['background']},
    children = [

        html.Div(style={'width': '99%', 'display': 'inline-block'}, children=[
        dcc.Graph(id='power', animate=False),
        ]),

        html.Div(style={'width': '40%', 'display': 'inline-block'}, children=[
        dcc.Graph(id='gauge', animate=False),
        dcc.Interval(id='interval',interval=15000,n_intervals = 0),
        dcc.Store(id="clientside-data",data = []),
        ]),

        html.Div(style={'width': '45%', 'display': 'inline-block','verticalAlign': 'top'}, children=[
        dcc.Graph(id='power_factor', animate=False),
        ]),

        html.Div(style={'width': '15%', 'display': 'inline-block'}, children=[
        html.H3("Last Raw Packet"),
        html.Div(id='my-output', style={'whiteSpace': 'pre-line',"color": colors['text']}), 
        ]),

        html.Div(style={'width': '49%', 'display': 'inline-block'}, children=[
        dcc.Graph(id='volt', animate=False),
        ]),
        html.Div(style={'width': '49%', 'display': 'inline-block'}, children=[
        dcc.Graph(id='current', animate=False),
        ]),
    ]
)

# MQTT client callbacks
def on_connect(client, userdata, flags, rc):
    print("Connected to MQTT broker")
    client.subscribe(topic)

# MQTT client setup
def on_message(client, userdata, msg):
    global Time, Volt
    # Assuming the payload is a single float value
    dec = msg.payload.decode()            
    if dec[2] == 'S':
        ID = dec.split(",")[11].split(":")[-1]
        if not compare_last_line(output_file, parse(dec)):
            with open(output_file, "a", newline="") as file:
                writer = csv.writer(file)
                writer.writerow(parse(dec))


def on_disconnect(client, userdata, rc):
    print("Disconnected from MQTT broker")

# Create MQTT client instance
client = mqtt.Client()

# Set username and password for MQTT broker authentication
client.username_pw_set(username, password)

# Assign callbacks
client.on_connect = on_connect
client.on_message = on_message
client.on_disconnect = on_disconnect

# Connect to MQTT broker
client.connect(broker_address, broker_port)    

# Start MQTT loop
client.loop_start()



@app.callback(
    Output('clientside-data', 'data'),
    Input('interval', 'n_intervals')
    )
def update_graph_scatter(n):
    df = pd.read_csv("GUI.csv")
    Time = df['Timestamp']
    V_rms = df['Volt_RMS'].to_numpy()
    I_rms = df['Current_RMS'].to_numpy()
    Real_Power = df['Real_Power'].to_numpy()
    PF = df['PF'].to_numpy()
    VA = V_rms * I_rms
    last_entry = df.tail(1)
    plot_data = {'Time':list(Time),'Vrms':list(V_rms),'Irms':list(I_rms),
                 'Real_Power':list(Real_Power),'PF':list(PF),'VA':list(VA) ,'Raw':last_entry['RAW_Packet'] }
    return plot_data


@app.callback(Output(component_id='my-output', component_property='children'),
        [Input('clientside-data', 'data'),]
        )
def update_string(data):
    packet_string = ''.join(data['Raw'])
    packet_string = packet_string.replace(",", "\n")
    return '{}'.format(packet_string)

@app.callback(Output('gauge', 'figure'),
        Input('clientside-data', 'data'),
        )

def update_graph_scatter(data):
    fig = make_subplots(
    rows=2,
    cols=2,                   
    specs=[[{'type': 'indicator'}, {'type': 'indicator'}],
    [{'type': 'indicator'}, {'type': 'indicator'}]],horizontal_spacing = 0.15,
    vertical_spacing = 0.3
    )
    
    fig.add_trace(go.Indicator(
        name = "power_trace",
        value=float(data['Real_Power'][-1]),
            mode="gauge+number",
            title={'text': "Power"},
            number = {'valueformat':'.2f','suffix': 'W'},
            
            gauge={'axis': {'range': [None, 10*230]},
            'bar': {'color': "black"},
            'steps': [
                {'range': [0, 5*230], 'color': "green"},
                {'range': [5*230, 8*230], 'color': "orange"},
                {'range': [8*230, 10*230], 'color': "red"}],}),
            row=1,
            col=1,)
    
    fig.add_trace(go.Indicator(
        name = "pf_trace",
        value=data['PF'][-1],
        mode="gauge+number",
        title={'text': "Power factor, cos(φ)"},
        number = {'valueformat':'.3f'},
        gauge={'axis': {'range': [None, 1.0]},
           'bar': {'color': "black"},
           'steps': [
               {'range': [0.9, 1.0], 'color': "green"},
               {'range': [0.4, 0.9], 'color': "orange"},
               {'range': [0, 0.4], 'color': "red"}],}),
           row=1,
           col=2,)
    
    fig.add_trace(go.Indicator(
        name = "volt_trace",
        value=float(data['Vrms'][-1]),
        mode="gauge+number",
        title={'text': 'Volts'},
        number = {'valueformat':'.2f','suffix': 'V'},
        gauge={'axis': {'range': [207, 253]},
           'bar': {'color': "black"},
           'steps': [
               {'range': [207, 210], 'color': "red"},
               {'range': [210, 220], 'color': "orange"},
               {'range': [220, 240], 'color': "green"},
               {'range': [240, 250], 'color': "orange"},
               {'range': [250, 253], 'color': "red"}],}),
           row=2,
           col=1,)
           
    
    fig.add_trace(go.Indicator(
        name = "current_trace",
        value=float(data['Irms'][-1]),
        mode="gauge+number",
        title={'text': 'Current',},
        number = {'valueformat':'.2f','suffix': 'A'},
        gauge={'axis': {'range': [None, 10]},
        'bar': {'color': "black"},
        'steps': [
            {'range': [0, 5], 'color': "green"},
             {'range': [5, 8], 'color': "orange"},
            {'range': [8, 10], 'color': "red"}],}),
        row=2,
        col=2,)
    fig.update_layout(
        plot_bgcolor=colors['background'],
        paper_bgcolor=colors['background'],
        font_color=colors['text'],
        font=dict(family="Courier New, monospace",size=18)
    )
    
    return fig

@app.callback(Output('power', 'figure'),
        Input('clientside-data', 'data'),
        )

def update_graph_scatter(data):
    fig = go.Figure()
    fig.add_trace(go.Scattergl(
        name = "Real-power(W)",
        x = data['Time'],
        y = data['Real_Power'],
        mode='lines',
        marker=dict(size=10,color='yellow'),
        ))
    fig.add_trace(go.Scattergl(
        name = "Volt-ampere(S)",
        x = data['Time'],
        y = data['VA'],
        mode='lines',
        marker=dict(size=10,color='green'),
        ))
    fig.update_layout(
        title="Power",
        title_x=0.5,
        xaxis_title="Time",
        #yaxis_title="Power",
        legend_title="",
        plot_bgcolor=colors['background'],
        paper_bgcolor=colors['background'],
        font=dict(family="Courier New, monospace",size=18,color=colors['text'])
    )
    fig.update_layout(legend=dict(
    orientation="h",
    yanchor="bottom",
    y=1.02,
    xanchor="right",
    x=1
    ))
    return fig


@app.callback(Output('power_factor', 'figure'),
        Input('clientside-data', 'data'),
        )

def update_graph_scatter(data):
    fig = go.Figure()
    fig.add_trace(go.Scattergl(
        name = "Power Factor",
        x = data['Time'],
        y = data['PF'],
        mode='markers+lines',
        marker=dict(size=1,color='yellow'),
        ))
    fig.update_layout(
        title="Power Factor",
        title_x=0.5,
        xaxis_title="Time",
        yaxis_title="Cos(φ)",
        legend_title="Legend Title",
        plot_bgcolor=colors['background'],
        paper_bgcolor=colors['background'],
        font=dict(family="Courier New, monospace",size=18,color=colors['text'])
    )
    return fig

@app.callback(Output('volt', 'figure'),
        Input('clientside-data', 'data'),
        )

def update_graph_scatter(data):
    fig = go.Figure()
    fig.add_trace(go.Scattergl(
        name = "Voltage",
        x = data['Time'],
        y = data['Vrms'],
        mode='lines',
        marker=dict(size=10,color=colors['text']),
        ))
    fig.update_layout(
        title="Volatge",
        title_x=0.5,
        xaxis_title="Time",
        yaxis_title="(V)",
        legend_title="Legend Title",
        plot_bgcolor=colors['background'],
        paper_bgcolor=colors['background'],
        font=dict(family="Courier New, monospace",size=18,color=colors['text'])
    )
    return fig

@app.callback(Output('current', 'figure'),
        Input('clientside-data', 'data'),
        )

def update_graph_scatter(data):
    fig = go.Figure()
    fig.add_trace(go.Scattergl(
        name = "Current",
        x = data['Time'],
        y = data['Irms'],
        mode='lines',
        marker=dict(size=10,color='red'),
        ))
    fig.update_layout(
        title="Current",
        title_x=0.5,
        xaxis_title="Time",
        yaxis_title="(A)",
        legend_title="Legend Title",
        plot_bgcolor=colors['background'],
        paper_bgcolor=colors['background'],
        font=dict(family="Courier New, monospace",size=18,color=colors['text'])
    )
    return fig


if __name__ == '__main__':

   

    #with open(output_file, "w", newline="") as file:
        #writer = csv.writer(file)
        #writer.writerow(header)

    # Run the Dash app
    app.run_server(debug=False)
