def round(abs_value, abs_mask, RS_bits, sign, effective_subtraction):
    """
    Hardcode Round to nearest, ties to even for testing purposes
    """
    round_up = 0

    match RS_bits & 0x3:
        case 0x0 | 0x1: # 2'b00, 2'b01: < ulp/2 away, round down
            round_up = 0
        case 0x2:       # 2'b10: = ulp/2 away, round towards even LSB
            round_up = abs_value & 0x1
        case 0x3:       # 2'b11: > ulp/2 away, round up
            round_up = 1
        case _:
            assert(False)

    abs_rounded = (abs_value + round_up) & abs_mask
    exact_zero = (abs_value == 0) and ((RS_bits & 0x3) == 0)

    if exact_zero and effective_subtraction:
        sign_o = 0
    else:
        sign_o = sign

    return abs_rounded, exact_zero, sign_o