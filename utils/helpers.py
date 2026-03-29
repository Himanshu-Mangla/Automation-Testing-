from datetime import datetime


def get_report_timestamp() -> str:
    """Returns DD-MM-YYYY HH:MM:SS — used in report names."""
    return datetime.now().strftime("%d-%m-%Y %H:%M:%S")


def get_file_timestamp() -> str:
    """Returns DD-MM-YYYY_HH-MM-SS — safe for file names."""
    return datetime.now().strftime("%d-%m-%Y_%H-%M-%S")
