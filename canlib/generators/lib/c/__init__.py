from pathlib import Path
from typing import List

import jinja2 as j2

from canlib import config
from canlib.common.network import Network
from canlib.common.schema import Conversion, Field, Number, Schema

BASE_DIR = Path(__file__).parent

TEMPLATE_IDS = j2.Template((BASE_DIR / "ids.h.j2").read_text())
TEMPLATE_NETWORK = j2.Template((BASE_DIR / "network.h.j2").read_text())
TEMPLATE_WATCHDOG = j2.Template((BASE_DIR / "watchdog.h.j2").read_text())


def generate(network: Network, schema: Schema, output_path: Path):
    ids_path = output_path / "ids.h"
    ids_path.write_text(TEMPLATE_IDS.render(network=network, schema=schema))

    endianess = "LITTLE_ENDIAN" if config.IS_LITTLE_ENDIAN else "BIG_ENDIAN"

    network_path = output_path / "network.h"
    network_path.write_text(
        TEMPLATE_NETWORK.render(
            network=network,
            schema=schema,
            serialize=serialize,
            deserialize=deserialize,
            get_conversion=get_conversion,
            get_deconversion=get_deconversion,
            endianess=endianess,
        )
    )

    watchdog_path = output_path / "watchdog.h"
    watchdog_path.write_text(TEMPLATE_WATCHDOG.render(network=network, schema=schema))


def get_conversion(conversion: Conversion, network: Network, prefix: str):
    sign = "-" if conversion.offset > 0 else "+"
    return f"({network.name}_{conversion.raw_type.name})(({prefix} {sign} {abs(conversion.offset)}) * {conversion.conversion})"


def get_deconversion(conversion: Conversion, network: Network, prefix: str):
    sign = "-" if conversion.offset < 0 else "+"
    return f"((({network.name}_{conversion.converted_type.name}){prefix}) / {conversion.conversion}) {sign} {abs(conversion.offset)}"


def casts(network: Network, field: Field):
    return network.name + "_" + field.type.name


def serialize_byte(fields: List[Field], prefix: str) -> str:
    fields = [
        f"{prefix}{field.name} << {field.shift}"
        if field.shift != 0
        else f"{prefix}{field.name}"
        for field in fields
    ]
    return " | ".join(fields)


def serialize_big(network: Network, field: Field, prefix: str) -> str:
    if isinstance(field.type, Number) and field.type.name in ["float32", "float64"]:
        return [
            f"{network.name}_float32_to_bytes({prefix}{field.name}, {byte_index})"
            for byte_index in range(field.bit_size // 8)
        ]
    elif field.bit_size > 8:
        return [f"{prefix}{field.name} & 255"] + [
            f"({prefix}{field.name} >> {number_index * 8}) & 255"
            for number_index in range(1, field.bit_size // 8)
        ]
    else:
        return [f"{prefix}{field.name}"]


def serialize(network: Network, fields: List[Field], prefix: str = ""):
    if len(fields) == 0:
        return []

    if len(fields) == 1 and fields[0].bit_size >= 8:
        field = fields[0]
        return serialize_big(network, field, prefix)
    else:
        return [serialize_byte(fields, prefix)]


def deserialize_float_constructor(index: int, field: Field) -> str:
    fields = [f"data[{index + offset}]" for offset in range(field.bit_size // 8)]
    return f"{{{' ,'.join(fields)}}}"


def deserialize_bytes(index: int, field: Field) -> str:
    fields = [
        f"(data[{index + number_index + 1}] << {8 * (number_index + 1)})"
        for number_index in range(field.bit_size // 8 - 1)
    ]
    return " | ".join(fields)


def deserialize_big(network: Network, index: int, field: Field) -> str:
    if isinstance(field.type, Number) and field.type.name in ["float32", "float64"]:
        constructor = deserialize_float_constructor(index, field)
        return f"(({casts(network, field)}_helper) {constructor}).value"
    elif field.bit_size > 8:
        return f"data[{index}] | {deserialize_bytes(index, field)}"
    else:
        return f"data[{index}]"


def deserialize_small(network: Network, index: int, field: Field) -> str:
    if field.type.name != "bool":
        return f"({casts(network, field)}) ((data[{index}] & {field.bit_mask}) >> {field.shift})"
    else:
        return f"(data[{index}] & {field.bit_mask}) >> {field.shift}"


def deserialize(network: Network, index: int, fields: List[Field]) -> str:
    result = {}

    if fields:
        if len(fields) == 1 and fields[0].bit_size >= 8:
            field = fields[0]
            result[field.name] = deserialize_big(network, index, field)
        else:
            for field in fields:
                result[field.name] = deserialize_small(network, index, field)

    return result
