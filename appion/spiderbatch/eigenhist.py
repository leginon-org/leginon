#!/usr/bin/python

# eigenhist.py : converts the cor_EIG.dat file output by CA S into
#               a file of gnuplot commands to view as a histogram.

# use: python eigenhist.py cor_EIG.dat [eigenhist.dat] > gnuplotfile
#   where cor_EIG.dat is the input file from CA S,
#   eigenhist.dat, is the output doc file of percents, with keys as the eigenvalue number
#   If no output is specified, the output is named 'eigenhist.ext'

import os
import sys
import time

# returns current time as tuple of 3 strings: (date, time, ID)
# e.g., ('16-OCT-03', '13:08:16', '031016130816')
def nowisthetime():
    tt = time.localtime(time.time())
    # localtime return format: (2003, 10, 16, 12, 48, 30, 3, 289, 1)
    t = time.asctime(tt).split()
    # asctime return format: 'Thu Oct 16 12:50:17 2003'
    mo = t[1].upper()
    day = t[2]
    timestr = t[3]
    yr = t[4]
    datestr = "%s-%s-%s" % (day, mo, yr)

    yr = yr[-2:]
    # this is just to get the month as a number
    d = map(str,tt)   # stringify all numbers in the tuple
    mon = d[1]
    if len(mon) < 2: mon = '0' + mon
    (h,m,s) = timestr.split(':')
    idstr = "%s%s%s%s%s%s" % (yr,mon,day,h,m,s)

    return (datestr, timestr, idstr)

def makeDocfileHeader(filename):
    filename = os.path.basename(filename)
    name, ext = os.path.splitext(filename)
    ext = ext[1:]
    date,time,idstr = nowisthetime()
    h = " ;%s/%s   %s AT %s   %s\n" % (ext,ext,date,time,filename)
    return h

def makeGnuplotCommands(filename, nboxes):
    " n = number of lines in doc file "
    min = 0.2
    max = nboxes + 0.5
    gnutxt = 'set xlabel "Eigenvalue number"\n'
    gnutxt += 'set ylabel "%"\n'
    gnutxt += 'set xrange [%3.1f:%3.1f]\n' % (min, max)
    gnutxt += 'set boxwidth 0.5\n'
    gnutxt += 'plot "%s" using 1:3 title "%s" with boxes\n' % (filename, filename)
    return gnutxt

#--------------------------------------------------------------------
if __name__ == '__main__':
    length = len(sys.argv[1:])

    docfile = 'eigenhist'

    if length == 0:
        print "Usage: python eigenhist.py PREFIX_EIG_file [output_docfile] > gnuplotfile"
        sys.exit(0)
    elif length == 1:
        eigfile = sys.argv[1]
        name, ext = os.path.splitext(eigfile)
        docfile += ext
    elif length == 2:
        eigfile = sys.argv[1]
        docfile = sys.argv[2]

    # read the EIG file
    fp = open(eigfile,'r')
    B = fp.readlines()
    fp.close()

    B = B[1:]  # drop the 1st line
    doctxt = makeDocfileHeader(docfile)

    k = 1
    for line in B:
        s = line.split()
        percent = float(s[1])
        doctxt += "%5d 1%12f\n" % (k, percent)
        k += 1

    # write out the doc file
    fp = open(docfile,'w')
    fp.writelines(doctxt)
    fp.close()

    print makeGnuplotCommands(docfile, k-1)
