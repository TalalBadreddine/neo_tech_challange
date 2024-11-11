import logging
import os
import json
from logging.handlers import RotatingFileHandler
from django.conf import settings

class CustomFormatter(logging.Formatter):
    def format(self, record):

        message = f"{self.formatTime(record)} - {record.levelname} - {record.getMessage()}"


        etl_fields = [
            ('component', 'Component'),
            ('action', 'Action'),
            ('job_id', 'Job ID'),
            ('model', 'Model'),
            ('file_path', 'File Path'),
            ('chunk_size', 'Chunk Size'),
            ('chunk_index', 'Chunk Index'),
            ('row_count', 'Row Count'),
            ('records_created', 'Records Created'),
            ('records_failed', 'Records Failed'),
            ('validation_failed_count', 'Validation Failed Count'),
            ('validation_errors', 'Validation Errors'),
            ('statistics', 'Statistics'),
            ('error', 'Error')
        ]


        for field, label in etl_fields:
            if hasattr(record, field):
                value = getattr(record, field)
                if isinstance(value, (dict, list)):
                    message += f"\n{label}: {json.dumps(value, indent=2, default=str)}"
                else:
                    message += f"\n{label}: {value}"

        return message

def setup_logger():
    log_directory = os.path.join(settings.BASE_DIR, 'logs')
    os.makedirs(log_directory, exist_ok=True)

    logger = logging.getLogger('neo_challenge')
    logger.setLevel(logging.INFO)


    logger.handlers = []


    class InfoFilter(logging.Filter):
        def filter(self, record):
            return record.levelno == logging.INFO

    class WarningFilter(logging.Filter):
        def filter(self, record):
            return record.levelno == logging.WARNING

    class ErrorFilter(logging.Filter):
        def filter(self, record):
            return record.levelno == logging.ERROR


    handlers = {
        'info': RotatingFileHandler(
            os.path.join(log_directory, 'etl_info.log'),
            maxBytes=10*1024*1024,
            backupCount=5
        ),
        'warning': RotatingFileHandler(
            os.path.join(log_directory, 'etl_validation_warnings.log'),
            maxBytes=10*1024*1024,
            backupCount=5
        ),
        'error': RotatingFileHandler(
            os.path.join(log_directory, 'etl_error.log'),
            maxBytes=10*1024*1024,
            backupCount=5
        ),
        'console': logging.StreamHandler()
    }


    handlers['info'].addFilter(InfoFilter())
    handlers['warning'].addFilter(WarningFilter())
    handlers['error'].addFilter(ErrorFilter())


    handlers['info'].setLevel(logging.INFO)
    handlers['warning'].setLevel(logging.WARNING)
    handlers['error'].setLevel(logging.ERROR)
    handlers['console'].setLevel(logging.INFO)


    formatter = CustomFormatter(datefmt='%Y-%m-%d %H:%M:%S')
    for handler in handlers.values():
        handler.setFormatter(formatter)
        logger.addHandler(handler)

    return logger

logger = setup_logger()