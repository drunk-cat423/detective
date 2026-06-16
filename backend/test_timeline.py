queries = ["bbb","cc"]
words = ["a","aa","aaa","aaaa"]


def f(s):
    s_sort = sorted(s)
    cnt = 0
    for i, x in enumerate(s_sort):
        if x == s_sort[0]:
            cnt += 1
        else:
            break
    return cnt


arr1 = []
arr2 = []
for item in queries:
    arr1.append(f(item))
for item in words:
    arr2.append(f(item))
arr2.sort()
print(arr1)
print(arr2)


def lower_bound(nums, target):
    left = 0
    right = len(nums) - 1
    while left <= right:
        mid = (left + right) // 2
        if nums[mid] < target:
            left = mid + 1
        else:
            right = mid - 1
    return len(nums) - left


result = []
for i, x in enumerate(arr1):
    result.append(lower_bound(arr2, x))

print(result)


#1 3 7 12
#3 10 21