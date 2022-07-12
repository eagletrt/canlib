from __future__ import annotations

import math
from typing import Optional

from canlib.common.limits import ALLOWED_INTERVALS, RESERVED_KEYWORKDS
from canlib.common.network import Network


class Number:
    def __init__(self, name: str, bit_size: int, format_string: str):
        self.name = name
        self.bit_size = bit_size
        self.format_string = format_string
        self.base_type = self  # self reference needed to comply to type API

    def __repr__(self):
        return f"{self.name}:{self.bit_size}:{self.format_string}"


NUMBER_TYPES = {
    "bool": Number("bool", 1, "PRIu8"),
    "int8": Number("int8", 8, "PRIi8"),
    "uint8": Number("uint8", 8, "PRIu8"),
    "int16": Number("int16", 16, "PRIi16"),
    "uint16": Number("uint16", 16, "PRIu16"),
    "int32": Number("int32", 32, "PRIi32"),
    "uint32": Number("uint32", 32, "PRIu32"),
    "int64": Number("int64", 64, "PRIi64"),
    "uint64": Number("uint64", 64, "PRIu64"),
    "float32": Number("float32", 32, "PRIf32"),
    "float64": Number("float64", 64, "PRIf64"),
}

NUMBER_TYPES_BY_SIZE = {
    1: NUMBER_TYPES["uint8"],
    2: NUMBER_TYPES["uint16"],
    3: NUMBER_TYPES["uint32"],
    4: NUMBER_TYPES["uint32"],
    5: NUMBER_TYPES["uint64"],
    6: NUMBER_TYPES["uint64"],
}


class Schema:
    def __init__(self, network: Network):
        self.messages = []
        self.types = {}
        self.bit_sets = []
        self.enums = []

        for name, definition in network.types.items():
            if name in RESERVED_KEYWORKDS:
                raise ValueError(
                    f"Type name {name} is reserved, network {network.name}"
                )

            if definition["type"] == "bitset":
                type = BitSet(name, definition)
                self.types[name] = type
                self.bit_sets.append(type)
            elif definition["type"] == "enum":
                type = Enum(name, definition)
                self.types[name] = type
                self.enums.append(type)

        for message_name, message in network.messages.items():
            self.messages.append(
                Message(
                    message_name,
                    message,
                    self.types,
                )
            )


class Message:
    def __init__(self, name: str, message: dict, types: dict):
        self.name = name
        self.fields = []
        self.interval = message.get("interval", -1)
        self.id = message.get("id", {})
        self.alignment = {0: [], 1: [], 2: [], 3: [], 4: [], 5: [], 6: [], 7: []}
        self.has_conversions = False

        if self.interval not in ALLOWED_INTERVALS:
            raise ValueError(f"Invalid interval {self.interval}, message {name}")

        self.fields = []
        for item_name, item_type in message["contents"].items():
            if item_name in RESERVED_KEYWORKDS:
                raise ValueError(f"Field name {item_name} is reserved, message {name}")
            if type(item_type) == dict:
                conversion = Conversion.from_dict(item_name, item_type)
                raw_type_name = conversion.raw_type.name
                self.fields.append(Field(item_name, raw_type_name, types, conversion))
                self.has_conversions = True
            else:
                self.fields.append(Field(item_name, item_type, types))

        index = 0
        start = 8

        sorted_fields = sorted(self.fields, key=lambda f: f.bit_size, reverse=True)

        for field in sorted_fields:
            if field.bit_size % 8 == 0:
                field.shift = 0
            else:
                if (index % 8) + field.bit_size >= 8:
                    index += 8 - (index % 8)
                    field.shift = 8 - (index % 8) - field.bit_size
                    start = 8
                else:
                    field.shift = 8 - (index % 8) - field.bit_size
                mask = 0
                if isinstance(field.type, Enum) or field.type.name == "bool":
                    for bit in reversed(range(start)):
                        if bit >= field.shift:
                            mask = mask | (1 << bit)
                            start -= 1
                    field.bit_mask = mask

            if index // 8 > 7:
                raise TypeError(f"{name} larger than 8 bytes")

            self.alignment[index // 8].append(field)
            field.alignment_index = index // 8

            index += field.bit_size

        self.bit_size = index
        self.byte_size = math.ceil(self.bit_size / 8)


class Conversion:
    def __init__(
        self, raw_type: Number, converted_type: Number, offset: float, conversion: float
    ):
        self.raw_type = raw_type
        self.converted_type = converted_type
        self.offset = offset
        self.conversion = conversion

    @classmethod
    def from_dict(cls, name: str, options: dict) -> Conversion:
        r0 = options["range"][0]
        r1 = options["range"][1]

        desired_type = NUMBER_TYPES[options["type"]]
        raw_type = None

        if "force" in options:
            raw_type = NUMBER_TYPES[options["force"]]

            conv = round((2**raw_type.bit_size - 1) / (r1 - r0), 6)
        else:
            prec = options["precision"]
            numbers = (r1 - r0) * (1 / prec)

            if numbers < 2**8:
                raw_type = NUMBER_TYPES_BY_SIZE[1]
            elif numbers < 2**16:
                raw_type = NUMBER_TYPES_BY_SIZE[2]
            elif numbers < 2**32:
                raw_type = NUMBER_TYPES_BY_SIZE[3]
            elif numbers < 2**64:
                raw_type = NUMBER_TYPES_BY_SIZE[4]
            else:
                raise TypeError(f"{name} is too large")

            if options.get("optimize", False):
                conv = round((2**raw_type.bit_size - 1) / (r1 - r0))
            else:
                conv = round(1 / prec, 6)

        return cls(raw_type, desired_type, r0, conv)


class Field:
    def __init__(
        self, name: str, type: str, types: dict, conversion: Optional[Conversion] = None
    ):
        self.name = name

        if type in NUMBER_TYPES:
            self.type = NUMBER_TYPES[type]
        else:
            self.type = types[type]

        self.conversion = conversion

        self.bit_size = self.type.bit_size
        self.byte_size = math.ceil(self.bit_size / 8)

        self.alignment_index = 0
        self.shift = None
        self.bit_mask = None

    def __repr__(self):
        return f"{self.name}:{self.type.name}"


class Enum:
    def __init__(self, name: str, definition: dict):
        self.name = name
        self.items = definition.get("items", [])

        self.bit_size = math.ceil(math.log2(len(self.items)))
        self.byte_size = max(self.bit_size // 8, 1)
        self.base_type = NUMBER_TYPES_BY_SIZE[self.byte_size]

        self.format_string = self.base_type.format_string

    def max_string_length(self):
        return max(len(item) for item in self.items)

    def __len__(self):
        return len(self.items)


class BitSet:
    def __init__(self, name: str, definition: dict):
        self.name = name
        self.items = definition.get("items", [])

        self.bit_size = (len(self.items) + 7) & (-8)
        self.byte_size = max(self.bit_size // 8, 1)
        self.base_type = NUMBER_TYPES_BY_SIZE[self.byte_size]

        self.format_string = self.base_type.format_string

    def max_string_length(self):
        # Formatted as A B C D
        return sum(len(item) for item in self.items) + len(self.items) - 1

    def __len__(self):
        return len(self.items)
