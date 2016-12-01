#Based on https://en.wikipedia.org/wiki/Held%E2%80%93Karp_algorithm
# and credits to https://github.com/CarlEkerot/held-karp for the travelling salesman algo implementation
 
import itertools
import random
import sys

def shortestPath(mCost):
    """
    Implementation of Held-Karp, algorithm for the Traveling Salesman Problem using dynamic programming
    """
    n = len(mCost)-1

    # Maps each subset of the nodes to the cost to reach that subset, as well
    # as what node it passed before reaching this subset.
    # Node subsets are represented as set bits.
    C = {}

    # Set transition cost from initial state
    #print range(1,n)
    for k in range(1, n):
        C[(1 << k, k)] = (mCost[0][k], 0)

    #print C
    # Iterate subsets of increasing length and store intermediate results
    # in classic dynamic programming manner
    for subset_size in range(2, n):
        for subset in itertools.combinations(range(1, n), subset_size):
            # Set bits for all nodes in this subset
            bits = 0
            for bit in subset:
                bits |= 1 << bit
            #print bits
            
            # Find the lowest cost to get to this subset
            for k in subset:
                prev = bits & ~(1 << k)

                res = []
                for m in subset:
                    if m == 0 or m == k:
                        continue
                    res.append((C[(prev, m)][0] + mCost[m][k], m))
                C[(bits, k)] = min(res)

    # We're interested in all bits but the least significant (the start state)
    bits = (2**n - 1) - 1
    #print bits
    #print C	

    # Calculate optimal cost
    res = []
    for k in range(1, n):
        res.append((C[(bits, k)][0] + mCost[k][n], k))		#for the end point
    #print res
    opt, parent = min(res)

    # Backtrack to find full path
    path = []
    for i in range(n - 1):
        path.append(parent)
        new_bits = bits & ~(1 << parent)
        _, parent = C[(bits, parent)]
        bits = new_bits

    return opt, list(reversed(path))