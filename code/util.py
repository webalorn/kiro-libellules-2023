from pathlib import Path
from collections import deque, namedtuple
from math import *
from random import randint, shuffle
from dataclasses import dataclass, asdict
from typing import Dict, List, Optional, Tuple

import numpy as np

import json
import time

BEST_SOLS = {}
BEST_SOLS_DATA = {}
IN_DATA = {}
INPUT_NAMES = [e.name for e in Path('../inputs').iterdir() if e.name.endswith('.json')]

OUT_SUFFIX = '-out-1' # TODO : to have different solutions names

# ========== Constants ==========

# TODO: depends on the subject 

# small
# MAX_SUBLOCS_HYPOTHESIS = 30
# MAX_SUBLOCS_CHILD_HYPOTHESIS = 4
# MAX_ASSIGN_TURB_HYPOTHESIS = 40

# Medium
MAX_SUBLOCS_HYPOTHESIS = 10
MAX_SUBLOCS_CHILD_HYPOTHESIS = 2
MAX_ASSIGN_TURB_HYPOTHESIS = 30

# large, huge
# MAX_SUBLOCS_HYPOTHESIS = 8
# MAX_SUBLOCS_CHILD_HYPOTHESIS = 2
# MAX_ASSIGN_TURB_HYPOTHESIS = 6

SCENARIO_PRODUCTION_POW = 16
CHOOSE_CABLE_LOST_POWER_COEFF = 2
CHOOSE_CABLE_PENALTY_COEFF = 1

# ========== Data ==========

@dataclass
class CableType:
    id: int
    rating: float
    variable_cost: float
    fixed_cost: float
    prob_fail: Optional[float]

    def import_(data, id):
        return CableType(
            id = id,
            rating = data["rating"],
            variable_cost = data["variable_cost"],
            fixed_cost = data["fixed_cost"],
            prob_fail = data.get("probability_of_failure")
        )

    def import_list(data):
        def aux(data, id):
            assert data["id"] == id+1
            return CableType.import_(data, id)

        return [aux(item, id) for id, item in enumerate(data)]


@dataclass
class Location:
    x: float
    y: float

    def import_(data):
        return Location(
            x = data["x"],
            y = data["y"]
        )

    def import_list(data):
        def aux(data, id):
            assert data["id"] == id+1
            return Location.import_(data)

        return [aux(item, id) for id, item in enumerate(data)]

@dataclass
class SubstationType:
    id: int
    cost: float
    prob_fail: float
    rating: float

    def import_(data, id):
        return SubstationType(
            id = id,
            cost = data["cost"],
            prob_fail = data["probability_of_failure"],
            rating = data["rating"]
        )

    def import_list(data):
        def aux(data, id):
            assert data["id"] == id+1
            return SubstationType.import_(data, id)

        return [aux(item, id) for id, item in enumerate(data)]

@dataclass
class WindScenario:
    turb_power: float
    prob: float

    def import_(data):
        return WindScenario(
            turb_power = data["power_generation"],
            prob = data["probability"]
        )

    def import_list(data):
        def aux(data, id):
            assert data["id"] == id+1
            return WindScenario.import_(data)

        return [aux(item, id) for id, item in enumerate(data)]

@dataclass
class GeneralParameters:
    curtailing_penalty: float
    curtailing_cost: float
    turb_cable_fixed_cost: float
    turb_cable_variable_cost: float
    main_land_station: Location
    maximum_power: float
    maximum_curtailing: float

    def import_(data):
        return GeneralParameters(
            curtailing_penalty = data["curtailing_penalty"],
            curtailing_cost = data["curtailing_cost"],
            turb_cable_fixed_cost = data["fixed_cost_cable"],
            turb_cable_variable_cost = data["variable_cost_cable"],
            main_land_station = Location(**data["main_land_station"]),
            maximum_power = data["maximum_power"],
            maximum_curtailing = data["maximum_curtailing"]
        )

@dataclass
class Input:
    params: GeneralParameters
    land_sub_cable_types: List[CableType]
    sub_locations: List[Location]
    sub_sub_cable_types: List[CableType]
    sub_types: List[SubstationType]
    wind_scenarios: List[WindScenario]
    turb_locations: List[Location]
    name: str

    def import_(data):
        return Input(
            params = GeneralParameters.import_(data["general_parameters"]),
            land_sub_cable_types = CableType.import_list(data["land_substation_cable_types"]),
            sub_locations = Location.import_list(data["substation_locations"]),
            sub_sub_cable_types = CableType.import_list(data["substation_substation_cable_types"]),
            sub_types = SubstationType.import_list(data["substation_types"]),
            wind_scenarios = WindScenario.import_list(data["wind_scenarios"]),
            turb_locations = Location.import_list(data["wind_turbines"]),
            name=None,
        )

