# Conrad Technology Centrum Relay Card tool

This is a Python tool for controlling CTC [197720][1] and [197730][2] relay
cards. There are commands for controlling single relays (`set`, `clear` and
`toggle`) and the `port` command to read or set all at once.

Chaining boards is supported but not tested. You should issue the `init`
command to trigger automatic address configuration and use the `--address` to
send follow-up to a specific board.

Please see `./ctc-relay.py --help` and `./ctc-relay.py $command --help` for
details.

This project is not affiliated with the Conrad Technology Centrum.

[1]: https://www.conrad.de/de/p/conrad-components-197720-relaiskarte-baustein-12-v-dc-24-v-dc-197720.html
[2]: https://www.conrad.de/de/p/conrad-components-197730-relaiskarte-baustein-12-v-dc-197730.html
