This information is useful if you want to open specific ports between computers with a
firewall in between.

-   MySQL normally uses port 3306 (but configurable in /etc/my.cnf)


-   Leginon TCP standard port to listen to connection from others: port 55555


-   Leginon TCP port to send message to others: dynamically assigned ports between
    49152 and 65535, but most likely only the first two to three in this range (minimal 2 needed).

There is no strict port assignment since we could potentially have more than one Leginon process running on the same linux host talking to different TEM hosts in its original design, even though we've never used it that way. You should only worry about opening up the first few of those ports in your firewall (maybe 49152 through 49162, or something like that).

See more discussion at Leginon bulletin board thread on [Network problem - Leginon not seeing tecnai host](http://emg.nysbc.org/redmine/boards/6/topics/3).

[Go up](/leginon/Leginon_Manual/Complete_Installation/Network_Configuration)