# ---- Out dataclasses

@dataclass
class SubInstance:
    # pos_id: int
    land_cable_type: int
    substation_type: int

@dataclass
class SubSubCable:
    sub_id_a: int
    sub_id_b: int
    cable_type: int

OutTurbineLoc = int
# @dataclass
# class OutTurbineLoc:
#     turb_id: int

@dataclass
class Solution:
    subs: List[Optional[SubInstance]]
    sub_sub_cables: List[SubSubCable]
    turbines: List[int]

    # return subs that are not aconnected to another sub
    def lone_subs(self):
        paired_subs = []
        ret = []
        for cable in self.sub_sub_cables:
            paired_subs.append(cable.sub_id_a)
            paired_subs.append(cable.sub_id_b)
        for id, sub in enumerate(self.subs):
            if sub is not None and id not in paired_subs:
                ret.append(id)
        return ret

    def turbines_of_subs(self):
        ret = [[] for _ in range(len(self.subs))]

        for turb_id, turb_sub in enumerate(self.turbines):
            ret[turb_sub].append(turb_id)

    def cost(self, in_data):
        return cost_sol(in_data, self)

    def cost_lone_sub(self, in_data, sub_id, turbines_of_subs):
        return cost_lone_sub(in_data, self, sub_id, turbines_of_subs)

    def cost_paired_sub(self, in_data, cable_id, turbines_of_subs):
        return self.cost(in_data)

# ---- Data utils functions

def dist(loc1, loc2):
    return sqrt((loc1.x - loc2.x)**2 + (loc1.y - loc2.y)**2)

def dist_origin(loc1):
    return sqrt((loc1.x)**2 + (loc1.y)**2)

def argmin(l): return l.index(min(l))
def argmax(l): return l.index(max(l))

def dict_min(d): return min(d.values())
def dict_max(d): return max(d.values())
def dict_argmin(d):m = dict_min(d);return [el for el, v in d.items() if v==m][0]
def dict_argmax(d):m = dict_max(d);return [el for el, v in d.items() if v==m][0]

# ========== Compute vals on sols ==========

def generate_empty_solution(in_data):
    pass # TODO, if needed

# ========== Input / Output ==========

def preprocess_input(data):
    return Input.import_(data)

def read_input(name):
    p = Path('../inputs') / name
    with open(str(p), 'r') as f:
        data = json.load(f)
    d = preprocess_input(data)
    d.name = name
    return d

def read_all_inputs():
    for name in INPUT_NAMES:
        IN_DATA[name] = read_input(name)

def read_all_outputs(input_names):
    for name in input_names:
        data = read_sol(name)
        cost = cost_sol(IN_DATA[name], data)
        if name not in BEST_SOLS:
            BEST_SOLS[name] = cost
            BEST_SOLS_DATA[name] = data

def _out_with_suffix(name):
    return name[:-5] + OUT_SUFFIX + name[-5:]

def read_sol(name):
    p = Path('../sols') / _out_with_suffix(name)
    with open(str(p), 'r') as f:
        data = output_to_sol(IN_DATA[name], json.load(f))
    return data

def sol_to_output(sol):
    out = {
        'substations': [],
    }

    # Construction substations 
    out["substations"] = []
    for i in range(len(sol.subs)):
        sub = sol.subs[i]
        if sub != None:
            d = dict()
            d["id"] = i+1
            d["land_cable_type"] = sub.land_cable_type + 1
            d["substation_type"] = sub.substation_type + 1
            out["substations"].append(d)

    # Construction substation_substation_cables
    s_s_cables = []
    for i in range(len(sol.sub_sub_cables)):
        d = dict()
        cable = sol.sub_sub_cables[i]
        d["substation_id"] = cable.sub_id_a+1
        d["other_substation_id"] = cable.sub_id_b+1
        d["cable_type"] = cable.cable_type
        cable = sol["sub_sub_cables"][i]
        d["substation_id"] = cable["sub_id_a"]+1
        d["other_substation_id"] = cable["sub_id_b"]+1
        d["cable_type"] = cable["cable_type"]+1
        s_s_cables.append(d)
    out["substation_substation_cables"]=s_s_cables

    #Construction turbines
    turb = []
    for i in range(len(sol.turbines)):
        d=dict()
        d["id"] = i+1
        d["substation_id"] = sol.turbines[i]+1
        turb.append(d)
    out["turbines"] = turb

    return out

