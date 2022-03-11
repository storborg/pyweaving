#
from copy import deepcopy

# mirror check
mseq = [1,2,3,4,1,4, 4,1,4,3,2,1]
mseq = [1,2,3,4,1,4, 2, 4,1,4,3,2,1]
mseq = [6, 2,3,4,1,4, 4,1,4,3,2, 1]
mseq = [1,2,3,4, 1,4,4,1, 1,2,3,4]
mseq = [1,2,3,4, 1,4,2,4,1, 1,2,3,4]
mseq = [1,2,3,4,1,4,1,1,4,1,1,1,1,4,1,1,4,1,4,3,2,1]
mseq = [1,2,2,1,1,4,1,1,4,1,0,1,1,4,1,1,0,1,4,3,2,1]
#mseq = [1,2,3,4,5,6,5,4,4,5,6,5,4,1,2,1,4,5,6,5,4,4,5,6,5,4,3,2,1]
#mseq = [1,2,3,4,5,6,4,5,6,4,5,6,5,4,1,2,1,4,5,6,4,5,6,4,5,6,5,4,3,2,1]

# R,M: simple and as 2D
rseq = [1,2,3, 2,3,2,3,2, 3,2,1]
rseq = [[1,1],[2,1],[3,1],[2,1],[3,1],[2,1],[3,1],[2,1],[3,1],[2,1],[1,1]]
# R: super simple 2D
##rseq = [1,2,3,4,5,3,4,5,6,7,8,6,7,8,2,3,4,6,7,8,9]
# rseq = [[1,1],[2,1],[3,1],[1,1],[2,1],[3,1],[1,1],[2,1],[3,1],[1,1],[2,1],[3,1]]

