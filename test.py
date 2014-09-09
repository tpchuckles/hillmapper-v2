a={'fart':[0,1,2,3,4,5,6,7,8,9,10], 'poop':3}
b=[0,1,2,3,4,5,6,7]
#1=[a,b]
maxl=4

newa=a.copy()
a['fart']=a['fart'][:maxl]
newa['fart']=newa['fart'][maxl:]
print a
print newa