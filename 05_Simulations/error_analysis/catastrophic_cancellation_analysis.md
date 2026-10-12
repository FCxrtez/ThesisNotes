# Casos Catastrophic cancellation graves

```bash
Vector Index : 144
Inputs (Hex)    : 78e2142b94a8f8e2
Inputs (Float16): [4.0000e+04, 1.0176e-03, -1.1368e-03, -4.0000e+04]
Expected (GT)   : 87d0  (-1.1921e-04)
Actual (HW)     : 8400  (-6.1035e-05)
ULP Error    : 976
```

```bash
Vector Index : 344
Inputs (Hex)    : 795883158164f958
Inputs (Float16): [4.3776e+04, -4.7028e-05, -2.1219e-05, -4.3776e+04]
Expected (GT)   : 8479  (-6.8247e-05)
Actual (HW)     : 8000  (-0.0000e+00)
ULP Error    : 1145
```