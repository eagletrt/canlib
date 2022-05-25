import os
import re
from pathlib import Path

import jinja2 as j2

from canlib.common import utils
from canlib.common.network import Network
from canlib.generators.proto.schema import BitSet, Enum, Number, Schema

BASE_DIR = Path(__file__).parent

UTILS_CPP_TEMPLATE_ = BASE_DIR / "network_utils_template.h.j2"
UTILS_PYTHON_TEMPLATE_ = BASE_DIR / "network_utils_template.py.j2"


def generate_utils(schema: Schema, network: Network, filename: str, utils_dir_network: str) -> None:
    types, structs, messages = parse_schema(schema, network)
        

    with open(f"{utils_dir_network}/cpp/{filename}_utils.h", "w") as f:
        f.write(generate_cpp_utils(filename, types, structs, messages))
    print(f"Generated {filename}_utils.h into {utils_dir_network}/cpp")

    with open(f"{utils_dir_network}/python/{filename}_utils.py", "w") as f:
        f.write(generate_python_utils(filename, messages))
    print(f"Generated {filename}_utils.py into {utils_dir_network}/python")


def generate_cpp_utils(filename, types, structs, messages):
    with open(UTILS_CPP_TEMPLATE_, "r") as f:
        skeleton_py = f.read()

    code = j2.Template(skeleton_py).render(
        filename=filename,
        types=types,
        structs=structs,
        messages=messages,
        utils=utils,
        isinstance=isinstance,
        BitSet=BitSet,
        Enum=Enum,
        Number=Number,
    )

    return code


def generate_python_utils(filename, messages):
    with open(UTILS_PYTHON_TEMPLATE_, "r") as f:
        skeleton_py = f.read()

    code = j2.Template(skeleton_py).render(
        filename=filename, messages=messages, utils=utils
    )

    return code


def parse_schema(schema: Schema, network: Network):
    types = schema.types
    structs = schema.structs
    messages = {}
    for message_name, message in network.messages.items():
        if not message_name in messages:
            messages[message_name] = []
        messages[message_name].append(message["id"])

    return types, structs, messages
