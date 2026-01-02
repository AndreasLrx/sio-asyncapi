from typing import Optional

from pydantic import BaseModel


class OperationReplyAddress(BaseModel):
    """
    An object that specifies where an operation has to send the reply.

    For specifying and computing the location of a reply address, a runtime expression is used.
    """
    
    location: str = ...
    """
    **REQUIRED**. A runtime expression that specifies the location of the reply address.
    """
    

    description: Optional[str] = None
    """
    An optional description of the address. CommonMark syntax can be used for rich text representation.
    """