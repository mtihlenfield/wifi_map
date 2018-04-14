import multiprocessing
import os

import scapy.all as sc
import scapy.layers.dot11 as dot11

from wmap_common.constants import DEFAULT_CONFIG

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

    packets = sc.rdpcap(fname)
    for packet in packets:
        if packet.haslayer(dot11.Dot11):
            # We don't need anything below the dot11 layer
            dot11_layer = packet.getlayer(dot11.Dot11)
            layer_bytes = sc.raw(dot11_layer)
            packet_queue.put(layer_bytes, block=False)


def spawn_workers(packet_queue):
    """
    Spawns subprocesses to grab packets from the packet queue
    """
    num_workers = min(MAX_WORKERS, os.cpu_count())
    procs = []

    for i in range(num_workers):
        proc = multiprocessing.Process(
            target=process_packets, args=(packet_queue,)
        )
        proc.start()
        procs.append(proc)

    return procs


def process_packets(packet_queue):
    """
    Reads packets of the packet_queue, writes new info to the database,
    and places any updates on the update queue for the server to pull from
    """
    while True:
        packet_bytes = packet_queue.get()
        dot11_packet = dot11.Dot11(packet_bytes)



