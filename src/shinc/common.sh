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
  ifconfig | sed 's/^.*\(ether\|HWaddr\) \([0-9a-f:]\+\).*$/\2/p;d' | head -n 1
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
inform_request() {
  url="$1"
  key="$2"
  mac=`echo $3 | sed 's/://g'`

  TMP=`mktemp -t unifi-inform-send.XXXXXXXXXX`

  "$ROOT"/unifi-inform-data enc "$key" "$mac" >"$TMP"
  wget -q -O- \
       -U 'unifi-inform-send' \
       --header='Accept: application/json' \
       --header='Content-Type: application/x-binary' \
       --post-file="$TMP" "$url" | \
    "$ROOT"/unifi-inform-data dec "$key"

  rm -f "$TMP"
}

