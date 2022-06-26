#!/bin/sh
### BEGIN INIT INFO
# Provides:          Mdluex
# Required-Start:    $remote_fs $syslog
# Required-Stop:     $remote_fs $syslog
# Default-Start:     2 3 4 5
# Default-Stop:      0 1 6
# Short-Description: Start Alexa at boot time
# Description:       Enable Alexa service.
### END INIT INFO

python3 /home/pi/wword.py --access_key 'replace this with your access key' --keyword_paths '/home/pi/alexa_en_raspberry-pi_v2_1_0.ppn' --sensitivities 0.8