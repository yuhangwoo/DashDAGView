import plotly.graph_objects as go
import numpy as np
from dash.dependencies import Input, Output
import dash_bootstrap_components as dbc
from dash import Dash, dash_table, dcc, html
import zmq

app = Dash(external_stylesheets=[dbc.themes.BOOTSTRAP])

data = {'nodes': {}, 'links': []}
rows = []
x_max = 30
epochs=[]
accs = []
losss = []
fig = go.Figure(layout={"template": "simple_white",
                        "xaxis": {"title": "Time", "constrain": "domain"},
                        "yaxis": {"title": "Plane", "constrain": "domain"},
                        "width": 1500,
                        "height": 500
                        })
acc_fig1 = go.Figure()
loss_fig = go.Figure()
trace_acc = None
trace_loss = None
def update_all(msg):
    '''生成节点'''
    global data, fig, rows, accs, losss, acc_fig1, loss_fig, epochs, trace_acc, trace_loss
    i = msg['transnum']
    data['nodes'][msg['id']]=msg
    '''添加link'''
    if msg['previous1']!='None' and msg['previous2']!='None':
        link1 = {'source': msg['previous1'], 'target': msg['id']}
        link2 = {'source': msg['previous2'], 'target': msg['id']}
        data['links'].append(link1)
        data['links'].append(link2)
        link_ls = [link1, link2]
    elif i>0:
        link = {'source': msg['previous1'], 'target': msg['id']}
        data['links'].append(link)
        link_ls = [link]

    '''绘制节点和边'''
    if i>0:
        for link in link_ls:
            node_source = data['nodes'][link['source']]
            node_target = msg
            fig.add_annotation(
                x=node_source['located'][0],
                y=node_source['located'][1],
                xref='x', yref='y',
                ax=node_target['located'][0],
                ay=node_target['located'][1],
                axref='x', ayref='y',
                showarrow=True,
                arrowhead=2, arrowsize=2,
                arrowwidth=1, standoff=10,
                arrowcolor='black', startstandoff=5
            )
    fig.add_trace(
        go.Scatter(
            x=[msg['located'][0]],
            y=[msg['located'][1]],
            text=msg['id']+'<br>Hash: '+msg['Transhash']+'<br>Accuracy: {:.4f}'.format(msg['Accuracy']),
            mode='markers',
            name=msg['id'],
            marker=dict(symbol='square', size=msg['value'], line=dict(width=2))
        )
    )
    fig.update_layout(
        legend_traceorder='reversed'
    )
    # 限制横轴最大值
    if msg['located'][0] > x_max:
        fig.update_xaxes(range=[msg['located'][0]-x_max-1, msg['located'][0]+1])

    rows.insert(0, {'T': msg['Transhash'], 'P': 'RSU{}'.format(np.random.randint(1,10)),
                    'P1': msg['previous1'], 'P2': msg['previous2'], 'Acc': round(msg['Accuracy'],5), 'W': msg['value']})
    '''绘制精度曲线'''
    accs.append(round(msg['Accuracy'],5))
    losss.append(round(msg['Loss'],5))
    epochs.append(len(accs))
    # if i>0:
    trace_acc=go.Scatter(
        x=epochs,
        y=accs,
        mode="lines",  # 线段绘图
        name="lines"
    )
    trace_loss=go.Scatter(
        x=epochs,
        y=losss,
        mode="lines",  # 线段绘图
        name="lines"
    )
    acc_fig1 = go.Figure(data=trace_acc, layout={
        "title": {"text": "Epoch vs Accuracy","font": {"size": 20}},
        "template": "ggplot2",
        "xaxis": {"title": "Epoch"},
        "yaxis": {"title": "Accuracy"}
    })
    loss_fig = go.Figure(data=trace_loss, layout={
        "title": {"text": "Epoch vs Loss","font": {"size": 20}},
        "template": "seaborn",
        "xaxis": {"title": "Epoch"},
        "yaxis": {"title": "Loss"}
    })

app.layout = html.Div([
    dbc.Row(dbc.Label('DAG Blockchain Easy View',style={'font-size': '24px', 'text-align': 'center', 'margin': '0 auto'}),justify='center'),
    dcc.Graph(id='graph', figure=fig),#, figure=fig
    dcc.Interval(id="interval"),
    html.Div([
        dcc.Graph(id='accuracy1', figure=acc_fig1, style={'width': '750px', 'height': '440px'}),
        dcc.Graph(id='loss', figure=loss_fig, style={'width': '750px', 'height': '440px'})
        ], style={'display': 'flex', 'flex-wrap': 'nowrap'}),
    dbc.Row(dbc.Label('DAG Transcations Information',style={'font-size': '24px', 'text-align': 'center', 'margin': '0 auto'}),justify='center'),
    dash_table.DataTable(id='table',
                         columns=[{'name': 'Transaction Hash', 'id': 'T'},{'name': 'Pbulisher', 'id': 'P'},{'name': 'Previous Trans 1', 'id': 'P1'},
                                  {'name': 'Previous Trans 2', 'id': 'P2'},{'name': 'Accuracy', 'id': 'Acc'},{'name': 'Weight', 'id': 'W'}],
                         page_size=50, data=rows,
                         style_table={'maxWidth': '1400px', 'maxHeight': '300px', 'overflowY': 'scroll', 'margin': '0 auto'},
                         style_cell={'textAlign': 'center'},
                         #'''换行显示'''
                         # style_cell={'textAlign': 'center', 'minWidth': '180px', 'width': '180px', 'maxWidth': '180px'},
                         # style_data={
                         #     'whiteSpace': 'normal',
                         #     'height': 'auto'}
                         )
])

def create_and_connect_zmq_socket(zmq_port="5411"):
    """创建并连接到 ZMQ 服务端"""
    context = zmq.Context()
    zmq_socket = context.socket(zmq.SUB)
    zmq_socket.connect("tcp://localhost:%s" % zmq_port)
    zmq_socket.setsockopt_string(zmq.SUBSCRIBE, "")  # 消息过滤
    return zmq_socket

@app.callback(Output('graph', 'figure'), Output('table', 'data'), Output('accuracy1', 'figure'), Output('loss', 'figure'), Input('interval', 'n_intervals'))
def update_components(n_intervals):
    if not hasattr(update_components, "zmq_socket"):
        update_components.zmq_socket = create_and_connect_zmq_socket()

    try:
        msg = update_components.zmq_socket.recv_pyobj(flags=zmq.NOBLOCK)
        # df.insert(0, msg)
        update_all(msg)
    except zmq.Again:
        pass
    return fig, rows, acc_fig1, loss_fig

if __name__ == '__main__':
    app.run_server(debug=True)
