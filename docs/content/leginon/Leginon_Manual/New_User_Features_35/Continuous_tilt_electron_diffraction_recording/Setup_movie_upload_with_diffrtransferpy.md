leginon/diffrtransfer.py is used to convert raw binary files from TIA to smv format that is more familiar to crystallography community and upload them to leginon database to be viewed through myamiweb. This is set up similarly to rawtransfer.py that is used to transfer direct detector frame movies.

    python diffrtransfer.py
    Usage: diffrtransfer.py [options]

    Options:
      -h, --help                       show this help message and exit
      --source_path=PATH    Mounted parent path to transfer, e.g. --source_path=/mnt/microed
      --check_interval=CHECK_INTERVAL
                                            Seconds between checking for new data
      --no_wait                       optional flag: Catch up upload without waiting for more images to come per series

1. Mount TIA_EXPORTED_DATA_NETWORK_DIR in fei.cfg on your linux host where diffrtransfer.py will be run from. This mounted point should be assigned to ---source_path

2. The default check_interval is 40 seconds.

3. The script needs access to the same libraries leginon needs as well as the database. It is therefore easiest to run as root like a service on the leginon processing host.

4. Files that failed, typically due to timing of data transfer, user interruption of data collection, are moved to a subdirectory bad_diffraction_series_id on the source_path. If it is determined later that these files are o.k. to upload, moving the *.bin back out will expose them for transfer again.

5. The transfer script moves the *.bin files in the session path /your_data/leginon/your_sessionname/diffraction_raw/tilt_series_id/

6. The converted SMV files are in /your_data/leginon/your_sessionname/diffraction/tilt_series_id/

For example, the following will check and process all *.bin files in /mnt/microed and repeat every 30 seconds for new ones.

    python diffrtransfer.py --source_path=/mnt/microed --check_interval=30
