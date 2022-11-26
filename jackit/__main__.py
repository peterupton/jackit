#!/usr/bin/env python3
""" main file for JackIt Improved """

# file globals:
__version__ = 0.1

import argparse
import logging
import sys
import string
from typing import Union

import dongle
import attack


def banner():
    """
    print the banner
    """

    print(r"""
     ____.              __   .___  __
    |    |____    ____ |  | _|   |/  |_
    |    \__  \ _/ ___\|  |/ /   \   __\
/\__|    |/ __ \\  \___|    <|   ||  |
\________(____  /\___  >__|_ \___||__| (Improved)
              \/     \/     \/          """)

    print("JackIt Improved Version %0.2f" % __version__)
    print("")


def unrecognized_action(action):
    """
    quits with a message about an unrecognized action
    """
    logging.error("unrecognized action: " + action)
    sys.exit(1)


def print_scan_output(channel_index, address, payload):
    """
    prints the scan output
    """
    print("channel:", channel_index, "address:", attack.Attack.to_display(address), "payload:",
          attack.Attack.to_display(payload))


def address_from_string(address_string: Union[string, None]):
    """
    get the address as bytes from string
    """
    if address_string == "" or address_string is None:
        return None
    return [int(b, 16) for b in address_string.split(':')][::-1]


def cli():
    """
    initial entry point in CLI mode
    """

    logging.basicConfig(level=logging.INFO)

    parser = argparse.ArgumentParser(
        prog="JackItImproved",
        description="An implementation of the MouseJack vulnerability packaged in an easy to use tool."
    )

    parser.add_argument('-d', '--device', help="the address of the dongle to use", default=None, type=int)
    parser.add_argument('-l', '--lna', help="(attack) enable LNA (only works on CrazyRadio dongles)", type=bool)
    parser.add_argument('-w', '--wait_time',
                        help="(attack scan) how long to wait on each channel when scanning (dwell time)", default=0.01,
                        type=float)
    parser.add_argument('-a', '--address', help='(attack sniff) which address to collect data from')
    parser.add_argument('object', help="one of 'dongle', 'attack'")
    parser.add_argument('action', help="dongle (list, info, flash), attack (scan, sniff)")

    args = parser.parse_args()

    if args.object == 'dongle':
        if args.action == 'list':
            dongles_list = dongle.Dongle.list()
            if len(dongles_list) == 0:
                print("No compatible dongles found, please check your devices.")
                return
            if len(dongles_list) == 1:
                print("Found " + str(len(dongles_list)) + " dongle.")
            else:
                print("Found " + str(len(dongles_list)) + " dongles.")

            for dongle_i in dongles_list:
                print(dongle_i.product, "dongle, at address: ", dongle_i.address)

        elif args.action == "info":
            selected_dongle = dongle.Dongle(args.device)
            print(selected_dongle.dongle_device.product, "dongle, at address: ", selected_dongle.dongle_device.address)

        elif args.action == 'flash':
            selected_dongle = dongle.Dongle(args.device)
            selected_dongle.start_flash()
        else:
            unrecognized_action(args.action)

    elif args.object == "attack":
        this_attack = attack.Attack(dongle.Dongle(args.device), args.lna)
        if args.action == "scan":
            this_attack.scan(print_scan_output, dwell_time=args.wait_time)
        elif args.action == "sniff":
            this_attack.sniff(address_from_string(args.address), callback=print_sniff_output)
            logging.error("stub code")
            # todo stub
        elif args.action == "inject":
            logging.error("stub code")
            # todo stub
        else:
            unrecognized_action(args.action)

    else:
        logging.error(args.object + " is an unrecognized object")
        sys.exit(1)


if __name__ == "__main__":
    cli()
