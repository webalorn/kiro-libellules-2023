# https://coin-or.github.io/pulp/guides/how_to_configure_solvers.html
# https://coin-or.github.io/pulp/

# pip install pulp

from pulp import *

model = LpProblem('linear_programming', LpMaximize)

# get solver
solver = getSolver('PULP_CBC_CMD')

# declare decision variables
x1 = LpVariable('x1', lowBound = 0, cat = 'continuous')
x2 = LpVariable('x2', lowBound = 0, cat = 'continuous')

# declare objective
model += 10*x1 + 5*x2

# declare constraints
model += x1 + x2 <= 24
model += 10*x1 <= 100
model += 5*x2 <= 100

# solve 
results = model.solve(solver=solver)

# print results
if LpStatus[results] == 'Optimal':
    print('The solution is optimal.')
print(f'Objective value: z* = {value(model.objective)}')
print(f'Solution: x1* = {value(x1)}, x2* = {value(x2)}')
