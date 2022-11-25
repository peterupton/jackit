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

    parser = argparse.ArgumentParser(
        prog="JackItImproved",
        description="An implementation of the MouseJack vulnerability packaged in an easy to use tool."
    )

    parser.add_argument('-v', '--verbose', action='store_true')
    parser.add_argument('object')
    parser.add_argument('action')

    args = parser.parse_args()
    logger = logging.getLogger(__name__)
    if args.verbose:
        logger.setLevel(logging.DEBUG)

    logging.debug("verbose mode enabled")

    if args.object == 'dongle':
        if args.action == 'list':
            dongles_list = dongle.Dongle.list()
            if len(dongles_list) == 0:
                print("No dongles found, please check your devices.")
                return
            if len(dongles_list) == 1:
                print("Found " + str(len(dongles_list)) + " dongle.")
            else:
                print("Found " + str(len(dongles_list)) + " dongles.")

            for dongle_i in dongles_list:
                print(dongle_i.product + ". serial number:", dongle_i.serial_number)
                logger.debug("Device details:")
                logger.debug(dongle_i)


    # example usage drafts:
    # jim dongle flash nrf
    # jim dongle list
    # jim dongle info
    # jim dongle flash default
    # jim dongle backup
    # jim dongle reset
    # jim exploit recon
    # jim capture


if __name__ == "__main__":
    cli()
