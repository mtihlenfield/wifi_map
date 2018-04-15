import time

import peewee
from playhouse.shortcuts import dict_to_model, model_to_dict

from .db_utils import get_db


class Network(peewee.Model):
    """
    An 802.11 based network (ESS)
    """
    class_name = "network"
    ssid = peewee.TextField(primary_key=True)
    channel = peewee.IntegerField(null=True)
    auth = peewee.TextField(null=True)
    enc = peewee.TextField(null=True)
    cipher = peewee.TextField(null=True)
    last_update = peewee.DateTimeField(default=time.time())

    class Meta:
        database = get_db()


class Station(peewee.Model):
    """
    A 802.11 capable device.
    """
    class_name = "station"
    mac = peewee.TextField(primary_key=True)
    is_ap = peewee.BooleanField(default=False, unique=False)
    ssid = peewee.ForeignKeyField(Network, null=True)
    manufacturer = peewee.TextField(null=True)
    last_update = peewee.DateTimeField(default=time.time())

    class Meta:
        database = get_db()


class Connection(peewee.Model):
    """
    An authentication/association relationship between two devices
    """
    class_name = "connection"
    conn_id = peewee.AutoField(primary_key=True, null=False, unique=True)
    # station1 = peewee.ForeignKeyField(Station)
    station1 = peewee.TextField(null=False)
    # station2 = peewee.ForeignKeyField(Station)
    station2 = peewee.TextField(null=False)
    connected = peewee.BooleanField()
    last_update = peewee.DateTimeField(default=time.time())

    class Meta:
        # primary_key = peewee.CompositeKey("station1", "station2")
        database = get_db()
        constraints = [
            peewee.SQL("UNIQUE (station1, station2)")
        ]


def to_dict(model):
    """
    Returns the model as a dict (trying to hide peewee)
    """
    return model_to_dict(model)


def from_dict(model_dict, model_class):
    """
    Converts a dict into a model (trying to hide peewee)
    """
    return dict_to_model(model_class, model_dict)
