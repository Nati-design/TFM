from src.models.vrp_solution import VRPSolution

def two_opt_multi_truck(solution: VRPSolution, max_km_per_vehicle: float | None = None) -> VRPSolution:
    """
    Applies the 2-opt algorithm to each route in a VRP solution,
    respecting the following constraints:
      - All loadings must come before unloadings in each route
      - At most one charger per route
      - Each route starts and ends at a parking
      - Total route distance must not exceed max_km_per_vehicle (if specified)

    Parameters:
        solution (VRPSolution): Initial VRP solution with one or multiple routes
        max_km_per_vehicle (float | None): Maximum allowed route distance in km.
                                            If None, no limit is enforced.

    Returns:
        VRPSolution: New solution with optimized routes
    """
    instance = solution.instance
    optimized_solution = VRPSolution(instance)

    for route in solution.routes:
        best_route = route.copy()
        improved = True

        while improved:
            improved = False
            n = len(best_route)

            # Skip first and last parking
            for i in range(1, n - 2):
                for j in range(i + 1, n - 1):
                    segment = best_route[i:j+1]
                    segment_types = [instance.locations[loc]['node'] for loc in segment]

                    # Constraint: no loading after unloading
                    if 'loading' in segment_types and 'unloading' in segment_types:
                        continue

                    # Constraint: at most one charger
                    if segment_types.count('charger') > 1:
                        continue

                    # Create new route by reversing the segment
                    new_route = best_route[:i] + segment[::-1] + best_route[j+1:]

                    # Compute total distance for new route
                    new_distance = sum(
                        instance.get_distance(new_route[k], new_route[k+1])
                        for k in range(len(new_route)-1)
                    )

                    # If a max distance is set, skip if violated
                    if max_km_per_vehicle is not None and new_distance > max_km_per_vehicle:
                        continue

                    # Compute old route distance
                    old_distance = sum(
                        instance.get_distance(best_route[k], best_route[k+1])
                        for k in range(len(best_route)-1)
                    )

                    # Accept new route if it improves distance
                    if new_distance < old_distance:
                        best_route = new_route
                        improved = True
                        break  # restart search after improvement
                if improved:
                    break

        # Add optimized route to the new solution
        optimized_solution.add_route(best_route)

    # Check full solution feasibility
    optimized_solution.complete_feasibility()
    return optimized_solution
