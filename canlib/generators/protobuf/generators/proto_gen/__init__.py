import os

import jinja2 as j2

from canlib.common import utils
from canlib.generators.protobuf.schema import BitSet, Enum, Schema

__PROTO_TEMPLATE_ = os.path.dirname(__file__) + "/template.proto.j2"


def generate(schema: Schema, filename, output_path):
    enums, structs = __parse_schema(schema)
    utils.create_subtree(output_path)
    with open(f"{output_path}/{filename}.proto", "w") as f:
        f.write(__generate_proto(filename, enums, structs))


def __generate_proto(filename, enums, structs):
    with open(__PROTO_TEMPLATE_, "r") as f:
        skeleton_py = f.read()

    code = j2.Template(skeleton_py).render(
        filename=filename,
        enums=enums,
        structs=structs,
        utils=utils,
        isinstance=isinstance,
        BitSet=BitSet,
        Enum=Enum,
        # Type=Type,
        enumerate=enumerate,
        # range=range,
        # zip=zip,
        # utils=utils
    )

    return code


def __parse_schema(schema: Schema):
    enums = {k: v for k, v in schema.types.items() if isinstance(v, Enum)}
    structs = schema.structs
    # print([struct.fields for struct in schema.structs])

    return enums, structs
