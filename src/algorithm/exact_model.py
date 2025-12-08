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
    M=1e5
    epsilon = 1e-6
    base_parking = vrp.parkings[0]
    ficticius_end_base_parking = 'FICT_END_' + base_parking
    dic_names = {i:i for i in vrp.get_location_names()} 
    dic_names[ficticius_end_base_parking] = base_parking

    V = vrp.get_location_names() + [ficticius_end_base_parking]
    F = vrp.chargers
    N = vrp.loadings + vrp.unloadings
    P = vrp.parkings + [ficticius_end_base_parking]

    if not P:
        raise ValueError("At least one parking location must exist")

    # -----------------------------
    # Create model
    # -----------------------------
    m = gp.Model("VRP")

    # Variables
    x = m.addVars(V, V, vtype=GRB.BINARY, name="x")   # route arcs
    z = m.addVars(F, vtype=GRB.BINARY, name="z")      # charger visit
    t = m.addVars(V, lb=0.0, ub=max_time_per_route, vtype=GRB.CONTINUOUS, name="t")  # arrival time
    m.update()

    # -----------------------------
    # Objective: travel cost + charging
    # -----------------------------
    obj = gp.quicksum(
        vrp.cost_matrix[dic_names[i], dic_names[j]] * x[i,j] for i in V for j in V if i != j) \
          + gp.quicksum(vrp.get_charging_cost(i) * z[i] for i in F)
    m.setObjective(obj, GRB.MINIMIZE)

    # -----------------------------
    # Constraints
    # -----------------------------
    # r0: initial time at base parking
    m.addConstr(t[base_parking] == 0, name="r0")

    # r1: each loading and unloading point is visited exactly once
    for j in N:
        m.addConstr(
            gp.quicksum(x[i, j] for i in V if i != j) == 1,
            name=f"visit_once_{j}"
        )

    # r2: flow conservation for all non-depot, non-fictitious nodes
    for j in V:
        if j not in [base_parking, ficticius_end_base_parking]:
            m.addConstr(
                gp.quicksum(x[i, j] for i in V if i != j)
                - gp.quicksum(x[j, h] for h in V if h != j) == 0,
                name=f"r2_{j}"
            )
            
    # r3: leave base parking exactly once
    m.addConstr(
        gp.quicksum(
            x[base_parking, j] 
            for j in V 
            if j not in [base_parking, ficticius_end_base_parking]
        ) == 1,
        name="r3"
    )
       
    # r4: return to fictitious end parking exactly once
    m.addConstr(
        gp.quicksum(
            x[i, ficticius_end_base_parking] 
            for i in V 
            if i not in [base_parking, ficticius_end_base_parking]
        ) == 1,
        name="r4"
    )

    # r5: fictitious end parking has no outgoing arcs
    for j in V:
        m.addConstr(
            x[ficticius_end_base_parking, j] == 0,
            name=f"r5_{j}"
        )

    # r6: unloading must be visited after loading
    for carga in vrp.loadings:
        for descarga in vrp.unloadings:
            m.addConstr(
                t[descarga] >= t[carga] + epsilon,
                name=f"precedence_{carga}_before_{descarga}"
            )

    # r7: time propagation along arcs (Big-M)
    for i in V:
        for j in V:
            if i != j:
                m.addConstr(
                    t[i] + vrp.time_matrix[dic_names[i], dic_names[j]] * x[i, j] 
                    - t[j] <= M * (1 - x[i, j]),
                    name=f"r7_{i}_{j}"
                )

    # r8.1: visit just one charger
    m.addConstr(
        gp.quicksum(z[j] for j in F) == 1,
        name="r8.1_single_charger"
    )
    # r8.2: visit just one charger
    m.addConstr(
        gp.quicksum(x[i,j] for i in F for j in N+P) == 1,
        name="r8.2_single_charger"
    )

    # r9: flag charger visit if arc arrives from N
    for i in F:
        for j in N + P:
            if i != j:
                m.addConstr(
                    x[i, j] <= z[i],
                    name=f"r9_{i}_{j}"
                )

    # r10: flag charger visit if arc arrives from N
    for i in N + P:
        for j in F:
            if i != j:
                m.addConstr(
                    x[i, j] <= z[j],
                    name=f"r10_{i}_{j}"
                )

    for j in V:
        if j not in [base_parking, ficticius_end_base_parking]:
            # Si ningún arco llega a j, t[j] = 0
            m.addConstr(
                t[j] <= gp.quicksum(x[i,j] for i in V if i != j) * M,
                name=f"t_zero_if_not_visited_{j}"
            )

    m.update()
    m.optimize()

    # -----------------------------
    # Print solution variables
    # -----------------------------
    # if m.status == GRB.OPTIMAL:
    #     print(f"Objective value: {m.objVal:.2f}\n")
    # 
    #     eps = 1e-6
    # 
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
    #        print("Status:", m.status, "SolCount:", m.SolCount)


    solution = VRPSolution(vrp)
        
    # Construimos la ruta desde arrival_times
    route = []

    # Agregamos el parking de inicio
    start_parking = vrp.parkings[0]
    route.append(start_parking)

    arrival_times = [(i, t[i].x) for i in V if t[i].x is not None and t[i].x > 0]
    arrival_times.sort(key=lambda tup: tup[1])
    # Añadimos nodos según arrival_times, ignorando t=0 si no es parking
    for node, t in arrival_times[:-1]:
        if t > 0 or vrp.is_type(node, 'parking'):
            route.append(node)

    # Aseguramos que termina en un parking
    route.append(start_parking)

    # Añadimos la ruta a la solución
    solution.add_route(route)
    solution.complete_feasibility()
    
    return solution
