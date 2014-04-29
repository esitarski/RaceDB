[TOC]

# Hardware and Devices

## Barcode Readers

Any barcode reader with a "keyboard wedge" capability will work (this is how most barcode readers work).

The "keyboard wedge" means that the barcode reader looks like a keyboard.  To the computer, scanning a barcode is exactly like typing in the barcode, followed by the Enter key.

The one I tested the system with was:

* Esky USB Automatic Barcode Scanner Scanning Barcode Bar-code Reader with Hands Free Adjustable Stand

From Amazon.  It is a bit of a pain to assemble (don't forget the metal stabilizing weight), but it works very well.

## Electronic Signature Pads

This must use the Scriptel EASYSCRIPT DEVICE INTERFACE.  For example:

* ST1501
* ST1551
* ST1401

See the [Scriptel Site](http://www.scriptel.com/products).

It is *essential* to get the Scriptel with the "Easyscript" interface.  The Proscript interface will not work.

All signature pads are not alike.  The key feature of the Scriptel Easyscript pads is that they work directly with any web browser - plug it in and go.  Other pads use a proprietary protocol and require custom software to talk to it.  This approach does not work with a zero-install web-based application.

The Scriptel models are available at different price points:

* In the middle price point, the ST1501 shows the signature on its LCD screen as the user signs it.  It also gives the use the option to accept the signature, or redo it.  This is the model the system was developed with.
* At the low end is the ST1401.  This signature pad does not show the signature on its screen.  The user signs a blank screen, and there is no option to review the signature before accepting it.  About 40% cheaper than the ST1501, it still meets the legal requirement for signature capture.  If budget is very sensitive for you, this may be the model to go with (I personally don't like these, but that's me).
* At an even higher price, the ST1551 is a nicer version of the ST1501, with a slimmer profile and a back-light so it can be seen at night.  These additional features did not justify the increased price for my application, but they might be important to you.

To use the Signature Pad to capture rider's signatures, plug the pad into the computer.
On the Participant Edit screen, click on the Signature field and follow the instructions.

## RFID Reader/Writer

The system supports one RFID reader.
The system was tested with:

* Impinj 440 (4 antennas)
* Impinj 420 (2 antennas)
* Impinj R1000 (4 antennas, older model)

RaceDB uses the LLRP 1.0 standard (Low-Level Reader Protocol) to communicate with the RFID reader.

### RFID Near-Field Antennas

When writing tags at registration it is *essential* to use UHF Near-Field (short range) antennas.
If you use a regular long-range antenna, you risk reprogramming all the tags in the immediate area (not good!).

A near-field antenna has a range of 0-10cm and will only read/write tags that are close to it.

Some suggestions for UHF near-field antennas are:

* A1001 from [Times-7](www.times-7.com)
* IPJ-A0303-000 Mini-Guardrail ILT Antenna from [Impinj](www.impinj.com)

### Local Area Network

The computer connects to the RFID reader over a local area network.  The RFID Reader must be connected to the network.

Consider something like:

* Cisco-Linksys WRT54GL Wireless-G Broadband Router

This will allow you to connect the RFID reader with cables to the RaceDB computer, and additionally, it will allow you to connect other devices at the race server wirelessly.
Set up a security code to connect to the wireless network.  At present, RaceDB does not have security of its own.

After setting up your wireless network, consult your device for how to configure it so that remote computers can access it.

If you have a printer, it may make sense to make it accessible from the wireless network.

### Generator

Unless you have a source of power, you will need a reliable generator to power the system.

This does not need to be high-wattage.  The only devices that require power are the computer, the router, the RFID reader and possibly a printer if you need to print something.

Not more than 150 watts peak.