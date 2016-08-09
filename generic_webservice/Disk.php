<?php

class Disk {

    public function checkQuota($group) {

       // This will let myamiweb know if sufficient diskpace exists to run the application
       // The returns codes are based on code in myamiweb that looks for specific strings
       // and artifcat of running the df command and parsing output
        
       // anything under 99% is ok with myamiweb
       return "50% %50";

       # if this should return an error... 
       #         return "99% %99"  and myamiweb will error out with a disk space alert
    }

}
