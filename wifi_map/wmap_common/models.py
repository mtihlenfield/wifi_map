import peewee

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

    class Meta:
        database = get_db()


class Connection(peewee.Model):
    """
    An authentication/association relationship between two devices
    """
    station1 = peewee.ForeignKeyField(Station)
    station2 = peewee.ForeignKeyField(Station)
    connected = peewee.BooleanField()

    class Meta:
        primary_key = peewee.CompositeKey("station1", "station2")
        database = get_db()
