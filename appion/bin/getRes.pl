#!/usr/bin/env perl

# go through a fsc.eotest.* file and determine the resolution at 0.5
# usage: getRes [iteration] [boxsize] [ang/pix]

if (!$ARGV[2]){
    print "\nusage: getRes.pl [iteration] [boxsize] [ang/pix]\n";
    exit;
}

$iter=$ARGV[0];
$box=$ARGV[1];
$apix=$ARGV[2];
$file='fsc.eotest.'.$iter;

open(FILE,"<$file") || die("Couldn't open file: $file");

@plot=<FILE>;

close(FILE);

$lastx=0;
$lasty=0;
foreach $point(@plot) {
    chomp($point);
    ($x,$y)=split('\s+',$point);
    if ($y>0.5){
	$lastx=$x;
	$lasty=$y;
    }
    else {
	# get difference of fsc
	$diffy=$lasty-$y;

	# get distance from 0.5
	$distfsc=(0.5-$y)/$diffy;

	# get interpolated spatial freq
	$intfsc=$x-($distfsc*($x-$lastx));

	$res=$box*$apix/$intfsc;
	print "iteration $iter: $res\n";
	exit;
    }
}
#FSC does not go below 0.5
$res=$box*$apix/$lastx;
print "iteration $iter: $res\n";

