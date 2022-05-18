import math
import re

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

        for custom_type_name, custom_type_content in network.types.items():
            if custom_type_content["type"] == "bitset":
                type = BitSet(custom_type_name, custom_type_content)
                self.types[custom_type_name] = type
            elif custom_type_content["type"] == "enum":
                type = Enum(custom_type_name, custom_type_content["items"])
                self.types[custom_type_name] = type
            else:
                raise ValueError(f"Unknown type {custom_type_content['type']}")

        for topic_name in network.topics.keys():
            messages = network.get_messages_by_topic(topic_name)
            for message_name, message in messages.items():
                self.messages.append(
                    Message(
                        message_name,
                        message,
                        self.types,
                    )
                )

    def get_enums(self):
        return [type for type in self.types.values() if isinstance(type, Enum)]

    def get_bit_sets(self):
        return [type for type in self.types.values() if isinstance(type, BitSet)]


class Message:
    def __init__(self, name: str, message: dict, types: dict):
        self.name = name
        self.fields = []
        self.frequency = message.get("frequency", -1)

        self.partitioned_size = {
            0: [],
            1: [],
            2: [],
            3: [],
            4: [],
            5: [],
            6: [],
            7: [],
        }

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

            self.partitioned_size[index // 8].append(field)

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
    def __init__(self, name, field_content):
        self.name = name
        self.content = []

        if "items" in field_content:
            self.content = [
                Item(field, index) for index, field in enumerate(field_content["items"])
            ]
            self.size = len(field_content["items"])
        elif "size" in field_content:
            self.size = field_content["size"]
        else:
            raise Exception("Invalid bitset format")

        self.bit_size = math.ceil(self.size / 8) * 8
        self.byte_size = max(self.bit_size // 8, 1)
        self.parent = []
        if "contents" in field_content:
            for bitset in field_content["contents"]:
                self.parent.append(str(bitset))


class Enum:
    def __init__(self, name, field_content):
        self.name = name
        self.content = []

        for index, enum_item in enumerate(field_content):
            self.content.append(Item(enum_item, index))

        self.bit_size = math.ceil(math.log2(len(self.content)))


class Item:
    def __init__(self, item, index):
        self.item = item
        self.index = index
