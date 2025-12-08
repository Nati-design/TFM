from src.vrp_instance import VRPInstance
from src.vrp_solution import VRPSolution


def nearest_neighbour(instance: VRPInstance):
    """
    Construye una solución VRP usando el algoritmo del vecino más próximo,
    asegurando que cada ruta:
      - Comience en un parking
      - Visite primero todos los loadings
      - Luego todos los unloadings
      - Incluya exactamente un charger en la mejor posición para minimizar distancia
      - Termine en un parking
    
    Parámetros:
        instance (VRPInstance): La instancia del VRP.
    
    Retorna:
        VRPSolution: La solución generada.
    """
    solution = VRPSolution(instance)

    # Nodos que aún deben visitarse
    unvisited_loadings = set(instance.loadings)
    unvisited_unloadings = set(instance.unloadings)

    while unvisited_loadings or unvisited_unloadings:
        # Inicializar ruta en un parking
        start_parking = instance.parkings[0]
        route = [start_parking]
        current_loc = start_parking

        # ---- Fase de loadings ----
        while unvisited_loadings:
            next_loc = min(unvisited_loadings, key=lambda loc: instance.get_distance(current_loc, loc))
            route.append(next_loc)
            current_loc = next_loc
            unvisited_loadings.remove(next_loc)

        # ---- Fase de unloadings ----
        while unvisited_unloadings:
            next_loc = min(unvisited_unloadings, key=lambda loc: instance.get_distance(current_loc, loc))
            route.append(next_loc)
            current_loc = next_loc
            unvisited_unloadings.remove(next_loc)

        # ---- Insertar un solo charger en la mejor posición ----
        if instance.chargers:
            charger = min(instance.chargers, key=lambda c: instance.get_distance(route[-1], c))
            
            # Elegir la posición que minimice la distancia incremental
            best_pos = 1
            min_increase = float('inf')
            for i in range(1, len(route)):
                prev = route[i-1]
                next_ = route[i]
                increase = instance.get_distance(prev, charger) + instance.get_distance(charger, next_) - instance.get_distance(prev, next_)
                if increase < min_increase:
                    min_increase = increase
                    best_pos = i
            route.insert(best_pos, charger)

        # ---- Terminar la ruta en parking ----
        end_parking = start_parking
        route.append(end_parking)

        # Agregar ruta a la solución
        solution.add_route(route)

    # Revisar factibilidad completa
    solution.complete_feasibility()

    return solution
