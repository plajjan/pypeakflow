from datetime import datetime
import logging
import sys
import os
import re
from peakflow_soap import PeakflowSOAP 

from lxml import objectify

import urllib2

wsdl_url = 'file://%s/PeakflowSP.wsdl' % os.getcwd()
soap_url = "https://peakflow.tele2.net/soap/sp"

def num_normalise(number):
    prefix = ['', 'K', 'M', 'G', 'T', 'P', 'E']
    order = 0
    try:
        while True:
            if float(number) < 1000:
                break
            number = float(number) / 1000
            order += 1

        return "%.1f%s" % (number, prefix[order])
    except:
        return "N/A"

class Alert:
    def __init__(self):
        self.direction = None
        self.type = None
        self.protocol = None
        self.protocol_number = None
        self.destination = None
        self.target_mo = None
        self.target_mo_id = None
        self.sources = []
        self.impact_bps = None
        self.impact_pps = None
        self.threshold = None
        self.threshold_unit = None
        self.attack_start = None
        self.attack_stop = None
        self.ongoing = None
        self.duration = None
        self.mitigation_name = None
        self.mitigation_start = None
        self.mitigation_stop = None

    def get_current_status(self):
        """ Return a human readable string about current state of attack
        """
        impact = ''
        if self.impact_pps or self.impact_bps:
            impact = 'Impact '
        if self.impact_pps:
            impact += "%spps" % num_normalise(self.impact_pps)
        if self.impact_bps:
            if self.impact_pps:
                impact += " / "
            impact += "%sbps" % num_normalise(self.impact_bps)

        mitigation = ''
        if self.mitigation_start:
            if self.mitigation_stop:
                mitigation = 'Mitigation started at %s and ended at %s' % (self.mitigation_start, self.mitigation_stop)
            else:
                mitigation = 'Mitigation started at %s' % self.mitigation_start

        if not self.attack_stop:
            # attack has started
            res = """%(direction)s %(type)s attack towards %(destination)s (%(target_mo)s). Attack started at %(attack_start)s. %(impact)s Crossed threshold of %(threshold)s%(threshold_unit)s.""" % {
                    'direction': self.direction,
                    'type': self.type,
                    'destination': self.destination,
                    'target_mo': self.target_mo,
                    'impact': impact,
                    'threshold': num_normalise(self.threshold),
                    'threshold_unit': self.threshold_unit,
                    'attack_start': self.attack_start,
                    'attack_stop': self.attack_stop
                    }
        else:
            # attack has stopped
            res = """%(direction)s %(type)s attack towards %(destination)s (%(target_mo)s) has ended. Attack started at %(attack_start)s and finished at %(attack_stop)s. %(impact)s. Crossed threshold of %(threshold)s%(threshold_unit)s. %(mitigation)s.""" % {
                    'direction': self.direction,
                    'type': self.type,
                    'destination': self.destination,
                    'target_mo': self.target_mo,
                    'impact': impact,
                    'mitigation': mitigation,
                    'threshold': num_normalise(self.threshold),
                    'threshold_unit': self.threshold_unit,
                    'attack_start': self.attack_start,
                    'attack_stop': self.attack_stop
                    }

