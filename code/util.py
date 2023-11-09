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

    def import_(data):
        return Input(
            params = GeneralParameters.import_(data["general_parameters"]),
            land_sub_cable_types = CableType.import_list(data["land_substation_cable_types"]),
            sub_locations = Location.import_list(data["substation_locations"]),
            sub_sub_cable_types = CableType.import_list(data["substation_substation_cable_types"]),
            sub_types = SubstationType.import_list(data["substation_types"]),
            wind_scenarios = WindScenario.import_list(data["wind_scenarios"]),
            turb_locations = Location.import_list(data["wind_turbines"])
        )

# ---- Out dataclasses

@dataclass
class OutSubLocation:
    # pos_id: int
    land_cable_type: int
    substation_type: int

@dataclass
class OutSubSubCable:
    sub_id_a: int
    sub_id_b: int
    cable_type: int

OutTurbineLoc = int
# @dataclass
# class OutTurbineLoc:
#     turb_id: int

@dataclass
class OutData:
    subs: List[Optional[OutSubLocation]]
    sub_sub_cables: List[OutSubSubCable]
    turbines: List[int]

# ---- Data utils functions

def dist(loc1, loc2):
    return sqrt((loc1.x - loc2.x)**2 + (loc1.y - loc2.y)**2)

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
    return preprocess_input(data)

def read_all_inputs():
    for name in INPUT_NAMES:
        IN_DATA[name] = read_input(name)

def _out_with_suffix(name):
    return name[:-5] + OUT_SUFFIX + name[-5:]

def read_sol(name):
    p = Path('../sols') / _out_with_suffix(name)
    with open(str(p), 'r') as f:
        data = output_to_sol(json.load(f))
    return data

def sol_to_output(out_data):
    out = dict()

    # Construction substations 
    substation = []
    for i in range(len(out_data.subs)):
        sub = out_data.subs[i]
        if sub != None:
            d = dict()
            d["id"] = i+1
            d["land_cable_type"] = sub.land_cable_type + 1
            d["substation_type"] = sub.substation_type + 1
            substation.append(d)
    out["substations"] = d

    # Construction substation_substation_cables
    s_s_cables = []
    for i in range(len(out_data.sub_sub_cables)):
        d = dict()
        cable = out_data.sub_sub_cables[i]
        d["substation_id"] = cable.sub_id_a+1
        d["other_substation_id"] = cable.sub_id_b+1
        d["cable_type"] = cable.cable_type
        cable = out_data["sub_sub_cables"][i]
        d["substation_id"] = cable["sub_id_a"]+1
        d["other_substation_id"] = cable["sub_id_b"]+1
        d["cable_type"] = cable["cable_type"]+1
        s_s_cables.append(d)
    out["substation_substation_cables"]=s_s_cables

    #Construction turbines
    turb = []
    for i in range(len(out_data.turbines)):
        d=dict()
        d["id"] = i+1
        d["substation_id"] = out_data.turbines[i]+1
        turb.append(d)
    out["turbines"] = turb

    return out

def output_to_sol(in_data,sol): #in_data preprocess

    # Construction subs
    sub = sol["substations"]
    nb_pos = len(in_data["sub_locations"])
    substation = [None]*nb_pos
    for i in sub:
        substation[i["id"]-1] = OutSubLocation(land_cable_type=i["land_cable_type"]-1,substation_type=i["substation_type"]-1)
    
    # Construction sub_sub_cables
    ss_cables = []
    cables = sol["substation_substation_cables"]
    for c in cables:
        ss_cables.append(OutSubSubCable(sub_id_a=c["substation_id"]-1,sub_id_b=c["ohter_substation_id"]-1,cable_type=c["cable_type"]-1))
    
    # Construction turbines
    turb = sol["turbines"]
    new_turb = []
    for t in turb:
        new_turb.append(t["substation_id"]-1)

    return OutData(subs=substation,sub_sub_cables=ss_cables,turbines=new_turb) 



def output_sol_force_overwrite(name, data):
    p = Path('../sols') / _out_with_suffix(name)
    with open(str(p), 'w') as f:
        json.dump(sol_to_output(data), f)

def output_sol_if_better(name, data):
    """ Returns True if the solution is better than the last found solution in this program run,
        even solution already written in the JSON file is even better.
        Updates BEST_SOLS_DATA and BEST_SOLS """
    sol_val = eval_sol(data)
    if name in BEST_SOLS and is_better_sol(sol_val, BEST_SOLS[name]):
        return False
    BEST_SOLS[name] = sol_val
    BEST_SOLS_DATA[name] = data

    cur_file_sol = None
    try:
        cur_file_sol = read_sol(name)
    except:
        pass
    if cur_file_sol is not None:
        old_val = eval_sol(cur_file_sol)
        if not is_better_sol(old_val, sol_val):
            return True
    print(f"----> Found solution for {name} of value {sol_val}")
    output_sol_force_overwrite(name, data)
    return True

# ========== Evaluation ==========

def construction_substation(in_data,out_data):
    c = 0
    sub = out_data.subs
    for i in sub:
        if i!=None:
            c += in_data.sub_types[i["substation_type"]].cost
    return c


def eval_sol(data):
    return 0

def is_better_sol(old_sol_value, new_sol_value):
    return new_sol_value > old_sol_value # TODO : Replace by < if the best value is the lower one
            

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
