import time
from wmap_common import constants
from wmap_common import state
from wmap_common.models import Station, Connection, Network
from wmap_common.models import to_dict as model_to_dict

BAD_MACS = [constants.MAC_BROADCAST, constants.MAC_NONE]


def get_handler(frame_type, frame_subtype):
    """
    Retrieves a packet handler function for the given frame type
    and subtype
    """
    if frame_type == constants.FRAME_TYPE_MGMT:
        return get_mgmt_handler(frame_subtype)
    elif frame_type == constants.FRAME_TYPE_CTRL:
        return get_ctrl_handler(frame_subtype)
    elif frame_type == constants.FRAME_TYPE_DATA:
        return get_data_handler(frame_subtype)
    else:
        raise ValueError("Invalid frame type")


def get_data_handler(subtype):
    """
    Retrieves a packet handler for the given data subtype
    """
    return default_data_handler


def get_mgmt_handler(subtype):
    """
    Retrieves a packet handler for the given management subtype
    """
    if subtype == constants.FRAME_SUBTYPE_PROBE_RES:
        return probe_res_handler
    elif subtype == constants.FRAME_SUBTYPE_BEACON:
        return beacon_handler
    elif subtype in [constants.FRAME_SUBTYPE_REASSOC_RES, constants.FRAME_SUBTYPE_REASSOC_REQ]:
        return reassoc_handler
    elif subtype == constants.FRAME_SUBTYPE_AUTH:
        return auth_handler
    elif subtype in [constants.FRAME_SUBTYPE_DISAS, constants.FRAME_SUBTYPE_DEUATH]:
        return disconnect_handler

    return default_mgmt_handler


def get_ctrl_handler(subtype):
    """
    Retrieves a packet handler for the given control subtype
    """
    return default_ctrl_handler


def default_data_handler(pkt, db_lock):
    """
    Default packet handler for data frames
    """
    state_changes = []

    to_ds = pkt.FCfield.__getattr__("to-DS")
    from_ds = pkt.FCfield.__getattr__("from-DS")

    addresses = {}

    if to_ds and from_ds:
        addresses[constants.ADDRESS_RCV] = pkt.addr1
        addresses[constants.ADDRESS_TRNSMT] = pkt.addr2
        addresses[constants.ADDRESS_DST] = pkt.addr3
        addresses[constants.ADDRESS_SRC] = pkt.addr4
    elif to_ds and not from_ds:
        addresses[constants.ADDRESS_BSSID] = pkt.addr1
        addresses[constants.ADDRESS_SRC] = pkt.addr2
        addresses[constants.ADDRESS_DST] = pkt.addr3
    elif not to_ds and from_ds:
        addresses[constants.ADDRESS_DST] = pkt.addr1
        addresses[constants.ADDRESS_BSSID] = pkt.addr2
        addresses[constants.ADDRESS_SRC] = pkt.addr3
    else:
        addresses[constants.ADDRESS_DST] = pkt.addr1
        addresses[constants.ADDRESS_SRC] = pkt.addr2
        addresses[constants.ADDRESS_BSSID] = pkt.addr3

    with db_lock:
        # print("Lock acquired")
        existing_stations = Station.select().where(Station.mac in addresses.values()).execute()
        existing_macs = [station.mac for station in existing_stations]

        # print("existing: ", existing_macs)

        new_stations = []
        new_macs = []
        for addr_type, mac in addresses.items():
            if (mac not in existing_macs) and (mac not in BAD_MACS) and (mac not in new_macs):
                new_station = Station(
                    mac=mac,
                    is_ap=(addr_type == constants.ADDRESS_BSSID)
                )

                new_stations.append(new_station)
                new_macs.append(mac)

                state_changes.append(state.StateChange(
                    state.ACTION_CREATE,
                    Station,
                    new_station
                ))

        # print("new: ", new_macs)
        if len(new_stations) > 0:
            station_dicts = [model_to_dict(station) for station in new_stations]
            Station.insert_many(station_dicts).execute()

        print("processed {}".format(time.time()))

    return state_changes


def default_ctrl_handler(pkt, db_lock):
    """
    Default packet handler for control frames
    """
    pass


def default_mgmt_handler(pkt, db_lock):
    """
    Default packet handler for management frames
    """
    pass


def probe_res_handler(pkt, db_lock):
    pass


def beacon_handler(pkt, db_lock):
    pass


def reassoc_handler(pkt, db_lock):
    pass


def auth_handler(pkt, db_lock):
    pass


def disconnect_handler(pkt, db_lock):
    pass


def is_from_ad_hoc(pkt):
    """
    Determines if a packet came from an ad hoc network
    """
    # I can't seem to get FCfield.toDS or to_DS to work. Maybe a bug in scapy?
    to_ds = pkt.FCfield.__getattr__("to-DS")
    from_ds = pkt.FCfield.__getattr__("from-DS")

    return not (to_ds or from_ds)






