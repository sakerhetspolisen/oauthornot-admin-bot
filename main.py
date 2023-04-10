import argparse
from loggerConfig import logger, logging, LogFormatter
from queues import DistributedTaskQueue
import signal
import sys
from webserver import getWebServer
from flask.logging import default_handler

N_OF_WORKERS = 1


def main():
    parser = argparse.ArgumentParser(
        description="Bot that simulates the admin user of an OAuth client.")
    parser.add_argument("--log", dest="logLevel", choices=[
                        "DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"], help="Set the logging level", default="WARNING")
    parser.add_argument("-p", "--port", dest="port",
                        help="Which port the web server should run on", default=5000)
    parser.add_argument("--host", dest="host",
                        help="Which host the web server should run on", default="localhost")
    parser.add_argument("--server-only", dest="webServerOnly",
                        help="Start only the Flask server, skip Selenium. NOTE: API will not be functional.", action='store_true')

    args = parser.parse_args()
    logger.setLevel(args.logLevel)

    ch = logging.StreamHandler()
    ch.setLevel(logging.DEBUG)
    ch.setFormatter(LogFormatter())
    logger.addHandler(ch)

    if args.webServerOnly:
        taskQueue = None
    else:
        taskQueue = DistributedTaskQueue(N_OF_WORKERS, logger)

    def signal_handler(sig, frame):
        print("Exiting...")
        taskQueue.add("STOP")
        taskQueue.terminateWhenComplete()
        sys.exit(0)

    signal.signal(signal.SIGINT, signal_handler)

    webServer = getWebServer(taskQueue)
    webServer.logger.removeHandler(default_handler)
    webServer.run(port=args.port, host=args.host, debug=True)

    taskQueue.terminateWhenComplete()


if __name__ == "__main__":
    main()
