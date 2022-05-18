import math
from typing import List

from canlib.common.network import Network


class Number:
    def __init__(self, name, bit_size):
        self.name = name
        self.bit_size = bit_size


NUMBER_TYPES = {
    "bool": Number("bool", 1),
    "int8": Number("int8", 8),
    "uint8": Number("uint8", 8),
    "int16": Number("int16", 16),
    "uint16": Number("uint16", 16),
    "int32": Number("int32", 32),
    "uint32": Number("uint32", 32),
    "int64": Number("int64", 64),
    "uint64": Number("uint64", 64),
    "float32": Number("float32", 32),
    "float64": Number("float64", 64),
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
                type = Enum(name, definition["items"])
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
        self.alignment = {0: [], 1: [], 2: [], 3: [], 4: [], 5: [], 6: [], 7: []}

        fields = []
        for name, type in message["contents"].items():
            fields.append(Field(name, type, types))

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
                            start = start - 1
                    field.bit_mask = mask

            self.alignment[index // 8].append(field)

            index += field.bit_size

        self.size = math.ceil(index / 8)


class Field:
    def __init__(self, name: str, type: str, types: dict):
        self.name = name

        if type in NUMBER_TYPES:
            self.type = NUMBER_TYPES[type]
        else:
            self.type = types[type]

        self.bit_size = self.type.bit_size
        self.byte_size = math.ceil(self.bit_size / 8)

        self.shift = None
        self.bit_mask = None


class BitSet:
    def __init__(self, name, content):
        self.name = name
        self.content = content.get("items", [])
        self.size = content.get("size", len(self.content))

        self.bit_size = math.ceil(self.size / 8) * 8
        self.byte_size = max(self.bit_size // 8, 1)
        self.parent = []

        for bitset in content.get("contents", []):
            self.parent.append(str(bitset))


class Enum:
    def __init__(self, name: str, content: List[str]):
        self.name = name
        self.content = content
        self.bit_size = math.ceil(math.log2(len(self.content)))
