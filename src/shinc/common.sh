#
# UniFi controllable switch - common functions
#

[ -z "$ROOT" ] && echo "Set ROOT before sourcing common.sh" 1>&2

if [ -e /var/etc/persistent ]; then
  DEVEL=
  CFG_DIR=/var/etc/persistent/cfg
else
  # it looks like we're running in-tree for development
  DEVEL=1
  CFG_DIR="$ROOT"/../cfg
fi

export ROOT DEVEL CFG_DIR

# return a variable from a configuration file
cfg_get() {
  file="$CFG_DIR/$1"
  key=`echo "$2" | sed 's/\./\\\\./g'`
  sed "s/^$key=//p;d" "$file" 2>/dev/null
}

# set a configuration variable
cfg_set() {
  file="$CFG_DIR/$1"
  key="$2"
  value="$3"

  mkdir -p "$CFG_DIR"
  if grep -q "^$key=" "$file" 2>/dev/null; then
     sed -i "s/^\($key=\).*$/\1$value/" "$file"
  else
     echo "$key=$value" >>"$file"
  fi
}

# return first mac address found in system
find_system_mac() {
  ifconfig | sed 's/^.*\(ether\|HWaddr\) \([0-9a-fA-F:]\+\).*$/\2/p;d' | head -n 1
}

# return mac address from configuration or system
get_mac() {
  cfg_get dev mac || find_system_mac
}

# return model id recognized by UniFi
get_model_id() {
  if grep -q '^board.portnumber=5$' /etc/board.info 2>/dev/null; then
    echo -n 'US8P60'
  else
    echo -n 'US8P150'
  fi
}

# run JSON.sh
JSONsh() {
  "$ROOT"/shinc/JSON.sh
}
# workaround for https://github.com/dominictarr/JSON.sh/issues/50
[ -x "$ROOT"/egrep ] && PATH="$ROOT:$PATH" && export PATH

# perform an inform request
# use netcat instead of wget, because busybox misses wget's --post-file argument
inform_request() {
  url="$1"
  key="$2"
  mac=`echo "$3" | sed 's/://g'`

  hostport=`echo "$url" | sed 's/^\w\+:\/\///;s/\/.*$//'`
  host=`echo "$hostport" | sed 's/:.*$//'`
  port=`echo "$hostport" | sed 's/^.*://'`
  [ -z "$port" ] && port=80

  TMP1=`mktemp -t unifi-inform-send-in.XXXXXXXXXX`
  cat >"$TMP1" # encryption can't handle buffering
  TMP2=`mktemp -t unifi-inform-send-enc.XXXXXXXXXX`
  "$ROOT"/unifi-inform-data enc "$key" "$mac" <"$TMP1" >"$TMP2"

  (
    printf "POST %s HTTP/1.0\r\n" "$url"
    printf "Host: %s%s\r\n" "$hostport"
    printf "Accept: application/x-binary\r\n"
    printf "Content-Type: application/x-binary\r\n"
    printf "Content-Length: %d\r\n" `wc -c "$TMP2" | awk '{print $1}'`
    printf "\r\n"
    cat "$TMP2"
  ) | nc "$host" "$port" | (
    while IFS= read -r line; do [ ${#line} -eq 1 ] && break; done
    "$ROOT"/unifi-inform-data dec "$key"
  )

  rm -f "$TMP1" "$TMP2"
}

# send a broadcast packet
# busybox's netcat does not support this, so it was added to unifi-inform-data
broadcast() {
  "$ROOT"/unifi-inform-data bcast
}

