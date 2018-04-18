import multiprocessing


class UpdateQueue():

    def __init__(self):
        self.queue = multiprocessing.Queue()
        # self.connection = connection
        # self.channel = self.connection.channel()
        # self.channel.queue_declare(queue=QUEUE_NAME)

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
