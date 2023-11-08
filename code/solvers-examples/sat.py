# https://pypi.org/project/python-sat/
# https://github.com/pysathq/pysat/blob/master/examples/usage.py
# https://github.com/pysathq/pysat/blob/master/pysat/solvers.py

# pip install --upgrade python-sat

from pysat.solvers import Solver
import random

# Une variable est un entier, positif si elle est vrai, négatif si elle est fausse dans la formule
# -> Si x est noté par 5, !x est noté par -5
s1 = Solver(name='g3')
s1.add_clause([-1, 2])
s1.add_clause([-2, 3])
s1.add_clause([-3, 4])
s1.add_clause([4])

for i in range(5, 1000000):
    s1.add_clause([i * random.choice([-1, 1]), random.randint(1, i-1) * random.choice([-1, 1])])
    if random.randint(1, 50) == 1:
        s1.add_clause([i * random.choice([-1, 1]), random.randint(1, i-1) * random.choice([-1, 1])])

if s1.solve() == True:
    print("Success")
    # print(s1.get_model())
else:
    print("Failure")