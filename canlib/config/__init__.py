from pathlib import Path

BASE_DIR = Path(__file__).parent

NETWORK_VALIDATION_SCHEMA = BASE_DIR / "schema/network.json"
CAN_CONFIG_VALIDATION_SCHEMA = BASE_DIR / "schema/can_config.json"

# IDS & masks
C_IDS_INCLUDE = "ids.h"
PY_IDS_INCLUDE = "ids.py"

# Utility tools & functions
C_UTILS_INCLUDE = "utils.h"
PY_UTILS_INCLUDE = "utils.py"

# CAN configuration
C_CAN_CONFIG_INCLUDE = "can_config.h"
PY_CAN_CONFIG_INCLUDE = "can_config.py"

# CUSTOMIZATION SETTINGS
IS_LITTLE_ENDIAN = True

COLUMNS_ORDER = [
    "name",
    "id",
    "network",
    "topic",
    "priority",
    "sending",
    "receiving",
    "interval",
    "contents",
    "description",
]
