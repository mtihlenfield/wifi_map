import json

import peewee
from playhouse.shortcuts import dict_to_model, model_to_dict

from .db_utils import get_db


class Network(peewee.Model):
    """
    An 802.11 based network (ESS)
    """
    ssid = peewee.TextField(primary_key=True)
    channel = peewee.IntegerField()
    auth = peewee.TextField()
    enc = peewee.TextField()
    cipher = peewee.TextField()
    last_update = peewee.DateTimeField()

    class Meta:
        database = get_db()


class Station(peewee.Model):
    """
    A 802.11 capable device.
    """
    mac = peewee.TextField(primary_key=True)
    is_ap = peewee.BooleanField()
    ssid = peewee.ForeignKeyField(Network)
    manufacturer = peewee.TextField()
    last_update = peewee.DateTimeField()

    class Meta:
        database = get_db()


class Connection(peewee.Model):
    """
    An authentication/association relationship between two devices
    """
    station1 = peewee.ForeignKeyField(Station)
    station2 = peewee.ForeignKeyField(Station)
    connected = peewee.BooleanField()
    last_update = peewee.DateTimeField()

    class Meta:
        primary_key = peewee.CompositeKey("station1", "station2")
        database = get_db()


def to_json(model):
    """
    Returns the model as a json_string
    """
    model_dict = model_to_dict(model)
    return json.dumps(model_dict)


def from_json(json_model, model_class):
    """
    Converts a json string into a model
    """
    model_dict = json.loads(json_model)
    return dict_to_model(model_class, model_dict)

