import struct

def pp_bits(value, length):
    """
    Formats an integer as a fixed-length binary string.
    """
    return f"{value:0{int(length)}b}"


def pp_bits_spaced(value, length):
    """
    Formats an integer as a fixed-length binary string, separated by spaces every 4 bits.
    """
    mask         = (1 << length) - 1 # 00...00011111 para length = 5
    masked_value = value & mask

    num_spaces   = (length - 1) // 4
    total_length = length + num_spaces

    return f"{masked_value:0{total_length}_b}".replace("_", " ")


def pp_hex(value, num_digits=4):
    """
    Formats an integer as a fixed-length hexadecimal string.
    """
    return f"0x{value:0{int(num_digits)}X}"


def float_to_bits(f):
    """
    Converts a floating-point number to its 16-bit bit representation.
    >e: big-endian _Float16, >H: big-endian unsigned short (16 bits)
    """
    return struct.unpack(">H", struct.pack(">e", f))[0]

def bits_to_float(b):
    return struct.unpack(">e", struct.pack(">H", b))[0]
