import struct
from math import copysign

MAN_BITS = 10
EXP_BITS = 5
PRECISION_BITS = MAN_BITS + 1


class Info:
    is_normal     = False # is the value normal
    is_subnormal  = False # is the value subnormal
    is_zero       = False # is the value zero
    is_inf        = False # is the value infinity
    is_nan        = False # is the value NaN
    is_signalling = False # is the value a signalling NaN
    is_quiet      = False # is the value a quiet NaN
    is_boxed      = False # is the value properly NaN=Boxed (RISC-V specific)

    def __init__(self, signo, exponente, mantisa):
        self.signo = signo
        self.exponente = exponente
        self.mantisa = mantisa
        self.classify()
    
    def classify(self):
        self.is_normal = (self.exponente != 0 ) and (self.exponente != 0x1F)
        self.is_zero = (self.exponente == 0) and (self.mantisa == 0)
        self.is_subnormal = (self.exponente == 0) and (self.mantisa != 0)
        self.is_inf = (self.exponente == 0x1F) and (self.mantisa == 0)
        self.is_nan = (self.exponente == 0x1F) and (self.mantisa != 0)
        self.is_signalling = self.is_nan and (self.mantisa & 0x200 == 0) and (self.mantisa & 0x1FF != 0) # bit más significativo de la mantisa es 0, y algun bit de fraccion es 1
        self.is_quiet = self.is_nan and (self.mantisa & 0x200 == 1) # bit mas significativo de la mantisa es 1

    def set_is_boxed(self, value):
        self.is_boxed = value

def pp_bits(value, length):
    """
    Formats an integer as a fixed-length binary string.
    """
    # The '0' pads with zeros, {length} sets the width, and 'b' formats as binary
    return f"{value:0{int(length)}b}"

def pp_bits_spaced(value, length):
    """
    Formats an integer as a fixed-length binary string, separated by spaces every 4 bits.
    """
    mask = (1<<length)-1 # 00...00011111 para length = 5
    masked_value = value & mask

    num_spaces = (length - 1) // 4
    total_length = length + num_spaces

    return f"{masked_value:0{total_length}_b}".replace("_", " ")

def pp_hex(value, num_digits=4):
    """
    Formats an integer as a fixed-length hexadecimal string.
    num_digits=4 is perfect for 16-bit numbers (since 1 hex digit = 4 bits).
    """
    # The 'X' formats it as uppercase hex. Use 'x' for lowercase.
    return f"0x{value:0{int(num_digits)}X}"

def float_to_bits(f):
    """Convierte un número flotante a su representación en bits."""
    return struct.unpack('>H', struct.pack('>e', f))[0]
    # >e: big-endian _Float16, >H: big-endian unsigned short (16 bits)

def exp_align(e):
    shifts = [0]*4
    diferences = []
    for i in range(len(e)):
        for j in range(i+1, len(e)):
            diferences.append((i+1, j+1, e[i] - e[j]))
    
    print("Diferencias de exponentes:")
    for i, j, diff in diferences:
        print(f"  exp.{i} - exp.{j}    =    {pp_bits(e[i-1], 5)} - {pp_bits(e[j-1], 5)}    =    {pp_bits(diff, 6)} == {diff}")
    print("\n")

    signs = [False if copysign(1,dif[2]) == -1 else True for dif in diferences] # False/True para que is_max solo contenga booleanos.

    is_max = [False]*4
    is_max[0] = signs[0] and signs[1] and signs[2]
    is_max[1] = not signs[0] and signs[3] and signs[4]
    is_max[2] = not signs[1] and not signs[3] and signs[5]
    is_max[3] = not signs[2] and not signs[4] and not signs[5]
    
    print("el maximo exponente en numero:")
    print("  " + str(is_max))

    if is_max[0]: # el maximo es el 1
        shifts[1] = diferences[0][2]
        shifts[2] = diferences[1][2]
        shifts[3] = diferences[2][2]
    elif is_max[1]: # el maximo es el 2
        shifts[0] = -diferences[0][2]
        shifts[2] = diferences[3][2]
        shifts[3] = diferences[4][2]
    elif is_max[2]: # el maximo es el 3
        shifts[0] = -diferences[1][2]
        shifts[1] = -diferences[3][2]
        shifts[3] = diferences[5][2]
    elif is_max[3]: # el maximo es el 4
        shifts[0] = -diferences[2][2]
        shifts[1] = -diferences[4][2]
        shifts[2] = -diferences[5][2]

    print("shifts:")
    print("  " + str(shifts))
    print("\n"+"-"*50+"\n")

    return shifts

