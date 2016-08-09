<?php

/* EXAMPLES 

{"command": "destinations", "username":"dcshrum", "jobType": "ctfestimate","script": "ctfestimate.py"}
 
 */

/**
Handler received text:{"username": "dcshrum", "command": "destinations", "jobType": "partalign", "script": ["runXmipp3CL2D.py", "--bin=3", "--lowpass=10", "--highpass=2000", "--max-iter=15", "--commit", "--nodes=1", "--ppn=2", "--mem=5", "--walltime=3", "--cput=4", "--description=testing stuff", "--runname=cl2d6", "--rundir=/lustre/cryo/lustre/appiondata/15nov02z/align/cl2d6", "--stack=1", "--num-ref=20", "--num-part=173", "--correlation", "--classical_multiref", "--nproc=2", "--projectid=461", "--expid=9681", "--jobtype=partalign", "--jobid=2911"]}

 */
class Destinations {

    public function getParams($script, $username, $group) {

        $scriptName = $script[0];
        
        $s = file_get_contents('Settings.json');
        $s_array = json_decode($s, true);

        # get defaults.... not doing anything right now...
        /*$resultArray = $s_array['GlobalJobParameters']['default'];
        if (array_key_exists($scriptName, $s_array['GlobalJobParameters'])) {
            $resultArray = array_replace_recursive($resultArray,$s_array['GlobalJobParameters'][$scriptName]);
        }
        if (array_key_exists($username, $s_array['UserJobParameters'])) {
            $resultArray = array_replace_recursive($resultArray,$s_array['UserJobParameters'][$username]['default']);
        }
        if (array_key_exists($scriptName, $s_array['UserJobParameters'][$username])) {
            $resultArray = array_replace_recursive($resultArray,$s_array['UserJobParameters'][$username][$scriptName]);
        }*/
                
        
        $resultArray = $s_array['GlobalJobParameters']['default'];
        # check to see if global app specific setting exist... 
        if (array_key_exists($scriptName, $s_array['GlobalJobParameters'])) {
            if (array_key_exists('header', $s_array['UserJobParameters'][$username][$scriptName])) {
                $resultArray['header'] = $s_array['UserJobParameters'][$username][$scriptName]['header'];
            }
            if (array_key_exists('prefix', $s_array['UserJobParameters'][$username][$scriptName])) {
                $resultArray['prefix'] = $s_array['UserJobParameters'][$username][$scriptName]['prefix'];
            }
            if (array_key_exists('execCommand', $s_array['UserJobParameters'][$username][$scriptName])) {
                $resultArray['execCommand'] = $s_array['UserJobParameters'][$username][$scriptName]['execCommand'];
            }
            if (array_key_exists('statusCommand', $s_array['UserJobParameters'][$username][$scriptName])) {
                $resultArray['statusCommand'] = $s_array['UserJobParameters'][$username][$scriptName]['statusCommand'];
            }
            if (array_key_exists('options', $s_array['UserJobParameters'][$username][$scriptName])) { 
                $resultArray['options'] = $s_array['UserJobParameters'][$username][$scriptName]['options'];
            }
            if (array_key_exists('executables', $s_array['UserJobParameters'][$username][$scriptName])) { 
                $resultArray['executables'] = $s_array['UserJobParameters'][$username][$scriptName]['executables'];
            }
        }        
        ## DEFUALTS are set

        
        
        # check to see if user specific setting are there....
        # if so take setting specific to user and app...
        if (array_key_exists($scriptName, $s_array['GlobalJobParameters'])) {
            if (array_key_exists('header', $s_array['GlobalJobParameters'][$scriptName])) {
                $resultArray['header'] = $s_array['GlobalJobParameters'][$scriptName]['header'];
            }
            if (array_key_exists('prefix', $s_array['GlobalJobParameters'][$scriptName])) {
                $resultArray['prefix'] = $s_array['GlobalJobParameters'][$scriptName]['prefix'];
            }
            if (array_key_exists('execCommand', $s_array['GlobalJobParameters'][$scriptName])) {
                $resultArray['execCommand'] = $s_array['GlobalJobParameters'][$scriptName]['execCommand'];
            }
            if (array_key_exists('statusCommand', $s_array['GlobalJobParameters'][$scriptName])) {
                $resultArray['statusCommand'] = $s_array['GlobalJobParameters'][$scriptName]['statusCommand'];
            }
            if (array_key_exists('options', $s_array['GlobalJobParameters'][$scriptName])) {
                $resultArray['options'] = $s_array['GlobalJobParameters']   [$scriptName]['options'];
            }
            if (array_key_exists('executables', $s_array['GlobalJobParameters'][$scriptName])) {
                $resultArray['executables'] = $s_array['GlobalJobParameters']   [$scriptName]['executables'];
            }
        } 
    
        # or default settings for user...
        # notice I only write over parts of the result that are there.
        # so if no user header is defined we'll return the defaults.
        
        if (array_key_exists($username, $s_array['UserJobParameters'])) {
            if (!array_key_exists($scriptName, $s_array['UserJobParameters'][$username])) {
                $scriptName = "default";
            }
            if (array_key_exists('header', $s_array['UserJobParameters'][$username][$scriptName])) {
                $resultArray['header'] = $s_array['UserJobParameters'][$username][$scriptName]['header'];
            }
            if (array_key_exists('prefix', $s_array['UserJobParameters'][$username][$scriptName])) {
                $resultArray['prefix'] = $s_array['UserJobParameters'][$username][$scriptName]['prefix'];
            }
            if (array_key_exists('execCommand', $s_array['UserJobParameters'][$username][$scriptName])) {
                $resultArray['execCommand'] = $s_array['UserJobParameters'][$username][$scriptName]['execCommand'];
            }
            if (array_key_exists('statusCommand', $s_array['UserJobParameters'][$username][$scriptName])) {
                $resultArray['statusCommand'] = $s_array['UserJobParameters'][$username][$scriptName]['statusCommand'];
            }
            if (array_key_exists('options', $s_array['UserJobParameters'][$username][$scriptName])) {
                $resultArray['options'] = $s_array['UserJobParameters'][$username][$scriptName]['options'];
            }
            if (array_key_exists('executables', $s_array['UserJobParameters'][$username][$scriptName])) {
                $resultArray['executables'] = $s_array['UserJobParameters'][$username][$scriptName]['executables'];
            }
        }
        
        foreach ($script as $item) {
            // --nproc=33 Number of Processors 
            if (preg_match('/^--template-list/', $item)) {
                $a = explode("=", $item);
                $numTemplates = count(explode(",", $a[1]));
                if ($numTemplates > 8) {
                    $numTemplates = 8;
                }
                $resultArray['options']['-n'] = (string)$numTemplates;
                $resultArray['options']['-N'] = "1";
            }

// --template-list=731,721,701
        }
        
        return $resultArray;
                        
    }
}
