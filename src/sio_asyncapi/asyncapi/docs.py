"""
AsycnAPI [https://studio.asyncapi.com/] documentation auto generation.
"""
import json
import textwrap
from typing import Callable, Literal, Optional, Dict, Type, Union, List, Set, Tuple, TypeVar, Any, cast, get_args, get_origin, get_type_hints
from uuid import UUID
import dataclasses

from sio_asyncapi.asyncapi.models.channel import ChannelItem
from sio_asyncapi.asyncapi.models.components import Components
from sio_asyncapi.asyncapi.models.operation import Operation
from sio_asyncapi.asyncapi.models.operation_reply import OperationReply
from sio_asyncapi.asyncapi.models.tag import Tag
import yaml
from loguru import logger
from pydantic import BaseModel, Field, create_model

from sio_asyncapi.asyncapi.models.async_api_base import AsyncAPIBase
from sio_asyncapi.asyncapi.models.message import Message
from sio_asyncapi.asyncapi.models.reference import Reference

from .utils import add_ref_prepath

try:
    import peewee
except:
    peewee = None

NotProvidedType = Literal["NotProvided"]

T = TypeVar('T')

add_description ="""
<br/> AsyncAPI currently does not support Socket.IO binding and Web Socket like syntax used for now.
In order to add support for Socket.IO ACK value, AsyncAPI is extended with with x-ack keyword.
This documentation should **NOT** be used for generating code due to these limitations.
"""

default_components = yaml.safe_load(
"""
messages:

schemas:
  NoSpec:
    description: Specification is not provided
"""
)

_ref_cache: Dict[type, Type] = {}

def peewee_uuid_ref(model_cls: type) -> Type:
    """
    Returns a Pydantic-friendly type for a Peewee model reference.
    Accepts: model instance | UUID | uuid-string
    Produces: UUID
    Schema: {type: "string", format: "uuid"}
    """
    if model_cls in _ref_cache:
        return _ref_cache[model_cls]

    if not (peewee and isinstance(model_cls, type) and issubclass(model_cls, peewee.Model)):
        return model_cls
    pk_name = model_cls._meta.primary_key.name

    class PeeweeUUIDRef:
        @classmethod
        def __get_validators__(cls):
            yield cls.validate

        @classmethod
        def validate(cls, v: Any) -> UUID:
            # Accept peewee model instance
            if isinstance(v, model_cls):
                v = getattr(v, pk_name)

            if v is None:
                raise TypeError("None is not allowed")

            # Accept UUID or uuid-string
            if isinstance(v, UUID):
                return v
            return UUID(str(v))

        @classmethod
        def __modify_schema__(cls, field_schema: dict) -> None:
            field_schema.update(type="string", format="uuid")

    PeeweeUUIDRef.__name__ = f"{model_cls.__name__}UUIDRef"
    _ref_cache[model_cls] = PeeweeUUIDRef
    return PeeweeUUIDRef


_dc_cache = {}

def rebuild_container(origin: Type, args: List[Type]) -> Type:
    # args are already rewritten
    if origin is list:
        return List[args[0]]
    if origin is set:
        return Set[args[0]]
    if origin is dict:
        return Dict[args[0], args[1]]
    if origin is tuple:
        # tuple[T, ...] form
        if len(args) == 2 and args[1] is Ellipsis:
            return Tuple[args[0], ...]
        return Tuple[tuple(args)]
    return None

def rewrite_type(tp: Any) -> Any:
    # Peewee model class => ref type
    if peewee and isinstance(tp, type) and issubclass(tp, peewee.Model):
        return peewee_uuid_ref(tp)

    # Dataclass => shadow pydantic model with rewritten fields
    if isinstance(tp, type) and dataclasses.is_dataclass(tp):
        if tp in _dc_cache:
            return _dc_cache[tp]
        hints = get_type_hints(tp)
        dc_fields = {}
        for f in dataclasses.fields(tp):
            ann = hints.get(f.name, f.type)
            dc_fields[f.name] = (rewrite_type(ann), Field(...))
        M = create_model(f"{tp.__name__}Schema", **dc_fields)
        _dc_cache[tp] = M
        return M

    origin = get_origin(tp)
    if origin is None:
        return tp

    args = tuple(rewrite_type(a) for a in get_args(tp))

    if origin is Union:
        return Union[args]  # type: ignore

    # containers
    rebuilt = rebuild_container(origin, args)
    if rebuilt is not None:
        return rebuilt

    return tp

