import logging

def get_logger(name=''):
    import logging
    import os
    import sys
    filedir = "logs"
    filename = "{}/{}.log".format(filedir, os.getenv('HOSTNAME'))
    os.makedirs(filedir, exist_ok=True)
    filehandlers = [
        logging.FileHandler(filename),
        logging.StreamHandler()
    ]
    logging.basicConfig(
        format="%(asctime)s [%(threadName)-12.12s] [%(levelname)-5.5s]  %(message)s",
        handlers=filehandlers,
        level=logging.DEBUG
    )
    return logging.getLogger(name)
