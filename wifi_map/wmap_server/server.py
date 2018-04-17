import json
import itertools

from flask import Flask, render_template, jsonify
from flask_socketio import SocketIO

from wmap_common import constants
from wmap_common.update_queue import UpdateQueue
from wmap_common import models
from wmap_common import state

app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret!'
socketio = SocketIO(app)


def start_server(config=constants.DEFAULT_CONFIG):
    update_queue = UpdateQueue.get_connection(config["mq_port"])
    socketio.start_background_task(queue_listen, update_queue)
    print("Starting server...")

    try:
        socketio.run(app, port=config["portno"])
    except KeyboardInterrupt:
        update_queue.close()


def queue_listen(update_queue):
    def callback(update):
        socketio.emit(json.dumps(update), broadcast=True)
        update_queue.listen(callback)


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/init")
def init():
    """
    Retrieves the current map state and returns it as an update
    """
    print("Got init request")
    stations = models.Station.select().execute()
    connections = models.Connection.select().execute()
    networks = models.Network.select().execute()

    all_models = itertools.chain(stations, connections, networks)
    update = {}

    for model in all_models:
        if model.class_name not in update:
            update[model.class_name] = []

        change = state.StateChange(
            state.ACTION_CREATE,
            type(model),
            model
        )

        update[model.class_name].append(change.to_dict())

    return jsonify(update)
