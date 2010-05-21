/<options/ d
/PRIMARY/ s/.*Key_name="\([^"]*\).*Column_name="\([^"]*\).*/    <key>PRIMARY KEY (`\2`)<\/key>/
/<key / s/.*Key_name="\([^"]*\).*Column_name="\([^"]*\).*/    <key>KEY `\2` (`\2`)<\/key>/
