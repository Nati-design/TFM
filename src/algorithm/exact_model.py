import gurobipy as gp
from gurobipy import GRB
from src.vrp_instance import VRPInstance
from src.vrp_solution import VRPSolution

def exact_model(vrp: VRPInstance, max_time_per_route=15*60, M=1e5, epsilon = 1e-6):
    """
    Solve VRP using Gurobi and return a VRPSolution object.
    Uses tuple-key matrices (i,j) consistent with VRPInstance.
    """
    # -----------------------------
    # Sets
    # -----------------------------
    
    max_time_per_route=15*60
    L=1e5
    epsilon = 1e-6
    base_parking = vrp.parkings[0]
    ficticius_end_base_parking = 'FICT_END_' + base_parking
    dic_names = {i:i for i in vrp.get_location_names()} 
    dic_names[ficticius_end_base_parking] = base_parking

    V = vrp.get_location_names() + [ficticius_end_base_parking]
    F = vrp.chargers
    N = vrp.loadings + vrp.unloadings
    P = vrp.parkings + [ficticius_end_base_parking]
    M = range(20) #vehículos

    if not P:
        raise ValueError("At least one parking location must exist")

    # -----------------------------
    # Create model
    # -----------------------------
    model = gp.Model("VRP")

    # Variables
    x = model.addVars(M, V, V, vtype=GRB.BINARY, name="x")   # route arcs
    z = model.addVars(M, F, vtype=GRB.BINARY, name="z")      # charger visit
    t = model.addVars(M, V, lb=0.0, ub=max_time_per_route, vtype=GRB.CONTINUOUS, name="t")  # arrival time
    model.update()

    # -----------------------------
    # Objective: travel cost + charging
    # -----------------------------
    obj = gp.quicksum(
        vrp.cost_matrix[dic_names[i], dic_names[j]] * x[m,i,j] for m in M for i in V for j in V if i != j) \
          + gp.quicksum(vrp.get_charging_cost(i) * z[m,i] for m in M for i in F)
    model.setObjective(obj, GRB.MINIMIZE)

    # -----------------------------
    # Constraints
    # -----------------------------
    # r0: initial time at base parking
    for m in M:
        model.addConstr(t[m, base_parking] == 0, name="r0")

    # r1: each loading and unloading point is visited exactly once
    for j in N:
        model.addConstr(
            gp.quicksum(x[m, i, j] for m in M for i in V if i != j) == 1,
            name=f"visit_once_{j}"
        )

    # r2: flow conservation for all non-depot, non-fictitious nodes
    for m in M:
        for j in V:
            if j not in [base_parking, ficticius_end_base_parking]:
                model.addConstr(
                    gp.quicksum(x[m,i, j] for i in V if i != j)
                    - gp.quicksum(x[m,j, h] for h in V if h != j) == 0,
                    name=f"r2_{j}"
                )
            
    # r3: leave base parking exactly once
    for m in M:
        model.addConstr(
            gp.quicksum(
                x[m,base_parking, j] 
                for j in V 
                if j not in [base_parking, ficticius_end_base_parking]
            ) <= 1, ## Así no se usan todos los camiones obligatoriamente
            name="r3"
        )
       
    # r4: return to fictitious end parking exactly once
    for m in M:
        model.addConstr(
            gp.quicksum(
                x[m,i, ficticius_end_base_parking] 
                for i in V 
                if i not in [base_parking, ficticius_end_base_parking]
            ) <= 1,## Así no se usan todos los camiones obligatoriamente
            name="r4"
        )

    # r5: fictitious end parking has no outgoing arcs
    for m in M:
        for j in V:
            model.addConstr(
                x[m,ficticius_end_base_parking, j] == 0,
                name=f"r5_{j}"
            )

    # r6: unloading must be visited after loading
    for m in M:
        for carga in vrp.loadings:
            for descarga in vrp.unloadings:
                model.addConstr(
                    t[m,descarga] >= t[m,carga] + epsilon,
                    name=f"precedence_{carga}_before_{descarga}"
                )

    # r7: time propagation along arcs (Big-L)
    for m in M:
        for i in V:
            for j in V:
                if i != j:
                    model.addConstr(
                        t[m,i] + vrp.time_matrix[dic_names[i], dic_names[j]] * x[m,i, j] 
                        - t[m,j] <= L * (1 - x[m,i, j]),
                        name=f"r7_{i}_{j}"
                    )

    # r8.1: visit just one charger
    for m in M:
        model.addConstr(
            gp.quicksum(z[m,j] for j in F) == 1,
            name="r8.1_single_charger"
        )
    # r8.2: visit just one charger
    for m in M:
        model.addConstr(
            gp.quicksum(x[m,i,j] for i in F for j in N+P) == 1,
            name="r8.2_single_charger"
        )

    # r9: flag charger visit if arc arrives from N
    for m in M:
        for i in F:
            for j in N + P:
                if i != j:
                    model.addConstr(
                        x[m,i, j] <= z[m,i],
                        name=f"r9_{i}_{j}"
                    )

    # r10: flag charger visit if arc arrives from N
    for m in M:
        for i in N + P:
            for j in F:
                if i != j:
                    model.addConstr(
                        x[m,i, j] <= z[m,j],
                        name=f"r10_{i}_{j}"
                    )
    for m in M:
        for j in V:
            if j not in [base_parking, ficticius_end_base_parking]:
                # Si ningún arco llega a j, t[j] = 0
                model.addConstr(
                    t[m,j] <= gp.quicksum(x[m,i,j] for i in V if i != j) * L,
                    name=f"t_zero_if_not_visited_{j}"
                )

    # Restricción de batería: longitud de ruta ≤ 400 km por vehículo
    max_route_length = 400.0
    for m in M:
        model.addConstr(
            gp.quicksum(
                vrp.distance_matrix[dic_names[i], dic_names[j]] * x[m, i, j]
                for i in V for j in V if i != j
            ) <= max_route_length,
            name=f"battery_limit_{m}"
        )
            
    # Limitar el tiempo de ejecución a 15 minutos (900 segundos)
    model.Params.TimeLimit = 900
    model.update()
    model.optimize()

    # -----------------------------
    # Print solution variables
    # -----------------------------
    # if model.status == GRB.OPTIMAL:
    #     print(f"Objective value: {model.objVal:.2f}\n")
    # 
    #     eps = 1e-6
    # z
    #     # Imprimir arcos seleccionados
    #     print("Selected arcs (x[i,j] = 1):")
    #     for i in V:
    #         for j in V:
    #             if i != j and x[i,j].x is not None and x[i,j].x > eps:
    #                 print(f"x[{i},{j}] = {x[i,j].x:.2f}")
    # 
    #     # Imprimir arcos seleccionados
    #     print("Selected cahrger:")
    #     for i in F:
    #         if z[i].x > eps:
    #             print(f"z[{i}] = {z[i].x:.2f}")
    # 
    #     # Crear lista de (nombre, tiempo) y ordenar
    #     arrival_times = [(i, t[i].x) for i in V if t[i].x is not None and t[i].x > 0]
    #     arrival_times.sort(key=lambda tup: tup[1])  # orden creciente
    # 
    #     # Imprimir tiempos ordenados
    #     print("\nArrival times (sorted):")
    #     for loc, time in arrival_times:
    #         print(f"t[{loc}] = {time:.2f} min")
    #
    #    else:
    #        print("No optimal solution found")
    #        print("Status:", model.status, "SolCount:", model.SolCount)


    solution = VRPSolution(vrp)
    start_parking = vrp.parkings[0]
    status = model.Status
    if status not in [GRB.OPTIMAL, GRB.SUBOPTIMAL, GRB.TIME_LIMIT]:
        # No hay solución que leer
        print(f"No feasible solution. Status = {status}, SolCount = {model.SolCount}")
        return None
    


    for m in M:
        # tiempos de llegada del vehículo k
        arrival_times_m = [
            (i, t[m, i].x) for i in V
            if t[m, i].x is not None and t[m, i].x > 0
        ]
        arrival_times_m.sort(key=lambda tup: tup[1])

        # si el vehículo no visita nada, saltar
        if not arrival_times_m:
            continue

        route_m = [start_parking]
        for node, tau in arrival_times_m[:-1]:
            if tau > 0 or vrp.is_type(node, 'parking'):
                route_m.append(node)
        route_m.append(start_parking)

        solution.add_route(route_m)

    solution.complete_feasibility()

    return solution
