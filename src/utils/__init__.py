"""Utility modules for logging, metrics, and other helpers"""

# Import utility functions from parent utils.py module
# This allows backward compatibility with imports like "from src.utils import get_iso_timestamp"
import sys
import os
_parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _parent_dir not in sys.path:
    sys.path.insert(0, _parent_dir)

# Import from utils.py in parent src/ directory
import importlib.util
_utils_path = os.path.join(_parent_dir, 'utils.py')
if os.path.exists(_utils_path):
    spec = importlib.util.spec_from_file_location("utils", _utils_path)
    utils_module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(utils_module)
    
    # Re-export functions
    get_iso_timestamp = utils_module.get_iso_timestamp
    generate_uuid = utils_module.generate_uuid
    encode_cursor = utils_module.encode_cursor
    decode_cursor = utils_module.decode_cursor
    validate_payload_size = utils_module.validate_payload_size
    format_not_found_error = utils_module.format_not_found_error
    format_conflict_error = utils_module.format_conflict_error
    format_validation_error = utils_module.format_validation_error
else:
    # Fallback: define minimal stubs if utils.py doesn't exist
    raise ImportError("src/utils.py not found")

from src.utils.logging import get_logger, set_request_context, clear_request_context

__all__ = [
    'get_logger', 
    'set_request_context', 
    'clear_request_context',
    'get_iso_timestamp',
    'generate_uuid',
    'encode_cursor',
    'decode_cursor',
    'validate_payload_size',
    'format_not_found_error',
    'format_conflict_error',
    'format_validation_error'
]

# Metrics will be imported when implemented
# from src.utils.metrics import CloudWatchMetrics

