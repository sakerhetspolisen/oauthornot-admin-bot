from multiprocessing import Queue, cpu_count
from threading import Thread
from sessions import GithubAdminSession
from task import Task


class DistributedTaskQueue():
    def __init__(self, nOfWorkers, logger) -> None:
        self.logger = logger
        # Create the two queues to hold the data and the IDs for the selenium workers
        self.dataQueue = Queue()
        self.workerQueue = Queue()
        self.queuedIDs = set()
        self.IDsCurrentlyProcessing = set()
        self.completedIDs = set()
        # self.workerIDs = list(range(cpu_count()))
        self.workerIDs = list(range(nOfWorkers))
        self.workers = {i: GithubAdminSession(
            i, self.logger) for i in self.workerIDs}

        for workerID in self.workerIDs:
            self.workerQueue.put(workerID)

        self.initListeners()

    def initListeners(self):
        # Create one new queue listener thread per selenium worker and start them
        self.logger.info("Starting selenium background processes")
        self.processes = [Thread(target=self.queueListener,
                                 args=(self.dataQueue, self.workerQueue)) for _ in self.workerIDs]

        for p in self.processes:
            p.daemon = True
            p.start()

    def add(self, url):
        task = Task(url)
        self.dataQueue.put(task)
        self.queuedIDs.add(task.id)
        return task

    def status(self, taskID):
        if taskID in self.queuedIDs:
            return "queued"
        elif taskID in self.IDsCurrentlyProcessing:
            return "processing"
        elif taskID in self.completedIDs:
            return "completed"
        else:
            return "not found"

    def clear(self):
        self.dataQueue.queue.clear()
        self.queuedIDs.clear()

    def terminateWhenComplete(self):
        # Wait for all selenium queue listening processes to complete, this happens when the queue listener returns
        self.logger.info("Waiting for Queue listener threads to complete")
        for p in self.processes:
            p.join()

        # Quit all the web workers elegantly in the background
        self.logger.info("Tearing down web workers")
        for b in self.workers.values():
            b.quit()

    def terminate(self):
        # Quit all the web workers elegantly in the background
        self.logger.info("Tearing down web workers")
        for b in self.workers.values():
            b.quit()

    def queueListener(self, dataQueue, workerQueue):
        """
        Monitor a data queue and assign new pieces of data to any available web workers to action
        :param data_queue: The python FIFO queue containing the data to run on the web worker
        :type data_queue: Queue
        :param worker_queue: The queue that holds the IDs of any idle workers
        :type worker_queue: Queue
        :rtype: None
        """
        self.logger.info("Selenium func worker started")
        while True:
            currentData = dataQueue.get()
            if currentData == 'STOP':
                # If a stop is encountered then kill the current worker and put the stop back onto the queue
                # to poison other workers listening on the queue
                self.logger.warning("STOP encountered, killing worker thread")
                dataQueue.put(currentData)
                break
            else:
                self.logger.info(
                    f'Got the item {currentData.url} on the data queue')
            # Get the ID of any currently free workers from the worker queue
            workerID = workerQueue.get()
            worker = self.workers[workerID]

            self.queuedIDs.remove(currentData.id)
            self.IDsCurrentlyProcessing.add(currentData.id)

            # Assign current worker and current data to your selenium function
            worker.doTask(currentData)

            self.IDsCurrentlyProcessing.remove(currentData.id)
            self.completedIDs.add(currentData.id)

            # Put the worker back into the worker queue as  it has completed it's task
            workerQueue.put(workerID)
        return
