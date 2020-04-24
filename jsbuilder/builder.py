import inspect
from dataclasses import _get_field
from typing import List


class NativeJsonschemaTypes:
    string = "string"
    number = "number"
    object = "object"
    array = "array"
    boolean = "boolean"


native_jsonschema_types = [
    NativeJsonschemaTypes.string,
    NativeJsonschemaTypes.number,
    NativeJsonschemaTypes.object,
    NativeJsonschemaTypes.array,
    NativeJsonschemaTypes.boolean,
]

python_type_map = {
    str: "string",
    int: "number",
    float: "number",
    dict: "object",
    list: "array",
    bool: "boolean"
}


def _resolve_node(unknown_type):
    if unknown_type is str:
        if unknown_type in native_jsonschema_map:
            return native_jsonschema_map[unknown_type]
        return JsonSchemaString()
    elif unknown_type in python_type_map:
        return native_jsonschema_map[python_type_map[unknown_type]]

    return None


class JsonSchemaNode(object):
    def render(self):
        raise NotImplementedError('Base class does not implement rendering.')

    def is_native(self):
        return False


class JsonSchemaRef(JsonSchemaNode):
    def __init__(self, ref_name: str, root: str='#/definitions/'):
        self._root = root
        self._ref_name = ref_name

    def render(self):
        return {"$ref": self._root + self._ref_name}

    def is_native(self):
        return True


def _find_ref_node_in_defs(unknown_type, definitions: dict) -> (JsonSchemaRef, None):
    for d_name in definitions:
        d = definitions[d_name]
        if unknown_type == d:
            return JsonSchemaRef(d_name)
    return None


def _find_ref_node_in_schema(unknown_type, schema_context) -> (JsonSchemaRef, None):
    if schema_context is None or "definitions" not in schema_context:
        raise TypeError('Could not find complex type <T> without schema context.'.format(T=unknown_type))

    return _find_ref_node_in_defs(unknown_type, schema_context["definitions"])


class JsonSchemaObject(JsonSchemaNode):
    @classmethod
    def from_object(schema_class, cls):
        assert inspect.isclass(cls)
        cls_annotations = cls.__dict__.get('__annotations__', {})
        cls_fields = [_get_field(cls, name, type) for name, type in cls_annotations.items()]

        schema_obj = JsonSchemaObject()
        for f in cls_fields:
            schema_obj.add_property(f.name, f.type)
            #print(f)

        return schema_obj

    def __init__(self, properties: list = None):
        self._properties = properties or {}

    def add_property(self, name, raw_type):
        type_node = _resolve_node(raw_type)
        if type_node is None:
            # TODO resolve name
            type_name = str(raw_type.__name__)
            type_node = JsonSchemaRef(type_name)
        self._properties[name] = type_node

    def render(self):
        descr = {"type": "object"}

        descr_properties = {}
        for prop_name in self._properties:
            node = self._properties[prop_name]
            if isinstance(node, JsonSchemaNode):
                descr_properties[prop_name] = self._properties[prop_name].render()
            elif node in python_type_map:
                descr_properties[prop_name] = {"type": python_type_map[node]}
        if len(descr_properties) > 0:
            descr["properties"] = descr_properties

        return descr

    def is_native(self):
        return all(self._properties[prop_name].is_native() if isinstance(self._properties[prop_name], JsonSchemaNode) else self._properties[prop_name] in native_jsonschema_types for prop_name in self._properties)


class JsonSchemaArray(JsonSchemaNode):
    def render(self):
        return {
            "type": "array"
        }

    def is_native(self):
        return True


class JsonSchemaNumber(JsonSchemaNode):
    def __init__(self, exact_type: str = None, multipleOf: int = None):
        self._exact_type = exact_type if exact_type is not None else "number"
        assert self._exact_type in ["integer", "number"]
        if multipleOf is not None:
            assert multipleOf > 0  # must be a positive number
        self._multiple_of = multipleOf

    def render(self):
        descr = { "type": self._exact_type }
        if self._multiple_of is not None:
            descr["multipleOf"] = self._multiple_of
        return descr

    def is_native(self):
        return True


