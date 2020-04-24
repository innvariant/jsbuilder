import pytest
import os
import json
from jsonschema import validate

from dataclasses import dataclass
from jsbuilder.builder import JsonSchemaBuilder


draft07_schema_file = 'json/draft-07/schema'
with open(draft07_schema_file, 'r') as handle:
    draft07_schema = json.load(handle)


class SomeType:
    my_prop: int
    aList: list = ["a", "b", "c"]


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

    validate(schema_instance, draft07_schema)


def test_dev():
    builder = JsonSchemaBuilder()
    builder.add_property('name', str)
    builder.add_property('bar', SubType)


def test_valid_schema():
    builder = JsonSchemaBuilder()
    builder.add_property('name', str)
    builder.add_property('bar', SubType)

    print(builder.render())
    print(json.dumps(builder.render(), indent=1))

    #validate(json.dumps(builder.render()), json.dumps(draft07_schema))
    validate(builder.render(), draft07_schema)