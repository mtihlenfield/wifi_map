import copy

import peewee
import scapy.layers.dot11 as dot11

from wmap_common import constants
from wmap_common import state
from wmap_common import db_utils
from wmap_common.models import Station, Connection, Network
from wmap_common.models import to_dict as model_to_dict


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
    if subtype == constants.FRAME_SUBTYPE_PROBE_RES \
            or subtype == constants.FRAME_SUBTYPE_BEACON:
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


def default_data_handler(pkt, time_recieved, locks):
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

    # clear out bad addresses
    addrs_copy = copy.copy(addresses)
    for addr_type, mac in addresses.items():
        if not safe_mac(mac) or mac is None:
            del addrs_copy[addr_type]
    addresses = addrs_copy

    with locks["station"]:
        existing_stations = Station.select().where(Station.mac in addresses.values()).execute()
        existing_macs = [station.mac for station in existing_stations]

        new_stations = []
        updated_macs = []
        new_macs = []
        for addr_type, mac in addresses.items():
            is_ap = addr_type == constants.ADDRESS_BSSID
            if mac in existing_macs:
                for sta in existing_stations:
                    # we've got an existing AP that hasn't been marked as one yet.
                    if sta.mac == mac and not sta.is_ap and is_ap:
                        sta.is_ap = True
                        updated_macs.append(mac)

                        state_changes.append(state.StateChange(
                            state.ACTION_UPDATE,
                            Station,
                            sta,
                            updates=["is_ap"],
                        ))
                    break

            elif mac not in new_macs:
                new_macs.append(mac)
                new_station = Station(mac=mac, is_ap=is_ap)
                new_stations.append(new_station)

                state_changes.append(state.StateChange(
                    state.ACTION_CREATE,
                    Station,
                    new_station
                ))

        if len(new_stations) > 0:
            station_dicts = [model_to_dict(station) for station in new_stations]
            Station.insert_many(station_dicts).execute()

        if len(updated_macs) > 0:
            Station.update(is_ap=True).where(Station.mac in updated_macs).execute()

    poss_cons = []
    poss_con_pairs = []

    # Determining what connections I should have:
    if constants.ADDRESS_BSSID in addresses:  # normal AP to client connection
        for addr_type, addr in addresses.items():
            if not addr_type == constants.ADDRESS_BSSID and addr != addresses[constants.ADDRESS_BSSID]:
                # connection.station1 and connection.station2 are sorted alphabetically
                sorted_addrs = sorted((addr, addresses[constants.ADDRESS_BSSID]))
                poss_con_pairs.append(sorted_addrs)
    elif constants.ADDRESS_BSSID not in addresses and constants.ADDRESS_TRNSMT not in addresses \
            and constants.ADDRESS_DST in addresses and constants.ADDRESS_RCV in addresses:  # ad hoc connection
        sorted_addrs = sorted((addresses[constants.ADDRESS_DST], addresses[constants.ADDRESS_SRC]))
        poss_con_pairs.append(sorted_addrs)
    elif constants.ADDRESS_TRNSMT in addresses:  # WDS connection
        # if one of the devices is an access point then create connections to it.
        # TODO implement this
        pass

    for pair in poss_con_pairs:
        poss_cons.append(Connection(
            station1=pair[0],
            station2=pair[1],
            connected=True,
            last_update=time_recieved
        ))

    # TODO this lock essenatially makes having multiple workers useless
    with locks["connection"]:
        existing_cons_query = Connection.select().where(
            Connection.station1 in addresses.values() or
            Connection.station2 in addresses.values()
        )

        existing_cons = existing_cons_query.execute()

        # TODO this is bad... so bad...
        new_cons = []
        for poss_con in poss_cons:
            needs_created = True
            for con in existing_cons:
                if poss_con.station1 == con.station1 and \
                        poss_con.station2 == con.station2:

                    needs_created = False

            if needs_created:
                new_cons.append(poss_con)
                state_changes.append(state.StateChange(
                    state.ACTION_CREATE,
                    Connection,
                    poss_con
                ))

        # Need to create a state change if the con wasn't already connected
        for con in existing_cons:
            if con.last_update < time_recieved and not con.connected:
                state_changes.append(state.StateChange(
                    state.ACTION_UPDATE,
                    Connection,
                    con
                ))

        with db_utils.get_db().atomic():
            if len(new_cons) > 0:
                con_dicts = [model_to_dict(con) for con in new_cons]
                Connection.insert_many(con_dicts).execute()

            # Every connection needs at least its last_update param reset but it
            # should also be connected
            existing_ids = [con.conn_id for con in existing_cons]
            Connection \
                .update(last_update=time_recieved, connected=True) \
                .where(Connection.conn_id in existing_ids) \
                .execute()

    return state_changes


def default_ctrl_handler(pkt, time_recieved, locks):
    """
    Default packet handler for control frames
    """
    return []


def default_mgmt_handler(pkt, time_recieved, locks):
    """
    Default packet handler for management frames
    """
    return []


def beacon_handler(pkt, time_recieved, locks):
    state_changes = []
    if pkt.haslayer(dot11.Dot11Elt):
        dot11_layer = pkt
        elt = pkt.getlayer(dot11.Dot11Elt)

        network_info = {}
        while elt:
            if elt.ID == 0 and elt.info.decode("utf-8") != "":
                network_info["ssid"] = elt.info.decode("utf-8")
            elif elt.ID == 4:
                network_info["channel"] = elt.info

            # everything else would take too much time to parse...
            elt = elt.payload.getlayer(dot11.Dot11Elt)

        # We should probably save some info...
        if "ssid" in network_info and network_info["ssid"]:
            with locks["network"]:
                try:
                    network = Network.get_by_id(network_info["ssid"])
                    if network.ssid != network_info["ssid"]:
                        network.ssid = network_info["ssid"]
                        network.save()

                        state_changes.append(state.StateChange(
                            state.ACTION_CREATE,
                            Network,
                            network,
                            upates=["ssid"]
                        ))
                except peewee.DoesNotExist:
                    network = Network.create(
                        ssid=network_info["ssid"],
                        channel=network_info["channel"] if "channel" in network_info else None
                    )
                    network.save()
                    state_changes.append(state.StateChange(
                        state.ACTION_CREATE,
                        Network,
                        network
                    ))

        # check for device and make sure is_ap is set
        if not safe_mac(dot11_layer.addr2):
            return state_changes

        with locks["station"]:
            try:
                sta = Station.get_by_id(dot11_layer.addr2)
                if not sta.is_ap:
                    sta.is_ap = True
                    sta.save(force_insert=True)

                    state_changes.append(state.StateChange(
                        state.ACTION_UPDATE,
                        Station,
                        sta,
                        updates=["is_ap"]
                    ))
            except peewee.DoesNotExist:
                sta = Station(
                    mac=dot11_layer.addr2,
                    is_ap=True,
                    ssid=network_info["ssid"] if "ssid" in network_info else None
                )
                sta.save(force_insert=True)

                state_changes.append(state.StateChange(
                    state.ACTION_CREATE,
                    Station,
                    sta
                ))

    return state_changes


def reassoc_handler(pkt, time_recieved, ldb_lock):
    return []


def auth_handler(pkt, time_recieved, ldb_lock):
    return []


def disconnect_handler(pkt, time_recieved, ldb_lock):
    return []

def safe_mac(mac):
    for start in constants.MAC_RES_START:
        if mac.lower().startswith(start):
            return False

    return mac not in constants.UNSAFE_MACS
