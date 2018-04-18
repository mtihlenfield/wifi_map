var d3 = d3 || {};
var io = io || {};

function getStyleProperty(id, property) {
    const element = document.querySelector(id);
    const style = window.getComputedStyle(element);
    const value = style.getPropertyValue(property);

    return value;
}


// Modified version of this https://bl.ocks.org/mbostock/1095795
class NetworkGraph {
    constructor(containerId, networksId, colorCb, shapeCb, sizeCb, clickCb) {
        this.container = d3.select(containerId);
        this.netContainer = d3.select(networksId);
        this.width = parseInt(getStyleProperty(containerId, "width"), 10);
        this.height = parseInt(getStyleProperty(containerId, "height"), 10);
        this.color = colorCb;
        this.shape = shapeCb;
        this.size = sizeCb;
        this.click = clickCb;
        this.nodes = [];
        this.links = [];
        this.networks = [];

        this.simulation = d3.forceSimulation(this.nodes)
            .force("charge", d3.forceManyBody().strength(-1500))
            .force("link", d3.forceLink(this.links).distance(200))
            .force("x", d3.forceX())
            .force("y", d3.forceY())
            .alphaTarget(1)
            .on("tick", () => { this.ticked(); });

        this.g = this.container
            .append("g")
            .attr("pointer-events", "all")
            .attr(
                "transform",
                "translate(" + this.width / 2 + "," + this.height / 2 + ")"
            );

        this.link = this.g.append("g")
            .attr("stroke", "#000")
            .attr("stroke-width", 1.5)
            .selectAll(".link");

        this.node = this.g.append("g")
            .attr("stroke", "#fff")
            .attr("stroke-width", 1.5)
            .selectAll(".node");

        this.label = this.g.append("g")
            .attr("font-size", 15)
            .selectAll(".label");

        this.network = this.netContainer
            .select("ul")
            .selectAll("li");

        const zoom_handler = d3.zoom()
            .on("zoom", () => this.g.attr("transform", d3.event.transform));

        zoom_handler(this.container);

        this.reset();
    }

    reset() {
        let self = this;

        if (this.networks.length > 0) {
            this.netContainer.style("display", "block");
        }

        this.network = this.network
            .data(this.networks, (d) => { return d.ssid; });

        this.network.exit().remove();

        this.network = this.network
            .enter()
            .append("li")
            .style("color", (d) => { return this.color(d); })
            .text(d => d.ssid)
            .merge(this.network);

        // update number of node elements
        this.node = this.node.data(this.nodes, (d) => { return d.id;});

        // Make sure shapes are up to date
        this.node.selectAll("path")
            .attr("d", d3.symbol()
                .size((d) => { return this.size(d); } )
                .type((d) => { return this.shape(d); })
            ).attr("fill", (d) => { return this.color(d); });

        // remove any node elemnents that no longer have stations
        this.node.exit().remove();

        // create any new node elements
        this.node = this.node.enter()
            .append("path")
            .attr("fill", (d) => { return this.color(d); })
            .attr("d", d3.symbol()
                .size((d) => { return this.size(d); } )
                .type((d) => { return this.shape(d); })
            )
            .attr("class", "node")
            .on("click", function(d) { self.click(d); })
            .call(d3.drag()
                .on("start", (d) => { this.dragstarted(d); })
                .on("drag", (d) => { this.dragged(d); })
                .on("end", (d) => { this.dragended(d); })
            )
            .merge(this.node);

        this.label = this.label.data(this.nodes, node => node.id);
        this.label.exit().remove();
        this.label = this.label.enter()
            .append("text")
            .text(node => node.ssid || node.id)
            .merge(this.label);

        // Apply the general update pattern to the links.
        this.link = this.link.data(this.links, (d) => { return d.source.id + "-" + d.target.id; });
        this.link.exit().remove();
        this.link = this.link
            .enter()
            .append("line")
            .attr("class", "link")
            .merge(this.link);

        // Update and restart the simulation.
        this.simulation.nodes(this.nodes);
        this.simulation.force("link").links(this.links);
        this.simulation.alpha(1).restart();
    }

    ticked() {
        this.node.attr("transform", function(d) {
            return "translate(" + d.x + "," + d.y + ")";
        });

        this.label.attr("dx", node => { return node.x -20 ; })
            .attr("dy", node => { return node.y - 20; });

        this.link.attr("x1", (d) => { return d.source.x; })
            .attr("y1", (d) => { return d.source.y; })
            .attr("x2", (d) => { return d.target.x; })
            .attr("y2", (d) => { return d.target.y; });
    }

    findNodeIndex(id) {
        for (let i = 0; i < this.nodes.length; i++) {
            if (this.nodes[i].id == id) {
                return i;
            }
        }
    }

    findLinkIndex(id) {
        for (let i = 0; i < this.links.length; i++) {
            if (this.links[i].id == id) {
                return i;
            }
        }
    }

    addNode(newNode) {
        this.nodes.push(newNode);
        this.reset();
    }


    addLink(newLink) {
        this.links.push(newLink);
        this.reset();
    }

    addNetwork(newNetwork) {
        this.networks.push(newNetwork);
        this.reset();
    }

