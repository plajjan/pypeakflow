import logging
import sys
import os
import re
import urllib

from peakflow_soap import ConnectionOptions, PeakflowSOAP

class MoMatch:
    """ Match
    """

class MoMatchAsPath(MoMatch):
    def __init__(self):
        self.aspath = None

    @classmethod
    def from_value(cls, aspath_string=None):
        match = MoMatchAsPath()
        if aspath_string:
            match.aspath = urllib.unquote(aspath_string)
        return match

    def __repr__(self):
        return "AS Path Regexp: %s" % self.aspath


class MoMatchCidrBlocks(MoMatch):
    def __init__(self):
        self.prefix = []

    @classmethod
    def from_value(cls, prefix_string=None):
        match = MoMatchCidrBlocks()
        if prefix_string:
            match.prefix = list(set(prefix_string.split(',')))
        return match

    def __repr__(self):
        res = "CIDR blocks:\n"
        for prefix in sorted(self.prefix):
            res += "    %s\n" % prefix
        return res


class MoMatchCidrV6Blocks(MoMatch):
    def __init__(self):
        self.prefix = []

    @classmethod
    def from_value(cls, prefix_string=None):
        match = MoMatchCidrV6Blocks()
        if prefix_string:
            match.prefix = list(set(prefix_string.split(',')))
        return match

    def __repr__(self):
        res = "CIDRv6 blocks:\n"
        for prefix in sorted(self.prefix):
            res += "    %s\n" % prefix
        return res




class MoMatchPeerAs(MoMatch):
    def __init__(self):
        self.peer_as = []

    @classmethod
    def from_value(cls, peer_as_string=None):
        match = MoMatchPeerAs()
        if peer_as_string:
            match.peer_as = peer_as_string
        return match

    def __repr__(self):
        return "Peer AS: %s" % self.peer_as

    def get_conf(self):
        return "peer_as %s" % self.peer_as


class ManagedObject:
    """ Manged Object
    """

    def __init__(self):
        self.config_lines = []
        self.name = None
        self.description = None
        self.family = None
        self.tags = {}
        self.match = None

    def __repr__(self):
        return "%s" % self.name

    @classmethod
    def from_peakflow(cls, co):
        """
        """
        pf = PeakflowSOAP(co)
        config = pf.cliRun("config show")
        mos = cls.from_conf(config['results'])
        for mo in mos:
            mo.co = co
        return mos

    @classmethod
    def from_conf(cls, config):
        """ Read managed objects from config and return a list of objects
            representing managed objects on the Peakflow platform.
        """
        mos = []
        raw_mos = {}
        for line in config.splitlines():
            m = re.match('services sp managed_objects (add(_with_parent)?|edit) "(?P<name>[^"]+)"', line)
            if m is not None:
                name = m.group('name').split('|')[-1]
                if name not in raw_mos:
                    raw_mos[name] = []
                raw_mos[name].append(line)

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
            # store a verbatim copy of the configuration lines that pertain to
            # this MO
            mo.config_lines.append(line)

            # name
            m = re.match('services sp managed_objects add(_with_parent)? "(?P<name>[^"]+)"', line)
            if m is not None:
                mo.name = m.group('name').split('|')[-1]

            # description
            m = re.match('services sp managed_objects edit "([^"]+)" description set "(?P<description>[^"]+)"', line)
            if m is not None:
                mo.description = m.group('description')

            # family
            m = re.match('services sp managed_objects edit "([^"]+)" family set ([^ $]+)', line)
            if m is not None:
                mo.family = m.group(2)

            # tag
            m = re.match('services sp managed_objects edit "([^"]+)" tags add "([^"]+)"', line)
            if m is not None:
                mo.tags[m.group(2)] = None

            # match
            m = re.match('services sp managed_objects edit "([^"]+)" match set (?P<match>[^ ]+) (?P<value>.+)', line)
            if m is not None:

                if m.group('match') == 'asregexp_uri':
                    mo.match = MoMatchAsPath.from_value(m.group('value').strip('"'))
                elif m.group('match') == 'cidr_blocks':
                    mo.match = MoMatchCidrBlocks.from_value(m.group('value'))
                elif m.group('match') == 'cidr_v6_blocks':
                    mo.match = MoMatchCidrV6Blocks.from_value(m.group('value'))
                elif m.group('match') == 'peer_as':
                    mo.match = MoMatchPeerAs.from_value(m.group('value'))
                else:
                    raise NotImplementedError("No match class for: %s" % m.group('match'))

            # misuse detection
            m = re.match('services sp managed_objects edit "([^"]+)" detection misuse (?P<match>[^ ]+) (trigger|high_severity) set (?P<value>[0-9]+)', line)
            if m is not None:
                #if m.group(
                pass

        return mo

    def save(self):
        cmds = []
        cmds.append("services sp managed_objects add \"%s\"" % self.name)
        for tag in self.tags:
            cmds.append("services sp managed_objects edit \"%s\" tags add \"%s\"" % (self.name, tag))
        cmds.append("services sp managed_objects edit \"%s\" description set \"%s\"" % (self.name, self.description))
        cmds.append("services sp managed_objects edit \"%s\" family set \"%s\"" % (self.name, self.family))
        cmds.append("services sp managed_objects edit \"%s\" match set %s" % (self.name, self.match.get_conf()))

        pf = PeakflowSOAP(self.co)
        for cmd in cmds:
            res = pf.cliRun(cmd)
        return res
            
            



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
    parser.add_option("--show", metavar='MO', help="Show detailed info on MO")
    parser.add_option("--new", action='store_true', help="test creation of new MO")
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

        if options.show:
            mo = None
            for mo_name in mos:
                if mo_name.name == options.show:
                    mo = mo_name

            print "Configuration:"
            for line in mo.config_lines:
                print line
            print "%-14s : %s" % ('Name', mo.name)
            print "%-14s : %s" % ('Family', mo.family)
            print "%-14s : %s" % ('Description', mo.description)
            print "%-14s : %s" % ('Tags', [key for key in mo.tags])
            print "Match", mo.match
