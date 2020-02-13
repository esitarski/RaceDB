#!/bin/bash

echo "Running init scripts stored in /docker-entrypoint-init.d"
#
# Run any other init scripts
for f in /docker-entrypoint-init.d/*; do
    case "$f" in
    	*.sh)
			if [ -x "$f" ]; then
			echo "$0: running bash script: $f"
			"$f"
			else
			echo "$0: sourcing bash script: $f"
			. "$f"
			fi
			;;
    	*.pl)
			if [ -x "$f" ]; then
			echo "$0: running perl script: $f"
			"$f"
			else
			echo "$0: sourcing perl script: $f"
			perl "$f"
			fi
			;;
    	*.py)
			if [ -x "$f" ]; then
			echo "$0: running python script: $f"
			"$f"
			else
			echo "$0: sourcing python script: $f"
			python3 "$f"
			fi
			;;
		*)        echo "$0: ignoring $f" ;;
		esac
		echo
done

# If we actually get here, it's because there was no 99_start.sh in the above
# list of scripts
echo "Shutting down in 10 secs!"
sleep 120
