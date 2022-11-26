#!/usr/bin/env python3
""" main file for JackIt Improved """

# file globals:
__version__ = 0.1

import argparse
import logging
import dongle


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


def cli():
    """
    initial entry point in CLI mode
    """

    logging.basicConfig(level=logging.INFO)

    parser = argparse.ArgumentParser(
        prog="JackItImproved",
        description="An implementation of the MouseJack vulnerability packaged in an easy to use tool."
    )

    parser.add_argument('-d', '--device', help="the serial number of the dongle to use", default=None)
    parser.add_argument('object', help="one of 'dongle'")
    parser.add_argument('action', help="dongle list, dongle info, dongle flash")

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
            raise Exception("Unrecognized Action")

    # example usage drafts:
    # jim dongle flash nrf
    # jim dongle flash default
    # jim dongle backup
    # jim dongle reset
    # jim exploit recon
    # jim capture


if __name__ == "__main__":
    cli()
