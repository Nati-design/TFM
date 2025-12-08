# TFM
Código usado en el TFM: "Comparación de técnicas exactas y heurísticas para la optimización de rutas de empresas de reparto de última milla".

1. En la carpeta datasets podemos encontrar los .pkl empleados para cada instancia y un .html que permite visualizar los datos en el mapa.
   Además, tenemos un programa generate_instances.py que permite generar las diferentes instancias.
2. En la carpeta src podemos encontrar:
   a) Una carpeta llamada algorithm con los programas exact_model.py, que calcula la solución con gurobi, nearest_neighbour.py, calcula la solución con el algoritmo del vecino más próximo, y two_opt.py, que la calcula para el algoritmo 2-opt.
   b) vrp_instance.py, utilizado para crear los archivos .html de cada instancia.
   c) vrp_solution.py, utilizado para crear los archivos .pkl y .html de los resultados.
3. main.py llama a los algoritmos y a los programas de representación para resolver el problema del EVRP. 
4. resultados.csv, archivo generado para comparar todas las soluciones de los algoritmos y sus tiempos de ejecución.   
5. En la carpeta results tenemos los resultados de cada método: gurobi, vecino más próximo y 2-opt.
   Tenemos los resultados en un archivo .pkl y en un .html que permite su visualización.
   
