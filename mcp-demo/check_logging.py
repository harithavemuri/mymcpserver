import logging
import os

# Check if log file exists and is writable
log_file = 'mcp_server.log'
print(f"Checking log file: {os.path.abspath(log_file)}")
print(f"File exists: {os.path.exists(log_file)}")
print(f"File writable: {os.access(os.path.dirname(os.path.abspath(log_file)), os.W_OK)}")

# Test logging
print("\nTesting logging...")
logger = logging.getLogger('test_logger')
logger.setLevel(logging.INFO)
handler = logging.FileHandler(log_file)
handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
logger.addHandler(handler)

logger.info("This is a test log message")
print("Test log message written. Check the log file for the test message.")
