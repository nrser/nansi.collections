#!/usr/bin/env bash

function .sysd.logs.invocation {
  local unit
  local invocation_id
  local args=()
  
  for arg in $@; do
    case $arg in
      -h|--help)
        cat << END >&2
View systemd logs for a unit *only* since it was last started.

Usage:
    .sysd.logs.invocation [OPTIONS] UNIT

Options:
    -h, --help  Where you are now.
    *           Passed to `journalctl`.

Example:
    .sysd.logs.invocation -xe grafana

END
        return 1
      ;;
      
      *)
        args+=("${arg}")
      ;;
    esac
  done
  
  if [[ "${#args[@]}" == 0 ]]; then
    (>&2 echo "ERROR: At least UNIT arg required, see --help")
    return 1
  fi
  
  unit="${args[-1]}"
  unset args[-1]
  
  invocation_id="$(systemctl show --value -p InvocationID "$unit")"
  
  journalctl _SYSTEMD_INVOCATION_ID="$invocation_id" "${args[@]}"
}

if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
  .sysd.logs.invocation "$@"
fi
