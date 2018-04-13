import multiprocessing

import scapy.all as sc
import scapy.layers.dot11 as dot11

from wmap_common import DEFAULT_CONFIG

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
    pass


def process_packets(packet_queue):
    pass
