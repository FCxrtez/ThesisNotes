from pp_functions.pp_functions import pp_bits_spaced


def csa_3to2(a, b, c):
    """Reduces three inputs to two: Sum and Carry."""
    save = a ^ b ^ c
    carry = ((a & b) | (b & c) | (a & c)) << 1
    return save, carry


def add_4_signed_mantissas(mantisas, bit_width=35):
    """
    Simulates a 4-input CSA tree for signed numbers.
    Assumes inputs are integers representing two's complement mantissas.
    """
    mask = (1 << bit_width) - 1

    s1, c1 = csa_3to2(mantisas[0] & mask, mantisas[1] & mask, mantisas[2] & mask)
    s_final, c_final = csa_3to2(s1 & mask, c1 & mask, mantisas[3] & mask)

    print(f"Resultado CSA Tree:")
    print(f"  save:  {pp_bits_spaced(s_final, bit_width)}")
    print(f"  carry: {pp_bits_spaced(c_final, bit_width)}")
    print("\n" + "-" * 50 + "\n")

    return s_final & mask, c_final & mask
