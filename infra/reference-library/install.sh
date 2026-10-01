#!/bin/sh
# Install the reference library's systemd user units and the app shortcut, then
# start listening on the socket. Safe to run again; it overwrites the copies.
set -eu

here="$(cd "$(dirname "$0")" && pwd)"
config="${XDG_CONFIG_HOME:-${HOME}/.config}"
units="${config}/systemd/user"
applications="${XDG_DATA_HOME:-${HOME}/.local/share}/applications"

install -d "${units}" "${config}/reference-library" "${applications}"
install -m 644 "${here}/reference-library.socket" "${here}/reference-library.service" \
  "${here}/reference-library-app.service" "${here}/reference-library-gateway.service" "${units}/"
install -m 644 "${here}/reference-library.caddyfile" "${config}/reference-library/"
# The shortcut keeps the app's own desktop-file name so it replaces the
# package's entry for this user.
install -m 644 "${here}/reference-library-app.desktop" "${applications}/zotero.desktop"

systemctl --user daemon-reload
systemctl --user enable --now reference-library.socket
