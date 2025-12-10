-   $outdir is the directory that contains the disk, session, jobtype, but not the runname: For example: /data/appion/10dec16a/extract


-   $rundir = $outdir + runname, For example: /data/appion/10dec16a/extract/dogrun1
    note: appion python code only accepts $rundir


-   $description


-   $commit


-   $command


-   $sessiondata'


-   $sessionid vs. $sessionId vs. $expid vs. $expId


-   $apix vs. $pixelsize


-   $box vs. $boxsize

## variable dump

    cd ~/myami/myamiweb/processing
    cat *.php | grep '$[A-Za-z]' | sed 's/$_[A-Za-z]*//' | sed 's/[^$]*($[A-Za-z0-9]*)[^$]*/\1 
    /g' | sort | uniq -c | sort -rn | head -50

<# of occurrences> `<variable name>

    1066 $command 
    1001 $particle 
     943 $ 
     854 $expId 
     630 $i 
     387 $formAction 
     385 $html 
     366 $javascript 
     349 $outdir 
     337 $projectId 
     327 $runname 
     326 $sessionId 
     299 $extra 
     213 $description 
     200 $graph 
     198 $stackid 
     198 $sessioninfo 
     186 $apix 
     180 $sessiondata 
     162 $display 
     160 $title 
     158 $templatetable 
     157 $user 
     136 $line 
     131 $javafunctions 
     127 $heading 
     126 $numpart 
     125 $jobinfo 
     117 $errors 
     114 $stackinfo 
     110 $t 
     110 $key 
     109 $s 
     108 $templateinfo 
     101 $sessionpath 
      98 $bin 
      96 $tomogram 
      96 $sub 
      96 $nproc 
      96 $filename 
      94 $stackId 
      91 $headinfo 
      90 $sessionname 
      90 $data 
      89 $j 
      89 $cmd 
      89 $box 
      89 $alignId 
      86 $r 
