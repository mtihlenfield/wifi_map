import json

import pika

from . import constants

QUEUE_NAME = "wifi_map_update"

update_queue = None


class UpdateQueue():

    def __init__(self, connection):
        self.connection = connection
        self.channel = self.connection.channel()
        self.channel.queue_declare(queue=QUEUE_NAME)

    def put(self, update):
        self.channel.basic_publish(
            exchange="",
            routing_key=QUEUE_NAME,
            body=json.dumps(update)
        )

    def listen(self, update_cb):
        def callback(ch, method, properties, body):
            update_dict = json.loads(body)
            update_cb(update_dict)

        self.channel.basic_consume(
            callback,
            queue=QUEUE_NAME,
            no_ack=True
        )

        self.channel.start_consuming()

    def close(self):
        self.connection.close()

    @staticmethod
    def get_connection(mq_port=constants.DEFAULT_MQ_PORT):
        global update_queue

        if not update_queue:
            con_params = pika.ConnectionParameters(host="localhost", port=mq_port)
            con = pika.BlockingConnection(con_params)

            update_queue = UpdateQueue(con)

        return update_queue
