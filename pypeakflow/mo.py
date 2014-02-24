import logging
import sys
import os
import re

from peakflow_soap import ConnectionOptions, PeakflowSOAP


class ManagedObject:
    """ Manged Object
    """

    def __init__(self):
        self.name = None
        self.family = None
        self.tags = {}
        self.match_peer_as = None

    def __repr__(self):
        return "%s" % self.name

    @classmethod
    def from_peakflow(cls, co):
        """
        """
        pf = PeakflowSOAP(co)
        config = pf.cliRun("config show")
        return cls.from_conf(config['results'])

    @classmethod
    def from_conf(cls, config):
        """ Read managed objects from config and return a list of objects
            representing managed objects on the Peakflow platform.
        """
        mos = []
        raw_mos = {}
        for line in config.splitlines():
            m = re.match('services sp managed_objects (add|edit) "([^"]+)"', line)
            if m is not None:
                if m.group(2) not in raw_mos:
                    raw_mos[m.group(2)] = []
                raw_mos[m.group(2)].append(line)

        for name in raw_mos:
            mos.append(ManagedObject.from_lines(raw_mos[name]))

        return mos



    @classmethod
    def from_lines(cls, lines):
        """ Create a Managed Object from a set of configuration lines

            Returns one ManagedObject representing a Managed Object on the
            Peakflow platform.
        """
        mo = ManagedObject()
        for line in lines:
            # name
            m = re.match('services sp managed_objects add "([^"]+)"', line)
            if m is not None:
                mo.name = m.group(1)

            # family
            m = re.match('services sp managed_objects edit "([^"]+)" family set "([^"]+)"', line)
            if m is not None:
                mo.family = m.group(2)

            # peer_as
            m = re.match('services sp managed_objects edit "([^"]+)" match set peer_as ([0-9]+)', line)
            if m is not None:
                mo.match_peer_as = int(m.group(2))

            # tag
            m = re.match('services sp managed_objects edit "([^"]+)" tags add "([^"]+)"', line)
            if m is not None:
                mo.tags[m.group(2)] = None

        return mo

            
            



if __name__ == '__main__':
    logger = logging.getLogger()
    log_stream = logging.StreamHandler()
    log_stream.setFormatter(logging.Formatter("%(asctime)s: %(levelname)-8s %(message)s"))
    logger.setLevel(logging.INFO)
    logger.addHandler(log_stream)

    import optparse

    parser = optparse.OptionParser()
    parser.add_option("-H", "--host", help="host for SOAP API connection, typically the leader")
    parser.add_option("-U", "--username", help="username for SOAP API connection")
    parser.add_option("-P", "--password", help="password for SOAP API connection")
    parser.add_option("--test-slurp", help="test to slurp config FILE")
    parser.add_option("--list", action='store_true', help="list MOs")
    (options, args) = parser.parse_args()

    co = ConnectionOptions(options.host, options.username, options.password)

    if options.list:
        for mo in ManagedObject.from_peakflow(co):
            print mo.name


    if options.test_slurp:
        f = open(options.test_slurp)
        mos = ManagedObject.from_conf(f.read())
        f.close()
        for mo in mos:
            tags = []
            for tag in mo.tags:
                tags.append(tag)
            print mo.name, tags, mo.match_peer_as

