var d3 = d3 || {}; // just to get rid of linter errors

function getStyleProperty(id, property) {
    const element = document.querySelector(id);
    const style = window.getComputedStyle(element);
    const value = style.getPropertyValue(property);

    return value;
}

// Modified version of this https://bl.ocks.org/mbostock/1095795
class NetworkGraph {
    constructor(containerId) {
        this.container = d3.select(containerId);
        this.width = parseInt(getStyleProperty(containerId, "width"), 10);
        this.height = parseInt(getStyleProperty(containerId, "height"), 10);
        this.color = d3.scaleOrdinal(d3.schemeCategory10);
        this.nodes = [];
        this.links = [];

        this. simulation = d3.forceSimulation(this.nodes)
            .force("charge", d3.forceManyBody().strength(-1000))
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

        this.reset();
    }

    reset() {
        // Apply the general update pattern to the nodes.
        this.node = this.node.data(this.nodes, (d) => { return d.id;});
        this.node.exit().remove();
        this.node = this.node.enter()
            .append("circle")
            .attr("fill", (d) => { return this.color(d.id); })
            .attr("r", 8)
            .merge(this.node);

        // Apply the general update pattern to the links.
        this.link = this.link.data(this.links, (d) => { return d.source.id + "-" + d.target.id; });
        this.link.exit().remove();
        this.link = this.link
            .enter()
            .append("line")
            .merge(this.link);

        // Update and restart the simulation.
        this.simulation.nodes(this.nodes);
        this.simulation.force("link").links(this.links);
        this.simulation.alpha(1).restart();
    }

    ticked() {
        this.node.attr("cx", (d) => { return d.x; })
            .attr("cy", (d) => { return d.y; });

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
}

function handleUpdate(state, graph, update) {
    if (update.hasOwnProperty("station")) {
        for (let sta of update["station"]) {
            sta.obj.id = sta.obj.mac;
            state.station[sta.obj.id] = sta.obj;
            graph.addNode(sta.obj);
        }
    }

    if (update.hasOwnProperty("connection")) {
        for (let conn of update["connection"]) {
            conn.obj.id = conn.obj.conn_id;
            conn.obj.source = state.station[conn.obj.station1];
            conn.obj.target = state.station[conn.obj.station2];
            state.connection[conn.obj.id] = conn.obj;
            graph.addLink(conn.obj);
        }
    }
}

// Main function
(function() {
    const netGraph = new NetworkGraph("#graph-container");

    // Keeping a table of objs by id for easy reference
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
    }).then((update) => {
        handleUpdate(state, netGraph, update);
        console.log("Intial state: ", state);
    }).catch(error => {
        console.error(error);
    });

})();
