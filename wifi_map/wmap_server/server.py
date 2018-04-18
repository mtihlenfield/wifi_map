import json
import itertools
import threading

from flask import Flask, render_template, jsonify
from flask_socketio import SocketIO

from wmap_common import constants
from wmap_common import models
from wmap_common import state

app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret!'
socketio = SocketIO(app)


def start_server(update_queue, config=constants.DEFAULT_CONFIG):
    socketio.start_background_task(queue_listen, update_queue)
    print("Client started on port {0}. Open 'http://localhost:{0}' in browser.".format(config["portno"]))

    try:
        socketio.run(app, port=config["portno"])
    except KeyboardInterrupt:
        print("Shutting down...")


def queue_listen(update_queue):
    def target(update_queue):
        while True:
            update = update_queue.get()
            socketio.emit("update", json.dumps(update), broadcast=True)

    # this is reallllly hacky
    proc = threading.Thread(target=target, args=(update_queue,))
    proc.start()


@socketio.on("connect")
def on_connect():
    print("websocket client connected")
    # socketio.emit("update", "test")


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/init")
def init():
    """
    Retrieves the current map state and returns it as an update
    """
    print("Got client request")
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
