import math
import os
import random
from pathlib import Path

import jinja2 as j2

from canlib import config
from canlib.common import utils
from canlib.common.network import Network
from canlib.generators.lib.schema import BitSet, Enum, Field, Message, Number, Schema

BASE_DIR = Path(__file__).parent

TEMPLATE_PY = j2.Template((BASE_DIR / "template.py.j2").read_text())
TEST_TEMPLATE_PY = j2.Template((BASE_DIR / "test_template.py.j2").read_text())

schema_msgs = {}


def generate(network: Network, schema: Schema, output_path: Path):
    enums, bitsets = parse_schema(schema.types, network.name)

    utils.create_subtree(output_path)

    with open(output_path / config.PY_CAN_CONFIG_INCLUDE, "w+") as file:
        file.write(generate_canconfig_include(network.can_config))

    with open(output_path / config.PY_IDS_INCLUDE, "w+") as file:
        file.write(generate_ids_include(network))

    with open(output_path / f"{network.name}.py", "w+") as file:
        file.write(
            generate_py(network.name, schema.messages, schema.messages_size, enums, bitsets)
        )

    with open(output_path / "test.py", "w+") as file:
        file.write(generate_py_test(network.name, schema.messages))


def generate_py(filename, messages, messages_size, enums, bitsets):
    endianness_tag = "<" if config.IS_LITTLE_ENDIAN else ">"

    code = TEMPLATE_PY.render(
        filename=filename,
        enums=enums,
        bitsets=bitsets,
        messages=messages,
        messages_size=messages_size,
        len=len,
        endianness_tag=endianness_tag,
        params=params,
        python_type_name=python_type_name,
        utils=utils,
        isinstance=isinstance,
        Number=Number,
        fields_deserialization=fields_deserialization,
        fields_serialization=fields_serialization,
        already_timestamp=already_timestamp,
    )

    return code


def generate_py_test(filename, messages):
    code = TEST_TEMPLATE_PY.render(
        filename=filename,
        messages=messages,
        len=len,
        params=params,
        random_values=random_values,
        args=args,
        utils=utils,
    )

    return code


"""
    Utility functions used for template rendering
"""


def parse_schema(types, prefix):
    """
    Parses generic schema to a more Python friendly one

    The actions performed on the schema are the following:
    - Renaming structs and enums to camel case

    Args:
        schema:

    Returns:
        The structs and other custom types distilled from the schema
    """
    bitsets = []
    enums = []
    for type_name, custom_type in types.items():
        if isinstance(custom_type, Enum):
            custom_type.name = utils.to_camel_case(f"{prefix}_{type_name}", "_")
            enums.append(custom_type)

        if isinstance(custom_type, BitSet):
            custom_type.name = utils.to_camel_case(f"{prefix}_{type_name}", "_")
            bitsets.append(custom_type)

    return enums, bitsets


def packing_schema(name, msg):
    global schema_msgs
    schema_msgs[name] = {0: [], 1: [], 2: [], 3: [], 4: [], 5: [], 6: [], 7: []}
    schema = "<" if config.IS_LITTLE_ENDIAN else ">"
    for index, items in msg.items():
        if len(items) > 1:
            schema += "B"
        elif len(items) == 1:
            item = items[0]
            schema += struct_schema(item)
        schema_msgs[name][index] = schema

    return schema


def struct_schema(field: Field):
    if isinstance(field.type, BitSet):
        return "B" * math.ceil(field.type.size / 8)
    else:
        return struct_format(field.type)


def struct_format(number):
    if isinstance(number, Enum):
        return "B"
    elif isinstance(number, Number):
        match number.name:
            case "uint8":
                return "B"
            case "uint16":
                return "H"
            case "uint32":
                return "I"
            case "uint64":
                return "Q"
            case "int8":
                return "b"
            case "int16":
                return "h"
            case "int32":
                return "i"
            case "int64":
                return "q"
            case "float32":
                return "f"
            case "float64":
                return "d"
            case "bool":
                return "B"
            case _:
                raise NotImplementedError(
                    f"Can't convert {number.name} to format for python's pack unpack functions"
                )


def args(message: Message, variable: str):
    attributes = []
    for field in message.fields:
        attributes.append(
            f"{{{utils.to_camel_case(message.name,'_')}_{variable}.{field.name}}}"
        )
    return attributes


def pack_fields(msg: dict):
    fields = []
    for _, items in msg.items():
        if len(items) > 1:
            fields.append(
                " | ".join(
                    [f"self.{item.name} << {item.shift} & 255" for item in items]
                )
            )
        elif len(items) == 1:
            item = items[0]
            if item.shift == 0:
                if isinstance(item.type, BitSet):
                    for bytes in reversed(range(item.type.byte_size)):
                        fields.append(f"(int(self.{item.name},2) >> {bytes*8}) & 255")
                else:
                    fields.append(f"self.{item.name}")
            else:
                fields.append(f"self.{item.name} << {item.shift} & 255")
    return fields


def lookup_msg_index(msg_name, field_name, messages_size):
    for index in range(8):
        if field_name in [field.name for field in messages_size[msg_name][index]]:
            return index