#            res += "towards has ended at %(attack_stop)s
#            res += "that started at %(attack_start)s and towards %(destination)s (%(target_mo)s) of %(impact_bps)sbps and %(impact_pps)spps, crossing threshold of %(threshold)s%(threshold_unit)s.""" % {
#                    'direction': self.direction,
#                    'type': self.type,
#                    'destination': self.destination,
#                    'target_mo': self.target_mo,
#                    'impact_bps': num_normalise(self.impact_bps),
#                    'impact_pps': num_normalise(self.impact_pps),
#                    'threshold': num_normalise(self.threshold),
#                    'threshold_unit': self.threshold_unit,
#                    'attack_start': self.attack_start
#                    }

        return res

    def __str__(self):
        r =  "Type             : %s\n" % self.type
        r += "Direction        : %s\n" % self.direction
        r += "Protocol         : %s (%s)\n" % (self.protocol, self.protocol_number)
        r += "Impact bps       : %sbps\n" % num_normalise(self.impact_bps)
        r += "Impact pps       : %spps\n" % num_normalise(self.impact_pps)
        r += "Threshold        : %s%s\n" % (num_normalise(self.threshold), self.threshold_unit)
        r += "Destination IP   : %s\n" % self.destination
        r += "Target MO        : %s\n" % self.target_mo
        r += "Attack start     : %s\n" % self.attack_start
        r += "Attack stop      : %s\n" % self.attack_stop
        r += "Ongoing          : %s\n" % self.ongoing
        r += "Duration         : %s\n" % self.duration
        r += "Mitigation name  : %s\n" % self.mitigation_name
        r += "Mitigation start : %s\n" % self.mitigation_start
        r += "Mitigation stop  : %s\n" % self.mitigation_stop
        # A CIDR block that was a significant contributor in an attack
        st = "Sources"
        for source in self.sources:
            r += "%s          : %s\n" % (st, source)
            st = "       "

        return r



    @classmethod
    def from_id(cls, co, alert_id):
        a = Alert()

        pf = PeakflowSOAP(co)

        # get XML from peakflow
        res = pf.getDosAlertSummariesXML(alert_id)
        # XML to python
        root = objectify.fromstring(res.encode('utf-8'))

        # extract values
        a.direction = root.alert.direction
        a.type = root.alert.get('type')
        a.destination = root.alert.resource.ip
        try:
            a.attack_start = datetime.fromtimestamp(int(root.alert.duration.get('start')))
        except:
            pass
        try:
            a.attack_stop = datetime.fromtimestamp(int(root.alert.duration.get('stop')))
        except:
            pass
        a.ongoing = bool(root.alert.duration.get('ongoing'))
        a.duration = int(root.alert.duration.get('length'))
        a.target_mo = root.alert.resource.managed_object.get('name')
        a.target_mo_id = root.alert.resource.managed_object.get('gid')
        try:
            a.protocol = root.alert.protocol
        except:
            pass
        try:
            a.impact_bps = root.alert.impact.get('bps')
        except:
            pass
        try:
            a.impact_pps = root.alert.impact.get('pps')
        except:
            pass
        a.threshold = root.alert.severity.get('threshold')
        a.threshold_unit = root.alert.severity.get('unit')

        try:
            for annotation in root.alert['annotation-list'].iterchildren():
                m = re.match("TMS mitigation '([^']+)' (started|stopped)", str(annotation.content))
                if m is not None:
                    a.mitigation_name = m.group(1)
                    if m.group(2) == 'started':
                        a.mitigation_start = datetime.fromtimestamp(int(annotation.added))
                    if m.group(2) == 'stopped':
                        a.mitigation_stop = datetime.fromtimestamp(int(annotation.added))
        except:
            pass

        res = client.service.getDosAlertDetailsXML(alert_id)
        root = objectify.fromstring(res.encode('utf-8'))
        for item in root['sample-list']:
            if item.get('name') is None:
                continue

            for prefix in item.prefixes.find('prefix'):
                if prefix.get('is_dst') == "0":
                    a.sources.append(prefix.get('cidr'))

        return a



if __name__ == '__main__':
    logger = logging.getLogger()
    log_stream = logging.StreamHandler()
    log_stream.setFormatter(logging.Formatter("%(asctime)s: %(levelname)-8s %(message)s"))
    logger.setLevel(logging.WARNING)
    logger.addHandler(log_stream)

    import optparse

    parser = optparse.OptionParser()
    parser.add_option("-H", "--host", help="host for SOAP API connection, typically the leader")
    parser.add_option("-U", "--username", help="username for SOAP API connection")
    parser.add_option("-P", "--password", help="password for SOAP API connection")
    parser.add_option("--human", action="store_true", help="Print a human readable summary of current state")
    parser.add_option("--detail", action="store_true", help="Print a details of alert")
    (options, args) = parser.parse_args()

    co = peakflow_soap.ConnectionOptions(host=options.host,
            username=options.username, password=options.password)
#    pf = PeakflowSOAP(options.host, options.username, options.password)

    for arg in args:
        alert = Alert().from_id(arg)
        if options.human:
            print alert.get_current_status()
        if options.detail:
            print alert
