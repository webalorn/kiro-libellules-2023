from util import *
import time
from solving import *
import copy
import micro_opti
# TODO : should import functions from modules

def generate_base_solution(in_data: Input):
    # Assign turbine to subs
    n_subs = len(in_data.sub_locations)
    n_turbs = len(in_data.turb_locations)

    sol = Solution(
        subs=[None for _ in range(n_subs)],
        sub_sub_cables=[],
        turbines=[None for _ in range(n_turbs)],
    )

    turbs_at_sub = [[] for _ in range(n_subs)]
    for turb_id, loc in enumerate(in_data.turb_locations):
        assign_to_sub = argmin([dist(sub, loc) for sub in in_data.sub_locations])
        turbs_at_sub[assign_to_sub].append(turb_id)
        sol.turbines[turb_id] = assign_to_sub
    
    # Get max power
    max_power = max([scenario.turb_power for scenario in in_data.wind_scenarios])

    # Assign cables types and station types
    for sub_id in range(n_subs):
        power_here = max_power * len(turbs_at_sub[sub_id])
        if power_here:
            sol.subs[sub_id] = SubInstance(None, None)

            cables_types = list(in_data.land_sub_cable_types)
            cables_types.sort(key=lambda c_type: (c_type.rating < power_here, c_type.fixed_cost))
            sol.subs[sub_id].land_cable_type = cables_types[0].id

            substation_types = list(in_data.sub_types)
            substation_types.sort(key=lambda s_type: (s_type.cost))
            sol.subs[sub_id].substation_type = substation_types[0].id
    return sol

def improve_sol(input_data, sol):
    sol = copy.deepcopy(sol)
    micro_opti.optimize_types(input_data, sol)
    return sol # TODO : use functions from modules

# ========== Main loop ==========

def main():
    inputs_names = INPUT_NAMES
    # # If we want to tune only some solutions ->
    # inputs_names = ['toy.json', 'small.json', 'medium.json', 'large.json', 'huge.json']
    #inputs_names = ['medium.json'] 

    start_time = time.time()
    read_all_inputs()

    N_TRY_GENERATE = 0 # TODO : number of iterations
    for name in inputs_names:
        print(f"========== GENERATE {name} ==========")
        in_data = IN_DATA[name]
        for _ in range(N_TRY_GENERATE):
            # sol_data = generate_base_solution(in_data)
            # output_sol_if_better(in_data, sol_data)
            sol_data, score = find_best_sol(in_data)
            output_sol_if_better(in_data, sol_data, score)

            # TODO: maybe improve a bit at first ?
            # Then output_sol_if_better(name, sol_data)
        
    
    # This will try to improve every solution stored in ../inputs
    N_TRY_IMPROVE = 1 # TODO : number of iterations
    for name in inputs_names:
        print(f"========== IMPROVE {name} ==========")
        in_data = IN_DATA[name]
        for _ in range(N_TRY_IMPROVE):
            sol_data = improve_sol(in_data, BEST_SOLS_DATA[name])
            output_sol_if_better(in_data, sol_data)
    
    
    end_time = time.time()
    print(f"\n\nFinished for now, took {end_time-start_time:.2f}s")


if __name__ == "__main__":
    main()
