import copy
import json

from . import models

ACTION_CREATE = "create"
ACTION_UPDATE = "update"


# def get_devices_state(addr1, addr2, addr3, addr4=None):
#     """
#     Returns the models of the devices as well as any connections
#     related to the devices
#     """
#     addrs = [addr1, addr2, addr3]
#     if addr4:
#         addrs.append(addr4)
#
#     stations = (Station.select().where(Station.mac in addrs))
#     connections = (Connections.select().where(
#         (Connection.addr1 in addrs) or
#         (Connection.addr2 in addrs)
#     ))


class StateChange():
    """
    Represents a change in state for a single object.
    """

    def __init__(self, action, objtype, obj, updates=[]):
        assert(action in [ACTION_CREATE, ACTION_UPDATE])
        self.action = action
        self.objtype = objtype
        self.obj = obj

        # this is just a list of keys that were changed. For example
        # if the change is a disconnected connection then
        # updates=['connected']
        self.updates = updates

    def to_dict(self):
        """
        Returns the state change object as a dict
        """
        dict_copy = {
            "action": self.action,
            "objtype": self.objtype.class_name,
            "obj": models.to_dict(self.obj)
        }

        return dict_copy
