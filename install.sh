#!/usr/bin/env bash
# Kept so old links and old notes still work. Everything moved into setup.sh,
# which is one command for install, update and repair on macOS and Linux.
exec "$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/setup.sh" "$@"
