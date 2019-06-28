#!/usr/bin/env python3

import os, argparse, serial
from struct import pack, unpack

def send(tty, args, cmd, addr, data):
    xor = cmd ^ addr ^ data
    pkt = pack("BBBB", cmd, addr, data, xor)
    if args.debug:
        print("--> %3d %3d %3d %3d" % (cmd, addr, data, xor))
    tty.write(pkt)

def receive(tty, args):
    pkt = tty.read(4)
    if len(pkt) != 4:
        raise TimeoutError()
    resp, addr, data, xor = unpack("BBBB", pkt)
    if args.debug:
        print("<-- %3d %3d %3d %3d" % (resp, addr, data, xor))
    if xor != resp ^ addr ^ data:
        raise Exception("Checksum mismatch!")
    return [resp, addr, data]

def init_chain(tty, args):
    # SETUP command
    send(tty, args, 0x1, 1, 0)

    # We rely on the timeout here so enforce it
    if tty.timeout is None:
        tty.timeout = 0.3

    while True:
        try:
            resp, addr, data = receive(tty, args)
            if resp == 254:
                print("Controller %d: Firmware version %d" % (addr, data))
            elif resp == 255:
                raise Exception("Command failed!")
        except TimeoutError:
            break
    return 0

def set_relay(tty, args):
    # SET_SINGLE command
    send(tty, args, 0x6, args.address, (1 << args.relay))
    resp, _, _ = receive(tty, args)
    if resp != 249:
        raise Exception("Command failed!")
    return 0

def clear_relay(tty, args):
    # DEL_SINGLE command
    send(tty, args, 0x7, args.address, (1 << args.relay))
    resp, _, _ = receive(tty, args)
    if resp != 248:
        raise Exception("Command failed!")
    return 0

def toggle_relay(tty, args):
    # TOGGLE command
    send(tty, args, 0x8, args.address, (1 << args.relay))
    resp, _, _ = receive(tty, args)
    if resp != 247:
        raise Exception("Command failed!")
    return 0

def port(tty, args):
    if args.set is not None:
        # SET_PORT command
        send(tty, args, 0x3, args.address, args.set)
        resp, addr, data = receive(tty, args)
        if resp != 252:
            raise Exception("Command failed!")
        return 0
    else:
        # GET_PORT command
        send(tty, args, 0x2, args.address, 0)
        resp, addr, data = receive(tty, args)
        if resp != 253:
            raise Exception("Command failed!")
        print("Port   : 0x%02X" % data)
        for i in range(0, 8):
            print("Relay %d: %s" % (i + 1, "On" if data & (1 << i) else "Off"))
        return 0

def type_relay_number(string):
    value = int(string, 0)
    if value < 1 or value > 8:
        raise argparse.ArgumentTypeError("Not a valid relay number!")
    return (value - 1)

def type_port_value(string):
    value = int(string, 0)
    if value < 0 or value > 255:
        raise argparse.ArgumentTypeError("Not a valid port value!")
    return value

def main():
    parser = argparse.ArgumentParser(
        description="Conrad Technology Centrum Relay Card"
    )
    parser.add_argument(
        "-d", "--debug", help="Enable debug output", action="store_true"
    )
    parser.add_argument(
        "-t", "--tty",
        help="""
            Serial device of relay card. May be set through the TTY environment
            variable.
        """,
        metavar="TTY",
        default=os.environ.get("TTY"),
        required=os.environ.get("TTY") is None
    )
    parser.add_argument(
        "-a", "--address",
        type=int, default=0,
        help="Device address (default: Broadcast)",
        metavar="ADDR"
    )
    parser.add_argument(
        "-T", "--timeout",
        help="Read timeout in seconds (float allowed)",
        type=float, default=None, metavar="SECONDS"
    )

    subparsers = parser.add_subparsers(
        title="command",
        description="The command to execute.",
        help="Command", metavar="command"
    )

    singlecmds = []

    subparser = subparsers.add_parser(
        "init", aliases=["i"],
        help="Initialize relay card chain"
    )
    subparser.set_defaults(func=init_chain)

    subparser = subparsers.add_parser(
        "set", aliases=["s"],
        help="Set single relay"
    )
    subparser.set_defaults(func=set_relay)
    singlecmds.append(subparser)

    subparser = subparsers.add_parser(
        "clear", aliases=["c"],
        help="Clear single relay"
    )
    subparser.set_defaults(func=clear_relay)
    singlecmds.append(subparser)

    subparser = subparsers.add_parser(
        "toggle", aliases=["t"],
        help="Toggle single relay"
    )
    subparser.set_defaults(func=toggle_relay)
    singlecmds.append(subparser)

    for p in singlecmds:
        p.add_argument(
            "relay", help="Relay number",
            type=type_relay_number, metavar="[1-8]"
        )

    subparser = subparsers.add_parser(
        "port", aliases=["p"],
        help="Get or set all relays of the port"
    )
    subparser.set_defaults(func=port)
    subparser.add_argument(
        "-s", "--set", help="Relay positions to set (ORed together)",
        type=type_port_value, metavar="[0-255]", default=None
    )

    args = parser.parse_args()
    if not hasattr(args, "func"):
        parser.error("Command is invalid.")

    tty = serial.Serial(args.tty, baudrate=19200)
    if args.timeout is not None:
        tty.timeout = args.timeout
    ret = args.func(tty, args)
    tty.close()
    return ret

if __name__ == "__main__":
    main()
