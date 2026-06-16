from pp_functions.pp_functions import pp_bits_spaced, pp_bits


def get_bit(value, index):
    return (value >> index) & 1

def gen_F(G, T, Z, V, bit_width):
    F = 0
    for i in range(bit_width):
        # If out of bounds, default to 0
        t_prev = get_bit(T, i - 1) if i > 0 else 0
        t_next = get_bit(T, i + 1) if i < bit_width - 1 else 0


        g_prev = get_bit(G, i - 1) if i > 0 else 0
        g_i    = get_bit(G, i)
        g_next = get_bit(G, i + 1) if i < bit_width - 1 else 0


        z_prev = get_bit(Z, i - 1) if i > 0 else 0
        z_i    = get_bit(Z, i)
        z_next = get_bit(Z, i + 1) if i < bit_width - 1 else 0


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
    return F

def LZD(F, bit_width):
    count = 0
    for i in range(bit_width - 1, -1, -1):
        if get_bit(F, i) == 0:
            count += 1
        else:
            break
    return count

def simulate_reduction_tree(leaf_nodes):
    current_layer = leaf_nodes
    capa = 0


    while len(current_layer) > 1:
        next_layer = []
        capa += 1

        # reducimos hasta nodo raiz
        for j in range(0, len(current_layer), 2):

            # Agarramos de a pares left y right
            if j + 1 < len(current_layer):
                # Since you appended from i=0 (LSB) up to MSB,
                # the higher index (j+1) represents the more significant bits (Left branch).
                # The lower index (j) represents the less significant bits (Right branch).
                left_node = current_layer[j + 1]
                right_node = current_layer[j]


                z_ = left_node[0] & right_node[0]
                p_ = (left_node[0] & right_node[1]) | (left_node[1] & right_node[0])
                n_ = left_node[2] | (left_node[0] & right_node[2])
                y_ = left_node[3] | (left_node[0] & right_node[3]) | (left_node[1] & right_node[2])


                next_layer.append((z_, p_, n_, y_))
            else:
                # Si el número de nodos es impar, el último nodo se propaga sin cambios a la siguiente capa.
                # next_layer.append(current_layer[j])
                left_node = (1, 0, 0, 0) # nodo neutro para la operacion de reduccion
                right_node = current_layer[j]


                z_ = left_node[0] & right_node[0]
                p_ = (left_node[0] & right_node[1]) | (left_node[1] & right_node[0])
                n_ = left_node[2] | (left_node[0] & right_node[2])
                y_ = left_node[3] | (left_node[0] & right_node[3]) | (left_node[1] & right_node[2])


                next_layer.append((z_, p_, n_, y_))

        print(f"Capa {capa}-esima:")
        for i, node in enumerate(next_layer):
            print(f"  Nodo {i}: {node}")
        current_layer = next_layer


    return current_layer[0]

def pre_encoding(G, T, Z, V, bit_width, monitor = None):
    mask = (1 << (bit_width + 1)) - 1

    # Agrandamos vectores ( G_n1 = [G, 0] )
    G_n1 = G << 1
    T_aligned = T | (V << bit_width)
    Z_n1 = Z << 1


    # Casos suma y resta con resultado positivo/negativo
    # suma o resta con resultado positivo
    G_Gp = G_n1 | V
    Z_Gp = Z_n1 | (V ^ 1)
    #resta - resultado negativo
    G_Gn = G_n1 | 0 # si resNegativa -> G_-1 = 0, si suma -> G_-1 = 0
    Z_Gn = Z_n1 | 1 # si resNegativa -> Z_-1 = 1, si suma -> Z_-1 = 1

    # string resultado positivo
    Gp_p = G_Gp # pues no cambia para suma o resta con resultado positivo, resta con res negativo no aplica
    Gp_n = Z_Gp & T_aligned # Zi & T(i+1)
    Gp_z = ~(Gp_p | Gp_n) & mask

    # string resultado negativo
    Gn_p = Z_Gn # si resNegativa -> Z_-1 = 0, si suma -> Z_-1 = 1
    Gn_n = G_Gn & T_aligned # Gi & T(i+1)
    Gn_z = ~(Gn_p | Gn_n) & mask


    print("Pre-encoding:")
    print(f"  Gp_p: {pp_bits_spaced(Gp_p, bit_width + 1)}")
    print(f"  Gp_n: {pp_bits_spaced(Gp_n, bit_width + 1)}")
    print(f"  Gp_z: {pp_bits_spaced(Gp_z, bit_width + 1)}\n")
    print(f"  Gn_p: {pp_bits_spaced(Gn_p, bit_width + 1)}")
    print(f"  Gn_n: {pp_bits_spaced(Gn_n, bit_width + 1)}")
    print(f"  Gn_z: {pp_bits_spaced(Gn_z, bit_width + 1)}\n")
    print("-" * 50 + "\n")

    monitor.record("LZA_Gp_p", f"{pp_bits(Gp_p, 36)}")
    monitor.record("LZA_Gp_n", f"{pp_bits(Gp_n, 36)}")
    monitor.record("LZA_Gp_z", f"{pp_bits(Gp_z, 36)}")

    monitor.record("LZA_Gn_p", f"{pp_bits(Gn_p, 36)}")
    monitor.record("LZA_Gn_n", f"{pp_bits(Gn_n, 36)}")
    monitor.record("LZA_Gn_z", f"{pp_bits(Gn_z, 36)}")

    return (Gp_p, Gp_n, Gp_z), (Gn_p, Gn_n, Gn_z)