class JsonSchemaInteger(JsonSchemaNode):
    def render(self):
        return {
            "type": "integer"
        }

    def is_native(self):
        return True


class JsonSchemaString(JsonSchemaNode):
    def render(self):
        return {
            "type": "string"
        }

    def is_native(self):
        return True


class JsonSchemaBoolean(JsonSchemaNode):
    def render(self):
        return {
            "type": "boolean"
        }

    def is_native(self):
        return True


native_jsonschema_map = {}
native_jsonschema_map[NativeJsonschemaTypes.string] = JsonSchemaString()
native_jsonschema_map[NativeJsonschemaTypes.number] = JsonSchemaNumber()
native_jsonschema_map[NativeJsonschemaTypes.object] = JsonSchemaObject()
native_jsonschema_map[NativeJsonschemaTypes.array] = JsonSchemaArray()
native_jsonschema_map[NativeJsonschemaTypes.boolean] = JsonSchemaBoolean()


class JsonSchemaDefinition(object):
    @classmethod
    def from_python(cls, typ):
        the_type = None
        if typ in python_type_map:
            the_type = python_type_map[typ]

        return cls(the_type)

    @classmethod
    def from_dataclass(cls, dataclass):
        pass

    def __init__(self, native_types: List[str] = None):
        self._base_descr = {}
        self._types = native_types
        self._ref = None

    def render(self):
        types = self._types if self._types is not None else []
        if not all(t in native_jsonschema_types for t in types):
            raise TypeError('Any of <{types}> are not native jsonschema types.'.format(types=types))

        descr = self._base_descr
        if len(types) > 0:
            if len(types) == 1:
                descr["type"] = types[0]
            else:
                descr["type"] = types
        elif self._ref is None:
            self._ref = str(types)

        if self._ref is not None:
            descr["$ref"] = "#/definitions/" + self._ref
        return descr

    def is_native(self):
        return all(t in native_jsonschema_types for t in self._types)

    def __eq__(self, other):
        if not isinstance(other, self.__class__):
            return False

        return self._types == other._types and self._ref == other._ref


class JsonSchemaBuilder(object):
    _DEFAULT_URI = 'http://json-schema.org/draft-07/schema#'

    def __init__(self, schema_uri: str=None):
        self._schema_uri = schema_uri if schema_uri is not None else JsonSchemaBuilder._DEFAULT_URI
        self._properties = {}
        self._definitions = {}

    def render(self):
        descr = {}
        descr["$schema"] = self._schema_uri
        descr["type"] = "object"

        descr_props = {}
        for prop_name in self._properties:
            node = self._properties[prop_name]
            assert isinstance(node, JsonSchemaNode), 'Property nodes should have been translated to node objects.'
            descr_props[prop_name] = node.render()

        descr_defs = {}
        for def_name in self._definitions:
            node = self._definitions[def_name]
            assert isinstance(node, JsonSchemaNode), 'Property nodes should have been translated to node objects.'
            descr_defs[def_name] = node.render()

        descr["definitions"] = descr_defs
        descr["properties"] = descr_props
        return descr

    def add_property(self, name, raw_type):
        type_node = _resolve_node(raw_type)
        if type_node is None:
            type_ref = _find_ref_node_in_defs(raw_type, self._definitions)
            if type_ref is None:
                # TODO resolve name
                type_name = str(raw_type.__name__)
                self.add_definition(type_name, raw_type)
                type_ref = JsonSchemaRef(type_name)
            type_node = type_ref
        self._properties[name] = type_node

    def add_definition(self, type_name, raw_type):
        type_obj = JsonSchemaObject.from_object(raw_type)
        if type_name in self._definitions and self._definitions[type_name] != type_obj:
            raise TypeError('You already have added a definition for <T> but it was different: <A> != <B>'.format(T=type_name, A=self._definitions[type_name], B=type_obj))
        self._definitions[type_name] = type_obj