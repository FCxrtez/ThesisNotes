# FPNew
En base a la arquitectura se me ocurrio la posibilidad de optimizar la unidad para un tipo de benchmark especifico, por ejemplo para workloads relacionados a IA/matrices, cambiando la distribuccion de las slices dentro de cada grupo.
N tipos de formatos en diseño
N slices por grupo + 1 "universal merged"
Podriamos dejar mas slices para un tipo de FP en base a alguna distribucion sobre las instrucciones tomadas en workloads en 8-bit
De esta manera la tesis logra tocar un punto mas de relevancia cientifica, sobre el rendimiento de IA en hw especifico. Dejando algunas unidades de calculo universal de manera que sea "completa" la FPU.
Este es un tipo de idea utilizado comunmente en arquitectura? Investigar en Hennesy-Patterson?
Puede que sea una burrada.
Puede no valerlo y llegar a resultados extremadamente malos, idea rara.
Yendo mas alla, se podria cuestionar la cantidad de slices por grupo de computo, dejando nuevamente unidades universales y asignando una mayor cantidad de slices a calculos comunes.
De la manera que trabaja ahora la FPU es que estos distintas slices pueden calcular en paralelo mientras que sean distintos formatos. Puede que este cambio que quiero introducir genere demasiada latencia para los otros formatos, los que dejen de tener slice exclusiva.
Siendo que el paper de FPNew hace enfeasis en su bajo de consumo energetico, puede que al optimizar y acelerar calculos se logre un menor consumo energetico por la rapidez del calculo (menor tiempo total)?
Para identificar si sera una buena idea, buscar primero la distribucion de operaciones, buscar benchmarks disponibles

***Individual lanes with merged slices have the pecular property of differing in bit width, and each lane needs support for a different set of formats***
No hay forma de crear slices universales? Que distintos data path compartan misma lane, supongo que a costo del area. 

Cantidad de lanes ***k*** dependen de la longitud del formato y de el ***widthFPU***.

lanes adentro de merged slices son todas distintas, se adaptan para tomar los distintos fomrato. La slice k soporta formato mas chico,
slice k/2 soporta formato mas chico y el mas grande siguiente, k/4 3 formatos mas chicos etc. ***Fig2/4b***

Fowarding dentro de FPU?
Segun chatgpt se puede complicar por los distintos fomratos, no solo que distintas instrucciones pueden tener distintos formatos, que deberia tenerse en cuenta (capaz se puede permitir fowarding entre unidades de mismo formato)

**Notably, fpu width can be chosen much wider than the largest supported format** 
notar que esto ademas esta limitado por la longitud de el registro vectorial con el que trabajemos, pues no tiene sentido tener vectores a los que no podamos pasarle los parametros de manera optima

Para tener como referencia cuantas slices podemos meter al reemplazar por otro podriamos basarnos en el area que ocupa cada slice
Asi si
Area(1 slice 32-bit) = 2 * Area(1 slice 8-bit)
Podemos mantener el area del procesador constante al sacar 1 slice de 32-bit y poner 2 de 8-bit
 