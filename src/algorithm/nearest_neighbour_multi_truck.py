from src.models.vrp_instance import VRPInstance
from src.models.vrp_solution import VRPSolution
from typing import Union

def nearest_neighbour_multi_truck(instance_or_solution: Union[VRPInstance, VRPSolution], max_km_per_vehicle: float | None = None):
    """
    Acepta VRPInstance (desde cero) O VRPSolution (usa solution.instance).
    """
    # 
    if isinstance(instance_or_solution, VRPSolution):
        instance = instance_or_solution.instance 
    else:
        instance = instance_or_solution
    
    if max_km_per_vehicle is None:
        max_km_per_vehicle = instance.max_km_per_vehicle

    solution = VRPSolution(instance)

    unvisited_loadings = set(instance.loadings)
    unvisited_unloadings = set(instance.unloadings)
    depot = instance.parkings[0]

    while unvisited_loadings or unvisited_unloadings:
        route = [depot]
        current_loc = depot
        current_distance = 0.0
        added_any = False

        # Loadings phase
        while unvisited_loadings:
            next_loc = min(
                unvisited_loadings,
                key=lambda loc: instance.get_distance(current_loc, loc)
            )
            if current_distance + instance.get_distance(current_loc, next_loc) + instance.get_distance(next_loc, depot) > max_km_per_vehicle:
                break
            route.append(next_loc)
            current_distance += instance.get_distance(current_loc, next_loc)
            current_loc = next_loc
            unvisited_loadings.remove(next_loc)
            added_any = True

        # Unloadings phase
        while unvisited_unloadings:
            next_loc = min(
                unvisited_unloadings,
                key=lambda loc: instance.get_distance(current_loc, loc)
            )
            if current_distance + instance.get_distance(current_loc, next_loc) + instance.get_distance(next_loc, depot) > max_km_per_vehicle:
                break
            route.append(next_loc)
            current_distance += instance.get_distance(current_loc, next_loc)
            current_loc = next_loc
            unvisited_unloadings.remove(next_loc)
            added_any = True

        # Insert charger
        if instance.chargers:
            charger = min(
                instance.chargers,
                key=lambda c: instance.get_distance(current_loc, c)
            )
            best_pos = 1
            min_increase = float("inf")
            for i in range(1, len(route)):
                prev = route[i - 1]
                next_ = route[i]
                increase = (
                    instance.get_distance(prev, charger)
                    + instance.get_distance(charger, next_)
                    - instance.get_distance(prev, next_)
                )
                if current_distance + increase + instance.get_distance(route[-1], depot) <= max_km_per_vehicle:
                    if increase < min_increase:
                        min_increase = increase
                        best_pos = i
            if best_pos is not None:  # Siempre True si best_pos se asignó
                route.insert(best_pos, charger)
                current_distance += min_increase

        # End route
        route.append(depot)
        current_distance += instance.get_distance(current_loc, depot)

        if not added_any:
            raise ValueError("A node cannot be added without exceeding max_km_per_vehicle")

        solution.add_route(route)

    solution.complete_feasibility()
    return solution
