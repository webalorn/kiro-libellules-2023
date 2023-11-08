# https://www.cvxpy.org/
# Functions : https://www.cvxpy.org/tutorial/functions/index.html#scalar-functions

# pip install --upgrade cvxpy

import cvxpy as cp
import numpy as np
import random
from scipy.sparse import dok_matrix
# import sc

print("Building problem")

# Problem data.
m = 30*100
n = 20*100
np.random.seed(1)
# A = np.random.randn(m, n)
b = np.random.randn(m)

# We also can use a sparse matrix
A = dok_matrix((m, n), dtype=float)
for i in range(m):
    for _ in range(10):
        j = random.randint(0, n-1)
        A[i, j] = np.random.randn()


# Construct the problem.
x = cp.Variable(n)
objective = cp.Minimize(cp.sum_squares(cp.logistic(A @ x - b)))
constraints = [0 <= x, x <= 1]
prob = cp.Problem(objective, constraints)

# The optimal objective value is returned by `prob.solve()`.
print("Solving...")

result = prob.solve()
# The optimal value for x is stored in `x.value`.
print(x.value)
# The optimal Lagrange multiplier for a constraint is stored in
# `constraint.dual_value`.
print(constraints[0].dual_value)