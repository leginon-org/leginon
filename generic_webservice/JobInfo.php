<?php

/**
 * The json content sent with this command:
 * {    "session-data":{"processingdb":"ap461","expId":"9681","projectId":"461",
 *      "processinghost":"localhost","advanced_user":"0","username":"dcshrum","password":"dcshrum","loggedin":"1" }, 
 * "command":"qstat -au dcshrum | egrep '^[0-9]'" }
 */
class JobInfo {

    // processing.inc (1015):  
    // processing.inc: checkcluster jobs runs: $cmd = "qstat -u ".$user." | egrep '^[0-9]'"; returns result

    public function checkQueue($username) {

        # a script that allows apache to run an squeue command as a different user
        $runCmd = "/usr/bin/sudo /var/www/webservice/apache_squeue.sh \"" . $username . "\""; 
        exec($runCmd, $output, $return);

        $value = "";
        foreach ($output as $row) {
            $value = $value . $row . "\n";
        }

        // echo $value;

        return $value;
    }
}
