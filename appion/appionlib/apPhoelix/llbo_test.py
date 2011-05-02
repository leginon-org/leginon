##For testing in terminal
"""
f = open('llbo.sa', 'w')

rise = 5
twist = -137.2
replen = 590
nfold = 1
maxbes = 60
maxll = 100

subs = replen/rise
if turns < 0:
	turns = math.floor((twist * subs)/360)
else:
	turns = math.ceil((twist * subs)/360)

i = 0
while i < maxll:
	j = -1*maxbes
	while j <= maxbes:
		test = ((nfold * i) + (turns * j))
		if test%subs == 0:
			bo = j
			ll = i
			print>>f, ll, bo
			i  = i+1
		else:	
			j = j+1
"""


##For testing in terminal:
"""
f = open('llbo.sa', 'w')
print>>f, 0, 0
llbo1 = [5,-13]
llbo2 = [6,8]
ll1 = llbo1[0]
bo1 = llbo1[1]
ll2 = llbo2[0]
bo2 = llbo2[1]
i = 0
startll = ll1 - (ll2 * 5)
startbo = bo1 - (bo2 * 5)
ll = startll
bo = startbo
while ll < 200:
	ll = startll + (ll2 * i)
	bo = startbo + (bo2 * i)
	while bo < 120 and bo > -120:
		if ll >= 0 and ll <= 100 and bo >= -60 and bo <= 60:
			print>>f, ll, bo
		ll = ll + ll1
		bo = bo + bo1
	i = i+1

i = 0
ll = 0
while ll < 200 and ll >= 0:
	ll = ll2 - (ll1 * i)
	bo = bo2 - (bo1 * i)
	while bo < 120 and bo > -120:
		if ll >= 0 and ll <= 100 and bo >= -60 and bo <= 60:
			print>>f, ll, bo
		ll = ll + ll2
		bo = bo + bo2
	i = i+1

f.close()
"""
