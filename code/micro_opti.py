def optimize_types(input_data, sol):
    for sub_id in sol.lone_subs():
        min_cost = sol.cost_lone_sub(sub_id)
        best_sub_type = sol.subs[sub_id].substation_type
        best_cable_type = sol.subs[sub_id].land_cable_type

        for sub_type in range(len(input_data.sub_types)):
            for cable_type in range(len(input_data.land_sub_cable_types)):
                sol.subs[sub_id].substation_type = sub_type
                sol.subs[sub_id].land_cable_type = cable_type
                cost = sol.cost_lone_sub(sub_id)
                if cost < min_cost:
                    min_cost = cost
                    best_sub_type = sub_type
                    best_cable_type = cable_type

        sol.subs[sub_id].substation_type = best_sub_type
        sol.subs[sub_id].land_cable_type = best_cable_type

    for cable in sol.sub_sub_cables:
        assert False
