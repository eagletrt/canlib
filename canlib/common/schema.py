from __future__ import annotations

import math

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
    "bool": Number("bool", 1, "%d"),
    "int8": Number("int8", 8, "%i"),
    "uint8": Number("uint8", 8, "%u"),
    "int16": Number("int16", 16, "%i"),
    "uint16": Number("uint16", 16, "%u"),
    "int32": Number("int32", 32, "%li"),
    "uint32": Number("uint32", 32, "%lu"),
    "int64": Number("int64", 64, "%li"),
    "uint64": Number("uint64", 64, "%lu"),
    "float32": Number("float32", 32, "%f"),
    "float64": Number("float64", 64, "%f"),
}

NUMBER_TYPES_BY_SIZE = {
    1: NUMBER_TYPES["uint8"],
    2: NUMBER_TYPES["uint16"],
    3: NUMBER_TYPES["uint32"],
    4: NUMBER_TYPES["uint64"],
}


class Schema:
    def __init__(self, network: Network):
        self.messages = []
        self.types = {}
        self.bit_sets = []
        self.enums = []

        for name, definition in network.types.items():
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
        self.frequency = message.get("frequency", -1)
        self.id = message.get("id", {})
        self.alignment = {0: [], 1: [], 2: [], 3: [], 4: [], 5: [], 6: [], 7: []}
        self.has_conversions = False

        fields = []
        for name, item_type in message["contents"].items():
            if type(item_type) == dict:
                conversion = Conversion.from_dict(name, item_type)
                fields.append(Field(name, conversion.raw_type.name, types, conversion))
                self.has_conversions = True
            else:
                fields.append(Field(name, item_type, types))

        self.fields = sorted(fields, key=lambda field: field.bit_size, reverse=True)

        index = 0
        start = 8

        for field in self.fields:
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
        self.size = math.ceil(index / 8)


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

            conv = round((2**raw_type.bit_size) / (r1 - r0), 6)
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

            if options["optimize"] == True:
                conv = round((2**raw_type.bit_size) / (r1 - r0))
            else:
                conv = round(1 / prec, 6)

        return cls(raw_type, desired_type, r0, conv)


class Field:
    def __init__(
        self, name: str, type: str, types: dict, conversion: Conversion = None
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

    def __len__(self):
        return len(self.items)


class BitSet:
    def __init__(self, name: str, definition: dict):
        self.name = name
        self.items = definition.get("items", [])

        self.bit_size = 1 << (math.ceil(len(self.items) / 8) * 8 - 1).bit_length()
        self.byte_size = max(self.bit_size // 8, 1)
        self.base_type = NUMBER_TYPES_BY_SIZE[self.byte_size]

        self.format_string = self.base_type.format_string

    def __len__(self):
        return len(self.items)