import random
from pathlib import Path

import jinja2 as j2

from canlib import config
from canlib.common import utils
from canlib.common.network import Network
from canlib.generators.lib.schema import BitSet, Enum, Number, Schema

BASE_DIR = Path(__file__).parent

TEMPLATE_H = j2.Template((BASE_DIR / "template.h.j2").read_text())
TEST_TEMPLATE_C = j2.Template((BASE_DIR / "test_template.c.j2").read_text())

TEMPLATE_IDS_H = j2.Template((BASE_DIR / "ids.h.j2").read_text())
TEMPLATE_UTILS_H = j2.Template((BASE_DIR / "utils.h.j2").read_text())


def generate(network: Network, schema: Schema, output_path: Path):
    """
    Generates the source files in the specified output path

    Args:
        schema:
        output_path:
        filename:
    """
    enums, bitsets = parse_schema(schema.types, network.name)

    utils.create_subtree(output_path)
    with open(output_path / config.C_IDS_INCLUDE, "w+") as file:
        file.write(generate_ids_include(network))

    with open(output_path / config.C_UTILS_INCLUDE, "w+") as file:
        file.write(generate_utils_include(network, schema))

    with open(output_path / config.C_CAN_CONFIG_INCLUDE, "w+") as file:
        file.write(generate_canconfig_include(network.can_config, network.name))

    with open(output_path / f"{network.name}.h", "w") as file:
        file.write(
            generate_h(
                network.name, schema.messages, schema.messages_size, enums, bitsets
            )
        )

    with open(output_path / "test.c", "w") as file:
        file.write(generate_test_c(network.name, schema.messages))


def generate_h(filename, messages, messages_size, enums, bitsets):
    """
    Generates C header file
    """
    endianness_tag = "LITTLE_ENDIAN" if config.IS_LITTLE_ENDIAN else "BIG_ENDIAN"

    code = TEMPLATE_H.render(
        bitsets=bitsets,
        enums=enums,
        messages=messages,
        messages_size=messages_size,
        endianness_tag=endianness_tag,
        filename=filename,
        casts=casts,
        fields_serialization=fields_serialization,
        fields_deserialization=fields_deserialization,
        utils=utils,
        already_timestamp=already_timestamp,
        parameters=parameters,
    )

    return code


def generate_test_c(filename, messages):
    """
    Generates C source file for tests
    """
    code = TEST_TEMPLATE_C.render(
        messages=messages,
        filename=filename,
        len=len,
        printf_cast=printf_cast,
        printf_arguments_cast=printf_arguments_cast,
        random_values=random_values,
        utils=utils,
        buffer_size=buffer_size,
    )

    return code


def parse_schema(types, prefix):
    """
    Parses generic schema to a more C friendly one

    The actions performed on the schema are the following:
    - Prefixing structs and enums' name to avoid conflicts with other libraries

    Args:
        schema:
        prefix:

    Returns:
        The structs and other custom types distilled from the schema
    """
    bitsets = []
    enums = []
    for type_name, custom_type in types.items():
        if isinstance(custom_type, Enum):
            custom_type.name = f"{prefix}_{type_name}"
            enums.append(custom_type)

        if isinstance(custom_type, BitSet):
            custom_type.name = f"{prefix}_{type_name}"
            bitsets.append(custom_type)

    return enums, bitsets