ascols = [(0, 0, 0, 0, 14, 2, 14, 12, 0, 0, 14, 14, 0, 0, 14, 14, 0, 0, 0, 0, 14, 14, 14, 14, 0, 0, 14, 7, 0, 0, 14, 9),
          (14, 0, 0, 0, 0, 14, 14, 14, 14, 0, 0, 14, 14, 0, 0, 14, 14, 0, 0, 0, 0, 14, 14, 14, 14, 0, 0, 14, 14, 0, 0, 14),
          (4, 14, 0, 0, 0, 0, 14, 14, 13, 1, 0, 0, 14, 14, 0, 0, 14, 14, 0, 0, 0, 0, 14, 14, 14, 14, 0, 0, 14, 14, 0, 0),
          (0, 14, 14, 0, 0, 0, 0, 14, 14, 14, 14, 0, 0, 14, 14, 0, 0, 14, 14, 0, 0, 0, 0, 14, 14, 14, 14, 0, 0, 14, 14, 0),
          (0, 0, 14, 14, 0, 0, 0, 0, 14, 14, 14, 14, 0, 0, 14, 14, 0, 0, 14, 14, 0, 0, 0, 0, 14, 8, 14, 14, 0, 0, 14, 14),
          (14, 0, 0, 2, 2, 0, 0, 0, 0, 2, 2, 3, 14, 0, 0, 14, 14, 0, 0, 14, 14, 0, 0, 0, 0, 10, 14, 14, 14, 0, 0, 14),
          (14, 14, 0, 0, 14, 14, 0, 0, 0, 0, 14, 14, 14, 14, 0, 0, 14, 14, 0, 0, 14, 14, 0, 0, 0, 0, 14, 14, 14, 14, 0, 0),
          (0, 14, 14, 0, 0, 14, 14, 0, 0, 0, 0, 14, 14, 14, 14, 0, 0, 14, 14, 0, 0, 14, 14, 0, 0, 0, 0, 14, 14, 14, 14, 0),
          (0, 0, 14, 11, 0, 0, 14, 14, 0, 0, 0, 0, 14, 14, 14, 14, 0, 0, 14, 14, 0, 0, 14, 14, 0, 0, 0, 0, 14, 14, 14, 14),
          (14, 0, 0, 14, 14, 0, 0, 14, 14, 0, 0, 0, 0, 14, 14, 14, 14, 0, 0, 14, 14, 0, 0, 14, 14, 0, 0, 0, 0, 14, 14, 14),
          (14, 14, 0, 0, 14, 14, 0, 0, 14, 14, 0, 0, 0, 0, 14, 14, 14, 14, 0, 0, 14, 14, 0, 0, 14, 14, 0, 0, 0, 0, 14, 14),
          (14, 13, 14, 0, 0, 14, 14, 0, 0, 6, 14, 0, 0, 0, 0, 14, 14, 14, 14, 0, 0, 14, 14, 0, 0, 14, 14, 0, 0, 0, 0, 14),
          (14, 14, 14, 14, 0, 0, 14, 14, 0, 0, 14, 14, 0, 0, 0, 0, 14, 14, 14, 14, 0, 0, 14, 14, 0, 0, 14, 14, 0, 0, 0, 0),
          (0, 14, 14, 14, 14, 0, 0, 14, 14, 0, 0, 14, 14, 0, 0, 0, 0, 14, 14, 14, 14, 0, 0, 14, 14, 0, 0, 14, 14, 0, 0, 0),
          (0, 0, 14, 14, 14, 14, 0, 0, 14, 5, 0, 0, 14, 14, 0, 0, 0, 0, 14, 14, 14, 14, 0, 0, 14, 14, 0, 0, 14, 14, 0, 0),
          (0, 0, 0, 14, 14, 14, 14, 0, 0, 14, 14, 0, 0, 14, 14, 0, 0, 0, 0, 14, 14, 14, 14, 0, 0, 14, 14, 0, 0, 14, 14, 0),
          (0, 0, 0, 0, 14, 14, 14, 14, 0, 0, 14, 14, 0, 0, 14, 14, 0, 0, 0, 0, 14, 14, 14, 14, 0, 0, 14, 14, 0, 0, 14, 14),
          (14, 0, 0, 0, 0, 14, 14, 14, 14, 0, 0, 14, 14, 0, 0, 14, 14, 0, 0, 0, 0, 14, 14, 14, 14, 0, 0, 14, 14, 0, 0, 14),
          (14, 14, 0, 0, 0, 0, 14, 14, 14, 14, 0, 0, 14, 14, 0, 0, 14, 14, 0, 0, 0, 0, 14, 14, 14, 14, 0, 0, 14, 14, 0, 0),
          (0, 14, 14, 0, 0, 0, 0, 14, 14, 14, 14, 0, 0, 14, 14, 0, 0, 14, 14, 0, 0, 0, 0, 14, 14, 14, 14, 0, 0, 14, 14, 0),
          (0, 0, 14, 14, 0, 0, 0, 0, 14, 14, 14, 14, 0, 0, 14, 14, 0, 0, 14, 14, 0, 0, 0, 0, 14, 14, 14, 14, 0, 0, 14, 14),
          (14, 0, 0, 14, 14, 0, 0, 0, 0, 14, 14, 14, 14, 0, 0, 14, 14, 0, 0, 14, 14, 0, 0, 0, 0, 14, 14, 14, 14, 0, 0, 14),
          (14, 14, 0, 0, 14, 14, 0, 0, 0, 0, 14, 14, 14, 14, 0, 0, 14, 14, 0, 0, 14, 14, 0, 0, 0, 0, 14, 14, 14, 14, 0, 0),
          (0, 14, 14, 0, 0, 14, 14, 0, 0, 0, 0, 14, 14, 14, 14, 0, 0, 14, 14, 0, 0, 14, 14, 0, 0, 0, 0, 14, 14, 14, 14, 0),
          (0, 0, 14, 14, 0, 0, 14, 14, 0, 0, 0, 0, 14, 14, 14, 14, 0, 0, 14, 14, 0, 0, 14, 14, 0, 0, 0, 0, 14, 14, 14, 14),
          (14, 0, 0, 14, 14, 0, 0, 14, 14, 0, 0, 0, 0, 14, 14, 14, 14, 0, 0, 14, 14, 0, 0, 14, 14, 0, 0, 0, 0, 14, 14, 14),
          (14, 14, 0, 0, 14, 14, 0, 0, 14, 14, 0, 0, 0, 0, 14, 14, 14, 14, 0, 0, 14, 14, 0, 0, 14, 14, 0, 0, 0, 0, 14, 14),
          (14, 14, 14, 0, 0, 14, 14, 0, 0, 14, 14, 0, 0, 0, 0, 14, 14, 14, 14, 0, 0, 14, 14, 0, 0, 14, 14, 0, 0, 0, 0, 14),
          (14, 14, 14, 14, 0, 0, 14, 14, 0, 0, 14, 14, 0, 0, 0, 0, 14, 14, 14, 14, 0, 0, 14, 14, 0, 0, 14, 14, 0, 0, 0, 0),
          (0, 14, 14, 14, 14, 0, 0, 14, 14, 0, 0, 14, 14, 0, 0, 0, 0, 14, 14, 14, 14, 0, 0, 14, 14, 0, 0, 14, 14, 0, 0, 0),
          (0, 0, 14, 14, 14, 14, 0, 0, 14, 14, 0, 0, 14, 14, 0, 0, 0, 0, 14, 14, 14, 14, 0, 0, 14, 14, 0, 0, 14, 14, 0, 0),
          (0, 0, 0, 14, 14, 14, 14, 0, 0, 14, 14, 0, 0, 14, 14, 0, 0, 0, 0, 14, 14, 14, 14, 0, 0, 14, 14, 0, 0, 14, 14, 0)]
for j,line in enumerate(ascols):
    newline = []
    for i in line:
        if i == 0: newline.append(0)
        else: newline.append(1)
    ascols[j] = newline


