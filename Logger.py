import logging
import os
import io
from TempFileName import TempFileName
import datetime
from Singleton import Singleton


class Logger(object, metaclass=Singleton):

    LEVELS = {'debug': logging.DEBUG,
              'info': logging.INFO,
              'warning': logging.WARNING,
              'error': logging.ERROR,
              'critical': logging.CRITICAL}

    def __init__(self, loglevel="error", log_to_file=False, location=None):
        """
                Set up logging to either a permanent file location or in memory
                params: log_to_file: True or False
                """
        self._log_directory = None
        self._log_file = None

        self.log_level = loglevel if loglevel in self.LEVELS else "info"
        if log_to_file:
            if location:
                self._log_directory = location  # else
                self._log_file = os.path.join(self._log_directory,
                                              f'_ags_{datetime.datetime.now().strftime("%Y%m%d_%H%M%S%f")}.log')
            else:
                self._log_file = TempFileName.generate_temporary_file_name(suffix=".log")

            logging.basicConfig(filename=self._log_file, level=self.LEVELS[self.log_level], format='%(asctime)s - %(levelname)s - %(message)s')
            logging.captureWarnings(True)
        else:
            # set the logging to the console and a string buffer we can query later

            self._stream = io.StringIO()
            self._stream_handler = logging.StreamHandler(self._stream)
            self._stream_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
            logging.getLogger().setLevel(self.LEVELS[self.log_level])
            logging.getLogger().addHandler(self._stream_handler)
            con = logging.StreamHandler()
            con.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
            con.setLevel(self.LEVELS[self.log_level])
            logging.getLogger().addHandler(con)

        self.do_message(f"log level set to: {self.log_level}", "info")
        #self.do_message("Log dir:" + str(self._log_directory) + ", Log file:" + str(self._log_file), "debug")

    def __str__(self):
        """ string support """
        if self._log_file:
            return self._log_file
        return "Logging to console/memory"

    def __repr__(self):
        """ pprint support """
        if self._log_file:
            return self._log_file
        return "Logging to console/memory"

        # noinspection PyMethodMayBeStatic

    def close_log(self):
        log = logging.getLogger()
        x = list(log.handlers)
        for i in x:
            try:
                log.removeHandler(i)
                i.flush()
                i.close()
            except Exception:
                pass

    @property
    def file_as_string(self):
        a_str = None
        with open(self.log_file, 'r') as log_file:
            a_str = log_file.read()
        return a_str

    @property
    def log_directory(self):
        return self._log_directory

    @property
    def log_file(self):
        return self._log_file

    @property
    def in_memory_log(self):
        if hasattr(self, '_stream_handler'):
            try:
                self._stream_handler.flush()
                return self._stream.getvalue()
            except Exception as err:
                return str(err)
        return ""

    # noinspection PyMethodMayBeStatic
    def do_message(self, message_string, level="info"):
        """
        Write to log method (file or memory)
        params: level: level to write (default info) - one of:
                       critical,error,warn,info,debug
        """
        message_string = str(message_string)
        if level == "critical":
            logging.critical(message_string)
        elif level == "error" or level == "err":
            logging.error("*"*50)
            logging.error(message_string)
            logging.exception("Traceback as follows:")
            logging.error("*"*50)
        elif level == "warn":
            logging.warning(message_string)
        elif level == "info":
            logging.info(message_string)
        elif level == "debug":
            logging.debug(message_string)
        else:
            print(message_string)

