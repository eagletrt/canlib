from pathlib import Path

import jinja2 as j2

from canlib.common.network import Network
from canlib.common.schema import Number, Schema

BASE_DIR = Path(__file__).parent

TEMPLATE_PROTO = j2.Template((BASE_DIR / "network.proto.j2").read_text())


def generate(network: Network, schema: Schema, output_path: Path):
    network_path = output_path / "network.proto"
    network_path.write_text(
        TEMPLATE_PROTO.render(
            network=network, schema=schema, protobuf_type=protobuf_type
        )
    )


PROTOBUF_TYPES = {
    "bool": "bool",
    "int8": "sint32",
    "uint8": "uint32",
    "int16": "sint32",
    "uint16": "uint32",
    "int32": "sint32",
    "uint32": "uint32",
    "int64": "sint64",
    "uint64": "uint64",
    "float32": "float",
    "float64": "double",
}


def protobuf_type(number: Number) -> str:
    return PROTOBUF_TYPES[number.base_type.name]
