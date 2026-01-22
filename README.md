# TFM
Código usado en el TFM: "Optimización de rutas de camión eléctrico: comparación de métodos exactos y heurísticos".

1. En la carpeta datasets podemos encontrar:
	a) reales: carpeta con las instancias reales y los resultados de la ejecución de los tres métodos (nearest_neighbour, or_tools y two_opt).
	b) sintéticos_10_15_20: carpeta con las instancias sintéticas y los resultados de la ejecución de los tres métodos (nearest_neighbour, or_tools y two_opt ).
	c) generate_instances.py: programa para generar las instancias.
   
2. En la carpeta src podemos encontrar:
	a) algorithm: carpeta con el programa para los tres métodos (nearest_neighbour, or_tools y two_opt, y sus variantes para múltiples vehículos.)
	b) models: una carpeta con los programas vrp_instance.py, utilizado para crear los archivos .html de cada instancia, vrp_solution.py, utilizado para crear los archivos .pkl y .html de los resultados. También se definen funciones para comprobar la factibilidad de las soluciones.
   
4. main.py: programa principal que llama a todos los algoritmos. 

   
