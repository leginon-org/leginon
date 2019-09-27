@cho off

set "source=C:\Users\supervisor\Documents\FEI\TIA\Exported Data"
set "destination=Z:\TEMScripting\BM-Falcon\microed"

robocopy "%source%" "%destination%" *.bin /mov /mot:1

exit b