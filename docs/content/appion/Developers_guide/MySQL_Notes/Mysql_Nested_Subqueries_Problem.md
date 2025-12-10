This is the query that I wanted to do because it is easy to understand (= easier to maintain).
Unfortunatly there is a bug in mysql (http://bugs.mysql.com/bug.php?id=10312) which makes this
so slow that no one has seen it complete. The subsequent query is a bit more difficult to follow
but gets around this problem.

    SELECT DB_PROJECT.projectexperiments.projectId 
    FROM DB_PROJECT.projectexperiments 
    WHERE DB_PROJECT.projectexperiments.name IN 
    ( 
        SELECT DB_LEGINON.SessionData.name 
        FROM DB_LEGINON.SessionData 
        WHERE DB_LEGINON.SessionData.`DEF_id` IN 
        ( 
            SELECT DB_PROJECT.shareexperiments.`REF|leginondata|SessionData|experiment` 
            FROM DB_PROJECT.shareexperiments 
            WHERE DB_PROJECT.shareexperiments.`REF|leginondata|UserData|user` = ".$userId." 
        )
    );

    SELECT DB_PROJECT.projectexperiments.projectId 
    FROM DB_PROJECT.projectexperiments 
    INNER JOIN 
    (
        SELECT DB_LEGINON.SessionData.name AS SessionName 
        FROM DB_LEGINON.SessionData 
        INNER JOIN 
        (       
            SELECT DB_PROJECT.shareexperiments.`REF|leginondata|SessionData|experiment` AS SessionId 
            FROM DB_PROJECT.shareexperiments 
            WHERE DB_PROJECT.shareexperiments.`REF|leginondata|UserData|user` = ".$userId." 
        ) AS SessionIds 
        ON DB_LEGINON.SessionData.`DEF_id` = SessionIds.SessionId 
    ) AS SessionNames 
    ON DB_PROJECT.projectexperiments.name = SessionNames.SessionName;

See another example [here](http://forums.mysql.com/read.php?24,54721,54721#msg-54721).
