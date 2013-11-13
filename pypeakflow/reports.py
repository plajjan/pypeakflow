import logging
import sys
import os
import re
from peakflow_soap import PeakflowSOAP 


class Report:
    def __init__(self):
        self.pf = PeakflowSOAP()

    def get_graph(self, output_filename, mo_type, mo_id, title = None, filter2 = None, filter2_binby = 1):
        query_filter = ""
        if filter2:
            query_filter = """<filter type="%s" binby="%s"/>""" % (filter2, filter2_binby)

        query = """
            <peakflow version="1.0">
                <query id="query1" type="traffic">
                    <time start_ascii="24 hours ago" end_ascii="now"/>
                    <unit type="bps"/>
                    <search limit="100" timeout="30"/>
                    <class>in</class>
                    <class>out</class>
                    <filter type="%(mo_type)s">
                        <instance value="%(mo_type_id)s"/>
                    </filter>
                    %(filter2)s
                </query>
            </peakflow>
        """ % {
                'mo_type': mo_type,
                'mo_type_id': mo_id,
                'filter2': query_filter
                }

        gc = """<?xml version="1.0" encoding="utf-8"?>
            <peakflow version="2.0">
            <graph id="graph1">
            <title>%(title)s</title>
            <ylabel>bps</ylabel>
            <width>800</width>
            <height>300</height>
            <legend>1</legend>
            </graph>
            </peakflow>
            """ % {
                    'title': title
                    }

        res = self.pf.getTrafficGraph(query, gc)

        f = open(output_filename, "w")
        f.write(res['graph'])
        f.close()


    def get_table(self, output_filename, mo_type, mo_id, title = None, filter2 = None, filter2_binby = 1):
        """
        """
        query_filter = ""
        if filter2:
            query_filter = """<filter type="%s" binby="%s"/>""" % (filter2, filter2_binby)

        query = """
            <peakflow version="1.0">
                <query id="query1" type="traffic">
                    <time start_ascii="24 hours ago" end_ascii="now"/>
                    <unit type="bps"/>
                    <search limit="100" timeout="30"/>
                    <class>in</class>
                    <class>out</class>
                    <filter type="%(mo_type)s">
                        <instance value="%(mo_type_id)s"/>
                    </filter>
                    %(filter2)s
                </query>
            </peakflow>
        """ % {
                'mo_type': mo_type,
                'mo_type_id': mo_id,
                'filter2': query_filter
                }

        return self.pf.runXmlQuery(query)




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
    parser.add_option("--customer-id", metavar="ID", help="get a graph for customer with id ID")
    parser.add_option("--output-file", metavar="FILE", help="write output to FILE")
    parser.add_option("--mo-type", help="MO type")
    parser.add_option("--mo-id", help="MO id")
    parser.add_option("--filter", help="Filter by [nexthop]")
    parser.add_option("--graph-title", help="title of the graph")
    parser.add_option("--graph", help="fetch data and write a graph")
    parser.add_option("--table", help="fetch data and print in tabular form")
    (options, args) = parser.parse_args()

    pf = PeakflowSOAP(options.host, options.username, options.password)

    if options.graph and not options.output_file:
        print >> sys.stderr, "Please provide an output file to write the graph to with --output-file"
        sys.exit(1)

    f = Report()
    if options.graph:
        f.get_graph(options.output_file, options.mo_type, options.mo_id,
                options.graph_title, options.filter, 1)

    if options.table:
        print f.get_table(options.output_file, options.mo_type, options.mo_id,
                options.graph_title, options.filter, 1)
