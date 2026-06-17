from typing import List

arrays = [[-8,-7,-7,-5,1,1,3,4],[-2],[-10,-10,-7,0,1,3],[2]]

def maxDistance(arrays: List[List[int]]) -> int:
    n = len(arrays)
    mn = arrays[0][0]
    mx = arrays[0][-1]
    ans = 0
    for i in range(1, n):
        ans = max(abs(max(arrays[i]) - mn), abs(mx - min(arrays[i])))
        mn = min(mn, min(arrays[i]))
        mx = max(mx, max(arrays[i]))
        print(f"max: {mx}")
        print(f"min: {mn}")
        print(f"ans: {ans}")

maxDistance(arrays)
#1 3 7 12
#3 10 21