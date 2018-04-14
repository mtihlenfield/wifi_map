import copy
import json

ACTION_CREATE = "create"
ACTION_UPDATE = "update"


def get_device_state(device_macs):
    """
    Returns the models of the devices as well as any connections
    related to the devices
    """
    pass


class State():
    """
    Represents the state of a collection of devices and their connections
    (i.e. not the state of all the networks, devices, and connections as whole
    """
    pass


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

    def to_json(self):
        """
        Returns the state change object in json format
        """
        dict_copy = copy.deepcopy(self.__dict__)

        if self.action == ACTION_CREATE:
            del dict_copy["updates"]

        return json.dumps(dict_copy)

