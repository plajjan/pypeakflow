""" Talk to Arbor Peakflow SP via SOAP
"""

import ZSI
from ZSI.ServiceProxy import ServiceProxy
from ZSI.auth import AUTH
import logging
import sys
import os
import base64


#
# overwrite fetch_challenge function since it's broken in ZSI
#
from ZSI.digest_auth import fetch_challenge

def new_fetch_challenge(http_header):
    """ apparently keywords Basic and Digest are not being checked 
        anywhere and decisions are being made based on authorization 
        configuration of client, so I guess you better know what you are
        doing.  Here I am requiring one or the other be specified.

            challenge Basic auth_param
            challenge Digest auth_param
    """
    m = fetch_challenge.wwwauth_header_re.match(http_header)
    if m is None:
      raise RuntimeError, 'expecting "WWW-Authenticate header [Basic,Digest]"'

    d = dict(challenge=m.groups()[0])
    m = fetch_challenge.auth_param_re.search(http_header)
    while m is not None:
        # XXX: ZSI doesn't limit the split and so if the value contains a '=' it
        #      breaks. Bloody noob mistake.
        k,v = http_header[m.start():m.end()].split('=', 1)
        d[k.lower()] = v[1:-1]
        m = fetch_challenge.auth_param_re.search(http_header, m.end())

    return d

ZSI.digest_auth.fetch_challenge = new_fetch_challenge



class PeakflowSOAP:
    """ Client library for talking to Arbor Peakflow SP via SOAP
    """

    __shared_state = {}

    def __init__(self, host = None, username = None, password = None):
        self.__dict__ = self.__shared_state

        # only do init if this is first time we are being run
        if host is None or username is None or password is None:
            return

        # ZSI init
        wsdl_url = 'file://%s/PeakflowSP.wsdl' % os.getcwd()
        soap_url = 'https://%s/soap/sp' % host

        cred = (AUTH.httpdigest, username, password)
        self.soap = ServiceProxy(wsdl = wsdl_url, url = soap_url, auth = cred)
        self._timeout = 10



    def cliRun(self, command):
        """ Run a command
        """
        return self.soap.cliRun(command = command, timeout = self._timeout)



    def getTrafficGraph(self, query, graph_configuration):
        return self.soap.getTrafficGraph(query = query, graph_configuration = graph_configuration)


    def runXmlQuery(self, query, output_format = 'xml'):
        return self.soap.runXmlQuery(query = query, output_format = output_format)

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
