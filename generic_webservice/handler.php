<?php

include(__DIR__ . "/ErrorCodes.php");
include(__DIR__ . "/Disk.php");
include(__DIR__ . "/Mkdir.php");
include(__DIR__ . "/RunJob.php");
include(__DIR__ . "/JobInfo.php");
include(__DIR__ . "/HttpRequest.php");
include(__DIR__ . "/Destinations.php");

# this webservice listens for commands from both appion and myamiweb... this could be split between two webservers


// an example of the json data that is sent by appion:
//  { "session-data":{"processingdb":"ap461","expId":"9681","projectId":"461","advanced_user":"0","username":"dcshrum",
//                     "password":"xyzzzzz","loggedin":"1","processinghost":"localhost" }, 
//    "command":"mkdir -p /lustre/cryo/lustre/appiondata/15nov02z/ctf/ctffindrun9;" }




$server = new Server;
$server->serve();

echo json_encode($server->resultArray);

class Server {

    // custom response is filled in with whatever appion wants.
    public $resultArray = array("result" => 0, "customResponse" => 0);

    
    public function serve() {

        $file = '/var/log/webservice.log';
        $stamp = date("Y-m-d h:i:sa");
        
        file_put_contents($file, "\n\n" . $stamp, FILE_APPEND | LOCK_EX);
        $postdata = file_get_contents("php://input");
        file_put_contents($file, "\n\nHandler received text:" . $postdata, FILE_APPEND | LOCK_EX);
        $obj = json_decode($postdata, true);
        
        $note = "\n\nHandler received the command:" . $obj['command'] . ": from user:" . $obj['session-data']['username'] . ":"; 
        file_put_contents($file, $note, FILE_APPEND | LOCK_EX);
        
        // /var/www/html/myami_new/processing/inc/processing.inc:666 
        // appion will error over 98.  Hardcoded to 50 for now.
        // See Disk.php to change result based on Quota data.
        if (preg_match('/^df .*/', $obj['command'])) {
            $d = new Disk;
            $this->resultArray['customResponse'] = $d->checkQuota($this->returnGroup($obj['session-data']['username']));
        }

        // /var/www/html/myami_new/processing/inc/processing.inc:914 
        // gets a true / false return value.  
        elseif (preg_match('/^mkdir .*/', $obj['command'])) {
            $m = new Mkdir;
            $this->resultArray['customResponse'] = $m->apache_mkdir($obj['command'], $obj['session-data']['username'], $this->returnGroup($obj['session-data']['username']));
        }

        // /var/www/html/myami_new/processing/inc/processing.inc:666
        // appion wants just the job number back as a return value
        elseif (preg_match('/runJob\.py .*/', $obj['command'])) {
            $r = new RunJob;
            $this->resultArray['customResponse'] = $r->apache_runjob($obj['command'], $obj['session-data']['username'], $this->returnGroup($obj['session-data']['username']));
        } 
        // From  /var/www/html/myami_new/processing/inc/processing.inc:452
        //  "TODO: what if the cluster does not use qstat? Moab uses mstat or some thing like that."
        // This command's raw output is dumped so I'll format some nice html into a response.
        elseif (preg_match('/^qstat .*/', $obj['command'])) {
            $j = new JobInfo;
            $this->resultArray['customResponse'] = $j->checkQueue($obj['session-data']['username']);
        } 

        // returns headers for appion jobs
        elseif (preg_match('/^destinations.*/', $obj['command'])) {
            $d = new Destinations();
            $this->resultArray['customResponse'] = $d->getParams($obj['script'], $obj['username'], $this->returnGroup($obj['username']));
        }
        
        
        else {
            $this->resultArray['customResponse'] = 400;
        }
    }

    
    # this function determines what group a user should belong to 
    private function returnGroup($user) {
        $s = file_get_contents('Settings.json');
        $s_array = json_decode($s, true);
        
        if (array_key_exists($user, $s_array['CustomGroups'])) {
            return $s_array['CustomGroups'][$user];
        }

        
        
        # return the user name as the group if ntohing else...
        return $user;
    }

}
