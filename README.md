# qmrdk-tools

QMRDK Tools
2015 by Bruno Espinoza (bruno.espinozaamaya@uq.net.au)

Some utilities in both Python and Matlab for the Quonset Microwave Radar Development Kit.

This Radar Development Kit (RDK) is based on the MIT Cantenna design, but
as opposed to it, it uses USBTMC interface instead of just reading
from the audio device.

The Matlab interface capture samples and output them into a .bin file, then
analysis is performed by the scripts for Doppler and Range.

The Python interface capture samples and output them into a .bin file that can be used
in GNU Radio for the radar analysis. A sample application was included.

The Matlab driver was tested on Windows and require the NI VISA Components.
The Python driver was tested on Linux (x86) and the Raspberry Pi. No VISA Components are needed.

