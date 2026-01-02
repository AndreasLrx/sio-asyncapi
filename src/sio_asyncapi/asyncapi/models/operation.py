from typing import Dict, List, Optional, Union, Literal

from pydantic import BaseModel, Field, Extra

from .reference import Reference
from .operation_bindings import OperationBindings
from .tag import Tag
from .external_documentation import ExternalDocumentation
from .operation_bindings import OperationBindings
from .operation_trait import OperationTrait
from .operation_reply import OperationReply
from .security_scheme import SecurityScheme


class Operation(BaseModel):
    """Describes a publish or a subscribe operation. This provides a place to document
    how and why messages are sent and received.

    For example, an operation might describe a chat application use case where a user
    sends a text message to a group. A publish operation describes messages that are
    received by the chat application, whereas a subscribe operation describes messages
    that are sent by the chat application."""
    
    action: Literal['send', 'receive'] = ...
    """
    **REQUIRED**. Use send when it's expected that the application will send a message
    to the given channel, and receive when the application should expect receiving
    messages from the given channel.
    """

    channel: Reference = ...
    """
    **REQUIRED**. A $ref pointer to the definition of the channel in which this operation
    is performed. If the operation is located in the root Operations Object, it MUST point
    to a channel definition located in the root Channels Object, and MUST NOT point to a
    channel definition located in the Components Object or anywhere else. If the operation
    is located in the Components Object, it MAY point to a Channel Object in any location.

    Please note the channel property value MUST be a Reference Object and, therefore,
    MUST NOT contain a Channel Object. However, it is RECOMMENDED that parsers
    (or other software) dereference this property for a better development experience.
    """

    title: Optional[str] = None
    """
    A human-friendly title for the operation.
    """

    summary: Optional[str] = None
    """
    A short summary of what the operation is about.
    """

    description: Optional[str] = None
    """
    A verbose explanation of the operation. CommonMark syntax can be used for rich
    text representation.
    """

    security: Optional[Dict[str, Union[SecurityScheme, Reference]]] = None
    """
    A declaration of which security schemes are associated with this operation.
    Only one of the security scheme objects MUST be satisfied to authorize an
    operation. In cases where Server Security also applies, it MUST also be satisfied.
    """

    tags: Optional[List[Tag]] = None
    """
    A list of tags for API documentation control. Tags can be used for logical grouping
    of operations.
    """

    externalDocs: Optional[ExternalDocumentation] = None
    """
    Additional external documentation for this operation.
    """

    bindings: Optional[Union[OperationBindings, Reference]] = None
    """
    A map where the keys describe the name of the protocol and the values describe
    protocol-specific definitions for the operation.
    """

    traits: Optional[List[Union[OperationTrait, Reference]]] = None
    """
    A list of traits to apply to the operation object. Traits MUST be merged into the
    operation object using the JSON Merge Patch algorithm in the same order they are
    defined here.
    """

    messages: Optional[List[Reference]] = None
    """
    A list of $ref pointers pointing to the supported Message Objects that can be
    processed by this operation. It MUST contain a subset of the messages defined
    in the channel referenced in this operation, and MUST NOT point to a subset of
    message definitions located in the Messages Object in the Components Object or
    anywhere else.
    
    Every message processed by this operation MUST be valid against one, and only one,
    of the message objects referenced in this list. Please note the messages property 
    value MUST be a list of Reference Objects and, therefore, MUST NOT contain Message
    Objects. However, it is RECOMMENDED that parsers (or other software)
    dereference this property for a better development experience.
    """

    reply: Optional[Union[OperationReply, Reference]] = None
    """
    The definition of the reply in a request-reply operation.
    """


    class Config:
        extra = "allow"
        schema_extra = {
            "examples": [
                            {
                                "operationId": "registerUser",
                                "summary": "Action to sign a user up.",
                                "description": "A longer description",
                                "tags": [
                                    { "name": "user" },
                                    { "name": "signup" },
                                    { "name": "register" }
                                    ],
                                "message": {
                                    "headers": {
                                        "type": "object",
                                        "properties": {
                                            "applicationInstanceId": {
                                                "description": "Unique identifier for a given instance of the publishing application",
                                                "type": "string"
                                                }
                                            }
                                        },
                                    "payload": {
                                        "type": "object",
                                        "properties": {
                                            "user": {
                                                "$ref": "#/components/schemas/userCreate"
                                                },
                                            "signup": {
                                                "$ref": "#/components/schemas/signup"
                                                }
                                            }
                                        }
                                    },
                                "bindings": {
                                    "amqp": {
                                        "ack": False
                                        }
                                    },
                                "traits": [
                                    { "$ref": "#/components/operationTraits/kafka" }
                                    ]
                                }
                        ]
            }
