from util import *
import random
from copy import copy
import time

def find_best_sol(in_data):
    return find_best_sol_stepIsSublocPos(in_data)

def find_best_sol_stepIsSublocPos(in_data):
    # Generate batch of base hypothesis
    n_sublocs = len(in_data.sub_locations)
    hypothesis = [[True] * n_sublocs]
    for i in range(n_sublocs):
        hypothesis.append([True] * n_sublocs)
        hypothesis[-1][i] = False
    for i in range(n_sublocs):
        for j in range(n_sublocs):
            if i != j:
                hypothesis.append([True] * n_sublocs)
                hypothesis[-1][i] = False
                hypothesis[-1][j] = False

    hypothesis = hypothesis[:MAX_SUBLOCS_HYPOTHESIS]

    # Get sols for each hypothesis
    seen_hyps = set([tuple(hyp) for hyp in hypothesis])
    hypothesis = [(hyp, ) + find_best_sol_stepIsAssignTurbs(in_data, tuple(hyp)) for hyp in hypothesis]

    # Generate new hypothesis
    def make_child_hypothesis(hyp, pos_id):
        new_hyp = list(hyp)
        new_hyp[pos_id] = False
        return tuple(new_hyp)

    for i_iter in range(n_sublocs):
        print('find_best_sol_stepIsSublocPos, iterate', i_iter+1, 'best score=', min([h[-1] for h in hypothesis]))
        new_hypothesis = []
        for hyp, sol, score in hypothesis:
            nb_turb_on_sub = [0 for _ in range(n_sublocs)]
            for subloc in sol.turbines:
                nb_turb_on_sub[subloc] += 1
            next_remove_list = sorted([
                (nb_turb_on_sub[i], random.random(), make_child_hypothesis(hyp, i))
                for i in range(n_sublocs) if hyp[i]
                if not make_child_hypothesis(hyp, i) in seen_hyps
            ])[:MAX_SUBLOCS_CHILD_HYPOTHESIS]
            new_hypothesis.extend([hyp_vals[-1] for hyp_vals in next_remove_list])
        
        seen_hyps.update(new_hypothesis)
        new_hypothesis = [(hyp, ) + find_best_sol_stepIsAssignTurbs(in_data, hyp) for hyp in new_hypothesis]

        # Keep best hypothesis
        hypothesis = hypothesis + new_hypothesis
        hypothesis.sort(key=lambda hyp_sol_score: hyp_sol_score[-1])
        hypothesis = hypothesis[:MAX_SUBLOCS_HYPOTHESIS]
    
    hypothesis.sort(key=lambda hyp_sol_score: hyp_sol_score[-1])
    _, sol, score = hypothesis[0]
    return sol, score

def find_best_sol_stepIsAssignTurbs(in_data, allowed_sublocs):
    n_allowed_sublocs = sum(allowed_sublocs)
    if n_allowed_sublocs == 0:
        return None, 10**9
    
    ### Generate batch of base hypothesis ###
    n_sublocs = len(in_data.sub_locations)
    n_turbs = len(in_data.turb_locations)

    # Best sublocs for each turbine
    # TODO: better generation of turbine placement !!!!
    closest_sublocs_to_turbs = []
    for i_turb in range(n_turbs):
        sublocs_dists = [
            (dist(in_data.sub_locations[i_subloc], in_data.turb_locations[i_turb]), i_subloc)
            for i_subloc in range(n_sublocs) if allowed_sublocs[i_subloc]
        ]
        sublocs_dists.sort()
        closest_sublocs_to_turbs.append(sublocs_dists)
    
    # Get a set of assignments
    possible_solutions = {tuple([0] * n_turbs)}
    next_possible_solutions = []
    while len(possible_solutions) < MAX_ASSIGN_TURB_HYPOTHESIS * n_turbs:
        for sol in possible_solutions:
            for k in range(n_turbs):
                if sol[k] < n_allowed_sublocs-1:
                    sol2 = list(sol)
                    sol2[k] += 1
                    next_possible_solutions.append(tuple(sol2))
        if not next_possible_solutions:
            break
        possible_solutions.update(next_possible_solutions)
        next_possible_solutions = []
    possible_solutions = list(possible_solutions)
    possible_solutions.sort(key = lambda sol : sum([closest_sublocs_to_turbs[i_turb][sol[i_turb]][0] for i_turb in range(n_turbs)]))
    hypothesis = [
        [closest_sublocs_to_turbs[i_turb][sol[i_turb]][1] for i_turb in range(n_turbs)]
        for sol in possible_solutions[:MAX_ASSIGN_TURB_HYPOTHESIS]
    ]

    ### Get sols for each hypothesis
    hypothesis = [(hyp, ) + find_best_sol_setpIsAssignCables(in_data, hyp) for hyp in hypothesis]
    hypothesis.sort(key=lambda hyp_sol_score: hyp_sol_score[-1])
    _, sol, score = hypothesis[0]
    return sol, score

def find_best_sol_setpIsAssignCables(in_data, turbines_assignments):
    # Assign turbine to subs
    n_subs = len(in_data.sub_locations)
    n_turbs = len(in_data.turb_locations)

    sol = Solution(
        subs=[None for _ in range(n_subs)],
        sub_sub_cables=[],
        turbines=[None for _ in range(n_turbs)],
    )

    turbs_at_sub = [[] for _ in range(n_subs)]
    for turb_id, assign_to_sub in enumerate(turbines_assignments):
        turbs_at_sub[assign_to_sub].append(turb_id)
        sol.turbines[turb_id] = assign_to_sub

    
    # Get a max power estimate weighted by probabilities
    max_power = sum([
        scenario.turb_power ** SCENARIO_PRODUCTION_POW * scenario.prob
        for scenario in in_data.wind_scenarios]
    ) ** (1/SCENARIO_PRODUCTION_POW)
    
    # For each substation, choose a cable and a station type
    coeff_cost_lost_power = CHOOSE_CABLE_LOST_POWER_COEFF * (in_data.params.curtailing_penalty + CHOOSE_CABLE_PENALTY_COEFF * in_data.params.curtailing_cost * in_data.params.maximum_power / in_data.params.maximum_curtailing)
    for sub_id in range(n_subs):
        power_here = max_power * len(turbs_at_sub[sub_id])
        if power_here:
            sol.subs[sub_id] = SubInstance(None, None)

            cables_types = list(in_data.land_sub_cable_types)
            cables_types.sort(key=lambda c_type:
                c_type.fixed_cost + c_type.variable_cost * dist_origin(in_data.sub_locations[sub_id])
                 + max(0, power_here - c_type.rating) * coeff_cost_lost_power
            )
            sol.subs[sub_id].land_cable_type = cables_types[0].id

            substation_types = list(in_data.sub_types)
            substation_types.sort(key=lambda s_type:
                s_type.cost
                 + max(0, power_here - s_type.rating) * coeff_cost_lost_power
            )
            sol.subs[sub_id].substation_type = substation_types[0].id
    
    # return find_best_sol_setpIsAssignPairs()
    score = eval_sol(in_data, sol)
    # print("Got score of", eval_sol(in_data, sol))
    output_sol_if_better(in_data, sol, score)
    return sol, score