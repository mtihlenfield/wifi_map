import multiprocessing
import json
import os

import scapy.all as sc
import scapy.layers.dot11 as dot11

from wmap_common.constants import DEFAULT_CONFIG
from . import handlers

# This is somewhat arbitrary...
MAX_WORKERS = 6


def sniff(interface, config=DEFAULT_CONFIG):
    """
    Listens for 802.11 packets on an interface and stores/queues
    revelant information.
    """
    print("Sniffing")


def read(fname, config=DEFAULT_CONFIG):
    """
    Reads 802.11 packets from a pcap file and stores/queues
    relevant information.
    """
    packet_queue = multiprocessing.Queue()
    spawn_workers(packet_queue)

    print("Reading")
    packets = sc.rdpcap(fname)
    print("Placing on queue")
    for packet in packets:
        if packet.haslayer(dot11.Dot11):
            # We don't need anything below the dot11 layer
            dot11_layer = packet.getlayer(dot11.Dot11)
            layer_bytes = sc.raw(dot11_layer)
            # TODO add timestamp to packet so updates stay in order
            packet_queue.put(layer_bytes, block=False)


def spawn_workers(packet_queue):
    """
    Spawns subprocesses to grab packets from the packet queue
    """
    # TODO implement a method of gracefully stopping the workers
    num_workers = min(MAX_WORKERS, os.cpu_count())
    procs = []

    # This lock must be acquired before executing database writes or database
    # reads followed by dependent database writes.
    # Having a single lock to access all tables for reads and writes is hamfisted
    # but I don't have time for a better approach
    db_lock = multiprocessing.Lock()

    for i in range(num_workers):
        proc = multiprocessing.Process(
            target=process_packets, args=(packet_queue, db_lock)
        )
        proc.start()
        procs.append(proc)

    return procs


def process_packets(packet_queue, db_lock):
    """
    Reads packets of the packet_queue, writes new info to the database,
    and places any updates on the update queue for the server to pull from
    """
    while True:
        packet_bytes = packet_queue.get()
        packet = dot11.Dot11(packet_bytes)
        handler = handlers.get_handler(packet.type, packet.subtype)

        changes = handler(packet, db_lock)

        if packet.type == 2:
            update = {}
            for change in changes:
                class_name = change.objtype.class_name
                if class_name not in update:
                    update[class_name] = []

                update[class_name].append(change.to_dict())

            serialized_update = json.dumps(update)

        # TODO enqueue update
