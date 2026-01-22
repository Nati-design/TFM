from ortools.linear_solver import pywraplp
from src.models.vrp_instance import VRPInstance
from src.models.vrp_solution import VRPSolution

def exact_model_or_tools(
    vrp: VRPInstance,
    max_time_per_route=15 * 60,
    max_km_per_vehicle = 400,
    M=1e5,
    epsilon=1e-6,
    max_solver_time_sec=20*60
):
    # -----------------------------
    # Sets
    # -----------------------------
    base_parking = vrp.parkings[0]
    K = range(20)

    # Nodo ficticio por vehículo
    fict_end = {k: f"FICT_END_{k}" for k in K}

    dic_names = {i: i for i in vrp.get_location_names()}
    for k in K:
        dic_names[fict_end[k]] = base_parking

    V = vrp.get_location_names() + list(fict_end.values())
    N = vrp.loadings + vrp.unloadings
    P = vrp.parkings + list(fict_end.values())
    F = vrp.chargers
 
    # -----------------------------
    # Solver
    # -----------------------------
    solver = pywraplp.Solver.CreateSolver("SCIP")
    
    if not solver:
        raise Exception("SCIP solver not available")

    solver.SetTimeLimit(max_solver_time_sec * 1000)

    # -----------------------------
    # Variables
    # -----------------------------
    x = {}
    for k in K:
        for i in V:
            for j in V:
                if i != j:
                    x[i, j, k] = solver.BoolVar(f"x_{i}_{j}_{k}")

    t = {(i, k): solver.NumVar(0.0, max_time_per_route, f"t_{i}_{k}")
         for i in V for k in K}

    z = {(i, k): solver.BoolVar(f"z_{i}_{k}") for i in F for k in K}

    # -----------------------------
    # Objective
    # -----------------------------
    objective_terms = []

    for k in K:
        for i in V:
            for j in V:
                if i != j:
                    objective_terms.append(
                        vrp.cost_matrix[dic_names[i], dic_names[j]] * x[i, j, k]
                    )

    for i in F:
        for k in K:
            objective_terms.append(vrp.get_charging_cost(i) * z[i, k])
    
    # Coste fijo por vehículo usando x directamente
    fixed_vehicle_cost = 3000/20
    for k in K:
        objective_terms.append(
            fixed_vehicle_cost * solver.Sum(z[i, k] for i in F)
        )

    solver.Minimize(solver.Sum(objective_terms))
    # -----------------------------
    # Constraints
    # -----------------------------

    # Start time at depot
    for k in K:
        solver.Add(t[base_parking, k] == 0)

    # Cada cliente visitado exactamente una vez por algún vehículo
    for j in vrp.loadings:
        solver.Add(
            solver.Sum(x[i, j, k] for i in V if i != j for k in K) == 1
        )

    # Flujo de cada vehículo
    for k in K:
        for j in vrp.loadings + vrp.unloadings + vrp.chargers:
            solver.Add(
                solver.Sum(x[i, j, k] for i in V if i != j)
                - solver.Sum(x[j, h, k] for h in V if h != j)
                == 0
            )

    # Salida del depósito = 1
    for k in K:
        solver.Add(
            solver.Sum(x[base_parking, j, k]
                       for j in V
                       if j not in vrp.parkings) == 1
        )

    # Llegada al nodo ficticio = 1
    for k in K:
        solver.Add(
            solver.Sum(x[i, fict_end[k], k]
                       for i in V
                       if i not in [fict_end]
                       and i!= fict_end[k]) == 1
        )

    # Cada vehículo solo puede visitar su nodo ficticio
    for k in K:
        for j in fict_end.values():
            if j != fict_end[k]: 
                solver.Add(
                    solver.Sum(x[i, j, k]
                            for i in V
                            if  i!= j) == 0
                )

    # Nadie sale del nodo ficticio
    for k in K:
        for j in V:
            if j != fict_end[k]:
                solver.Add(x[fict_end[k], j, k] == 0)

    # # Tiempo MTZ
    for k in K:
        for i in V:
            for j in V:
                if i != j:
                    solver.Add(
                        t[i, k]
                        + vrp.time_matrix[dic_names[i], dic_names[j]] * x[i, j, k]
                        - t[j, k]
                        <= M * (1 - x[i, j, k])
                    )
    
    # Descarga despues de carga
    for k in K:
        for carga in vrp.loadings:
            for descarga in vrp.unloadings:
                # solo aplica si el vehículo va de carga a descarga
                solver.Add(
                    t[descarga, k] >= t[carga, k] + epsilon
                    - M * (1 - solver.Sum(x[i, carga, k] for i in V if i != carga))
                )
    
    # for k in K:
    #     # Si visita alguna carga, al menos una descarga debe ser visitada
    #     solver.Add(
    #         solver.Sum(x[i, carga, k] for carga in vrp.loadings for i in V if i != carga)
    #         <= solver.Sum(x[i, descarga, k] for descarga in vrp.unloadings for i in V if i != descarga)
    #     )
    
    # # Activación de cargadores
    for k in K:
        solver.Add(solver.Sum([z[j, k] for j in vrp.chargers]) <= 1)
        solver.Add(
            M*solver.Sum(x[i, c, k] for i in vrp.parkings + vrp.loadings + vrp.unloadings for c in vrp.chargers if i != c)
            >= solver.Sum(x[i, carga, k] for i in vrp.parkings + vrp.loadings for carga in vrp.loadings if i != carga)
        )

        for j in vrp.chargers:
            solver.Add(
                z[j, k] >= solver.Sum(x[i, j, k] for i in V if i != j)
            )

    # -----------------------------
    # Restricción: límite de kilómetros por vehículo
    # -----------------------------
    for k in K:
        solver.Add(
            solver.Sum(vrp.distance_matrix[dic_names[i], dic_names[j]] * x[i, j, k]
                    for i in V for j in V if i != j) <= max_km_per_vehicle
        )
        
    # # Tiempo activado - creo que esta restriccion no es estrictamente necesaria
    for k in K:
        for j in V:
            if j not in [base_parking, fict_end[k]]:
                solver.Add(
                    t[j, k] <= solver.Sum(x[i, j, k] for i in V if i != j) * M
                )

    # -----------------------------
    # Solve
    # -----------------------------
    status = solver.Solve()

    solution = VRPSolution(vrp)

    if status in (pywraplp.Solver.OPTIMAL, pywraplp.Solver.FEASIBLE):
        
        print("\n=== Rutas por vehículo (solo no vacías, incluyendo cargadores) ===")
        for k in K:
            # Diccionario “siguiente nodo” para el vehículo k
            next_node = {}
            for i in V:
                for j in V:
                    if i != j and x[i, j, k].solution_value() > 0.5:
                        next_node[i] = j

            # Reconstruir ruta siguiendo arcos activos
            route = [base_parking]
            current = base_parking

            while current in next_node:
                current = next_node[current]
                # Detener al llegar a nodo ficticio
                if str(current).startswith("FICT_END"):
                    break
                route.append(current)

            # Añadir nodo final del depósito
            route.append(base_parking)

            # Filtrar rutas vacías (sin clientes ni cargadores)
            if any(node in vrp.loadings + vrp.unloadings + vrp.chargers for node in route):
                print(f"Vehículo {k} ruta: {route}")
                solution.add_route(route)

        print("Valor de la función objetivo:", solver.Objective().Value())
        solution.complete_feasibility()
    else:
        print("No solution found")

    return solution
