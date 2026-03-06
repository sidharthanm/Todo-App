import logging
import sys
from collections import deque
from pathlib import Path


class LastNMessagesFileHandler(logging.Handler):
    """Persist only the latest N formatted log messages to a file."""

    def __init__(self, filename: str, capacity: int = 500, encoding: str = "utf-8"):
        super().__init__()
        self.filename = Path(filename)
        self.capacity = capacity
        self.encoding = encoding
        self.filename.parent.mkdir(parents=True, exist_ok=True)
        self._messages = deque(maxlen=capacity)

        # Preload existing lines so restarts preserve the tail of logs.
        if self.filename.exists():
            with self.filename.open("r", encoding=self.encoding) as fh:
                for line in fh:
                    self._messages.append(line.rstrip("\n"))

    def emit(self, record: logging.LogRecord) -> None:
        try:
            message = self.format(record)
            self._messages.append(message)
            with self.filename.open("w", encoding=self.encoding) as fh:
                for line in self._messages:
                    fh.write(f"{line}\n")
        except Exception:
            self.handleError(record)


def setup_logging() -> None:
    formatter = logging.Formatter("%(asctime)s %(levelname)s %(message)s")

    stream_handler = logging.StreamHandler(sys.stdout)
    stream_handler.setFormatter(formatter)

    file_handler = LastNMessagesFileHandler("logs/app.log", capacity=500)
    file_handler.setFormatter(formatter)

    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO)
    root_logger.handlers.clear()
    root_logger.addHandler(stream_handler)
    root_logger.addHandler(file_handler)
