# Seccion III.Methodology
Atencion a como se definen las funciones para definir el framework de optimizacion. Estas usan el IPC y la utilizacion de recursos.
Como aseguramos que esta expresion en la correcta o que no se pueda mejorar? Como explorar el espacio de funciones y determinar su correctitud?

# Seccion IV.Results & Insights
Que nos dice que se encuentren buenos resultados al subir la iteracion de los workloads a ~1.000.000? Es razonable asumir que un workload va a ser ejecutado tantas veces? Como podemos saber que no nos resulta mas beneficioso un branch predictor con mejor desempeño de un cold-start?

**the importance of selecting appropiate iteration counts during architectural evaluation to avoid misleading conclusions about processor performance**

## Parameter sensitive analysis
Como determinaron que debian analizar el impacto **combinado** de integer operation latency, integer multiply latency, and memory write latency. Suponiendo que deciden cual es el punto de mejor/mas conveniente performance, como lo consiguen luego en el hw?
Al jugar con estos parametros parece que existen cieros parametros inaceptables, poco realistas:
 " We constrained our optimization to physically realistic values, excluding impractical configurations like 12-cycle DDR3readsat50MHz,whilemaintaining fixed architectural parameters to prevent overfitting. "

Es decir, es crucial elegir bien la cantidad de iteraciones de ejecucion de workload, y elegir bien la variacion de parametros pues deben ser realistas, etc.. Sino las pruebas pueden sugerir algun cambio que en la practica es imposible de aprovechar, ya que partimos de datos incorrectos.

## Hyperparameter optimization insights

### Resource optimization

En este paper se eligio el IPC y la utilizacion de recursos como parametros a optimizar. Que otros parametros podrian tomarse como indicadores de mejoras? Supongo que son dependientes del objetivo de la investigacion, en este caso la inestigacion era bastante general.

Se realizo "sensitivity analysis"