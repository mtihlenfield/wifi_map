import multiprocessing

# QUEUE_NAME = "wifi_map_update"


class UpdateQueue():

    instance = None

    def __init__(self):
        self.queue = multiprocessing.Queue()
        # self.connection = connection
        # self.channel = self.connection.channel()
        # self.channel.queue_declare(queue=QUEUE_NAME)

    @staticmethod
    def get():
        if not UpdateQueue.instance:
            UpdateQueue.instance = UpdateQueue()

        return UpdateQueue.instance

    def put(self, update):
        self.queue.put(update, block=False)
        # self.channel.basic_publish(
        #     exchange="",
        #     routing_key=QUEUE_NAME,
        #     body=json.dumps(update)
        # )

    def listen(self, update_cb):
        while True:
            update = self.queue.get()
            update_cb(update)

        # def callback(ch, method, properties, body):
        #     update_dict = json.loads(body)
        #     update_cb(update_dict)
        # self.channel.basic_consume(
        #     callback,
        #     queue=QUEUE_NAME,
        #     no_ack=True
        # )

        # self.channel.start_consuming()

    # def close(self):
    #     self.connection.close()

    # @staticmethod
    # def get_connection(mq_port=constants.DEFAULT_MQ_PORT):
    #     global update_queue

    #     if not update_queue:
    #         con_params = pika.ConnectionParameters(host="localhost", port=mq_port)
    #         con = pika.BlockingConnection(con_params)

    #         update_queue = UpdateQueue(con)

    #     return update_queue