class AsyncAPIDoc(AsyncAPIBase):
    """AsyncAPI documentation generator."""

    @classmethod
    def default_init(cls,
        version: str = "1.0.0",
        title: str = "Demo Chat API",
        description: str = "Demo Chat API",
        server_url: str = "http://localhost:5000",
        server_name: str = "BACKEND",
        server_protocol: str = "socketio",
    ) -> "AsyncAPIDoc":
        """Initialize AsyncAPI documentation generator."""
        logger.info(f"{server_url=}, {server_name=}, {server_protocol=}")
        default_components["messages"] = {}
        initial_spec_obj = {
            "info": {
                "title": title,
                "version": version,
                "description": description + add_description,
                "tags": [],
            },
            "servers": {
                server_name: {
                    "host": server_url,
                    "protocol": server_protocol}},
            "asyncapi": "3.0.0",
            "channels": {},
            "operations": {},
            "components": default_components,
        }
        return AsyncAPIDoc.parse_obj(initial_spec_obj)

    def get_yaml(self) -> str:
        """Return AsyncAPI documentation in YAML format."""
        return yaml.safe_dump(
            json.loads(
                self.json(
                    by_alias=True,
                    exclude_none=True,
                )
            )
        )

    def resolve_ref(self, obj: Union[str, T, Reference]) -> T:
        ref = None
        if obj and hasattr(obj, "ref"):
            ref = getattr(obj, "ref")
        elif isinstance(obj, str):
            ref = obj
        if ref is None:
            return cast(T, obj)
        if not ref.startswith("#/"):
            raise Exception("Unsupported ref %s" % ref)
        parts = ref[2:].split('/')
        current = self
        for p in parts:
            current = getattr(current, p)
        return cast(T, current)

    def make_ref(self, path: str) -> Reference:
        return Reference.parse_obj({"$ref": f"#{path}"})

    def add_component(self, obj: Any, tipe: str, name: str) -> Reference:
        # if not tipe in self.components:
        #     self.components[tipe] = {}
        getattr(self.components, tipe)[name] = obj
        return self.make_ref(f"/components/{tipe}/{name}")

    def sanitize_id(self, id: str) -> str:
        return id.replace("/", "")

    def add_global_tag(self, name: str, description: Optional[str] = None) -> None:
        for t in self.info.tags:
            if t.name == name:
                t.description = description
                return
        tag = Tag(name=name, description=description)
        self.info.tags.append(tag)

    def add_channel(self,
                    id: str,
                    address: Optional[str] = None,
                    title: Optional[str] = None,
                    summary: Optional[str] = None,
                    description: Optional[str] = None,
                    servers: Optional[List[str]] = None
                    ) -> None:
        address = id if not address else address
        id = self.sanitize_id(id)
        channel = self.channels.get(id, None)
        if channel is None:
            channel_obj = {
                "address": address,
                "title": title if title else id.title(),
                "summary": summary,
                "description": description,
            }
            if servers:
                channel_obj["servers"] = [self.make_ref(f"/servers/{s}") for s in servers]
            self.channels[id] = ChannelItem.parse_obj(channel_obj)
        else:
            raise Exception("Channel %s already exists" % id)

    def add_event(
            self,
            channel: str,
            id: str,
            handler: Optional[Callable] = None, # To extract name, summary, description
            title: Optional[str] = None,
            name: Optional[str] = None,
            summary: Optional[str] = None,
            description: Optional[str] = None,
            tags: Optional[List[str]] = None,
            ack_data_model: Optional[Union[Type[BaseModel], NotProvidedType]] = None,
            payload_model: Optional[Union[Type[BaseModel], NotProvidedType]] = None,
            action: str = "receive"
        ) -> None:
        if id.lower().startswith("on_"):
            id = id[3:]
        channel = self.sanitize_id(channel)
        channel_obj = self.resolve_ref(self.channels[channel])
        if not channel_obj.messages:
            channel_obj.messages = {}
        if id in channel_obj.messages:
            raise Exception("Message %s already in %s" % (id, channel))
        channel_ref = self.make_ref(f"/channels/{channel}")
        reply = None

        payload = None
        if handler:
            name = handler.__name__ if not name else name
            description = handler.__doc__ if not description else description
            
            type_hints = get_type_hints(handler)
            param_names = list(type_hints.keys())[:-1]  # Remove the return type
            fields = {}
            for param_name in param_names:
                param_type = type_hints[param_name]
                field_type = rewrite_type(param_type)
                fields[param_name] = (field_type, Field())
            payload_prefix = id.title().replace("_", "")
            try:
                if not payload_model:
                    payload_model = create_model(f"{payload_prefix}Payload", **fields)
            except Exception as e:
                print(e)
        
            if 'return' in type_hints and not ack_data_model:
                try:
                    return_type = type_hints["return"]
                    if return_type != type(None):
                        ack_title = f"{payload_prefix}Ack"
                        return_type = rewrite_type(return_type)
                        ack_data_model = create_model(f"{payload_prefix}Ack", success=(bool, Field(...)), error=(Optional[Any], Field(...)), data=(return_type, Field(...)))
                except Exception as e:
                    print(e)

        name = id if not name else name
        title = name if not title else title
        if payload_model:
            payload_schema_name = payload_model.__name__ # type: ignore
            payload = {"$ref": f"#/components/schemas/{payload_schema_name}"}
            payload_schema = payload_model.schema() # type: ignore
            add_ref_prepath(payload_schema, f"/components/schemas/{payload_schema_name}")
            self.components.schemas[payload_schema_name] = payload_schema # type: ignore
        if ack_data_model:
            ack_schema_name = ack_data_model.__name__ # type: ignore
            ack = {"$ref": f"#/components/schemas/{ack_schema_name}"}
            ack_schema = ack_data_model.schema() # type: ignore
            add_ref_prepath(ack_schema, f"/components/schemas/{ack_schema_name}")
            self.components.schemas[ack_schema_name] = ack_schema # type: ignore
            
            ack_message_obj = {
                "name": name + "_ack",
                "title": ack_title
            }
            if payload:
                ack_message_obj["payload"] = ack
            if tags:
                ack_message_obj["tags"] = [{"name": t} for t in tags]
            ack_id = id + "Ack"
            channel_obj.messages[ack_id] = Message.parse_obj(ack_message_obj)
            ack_msg_ref = self.make_ref(f"/channels/{channel}/messages/{ack_id}")
            reply = OperationReply.parse_obj({
                "channel": channel_ref,
                "messages": [ack_msg_ref]
            })

        message_obj = {
            "name": name,
            "title": title,
            "summary": summary,
            "description": description,
        }
        if payload:
            message_obj["payload"] = payload
        if tags:
            message_obj["tags"] = [{"name": t} for t in tags]
        channel_obj.messages[id] = Message.parse_obj(message_obj)
        msg_ref = self.make_ref(f"/channels/{channel}/messages/{id}")
        
        operation_obj = {
            "action": action,
            "channel": channel_ref,
            "title": title,
            "summary": id,
            "messages": [msg_ref]
        }
        if reply:
            operation_obj["reply"] = reply
        if tags:
            operation_obj["tags"] = [{"name": t} for t in tags]
        id = f"{channel}/{id}"
        self.operations[id] = Operation.parse_obj(operation_obj)

    def add_new_receiver(
            self,
            handler: Callable,
            name: str,
            message_name: Optional[str] = None,
            ack_data_model: Optional[Union[Type[BaseModel], NotProvidedType]] = None,
            payload_model: Optional[Union[Type[BaseModel], NotProvidedType]] = None,
        ) -> None:
        if message_name is None:
            message_name = name.title()

        # TODO: make sure schema name is unique
        if ack_data_model == "NotProvided":
            ack = {"$ref": "#/components/schemas/NoSpec"}
        elif isinstance(ack_data_model, type(BaseModel)):
            ack_schema_name = ack_data_model.__name__ # type: ignore
            ack = ack_data_model.schema() # type: ignore
            add_ref_prepath(ack, f"/components/schemas/{ack_schema_name}")
            self.components.schemas[ack_schema_name] = ack # type: ignore
        else:
            ack = None

        if payload_model == "NotProvided":
            payload = {"$ref": "#/components/schemas/NoSpec"}
        elif isinstance(payload_model, type(BaseModel)):
            payload_schema_name = payload_model.__name__ # type: ignore
            payload = {"$ref": f"#/components/schemas/{payload_schema_name}"}
            payload_schema = payload_model.schema() # type: ignore
            add_ref_prepath(payload_schema, f"/components/schemas/{payload_schema_name}")
            self.components.schemas[payload_schema_name] = payload_schema # type: ignore
        else:
            payload = None

        # create new message
        new_message = {
            "name": name,
            "description": handler.__doc__ if  handler.__doc__ else "",
            "x-ack": None,
        }

        # remove multiple spaces so yaml dump does not try to escape them
        if new_message["description"]:
            # add single indent at the beginning if not present
            if not new_message["description"].startswith(" "):
                new_message["description"] = " " + new_message["description"]
            new_message["description"] = textwrap.dedent(new_message["description"])

        new_message["x-ack"] = ack
        new_message["payload"] = payload

        # add message to spec
        if self.components and self.components.messages is not None:
            self.components.messages[message_name] = Message.parse_obj(new_message)

        # add to sub
        one_of = {"$ref": f"#/components/messages/{message_name}"}
        if self.channels and self.channels["/"] and self.channels["/"].publish and self.channels["/"].publish.message:
            self.channels["/"].publish.message.__dict__["oneOf"].append(one_of)

    def add_new_sender(
            self,
            event: str,
            payload_model: Optional[Union[Type[BaseModel], NotProvidedType]] = None,
            description: Optional[str] = None,
        ) -> None:
        """Generate new sender documentation for AsyncAPI."""
        if payload_model == "NotProvided":
            payload = {"$ref": "#/components/schemas/NoSpec"}
        elif isinstance(payload_model, type(BaseModel)):
            payload_schema_name = payload_model.__name__ # type: ignore
            payload_schema = payload_model.schema() # type: ignore
            payload = {"$ref": f"#/components/schemas/{payload_schema_name}"}
            add_ref_prepath(payload_schema, f"/components/schemas/{payload_schema_name}") # type: ignore
            self.components.schemas[payload_schema_name] = payload_schema # type: ignore
        else:
            payload = None

        # create new message
        new_message = {
            "name": event,
            "description": description if description else "",
            "payload": payload,
        }

        # remove multiple spaces so yaml dump does not try to escape them
        if new_message["description"]:
            # add single indent at the beginning if not present
            if not new_message["description"].startswith(" "):
                new_message["description"] = " " + new_message["description"]
            new_message["description"] = textwrap.dedent(new_message["description"])

        # add message to spec
        if self.components and self.components.messages is not None:
            self.components.messages[event] = Message.parse_obj(new_message)

        # add to pub
        one_of = {"$ref": f"#/components/messages/{event}"}
        if self.channels and self.channels["/"] and self.channels["/"].subscribe and self.channels["/"].subscribe.message:
            self.channels["/"].subscribe.message.__dict__["oneOf"].append(one_of)
