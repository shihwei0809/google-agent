import logging


def configure_logging() -> None:
    """Configure a concise application-wide logging format."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    )