def output_to_sol(in_data,sol): #in_data preprocess

    # Construction subs
    subs = sol["substations"]
    nb_pos = len(in_data.sub_locations)
    substation = [None]*nb_pos
    for i in subs:
        substation[i["id"]-1] = SubInstance(land_cable_type=i["land_cable_type"]-1,substation_type=i["substation_type"]-1)
    
    # Construction sub_sub_cables
    ss_cables = []
    cables = sol["substation_substation_cables"]
    for c in cables:
        ss_cables.append(SubSubCable(sub_id_a=c["substation_id"]-1,sub_id_b=c["ohter_substation_id"]-1,cable_type=c["cable_type"]-1))
    
    # Construction turbines
    turb = sol["turbines"]
    new_turb = []
    for t in turb:
        new_turb.append(t["substation_id"]-1)

    return Solution(subs=substation,sub_sub_cables=ss_cables,turbines=new_turb) 



def output_sol_force_overwrite(name, data):
    p = Path('../sols') / _out_with_suffix(name)
    with open(str(p), 'w') as f:
        json.dump(sol_to_output(data), f)

def output_sol_if_better(in_data, data, sol_val=None):
    """ Returns True if the solution is better than the last found solution in this program run,
        even solution already written in the JSON file is even better.
        Updates BEST_SOLS_DATA and BEST_SOLS """
    name = in_data.name
    if sol_val is None:
        sol_val = cost_sol(in_data, data)
    sol_val = cost_sol(in_data, data)
    if name in BEST_SOLS and not is_better_sol(BEST_SOLS[name], sol_val):
        return False
    BEST_SOLS[name] = sol_val
    BEST_SOLS_DATA[name] = data

    cur_file_sol = None
    try:
        cur_file_sol = read_sol(name)
    except FileNotFoundError:
        pass
    if cur_file_sol is not None:
        old_val = cost_sol(in_data, cur_file_sol)
        if not is_better_sol(old_val, sol_val):
            return True
    print(f"----> Found solution for {name} of value {sol_val}")
    output_sol_force_overwrite(name, data)
    return True

# ========== Utile pour evaluation ==========

def turbines_subs_link(in_data, sol): # Retourne une liste de listes, les turbines reliées à chaque sub
    nb_sub = len(in_data.sub_locations)
    fils_subs = [[] for _ in range(nb_sub)]
    turbs = sol.turbines
    for i in range(len(turbs)):
        fils_subs[turbs[i]].append(i)
    return fils_subs

# ========== Evaluation ==========

def distance(pos1,pos2): #pos1 = (x,y)
    return sqrt((pos1[0]-pos2[0])**2 + (pos1[1]-pos2[1])**2)

def cost_construction_substations(in_data, sol): #Check
    c = 0
    for i in sol.subs:
        if i!=None:
            c += in_data.sub_types[i.substation_type].cost
    return c

def cost_land_subs_cables(in_data, sol): #Check
    c = 0
    sub = sol.subs
    for i in range(len(sub)):
        subi = sub[i]
        if subi!=None:
            type_c = subi.land_cable_type
            c1 = in_data.land_sub_cable_types[type_c].fixed_cost
            c2 = in_data.land_sub_cable_types[type_c].variable_cost
            xsub,ysub=(in_data.sub_locations[i].x,in_data.sub_locations[i].y)
            d = distance((0,0),(xsub,ysub))
            c+=c1+d*c2
    return c

def cost_turbine_cables(in_data, sol): #Check
    c = 0
    turb = sol.turbines
    for t in range(len(turb)):
        i = turb[t] #Substation reliée à la turbine
        xsub,ysub=(in_data.sub_locations[i].x,in_data.sub_locations[i].y)
        xturb,yturb=(in_data.turb_locations[t].x,in_data.turb_locations[t].y)
        d = distance((xsub,ysub),(xturb,yturb))
        c+=in_data.params.turb_cable_fixed_cost+in_data.params.turb_cable_variable_cost*d
    return c

