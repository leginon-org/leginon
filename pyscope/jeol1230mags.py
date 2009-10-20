# joel1230mags.py contains magnification table for jeol 1230
# Author: Minghui Hu, mhu@nysbc.org, New York Structural Biology Center


screenup_LM = [ 50, 60, 80, 100, 120, 150, 200, 250, 300, 400, 500, 600, 800]
screendown_LM = screenup_LM									# 13 LM mags


screenup_M = []
screendown_M = screenup_M									# 0 M mags


screenup_SA = [1000, 1200, 1500, 2000, 2500, 3000, 4000, 5000, 6000, 8000, 10000, 12000, 15000, 20000, 25000, 30000, 40000, 50000, 60000, 80000, 100000, 120000, 150000, 200000, 250000, 300000, 400000, 500000]
screendown_SA = screenup_SA									# 28 SA mags


screenup = screenup_LM + screenup_M + screenup_SA
screendown = screenup										# Totally there are 41 mags