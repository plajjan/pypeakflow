import logging
import sys
import os
import re
import textwrap
import urllib

from peakflow_soap import ConnectionOptions, PeakflowSOAP

class InterfaceRule:
    """ Auto-Configuration Rule 
    """

    def __init__(self):
        self.config_lines = []
        self.name = None
        self.description = None
        self.precedence = None

        self.match_routers = []
        self.match_intf_subnet = None
        self.match_intf_desc_regex = None

        self.action_type = False
        self.action_set_type = None
        self.action_asns = False
        self.action_set_asn = None
        # simple, backbone, MO-facing
        self.action_set_mo_type = None
        self.action_set_mo_direction = None
        self.action_set_mos = []
        self.action_high_threshold = None
        self.action_low_threshold = None


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
            representing the auto configuration interfaces rules on the Peakflow
            platform.
        """
        intf_rules = []
        raw_intf_rules = {}
        for line in config.splitlines():
            m = re.match('services sp auto-config interface rules (add|edit) "([^"]+)"', line)
            if m is not None:
                if m.group(2) not in raw_intf_rules:
                    raw_intf_rules[m.group(2)] = []
                raw_intf_rules[m.group(2)].append(line)

        for name in raw_intf_rules:
            intf_rules.append(InterfaceRule.from_lines(raw_intf_rules[name]))

        return intf_rules



    @classmethod
    def from_lines(cls, lines):
        """ Create an auto config interface rule from a set of configuration lines

            Returns one InterfaceRule representing a auto config interface rule on the
            Peakflow platform.
        """
        ir = InterfaceRule()
        for line in lines:
            # store a verbatim copy of the configuration lines that pertain to
            # this interface rule
            ir.config_lines.append(line)

            # name
            m = re.match('services sp auto-config interface rules add "([^"]+)"', line)
            if m is not None:
                ir.name = m.group(1)

            # precedence
            m = re.match('services sp auto-config interface rules edit "([^"]+)" precedence set ([0-9]+)', line)
            if m is not None:
                ir.precedence = m.group(2)

            # description
            m = re.match('services sp auto-config interface rules edit "([^"]+)" description set "([^"]+)"', line)
            if m is not None:
                ir.description = m.group(2)

            # match / regexp_uri
            m = re.match('services sp auto-config interface rules edit "([^"]+)" regexp_uri set (.+)$', line)
            if m is not None:
                ir.regexp_uri = m.group(2)

            # action / action type enable
            m = re.match('services sp auto-config interface rules edit "([^"]+)" action type (.+)$', line)
            if m is not None:
                ir.action_type = bool(m.group(2))

            # action / set type
            m = re.match('services sp auto-config interface rules edit "([^"]+)" type set (.+)$', line)
            if m is not None:
                ir.action_set_type = m.group(2)

            # action / action asn enable
            m = re.match('services sp auto-config interface rules edit "([^"]+)" action asns (.+)$', line)
            if m is not None:
                ir.action_asns = bool(m.group(2))

            # action / peer ASN
            m = re.match('services sp auto-config interface rules edit "([^"]+)" peers set (.+)$', line)
            if m is not None:
                ir.action_set_asn = int(m.group(2))

            # mo type... simple / backbone / managed_object
            m = re.match('services sp auto-config interface rules edit "([^"]+)" managed_objects type set (.+)$', line)
            if m is not None:
                ir.action_set_mo_type = m.group(2)

            # mos
            m = re.match('services sp auto-config interface rules edit "([^"]+)" managed_objects add "([^"]+)"', line)
            if m is not None:
                ir.action_set_mos.append(m.group(2))

        return ir


    def save(self):
        cmds = []
        cmds.append("services sp auto-config interface rules add \"%s\"" % self.name)
        cmds.append("services sp auto-config interface rules edit \"%s\" precedence set %s" % (self.name, self.precedence))

        if self.action_type:
            cmds.append("services sp auto-config interface rules edit \"%s\" action type enable" % self.name)
            cmds.append("services sp auto-config interface rules edit \"%s\" type set %s" % (self.name, self.action_set_type))
        else:
            cmds.append("services sp auto-config interface rules edit \"%s\" action type disable" % self.name)

        if self.action_asns:
            cmds.append("services sp auto-config interface rules edit \"%s\" action asns enable" % self.name)
            cmds.append("services sp auto-config interface rules edit \"%s\" peers set %s" % (self.name, self.action_set_asn))
        else:
            cmds.append("services sp auto-config interface rules edit \"%s\" action asns disable" % self.name)

        if self.action_set_mo:
            cmds.append("services sp auto-config interface rules edit \"%s\" action managed_objects enable" % self.name)
            cmds.append("services sp auto-config interface rules edit \"%s\" managed_objects type set %s" % (self.name, self.action_set_mo_type))
            for mo in self.action_set_mos:
                cmds.append("services sp auto-config interface rules edit \"%s\" managed_objects add \"%s\"" % (self.name, mo))
        else:
            cmds.append("services sp auto-config interface rules edit \"%s\" managed_objects clear" % self.name)

        cmds.append("services sp auto-config interface rules edit \"%s\" regexp set \"%s\"" % (self.name, self.match_intf_desc_regex))

        pf = PeakflowSOAP(self.co)
        for cmd in cmds:
            res = pf.cliRun(cmd)
        return res

class IntfRuleList(list):
    """ Class that will emulate a normal list but is ordered by precedence of
        elements it holds
    """


if __name__ == '__main__':
    logger = logging.getLogger()
    log_stream = logging.StreamHandler()
    log_stream.setFormatter(logging.Formatter("%(asctime)s: %(levelname)-8s %(message)s"))
    logger.setLevel(logging.DEBUG)
    logger.addHandler(log_stream)

    import optparse

    parser = optparse.OptionParser()
    parser.add_option("--test-slurp", help="test to slurp config FILE")
    parser.add_option("--list", action="store_true", help="list rules")
    (options, args) = parser.parse_args()

    if options.test_slurp:
        f = open(options.test_slurp)
        intf_rules = InterfaceRule.from_conf(f.read())
        f.close()
        if options.list:
            for rule in intf_rules:
                print ""
                print "--", rule.name, "-"*(72-len(rule.name))
                print textwrap.fill(rule.description or '', 72)
                print "     Precedence  :", rule.precedence
                print "  -- Match --"
                print "     Routers  :", rule.match_routers
                print "     IF Subnet:", rule.match_intf_subnet
                print "     IF Descr :", rule.match_intf_desc_regex
                print "  -- Actions --"
                print "     Type     :", rule.action_set_type, "(" + str(rule.action_type) + ")"
                print "     ASNs     :", rule.action_set_asn, "(" + str(rule.action_asns) + ")"
                print "     MOs      :", str(rule.action_set_mo_type), str(rule.action_set_mos)
                print "  -- Raw configuration --"
                for line in rule.config_lines:
                    print "    %s" % line


