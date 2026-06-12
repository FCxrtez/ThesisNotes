def full_adder(a_bit, b_bit, c_in):
    s = a_bit ^ b_bit ^ c_in
    c_out = (a_bit & b_bit) | (b_bit & c_in) | (a_bit & c_in)
    return s, c_out

def ripple_carry_adder(a, b, width=35):
    """
    Simulates a Ripple Carry Adder (CPA) bit-by-bit.
    """
    
    sum_result = 0
    carry = 0

    for i in range(width):
        bit_a = (a >> i) & 1
        bit_b = (b >> i) & 1
        s, carry = full_adder(bit_a, bit_b, carry)
        sum_result |= (s << i)

    mask = (1 << width) - 1
    return sum_result & mask, carry
