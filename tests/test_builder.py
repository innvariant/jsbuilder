import json

from dataclasses import dataclass

from jsbuilder.builder import JsonSchemaBuilder

from .util import validate


class TinyType:
    a_key: str
    a_val: float


class SomeType:
    my_prop: int
    aList: list
    tiny: TinyType


@dataclass()
class SubType:
    some_name: str
    complex: SomeType
    a_value: float = 2.5
    camelNameSpaceProp1: str = "p1"
    camelNameSpaceProp2: str = "p2"


def test_empty_builder_is_valid_schema():
    builder = JsonSchemaBuilder()
    schema_instance = builder.render()

    validate(schema_instance)


def test_dev():
    builder = JsonSchemaBuilder()
    builder.add_property("name", str)
    builder.add_property("bar1", SubType)
    builder.add_property("bar2", SubType)

    print(json.dumps(builder.render(), indent=1))


def test_valid_schema():
    builder = JsonSchemaBuilder()
    builder.add_property("name", str)
    builder.add_property("bar", SubType)

    print(builder.render())
    print(json.dumps(builder.render(), indent=1))

    # validate(json.dumps(builder.render()), json.dumps(draft07_schema))
    validate(builder.render())
