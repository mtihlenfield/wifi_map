import multiprocessing
import time
import os
import queue

import scapy.all as sc
import scapy.layers.dot11 as dot11

from wmap_common.constants import DEFAULT_CONFIG
from wmap_common.update_queue import UpdateQueue
from . import handlers


def sniff(interface, config=DEFAULT_CONFIG):
    """
    Listens for 802.11 packets on an interface and stores/queues
    revelant information.
    """
    packet_queue = multiprocessing.Queue()
    update_queue = UpdateQueue.get_connection(config["mq_port"])
    completion_event = multiprocessing.Event()
    spawn_workers(packet_queue, update_queue, completion_event)

    def callback(packet):
        if packet.haslayer(dot11.Dot11):
            # We don't need anything below the dot11 layer
            dot11_layer = packet.getlayer(dot11.Dot11)
            layer_bytes = sc.raw(dot11_layer)
            time_recieved = time.time()

            message = {
                "pkt": layer_bytes,
                "rcvd": time_recieved
            }

            packet_queue.put(message, block=False)

    # TODO replace with raw socket listen. Scapy has too much overhead.
    sniff_proc = multiprocessing.Process(
        target=sc.sniff,
        kwargs={
            "iface": interface,
            "prn": callback
        }
    )

    print("Sniffing packets...")
    sniff_proc.start()


def read(fname, config=DEFAULT_CONFIG):
    """
    Reads 802.11 packets from a pcap file and stores/queues
    relevant information.
    """
    # TODO probably need to limit the # number of packets
    # written to the queue per second. We're writing
    # wayyyyyyy faster than we're reading.
    packet_queue = multiprocessing.Queue()
    update_queue = UpdateQueue.get_connection(config["mq_port"])
    completion_event = multiprocessing.Event()
    workers = spawn_workers(packet_queue, update_queue, completion_event)

    try:
        print("Reading...")
        packets = sc.rdpcap(fname)
        print("Placing on queue...")
        for packet in packets:
            if packet.haslayer(dot11.Dot11):
                # We don't need anything below the dot11 layer
                dot11_layer = packet.getlayer(dot11.Dot11)
                layer_bytes = sc.raw(dot11_layer)
                time_recieved = time.time()

                message = {
                    "pkt": layer_bytes,
                    "rcvd": time_recieved
                }

                packet_queue.put(message, block=False)
        print("Processing...")
        completion_event.set()
    except KeyboardInterrupt:
        print("Closing...")
        completion_event.set()

    for worker in workers:
        worker.join()

    print("Completed queueing updates")


def spawn_workers(packet_queue, update_queue, completion_event):
    """
    Spawns subprocesses to grab packets from the packet queue
    """
    num_workers = os.cpu_count()
    procs = []

    # This lock must be acquired before executing database writes or database
    # reads followed by dependent database writes.
    # TODO implement this more efficiently. This is rather hamfisted.
    locks = {
        "station": multiprocessing.Lock(),
        "connection": multiprocessing.Lock(),
        "network": multiprocessing.Lock()
    }

    for i in range(num_workers):
        proc = multiprocessing.Process(
            target=process_packets, args=(packet_queue, update_queue, locks, completion_event)
        )
        proc.start()
        procs.append(proc)

    return procs


def process_packets(packet_queue, update_queue, locks, completion_event):
    """
    Reads packets of the packet_queue, writes new info to the database,
    and places any updates on the update queue for the server to pull from
    """
    while True:
        try:
            message = packet_queue.get(block=False)
            packet = dot11.Dot11(message["pkt"])
            time_recieved = message["rcvd"]
            handler = handlers.get_handler(packet.type, packet.subtype)

            changes = handler(packet, time_recieved, locks)

            if len(changes) > 0:
                update = {}
                for change in changes:
                    class_name = change.objtype.class_name
                    if class_name not in update:
                        update[class_name] = []

                    update[class_name].append(change.to_dict())

                update_queue.put(update)

        except queue.Empty:
            if completion_event.is_set():
                return
            else:
                time.sleep(1)

        # TODO enqueue update
