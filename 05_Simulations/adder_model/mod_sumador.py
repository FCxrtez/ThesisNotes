from .adders import add_4_signed_mantissas, ripple_carry_adder
from .LZA import LZA
from .pp_functions import pp_bits, pp_bits_bus, pp_bits_spaced, pp_hex, float_to_bits, bits_to_float
from .info import Info, special_cases_handling
from .exp_man_fun import exp_align, twos_complement
from .rounding import round

# ------------------------
# Format Constants
# ------------------------

MAN_BITS = 10
EXP_BITS = 5
PRECISION_BITS = MAN_BITS + 1
FTZ_EN = 0

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
    monitor.record("mantisas"  , f"{pp_bits_bus(mantisas, 10)}")

    print("\n")
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
    
    monitor.record("implicit_mantisas", f"{pp_bits_bus(implicit_mantisas, 11)}")

    exponentes_exp_align = []

    for e in exponentes:
        if e == 0:
            exponentes_exp_align.append(1)
        else:
            exponentes_exp_align.append(e)

    print("\n"+"-"*50+"\n")

    monitor.record("exponentes", f"{pp_bits_bus(exponentes_exp_align, 5)}")

    # ------------------------
    # Exponent difference
    # ------------------------

    shifts, is_max = exp_align(exponentes_exp_align)

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
    #        <-        p       -> <- 2p+3 ->
    #       AFTER THE SHIFT:
    #       | 000..........000 | packed_mantissa[i] | 000...............0GR |  sticky bits  |
    #        <-   shifts[i]  -> <-         p      -> <-  2p+3-shifts[i]   -> <-  up to p  ->

    # Hacemos solo implicit_mantisas[i] << 3 * PRECISION_BITS pues a izq deben quedar 1 bit signo + 2 bit overflow que enmascaramos luego
    # 0x1_FFFF_FFFF({33{1'b1}}) para tener una precision maxima de 33 bits para mantisas (3*PRECISION_BITS) [cambiado a 0xFFF_FFFF_FFFF]
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

    monitor.record("mantisas_twos_comp_w_ovf", f"{pp_bits_bus(mantisas_twos_complement_w_ovf, 36)}")

    print("Mantisas signadas y alineadas:")
    for i, value in enumerate(mantisas_twos_complement_w_ovf):
        print(f"  {i+1}: {pp_bits_spaced(value, 36)}")
    print("\n"+"-"*50+"\n")

    save, carry = add_4_signed_mantissas(mantisas_twos_complement_w_ovf, (3 * PRECISION_BITS) + 3)

    monitor.record("save", f"{pp_bits(save, 36)}")
    monitor.record("carry", f"{pp_bits(carry, 36)}")

    suma_mantisas, _ = ripple_carry_adder(carry, save, (3 * PRECISION_BITS) + 3)

    # ------------------------
    # Leading Zero Anticipator (LZA)
    # ------------------------

    lzcounter, sum_ovf, one_bit_less_error, eff_substraction = LZA(
            carry     = carry                    ,
            save      = save                     ,
            signos    = signos                   ,
            bit_width = (3 * PRECISION_BITS) + 3 ,
            monitor   = monitor
        )

    monitor.record("LZA_zero_count", f"{pp_bits(lzcounter, 6)}") # acotado por ancho total bus = 36 -> $clog2(36)
    monitor.record("LZA_X",          f"{pp_bits(sum_ovf, 1)}")
    monitor.record("LZA_Y",          f"{pp_bits(one_bit_less_error, 1)}")

    actual_lzcounter = lzcounter + one_bit_less_error

    # ------------------------
    # Normalizacion, calculo de signo y exponente final
    # ------------------------

    is_sum_negative = (suma_mantisas >> ((3 * PRECISION_BITS) + 2)) & 0x1 
    final_sign      = pivot ^ is_sum_negative

    monitor.record("is_sum_negative", f"{pp_bits(is_sum_negative, 1)}")
    monitor.record("final_sign",      f"{pp_bits(final_sign, 1)}")

    if (is_sum_negative):
        abs_suma_mantissas = ((~suma_mantisas) & ((1 << ((3 * PRECISION_BITS) + 3)) - 1)) + 1
    else:
        abs_suma_mantissas = suma_mantisas
    
    enable_flush    = False
    max_exp         = exponentes[shifts.index(0)]
    eff_exp         = max_exp if max_exp > 0 else 1

    tentative_exp = eff_exp + 3 - actual_lzcounter

    if tentative_exp >= 1:
        # resultado normal
        shift_amount = actual_lzcounter
        exp_post_norm = tentative_exp
        enable_flush = False

    else:
        # resultado subnormal o cero
        if FTZ_EN:
            enable_flush = True
            shift_amount = 0
            exp_post_norm = 0

        else:
            enable_flush = False
            exp_post_norm = 0
            shift_amount = eff_exp + 3 - 1

    if enable_flush:
        normalized_mantisa = 0
    else:
        normalized_mantisa = abs_suma_mantissas << shift_amount

    print("Normalizacion mantisa:")
    print(f"    is_sum_negative: {is_sum_negative}")
    print(f"    Signo final: {final_sign}\n")
    print(f"    Mantisa con signo:   {pp_bits_spaced(suma_mantisas, (3 * PRECISION_BITS) + 3)}")
    print(f"    Mantisa absoluta:    {pp_bits_spaced(abs_suma_mantissas, (3 * PRECISION_BITS) + 3)}")
    print(f"    Mantisa normalizada: {pp_bits_spaced(normalized_mantisa, (3 * PRECISION_BITS) + 3)}\n")

    monitor.record("mantisa_sum"        ,f"{pp_bits(suma_mantisas     , 36)}")
    monitor.record("mantisa_abs"        ,f"{pp_bits(abs_suma_mantissas, 36)}")
    monitor.record("mantisa_normalized" ,f"{pp_bits(normalized_mantisa, 36)}")

    # encontre error en caso de dos maximos exponentes, ya que me dio como exponente final 31, esto en FP16 es +Inf

    monitor.record("max_exp",       f"{pp_bits(max_exp,   5)}")
    monitor.record("exp_post_norm", f"{pp_bits(exp_post_norm, 6)}")
    monitor.record("FTZ",           f"{pp_bits(enable_flush, 1)}")

    print(f"Normalizacion exponente:")
    print(f"    Exponente maximo: {max_exp}")
    print(f"    Exponente post-normalizacion: {exp_post_norm}")
    print(f"    Flush to zero: {True if enable_flush else False}")
    print("\n"+"-"*50+"\n")

    # ------------------------
    # Rounding
    # ------------------------

    # 7FE000000 = descartamos el primer bit (un 1) normalizado, nos quedamos con los siguientes 10 bits
    abs_val_masked = (normalized_mantisa & 0x7FE000000) >> 25
    g_bit          = (normalized_mantisa & 0x001000000)>> 24
    s_bit          = 1 if (normalized_mantisa & 0x000FFFFFF) > 0 else 0

    # or the sticky bits generated when aligning and the one of the normalized value
    RS_bits = (g_bit << 1) | (s_bit | any(sticky_bits))

    abs_rounded, exact_zero, rounded_sign = round(
            abs_value=abs_val_masked,
            abs_mask=0x7FF,
            RS_bits=RS_bits,
            sign=final_sign,
            effective_subtraction=eff_substraction
        )
    
    round_ovf = abs_rounded & 0x400
    
    if round_ovf:
        # caso especial para numeros subnormales?
        exp_final = exp_post_norm + 1
    else:
        exp_final = exp_post_norm
    
    monitor.record("final_exp",  f"{pp_bits(exp_final, 6)}")

    result_is_inf = exp_final > 30

    monitor.record("abs_rounded", f"{        pp_bits(abs_rounded, 10)  }")
    monitor.record("round_ovf", f"{          pp_bits(round_ovf, 1)     }")
    monitor.record("rounded_sign", f"{       pp_bits(rounded_sign, 1)  }")
    monitor.record("exact_zero", f"{         pp_bits(exact_zero, 1)    }")
    monitor.record("inf_result", f"{         pp_bits(result_is_inf, 1) }")

    print("Pre-redondeo:")
    print(f"    mantisa abs: {               pp_bits_spaced(abs_val_masked, 10) }")
    print(f"    Round/Sticky bits: {         pp_bits(RS_bits, 2)                }")
    print("Post-redondeo:")
    print(f"    mantisa redondeada: {        pp_bits_spaced(abs_rounded, 10)  }")
    print(f"    ovf por redondeo (bit 11): { pp_bits(round_ovf, 1)            }")
    print(f"    signo redondeado: {          pp_bits(rounded_sign, 1)         }")
    print(f"    cero exacto: {               True if exact_zero else False    }")
    print(f"    Result is inf: {             True if result_is_inf else False }")

    print("\n"+"-"*50+"\n")

    # ------------------------
    # casos especiales 
    # ------------------------
    special_cases_result = special_cases_handling(nums_info, result_is_inf, rounded_sign)

    # ------------------------
    # packing y generacion de resultado final
    # ------------------------

    result  = rounded_sign << (EXP_BITS + MAN_BITS)
    result |= (exp_final & 0x1F)<< MAN_BITS
    result |= (abs_rounded & 0x3FF)


    if(special_cases_result != None):
        print(f"Resultado especial:")
        print(f"    Resultado empaquetado: {pp_bits(special_cases_result,16)}")
        print(f"    Con valor de {bits_to_float(special_cases_result)}")
        result = special_cases_result
    else:
        print(f"Resultado normal:")
        print(f"    signo final: {rounded_sign}")
        print(f"    exponente final: {pp_bits(exp_final, 5)}")
        print(f"    mantisa final: {pp_bits_spaced(abs_rounded, 10)}\n")

        print(f"Resultado empaquetado: {pp_bits(result,16)}")
        print(f"Con valor de {bits_to_float(result)}")
        print(f"{num1} + {num2} + {num3} + {num4}")
        print("redondeado como:")
        print(f"{bits_to_float(binary_nums[0])} + {bits_to_float(binary_nums[1])} + {bits_to_float(binary_nums[2])} + {bits_to_float(binary_nums[3])} = {bits_to_float(result)}")
        print("\n" + "-"*50 + "\n")
        
    monitor.record("output", f"{pp_bits(result, 16)}")

if __name__ == "__main__":    main()