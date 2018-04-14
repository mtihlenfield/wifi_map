
from wmap_common import constants


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


def default_data_handler(pkt):
    """
    Default packet handler for data frames
    """
    pass


def default_ctrl_handler(pkt):
    """
    Default packet handler for control frames
    """
    pass


def default_mgmt_handler(pkt):
    """
    Default packet handler for management frames
    """
    pass


def probe_res_handler(pkt):
    pass


def beacon_handler(pkt):
    pass


def reassoc_handler(pkt):
    pass


def auth_handler(pkt):
    pass


def disconnect_handler(pkt):
    pass
