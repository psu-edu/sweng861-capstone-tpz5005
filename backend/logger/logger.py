import json
import logging
import datetime

# Sensitive keys to redact automatically
SENSITIVE_KEYS = {"password", "token", "access_token", "secret", "authorization", "secret_key", "custom_jwt_key"}

#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~#
class JSONFormatter(logging.Formatter):
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~#
    
    #-------------------------------------------#
    def format(self, record):
    #-------------------------------------------#
        # Create a logging struct to hold all 
        # required information
        log_obj = {
            "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage()
        }

        # Include request ID if available
        if hasattr(record, "request_id"):
            log_obj["request_id"] = record.request_id

        # Include extra fields if available
        if hasattr(record, "extra_data") and isinstance(record.extra_data, dict):
            clean_extra = self.sanitize_data(record.extra_data)
            log_obj.update(clean_extra)

        # Record any exceptions that occur
        if record.exc_info:
            log_obj["exception"] = self.formatException(record.exc_info)

        return json.dumps(log_obj)

    #-------------------------------------------#
    def sanitize_data(self, data: dict) -> dict:
    #-------------------------------------------#
        clean = {}
        for key, val in data.items():
            if any(sens in key.lower() for sens in SENSITIVE_KEYS):
                clean[key] = "[PRIVATE]"
            # For nested dictionaries
            elif isinstance(val, dict):
                clean[key] = self.sanitize_data(val)
            else:
                clean[key] = val
        return clean


# Initialize logger instance
handler = logging.StreamHandler()
handler.setFormatter(JSONFormatter())

logger = logging.getLogger("backend_logger")
logger.setLevel(logging.INFO)
logger.addHandler(handler)
logger.propagate = False


# Logging function
#-------------------------------------------#
def log_event(level: str, 
              event_name: str, 
              message: str, 
              request_id: str = None, 
              **extra):
#-------------------------------------------#
    log_record = logger.makeRecord(
        logger.name, getattr(logging, level.upper(), logging.INFO),
        fn="", lno=0, msg=message, args=(), exc_info=None
    )
    log_record.request_id = request_id or "N/A"
    log_record.extra_data = {"event": event_name, **extra}
    logger.handle(log_record)