from src.vrp_solution import VRPSolution

def two_opt(solution):
    """
    Aplica el algoritmo 2-opt sobre una solución VRP inicial,
    respetando las restricciones:
      - Loadings antes que unloadings
      - Un solo charger por ruta
      - Cada ruta empieza y termina en parking
    
    Parámetros:
        solution (VRPSolution): Solución inicial generada (por NN, por ejemplo)
    
    Retorna:
        VRPSolution: Nueva solución optimizada
    """
    instance = solution.instance
    new_solution = VRPSolution(instance)

    for route in solution.routes:
        improved = True
        best_route = route.copy()

        while improved:
            improved = False
            n = len(best_route)
            for i in range(1, n-2):          # no tocar el primer parking
                for j in range(i+1, n-1):    # no tocar el último parking
                    # Evitamos invertir un segmento que rompa el orden loadings -> unloadings
                    segment = best_route[i:j+1]
                    types = [instance.locations[loc]['node'] for loc in segment]

                    if 'unloading' in types and 'loading' in types:
                        continue  # no invertir si hay mezcla de load/unload

                    # Solo invertir si no hay más de un charger en el segmento
                    if types.count('charger') > 1:
                        continue

                    # Realizar inversión
                    new_route = best_route[:i] + segment[::-1] + best_route[j+1:]

                    # Calcular nueva distancia
                    old_dist = sum(instance.get_distance(best_route[k], best_route[k+1]) for k in range(n-1))
                    new_dist = sum(instance.get_distance(new_route[k], new_route[k+1]) for k in range(n-1))

                    if new_dist < old_dist:
                        best_route = new_route
                        improved = True
                        break  # reiniciar búsqueda
                if improved:
                    break

        # Agregar la ruta optimizada a la nueva solución
        new_solution.add_route(best_route)

    # Revisar factibilidad completa
    new_solution.complete_feasibility()

    return new_solution
