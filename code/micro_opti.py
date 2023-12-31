import util
import random

def optimize_types(input_data, sol):
    turbines_of_subs = sol.turbines_of_subs()

    for sub_id in sol.lone_subs():
        util.print_info(sub_id)
        min_cost = sol.cost_lone_sub(input_data, sub_id, turbines_of_subs)
        best_sub_type = sol.subs[sub_id].substation_type
        best_cable_type = sol.subs[sub_id].land_cable_type

        for sub_type in range(len(input_data.sub_types)):
            for cable_type in range(len(input_data.land_sub_cable_types)):
                sol.subs[sub_id].substation_type = sub_type
                sol.subs[sub_id].land_cable_type = cable_type
                cost = sol.cost_lone_sub(input_data, sub_id, turbines_of_subs)
                if cost < min_cost:
                    min_cost = cost
                    best_sub_type = sub_type
                    best_cable_type = cable_type

        sol.subs[sub_id].substation_type = best_sub_type
        sol.subs[sub_id].land_cable_type = best_cable_type

    # Skip very slow
    return

    for cable_id, cable in enumerate(sol.sub_sub_cables):
        min_cost = sol.cost_paired_subs(input_data, cable_id, turbines_of_subs)
        best_sub_type_a = sol.subs[cable.sub_id_a].substation_type
        best_cable_type_a = sol.subs[cable.sub_id_a].land_cable_type
        best_sub_type_b = sol.subs[cable.sub_id_b].substation_type
        best_cable_type_b = sol.subs[cable.sub_id_b].land_cable_type
        best_cable_type_pair = cable.cable_type

        for sub_type_a in range(len(input_data.sub_types)):
            for cable_type_a in range(len(input_data.land_sub_cable_types)):
                for sub_type_b in range(len(input_data.sub_types)):
                    for cable_type_b in range(len(input_data.land_sub_cable_types)):
                        for cable_type_pair in range(len(input_data.sub_sub_cable_types)):
                            sol.subs[cable.sub_id_a].substation_type = sub_type_a
                            sol.subs[cable.sub_id_a].land_cable_type = cable_type_a
                            sol.subs[cable.sub_id_b].substation_type = sub_type_b
                            sol.subs[cable.sub_id_b].land_cable_type = cable_type_b
                            cable.cable_id = cable_type_pair
                            cost = sol.cost_paired_subs(input_data, cable_id, turbines_of_subs)
                            if cost < min_cost:
                                min_cost = cost
                                best_sub_type_a = sub_type_a
                                best_cable_type_a = cable_type_a
                                best_sub_type_b = sub_type_b
                                best_cable_type_b = cable_type_b
                                best_cable_type_pair = cable_type_pair

        sol.subs[cable.sub_id_a].substation_type = best_sub_type_a
        sol.subs[cable.sub_id_a].land_cable_type = best_cable_type_a
        sol.subs[cable.sub_id_b].substation_type = best_sub_type_b
        sol.subs[cable.sub_id_b].land_cable_type = best_cable_type_b
        cable.cable_id = best_cable_type_pair

# def optimize_pairs(in_data, sol):
#     base_sub_sub_cables = sol.sub_sub_cables
#     n_subs = len(in_data.sub_locations)
#     pairs = []
#     for i_sub_a in range(n_subs):
#         for i_sub_b in range(n_subs):
#             if not sol.subs[i_sub_a] or not sol.subs[i_sub_b] or i_sub_a != i_sub_b:
#                 continue
#             pairs.append((i_sub_a, i_sub_b))
#     random.shuffle(pairs)

#     for i_sub_a, i_sub_b in pairs: