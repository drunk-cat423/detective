from collections import defaultdict
from typing import List


def numEquivDominoPairs(dominoes: List[List[int]]) -> int:
    idk = defaultdict(int)
    cnt = 0
    for i, x in enumerate(dominoes):
        if tuple([x[1], x[0]]) in idk:
            cnt += 1
        elif tuple([x[0],x[1]]) in idk:
            cnt += idk[tuple(x)]
            print(f"idk{x}:{idk[tuple(x)]}")
        idk[tuple(x)] += 1
        print(cnt)
        print(idk)
        print("==================")
    return cnt

dominoes = [[1,1],[2,2],[1,1],[1,2],[1,2],[1,1]]
numEquivDominoPairs(dominoes)