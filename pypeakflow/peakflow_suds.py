""" Talk to Arbor Peakflow SP via SOAP using the SUDS library
"""

import logging
import sys
import os
import base64
import urllib2

from lxml import objectify

from suds.client import Client
from suds.transport.https import HttpAuthenticated


class PeakflowSuds:
    """ Client library for talking to Arbor Peakflow SP via SOAP
    """

    def __init__(self, con_opts):
        wsdl_url = 'file://%s/PeakflowSP.wsdl' % os.path.dirname(__file__)
        soap_url = 'https://%s/soap/sp' % con_opts.host

        # SOAP shit
        t = HttpAuthenticated(username=con_opts.username, password=con_opts.password)
        t.handler = urllib2.HTTPDigestAuthHandler(t.pm)
        t.urlopener = urllib2.build_opener(t.handler)
        self.client = Client(url = wsdl_url, location = soap_url, transport = t)

        self._timeout = 10



    def cliRun(self, command):
        """ Run a command
        """
        return self.client.service.cliRun(command = command, timeout = self._timeout)
        #return objectify.fromstring(res.encode('utf-8'))



    def getTrafficGraph(self, query, graph_configuration):
        return self.soap.getTrafficGraph(query = query, graph_configuration = graph_configuration)


    def runXmlQuery(self, query, output_format = 'xml'):
        return self.soap.runXmlQuery(query = query, output_format = output_format)

    def getDosAlertSummariesXML(self, alert_id):
        print "AlertID:", alert_id
        return self.client.service.getDosAlertSummariesXML(alertID = alert_id)

    def getDosAlertDetailsXML(self, alert_id):
        return self.soap.getDosAlertDetailsXML(alertID = alert_id)

    def getDosAlertGraph(self, alert_id, width, height):
        return self.soap.getDosAlertGraph(alertID = alert_id, width = width, height = height)

    def getMitigationSummariesXML(self, filter = '', max_count = 1000):
        return self.soap.getMitigationSummariesXML(filter = filter, max_count = max_count)






if __name__ == '__main__':
    logger = logging.getLogger()
    log_stream = logging.StreamHandler()
    log_stream.setFormatter(logging.Formatter("%(asctime)s: %(levelname)-8s %(message)s"))
    logger.setLevel(logging.DEBUG)
    logger.addHandler(log_stream)

    import optparse

    parser = optparse.OptionParser()
    parser.add_option("-H", "--host", help="host for SOAP API connection, typically the leader")
    parser.add_option("-U", "--username", help="username for SOAP API connection")
    parser.add_option("-P", "--password", help="password for SOAP API connection")
    parser.add_option("--cli-run", help="Run a command on the Peakflow system")
    (options, args) = parser.parse_args()

    if not options.host:
        print >> sys.stderr, "Please specify a remote host for SOAP API connection."
        sys.exit(1)

    if not options.username:
        print >> sys.stderr, "Please specify a username to be used for the SOAP API connection."
        sys.exit(1)

    if not options.password:
        print >> sys.stderr, "Please specify a password to be used for the SOAP API connection."
        sys.exit(1)

    pf = PeakflowSOAP(options.host, options.username, options.password)

    if options.cli_run:
        print pf.cliRun(options.cli_run)
