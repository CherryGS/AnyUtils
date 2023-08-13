import logging

from rich.logging import RichHandler

from .logger import console_formatter

hldr = RichHandler()
hldr.setFormatter(console_formatter)
rootLogger = logging.getLogger("anyutils")
# rootLogger.addHandler(hldr)
