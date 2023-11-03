#!/usr/bin/python
from copy import deepcopy



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
for j, line in enumerate(ascols):
    newline = []
    for i in line:
        if i == 0:
            newline.append(0)
        else:
            newline.append(1)
    ascols[j] = newline

beryl = [8, 7, 6, 5, 4, 3, 2, 1, 8, 7, 6, 5, 4, 3, 2, 1, 8, 7, 6, 5, 4, 3, 2, 1, 2, 3, 4,
         5, 6, 7, 8, 1, 2, 3, 4, 1, 2, 3, 4, 5, 2, 3, 4, 5, 2, 3, 4, 5, 6, 3, 4, 5, 6, 3,
         4, 5, 6, 7, 4, 5, 6, 7, 4, 5, 6, 7, 8, 5, 6, 7, 8, 5, 6, 7, 8, 1, 6, 7, 8, 1, 6,
         7, 8, 1, 2, 7, 8, 1, 2, 7, 8, 1, 2, 3, 8, 1, 2, 3, 8, 1, 2, 3, 4, 1, 2, 3, 4, 5,
         6, 7, 8, 7, 6, 5, 4, 3, 2, 1, 2, 3, 4, 5, 6, 7, 8, 7, 6, 5, 4, 3, 2, 1, 2, 3, 4,
         5, 6, 7, 8, 7, 6, 5, 4, 3, 2, 1, 8, 7, 6, 5, 4, 3, 2, 1, 8, 7, 6, 5, 4, 3, 2, 1,
         8, 7, 6, 5, 4, 3, 2, 1, 2, 3, 4, 5, 6, 7, 8, 7, 6, 5, 4, 3, 2, 1, 2, 3, 4, 5, 6,
         7, 8, 7, 6, 5, 4, 3, 2, 1, 2, 3, 4, 5, 6, 7, 8, 7, 6, 5, 4, 3, 2, 1, 2, 3, 4, 5,
         6, 7, 8, 7, 6, 5, 4, 3, 2, 1, 2, 3, 4, 5, 6, 7, 8, 1, 2, 3, 4, 5, 6, 7, 8, 1, 2,
         3, 4, 5, 6, 7, 8, 1, 2, 3, 4, 5, 6, 7, 8, 7, 6, 5, 4, 3, 2, 1, 2, 3, 4, 5, 6, 7,
         8, 7, 6, 5, 4, 3, 2, 1, 2, 3, 4, 5, 6, 7, 8, 7, 6, 5, 4, 3, 2, 1, 4, 3, 2, 1, 8,
         3, 2, 1, 8, 3, 2, 1, 8, 7, 2, 1, 8, 7, 2, 1, 8, 7, 6, 1, 8, 7, 6, 1, 8, 7, 6, 5,
         8, 7, 6, 5, 8, 7, 6, 5, 4, 7, 6, 5, 4, 7, 6, 5, 4, 3, 6, 5, 4, 3, 6, 5, 4, 3, 2,
         5, 4, 3, 2, 5, 4, 3, 2, 1, 4, 3, 2, 1, 8, 7, 6, 5, 4, 3, 2, 1, 2, 3, 4, 5, 6, 7,
         8, 1, 2, 3, 4, 5, 6, 7, 8, 1, 2, 3, 4, 5, 6, 7, 8]


# When looking for repeats in a sequence we might find several repeats which overlap.
# E.g. a len=4 repeat might appear twice but inside this len4 repeat there are two len2 repeats.
#      so they will also appear but 4 of them.
# so we also need to work out which of these repats is teh most important.
# Mirrors wil also appear in this way (min length 3)
# When trying to discover all mirrors and repeats in a draft we wil need to look for a good strategy.
# - in general the sequence that is shortest and conatins the most entities is probably the best description

# Outputs:
# (assuming in rows)
# - we want to see a sequence of col indexes in each section
# - nested.
# E.g. [{R1: [1-4]}, {M1: [5-17]}, {R1: [18-21]}]


# Strategy:
# 1. look for an outer mirror
#  1a. if not at boundary then check to see if outer is a repeat
# 2. look for repeats inside one of the mirrors - keep the largest number of repeats
# 3. look for mirrors inside the repeats (we probably found these in 1a)
# 4 keep repeating until no repeats or mirros found.
# present.

# Implementation:
# - keep a running list of ranges and what has been checked for R and M
# - end when all checked.
# insert into each sequence as it is broken up.
# E.g. if R3 = [12-22, 32-42] then break one open if find mirror inside.
# types are SN = a sequence, RN = a repeat, MN = a mirror
# [ SN[1-100] ]

# In practice we collect all repeats (and all mirors) on initial inspection
# - so want to find nesting and organise into the final structure

def remove_growing_patterns(patterns):
    concise = patterns[:-1]
    concise_len = -1
    while len(concise) != concise_len:
        # repeat until the list stops getting shorter
        concise_len = len(concise)
        print(len(concise))
        new_concise = []
        for i, (p, w) in enumerate(concise):
            superseded = False
            preceded = False
            if i < len(patterns):
                next_p = patterns[i+1]
                # is the following for the same seq but longer
                superseded = p == next_p[0][:len(p)] and w == next_p[1]
                print("super",p,w,superseded)
                if i > 0:
                    # is this one shorter than the previous entry
                    prev_p = patterns[i - 1]
                    preceded = p == prev_p[0][1:] and [q-1 for q in w] == prev_p[1]
                if not superseded and not preceded:
                    new_concise.append([p, w])
        concise = new_concise
    return concise

