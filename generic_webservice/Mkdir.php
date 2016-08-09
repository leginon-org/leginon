<?php

// example data format:
// { "session-data":{"processingdb":"ap461","expId":"9681","projectId":"461","advanced_user":"0","username":"dcshrum","password":"dcshrum","loggedin":"1","processinghost":"localhost" }, "command":"mkdir -p /lustre/cryo/lustre/appiondata/15nov02z/ctf/ctffindrun2;" }
class Mkdir {

    public function apache_mkdir($fullCommand, $username, $groupname) {

        // mkdir -p /lustre/cryo/lustre/appiondata/15nov02z/ctf/ctffindrun9;
        // [root@kriosdb job_api]# /var/www/webservice/apache_mkdir.sh
        // usage: apache_mkdir.sh path user group (group is optional)
        
        $path = preg_replace('/mkdir -p /', '', $fullCommand);
        $path = preg_replace('/;/', '', $path);
        
        $runCmd = "/usr/bin/sudo /var/www/webservice/apache_mkdir.sh " . $path . " " . $username . " " . $groupname; //. " &> /testing/result.txt";
        exec($runCmd, $output, $return);
        //echo $runCmd . " returned $return, and output:\n";
        //var_dump($output);
        
        return $return;
    }

}
