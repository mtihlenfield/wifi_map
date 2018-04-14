import os

DEFAULT_DB_PORT = 3306  # MySQL
DEFAULT_MQ_PORT = 5672  # rabbit mq
DEFAULT_SERVER_PORT = 6363
DEFAULT_CONFIG = {
    "portno": DEFAULT_SERVER_PORT,
    "mq_port": DEFAULT_MQ_PORT,
    "db_port": DEFAULT_DB_PORT
}

DB_DIR = os.path.join(
    os.path.expanduser("~"),
    ".wifi_map",
)

DB_FILE = os.path.join(
    DB_DIR,
    "wifi_map.db"
)
