import logging
import sys
import os
import re
import textwrap


class IntfRule:
    """ Auto-Configuration Rule 
    """

    def __init__(self):
        self.name = None
        self.description = None
        self.rule_precedence = None

        self.match_routers = []
        self.match_intf_subnet = None
        self.match_intf_desc_regex = None

        self.action_type = False
        self.action_set_type = None
        self.action_asns = False
        self.action_set_asn = None
        self.action_set_mo = None
        self.action_set_mo_direction = None
        self.action_set_mos = None
        self.action_high_threshold = None
        self.action_low_threshold = None


    @classmethod
    def from_peakflow(cls):
        """
        """
        pf = pypeakflow.Peakflow()


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
            intf_rules.append(IntfRule.from_lines(raw_intf_rules[name]))

        return intf_rules



    @classmethod
    def from_lines(cls, lines):
        """ Create an auto config interface rule from a set of configuration lines

            Returns one IntfRule representing a auto config interface rule on the
            Peakflow platform.
        """
        ir = IntfRule()
        for line in lines:
            # name
            m = re.match('services sp auto-config interface rules add "([^"]+)"', line)
            if m is not None:
                ir.name = m.group(1)

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

        return ir

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
    (options, args) = parser.parse_args()

    if options.test_slurp:
        f = open(options.test_slurp)
        intf_rules = IntfRule.from_conf(f.read())
        f.close()
        for rule in intf_rules:
            print ""
            print "--", rule.name, "-"*(72-len(rule.name))
            print textwrap.fill(rule.description or '', 72)
            print "  -- Match --"
            print "     Routers  :", rule.match_routers
            print "     IF Subnet:", rule.match_intf_subnet
            print "     IF Descr :", rule.match_intf_desc_regex
            print "  -- Actions --"
            print "     Type     :", rule.action_set_type, "(" + str(rule.action_type) + ")"
            print "     ASNs     :", rule.action_set_asn, "(" + str(rule.action_asns) + ")"