    removeNode(id) {
        const nodeIndex = this.findNodeIndex(id);
        const nodeId = this.nodes[nodeIndex].id;

        // Need to remove any links attached to the node
        let i = 0;
        while (i < this.links.length) {
            if ((this.links[i].source == nodeId) || (this.links[i].source == nodeId)) {
                this.links.splice(i, 1);
            }
            else i++;
        }

        this.nodes.splice(nodeIndex, 1);

        this.reset();
    }

    removeLink(id) {
        const linkIndex = this.findLinkIndex(id);
        this.links.splice(linkIndex, 1);
        this.reset();
    }

    update() {
        this.reset();
    }

    dragstarted(obj) {
        if (!d3.event.active) this.simulation.alphaTarget(0.3).restart();
        obj.fx = obj.x;
        obj.fy = obj.y;
    }

    dragged(obj) {
        obj.fx = d3.event.x;
        obj.fy = d3.event.y;
    }

    dragended(obj) {
        if (!d3.event.active) this.simulation.alphaTarget(0);
        obj.fx = null;
        obj.fy = null;
    }
}

function getStationNetwork(state, sta) {
    // In order to find the stations network we need to see if
    // it has any connections that have networks
    let net = null;
    for (let conn of Object.values(state["connection"])) {
        if (conn.source.id == sta.id && conn.target.ssid !== null) {
            net = conn.target.ssid;
            sta.ssid = net;
            break;
        }
        if (conn.target.id == sta.id && conn.source.ssid !== null) {
            net = conn.source.ssid;
            sta.ssid = net;
            break;
        }
    }

    return net;
}

function getColor(state, obj) {
    let netid = null;
    if (obj.ssid) {
        netid = obj.ssid;
    } else if (obj.type == "station") {
        netid = getStationNetwork(state, obj);
    }

    if (netid != null) {
        let color = state.color(netid);
        return color;
    }

    return "#808080"; // grey
}

function getShape(state, sta) {
    if (sta.is_ap) {
        return d3.symbolTriangle;
    } else {
        return d3.symbolSquare;
    }
}

function getSize(state, sta) {
    if (sta.is_ap) {
        return 900;
    } else {
        return 500;
    }
}

function onClick(state, obj) {
    if (obj.type == "station") {
        let infoPanel = d3.select("#sta-info");
        infoPanel.style("display", "block");

        d3.select("#sta-mac")
            .text(obj.mac);

        if (obj.is_ap && obj.ssid) {
            d3.select("#sta-network")
                .text(obj.ssid);
        } else {
            d3.select("#sta-network")
                .text(getStationNetwork(state, obj) || "unknown");
        }

        d3.select("#sta-man")
            .text(obj.manufacturer || "unknown");

        d3.select("#sta-ap")
            .text(obj.is_ap ? "yes" : "no");
    }
}

function handleUpdate(state, graph, update) {
    // order is important here. stations and connections
    // both reference networks

    if (update.hasOwnProperty("network")) {
        for (let change of update["network"]) {
            if (change.action === "update") {
                let curr_net = state.network[change.obj.ssid];
                for (let key of change.updates) {
                    curr_net[key] = change.obj[key];
                }
            } else {
                change.obj.id = change.obj.ssid;
                change.obj.type = "network";
                state.network[change.obj.id] = change.obj;
                graph.addNetwork(change.obj);
            }
        }

    }

    if (update.hasOwnProperty("station")) {
        for (let change of update["station"]) {
            if (change.action === "update") {
                let curr_sta = state.station[change.obj.mac];
                for (let key of change.updates) {
                    curr_sta[key] = change.obj[key];
                }
            } else {
                change.obj.id = change.obj.mac;
                change.obj.type = "station";
                state.station[change.obj.id] = change.obj;
                graph.addNode(change.obj);
            }
        }
    }


    if (update.hasOwnProperty("connection")) {
        for (let change of update["connection"]) {
            if (change.action === "update") {
                let curr_conn = state.station[change.obj.conn_id];

                // TODO need to handle creation/deletion of connections for 'updates'
                for (let key of change.updates) {
                    curr_conn[key] = change.obj[key];
                }

            } else {
                change.obj.id = change.obj.conn_id;
                change.obj.type = "connection";
                change.obj.source = state.station[change.obj.station1];
                change.obj.target = state.station[change.obj.station2];
                state.connection[change.obj.id] = change.obj;
                graph.addLink(change.obj);
            }
        }
    }
}

// Main function
(function() {
    // Keeping a table of objs by id for easy reference
    const state = {
        station: {},
        connection: {},
        network: {},
        color: d3.scaleOrdinal(d3.schemePaired)
    };

    const netGraph = new NetworkGraph(
        "#graph-container",
        "#networks",
        (obj) => { return getColor(state, obj); },
        (obj) => { return getShape(state, obj); },
        (obj) => { return getSize(state, obj); },
        (obj) => { onClick(state, obj); }
    );

    const initRequest = new Request("/init", {
        mode: "no-cors",
        method: "GET"
    });

    fetch(initRequest).then(response => {
        return response.json();
    }).then((update) => {
        handleUpdate(state, netGraph, update);
        console.log("Intial state: ", state);
    }).catch(error => {
        console.error(error);
    });

    const socket = io.connect("http://" + document.domain + ":" + location.port);
    // this is a callback that triggers when the "my response" event is emitted by the server.
    socket.on("update", function(update) {
        handleUpdate(state, netGraph, JSON.parse(update));
    });
})();
