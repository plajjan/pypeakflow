""" Talk to Arbor Peakflow SP via SOAP
"""

import logging
import sys

import peakflow_suds
import peakflow_zsi

class ConnectionOptions:
    """ ConnectionOptions just carries some information like host to connect to,
        user, pass and so forth
    """
    def __init__(self, host=None, username=None, password=None, port=None):
        self.host = host
        self.port = port
        self.username = username
        self.password = password


class PeakflowSOAP:
    """ Client library for talking to Arbor Peakflow SP via SOAP
    """


    def __init__(self, con_opts):

        self.suds = peakflow_suds.PeakflowSuds(con_opts)
        self.zsi = peakflow_zsi.PeakflowZsi(con_opts)
        self._timeout = 10



    def cliRun(self, command):
        """ Run a command
        """
        return self.zsi.cliRun(command = command)


    def commit(self, comment=None):
        return self.zsi.cliRun(command = 'config write')


    def getTrafficGraph(self, query, graph_configuration):
        return self.suds.getTrafficGraph(query = query, graph_configuration = graph_configuration)


    def runXmlQuery(self, query, output_format = 'xml'):
        return self.suds.runXmlQuery(query = query, output_format = output_format)

    def getDosAlertSummariesXML(self, alert_id):
        return self.suds.getDosAlertSummariesXML(alert_id)

    def getDosAlertDetailsXML(self, alert_id):
        return self.suds.getDosAlertDetailsXML(alert_id)

    def getDosAlertGraph(self, alert_id, width, height):
        return self.suds.getDosAlertGraph(alertID = alert_id, width = width, height = height)

    def getMitigationSummariesXML(self, filter = '', max_count = 1000):
        return self.suds.getMitigationSummariesXML(filter = filter, max_count = max_count)






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

    co = ConnectionOptions(options.host, options.username, options.password)
    pf = PeakflowSOAP(co)

    if options.cli_run:
        print pf.cliRun(options.cli_run)

