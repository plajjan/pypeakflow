pypeakflow
==========

Python library for Arbor Peakflow SP

The various APIs of Arbors Peakflow SP system does not offer much in terms of
configuring managed objects. This library aims to fix that and perhaps add more
functionality for convenience of accessing other information in a Peakflow
system.

Development has just started ;)

status
------
The SOAP API of PeakFlow requires digest authentication. Thus far I've only
tried the suds SOAP library for Python and it seems it is not capable of Digest
authentication. Need to look at another lib, ZSI perhaps? But it seems it's not
being developed and it's a behemoth.
