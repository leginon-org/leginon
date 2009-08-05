#!/usr/bin/python

import os
import sys
import time
from optparse import OptionParser

def getSyntax():
    syntax = '\n'
    syntax += 'Description:\n'
    syntax += '    Takes dres.spi file from Spider and \n'
    syntax += '    generates a text file (dres.txt) and gnuplot command file (dres.plot)\n'
    syntax += '    These can be used to plot the resolution curve using gnuplot.\n'
    syntax += '\n'
    syntax += 'Syntax:\n'
    syntax += '    python %s dres.spi [options] > dres.plot\n' % sys.argv[0]
    syntax += '    where dres.spi is the input file from spider\n'
    syntax += '    -h, --help to show all optional arguments\n'
    syntax += '\n'
    syntax += 'Example:\n'
    syntax += '  Step 1) Make gnuplot commands and text file using %s:\n' % sys.argv[0]
    syntax += '    >  python %s dres002.spi\n' % sys.argv[0]
    syntax += '    >  python %s dres002.spi -a 4.2 -p dres002.plot\n' % sys.argv[0]
    syntax += '    >  python %s dres002.spi -p dres002.plot\n' % sys.argv[0]
    syntax += '    >  python %s dres002.spi -a 4.2 -t 6023 -n 2915 -p dres002.plot\n' % sys.argv[0]
    syntax += '    >  python %s dres002.spi -a 4.2 -o dres002.txt -p dres002.plot --cref\n' % sys.argv[0]
    syntax += '  Step 2) Make FSC plot with gnuplot:\n'
    syntax += '    >  gnuplot -persist dres.plot\n'
    syntax += '  Step 3) Export FSC plot as encapsulated postscript to make a figure:\n'
    syntax += '    >  gnuplot\n'
    syntax += '       >>> set term post eps\n'
    syntax += '       >>> set output \'dres.eps\'\n'
    syntax += '       >>> load \'dres.plot\'\n'
    syntax += '       >>> set term x11\n'
    syntax += '       >>> set output\n'
    syntax += '       >>> quit\n'
    return syntax

def parseArguments():
    syntax = 'python %prog dresfile.spi [options] gnuplot.plot'
    parse = OptionParser(usage=syntax)
    parse.add_option("-a", "--apix", dest="Apix", default=1.0, type="float", help="Pixel size in Angstroms")
    parse.add_option("-o", "--outtxt", dest="txtfile", default='', type="string", help="Name of output text file")
    parse.add_option("-p", "--plot", dest='plotfile', default='', type="string", help="Name of output gnuplot command file")
    parse.add_option("-t", "--total", dest="nt", type="int", default=0, help="Total number of particles")
    parse.add_option("-n", "--num", dest="ni", type="int", default=0, help="Number of particles in subgroup")
    parse.add_option("-c", "--cref", dest="Cref", action="store_true", default=False, help="Also make Cref curve")
    (options, args) = parse.parse_args()
    return options, args

def nowisthetime():
    """ returns current time as tuple of 3 strings: (date, time, ID)
        e.g., ('16-OCT-03', '13:08:16', '031016130816')"""
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

def makeGnuplotCommands(datafile, max):
    " n = number of lines in doc file "
    min = 0.0
    gnutxt = 'set xlabel "Resolution (A)"\n'
    gnutxt += 'set ylabel "Correlation"\n'
    gnutxt += 'set xrange [%3.1f:%3.1f]\n' % (min, max)
    gnutxt += 'set grid \n'
    tics = [50,40,30,25,20,15,12,10,5]
    gnutxt += 'set xtics ('
    for tic in tics:
        if tic > 1/max:
            gnutxt += '"%1.0f" %1.9g, ' % (tic,1./tic)
    gnutxt += '"%2.2g" %1.9g) \n' % (1./max,max)
    gnutxt += 'set yrange [-0.1:1.1]\n'
    gnutxt += 'set ytics (0, 0.25, 0.5, 0.75, 1.0)\n'
    gnutxt += 'set title "%s"\n' % os.path.basename(datafile)
    gnutxt += 'set boxwidth 0.007\n'
    gnutxt += 'plot "%s" using 1:2 title "%s" with linespoints' % (datafile, 'FSC')
    gnutxt += ', "%s" using 1:3 title "%s" with lines' % (datafile, '3-sigma')
    #gnutxt += ', ((x*0)+0.5) title "%s" \n' % (0.5)
    return gnutxt

#--------------------------------------------------------------------
if __name__ == '__main__':
    if len(sys.argv[1:]) < 1 or '-h' in sys.argv or '--help' in sys.argv:
        syntax = getSyntax()
        print syntax
    (options,args)=parseArguments()
    if len(args) == 0:
        sys.exit(0)
    dresfile = args[0]
    if len(options.txtfile) == 0:
        txtfile,ext = os.path.splitext(dresfile)
        txtfile += '.txt'
    if len(options.plotfile) == 0:
        plotfile,ext = os.path.splitext(dresfile)
        plotfile += '.plot'

    ##figure out if 2nd argument is Apix(float) or dres(string)
    #if length == 2:
    #    if isinstance(sys.argv[2], str):
    #        try:
    #            Apix = float(sys.argv[2])
    #        except ValueError:
    #            txtfile = sys.argv[2]
    #    elif isinstance(sys.argv[2], (int, float)):
    #        Apix = float(sys.argv[2])
    #elif length == 3:
    #    Apix = float(sys.argv[2])
    #    txtfile = sys.argv[3]

    infile = open(dresfile,'r')    # read the DRES file
    FSCadj = True
    if options.nt < options.ni:
        print "Error..number of particles in subgroup %d is greater than total number of particles %d" % (options.ni, options.nt)
        sys.exit(1)
    if options.nt == 0 or options.ni == 0:
        FSCadj = False
    doctxt = makeDocfileHeader(txtfile)
    for line in infile:
        if not ' ;' in line:
            s = line.split()    #keys=0,cols=1,freq=2,dpc=3,frc=4,frccrit=5,voxels=6
            freq = float(s[2])/options.Apix  # freq=(1/pix)*(pix/A)
            fsc = float(s[4])
            crit = float(s[5])
            doctxt += " %9.9g  %9.9g  %9.9g " % (freq,fsc,crit)
            if FSCadj == True:
                adj = fsc/(fsc*(1.0-float(options.ni)/float(options.nt))+(float(options.ni)/float(options.nt)))
                doctxt += " %9.9g " % (adj)
            if options.Cref == True:
                try: #sometimes fsc is negative number, instead set to zero
                    cref = ((2*fsc)/(1+fsc))**0.5
                except ValueError:
                    cref = 0.0
                doctxt += " %9.9g " % (cref)
            doctxt += "\n"
    infile.close()
    # write out the doc file
    outfile = open(txtfile, 'w')
    outfile.writelines(doctxt)
    outfile.close()
    
    gnucom = makeGnuplotCommands(txtfile, freq) #lastfreq is max-x value
    column = 3
    if FSCadj == True:
        column += 1
        gnucom += ', "%s" using 1:%d title "%s" with linespoints' % (txtfile, column, 'FSCadj')
    if options.Cref == True:
        column +=1
        gnucom += ', "%s" using 1:%d title "%s" with linespoints' % (txtfile, column, 'Cref')
    outfile = open(plotfile, 'w')
    outfile.writelines(gnucom)
    outfile.close()
    #print gnucom
