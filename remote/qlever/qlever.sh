#!/bin/bash
### BEGIN INIT INFO
# Provides:          qlever
# Required-Start:    $remote_fs $syslog $network
# Required-Stop:     $remote_fs $syslog $network
# Default-Start:     2 3 4 5
# Default-Stop:      0 1 6
# Short-Description: QLever SPARQL server
# Description:       Start/stop the QLever SPARQL engine
### END INIT INFO

# install in /etc/init.d/qlever, then:
# sudo chmod 755 /etc/init.d/qlever
# sudo chown root:root /etc/init.d/qlever
# sudo update-rc.d qlever defaults

INDEX_PATH=/data/globalise_qlever/indexes
USER=qlever
NAME=qlever
DESC=triplestore
#INDEXES="globalise 1119 3598"
INDEXES="1119"

. /lib/lsb/init-functions

start_qlever() {
	# Start the qlever instances
	for i in $INDEXES; do
		log_daemon_msg "Starting $DESC" "$NAME-$i"
	  (cd ${INDEX_PATH}/$i && su -s /bin/sh $USER -c "make start") &
	done
}

stop_qlever() {
	# Stops the qlever instances
	for i in $INDEXES; do
	  (cd ${INDEX_PATH}/$i && su -s /bin/sh $USER -c "make stop")
	done
}

#upgrade_qlever() {
#	# Online upgrade qlever executable
#	cd ${INDEX_PATH} && sudo -u $USER make upgrade
#}

case "$1" in
	start)
		log_daemon_msg "Starting $DESC" "$NAME"
		start_qlever
#		case "$?" in
#			0|1) log_end_msg 0 ;;
#			2)   log_end_msg 1 ;;
#		esac
		;;
	stop)
		log_daemon_msg "Stopping $DESC" "$NAME"
		stop_qlever
#		case "$?" in
#			0|1) log_end_msg 0 ;;
#			2)   log_end_msg 1 ;;
#		esac
		;;
	restart)
		log_daemon_msg "Restarting $DESC" "$NAME"

		stop_qlever
		case "$?" in
			0|1)
				start_qlever
				case "$?" in
					0) log_end_msg 0 ;;
					1) log_end_msg 1 ;; # Old process is still running
					*) log_end_msg 1 ;; # Failed to start
				esac
				;;
			*)
				# Failed to stop
				log_end_msg 1
				;;
		esac
		;;
	status)
	  /usr/bin/qlever status
		;;
#	upgrade)
#		log_daemon_msg "Upgrading binary" "$NAME"
#		upgrade_qlever
#		log_end_msg $?
#		;;
	*)
		echo "Usage: $NAME {start|stop|restart|status}" >&2
		exit 3
		;;
esac

exit 0