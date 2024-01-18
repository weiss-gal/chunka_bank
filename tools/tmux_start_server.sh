function show_usage {
	echo "Usage: $(basename "$0") [-h] [session_name]"
	echo "  -h: Display this help message."
	echo "  session_name: tmux session name to use"
}


if [ $# -ne 1 ] || [ "$1" == "-h"  ] ; then
	show_usage
	exit 1
fi

tmux new-session -d -s $1 -n cb_server 'bash' \; \
	new-window -n cb_bot 'bash' \; \
	new-window -n backup 'bash'

tmux select-window -t 0 
tmux send-keys "python3 -m cb_server.cb_server" C-m
tmux select-window -t 1
tmux send-keys "python3 -m cb_bot.cb_bot" C-m
tmux select-window -t 2
tmux send-keys "python3 tools/backupd.py" C-m

