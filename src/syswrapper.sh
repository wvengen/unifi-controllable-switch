#!/bin/sh
#
# UniFi controllable switch - syswrapper script
#
# This script is meant to be installed in /usr/bin/syswrapper.sh
# The UniFi controller SSHs into the device and runs this on adoption
# and some other occasions.
#

ROOT=`dirname "$0"`
. "$ROOT"/shinc/common.sh

case "$1" in
set-adopt)
  [ "$2" ] && cfg_set _cfg inform_url  "$2"
  [ "$3" ] && cfg_set _cfg authkey "$3"
  # then call inform twice (adoption and association)
  "$ROOT"/unifi-inform-status |
    "$ROOT"/unifi-inform-send "$2" "$3" |
    "$ROOT"/unifi-inform-process
  "$ROOT"/unifi-inform-status |
    "$ROOT"/unifi-inform-send "$2" "$3" |
    "$ROOT"/unifi-inform-process
  ;;
*)
  echo "Usage: $0 set-adopt <inform_url> <authkey>"
  return 1
  ;;
esac

