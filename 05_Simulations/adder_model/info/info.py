def special_cases_handling(nums_info):
    """
    Args:
        nums_info (list[Info]): List of info objects
    """
    canonical_qnan_bin  = 0x7E00
    pos_inf             = 0x7C00
    neg_inf             = 0xFC00

    for op in nums_info:
        if op.is_nan:
            # propagate the NaN, ensuring it's quietNaN
            return canonical_qnan_bin

    has_pos_inf = any(op.is_inf and op.signo == 0 for op in nums_info)
    has_neg_inf = any(op.is_inf and op.signo == 1 for op in nums_info)

    if has_pos_inf and has_neg_inf:
        # +inf + -inf = NaN
        return canonical_qnan_bin
    elif has_pos_inf:
        return pos_inf
    elif has_neg_inf:
        return neg_inf

    return None  # No special case detected

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
        self.is_normal      = (self.exponente != 0)    and (self.exponente != 0x1F)
        self.is_zero        = (self.exponente == 0)    and (self.mantisa == 0)
        self.is_subnormal   = (self.exponente == 0)    and (self.mantisa != 0)
        self.is_inf         = (self.exponente == 0x1F) and (self.mantisa == 0)
        self.is_nan         = (self.exponente == 0x1F) and (self.mantisa != 0)
        self.is_signalling  = self.is_nan and (self.mantisa & 0x200 == 0) and (self.mantisa & 0x1FF != 0) # bit más significativo de la mantisa es 0, y algun bit de fraccion es 1
        self.is_quiet       = self.is_nan and (self.mantisa & 0x200 == 1) # bit mas significativo de la mantisa es 1

    def set_is_boxed(self, value):
        self.is_boxed = value
