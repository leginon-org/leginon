#! /usr/bin/env perl 
# wjr 2025-02-07
# Script to auto capture a specific screen every n seconds, default 1800 = 30 min
# used for Smart Leginon sessions
# Saves images in the main Leginon directory for the session.
# Requires perl DBI CSPAN plugin.
# Requires import from ImageMagick to do the screen capture. Newer versions may require "magick import" instead of import.
# Requires the Leginon Window ID, which can be obtained using xwininfo or other similar programs
   
#  Usage: $0 <optional window-id> 
#  Use xwininfo to get window-id of Leginon window.

use strict;
use warnings;
use DBI;
my $host='10.150.38.162'; # leginon db host IP, CHANGE as needed
my $user = 'usr_object';  # leginon db user, CHANGE as needed
my $pw = 'MYPASSWORD'; # leginon database password, CHANGE as needed
my $sleeptime=1800;  #seconds between screencaps, CHANGE as needed

my @months = qw(Jan Feb Mar Apr May Jun Jul Aug Sep Oct Nov Dec);
my @days = qw(Sun Mon Tue Wed Thur Fri Sat Sun);
print "\nLeave Leginon in Square targeting node and make sure window covers atlas\n\n";

unless (defined $ARGV[0]) {
   print "Usage: $0 <window-id>\n";
   print "To get window-id, run xwininfo and click on the Leginon main window.\n"
   die;
}
my $window_id = $ARGV[0];

my $dbh = DBI -> connect("dbi:mysql:database=leginondb;host=$host;port=3306;mysql_compression=1",$user,$pw);
while (1) {
   my ($sec,$min,$hour,$mday,$mon,$year,$wday,$yday,$isdst) = localtime();
   my $session;
   $year += 1900;
   my $name = sprintf("%.4d%s%.2d_%.2d_%.2d",$year,$months[$mon],$mday,$hour,$min);
   my @wininfo=`xwininfo -id $window_id`;
   foreach my $line (@wininfo) {
      if ($line =~ m/Leginon:\s+(\w+)/) {
         $session = $1;
         last;
     }
   }
   my $rows = $dbh->selectall_arrayref("SELECT DEF_id,comment,`image path` FROM SessionData WHERE name = '$session';");
   my $row = pop @$rows;
   my $def_id = $row->[0];
   my $comment = $row->[1];
   my $dir = $row->[2];
   $dir =~s/rawdata//;   # save in main leginon rather than mixing up with images 
   $comment =~ s/\s+/_/g;
   $rows = $dbh->selectall_arrayref("SELECT filename FROM AcquisitionImageData WHERE `REF|SessionData|session`=$def_id;");
   $row = pop @$rows;  # get the last image taken in session as the source for the grid name
   my $gridname = $row->[0];
   if ($gridname =~ m/($session\_[a-zA-Z0-9]+\_)/) {
      $name = 'atlas_' . $1 . '_' . $comment . $name ; 
   }
   else {
      $name = 'atlas_' . $comment . '_' . $name ;
   }
   my $outfile = $dir . $name . '.png';
   print "saving to $outfile\n";
   `import -window $window_id $outfile`;
   print "sleeping for $sleeptime seconds\n";
   sleep $sleeptime;
}
