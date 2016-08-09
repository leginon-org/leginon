<?php

class Disk {

    public function checkQuota($group) {

       // temp fix... 
       return "50% %50";

        $url = "http://v1.webservices.rcc.fsu.edu/allocations/lustre_quota?group=" . $group;

        $H = new HttpRequest();
        $response = $H->sendRequest("GET", $url, null);

        $ar = json_decode($response, true);

        if (($ar['Bytes Hard Limit'] - $ar['Bytes Used']) > 1073741824) {
            return "50% %50";
        }
        return "99% %99";
    }

}