def csa_3to2(a, b, c):
    """Reduces three inputs to two: Sum and Carry."""
    # S = a ^ b ^ c
    save = a ^ b ^ c

    # C = (a&b | b&c | a&c) << 1
    # We shift left because the carry at bit i belongs to position i+1
    carry = ((a & b) | (b & c) | (a & c)) << 1
    return save, carry

def add_4_signed_mantissas(mantisas, bit_width=35):
    """
    Simulates a 4-input CSA tree for signed numbers.
    Assumes inputs are integers representing two's complement mantissas.
    """
    # 1. Sign extension mask (to keep within bit_width)
    # Necesito mascara si ya agregue mits de mascara y ovf previamente? No
    mask = (1 << bit_width ) - 1
    
    # 2. First Level: Reduce 4 inputs to 3
    # We treat m1, m2, m3 first
    s1, c1 = csa_3to2(mantisas[0] & mask, mantisas[1] & mask, mantisas[2] & mask)
    
    # 3. Second Level: Reduce the result + m4 to 2 (The final S and C)
    # Now we have s1, c1, and m4
    s_final, c_final = csa_3to2(s1 & mask, c1 & mask, mantisas[3] & mask)

    print(f"Resultado CSA Tree:")
    print(f"  save:  {pp_bits_spaced(s_final, bit_width)}")
    print(f"  carry: {pp_bits_spaced(c_final, bit_width)}")
    print("\n"+"-"*50+"\n")
    return s_final & mask, c_final & mask

def full_adder(a, b, c_in):
    """Single bit-slice of a Full Adder."""
    s = a ^ b ^ c_in
    c_out = (a & b) | (b & c_in) | (a & c_in)
    return s, c_out

def ripple_carry_adder(a, b, width=35):
    """
    Simulates a Ripple Carry Adder (CPA) bit-by-bit.
    
    Args:
        a: Integer representing the first operand.
        b: Integer representing the second operand.
        width: The hardware bit-width boundary.
        
    Returns:
        sum_result: The final sum bounded to the hardware width.
        carry_out: The final carry-out bit from the MSB.
    """
    sum_result = 0
    carry = 0  # Initial carry-in at bit 0 is always 0 for standard addition
    
    for i in range(width):
        # 1. Extract the i-th bit of A and B
        bit_a = (a >> i) & 1
        bit_b = (b >> i) & 1
        
        # 2. Pass them through the Full Adder along with the previous carry
        s, carry = full_adder(bit_a, bit_b, carry)
        
        # 3. Place the resulting sum bit into the correct position of our final result
        sum_result |= (s << i)
        
    # Mask to ensure the result strictly fits our hardware bounds
    mask = (1 << width) - 1
    return sum_result & mask, carry

def twos_complement(a_mantisas, signos, bit_mask=33):
    # Implementation for two's complement conversion
    twos_complement_mantisas= []

    precision_w_ovf = bit_mask + 2
    mask_w_ovf = (1 << precision_w_ovf) - 1

    for am, s in zip(a_mantisas, signos):
        if s == 1: # negative number
            one_complement = am ^ mask_w_ovf # invertimos los bits dentro de la mascara
            twos_comp = (one_complement + 1) & mask_w_ovf

        else: # positive number, no change
            twos_comp = (am & mask_w_ovf)
        
        # twos_comp_w_sign = twos_comp | (s << (precision_w_ovf))
        # No debo agregar el signo, los bits the ovf ya indican el signo correcto. En paper de Tenca el bit 
        twos_complement_mantisas.append(twos_comp)

        print(f"Signo: {s}")
        print(f"Mantisa original:\n      {pp_bits_spaced(am, bit_mask)}")
        print(f"Complemento a dos con ovf: \n    {pp_bits_spaced(twos_comp, bit_mask+2)}\n")
        #print(f"Complemento a dos con signo:\n   {pp_bits_spaced(twos_comp_w_sign, bit_mask+3)}\n")
    
    print("\n"+"-"*50+"\n")
    return twos_complement_mantisas

