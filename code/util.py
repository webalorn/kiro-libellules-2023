from pathlib import Path
from collections import deque, namedtuple
from math import *
from random import randint, shuffle
from dataclasses import dataclass, asdict

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
    rating: int
    variable_cost: float
    fixed_cost: float
    prob_fail: float

@dataclass
class Locaction:
    x: int
    y: int

@dataclass
class SubstationType:
    cost: int
    prob_fail: float
    rating: int

@dataclass
class GeneralParameters:
    curtailing_penalty: float
    curtailing_cost: float
    turb_cable_fixed_cost: float
    turb_cable_variable_cost: float
    main_land_station: Locaction
    maximum_power: int
    maximum_curtailing: float

    def import_(data):
        return GeneralParameters(
            curtailing_penalty = data["curtailing_penalty"]
            curtailing_cost = data["curtailing_cost"]
            turb_cable_fixed_cost = data["fixed_cost_cable"]
            turb_cable_variable_cost = data["variable_cost_cable"]
            main_land_station = Locaction(**data["main_land_station"])
            maximum_power = data["maximum_power"]
            maximum_curtailing = data["maximum_curtailing"]
        )

@dataclass
class WindScenario:
    turb_power: int
    prob: float

@dataclass
class Input:
    params: GeneralParameters
    land_sub_cable_types: list[CableType]
    sub_locations: list[Locaction]
    sub_sub_cable_types: list[CableType]
    sub_types: list[SubstationType]
    wind_scenarios: list[WindScenario]
    turb_locations: list[Locaction]

    def import_(data):
        return Input(
            params = GeneralParameters.import_(data["general_parameters"])
            land_sub_cable_types = CableType.import_list(data["land_substation_cable_types"])
            sub_locations = Locaction.import_list(data["substation_locations"])
            sub_sub_cable_types = CableType.import_list(data["substation_substation_cable_types"])
            sub_types = SubstationType.import_list(data["substation_types"])
            wind_scenarios = WindScenario.import_list(data["wind_scenarios"])
            turb_locations = Locaction.import_list(data["wind_turbines"])
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
    for i in range(len(out_data["subs"])):
        sub = out_data["subs"][i]
        if sub != None:
            d = dict()
            d["id"] = i+1
            d["land_cable_type"] = sub["land_cable_type"]
            d["substation_type"] = sub["substation_type"]
            substation.append(d)
    out["substations"] = d

    # Construction substation_substation_cables
    s_s_cables = []
    for i in range(len(out_data["sub_sub_cables"])):
        d = dict()
        cable = out_data["sub_sub_cables"][i]
        d["substation_id"] = cable["sub_id_a"]+1
        d["other_substation_id"] = cable["sub_id_b"]+1
        d["cable_type"] = cable["cable_type"]
        s_s_cables.append(d)
    out["substation_substation_cables"]=s_s_cables

    #Construction turbines
    turb = []
    for i in range(len(out_data["turbines"])):
        d=dict()
        d["id"] = i+1
        d["substation_id"] = out_data["turbines"][i]+1
        turb.append(d)
    out["turbines"] = turb

    return out

def output_to_sol(in_data,sol): #in_data preprocess

    # Construction subs
    sub = sol["substations"]
    nb_pos = len(in_data["sub_locations"])
    substation = [None]*nb_pos
    for i in sub:
        substation[i["id"]-1] = OutSubLocation(land_cable_type=i["land_cable_type"],substation_type=i["substation_type"])
    
    # Construction sub_sub_cables
    ss_cables = []
    cables = sol["substation_substation_cables"]
    for c in cables:
        ss_cables.append(OutSubSubCable(sub_id_a=c["substation_id"]-1,sub_id_b=c["ohter_substation_id"]-1,cable_type=c["cable_type"]))
    
    # Construction turbines
    turb = sol["turbines"]
    new_turb = []
    for t in turb:
        new_turb.append(t["substation_id"]-1)

    return OutData(subs=substation,sub_sub_cables=ss_cables,turbines=new_turb) 



def output_sol_force_overwrite(name, data):
    p = Path('../sols') / _out_with_suffix(name)
    with open(str(p), 'w') as f:
        json.dump(data, f)

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
