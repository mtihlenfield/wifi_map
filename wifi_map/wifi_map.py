#!/usr/bin/env python
import argparse
import os

from wmap_sniffer import sniff, read
from wmap_common import DEFAULT_DB_PORT, \
    DEFAULT_SERVER_PORT, DEFAULT_MQ_PORT


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
        "-p", "--port", type=port, default=DEFAULT_SERVER_PORT,
        help="TCP port to run the web client on"
    )

    parser.add_argument(
        "--db-port", type=port, default=DEFAULT_DB_PORT,
        help="TCP port that MySQL is running on."
    )

    parser.add_argument(
        "--mq-port", type=port, default=DEFAULT_MQ_PORT,
        help="TCP port that RabbitMQ is running on."
    )

    return parser.parse_args()


def main():
    # TODO verify rabbitmq is running
    # TODO initialize database
    # TODO spin up server process

    args = parse_args()

    config = {
        "portno": args.port,
        "mq_port": args.mq_port,
        "db_port": args.db_port
    }

    if args.read:
        print("Reading pcap")
        read(args.read, config)
        print("Completed processing pcap.")
    else:
        sniff(args.interface, config)


if __name__ == "__main__":
    main()
