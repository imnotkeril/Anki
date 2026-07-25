from beartype import beartype


def _read_varint(buf: bytes, pos: int) -> tuple[int, int]:
    result = 0
    shift = 0
    while True:
        b = buf[pos]
        pos += 1
        result |= (b & 0x7F) << shift
        if not (b & 0x80):
            break
        shift += 7
    return result, pos


@beartype
def extract_strings(buf: bytes) -> list[str]:
    """Return every printable UTF-8 length-delimited field in a protobuf blob, in order."""
    out: list[str] = []
    pos = 0
    end = len(buf)
    while pos < end:
        tag, pos = _read_varint(buf, pos)
        wire_type = tag & 0x7
        if wire_type == 0:
            _, pos = _read_varint(buf, pos)
        elif wire_type == 1:
            pos += 8
        elif wire_type == 2:
            length, pos = _read_varint(buf, pos)
            sub = buf[pos : pos + length]
            pos += length
            try:
                text = sub.decode("utf-8")
                printable = sum(1 for c in text if c.isprintable() or c in "\n\t")
                if text and printable / len(text) > 0.85:
                    out.append(text)
                    continue
            except UnicodeDecodeError:
                pass
            out.extend(extract_strings(sub))
        elif wire_type == 5:
            pos += 4
        else:
            break
    return out