def error_detection(Gp, Gn, V, Z_n1, bit_width):
    # Primero generamos los vectores para cada nodo de cada arbol
    inp_nodes_pos, inp_nodes_neg = [], []
    for i in range(bit_width + 1):
        # (z, p, n, y)
        inp_nodes_pos.append((get_bit(Gp[2], i), get_bit(Gp[0], i), get_bit(Gp[1], i), 0))
        inp_nodes_neg.append((get_bit(Gn[2], i), get_bit(Gn[0], i), get_bit(Gn[1], i), 0))

    assert(len(inp_nodes_pos) == bit_width + 1)
    assert(len(inp_nodes_neg) == bit_width + 1)
    
    print("   " + "-" * 25 + "\n")
    print("Reduccion arbol para resultado positivo:")
    root_pos = simulate_reduction_tree(inp_nodes_pos)
    print("   " + "-" * 25 + "\n")
    print("Reduccion arbol para resultado negativo:")
    root_neg = simulate_reduction_tree(inp_nodes_neg)
    print("   " + "-" * 25 + "\n")


    P_p, N_p, Y_p = root_pos[1], root_pos[2], root_pos[3]
    Y_n = root_neg[3]


    X = (V ^ 1) & Y_p
    Y = (V & (Y_p | Y_n)) | ((V ^ 1) & (N_p & Z_n1))


    return X, Y

def LZA(a, b, signos, bit_width=35, monitor = None):
    """
    Simulates a Leading Zero Anticipator (LZA) with concurrent error detection.
    """
    if all(signos) or all(map(lambda s: 0 if s == 1 else 1, signos)):
        V = False
    else:
        V = True

    monitor.record("V", f"{pp_bits(V, 1)}")

    c = b

    T = a ^ c
    G = a & c
    Z = int(~(a | c))


    print("LZA:")
    print(f"  T: {pp_bits_spaced(T, bit_width)}")
    print(f"  G: {pp_bits_spaced(G, bit_width)}")
    print(f"  Z: {pp_bits_spaced(Z, bit_width)}\n")
    print(f" flag V: {V} -> {'eff Substraction' if V else 'eff Addition'} \n ")

    F = gen_F(G, T, Z, V, bit_width)

    monitor.record("LZA_F", pp_bits(F, bit_width))

    print(f"  F: {pp_bits_spaced(F, bit_width)}\n")

    # Calculating the leading-zero number
    zeroes = LZD(F, bit_width)


    # "Concurrent" error detection
    # Pre-encoding (deberian tener un bit mas, el -1)
    Gp, Gn = pre_encoding(G, T, Z, V, bit_width, monitor)

    Z_n1 = (Z >> bit_width) & 1 # Z_-1 es el bit mas significativo de Z_n1
    X, Y = error_detection(Gp, Gn, V, Z_n1, bit_width)

    print(f"Resultados LZA:")
    print(f"  Cantidad de ceros a la izquierda: {zeroes}")
    print(f"  Señal de error X (overflow en suma): {X}")
    print(f"  Señal de error Y (one bit less): {Y}")
    print("\n" + "-" * 50 + "\n")

    return zeroes, X, Y