def LZA(a, b, signos, bit_width=35):
    """
    Simulates a Leading Zero Anticipator (LZA) with error detection proposed by Yao Tao and Gao Deyuan in "A Novel Concurrent Error Detection Circuit for Leading Zero Anticipator" for the carry-save addition result.
    
    Args:
        a: Integer representing the save bits from the CSA tree.
        b: Integer representing the carry bits from the CSA tree.
        bit_width: The hardware bit-width boundary.
    """
    def get_bit(value, index):
        return (value >> index) & 1

    T, G, Z = [0]*bit_width, [0]*bit_width, [0]*bit_width
    if (all(signos) or all(map(lambda s: 1 if s == 0 else 0, signos))): # si todos los signos son iguales, entonces es una suma, sino es una resta
        V = False
    else:
        V = True

    # segun IA no es necesario pues es manejado por el arbol de CSA
    # c = b if V else not b
    c = b

    # generamos vectores T, G, Z
    #for i in range(bit_width):
    #    bit_a = (a >> (bit_width - 1 - i)) & 0x1
    #    bit_c = (c >> (bit_width - 1 - i)) & 0x1
    #
    #    T[i] =         bit_a ^ bit_c
    #    G[i] =         bit_a & bit_c
    #    Z[i] = int(not(bit_a | bit_c))

    T = a ^ c
    G = a & c
    Z = int(~(a | c))
    
    print("LZA:")

    print(f"  T: {pp_bits_spaced(T, bit_width)}")
    print(f"  G: {pp_bits_spaced(G, bit_width)}")
    print(f"  Z: {pp_bits_spaced(Z, bit_width)}\n")
    print(f" flag V: {V} -> {"eff Substraction" if V else "eff Addition" } \n ")
    #for i in range(bit_width-1, 0, -1):
    #    print(get_bit(Z, i), end="")
    #print("\n")

    F = 0
    for i in range(bit_width):     
        # Fetch bits once per iteration to make the logic readable
        # If out of bounds, default to 0
        t_prev = get_bit(T, i-1) if i > 0 else 0
        t_next = get_bit(T, i+1) if i < bit_width - 1 else 0

        g_prev = get_bit(G, i-1) if i > 0 else 0
        g_i    = get_bit(G, i)
        g_next = get_bit(G, i+1) if i < bit_width - 1 else 0

        z_prev = get_bit(Z, i-1) if i > 0 else 0
        z_i    = get_bit(Z, i)
        z_next = get_bit(Z, i+1) if i < bit_width - 1 else 0

        # Use ^ 1 for bitwise inversion instead of Python's 'not'
        if i == 0:
            # LSB: f_0 = T_1(G_0 V + Z_0) + ~T_1(Z_0 V + G_0)
            f_i = (t_next & ((g_i & V) | z_i)) | ((t_next ^ 1) & ((z_i & V) | g_i))

        elif i == bit_width - 1:
            # MSB: f_n-1 = V(G_n-1 ~Z_n-2 + Z_n-1 ~G_n-2) + ~V(Z_n-1 ~Z_n-2 + ~Z_n-1)
            term_V = V & ((g_i & (z_prev ^ 1)) | (z_i & (g_prev ^ 1)))
            term_not_V = (V ^ 1) & ((z_i & (z_prev ^ 1)) | (z_i ^ 1))
            f_i = term_V | term_not_V

        else:
            # General: f_i = T_i-1(G_i ~Z_i+1 + Z_i ~G_i+1) + ~T_i-1(Z_i ~Z_i+1 + G_i ~G_i+1)
            term_T = t_prev & ((g_i & (z_next ^ 1)) | (z_i & (g_next ^ 1)))
            term_not_T = (t_prev ^ 1) & ((z_i & (z_next ^ 1)) | (g_i & (g_next ^ 1)))
            f_i = term_T | term_not_T

        F |= (f_i << i)

    # Calculating the leading-zero number
    zeroes = LCD(F, bit_width)

    # "Concurrent" error detection

    # Pre-encoding (deberian tener dos bits mas)

    # string resultado positivo
    Gp_p = G
    Gp_n = Z & (T << 1)
    Gp_z = (Gp_p | Gp_n) ^ 1
    # string resultado negativo
    Gn_p = Z
    Gn_n = G & (T << 1)
    Gn_z = (Gn_p | Gn_n) ^ 1




    print(f"  F: {pp_bits_spaced(F, bit_width)}\n")

