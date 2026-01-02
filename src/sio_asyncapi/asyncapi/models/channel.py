from typing import Dict, List, Optional, Union

from pydantic import BaseModel, Field, Extra, constr

from .reference import Reference
from .channel_bindings import ChannelBindings
from .external_documentation import ExternalDocumentation
from .operation import Operation
from .parameter import Parameter, ParameterName
from .tag import Tag

ChannelUri = constr(regex=r"^([^\x00-\x20\x7f\"'%<>\\^`{|}]|%[0-9A-Fa-f]{2}|{[+#./;?&=,!@|]?((\w|%[0-9A-Fa-f]{2})(\.?(\w|%[0-9A-Fa-f]{2}))*(:[1-9]\d{0,3}|\*)?)(,((\w|%[0-9A-Fa-f]{2})(\.?(\w|%[0-9A-Fa-f]{2}))*(:[1-9]\d{0,3}|\*)?))*})*$")


class ChannelItem(BaseModel):
    """Describes the operations available on a single channel."""

    address: Optional[str] = None
    """
    An optional string representation of this channel's address. The address is typically
    the "topic name", "routing key", "event type", or "path". When null or absent, it MUST
    be interpreted as unknown. This is useful when the address is generated dynamically
    at runtime or can't be known upfront.
    
    It MAY contain Channel Address Expressions. Query parameters and fragments 
    SHALL NOT be used, instead use bindings to define them.
    """

    messages: Optional[Dict[str, Operation]] = None
    """
    A map of the messages that will be sent to this channel by any application at
    any time.
    
    Every message sent to this channel MUST be valid against one, and only one,
    of the message objects defined in this map.
    """

    title: Optional[str] = None
    """
    A human-friendly title for the channel.
    """

    summary: Optional[str] = None
    """
    A short summary of the channel.
    """

    description: Optional[str] = None
    """
    An optional description of this channel item. CommonMark syntax can be used for rich
    text representation.
    """

    servers: Optional[List[Reference]] = None
    """
    The servers on which this channel is available, specified as an optional unordered
    list of names (string keys) of Server Objects defined in the Servers Object (a map).
    If servers is absent or empty then this channel must be available on all servers
    defined in the Servers Object.
    """

    parameters: Optional[Dict[ParameterName, Union[Parameter, Reference]]] = None
    """
    A map of the parameters included in the channel name. It SHOULD be present only
    when using channels with expressions (as defined by RFC 6570 section 2.2).
    """

    tags: Optional[List[Tag]] = None
    """
    A list of tags for logical grouping and categorization of servers.
    """

    externalDocs: Optional[ExternalDocumentation] = None
    """
    Additional external documentation of the exposed API.
    """

    bindings: Optional[Union[ChannelBindings, Reference]] = None
    """
    A map where the keys describe the name of the protocol and the values describe
    protocol-specific definitions for the channel.
    """


    class Config:
        extra = "allow"
        schema_extra = {
            "examples": [
                            {
                                "description": "This channel is used to exchange messages about users signing up",
                                "subscribe": {
                                    "summary": "A user signed up.",
                                    "message": {
                                        "description": "A longer description of the message",
                                        "payload": {
                                            "type": "object",
                                            "properties": {
                                                "user": {
                                                    "$ref": "#/components/schemas/user"
                                                },
                                                "signup": {
                                                    "$ref": "#/components/schemas/signup"
                                                }
                                            }
                                        }
                                    }
                                },
                                "bindings": {
                                    "amqp": {
                                        "is": "queue",
                                        "queue": {
                                            "exclusive": True
                                        }
                                    }
                                }
                            }
                        ]
        }
