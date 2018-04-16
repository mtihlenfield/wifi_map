const si = new sigma("graph-container");
si.settings({
    defaultNodeColor: "blue"
});

const state = {
    station: {},
    connection: {},
    network: {}
};

const initRequest = new Request("/init", {
    mode: "no-cors",
    method: "GET"
});

fetch(initRequest).then(response => {
    return response.json();
}).then(handleUpdate).catch(error => {
    alert(error);
    console.error(error);
});

function handleUpdate(update) {
    if (update.hasOwnProperty("station")) {
        let pos = 0;
        for (let sta of update["station"]) {
            state.station[sta.obj.mac] = sta.obj;
            si.graph.addNode({
                id: sta.obj.mac,
                size: 5,
            });
            pos++;
        }
    }

    if (update.hasOwnProperty("connection")) {
        for (let sta of update["connection"]) {
            state.connection[sta.obj.conn_id] = sta.obj;
            si.graph.addEdge({
                id: sta.obj.conn_id,
                source: sta.obj.station1,
                target: sta.obj.station2
            });
        }
    }

    si.refresh();
    si.startForceAtlas2();
}
