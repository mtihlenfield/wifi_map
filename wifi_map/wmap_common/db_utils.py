import peewee

from .constants import DB_FILE

db = None


def get_db():
    """
    Returns a database object
    """
    global db

    if not db:
        db = peewee.SqliteDatabase(DB_FILE, pragmas=(('foreign_keys', 'on'),))
        # db = peewee.SqliteDatabase(DB_FILE)

    return db


def create_mac_table():
    pass
