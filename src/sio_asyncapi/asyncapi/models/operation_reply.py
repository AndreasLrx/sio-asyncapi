from typing import List, Optional, Union

from pydantic import BaseModel

from .reference import Reference
from .operation_reply_address import OperationReplyAddress


class OperationReply(BaseModel):
    """
    Describes the reply part that MAY be applied to an Operation Object.
    If an operation implements the request/reply pattern,
    the reply object represents the response message.
    """
    

    address: Optional[Union[OperationReplyAddress,  Reference]] = None
    """
    Definition of the address that implementations MUST use for the reply.
    """

    channel: Optional[Reference] = None
    """
    A $ref pointer to the definition of the channel in which this operation is performed.
    When address is specified, the address property of the channel referenced by this
    property MUST be either null or not defined. If the operation reply is located inside
    a root Operation Object, it MUST point to a channel definition located in the root
    Channels Object, and MUST NOT point to a channel definition located in the Components
    Object or anywhere else. 
    
    If the operation reply is located inside an [Operation Object] in the Components Object
    or in the Replies Object in the Components Object, it MAY point to a Channel
    Object in any location. 
    
    Please note the channel property value MUST be a Reference Object and, therefore, 
    MUST NOT contain a Channel Object. However, it is RECOMMENDED that parsers 
    (or other software) dereference this property for a better development experience.
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

    class Config:
        extra = "allow"