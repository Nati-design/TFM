from src.models.vrp_instance import VRPInstance
from src.models.vrp_solution import VRPSolution

# Algorithm imports
from src.algorithm.nearest_neighbour_single_truck import nearest_neighbour_single_truck as nn_single
from src.algorithm.nearest_neighbour_multi_truck import nearest_neighbour_multi_truck as nn_multi
from src.algorithm.two_opt_single_truck import two_opt_single_truck as two_opt_single
from src.algorithm.two_opt_multi_truck import two_opt_multi_truck as two_opt_multi
from src.algorithm.or_tools import exact_model_or_tools

import pickle
from pathlib import Path
import time
import pandas as pd


# ---------------------------
# Helper function
# ---------------------------
def run_algorithm(instance: VRPInstance, algorithm_func, algo_name: str,
                  results_folder: Path, instance_name: str,
                  previous_solution: VRPSolution = None) -> tuple[VRPSolution, dict]:
    """
    Run an algorithm on a VRP instance, measure execution time, save and plot solution.
    Optionally, pass previous_solution (for heuristics like 2-opt).
    """
    start_time = time.perf_counter()

    if previous_solution is not None:
        solution = algorithm_func(previous_solution)
    else:
        solution = algorithm_func(instance)

    exec_time = time.perf_counter() - start_time
    solution.execution_time = exec_time

    # Create algorithm-specific folder if it does not exist
    algo_folder = results_folder / algo_name
    algo_folder.mkdir(parents=True, exist_ok=True)

    # Save solution
    solution.save(filepath=algo_folder / f"{instance_name}_solution.pkl")

    # Plot solution
    solution.plot_vrp_solution(save_path=algo_folder / f"{instance_name}_solution.html")

    # Return solution and summary dict
    summary = {
        'instance_name': instance_name,
        'algorithm': algo_name,
        'execution_time': exec_time,
        'cost': solution.total_cost,
        'total_distance': solution.total_distance,
        'feasible': solution.complete_feasibility_flag,
        'num_vehicles': len(solution.routes)
    }

    return solution, summary


# ---------------------------
# Main function
# ---------------------------
def main(dataset_folder: str,
         results_folder: str,
         scenario: str = 'single_truck',
         max_km_per_vehicle: float | None = None) -> None:

    dataset_folder = Path(dataset_folder)
    results_folder = Path(results_folder)
    results_folder.mkdir(parents=True, exist_ok=True)

    summary_results = []

    # Define scenario-specific algorithms
    if scenario == 'single_truck':
        algorithms = [
            ('or_tools', exact_model_or_tools),
            ('nearest_neighbour_single_truck', nn_single),
            ('two_opt_single_truck', two_opt_single)
    ]
        max_km_per_vehicle = None  # no distance limit
    elif scenario == 'multi_truck':
        algorithms = [
            ('or_tools', exact_model_or_tools),
            ('nearest_neighbour_multi_truck', nn_multi),
            ('two_opt_multi_truck', two_opt_multi)        ]
    else:
        raise ValueError(f"Unknown scenario: {scenario}")

    # Iterate over all pickle files
    for pkl_file in dataset_folder.glob('*.pkl'):
        print(f"Processing {pkl_file.name}")

        # Load dataset
        with open(pkl_file, 'rb') as f:
            data = pickle.load(f)

        # Create VRP instance
        instance = VRPInstance(
            locations=data['locations'],
            distance_matrix=data['distance_matrix'],
            time_matrix=data['time_matrix'],
            charging_cost=data.get('chargin_cost', {}),  # verify spelling
            cost_matrix=data['cost_matrix'],
            max_km_per_vehicle=max_km_per_vehicle
        )

        # Plot instance once
        instance.plot_vrp_instance(save_path=dataset_folder / f"{pkl_file.stem}_instance.html")

        # Run algorithms sequentially, optionally chaining previous solution
        prev_solution = None
        for algo_name, algo_func in algorithms:
            prev_solution, summary = run_algorithm(
                instance,
                algorithm_func=algo_func,
                algo_name=algo_name,
                results_folder=results_folder,
                instance_name=pkl_file.stem,
                previous_solution=prev_solution
            )
            summary_results.append(summary)
            

    # Save summary CSV
    df = pd.DataFrame(summary_results)
    print(df)
    csv_file = results_folder / 'results_summary400.csv'
    df.to_csv(csv_file, index=False, encoding='utf-8')


# ---------------------------
# Run script
# ---------------------------
if __name__ == "__main__":
    # Example usage:
    # scenario can be 'single_truck' or 'multi_truck'
    main(
        dataset_folder='C:/Users/alex/Desktop/Natalia/camion_electrico_heuristicas_restricción_max_time/camion_electrico/datasets/sinteticos_10_15_20',
        results_folder='C:/Users/alex/Desktop/Natalia/camion_electrico_heuristicas_restricción_max_time/camion_electrico/datasets/sinteticos_10_15_20/results',
        scenario='multi_truck',
        max_km_per_vehicle=400
    )

