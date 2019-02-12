import Logger


class BaseLogger(object):

    def __init__(self):
        self._logger = Logger.Logger(loglevel="info", log_to_file=True)
        self.log = lambda x: self._logger.do_message(x)
        self.errorlog = lambda x: self._logger.do_message(x, "error")