# When looking for repeats in a sequence we might find several repeats which overlap.
# E.g. a len=4 repeat might appear twice but inside this len4 repeat there are two len2 repeats.
#      so they will also appear but 4 of them.
# so we also need to work out which of these repats is teh most important.
### Mirrors wil also appear in this way (min length 3)
# When trying to discover all mirrors and repeats in a draft we wil need to look for a good strategy.
# - in general the sequence that is shortest and conatins the most entities is probably the best description

### Outputs:
# (assuming in rows)
# - we want to see a sequence of col indexes in each section
# - nested.
# E.g. [{R1: [1-4]}, {M1: [5-17]}, {R1: [18-21]}]


### Strategy:
# 1. look for an outer mirror
#  1a. if not at boundary then check to see if outer is a repeat
# 2. look for repeats inside one of the mirrors - keep the largest number of repeats
# 3. look for mirrors inside the repeats (we probably found these in 1a)
# 4 keep repeating until no repeats or mirros found.
# present.

### Implementation:
# - keep a running list of ranges and what has been checked for R and M
# - end when all checked.
# insert into each sequence as it is broken up.
# E.g. if R3 = [12-22, 32-42] then break one open if find mirror inside.
# types are SN = a sequence, RN = a repeat, MN = a mirror
# [ SN[1-100] ]

### In practice we collect all repeas (and al mirors) on initial inspection
# - so want to find nesting and oragnise into eth final structure



###       
def find_repeats(seq, min_match_len=2, debug=False):
    """ Find all repeats in the sequence.
    return dictionary of all found sequences by seq length
    """
    found_patterns = {}
    patterns = []
    seq_len = len(seq)
    start = 0
    # step 1 fwd until halfway
    while start < len(seq) // 2 + 1:
        # window size grows from min_match_len
        for window in range(min_match_len, len(seq) // 2 + 1):
            sample = seq[start: start + window]
            # print(start,window,sample)
            found = [i for i in range(seq_len) if seq[i: i + len(sample)] == sample]
            if len(found) > 1 and sample not in [f for f, _ in patterns]:
                # print("Found",[sample, found])
                patterns.append([sample, found])
        # increment start and loop
##        print("Next", start+1, patterns)
        start += 1
    # all done but maybe run is stil not saved (all in single pattern)
    if debug: 
        print("All patterns:")
        for p in patterns:
            print(p)
    # remove patterns that got longer
    concise = []
    for i,(p,w) in enumerate(patterns[:-1]):
        superseded = False
        preceded = False
        if i < len(patterns):
            next_p = patterns[i+1]
            # is the following for the same seq but longer
            superseded = p==next_p[0][:len(p)] and w==next_p[1]
            if i > 0:
                # is this one shorter than the previous entry
                prev_p = patterns[i - 1]
                preceded = p==prev_p[0][1:] and [q-1 for q in w] == prev_p[1]
            if not superseded and not preceded:
                concise.append([p,w])
    if debug: 
        print("Concise patterns:")
        for p in concise:
            print(p)
    # package up by length
    for p in concise:
        entry = len(p[0])
        if entry not in found_patterns.keys():
            found_patterns[entry] = [p]
        else:
            found_patterns[entry].append(p)
    return found_patterns


def prune_pattern(pattern):
    """ Prune to a minmal pattern
    - look for smaller redundant patterns inside larger ones and remove
    - 
    """
    pass


def find_mirrors(seq, min_match_len=2):
    """ Find all repeats in the sequence.
    1. Starting on left, window size = min_match_len
    2. grow window while looking to right until seq ends or find match
    3. then increment start by 1 and loop until reach end of seq 
    return dictionary of all found sequences by seq length
    step forward slowly so will get subsequences that will need pruning
    """
    found_patterns = {}
    patterns = []
    seq_len = len(seq)
    start = 0
    # step 1 fwd until halfway
    while start < len(seq) // 2 + 1:
        # window size grows from min_match_len
        for window in range(min_match_len, len(seq) // 2):  # +1 ??
            sample = seq[start: start + window]
            sample_rev = deepcopy(sample)[::-1]
            # print(start,window,sample)
            found = [i for i in range(seq_len) if seq[i: i + len(sample)] == sample_rev]
            if len(found) > 1 and sample not in [f for f, _ in patterns]:
                # print("Found",[sample, found])
                patterns.append([sample, found])
        # increment start and loop
        # print("Next", start+1, patterns)
        start += 1
    # all done but maybe run is stil not saved (all in single pattern)
    print("All patterns:")
    for p in patterns:
        print(p)


if __name__ == "__main__":
    seq = rseq
    seq = mseq
    seq = ascols
    result = find_repeats(seq)
    print("Seq =", seq, len(seq))
    #result = find_mirrors(mseq)
    print("Seq =", seq)
    print(result)
    for key in result.keys():
        print(str(key) + ":")
        for s in result[key]:
            print("  " + str(s))
    max_rep = max(result.keys())
    print("Longest repeat is:", result[max_rep][0][1])
