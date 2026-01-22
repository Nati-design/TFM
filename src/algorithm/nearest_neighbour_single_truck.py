from src.models.vrp_instance import VRPInstance
from src.models.vrp_solution import VRPSolution


def nearest_neighbour_single_truck(instance: VRPInstance) -> VRPSolution:
    """
    Builds a VRP solution using the Nearest Neighbour algorithm, ensuring that each route:
      - Starts at a parking location
      - Visits all loading nodes first
      - Then visits all unloading nodes
      - Includes exactly one charger at the best position to minimize distance
      - Ends at a parking location
    
    Parameters:
        instance (VRPInstance): The VRP instance.
    
    Returns:
        VRPSolution: The generated VRP solution.
    """
    solution = VRPSolution(instance)

    # Nodes that still need to be visited
    unvisited_loadings = set(instance.loadings)
    unvisited_unloadings = set(instance.unloadings)

    while unvisited_loadings or unvisited_unloadings:
        # Initialize a new route starting from a parking
        start_parking = instance.parkings[0]
        route = [start_parking]
        current_loc = start_parking

        # ---- Loadings phase ----
        while unvisited_loadings:
            next_loc = min(
                unvisited_loadings,
                key=lambda loc: instance.get_distance(current_loc, loc)
            )
            route.append(next_loc)
            current_loc = next_loc
            unvisited_loadings.remove(next_loc)

        # ---- Unloadings phase ----
        while unvisited_unloadings:
            next_loc = min(
                unvisited_unloadings,
                key=lambda loc: instance.get_distance(current_loc, loc)
            )
            route.append(next_loc)
            current_loc = next_loc
            unvisited_unloadings.remove(next_loc)

        # ---- Insert a single charger at the best position ----
        if instance.chargers:
            # Choose the charger closest to the last node in the route
            charger = min(
                instance.chargers,
                key=lambda c: instance.get_distance(route[-1], c)
            )

            # Find the position in the route that minimizes incremental distance
            best_pos = 1
            min_increase = float('inf')
            for i in range(1, len(route)):
                prev = route[i - 1]
                next_ = route[i]
                increase = (
                    instance.get_distance(prev, charger)
                    + instance.get_distance(charger, next_)
                    - instance.get_distance(prev, next_)
                )
                if increase < min_increase:
                    min_increase = increase
                    best_pos = i

            route.insert(best_pos, charger)

        # ---- End the route at the parking ----
        route.append(start_parking)

        # Add the route to the solution
        solution.add_route(route)

    # Check full feasibility of the solution
    solution.complete_feasibility()

    return solution