def main():
    signos, exponentes, mantisas, mantisas_signadas = [], [], [], []

    num1 = float(input("Ingrese el primer número flotante: "))
    num2 = float(input("Ingrese el segundo número flotante: "))
    num3 = float(input("Ingrese el tercer número flotante: "))
    num4 = float(input("Ingrese el cuarto número flotante: "))
    print("-"*50+"\n")

    b_nums = [float_to_bits(num) for num in [num1, num2, num3, num4]]

    for i in b_nums:
        signo = (i >> 15) & 0x1 # 1 bit
        exponente = (i >> 10) & 0x1F # 5 bits
        mantisa = i & 0x3FF # 10 bits

        signos.append(signo)
        exponentes.append(exponente)
        mantisas.append(mantisa)
    
    for i,(bn, n) in enumerate(zip(b_nums, [num1, num2, num3, num4])):
        print(f"Representacion en bits de {n}: {pp_bits(bn, 16)}")
        print(f"  signo: {pp_bits(signos[i], 1)}, exponente: {pp_bits(exponentes[i], 5)}, mantisa: {pp_bits_spaced(mantisas[i], 10)}\n")

    print("\n"+"-"*50+"\n")

    # ------------------------
    # clasificacion de numeros y calculo de mantisa implicita
    # ------------------------
    nums_info = [Info(signos[i], exponentes[i], mantisas[i]) for i in range(4)]

    implicit_mantisas = []
    for e, m in enumerate(mantisas):
        implicit_mantisa = m | nums_info[e].is_normal << (PRECISION_BITS - 1)
        implicit_mantisas.append(implicit_mantisa)

        print(f"Operando {e+1}:")
        print(f"  Bit implicito: {int(nums_info[e].is_normal)}")
        print(f"  Mantisa original: {pp_bits_spaced(m, 10)}")
        print(f"  Mantisa con bit implicito: {pp_bits_spaced(implicit_mantisa, 11)}\n")

    print("\n"+"-"*50+"\n")

    # ------------------------
    # diferencia de exponentes
    # ------------------------

    shifteos = exp_align(exponentes)

    # ------------------------
    # cambio de signos (operando 0 como pivote)
    # ------------------------

    piv = signos[0]
    signos_cambiados = [s ^ piv for s in signos] # XOR para cambiar el signo si es diferente al pivote

    print(f"Signos originales: {signos}")
    print(f"pivote (signo 1er operando): {piv}, signos cambiados: {signos_cambiados}\n")

    # ------------------------
    # alineacion de mantisas
    # ------------------------
    # Comentarios sv:
    #       Each addend is right-shifted according to the exponent difference. Up to p bits
    #       are shifted out and compressed into a sticky bit.
    #       BEFORE THE EXPONENT SHIFT:
    #       | packed_mantissa[i] | 000..000 |
    #        <-        p       -> <- 3p+4 ->
    #       AFTER THE SHIFT:
    #       | 000..........000 | packed_mantissa[i] | 000...............0GR |  sticky bits  |
    #        <-   shifts[i]  -> <-         p      -> <-  2p+4-shifts[i]   -> <-  up to p  ->

    # Hacemos solo implicit_mantisas[i] << 3 * PRECISION_BITS pues a izq deben quedar 1 bit signo + 2 bit overflow que enmascaramos luego
    # 0x1_FFFF_FFFF(33'b1) para tener una precision maxima de 33 bits para mantisas (3*PRECISION_BITS) [cambiado a 0xFFF_FFFF_FFFF]
    # Deberia agregar una precision extra para los sticky bits? 0xFFF_FFFF_FFFF(44'b1) (3*PRECISION_BITS) + 11 (sticky bits)

    # Quiero que quede el MSB de las mantisas en el bit 33 o 44?
    # Para que quede en bit 33: m << (3 * PRECISION_BITS - 11), pues mantisa [10:0] -> 10 + (33-11) = 32 -> m [32:0] = [3 * PRECISION_BITS -1 :0]
    # Para que quede en bit 44: m << (3 * PRECISION_BITS)     , pues mantisa [10:0] -> 10 + (33)    = 43 -> m [43:0] = [3 * PRECISION_BITS + STICKY_BITS - 1 :0]

    # con sticky bits: 0xFFF_FFFF_FFFF(44'b1) para tener una precision maxima de 44 bits para mantisas (3*PRECISION_BITS) + 11 sticky bits
    # sin sticky bits: 0x1_FFFF_FFFF  (33'b1) para tener una precision maxima de 33 bits para mantisas (3*PRECISION_BITS)

    aligned_mantisas_w_sticky = [((implicit_mantisas[i] << (3 * PRECISION_BITS)) >> shifteos[i]) & 0xFFF_FFFF_FFFF for i in range(len(implicit_mantisas))]

    # 0x3FF ultimos 11 bits
    sticky_buses = [aligned_mantisas_w_sticky[i] & 0x3FF for i in range(len(aligned_mantisas_w_sticky))]
    sticky_bits = [1 if stk_bus != 0 else 0 for stk_bus in sticky_buses]

    aligned_mantisas = [am >> PRECISION_BITS for am in aligned_mantisas_w_sticky] # sin los sticky bits -> 3*PRECISION_BITS, MSB en posicion 33
    print("Mantisas alineadas:")
    for i, value in enumerate(aligned_mantisas):
        print(f"  {i+1}: {pp_bits_spaced(value, 33)} (sticky bit: {sticky_bits[i]})")
    print("\n"+"-"*50+"\n")


    # ------------------------
    # suma de mantisas con signo
    # ------------------------

    suma_mantisas = 0
    mantisas_twos_complement_w_ovf = twos_complement(aligned_mantisas, signos_cambiados, (3 * PRECISION_BITS))

    print("Mantisas signadas y alineadas:")
    for i, value in enumerate(mantisas_twos_complement_w_ovf):
        print(f"  {i+1}: {pp_hex(value, 36/4)} ({value})")
    
    print("\n"+"-"*50+"\n")

    carry, save = add_4_signed_mantissas(mantisas_twos_complement_w_ovf, (3 * PRECISION_BITS) + 2)

    # Generar vectores carry y save para LZA

    lzcounter = LZA(carry, save, signos, (3 * PRECISION_BITS) + 2)

    #suma_mantisas = carry +(bitwise) save
    suma_mantisas, carry_final = ripple_carry_adder(carry, save, (3 * PRECISION_BITS) + 2)
    
    #exp_final = exponentes[shifteos.index(0)] >> lzcounter ?

    #print(f"Suma de mantisas con signo: {suma_mantisas:046b} ({suma_mantisas})")

    signo_final = 0
    copysign(signo_final, suma_mantisas)

    signo_final = signo_final ^ piv

    # ------------------------
    # suma de mantisas con signo
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
        print(f"Resultado normal, con signo final: {signo_final} y suma de mantisas: {suma_mantisas:046b} ({suma_mantisas})")
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