def cost_sub_sub_cables(in_data, sol): #Check
    ss_cables = sol.sub_sub_cables
    c = 0
    for i in range(len(ss_cables)):
        xa,ya = (in_data.sub_locations[ss_cables[i].sub_id_a].x,in_data.sub_locations[ss_cables[i].sub_id_a].y)
        xb,yb = (in_data.sub_locations[ss_cables[i].sub_id_b].x,in_data.sub_locations[ss_cables[i].sub_id_b].y)
        d = distance((xa,ya),(xb,yb))
        c += (in_data.sub_sub_cable_types[ss_cables[i].cable_type].fixed_cost + in_data.sub_sub_cable_types[ss_cables[i].cable_type].variable_cost*d)
    return c

def proba_echec_sub_land_cable(in_data, sol,v): #Check
    c_type = sol.subs[v].land_cable_type
    s_type = sol.subs[v].substation_type
    p1 = in_data.land_sub_cable_types[c_type].prob_fail
    p2 = in_data.sub_types[s_type].prob_fail
    return p1 + p2

def curtailing_C(in_data,C): #Check
    return in_data.params.curtailing_cost * C + in_data.params.curtailing_penalty * max(0,(C - in_data.params.maximum_curtailing))

def power_sent_to_v(v_fils,scena):
    c = 0
    turbine_power = scena.turb_power
    return turbine_power * len(v_fils)

def curtailing_v_under_fixed_scena(in_data,scena,sol,v,turbs_fils):
    c = power_sent_to_v(turbs_fils[v],scena)

    sub_type = sol.subs[v].substation_type
    maxcapsub = in_data.sub_types[sub_type].rating
    cable_type = sol.subs[v].land_cable_type
    maxcapcable = in_data.land_sub_cable_types[cable_type].rating

    maxcap = min(maxcapsub,maxcapcable)

    return max(0,c-maxcap)

def curtailing_Cn_scena_fixed(in_data, sol,scena,turbs_fils):
    sub = sol.subs
    c = 0 
    for v in range(len(sub)):
        if sub[v]!=None:
            c += curtailing_v_under_fixed_scena(in_data,scena,sol,v,turbs_fils)
    return c

def curtailing_v_scena_fixed_failure_v(in_data, sol,scena,v,turbs_fils):
    c = power_sent_to_v(turbs_fils[v],scena)

    cbis = 0
    sub_sub_cable = sol.sub_sub_cables
    for i in range(len(sub_sub_cable)):
        cable = sub_sub_cable[i]
        if v == cable.sub_id_a or v == cable.sub_id_b:
            ctype = cable.cable_type
            cbis += in_data.sub_sub_cable_types[ctype].rating
    
    return max(0,(c-cbis))

def curtailing_vbar_scena_fixed_failure_v(in_data, sol,scena,v,turbs_fils):
    c = 0
    c3 = power_sent_to_v(turbs_fils[v],scena)
    c1 = 0
    c2 = 0
    maxcap = 0
    ss_cable = sol.sub_sub_cables
    for i in range(len(ss_cable)):
        if ss_cable[i].sub_id_a == v or ss_cable[i].sub_id_b == v:
            if ss_cable[i].sub_id_a == v:
                vbar = ss_cable[i].sub_id_b
            else:
                vbar == ss_cable[i].sub_id_a
            c1 = power_sent_to_v(turbs_fils[vbar],scena)
            c2 = min(in_data.sub_sub_cable_types[ss_cable[i].cable_type].rating,c3)

            sub_type = sol.subs[vbar].substation_type
            maxcapsub = in_data.sub_types[sub_type].rating
            cable_type = sol.subs[vbar].land_cable_type
            maxcapcable = in_data.land_sub_cable_types[cable_type].rating

            maxcap = min(maxcapsub,maxcapcable)
    
        c += max(0,c1 + c2 - maxcap)
    return c
    


def curtailing_Cf_scena_fixed(in_data,scena,sol,v,turbs_fils):

    return curtailing_v_scena_fixed_failure_v(in_data, sol,scena,v,turbs_fils) + curtailing_vbar_scena_fixed_failure_v(in_data, sol,scena,v,turbs_fils)

