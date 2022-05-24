import math

"""
    struct format = {
        "name": "struct_name",
        "fields": {
            "field_name": "field_type",
            ...
        }
        ...
    }

    enum format = {
        "name": "enum_name",
        "items": [ITEM_NAME, ...]
    }
"""


class Schema:
    def __init__(self, schema):
        self.types = {}
        self.structs = {}
        if schema is not None and isinstance(schema, dict):
            for type_name, type_description in schema["types"].items():
                if type_description["type"] == "enum":
                    self.types[type_name] = Enum(type_name, type_description["items"])
                elif type_description["type"] == "bitset":
                    if type_description.get("items") is not None:
                        self.types[type_name] = BitSet(
                            bitset_items=type_description["items"]
                        )
                    elif type_description.get("size") is not None:
                        self.types[type_name] = BitSet(
                            bitset_size=type_description["size"]
                        )
                else:
                    raise Exception(
                        f"{type_description['type'].capitalize()} type not yet supported"
                    )

            for struct_name, struct_description in schema["structs"].items():
                self.structs[struct_name] = Struct(struct_description, self.types)


class Enum:
    def __init__(self, type_name, enum_items: list):
        self.proto_type = type_name + "_type"
        self.values = []
        for index, item_name in enumerate(enum_items):
            self.values.append(EnumItem(item_name, index))


class EnumItem:
    def __init__(self, item_name, index):
        self.name = item_name
        self.index = index


class BitSet:
    def __init__(self, bitset_items: list = None, bitset_size=None):
        self.size = (
            math.ceil(len(bitset_items)) / 8
            if bitset_items
            else math.ceil(bitset_size / 8)
        )
        self.proto_type = "uint32" if self.size <= 4 else "uint64"


class Number:
    def __init__(self, number_type: str):
        self.original_type = number_type
        if self.original_type == "bool":
            self.proto_type = "bool"
        elif self.original_type == "float32":
            self.original_type = "float"
            self.proto_type = "float"
        elif self.original_type == "float64":
            self.original_type = "double"
            self.proto_type = "double"
        elif (
            self.original_type == "int8"
            or self.original_type == "int16"
            or self.original_type == "int32"
        ):
            self.proto_type = "int32"
        elif self.original_type == "int64":
            self.proto_type = "int64"
        elif (
            self.original_type == "uint8"
            or self.original_type == "uint16"
            or self.original_type == "uint32"
        ):
            self.proto_type = "uint32"
        elif self.original_type == "uint64":
            self.proto_type = "uint64"
        else:
            raise Exception(f"{self.original_type} number not yet supported")


class Struct:
    def __init__(self, struct_description, types) -> None:
        self.fields = []
        timestamp_message = False
        last_index = 0
        if "timestamp" in struct_description:
            timestamp_message = True
        for index, (field_name, field_type) in enumerate(struct_description.items()):
            if type(field_type) == dict:
                field_type = field_type["type"]
            self.fields.append(StructField(field_name, field_type, index + 1, types))
            last_index += 1
        if not timestamp_message:
            self.fields.append(
                StructField("_timestamp", "uint64", last_index + 1, types)
            )


class StructField:
    def __init__(self, field_name, field_type, index, types):
        self.name = field_name
        self.index = index

        if field_type in types:
            if isinstance(types[field_type], Enum) or isinstance(
                types[field_type], BitSet
            ):
                self.type = types[field_type]
        else:
            types[field_name] = Number(field_type)
            self.type = types[field_name]
