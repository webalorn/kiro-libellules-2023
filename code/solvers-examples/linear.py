# https://docs.scipy.org/doc/scipy/reference/generated/scipy.optimize.linprog.html

# pip install --upgrade scipy

from scipy.optimize import linprog

# declare the decision variable bounds
x1_bounds = (0, None)
x2_bounds = (0, None)

# declare coefficients of the objective function 
c = [-10, -5]

# declare the inequality constraint matrix
A = [[1,  1], 
     [10, 0], 
     [0,  5]]

# declare the inequality constraint vector
b = [24, 100, 100]

# solve min(x) such that (Ax <= b)
results = linprog(c=c, A_ub=A, b_ub=b, bounds=[x1_bounds, x2_bounds], method='highs-ds')

# print results
if results.status == 0:
    print(f'The solution is optimal.') 
print(f'Objective value: z* = {results.fun}')
print(f'Solution: x1* = {results.x[0]}, x2* = {results.x[1]}')