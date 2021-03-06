#!/usr/bin/env python
# import threading
import threading
import queue
import argparse
import os

from wmap_sniffer import sniff, read
from wmap_server import start_server
import wmap_common.constants as constants
import wmap_common.db_utils as db_utils
import wmap_common.models as models


def filename(fname):
    """
    argparse type function that makes sure a given filename exists
    """
    if not os.path.exists(fname):
        raise argparse.ArgumentTypeError(
            "Pcap file {} does not exist.".format(fname)
        )
    else:
        return fname


def port(portno):
    """
    argparse type function that makes sure a given port number is valid
    """
    portno = int(portno)
    if not (0 < portno < 65535):
        raise argparse.ArgumentTypeError(
            "Invalid port number {}.".format(portno)
        )
    else:
        return portno


def interface(nic_name):
    """
    argparse type function that makes sure a network interface with the given
    name exists
    """
    # NOTE: This is not portable. Won't work on Windows
    interfaces = os.listdir("/sys/class/net")
    if nic_name not in interfaces:
        raise argparse.ArgumentTypeError(
            "No such network interface: {}".format(nic_name)
        )
    else:
        return nic_name


def parse_args():
    """
    Parses and returns argparse arguments
    """
    parser = argparse.ArgumentParser(
        description="wifi_map - Visual nearby 802.11 devices and networks."
    )

    group = parser.add_mutually_exclusive_group(required=True)

    group.add_argument(
        "-r", "--read", type=filename, metavar="FNAME",
        help="Pcap file to read from."
    )

    group.add_argument(
        "-i", "--interface", type=interface,
        help="Network interface to listen on"
    )

    parser.add_argument(
        "-p", "--port", type=port, default=constants.DEFAULT_SERVER_PORT,
        help="TCP port to run the web client on"
    )

    parser.add_argument(
        "--db-port", type=port, default=constants.DEFAULT_DB_PORT,
        help="TCP port that MySQL is running on."
    )

    parser.add_argument(
        "--mq-port", type=port, default=constants.DEFAULT_MQ_PORT,
        help="TCP port that RabbitMQ is running on."
    )

    return parser.parse_args()


def main():
    # TODO verify rabbitmq is running
    # TODO initialize queues
    # TODO spin up server process

    args = parse_args()

    config = {
        "portno": args.port,
        "mq_port": args.mq_port
    }

    db_init()

    update_queue = queue.Queue()

    server_proc = threading.Thread(target=start_server, args=(update_queue, config,))
    server_proc.start()

    if args.read:
        read(args.read, update_queue, config)
    else:
        sniff(args.interface, update_queue, config)


def db_init():
    """
    Creates the database if it doesn't exist. Clears if it does.
    """
    if not os.path.isdir(constants.DB_DIR):
        os.mkdir(constants.DB_DIR)
        create_db()
    elif not os.path.exists(constants.DB_FILE):
        create_db()
    else:
        # Clearing the database insead of just deleting is so we don't have
        # to recreate the IEEE mac address table
        for model in [models.Station, models.Network, models.Connection]:
            model.delete().where(True).execute()


def create_db():
    """
    Creates the database and the tables.
    """
    db = db_utils.get_db()

    with db:
        db.create_tables([
            models.Station,
            models.Network,
            models.Connection
        ])


if __name__ == "__main__":
    main()
