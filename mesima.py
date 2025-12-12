
# nums = [2,11,7,15]
# target= 9
# nums2 = [3,3]
# target2= 6
# def sum(nums,target):
#     for i in nums:
#         need=target-i
#         if need in nums:
#             print(i,need)
#             break
# sum(nums,target)
# sum(nums2,target2)

# def reverse (x):
#     rx=int(str(x)[::-1])
#     return rx
# x=int(input("enter a number "))
# print(reverse(x)==x)


I=1
IV=4
V=5
IX=9
X=10
XL=40
L=50
XC=90
C=100
CD=400
D=500
CM=900
M=1000
# x="III"
# total=0
# y=list(x)
# print(y)




nums=[1,5,2,10]
biggest=0
x=len(nums)
for i   in range(x):
    for j in range(x):
        if nums[j]-nums[i]>biggest and j>i:
            biggest=nums[j]-nums[i]
    
if biggest>0:
    print(biggest)
else:
    print(-1)
    

