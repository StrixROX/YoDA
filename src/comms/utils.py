def pack_msg(msg) -> bytes:
    return msg.encode() + b"\0"
