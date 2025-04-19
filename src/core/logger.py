import logging

from rich.logging import RichHandler


def init_logger():
    logging.basicConfig(
        level=logging.DEBUG,
        format="%(name)s | %(message)s",
        datefmt="[%X]",
        handlers=[RichHandler(markup=True, show_path=True)],
    )