def printf_arguments_cast(message, name: str):
    fields = []
    for field in message.fields:
        if not isinstance(field.type, BitSet):
            fields.append(
                f"{utils.to_camel_case(message.name,'_')}_{name}.{field.name}"
            )
        else:
            for i in range(0, field.bit_size // 8):
                fields.append(
                    f"{utils.to_camel_case(message.name,'_')}_{name}.{field.name}[{i}]"
                )
    return fields


def convert(field, index):
    return [
        f"(data[{index+number_index+1}] << {8*(number_index+1)})"
        for number_index in range(field.bit_size // 8 - 1)
    ]


def params(fields, struct_info):
    return [
        f"{struct_info}{field.name} << {field.shift}"
        if field.shift != 0
        else f"{struct_info}{field.name}"
        for field in fields
    ]


def random_values(fields):
    values = []

    for field in fields:
        if isinstance(field.type, BitSet):
            values.append(
                f"{{ {', '.join([str(random.randint(0, 255)) for _ in range((field.bit_size // 8))])} }}"
            )
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


def casts(name: str):
    match name:
        case "uint8":
            return "uint8_t"
        case "uint16":
            return "uint16_t"
        case "uint32":
            return "uint32_t"
        case "uint64":
            return "uint64_t"
        case "int8":
            return "int8_t"
        case "int16":
            return "int16_t"
        case "int32":
            return "int32_t"
        case "int64":
            return "int64_t"
        case "float32":
            return "float"
        case "float64":
            return "double"
        case "bool":
            return "bool"
        case _:
            return utils.to_camel_case(name, "_")


def printf_cast(fields):
    casts = []
    for field in fields:
        if isinstance(field.type, Number):
            match field.type.name:
                case "float32":
                    casts.append("%f")
                case "float64":
                    casts.append("%lf")
                case "int8":
                    casts.append("%hhd")
                case "int16":
                    casts.append("%hd")
                case "int32":
                    casts.append("%d")
                case "int64":
                    casts.append("%ld")
                case "uint8":
                    casts.append("%hhu")
                case "uint16":
                    casts.append("%hu")
                case "uint32":
                    casts.append("%u")
                case "uint64":
                    casts.append("%lu")
                case "bool":
                    casts.append("%d")
        elif isinstance(field.type, Enum):
            casts.append("%d")
        elif isinstance(field.type, BitSet):
            casts.append(".".join(["%hhx"] * (field.bit_size // 8)))
    return casts


def float_deserialize(field, index):
    return [f"data[{index+byte_index}]" for byte_index in range(field.bit_size // 8)]


def fields_serialization(index, fields, struct: bool):
    serialized_fields = []
    struct_info = "msg->" if struct else ""

    if fields:
        if len(fields) == 1 and fields[0].bit_size >= 8:
            field = fields[0]
            if isinstance(field.type, BitSet):
                for bitset_index in range(field.bit_size // 8):
                    serialized_fields.append(
                        f"data[{index+bitset_index}] = {struct_info}{field.name}[{bitset_index}];"
                    )
            elif isinstance(field.type, Number) and (
                field.type.name == "float32" or field.type.name == "float64"
            ):
                for byte_index in range(field.bit_size // 8):
                    serialized_fields.append(
                        f"data[{index+byte_index}] = (({casts(field.type.name)}_t) {struct_info}{field.name}).bytes[{byte_index}];"
                    )
            elif field.bit_size > 8:
                serialized_fields.append(
                    f"data[{index}] = {struct_info}{field.name} & 255;"
                )
                for number_index in range(1, field.bit_size // 8):
                    serialized_fields.append(
                        f"data[{index+number_index}] = ({struct_info}{field.name} >> {number_index*8}) & 255;"
                    )
            else:
                serialized_fields.append(f"data[{index}] = {struct_info}{field.name};")
        else:
            serialized_fields.append(
                f"data[{index}] = {' | '.join(params(fields, struct_info))};"
            )

    return serialized_fields


def fields_deserialization(index, fields):
    deserialized_fields = []

    if fields:
        if len(fields) == 1 and fields[0].bit_size >= 8:
            field = fields[0]
            if isinstance(field.type, BitSet):
                for bitset_index in range(field.bit_size // 8):
                    deserialized_fields.append(
                        f"msg->{field.name}[{bitset_index}] = data[{index+bitset_index}];"
                    )
            elif isinstance(field.type, Number) and (
                field.type.name == "float32" or field.type.name == "float64"
            ):
                deserialized_fields.append(
                    "msg->{} = ((float_t) {}).value;".format(
                        field.name,
                        "{" + str(", ".join(float_deserialize(field, index))) + "}",
                    )
                )
            elif field.bit_size > 8:
                deserialized_fields.append(
                    f"msg->{field.name} = data[{index}] | {' | '.join(convert(field, index))};"
                )
            else:
                deserialized_fields.append(f"msg->{field.name} = data[{index}];")
        else:
            for field in fields:
                if field.type.name != "bool":
                    deserialized_fields.append(
                        f"msg->{field.name} = ({casts(field.type.name)}) ((data[{index}] & {field.bit_mask}) >> {field.shift});"
                    )
                else:
                    deserialized_fields.append(
                        f"msg->{field.name} = (data[{index}] & {field.bit_mask}) >> {field.shift};"
                    )

    return deserialized_fields


def buffer_size(message_name):
    return utils.to_snake_case(f"{message_name}_size").upper()


def already_timestamp(fields):
    if any(field.name == "timestamp" for field in fields):
        return True
    else:
        return False


def parameters(messages, message_name):
    msg = [msg for msg in messages if msg.name == message_name][0]
    if len(msg.fields) != 0:
        return ", " + f", ".join(
            [f"{casts(field.type.name)} {field.name}" for field in msg.fields]
        )
    else:
        return ""


def generate_ids_include(network: Network):
    return TEMPLATE_IDS_H.render(network=network)


def generate_utils_include(network: Network, schema: Schema):

    # Calculate maximum message name length
    msg_name_max_length = 1  # Minimum message name length must be at least 1
    for message_name, _ in network.messages.items():
        if (
            len(message_name) + 1 > msg_name_max_length
        ):  # 1 is added because of C strings (last char is '\0')
            msg_name_max_length = len(message_name) + 1

    code = TEMPLATE_UTILS_H.render(
        network=network,
        schema=schema,
        msg_name_max_length=msg_name_max_length,
        utils=utils,
        len=len,
        printf_cast=printf_cast,
        enumerate=enumerate,
    )

    return code


def generate_canconfig_include(canconfig, namespace):
    if not canconfig:
        return ""
    options = canconfig["options"]
    version = canconfig["version"]
    header = ""
    header += f"#ifndef {namespace}_CANCONFIG_H\n"
    header += f"#define {namespace}_CANCONFIG_H\n\n"
    header += f"#define {namespace}_CANCONFIG_VERSION {version}f\n\n"
    for k, v in options.items():
        if isinstance(v, dict):
            header += "\n"
            for _k, _v in v.items():
                header += f"#define {_k.upper()} {_v}"
                if isinstance(_v, float):
                    header += "f"
                header += "\n"
        else:
            header += f"#define {k.upper()} {v}"
            if isinstance(v, float):
                header += "f"
            header += "\n"
    header += "#endif\n"

    return header
