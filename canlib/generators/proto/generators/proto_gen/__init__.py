import os
from pathlib import Path

import jinja2 as j2

from canlib.common import utils
from canlib.generators.proto.schema import BitSet, Enum, Schema

BASE_DIR = Path(__file__).parent

PROTO_TEMPLATE = BASE_DIR / "template.proto.j2"


def generate(schema: Schema, filename, output_path):
    enums, structs = parse_schema(schema)
    utils.create_subtree(output_path)
    with open(f"{output_path}/{filename}.proto", "w") as f:
        f.write(generate_proto(filename, enums, structs))


def generate_proto(filename, enums, structs):
    with open(PROTO_TEMPLATE, "r") as f:
        skeleton_py = f.read()

    code = j2.Template(skeleton_py).render(
        filename=filename,
        enums=enums,
        structs=structs,
        utils=utils,
        isinstance=isinstance,
        BitSet=BitSet,
        Enum=Enum,
        enumerate=enumerate,
    )

    return code


def parse_schema(schema: Schema):
    enums = {k: v for k, v in schema.types.items() if isinstance(v, Enum)}
    structs = schema.structs

    return enums, structs
