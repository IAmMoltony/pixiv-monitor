import settings
import pathlib
import os
import sys
import logging
import logging.handlers

def init_logging(config, debug_log):
    log_config = config.get("log", settings.DEFAULT_LOG_CONFIG)
    pathlib.Path(log_config["directory"]).mkdir(parents=True, exist_ok=True)

    string_level = log_config.get("level", "info")
    log_level = logging.INFO
    if debug_log:
        log_level = logging.DEBUG
    else:
        match string_level:
            case "debug":
                log_level = logging.DEBUG
            case "info":
                log_level = logging.INFO
            case "warning":
                log_level = logging.WARNING
            case "error":
                log_level = logging.ERROR
            case "critical":
                log_level = logging.CRITICAL

    logger = logging.getLogger()
    logger.setLevel(logging.DEBUG)

    formatter = logging.Formatter("[%(asctime)s]:%(levelname)s %(message)s")

    file_handler = logging.handlers.RotatingFileHandler(os.path.join(log_config["directory"], "pixiv-monitor.log"), encoding="utf-8", maxBytes=log_config["max_size"] * 1024 * 1024, backupCount=log_config["backup_count"])
    file_handler.setLevel(log_level)
    if debug_log:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.DEBUG)
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)

    file_handler.setFormatter(formatter)
    
    logger.addHandler(file_handler)

    logging.getLogger("urllib3").setLevel(logging.WARNING)
    logging.getLogger("requests").setLevel(logging.WARNING)