def find_repeats(seq, min_match_len=2, debug=False):
    """
    Find all repeats in the sequence.
    Return a dictionary of found sequence lengths. Where each entry is
     - A list of twp lists.
     - first is the sequences found (of length = the key)
     - second is the start positions of each repeat in the sequence

    Args:
        list: seq. A one or 2D list of a sequence with possible repeats

    Returns:
        dict: of sequence lengths containing two lists; found sequences, positions of first item in list

    Notes:
        Subset sequences have been removed. E.g. if a 1,2 repeat is found and a 1,2,3 repeats is also found
        and there are no 1,2 repeats that are not also in 1,2,3 repeats - then only the 1,2,3 repeat will
        be returned.
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
        # print("Next", start+1, patterns)
        start += 1
    # all done but maybe run is stil not saved (all in single pattern)
    if debug:
        print("All patterns:")
        for p in patterns:
            print(p)
    # remove patterns that got longer
    concise = []
    concise = remove_growing_patterns(patterns)
##    for i, (p, w) in enumerate(patterns[:-1]):
##        superseded = False
##        preceded = False
##        if i < len(patterns):
##            next_p = patterns[i+1]
##            # is the following for the same seq but longer
##            superseded = p == next_p[0][:len(p)] and w == next_p[1]
##            print("super",p,superseded)
##            if i > 0:
##                # is this one shorter than the previous entry
##                prev_p = patterns[i - 1]
##                preceded = p == prev_p[0][1:] and [q-1 for q in w] == prev_p[1]
##            if not superseded and not preceded:
##                concise.append([p, w])
    # clip internal repeats
    #print("clip")
    for i,c in enumerate(concise):
        p,start = c
        #print("",p,start)
        elast = start[0]+len(p)
        new_w = [start[0]]
        if len(start)>1:
            for s in start[1:]:
                #print(" ",s,elast)
                if s >= elast: # no overlap so keep
                    new_w.append(s)
                    elast = s + len(p)
            concise[i] = [p,new_w]
            #print("  saving",[p,new_w])
    #
        
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
    #return found_patterns
    return concise

###----------------


def expand_repeat(seq, start, window, newpos, debug=False):
    """
    Keep growing the repeat to its maximum size.
    Return the longest repeat found.
    - include all other occurrences of that repeat.
    """
    sample = seq[start: start + window]
    #sample_rev = deepcopy(sample)[::-1]
    #end = newpos+window
    if debug:
        print(" expanding", sample,start,newpos)
    while seq[newpos:newpos+window] == sample and newpos >= start+window:
        #end += 1
        window += 1
        sample = deepcopy(seq[start: start + window])#[::-1]
        print(" ",window, start+window, seq[start: start + window], seq[newpos:newpos+window])
    # found max seq
    #newpos -= 1
    window -= 1
    found_starts = [newpos]
    sample = seq[start: start + window]
    #sample_rev = deepcopy(sample)[::-1]
    # print(" =",newpos,end, sample, seq[newpos:end])
    # search for more of this mirror
    for i in range(newpos+window, len(seq) - window+1):
        # print(" ", i, sample, seq[i:i + window])
        if sample == seq[i:i+window]:
            found_starts.append(i)
    if debug:
        print(" expanded to", [start, window, sample, found_starts])
    # return all found
    return [start, window, sample, found_starts]



def find_repeats(seq, min_match_len=2, debug=False):
    collection = []
    for start in range(len(seq) - 1):  # // 2 + 1):
        for window in range(min_match_len, len(seq) // 2 + 1):
            sample = seq[start: start + window]
            #sample_rev = deepcopy(sample)[::-1]
            for i in range(len(seq)-window):
                pos = start+window+i
                section = seq[pos:pos+window]
                if section == sample:#_rev:
                    if debug:
                        print("found", start, sample, pos, section)
                    # is it already in collection
                    if not already_collected(sample, pos, collection):
                        # found one so expand to full size
                        expanded = expand_repeat(seq, start, window, pos)
                        if debug:
                            print(" possible=", expanded, collection)
                        if not exact_match(expanded, collection):
                            collection.append(expanded)
                            if debug:
                                print(" stored")
                        if debug:
                            print("\n")
    if debug:
        print("\nCollection:", len(collection))
        for c in collection:
            print(c)
        print()
    return collection



# Mirrors


def expand_mirror(seq, start, window, newpos, debug=False):
    """
    Keep growing the mirror to its maximum size.
    Return the longest mirror found.
    - include all other occurrences of that mirror.
    """
    sample = seq[start: start + window]
    sample_rev = deepcopy(sample)[::-1]
    end = newpos+window
    if debug:
        print(" expanding", sample)
    while seq[newpos:end] == sample_rev and newpos >= start+window:
        newpos -= 1
        window += 1
        sample_rev = deepcopy(seq[start: start + window])[::-1]
        # print(" ",window, seq[start: start + window], seq[newpos:end])
    # found max seq
    newpos += 1
    window -= 1
    found_starts = [newpos]
    sample = seq[start: start + window]
    sample_rev = deepcopy(sample)[::-1]
    # print(" =",newpos,end, sample, seq[newpos:end])
    # search for more of this mirror
    for i in range(end, len(seq) - window+1):
        # print(" ", i, sample, seq[i:i + window])
        if sample_rev == seq[i:i+window]:
            found_starts.append(i)
    if debug:
        print(" expanded to", [start, window, sample, found_starts])
    # return all found
    return [start, window, sample, found_starts]


def already_collected(possible, pos, collection, debug=True):
    """
    Is the possible, at pos, in the collection already.
    """
    # poss_len = len(possible)
    matched = False
    for _, window, sample, positions in collection:
        ranges = [[p, p+window] for p in positions]
        range_chk = [s <= pos < e for s, e in ranges]
        # match = ((possible == sample[i:i + poss_len])
                 # for i in range(window - poss_len + 1))
        if debug:
            print("  chk=", list(range_chk))
        matched = any(range_chk)
        if matched:
            break
    return matched


def exact_match(sequence, collection):
    """
    Is there an exact match of sequence in the collection ?
    """
    matched = False
    for item in collection:
        if sequence[2] == item[2]:  # check 'sample' only
            matched = True
            break
    return matched


def find_mirrors(seq, min_match_len=2, debug=False):
    """
    Two kinds of mirroring:
    - a bounce - the reflection occurs around one (often) or more threads.
      - E.g. a point draw or an entire pattern reflected in half.
      - But can be uneven in order to get balanced selvedges or for any reason.
    - a mirror - no central bounce point. I.e. mirror plane is between threads.
      - this is uncommon in weaving - leads to long floats.
    """
    collection = []
    for start in range(len(seq) - 1):  # // 2 + 1):
        for window in range(min_match_len, len(seq) // 2 + 1):
            sample = seq[start: start + window]
            sample_rev = deepcopy(sample)[::-1]
            for i in range(len(seq)-window):
                pos = start+window+i
                section = seq[pos:pos+window]
                if section == sample_rev:
                    if debug:
                        print("found", start, sample, pos, section)
                    # is it already in collection
                    if not already_collected(sample, pos, collection):
                        # found one so expand to full size
                        expanded = expand_mirror(seq, start, window, pos)
                        if debug:
                            print(" possible=", expanded, collection)
                        if not exact_match(expanded, collection):
                            collection.append(expanded)
                            if debug:
                                print(" stored")
                        if debug:
                            print("\n")
    if debug:
        print("\nCollection:", len(collection))
        for c in collection:
            print(c)
        print()
    return collection


def find_longest_mirror(mirrors):
    """
    Return the longest mirror in mirrors.
    """
    max_len = 0
    longest = []
    for m in mirrors:
        start, window, sample, positions = m
        if window > max_len:
            longest = m
            max_len = window
    return longest


def parse_mirrors(seq, mirrors):
    """
    Report on the found mirrors
    """
    max_len = end = len(seq)
    max_mirror = find_longest_mirror(mirrors)
    if not max_mirror:
        print("no mirrors found")
    else:
        print("longest is", max_mirror[1], "in", max_len, "(", max_mirror[1]*2, ")")
        if max_mirror[1] * 2 + 1 == max_len:
            print("Perfect half mirror reflection around a thread.")
            end = max_mirror[1]  # where to stop parsing
        elif max_mirror[1] * 2 == max_len:
            print("Perfect half mirror reflection. Mirror plane between threads.")
            end = max_mirror[1]  # where to stop parsing
        # 
        for m in mirrors:
            # if m[1] != max_mirror[1]:
            repeats = [p for p in m[-1]]  # if p < max_mirror[0] + max_mirror[1]]
            print("", repeats)
            if repeats:
                print("seq=%s %d %s" % (m[2], len(repeats), "mirror repeats"))

def find_mirrors_repeats(seq, min_match_len=2, debug=False):
    """
    Gather the mirrors and repeats into a series of ranges
    """
    results = {'mirrors': [], 'repeats': []}
    # repeats = find_repeats(seq, min_match_len)
    # mirrors = find_mirrors(seq, min_match_len)
    # Mirrors
    # for m in mirrors:
        # start, window, sample, positions = m
        # series = [[start,start+window-1]]
        # series.extend([[p,p+window-1] for p in positions])
        # results['mirrors'].append([sample,series])
    # Repeats
    # print(repeats)
    # for r in repeats:
        #sample, positions = r
        #s_len = len(sample)
        #series = [[p,p+s_len-1] for p in positions]
        # start, window, sample, positions = r
        # series = [[start,start+window-1]]
        # series.extend([[p,p+window-1] for p in positions])
        # results['repeats'].append([sample,series])
    # print(results)
    # for r in results['repeats']:
        # rr = Repeat(r, len(seq))
        # print("",rr)
    #
    test = Pattern(seq, min_match_len)
    print("\n",test)
    for p in test.repeats:
        print("",p,"\n   ", p.positions)
    for p in test.mirrors:
        print("",p,"\n   ", p.positions)
        print("   ", p.seq[:p.mirror_length], p.gap)
    results['mirrors'] = [[r.seq, r.positions] for r in test.mirrors]
    results['repeats'] = [[r.seq, r.positions] for r in test.repeats]
    return results

class Span(object):
    """
    A contiguous collection of repeats|mirrors.
    May contain a repeat containing mirrors or vice versa.
    """
    def __init__(self, input_series, seqlen):
        self.seq = input_series[0]
        self.positions = input_series[1]
        self.start = self.positions[0][0]
        # self.start = None  # start index in toplevel sequence
        self.end = None
        self.children = []
        self.span = [self.start, self.end]
        self.count = len(self.positions)
        self.remainder = seqlen - len(self.seq) * self.count


    def __repr__(self):
        label = self.seq
        lab_len = len(label)
        if lab_len > 10:
            label = "%s..(%d)..%s" %(str(label[:4])[:-1], lab_len-8, str(label[-4:])[1:])
        return "<Span: %s start:%d count:%d children:%s remainder:%d>" %(label, self.start, self.count, self.children, self.remainder)


class Pattern(object):
    """
    Given a pattern find repeats and mirrors.
    Repeats may be nested. Mirrors may be top level or inside repeats
    Find nested structure. Enable discovery of smallest atoms and reporting of ordered structure.
    Final result wil be a fully enumerated sequence of repeats, mirrors and isolated components.
    """
    def __init__(self, sequence, min_match_len=2):
        self.sequence = sequence
        self.min_match_len = min_match_len
        self.seqlen = len(sequence)
        self.repeats = self.find_repeats(self.sequence, self.min_match_len)
        self.all_mirrors = self.find_mirrors(self.sequence, self.min_match_len)
        self.mirrors = self.prune_balanced_inferior_mirrors(self.all_mirrors)
        self.mirrors_minmal = self.find_minimal_mirrors(self.mirrors)
        self.spans = []
        #
        self.series = []  # the entire sequence as a list of components
        self.atoms = []  # the smallest unique parts in pattern order
        #
        self.examine_repeats()  # find sub repeats and add
        self.examine_mirrors()  # insert mirrors into repeats
        # entire system should now be elaborated
        self.find_atoms()
        self.determine_series()


    def __repr__(self):
        return "<Pattern:(%d)%s Repeats:%d Mirrors:%d>" %(self.seqlen, self.sequence, len(self.repeats), len(self.mirrors))


    def exact_sample_match(self, sequence, collection, debug=True):
        """
        Is there an exact match of sequence in the collection ?
        - used by find_repeats(), find_mirrors()
        """
        matched = False
        for item in collection:
            if sequence[2] == item[2]:  # check 'sample' only
                matched = True
                break
        if debug and matched:
            print(" .exists")
        return matched


    def already_collected_repeat(self, possible, pos, collection, debug=False):
        """
        Is the possible, at pos, in the collection already.
        - used by find_repeats(), find_mirrors()
        """
        poss_len = len(possible)
        matched = False
        for start, window, _, positions in collection:  # (start, window, sample, positions)
            if False:  # poss_len > len(sample):
                range_chk = []
            else:
                ranges = [[start,start+window]]
                ranges.extend([[p, p+window] for p in positions])
                range_chk = [s <= pos < e for s, e in ranges]
            if debug:
                print("  chk=", any(range_chk),list(range_chk), [[s,pos,e] for s, e in ranges])
            matched = any(range_chk)
            if matched:
                break
        return matched


    def expand_repeat(self, seq, start, window, newpos, debug=False):
        """
        Keep growing the repeat to its maximum size.
        Return the longest repeat found.
        - include all other occurrences of that repeat.
        - used by find_repeats()
        """
        sample = seq[start: start + window]
        if debug:
            print(" expanding", sample,start,newpos)
        while seq[newpos:newpos+window] == sample and newpos >= start+window:
            window += 1
            sample = seq[start: start + window]
            # print(" ",window, start+window, seq[start: start + window], seq[newpos:newpos+window])
        # found max seq
        window -= 1
        found_starts = [newpos]
        sample = seq[start: start + window]
        # print(" =",newpos,end, sample, seq[newpos:end])
        # search for more of this repeat
        for i in range(newpos+window, len(seq) - window+1):
            # print(" ", i, sample, seq[i:i + window])
            if sample == seq[i:i+window]:
                found_starts.append(i)
        if debug:
            print(" expanded to", [start, window, sample, found_starts])
        # return all found
        return [start, window, sample, found_starts]


    def find_repeats(self, seq, min_match_len=2, debug=False):
        collection = []
        results = []  # of Repeats
        for start in range(len(seq) - 1):
            for window in range(min_match_len, len(seq)-min_match_len):# // 2 + 1):
                sample = seq[start: start + window]
                for i in range(len(seq)-window):
                    pos = start+window+i
                    section = seq[pos:pos+window]
                    if section == sample:
                        if debug:
                            print("Found", start, sample, pos, section)
                        # is it already in collection
                        if not self.already_collected_repeat(sample, pos, collection):
                            # found one so expand to full size
                            expanded = self.expand_repeat(seq, start, window, pos)
                            if debug:
                                print(" possible=", expanded, collection)
                            if not self.exact_sample_match(expanded, collection):
                                collection.append(expanded)
                                if debug:
                                    print(" stored", len(collection))
                            if debug:
                                print("\n")
                        elif debug:
                            print(" already collected",sample, pos, collection)
        # we have a collection of repeats
        for c in collection:
            start, window, sample, positions = c
            series = [[start,start+window-1]]
            series.extend([[p,p+window-1] for p in positions])
            results.append(Repeat([sample, series], self.seqlen))
        if debug:
            print("\nCollection(R):", len(collection))
            for c in collection:
                print(c)
            print()
        return results


    def is_mirror(self,seq):
        return seq==seq[::-1]


    def expand_mirror(self, seq, start, window, newpos, debug=True):
        """
        Keep growing the mirror to its maximum size.
        Return the longest mirror found.
        - include all other occurrences of that mirror.
        """
        sample = seq[start: start + window]
        # initial = deepcopy(sample)
        sample_rev = sample[::-1]
        end = newpos+window
        if debug:
            print(" expanding", sample)
        while seq[newpos:end] == sample_rev and newpos > start+window:
            newpos -= 1
            window += 1
            sample_rev = seq[start: start + window][::-1]
        # found max seq
        # look for repeats of this mirror
        newpos += 1
        window -= 1
        found_starts = []
        window = (window) * 2 + 1
        span = window
        # if span % 2 == 0:  # perfect mirror case
            # span += 1
        sample = seq[start: start + span]
        if self.is_mirror(sample):
            sample_rev = sample[::-1]
            # print(" =",newpos, end, sample, seq[newpos:end])
            # search for more of this mirror
            i = end#+span+1
            while i < len(seq) - span+1:
                if sample_rev == seq[i:i+span]:
                    found_starts.append(i)
                    i += span-1
                else:
                    i += 1
            if debug:
                print(" expanded to", [start, span, sample, found_starts])
            # return all found
            return [start, window, sample, found_starts]
        else:  # too short or not a mirror
            return None

##    def already_collected_mirror(self, possible, pos, collection, debug=True):
##        """
##        Is the possible, at pos, in the collection already.
##        - used by find_repeats(), find_mirrors()
##        """
##        poss_len = len(possible)
##        matched = False
##        for start, window, _, positions in collection: # (start, window, sample, positions)
##            if False:#poss_len > len(sample):
##                range_chk = []
##            else:
##                ranges = [[start,start+window]]
##                ranges.extend([[p, p+window] for p in positions])
##                range_chk = [s <= pos < e for s, e in ranges]
##            if debug:
##                print("  chk=", any(range_chk),list(range_chk), [[s,pos,e] for s, e in ranges])
##            matched = any(range_chk)
##            matched = False
##            if matched:
##                break
##        return matched


    def already_collected_mirror(self, possible, pos, collection, debug=True):
        """
        Is the possible, in the collection already.
        - used by find_mirrors()
        """
        poss_len = len(possible)
        matched = False
        for start, window, sample, positions in collection: # (start, window, sample, positions)
            # is possible inside sample centered
            size_diff = len(sample) - poss_len
            if debug:
                print(".",possible, sample, size_diff//2, size_diff//2+poss_len)
            if size_diff > 0 and size_diff % 2 == 0:
                # check = [possible == sample[i:i+poss_len] for i in range(size_diff//2)]
                check = possible == sample[size_diff//2:size_diff//2+poss_len]
                print(" .centercheck",check)
                if check:
                    # even if matched it may be a smaller internal mirror and we should keep it
                    # does it appear anywhere else in the sequence as a repeat
                    if len(sample)//poss_len > 1:
                        count = [possible == sample[i:i+poss_len] for i in range(size_diff)]
                        print(" .count",sum(count))
                        if count == 1:
                            matched = True
                            break
        return matched


    def find_mirrors(self, seq, min_match_len=2, debug=False):
        """
        Two kinds of mirroring:
        - a bounce - the reflection occurs around one (often) or more threads.
          - E.g. a point draw or an entire pattern reflected in half.
          - But can be uneven in order to get balanced selvedges or for any reason.
        - a mirror - no central bounce point. I.e. mirror plane is between threads.
          - this is uncommon in weaving - leads to long floats.
        """
        collection = []
        mirrors = []
        results = []  # of Mirrors
        for start in range(len(seq) - 1):  # // 2 + 1):
            for window in range(min_match_len, len(seq) // 2 + 1):
                sample = seq[start: start + window]
                sample_rev = sample[::-1]
                for i in range(len(seq)-window):
                    pos = start+window+i
                    section = seq[pos:pos+window]
                    if section == sample_rev:
                        if debug:
                            print("found", start, sample, pos, section)
                        # is it already in collection
                        if not self.already_collected_mirror(sample, pos, collection):
                            # found one so expand to full size
                            expanded = self.expand_mirror(seq, start, window, pos)
                            if debug:
                                print(" possible=", expanded, len(collection))
                                # print(" -",self.already_collected(expanded[2], pos, collection), expanded[2])
                            if expanded and not self.exact_sample_match(expanded, collection) and not self.already_collected_mirror(expanded[2], pos, collection):
                                collection.append(expanded)
                                if debug:
                                    print(" stored")
                            if debug:
                                print("\n")
        # we have a collection of mirrors
        # create Mirrors
        for c in collection:
            start, window, sample, positions = c
            series = [[start, start+window-1]]
            series.extend([[p,p+window-1] for p in positions])
            results.append(Mirror([sample, series], self.seqlen))
        if debug:
            print("\nCollection(M):", len(collection),len(results))
            for c in collection:
                print(c)
            print()
        return results

    def prune_balanced_inferior_mirrors(self, mirrors, debug=False):
        """
        Store a copy of mirrors with no internal subsets.
        """
        return self.prune_mirrors(mirrors, True, debug)
        
    def find_minimal_mirrors(self, mirrors, debug=False):
        """
        Make a list of only maximal spanning mirrors.
        No subsets balanced or otherwise
        """
        return self.prune_mirrors(mirrors, False, debug)
        
    def prune_mirrors(self, mirrors, balanced=True, debug=False):
        results = []
        # remove single redundant internals
        for i,m in enumerate(mirrors):
            if debug:
                print("Checking Mirror:",m)
            # results.append(m)
            ok = True
            for m2 in mirrors[i+1:]:
                if m.is_inside(m2):
                    ok = False
                    break
            if ok:  # also check the gathered ones
                if debug:
                    print(" Checked mirrors - checking results:")
                for m2 in results:
                    if m.is_inside(m2):
                        ok = False
                        break
            if ok:
                results.append(m)
        return results


    def examine_repeats(self):
        """
        Find repeats inside repeats. create if not exist and link into children.
        actually find any connected repeats and make a new repeat concatenating them as children.
        """
        spans = []
        for r in self.repeats:
            seq = r.seq
            adj_positions = []
            last = r.positions[0]
            count = 0
            for next in r.positions[1:]:
                # print("",last,next)
                if last[1] == next[0]-1:
                    count += 1
                    # adjacent so collect for new Repeat
                    if adj_positions:
                        adj_positions[1] = next[1]
                    else:
                        adj_positions = [last[0],next[1]]
                else:  # run ended
                    if count > 0:
                        # save new repeat
                        # print("new", adj_positions)
                        count += 1
                        temp = Span([r.seq*count, [adj_positions]], self.seqlen)
                        temp.children = [r,count]
                        spans.append(temp)
                        adj_positions = []
                        count = 0
                last = next
            # traversed that repeat
            if count > 0:
                # save new repeat
                count+=1
                # print(" new_int", r.seq, count)
                temp = Span([r.seq*count, [adj_positions]], self.seqlen)
                temp.children = [r,count]
                spans.append(temp)
        if spans:
            # print(" New", count)
            self.spans.extend(spans)
        
    def examine_mirrors(self):
        """
        Find mirrors inside repeats and link into Repeat's children.
        - start with smallest mirrors to avoid recursion
        """
        pass

    def find_atoms(self):
        pass
    def determine_series(self):
        pass
    

class Repeat(object):
    """
    A sequence which occurs more than once in a Pattern.
    May contain children which are also Repeats or Mirrors.
    """
    def __init__(self, input_series, seqlen):
        self.seq = input_series[0]
        # print(input_series)
        self.children = []
        # might not need these. e.g if self.children
        self.irreducible = False  # contains no repeats also indicates processed?
        self.has_mirrors = False  # contains mirrors
        #
        self.length = len(self.seq)
        self.positions = input_series[1]
        self.start = self.positions[0][0]
        self.count = len(self.positions)
        self.remainder = seqlen - len(self.seq) * self.count
    
    def __repr__(self):
        label = self.seq
        lab_len = len(label)
        if lab_len > 10:
            label = "%s..(%d)..%s" %(str(label[:4])[:-1], lab_len-8, str(label[-4:])[1:])
        return "<Repeat: %s start:%d count:%d children:%s remainder:%d>" %(label, self.start, self.count, self.children, self.remainder)

class Mirror(object):
    """
    """
    def __init__(self, input_series, seqlen):
        self.seq = input_series[0]
        #print(input_series)
        self.children = []
        self.gap = self.find_gap(self.seq)
        self.mirror_length = (len(self.seq) - self.gap )//2  # should be even
        # might not need these. e.g if self.children
        self.irreducible = False  # contains no repeats also indicates processed?
        self.has_repeats = False  # contains mirrors
        #
        self.length = len(self.seq)
        self.positions = input_series[1]
        self.start = self.positions[0][0]
        self.count = len(self.positions)
        # print("Mrem",seqlen,len(self.seq),self.positions, self.seq)
        self.remainder = seqlen - len(self.seq) * self.count
    
    def __repr__(self):
        label = self.seq
        lab_len = len(label)
        if lab_len > 10:
            label = "%s..(%d)..%s" %(str(label[:4])[:-1], lab_len-8, str(label[-4:])[1:])
        title = "Mirror"
        if self.gap == 0:
            title += "(Perfect)"
        elif self.gap == 1:
            title += "(Bounce)"
        else:  # gap > 1
            title += "(Doughnut)"
        return "<%s: %s start:%d count:%d length:%d remainder:%d children:%s>" %(title, label, self.start, self.count, self.mirror_length, self.remainder, self.children)

    def is_inside(self, mirror, balanced=True):
        """
        Is the mirror a single inside this one ?
        ! needs to deal with counts >1
        """
        result = False
        # is it a single
        # print(self)
        if mirror.count == 1 and mirror.children == [] and mirror.length >= self.length:
            # is it inside
            dist1 = mirror.start - self.start
            dist2 = (mirror.start + mirror.length) - (self.start + self.length)
            # print("  checking",dist1,dist2,"-",mirror.start, mirror.count, mirror.length,mirror)
            if balanced:
                if dist1 == -dist2:
                    result = True
            else:
                result = True
        # print("  ",result)
        return result

    def find_gap(self, seq):
        """
        How long is the gap inside this mirror.
        Used to determine if perfect reflection, bounce, or mirrored doughnut.
        """
        seqlen = len(seq)
        gapstart = 0
        gap = 0
        oddp = seqlen%2 != 0
        for i,val in enumerate(seq[:seqlen//2+1]):
            if val != seq[-i-1]:
                gapstart = i
                break
        # Calculate gap
        if gapstart == 0:
            if oddp:
                gap = 1
        else:  # we found a bigger gap
            gap = seqlen - gapstart * 2
        # print("Gap", gap, gapstart, len(seq), seq)
        return gap

# if there a halfway mirror (+-2 given ends may not be perfetcly reflected)
#  - look for seq_repeats in the first mirror
# if there is a mirror at either end (+-2 for same reason)
#  - then start with that and look for seq_repeats inbetween them
# if there is no remainder for any repeat (mirrors handled already)
#  - look for mirrors in seq_repeats
# seq_repeats - look for exact or nearest adjacent items from a repeat.
#  - presort mirrors within repeats and repeats within mirrors as units


def prune_pattern(patterns, seqlen):
    """
    Prune to a minmal pattern
    - Expects list of patterns structured from find_mirrors_repeats()
    - (just the repeats or the mirrors)
    - look for smaller redundant patterns inside larger ones and remove
    Returns one or more minimal sequences of the pattern. If more than one - then similar
    """
    result = []
    etoe = []
    # Algorithm:
    # Starting at 1 find sequences of non-verlapping series
    # 1. sort by starting point
    #   - find EtoE repeat if exists
    #   - If not at end then search other seqs for this start pos
    #      - iterate over each of those
    #  repeat until end of sequence
    #  - start at next earliest starting point
    p_sort = sorted(patterns, reverse=True, key=lambda i: len(i[1]))
    p_adj = []
    connected = []
    coincident = []
    print("EtoE:", len(p_sort))
    for seq,pos in p_sort:
        firsts = [a for a,b in pos]
        secs = [b for a,b in pos]
        print(firsts, secs)  #, list(zip(secs, firsts[1:])))
        count = [e==s+1 for s,e in zip(secs, firsts[1:])].count(True)
        print("",count,seq,pos)
        if count:
            etoe.append([seq,pos])
            print(" %d (%d rem)"%(count+1,seqlen - len(seq)*len(pos)),seq,pos)
    # find sequences following each other.
    for this_pattern in patterns:
        seq, pos = this_pattern
        curr_pos = 1  # overall position in each this_pattern
        this_seq = [[seq,[pos[0]]]]
        
        # add to connected sequences
        connected.append(follow_repeat(curr_pos, seqlen, patterns))
        # find one with least remailnder or most repeats?
    print("connected",len(connected),connected[:2])


    # find continuations
    # for seq,pos in etoe:
        # starts = [s for s,e in pos]
        # ends = [e for s,e in pos]
        # for pat in p_sort:
            # s,p = pat
            # for st,en in p:
                # if st in ends and en in starts:
                    # if pat not in coincident:
                        # coincident.append(pat)
        # print ("coincident",len(coincident), [c[0] for c in coincident])
    #
    # result = etoe + coincident
    result = connected
    
    for seq,pos in result:
        rem = seqlen - len(seq)*len(pos)
        print(" %d (%d rem)"%(count+1,seqlen - len(seq)*len(pos)),seq,pos)

    return result

def find_relevant_patterns(start, patterns):
    """ look through patterns collecting the ones that start at or after start
    """
    result = []
    for seq, pos in patterns:
        # remove intial parts of pos below start
        newpos = [(s,e) for s,e in pos if s >= start]
        if newpos:
            result.append([seq,newpos])
    return result

# one seq at a time - ordered from 1
# - follow repeats until end.
# - loop looking for adjacent (or closest) repeat start
# - until end
# collect all and sort by minimal remainder

def follow_repeat(curr_pos, maxpos, patterns):
    """
    curr_pos = overall position in this recurive sequence. Counts through to end then recurses back.
    """
    # return sequence
    # recurse on less patterns
    this_seq = [patterns[0][0],[]]
    # print("\nStarting with", len(patterns))
    for seq, pos in patterns:
        # collect the adjacents then move onto the next pattern
        # print("begin =",seq)
        adjacent = True
        pcount = 0
        while adjacent and pcount < len(pos):
            start, end = pos[pcount]
            # find the next index
            if start >= curr_pos:
                this_seq[-1].append(pos[pcount])
                # now at end
                # continue (if adjacent) or do we start scanning remaining patterns
                # print("",end, pos[pcount+1][0])
                adjacent = pcount+1<len(pos) and end+1 == pos[pcount+1][0]
                curr_pos = end+1
            pcount += 1
        # need to move to next pattern
        rem_patterns = find_relevant_patterns(curr_pos, patterns)
        if not rem_patterns:
            return this_seq
        else:
            this_seq.append(follow_repeat(curr_pos, maxpos, rem_patterns))


if __name__ == "__main__":
    # Mirror tests
    seq = [1, 3, 4, 5, 6, 7, 5, 4, 6, 5, 4, 3]  #. long seq internal
    seq = [1, 3, 4, 5, 6, 7, 4, 6, 5, 4, 3]  #. long seq internal gap2
    seq = [1, 3, 4, 5, 6, 4, 3, 5, 4, 3, 6, 3, 1, 5, 4, 3]  #. 1,3 ans 3,4 mirrors
    seq = [1, 2, 3, 2, 1, 2, 3, 4, 5, 6, 5, 4, 3, 2, 1, 6]  #. ok bigger seq after smaller seq
    # seq = [1, 2, 3, 4, 5, 6, 5, 4, 3, 2, 1, 6, 1, 3, 2, 1] #. smaller seq after bigger
    # seq = [1, 2, 3, 4, 1, 4, 2, 4, 1, 1, 2, 3, 4]
    # seq = [1, 2, 3, 4, 1, 4, 1, 1, 4, 1, 1, 1, 1, 4, 1, 1, 4, 1, 4, 3, 2, 1]
    # seq = [1, 2, 2, 1, 1, 4, 1, 1, 4, 1, 0, 1, 1, 4, 1, 1, 0, 1, 4, 3, 2, 1]
    # seq = [1, 2, 3, 4, 5, 6, 5, 4, 4, 5, 6, 5, 4, 1, 2, 1, 4, 5, 6, 5, 4, 4, 5, 6, 5, 4, 3, 2, 1]
    # seq = [1, 2, 3, 4, 5, 6, 4, 5, 6, 4, 5, 6, 5, 4, 1, 2, 1, 4, 5, 6, 4, 5, 6, 4, 5, 6, 5, 4, 3, 2, 1]
    seq = [1,6,7,6,1,6,7,6,1,2,3,2,1,2,3,2,1,2,3,2,1]  # good
    seq = [1,6,7,6,1,6,7,6,1,2,3,2,1,2,3,2,1,2,3,2,1,6,7,6,1]  # mirror missing 1232@8

    # Repeat tests
    # seq = [1, 2, 3, 4, 1, 4, 4, 1, 1, 2, 3, 4]
    # seq = [1,2,3,4,5,2,3,4,6,2,3,4,7,1,2,3,4]
    # seq = [1,2,3,4,5,2,3,4,6,1,2,3,4]
    # seq = [1,2,3,1,2,3,6,1,2,3,1,2,3]  # want extra repeat of the doublet
    # R,M: simple and as 2D
    # seq = [1, 2, 3, 2, 3, 2, 3, 2, 3, 2, 1]
    # seq = [[1,1],[2,1],[3,1],[2,1],[3,1],[2,1],[3,1],[2,1],[3,1],[2,1],[1,1]]
    # R: super simple 2D
    # seq = [1, 2, 3, 4, 5, 3, 4, 5, 6, 7, 8, 6, 7, 8, 2, 3, 4, 6, 7, 8, 9]
    # seq = [[1,1],[2,1],[3,1],[1,1],[2,1],[3,1],[1,1],[2,1],[3,1],[1,1],[2,1],[3,1]]
    # seq = [1,2,3,4,1,2,3,4,1,2,3,4,1,2,3,4]
    # seq = [1,2,1,2,1,2,1,2,1,2,1,2]

    # seq = beryl
    print("       0  1  2  3  4  5  6  7  8  9  0  1  2  3  4  5  6  7  8  9  0  1  2  3")
    print("Seq =", seq, len(seq))
    # result = find_mirrors(seq)
    # result = find_repeats(seq, 2)
    # print("\nCollection: (%d)" % (len(result)))
    # print(result)
    # for r in result:
    #    print(r)
    # print()
    print("       0  1  2  3  4  5  6  7  8  9  0  1  2  3  4  5  6  7  8  9  0  1  2  3")
    print("Seq =", seq)
    # parse_mirrors(seq, result)
    # parse_repeats(seq, result)
    # f = find_mirrors_repeats(seq)
    # print("Mirrors")
    # for i in f['mirrors']:
        # print(i)
    # print("Repeats")
    # for i in f['repeats']:
        # print(i)
    #
    test = Pattern(seq, 2)
    print(test)
    for p in test.repeats:
        print(" ",p,"\n   ", p.positions)
    # print("!!!#",len(test.mirrors), test.mirrors)
    for p in test.mirrors:
        print(" ",p,"\n   ", p.positions)
    for p in test.spans:
        print(" ",p,"\n   ", p.positions)

# Todo
#  can we lose deepcopies
#  can we lose extra check for already ?
#  can we do -1 for unused slots - ignores
# what about the other mirror in aae