def random_values(fields):
    values = []

    for field in fields:
        if isinstance(field.type, BitSet):
            value = f"{random.randint(0, (2 ** (field.bit_size)-1))}"
            values.append(value)
        elif isinstance(field.type, Enum):
            values.append(f"{random.randint(0, (2 ** (field.bit_size-1)))}")
        elif "uint" in field.type.name:
            values.append(f"{random.randint(0, (2 ** field.bit_size) - 1)}")
        elif "int" in field.type.name:
            values.append(
                f"{random.randint(-2 ** (field.bit_size-1), (2 ** (field.bit_size-1)) - 1)}"
            )
        elif "float" in field.type.name:
            values.append(f"{random.uniform(0, 1)}")
        else:
            values.append(f"{random.randint(0, 1)}")

    return values


def custom_unpack_schema(msg_name, msg, field_name):
    schema = "<" if config.IS_LITTLE_ENDIAN else ">"
    max_index = 0
    for index, items in msg.items():
        if field_name in [item.name for item in items]:
            if len(items) > 1:
                schema += "B"
                max_index = index + 2
            elif len(items) == 1:
                item = items[0]
                bytes = struct_schema(item)
                schema += bytes
                max_index = index + len(bytes) + 1
        else:
            schema += "x"
    return schema[0:max_index]


def params(fields):
    parameters = []
    parameters.append("self")
    for field in fields:
        parameters.append(f"{field.name}: {python_type_name(field)} = None")
    return parameters


def python_type_name(field: Field):
    if "int" in field.type.name:
        return "int"
    elif field.type.name == "float32" or field.type.name == "float64":
        return "float"
    elif isinstance(field.type, BitSet):
        return "bin"
    else:
        return field.type.name


def bitset_unpack(msg_name, msg, field, index):
    deserialized = []
    bytes = range(field.type.byte_size)
    reversed_bytes = reversed(bytes)
    for (byte, reversed_byte) in zip(bytes, reversed_bytes):
        if isinstance(field.type, BitSet):
            deserialized.append(
                f'(unpack("{ custom_unpack_schema(msg_name, msg, field.name) }", data[0:{ index+field.byte_size }])[{ byte }] << { reversed_byte*8 })'
            )
        else:
            deserialized.append(
                f'{python_type_name(field)}((unpack("{ custom_unpack_schema(msg_name, msg, field.name) }", data[0:{ index+field.byte_size }])[{ byte }] << { byte*8 }))'
            )
    return deserialized


def fields_serialization(message, messages_size):
    serialized_fields = []

    if len(message.fields) != 0:
        serialized_fields.append("data = bytearray()")
        msg = messages_size[message.name]
        serialized_fields.append(
            f"data.extend(pack(\"{packing_schema(message.name, msg)}\", {', '.join(pack_fields(msg)) }))"
        )
        serialized_fields.append("return data")
    else:
        serialized_fields.append("return bytearray()")

    return serialized_fields


def fields_deserialization(message, messages_size):
    deserialized_fields = []

    if len(message.fields) != 0:
        for field in message.fields:
            msg = messages_size[message.name]
            index = lookup_msg_index(message.name, field.name, messages_size)
            if isinstance(field.type, BitSet):
                deserialized_fields.append(
                    f"self.{field.name} = bin({' | '.join(bitset_unpack(message.name, msg, field, index))})"
                )
            elif field.shift == 0:
                deserialized_fields.append(
                    f'self.{field.name} = {python_type_name(field)}(unpack("{custom_unpack_schema(message.name, msg, field.name)}", data[0:{index+field.byte_size}])[0])'
                )
            else:
                deserialized_fields.append(
                    f'self.{field.name} = {python_type_name(field)}((unpack("{custom_unpack_schema(message.name, msg, field.name)}", data[0:{index+field.byte_size}])[0] & {field.bit_mask}) >> {field.shift})'
                )
    else:
        deserialized_fields.append("pass")

    return deserialized_fields


def already_timestamp(fields):
    if any(field.name == "timestamp" for field in fields):
        return True
    else:
        return False


def generate_ids_include(network: Network):
    header = ""
    header += "version = {0}\n\n".format(network.version)
    for topic_name, topic_id in network.topics.items():
        topic_messages = network.get_messages_by_topic(topic_name)
        header += f"# TOPIC {topic_name}\n"
        if topic_id is not None:
            header += f"TOPIC_{topic_name}_MASK = 0b{0b00000011111:>011b}\n"
            header += f"TOPIC_{topic_name}_FILTER = 0b{topic_id:>011b}\n"
        for message_name, message_contents in topic_messages.items():
            if "description" in message_contents:
                header += '"""\n'
                for line in message_contents["description"].split("\n"):
                    header += f"{line}\n"
                header += '"""\n'
            header += f"{network.name.upper()}_ID_{message_name} = 0b{message_contents['id']:>011b}\n"
        header += "\n"

    return header


def generate_canconfig_include(canconfig):
    if not canconfig:
        return ""
    options = canconfig["options"]
    version = canconfig["version"]
    header = ""
    header += "CANCONFIG_VERSION = {0}\n\n".format(version)
    for k, v in options.items():
        if isinstance(v, dict):
            header += "\n"
            for _k, _v in v.items():
                header += f"{_k.upper()} = {_v}"
                header += "\n"
        else:
            header += f"{k.upper()} = {v}\n"

    return header
