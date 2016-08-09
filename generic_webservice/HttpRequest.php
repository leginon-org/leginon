<?php

// IF the web service needs to call a webservice...  
class HttpRequest {

    public function sendRequest($method, $url, $content) {
        $ch = curl_init($url);
        curl_setopt($ch, CURLOPT_RETURNTRANSFER, true);
        curl_setopt($ch, CURLOPT_SSL_VERIFYPEER, false);
        curl_setopt($ch, CURLOPT_HTTPHEADER, Array("Content-Type: application/json"));

        //Can be GET - read/  POST - create / PUT - update  / DELETE - delete
        curl_setopt($ch, CURLOPT_CUSTOMREQUEST, $method);
        if ($method !== "GET") {
            curl_setopt($ch, CURLOPT_POSTFIELDS, $content);
        }
        try {
            curl_setopt($ch, CURLOPT_FOLLOWLOCATION, true);
            $response = curl_exec($ch);

            if (curl_error($ch)) {
                curl_close($ch);
                return curl_error($ch);
            }

            //$head = curl_getinfo($ch);
            //$content = $head["content_type"]; //application/json
            //$code = $head["http_code"]; //200
            curl_close($ch);

            return $response;
            
        } catch (Exception $e) {
            throw $e;
        }
    }

    //put your code here
}
