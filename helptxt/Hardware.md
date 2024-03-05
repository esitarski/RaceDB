[TOC]

# Hardware and Devices

## USB RFID Readers

RaceDB works with any 860-915 MHz USB RFID reader (for example, [here](https://www.amazon.ca/s?k=usb+rfid+reader+uhf+epc&sprefix=uhf+usb%2Caps%2C106&ref=nb_sb_ss_ts-doa-p_1_7)).
Make sure you get a UHF reader (the 125KHz or 13.56KHz ones don't work).

These readers work like a keyboard when they read a tag.  Any computer, tablet or smartphone connected to the reader sees the tag characters followed by an Enter as if they were typed in.
RaceDB has been carefully designed to take advantage of this behavior to automatically trigger its web pages.

USB RFID Readers cannot write tag codes, however, RaceDB can manage all aspects of tags (issue and revoke) with USB RFID Readers.
This allows you to accomplish everything you need to do for race management, including self-checkin, provided that you set up a pool of unique tags ahead of time.
This can easily be done by ordering tags with random or sequential EPC codes on them.  Alternatively, you can program tags any way you want with TagReadWrite.

There are many advantages of USB RFID Readers over using a traditional RFID reader (eg. Impinj):

* Allows you to manage all aspects of deploying chip tags at registration with a pool of unique tags.
* Easier and more flexible setup.  Plug in the USB RFID Reader, login with the "reg" (for registration) or "serve" (for self-serve) username.  You are ready to go.  No central RFID reader to power and no antenna cables to run.
* Any number of readers supported.  Traditional RFID readers support 2-4 antennas.  With USB RFID Readers, you can deploy as many as you want with each check-in device.
* More economical than traditional RFID readers.  One near-field antenna with cable is more expensive than one USB RFID Reader alone.  The cost of the traditional reader itself and its power supply are additional.
* Supports RaceDB cloud deployment.  With a traditional RFID reader, RaceDB must be running locally so it can connect to the reader hardware.  With USB RFID Readers, this is no longer required and RaceDB can run in the cloud.  Start Lists, Results and Series Results are instantly available to all on RaceDBHub.  Callups for accurate Start Lists are instantly available based on current Series standings.

## Barcode Readers

Any barcode reader with a "keyboard wedge" capability will work (this is how most barcode readers work).

The "keyboard wedge" means that the barcode reader acts like a keyboard to the computer, tablet or smart phone.

The one tested the system with was:

* Esky USB Automatic Barcode Scanner Scanning Barcode Bar-code Reader with Hands Free Adjustable Stand

Most USB barcode readers should work.

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

RaceDB also supports one RFID reader.  This allows registration staff to write chip tags on demand, however, it is significantly more expensive and inconvenient that USB RFID Readers.


RaceDB was tested with:

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
