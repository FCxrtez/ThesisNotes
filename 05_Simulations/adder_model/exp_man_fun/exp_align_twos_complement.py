from math import copysign
from pp_functions.pp_functions import pp_bits, pp_bits_spaced

def exp_align(e):
    shifts = [0] * 4
    differences = []

    for i in range(len(e)):
        for j in range(i + 1, len(e)):
            differences.append((i + 1, j + 1, e[i] - e[j]))

    print("Diferencias de exponentes:")
    for i, j, diff in differences:
        print(f"  exp.{i} - exp.{j}    =    {pp_bits(e[i - 1], 5)} - {pp_bits(e[j - 1], 5)}    =    {pp_bits(diff, 6)} == {diff}")
    print("\n")

    # False/True para que is_max solo contenga booleanos.
    signs = [False if copysign(1, dif[2]) == -1 else True for dif in differences]

    is_max = [False] * 4
    is_max[0] = signs[0] and signs[1] and signs[2]
    is_max[1] = not signs[0] and signs[3] and signs[4]
    is_max[2] = not signs[1] and not signs[3] and signs[5]
    is_max[3] = not signs[2] and not signs[4] and not signs[5]

    print("Maximo exponente en numero:")
    print("  " + str(is_max))

    if is_max[0]:
        shifts[1] = differences[0][2]
        shifts[2] = differences[1][2]
        shifts[3] = differences[2][2]
    elif is_max[1]:
        shifts[0] = -differences[0][2]
        shifts[2] = differences[3][2]
        shifts[3] = differences[4][2]
    elif is_max[2]:
        shifts[0] = -differences[1][2]
        shifts[1] = -differences[3][2]
        shifts[3] = differences[5][2]
    elif is_max[3]:
        shifts[0] = -differences[2][2]
        shifts[1] = -differences[4][2]
        shifts[2] = -differences[5][2]

    print("shifts:")
    print("  " + str(shifts))
    print("\n" + "-" * 50 + "\n")

    return shifts, is_max


def twos_complement(a_mantisas, signos, bit_mask=33):
    twos_complement_mantisas = []

    precision_w_ovf = bit_mask + 2
    mask_w_ovf = (1 << precision_w_ovf) - 1

    for am, s in zip(a_mantisas, signos):
        # Negative number
        if s == 1:
            one_complement = am ^ mask_w_ovf
            twos_comp = (one_complement + 1) & mask_w_ovf

        # Positive number, no change
        else:
            twos_comp = am & mask_w_ovf

        # No debo agregar el signo, los bits the ovf ya indican el signo correcto.
        twos_complement_mantisas.append(twos_comp)

        print(f"Signo: {s}")
        print(f"Mantisa original:\n      {pp_bits_spaced(am, bit_mask)}")
        print(f"Complemento a dos con ovf: \n    {pp_bits_spaced(twos_comp, precision_w_ovf)}\n")

    print("\n" + "-" * 50 + "\n")
    return twos_complement_mantisas
