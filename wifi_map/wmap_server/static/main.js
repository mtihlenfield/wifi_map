var d3 = d3 || {}; // just to get rid of linter errors

function getStyleProperty(id, property) {
    const element = document.querySelector(id);
    const style = window.getComputedStyle(element);
    const value = style.getPropertyValue(property);

    return value;
}


// Modified version of this https://bl.ocks.org/mbostock/1095795
class NetworkGraph {
    constructor(containerId, colorCb, shapeCb) {
        this.container = d3.select(containerId);
        this.width = parseInt(getStyleProperty(containerId, "width"), 10);
        this.height = parseInt(getStyleProperty(containerId, "height"), 10);
        this.color = colorCb;
        this.shape = shapeCb;
        this.nodes = [];
        this.links = [];

        this. simulation = d3.forceSimulation(this.nodes)
            .force("charge", d3.forceManyBody().strength(-2000))
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

        this.reset();
    }

    reset() {
        // Apply the general update pattern to the nodes. https://github.com/d3/d3-selection/blob/master/README.md#joining-data
        this.node = this.node.data(this.nodes, (d) => { return d.id;});
        this.node.exit().remove();
        this.node = this.node.enter()
            .append("circle")
                .attr("fill", (d) => { return this.color(d); })
                .attr("r", 20)
                .attr("class", "node")
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
        // this.node.attr("cx", (d) => { return d.x; })
        //    .attr("cy", (d) => { return d.y; });
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
    for (let conn of Object.values(state["connection"])) {
        if (conn.source == sta.id || conn.target == sta.id) {
            if (conn.ssid !== null) {
                return state["network"][conn.ssid];
            }
        }
    }

    return null;
}

function getColor(state, obj) {
    let network = getStationNetwork(state, obj);
    if (network != null) {
        return state.color(network.ssid);
    }

    return "#808080"; // grey
}

function getShape(state, obj) {
    return "circle";
}

function handleUpdate(state, graph, update) {
    if (update.hasOwnProperty("station")) {
        for (let sta of update["station"]) {
            sta.obj.id = sta.obj.mac;
            sta.obj.type = "station";
            state.station[sta.obj.id] = sta.obj;
            graph.addNode(sta.obj);
        }
    }

    if (update.hasOwnProperty("connection")) {
        for (let conn of update["connection"]) {
            conn.obj.id = conn.obj.conn_id;
            conn.obj.type = "connection";
            conn.obj.source = state.station[conn.obj.station1];
            conn.obj.target = state.station[conn.obj.station2];
            state.connection[conn.obj.id] = conn.obj;
            graph.addLink(conn.obj);
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
        color: d3.scaleOrdinal(d3.schemeCategory20)
    };

    const netGraph = new NetworkGraph(
        "#graph-container",
        (obj) => { return getColor(state, obj); },
        (obj) => { return getShape(state, obj); }
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

})();
