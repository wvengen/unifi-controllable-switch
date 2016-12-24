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
  if grep -q "^$key=" "$file"; then
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

# perform an inform request
# cannot use wget because busybox misses --post-file
inform_request() {
  url="$1"
  key="$2"
  mac=`echo "$3" | sed 's/://g'`

  hostport=`echo "$url" | sed 's/^\w\+:\/\///;s/\/.*$//'`
  host=`echo "$hostport" | sed 's/:.*$//'`
  port=`echo "$hostport" | sed 's/^.*://'`
  [ -z "$port" ] && port=80

  TMP=`mktemp -t unifi-inform-send.XXXXXXXXXX`
  "$ROOT"/unifi-inform-data enc "$key" "$mac" >"$TMP"

  (
    echo "POST $url HTTP/1.0\r"
    echo "Host: $hostport\r"
    echo "Accept: application/x-binary\r"
    echo "Content-Type: application/x-binary\r"
    echo "Content-Length: `wc -c "$TMP" | awk '{print $1}'`\r"
    echo "\r"
    cat "$TMP"
  ) | nc "$host" "$port" | (
    while IFS= read -r line; do [ ${#line} -eq 1 ] && break; done
    "$ROOT"/unifi-inform-data dec "$key"
  )

  rm -f "$TMP"
}

