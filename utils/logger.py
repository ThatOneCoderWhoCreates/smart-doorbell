import logging
import yaml
import os

with open("config.yaml") as f:
    config = yaml.safe_load(f)

log_file = config["logging"]["file"]

# Ensure log directory exists
os.makedirs(os.path.dirname(log_file), exist_ok=True)

logging.basicConfig(
    filename=log_file,
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s"
)

def log(msg):
    logging.info(msg)
<<<<<<< HEAD
    print(msg)
=======
>>>>>>> bae2011394891f3509e14bf25e50836c364789e0