def cost_scena_fixed(scena,in_data, sol,turbs_fils):
    sub = sol.subs
    c = 0
    for v in range(len(sub)):
        if sub[v] != None:
            c += (proba_echec_sub_land_cable(in_data, sol,v)*curtailing_C(in_data,curtailing_Cf_scena_fixed(in_data,scena,sol,v,turbs_fils)))
            c1 = proba_echec_sub_land_cable(in_data, sol,v)
            c1 = 1 - c1
            c1 *= curtailing_C(in_data,curtailing_Cn_scena_fixed(in_data, sol,scena,turbs_fils))
    return c + c1


def cost_operational_cost(in_data, sol,turbs_fils):
    scenario = in_data.wind_scenarios
    c = 0
    for scena in scenario:
        c += scena.prob * cost_scena_fixed(scena,in_data, sol,turbs_fils)

    return c

def cost_sol(in_data, sol):
    turbs_fils = turbines_subs_link(in_data, sol)
    return cost_construction_substations(in_data, sol) + cost_land_subs_cables(in_data, sol) + cost_turbine_cables(in_data, sol) + cost_sub_sub_cables(in_data, sol) + cost_operational_cost(in_data, sol,turbs_fils)

def cost_lone_sub_fixed_scena(in_data,sol, sub_id, turbines_of_subs, scena):
    power = scena.turb_power
    received_power = power*len(turbines_of_subs[sub_id])
    sub = sol.subs[sub_id]
    sub_type = sub.substation_type
    cable_land_type = sub.land_cable_type
    cost_cable_turbine = 0
    xs,ys = (sol.sub_locations[sub_id].x,sol.sub_locations[sub_id].y)
    for i in range(len(turbines_of_subs[sub_id])):
        turb = turbines_of_subs[sub_id][i]
        xt,yt = (sol.turb_locations[turb].x,sol.turb_locations[turb].y)
        d=distance((xs,ys),(xt,yt))
        cost_cable_turbine += sol.params.turb_cable_fixed_cost + sol.params.turb_cable_variable_cost*d
    distsol = distance((0,0),(xs,ys))
    return cost_cable_turbine + cable_land_type.fixed_cost + distsol*cable_land_type.variable_cost + sub_type.cost



def cost_lone_sub(in_data, sol, sub_id, turbines_of_subs):
    sub = sol.subs[sub_id]
    sub_type = sub.substation_type
    cable_land_type = sub.land_cable_type
    cost_cable_turbine = 0
    xs,ys = (sol.sub_locations[sub_id].x,sol.sub_locations[sub_id].y)
    for i in range(len(turbines_of_subs[sub_id])):
        turb = turbines_of_subs[sub_id][i]
        xt,yt = (sol.turb_locations[turb].x,sol.turb_locations[turb].y)
        d=distance((xs,ys),(xt,yt))
        cost_cable_turbine += sol.params.turb_cable_fixed_cost + sol.params.turb_cable_variable_cost*d
    distsol = distance((0,0),(xs,ys))
    return cost_cable_turbine + cable_land_type.fixed_cost + distsol*cable_land_type.variable_cost + sub_type.cost



    return cost_sol(in_data, sol)

def is_better_sol(old_sol_value, new_sol_value):
    return new_sol_value < old_sol_value # TODO : Replace by < if the best value is the lower one
            

# ========== Utilities ==========

COLORS = {
    'PURPLE': '\033[95m',
    'BLIE': '\033[94m',
    'CYAN': '\033[96m',
    'GREEN': '\033[92m',
    'ORANGE': '\033[93m',
    'RED': '\033[91m',
    'END': '\033[0m',
    'BOLD': '\033[1m',
    'UNDERLINE': '\033[4m',
}

def _print_color(color, *args, **kwargs):
    print(f"{color}{args[0]}", *args[1:], '\033[0m', **kwargs)

def print_err(*args, **kwargs):
    _print_color("\033[91m", "[ERROR]", *args, **kwargs)

def print_info(*args, **kwargs):
    _print_color("\033[94;1m", "[INFO]", *args, **kwargs)

def print_warning(*args, **kwargs):
    _print_color("\033[93m", "[WARNING]", *args, **kwargs)

def print_ok(*args, **kwargs):
    _print_color("\033[92m", "[WARNING]", *args, **kwargs)

class Heap(): # Smaller number on top
    def __init__(self, l=[]):
        self.l = copy(l)
        if self.l: heapq.heapify(self.l)
    def push(self, el): return heapq.heappush(self.l, el)
    def top(self): return self.l[0]
    def pop(self): return heapq.heappop(self.l)
    def size(self): return len(self.l)
    def empty(): return self.l == []
