<?php 
/*
 {
	"session-data": {
		"processingdb": "ap461",
		"expId": "9681",
		"projectId": "461",
		"advanced_user": "0",
		"username": "dcshrum",
		"password": "dcshrum",
		"loggedin": "1",
		"processinghost": "localhost"
	},
	"command": "runJob.py ctfestimate.py --runname=ctffindrun7 
                   --rundir=/lustre/cryo/lustre/appiondata/15nov02z/ctf/ctffindrun7 
                   --commit --preset=upload --projectid=461 --session=15nov02z 
                  --no-rejects --no-wait --continue --ampcarbon=0.15 --ampice=0.07 
                  --fieldsize=512 --medium=ice --bin=2 --resmin=100 --resmax=10 
                  --defstep=1000 --numstep=25 --dast=500 --expid=9681 
                  --jobtype=ctfestimate --ppn=1 --nodes=1 --walltime=240 --jobid=2351 "
}
*/

class RunJob {

    public function apache_runjob($fullCommand, $username, $group) {

        if ((preg_match('/dogPicker/', $fullCommand)) && (preg_match('/--mrclist/', $fullCommand))) {
            $result = preg_replace('/^.*runJob\.py dogPicker\.py/', 'dogPicker.py', $fullCommand); 
            $fullCommand = preg_replace('/--jobtype=dogpicker.*$/', '--jobtype=dogpicker', $result); 
        }
        if ((preg_match('/templateCorrelator/', $fullCommand)) && (preg_match('/--mrclist/', $fullCommand))) {
            $result = preg_replace('/^.*runJob\.py templateCorrelator\.py/', 'templateCorrelator.py', $fullCommand); 
            $fullCommand = preg_replace('/--jobtype=templatecorrelator.*$/', '--jobtype=templatecorrelator', $result); 
        }
       
        $file = '/var/log/webservice.log';
        $stamp = date("Y-m-d h:i:sa");
        file_put_contents($file, "\n\n" . $stamp, FILE_APPEND | LOCK_EX);
       
        $fullCommand = str_replace("\"", "\\\"", $fullCommand );
       
        $runCmd = "/usr/bin/sudo /var/www/webservice/apache_runjob.sh \"" . $fullCommand . "\" \"" . $username . "\" \"" . $group . "\""; // &> /testing/result.txt";
       
        file_put_contents($file, "\n\n" . $runCmd, FILE_APPEND | LOCK_EX);
        
        exec($runCmd, $output, $return);
        file_put_contents($file, "OUTPUT:" . $output, FILE_APPEND | LOCK_EX);
        file_put_contents($file, "RETURN CODE:" . $return, FILE_APPEND | LOCK_EX);
        
        if ((preg_match('/dogPicker/', $fullCommand)) && (preg_match('/--mrclist/', $fullCommand))) {
            file_put_contents($file, "returned output (see above)", FILE_APPEND | LOCK_EX);
            return $output;
        }
        if ((preg_match('/templateCorrelator/', $fullCommand)) && (preg_match('/--mrclist/', $fullCommand))) {
            file_put_contents($file, "returned output (see above)", FILE_APPEND | LOCK_EX);
            return $output;
        }
        
        
        foreach ($output as $line) {
            if(preg_match("/^\d\d\d\d\d/",$line)) { 
                file_put_contents($file, "Returned " . $line, FILE_APPEND | LOCK_EX);
                return $line;
            }
        }
        
        //return 1617523;
        file_put_contents($file, "Returned \"\"", FILE_APPEND | LOCK_EX);
        return "";
    }

} 
