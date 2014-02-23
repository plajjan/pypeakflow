pypeakflow
==========

Python library for Arbor Peakflow SP

The various APIs of Arbors Peakflow SP system does not offer much in terms of
configuring managed objects. This library aims to fix that and perhaps add more
functionality for convenience of accessing other information in a Peakflow
system.

Status of this is alpha alpha.. but please contribute if you are interested in
the topic :)

I'm currently using both SUDS and ZSI for SOAP calls as I'm having difficulty
decoding certain results with SUDS while for other stuff SUDS provides much
better output.

Usage
-----
Try running a command;

	python peakflow_soap.py -H my-peakflow-box -U username -P password --cli-run "system version"

