[RISC-V: Changing the Way AI/ML Accelerators and Computing Infrastructure Are Built - David Chen](https://www.youtube.com/watch?v=lYa7j_iFf68&list=PL85jopFZCnbOSpq2ADYSFM7CXTyfopDh7&index=2)
- Matrix extension proposal(AME)
- Proyecto de ~ 3 años
- https://github.com/riscv-stc/riscv-matrix-spec
- berkly open source machine?
- Proyecto CHP procesador SCOOP = BOOM + Vector + Matrix

[Cervell™: Revolutionizing AI Compute with Scalable RISC-V NPU Architecture](https://www.youtube.com/watch?v=jwRL3b2PDg0&list=PL85jopFZCnbM7_1EulqQEDTTpU7yc-jfj&index=8)
- NPU? Neural processing unit
- RISC-V ISA is suitable for modern (parallel) workloads
- Vector instructions serve as GPGPU under same ISA
- Vector Instructions enable effective and efficient handling of ever growing amounts of data
- Standard Data type support: INT8-16-32-64, FP16-32-64
- NPU TOP's?
- ONNX? Execution provider?

[The case for Open Source Hardware at Thales: Motivations and Recent Miletones with CVA6](https://www.youtube.com/watch?v=k3tSK9-tRRE)
- Thales? international company in technology domains such as avionics, space, defense, communication, cyber security
- CV32A60X: Low area and High perfomance CVA6 Core
- CV64A60AX?
- Presentacion de productos. No tecnico

[CVA6S+: A Superscalar RISC-V Core with High-Throughput Memory Architecture](https://www.youtube.com/watch?v=eU16AtP6Fng&list=PL85jopFZCnbM7_1EulqQEDTTpU7yc-jfj&index=14)
- Superscalar dual-issue version of CVA6
- built on top of CVA6, introduces Register renaming, Improved branch redictor, ALU-ALU fowarding, FPU integration in superscalar mode
- Buen grafico que muestra los eventos/ciclos, normalizado a la cantidad total de ciclos. Muestra lo que esta pasando en cada ciclo
- Usan el grafico para identificar problemas. Una vez identificados los intentan resolver. Por ej, "Branch mispredictions cause the instruction queue to be empty => Use a better branch predictor
- Usaron Embench-IoT suite
- Introducen un private history predictor: Correccion de 82% a 92% 
- introducen register renaming
- introducen FPU support
- ALU-ALU fowarding: Eligieron algunas operaciones que evitan fowardear para mantener el critical path, ademas al introducir otra ALU estas dos pueden trabajar de manera independiente
- Reaizaron los benchmarks con cache's calientes (al igual que primer paper leido)
- Comparan espacio que ocupa, y frecuencia maxima entre ambos diseños
- Ademas introducen un diseño nuevo de cache: C. Fuguet, "HPDcache: Open-Source High-Performance L1 Data Cache for RISC-V Cores", ACM CF'23
- PULP Plataform?
- riccardo.tedeschi6@unibo.it

[RISC-V open designs and contributions to hardware security research and development activities](https://www.youtube.com/watch?v=4F8xiKcruV0)
- Hardware accelleration for Elliptic curves crypto(ECC)
- Hardware sharing for ML-KEM and HQC: a proyect that integrates two different cryptographic method that can be interchanged. Useful for quantum computing?
- ARSENE proyect: muchas cosas, en parte trabajar ne la ISA RISC-V para mejorar la perfomance y seguridad the algoritmos criptograficos
- FOWARD proyect: formal verification and physical attacks resilience of HW countermeasures

[Accelerating AI Models with Andes Matrix Multiplication and RISC-V Vector extensions](https://www.youtube.com/watch?v=vQ7P5jNy4qE)
- IREE framework?
- Andes Matrix Multiplication (AMM) is being designed to optimize tiled matrix multiplication
- tiles stored in RVV vector registers
- 2D load and store intructions
- AMM is scalable with vector registers, depends on the size of the vectors

[Developing Custom RISC-V ISA Extensions for General Embedded Image Processing Operations](https://www.youtube.com/watch?v=MwBmKXq8aLg)
- Explicacion de productos, nada muy tecnico

[Enhancing convolutional neural network computation with integrated matrix extension - Jim Ke, Andes](https://www.youtube.com/watch?v=Rp_Vxea3urc)
- no tenia ganas de mirarlo

