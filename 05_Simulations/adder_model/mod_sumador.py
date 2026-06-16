from adders import add_4_signed_mantissas, ripple_carry_adder
from LZA import LZA
from pp_functions import pp_bits, pp_bits_bus, pp_bits_spaced, pp_hex, float_to_bits
from info import Info
from exp_man_fun import exp_align, twos_complement

# ------------------------
# Format Constants
# ------------------------

MAN_BITS = 10
EXP_BITS = 5
PRECISION_BITS = MAN_BITS + 1


def main(num1, num2, num3, num4, monitor = None):
    """
    Only accepts floats, anything else will lead to undefined behaviour
    """

    signos, exponentes, mantisas = [], [], []
    binary_nums = [float_to_bits(f) for f in [num1, num2, num3, num4]]

    for i in binary_nums: 
        # [sign | exponent | mantissa]
        signo = (i >> (MAN_BITS + EXP_BITS)) & 0x1 # 1 bit
        exponente = (i >> MAN_BITS) & 0x1F # 5 bits
        mantisa = i & 0x3FF # 10 bits

        signos.append(signo)
        exponentes.append(exponente)
        mantisas.append(mantisa)
    
    monitor.record("signos"    , f"{pp_bits_bus(signos, 1)}")
    monitor.record("exponentes", f"{pp_bits_bus(exponentes, 5)}")
    monitor.record("mantisas"  , f"{pp_bits_bus(mantisas, 10)}")

    for i,(bn, n) in enumerate(zip(binary_nums, [num1, num2, num3, num4])):
        print(f"Representacion en bits de {n}: {pp_bits(bn, 16)}")
        print(f"  signo: {pp_bits(signos[i], 1)}, exponente: {pp_bits(exponentes[i], 5)}, mantisa: {pp_bits_spaced(mantisas[i], 10)}\n")

    print("\n"+"-"*50+"\n")

    # ------------------------
    # input classification & implicit mantissa computation
    # ------------------------
    nums_info = [Info(signos[i], exponentes[i], mantisas[i]) for i in range(4)]

    implicit_mantisas = []
    for e, m in enumerate(mantisas):
        implicit_mantisa = m | (nums_info[e].is_normal << (PRECISION_BITS - 1))
        implicit_mantisas.append(implicit_mantisa)

        print(f"Operando {e+1}:")
        print(f"  Bit implicito: {int(nums_info[e].is_normal)}")
        print(f"  Mantisa original: {pp_bits_spaced(m, 10)}")
        print(f"  Mantisa con bit implicito: {pp_bits_spaced(implicit_mantisa, 11)}\n")
    
    monitor.record("implicit_mantisas", f"{pp_bits_bus(implicit_mantisas, 11)}" )

    print("\n"+"-"*50+"\n")

    # ------------------------
    # Exponent difference
    # ------------------------

    shifts, is_max = exp_align(exponentes)

    monitor.record("shifts", f"{pp_bits_bus(shifts, 5)}")
    monitor.record("is_max", f"{pp_bits_bus(is_max, 1)}")

    # ------------------------
    # Sign inversion (using num1 as pivot)
    # ------------------------

    pivot = signos[0]
    signos_cambiados = [s ^ pivot for s in signos] # XOR para cambiar el signo si es diferente al pivote

    monitor.record("xor_signs", f"{pp_bits_bus(signos_cambiados, 1)}")

    print(f"Signos originales: {signos}")
    print(f"pivote (signo 1er operando): {pivot}, signos cambiados: {signos_cambiados}\n")

    # ------------------------
    # Mantissa align
    # alineacion de mantisas
    # ------------------------
    # Comentarios sv:
    #       Each addend is right-shifted according to the exponent difference. Up to p bits
    #       are shifted out and compressed into a sticky bit.
    #       BEFORE THE EXPONENT SHIFT:
    #       | packed_mantissa[i] | 000..000 |
    #        <-        p       -> <- 3p+3 ->
    #       AFTER THE SHIFT:
    #       | 000..........000 | packed_mantissa[i] | 000...............0GR |  sticky bits  |
    #        <-   shifts[i]  -> <-         p      -> <-  2p+3-shifts[i]   -> <-  up to p  ->

    # Hacemos solo implicit_mantisas[i] << 3 * PRECISION_BITS pues a izq deben quedar 1 bit signo + 2 bit overflow que enmascaramos luego
    # 0x1_FFFF_FFFF(33'b1) para tener una precision maxima de 33 bits para mantisas (3*PRECISION_BITS) [cambiado a 0xFFF_FFFF_FFFF]
    # Deberia agregar una precision extra para los sticky bits? 0xFFF_FFFF_FFFF(44'b1) (3*PRECISION_BITS) + 11 (sticky bits)

    # Quiero que quede el MSB de las mantisas en el bit 33 o 44?
    # Para que quede en bit 33: m << (3 * PRECISION_BITS - 11), pues mantisa [10:0] -> 10 + (33-11) = 32 -> m [32:0] = [3 * PRECISION_BITS -1 :0]
    # Para que quede en bit 44: m << (3 * PRECISION_BITS)     , pues mantisa [10:0] -> 10 + (33)    = 43 -> m [43:0] = [3 * PRECISION_BITS + STICKY_BITS - 1 :0]

    # con sticky bits: 0xFFF_FFFF_FFFF(44'b1) para tener una precision maxima de 44 bits para mantisas (3*PRECISION_BITS) + 11 sticky bits
    # sin sticky bits: 0x1_FFFF_FFFF  (33'b1) para tener una precision maxima de 33 bits para mantisas (3*PRECISION_BITS)

    aligned_mantisas_w_sticky = [((implicit_mantisas[i] << (3 * PRECISION_BITS)) >> shifts[i]) & 0xFFF_FFFF_FFFF for i in range(len(implicit_mantisas))]

    # 0x7FF ultimos 11 bits
    sticky_buses = [aligned_mantisas_w_sticky[i] & 0x7FF for i in range(len(aligned_mantisas_w_sticky))]
    sticky_bits = [1 if stk_bus != 0 else 0 for stk_bus in sticky_buses]

    aligned_mantisas = [am >> PRECISION_BITS for am in aligned_mantisas_w_sticky] # sin los sticky bits -> 3*PRECISION_BITS, MSB en posicion 33

    print("Mantisas alineadas:")
    for i, value in enumerate(aligned_mantisas):
        print(f"  {i+1}: {pp_bits_spaced(value, 33)} (sticky bit: {sticky_bits[i]})")
    print("\n"+"-"*50+"\n")

    monitor.record("aligned_mantisas", f"{pp_bits_bus(aligned_mantisas, 33)}")
    monitor.record("sticky_bits", f"{pp_bits_bus(sticky_bits, 1)}")

    # ------------------------
    # suma de mantisas con signo
    # ------------------------

    suma_mantisas = 0
    mantisas_twos_complement_w_ovf = twos_complement(aligned_mantisas, signos_cambiados, (3 * PRECISION_BITS))

    monitor.record("mantisas_twos_comp_w_ovf", f"{pp_bits_bus(mantisas_twos_complement_w_ovf, 35)}")

    print("Mantisas signadas y alineadas:")
    for i, value in enumerate(mantisas_twos_complement_w_ovf):
        print(f"  {i+1}: {pp_hex(value, 36/4)} ({value})")
    
    print("\n"+"-"*50+"\n")

    # Generar vectores carry y save para LZA
    save, carry = add_4_signed_mantissas(mantisas_twos_complement_w_ovf, (3 * PRECISION_BITS) + 2)

    monitor.record("save", f"{pp_bits(save, 35)}")
    monitor.record("carry", f"{pp_bits(carry, 35)}")

    #suma_mantisas = carry +(bitwise) save
    suma_mantisas, carry_final = ripple_carry_adder(carry, save, (3 * PRECISION_BITS) + 2)


    # nunca deberiamos tener ovf? puede salir algun 1 por 2's comp?
    # assert(~carry_final)
    
    # ------------------------
    # Leading Zero Anticipator (LZA)
    # ------------------------

    lzcounter, sum_ovf, one_bit_less_error = LZA(carry, save, signos, (3 * PRECISION_BITS) + 2, monitor)

    monitor.record("LZA_zero_count", f"{pp_bits(lzcounter, 6)}") # acotado por ancho total bus = 35 -> $clog2(35)
    monitor.record("LZA_X",          f"{pp_bits(sum_ovf, 1)}")
    monitor.record("LZA_Y",          f"{pp_bits(one_bit_less_error, 1)}")

    # ------------------------
    # Normalizacion y calculo de signo y exponente final
    # ------------------------
    # Caso overflow en suma? deberiamos sumar a exponente final

    is_sum_negative = (suma_mantisas >> ((3 * PRECISION_BITS) + 1)) & 0x1 # bit de overflow mas significativo indica el signo del resultado final
    final_sign = pivot ^ is_sum_negative

    monitor.record("is_sum_negative", f"{pp_bits(is_sum_negative, 1)}")
    monitor.record("final_sign",      f"{pp_bits(final_sign, 1)}")

    if (is_sum_negative):
        abs_suma_mantissas = ((~suma_mantisas) & ((1 << ((3 * PRECISION_BITS) + 2)) - 1)) + 1 #complemento a dos para obtener el valor absoluto
    else:
        abs_suma_mantissas = suma_mantisas
    
    # LZC adjustment

    actual_lzcounter = lzcounter + one_bit_less_error

    normalized_mantisa = abs_suma_mantissas << actual_lzcounter

    print("Normalizacion mantisa:")
    print(f"    is_sum_negative: {is_sum_negative}")
    print(f"    Signo final: {final_sign}\n")
    print(f"    Mantisa con signo:   {pp_bits_spaced(suma_mantisas, (3 * PRECISION_BITS) + 2)}")
    print(f"    Mantisa absoluta:    {pp_bits_spaced(abs_suma_mantissas, (3 * PRECISION_BITS) + 2)}")
    print(f"    Mantisa normalizada: {pp_bits_spaced(normalized_mantisa, (3 * PRECISION_BITS) + 2)}\n")

    monitor.record("mantisa_sum"        ,f"{pp_bits(suma_mantisas     , 35)}")
    monitor.record("mantisa_abs"        ,f"{pp_bits(abs_suma_mantissas, 35)}")
    monitor.record("mantisa_normalized" ,f"{pp_bits(normalized_mantisa, 35)}")

    # encontre error en caso de dos maximos exponentes, ya que me dio como exponente final 31, esto en FP16 es +Inf
    max_exp = exponentes[shifts.index(0)]
    exp_final = max_exp + 2 - actual_lzcounter

    result_is_inf = exp_final > 30

    monitor.record("max_exp",   f"{pp_bits(max_exp,   5)}")
    monitor.record("final_exp", f"{pp_bits(exp_final, 6)}")

    print(f"Normalizacion exponente:")
    print(f"    Exponente maximo: {max_exp}")
    print(f"    Exponente final: {exp_final}")
    print("\n"+"-"*50+"\n")
    #print(f"Suma de mantisas con signo: {suma_mantisas:046b} ({suma_mantisas})")

    # ------------------------
    # Rounding
    # ------------------------

    # ------------------------
    # casos especiales 
    # ------------------------
    any_NaN = any(info.is_nan for info in nums_info)
    any_inf = any(info.is_inf for info in nums_info)
    if any_NaN:
        resultado_especial = "NaN"
    elif any_inf:
        if any_inf and any(info.is_inf and info.signo != signos[0] for info in nums_info):
            resultado_especial = "NaN" # Inf + (-Inf) = NaN
        else:
            resultado_especial = "Inf"
    else:
        resultado_especial = None

    # ------------------------
    # packing y generacion de resultado final
    # ------------------------

    result = 0
    monitor.record("output", f"{pp_bits(result, 16)}")

    if(resultado_especial != None):
        print(f"El resultado es especial: {resultado_especial}")
        if resultado_especial == "NaN":
            # En RISC-V, NaN se representa con el exponente al máximo y una mantisa no nula. El bit más significativo de la mantisa determina si es un NaN silencioso (quiet) o señalante (signalling).
            # Para un NaN silencioso, el bit más significativo de la mantisa es 1, y para un NaN señalante es 0.
            # Aquí podríamos decidir arbitrariamente usar un NaN silencioso para representar cualquier resultado NaN, o podríamos intentar preservar el tipo de NaN si es que uno de los operandos era un NaN señalante.
            if any(info.is_signalling for info in nums_info):
                # Si hay al menos un NaN señalante, podríamos optar por devolver un NaN señalante.
                resultado = 0x7E00  # Exponente máximo (0x1F) y mantisa con el bit más significativo en 0 (señalante)
            else:
                # Si no hay NaN señalante, devolvemos un NaN silencioso.
                resultado = 0x7F00  # Exponente máximo (0x1F) y mantisa con el bit más significativo en 1 (silencioso)
        elif resultado_especial == "Inf":
            resultado = 0
    else:
        print(f"Resultado normal, con signo final: {final_sign} y suma de mantisas: {suma_mantisas:046b} ({suma_mantisas})")
        # Aquí iría la normalización, ajuste de exponente, y packing final a formato flotante de 16 bits.
        # Esto implicaría:
        # 1. Normalizar la suma de mantisas (encontrar el primer bit 1 y ajustar el exponente en consecuencia)
        # 2. Ajustar el exponente basado en el número de shifts realizados durante la normalización
        # 3. Empaquetar el resultado final en formato flotante de 16 bits (signo, exponente ajustado, mantisa ajustada)

        # Convertir la suma de bits de vuelta a un número flotante
        #resultado = struct.unpack('>e', struct.pack('>H', suma_bits))[0]

    # Mostrar el resultado
    #print(f"La suma de {num1} y {num2} es: {resultado}")

if __name__ == "__main__":    main()