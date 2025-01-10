# DashDAGView
DashDAGView is a website for visualizing the directed acyclic graph structure and the information of transactions in the DAG-FL (Federated Learning).

You should define anothor py file that using zmq send message to 'Dash-DAG-View.py' through port '5411'. Example as follows

```
import zmq

context = zmq.Context()
socket = context.socket(zmq.PUB)
socket.bind("tcp://*:5411")
message = "sent message that follow the defined format"
socket.send_pyobj(message)
```

Notice that message follows the follow dictionary type:
{
  'Transhash': '899907GwaNTJfauxKTNBBePgOE0xYYOaEKZfe7ZYFki3bILPPC', 
  'previous1': 'Trans3', 
  'previous2': 'Trans2', 
  'id': 'Trans7', 
  'transnum': 7, 
  'value': 20, 
  'located': [14, 2.353932164273416], 
  'Accuracy': 0.7543617486953735, 
  'Loss': 1.3086285591125488
}
