/*======================================================
 * Scriptel ScripTouch EasyScript JavaScript API
 * Copyright 2013 - Scriptel Corporation
 *======================================================
 */

/**
 * Constructor, creates a new instance of this type.
 * @classdesc This error is thrown in the event there is an error parsing the
 * signature.
 * @constructor
 */


/*global InternationalKeyboard, InstallTrigger */

function SignatureError(msg, pos) {
    "use strict";
    /**
     * This member carries a human readable message as to what type of error
     * occurred while parsing.
     * @public
     * @instance
     * @type {string}
     */
    this.message = msg;
    /**
     * This member carries the character position of where the error occurred.
     * @public
     * @instance
     * @type {number}
     */
    this.position = pos;
}

/**
 * Constructor, creates a new instance of this class.
 * @classdesc This class represents a parsed signature string.
 * @constructor
 */
function ScriptelSignature() {
    "use strict";
    /**
     * The captured protocol version, at present only 'A' exists.
     * @public
     * @instance
     * @type {string}
     */
    this.protocolVersion = "";
    /**
     * The model of the device that captured the signature.
     * @public
     * @instance
     * @type {string}
     */
    this.model = "";
    /**
     * The currently running version of the firmware on the device that captured the signature.
     * @public
     * @instance
     * @type {string}
     */
    this.version = "";
    /**
     * An array of coordinate arrays containing the pen strokes parsed from the signature stream.
     * @public
     * @instance
     * @type {array<array<ScriptelCoordinate>>
     */
    this.strokes = [];
}

/**
 * Constructor, creates a new instance of this class.
 * @classdesc This class represents a parsed card swipe string.
 * @constructor
 */
function ScriptelCardSwipe() {
    "use strict";
    /**
     * The captured protocol version, at present only 'A' exists.
     * @public
     * @instance
     * @type {string}
     */
    this.protocolVersion = "";
    /**
     * This will contain the captured card swipe data. Any tracks
     * that were unable to be read will not be present.
     */
    this.cardData = "";
    /**
     * If this card is a financial card, parsed information will
     * be available here.
     */
    this.financialCard = false;
    /**
     * If this card is an identification card (driver's license)
     * the parsed information will be available here.
     */
    this.identificationCard = false;
}
/**
 * Constructor, creates a new instance of this class.
 * @classdesc This class represents a parsed financial card.
 * @constructor
 */
function ScriptelFinancialCard() {
    "use strict";
    /**
     * Contains the contents of the parsed first track. False if the track couldn't be read/parsed.
     * @public
     * @instance
     * @type {FinancialTrackOneData}
     */
    this.trackOne = false;
    /**
     * Contains the contents of the parsed second track. False if the track couldn't be read/parsed.
     * @public
     * @instance
     * @type {FinancialTrackTwoData}
     */
    this.trackTwo = false;
    /**
     * Contains the name of the card issuer, false if unknown.
     * @public
     * @instance
     * @type {string}
     */
    this.cardIssuer = false;
    /**
     * Indiciates whether or not the identification number on the card passed checksum.
     * @public
     * @instance
     * @type {boolean}
     */
    this.numberValid = false;
}
/**
 * Constructor, creates a new instance of this class.
 * @classdesc This class represents a parsed identification card.
 * @constructor
 */
function ScriptelIdentificationCard() {
    "use strict";
    /**
     * Contains the contents of the first parsed track. False if the track couldn't be read/parsed.
     * @public
     * @instance
     * @type {IdentificationTrackOneData}
     */
    this.trackOne = false;
    /**
     * Contains the contents of the second parsed track. False if the track couldn't be read/parsed.
     * @public
     * @instance
     * @type {IdentificationTrackTwoData}
     */
    this.trackTwo = false;
    /**
     * Contains the contents of the third parsed track. False if the track couldn't be read/parsed.
     * @public
     * @instance
     * @type {IdentificationTrackThreeData}
     */
    this.trackThree = false;
}
/**
 * Constructor, creates a new instance of this class.
 * @classdesc This class represents a single point on a two dimensional plane.
 * @constructor
 */
function ScriptelCoordinate(x, y) {
    "use strict";
    /**
     * The horizontal location of the point.
     * @public
     * @instance
     * @type {number}
     */
    this.x = x || -1;
    /**
     * The vertical location of the point.
     * @public
     * @instance
     * @type {number}
     */
    this.y = y || -1;
}
/**
 * Constructor, creates a new instance of this class.
 * @classdesc This class represents the bounding box around a set of points on
 * a two dimensional plane.
 * @constructor
 */
function ScriptelBoundingBox() {
    "use strict";
    /**
     * The left most edge.
     * @public
     * @instance
     * @type {number}
     */
    this.x1 = -1;
    /**
     * The right most edge.
     * @public
     * @instance
     * @type {number}
     */
    this.x2 = -1;
    /**
     * The top most edge.
     * @public
     * @instance
     * @type {number}
     */
    this.y1 = -1;
    /**
     * The bottom most edge.
     * @public
     * @instance
     * @type {number}
     */
    this.y2 = -1;
    /**
     * The total width of the points.
     * @public
     * @instance
     * @type {number}
     */
    this.width = -1;
    /**
     * The total height of the points.
     * @public
     * @instance
     * @type {number}
     */
    this.height = -1;
}

/**
 * Constructor, creates a new instance of this type.
 * @classdesc This class represents an EasyScript protocol
 * @constructor
 */
function STNSignatureProtocol() {
    "use strict";
    /**
     * This string contains a textual name of this protocol.
     * @public
     * @instance
     * @type {string}
     */
    this.protocolName = "Standard EasyScript Protocol";
    /**
     * This character represents the glyph that starts a signature stream.
     * @public
     * @instance
     * @type {string}
     */
    this.startStream = '~';
    /**
     * This character represents the glyph that ends a signature stream.
     * @public
     * @instance
     * @type {string}
     */
    this.endStream = '`';
    /**
     * This character represents the glyph that signifies a break between strokes.
     * @public
     * @instance
     * @type {string}
     */
    this.penUp = ' ';
    /**
     * This string represents the "sentinel" that must be present before considering this the correct protocol.
     * @public
     * @instance
     * @type {string}
     */
    this.sentinel = "STSIGN";
    /**
     * The width in pixels of the devices using this protocol.
     * @public
     * @instance
     * @type {number}
     */
    this.width = 240;
    /**
     * The height in pixels of the devices using this protocol.
     * @public
     * @instance
     * @type {number}
     */
    this.height = 64;
    /**
     * This table contains the character codes and values of the most and least significant bytes of
     * the x and y coordinates. This is required to accurately decode a signature.
     * @public
     * @instance
     * @type {object<string,array<array<number>>>}
     */
    this.valueTable = {
        "x": [
            [0x41, 0x43, 0x45, 0x47, 0x49, 0x4b, 0x4d, 0x4f, 0x51, 0x53, 0x55, 0x57, 0x59, 0x21, 0x23, 0x25, 0x26, 0x28, 0x2b, 0x7d, 0x22, 0x3c],
            [0x42, 0x44, 0x46, 0x48, 0x4a, 0x4c, 0x4e, 0x50, 0x52, 0x54, 0x56, 0x58, 0x5a, 0x40, 0x24, 0x5e, 0x2a, 0x29, 0x5f, 0x7b, 0x7c, 0x3a, 0x3e]
        ],
        "y": [
            [0x61, 0x63, 0x65, 0x67, 0x69, 0x6b, 0x6d, 0x6f, 0x71, 0x73, 0x75, 0x77, 0x79, 0x31, 0x33, 0x35, 0x37, 0x39, 0x3d, 0x5d, 0x27, 0x2c],
            [0x62, 0x64, 0x66, 0x68, 0x6a, 0x6c, 0x6e, 0x70, 0x72, 0x74, 0x76, 0x78, 0x7a, 0x32, 0x34, 0x36, 0x38, 0x30, 0x2d, 0x5b, 0x5c, 0x3b, 0x2e]
        ]
    };
}
/**
 * Constructor, creates a new instance of this type.
 * @classdesc This class represents an EasyScript card swipe protocol
 * @constructor
 */
function STNCardSwipeProtocol() {
    "use strict";
    /**
     * This string contains a textual name of this protocol.
     * @public
     * @instance
     * @type {string}
     */
    this.protocolName = "Standard EasyScript Card Swipe Protocol";
    /**
     * This character represents the glyph that starts a signature stream.
     * @public
     * @instance
     * @type {string}
     */
    this.startStream = '!';
    /**
     * This character represents the glyph that ends a signature stream.
     * @public
     * @instance
     * @type {string}
     */
    this.endStream = '\r';
    /**
     * This string represents the "sentinel" that must be present before considering this the correct protocol.
     * @public
     * @instance
     * @type {string}
     */
    this.sentinel = "STCARD";
}
/**
 * Constructor, creates a new instance of this class.
 * @classdesc This class represents the parsed first track of a financial card.
 * @constructor
 */
function FinancialTrackOneData() {
    "use strict";
    /**
     * Contains the account number of the financial card.
     * @public
     * @instance
     * @type {string}
     */
    this.accountNumber = "";
    /**
     * Contains the first name of the card holder.
     * @public
     * @instance
     * @type {string}
     */
    this.firstName = "";
    /**
     * Contains the last name of the card holder
     * @public
     * @instance
     * @type {string}
     */
    this.lastName = "";
    /**
     * Contains the expiration date of the card.
     * @public
     * @instance
     * @type {Date}
     */
    this.expiration = false;
    /**
     * Contains the service code of the card.
     * @public
     * @instance
     * @type {string}
     */
    this.serviceCode = "";
    /**
     * Contains any other data the card issuer wanted to include on the first track.
     * @public
     * @instance
     * @type {string}
     */
    this.discretionaryData = "";
}
/**
 * Constructor, creates a new instance of this class.
 * @classdesc This class represents the parsed second track of a financial card.
 * @constructor
 */
function FinancialTrackTwoData() {
    "use strict";
    /**
     * Contains the account number of the financial card.
     * @public
     * @instance
     * @type {string}
     */
    this.accountNumber = "";
    /**
     * Contains the expiration date of the card.
     * @public
     * @instance
     * @type {Date}
     */
    this.expiration = false;
    /**
     * Contains the service code of the card.
     * @public
     * @instance
     * @type {string}
     */
    this.serviceCode = "";
    /**
     * Contains any other data the card issuer wanted to include on the first track.
     * @public
     * @instance
     * @type {string}
     */
    this.discretionaryData = "";
}
/**
 * Constructor, creates a new instance of this class.
 * @classdesc This class represents the parsed first track of an identification card.
 * @constructor
 */
function IdentificationTrackOneData() {
    "use strict";
    /**
     * Two character state code.
     * @public
     * @instance
     * @type {string}
     */
    this.state = "";
    /**
     * City of residence.
     * @public
     * @instance
     * @type {string}
     */
    this.city = "";
    /**
     * Last name of the card holder.
     * @public
     * @instance
     * @type {string}
     */
    this.lastName = "";
    /**
     * First name of the card holder.
     * @public
     * @instance
     * @type {string}
     */
    this.firstName = "";
    /**
     * Middle name of the card holder.
     * @public
     * @instance
     * @type {string}
     */
    this.middleName = "";
    /**
     * Home address of the card holder.
     * @public
     * @instance
     * @type {string}
     */
    this.homeAddress = "";
    /**
     * Any additional information the issuer wanted to include.
     * @public
     * @instance
     * @type {string}
     */
    this.discretionaryData = "";
}
/**
 * Constructor, creates a new instance of this class.
 * @classdesc This class represents the parsed second track of an identification card.
 * @constructor
 */
function IdentificationTrackTwoData() {
    "use strict";
    /**
     * Issuer identification number.
     * @public
     * @instance
     * @type {string}
     */
    this.issuerNumber = "";
    /**
     * Cardholder identification number (license number).
     * @public
     * @instance
     * @type {string}
     */
    this.idNumber = "";
    /**
     * Card expiration date.
     * @public
     * @instance
     * @type {date}
     */
    this.expiration = false;
    /**
     * Cardholder birth date.
     * @public
     * @instance
     * @type {date}
     */
    this.birthDate = false;
}
/**
 * Constructor, creates a new instance of this class.
 * @classdesc This class represents the parsed third track of an identification card.
 * @constructor
 */
function IdentificationTrackThreeData() {
    "use strict";
    /**
     * Specification version.
     * @public
     * @instance
     * @type {number}
     */
    this.cdsVersion = -1;
    /**
     * Jurisdiction version.
     * @public
     * @instance
     * @type {number}
     */
    this.jurisdictionVersion = -1;
    /**
     * Either full or truncated postcal code.
     * @public
     * @instance
     * @type {string}
     */
    this.zipCode = -1;
    /**
     * The class of this identification card/drivers license.
     * @public
     * @instance
     * @type {string}
     */
    this.licenseClass = "";
    /**
     * Restriction codes designated by issuer.
     * @public
     * @instance
     * @type {string}
     */
    this.restrictions = "";
    /**
     * Endorsement codes designated by issuer.
     * @public
     * @instance
     * @type {string}
     */
    this.endorsements = "";
    /**
     * Cardholder sex, M for male, F for female.
     * @public
     * @instance
     * @type {string}
     */
    this.sex = "";
    /**
     * Height of the cardholder.
     * @public
     * @instance
     * @type {string}
     */
    this.height = "";
    /**
     * Weight of the cardholder.
     * @public
     * @instance
     * @type {string}
     */
    this.weight = "";
    /**
     * Hair color of the cardholder.
     * @public
     * @instance
     * @type {string}
     */
    this.hairColor = "";
    /**
     * Eye color of the cardholder.
     * @public
     * @instance
     * @type {string}
     */
    this.eyeColor = "";
    /**
     * Any additional information included by the issuer.
     * @public
     * @instance
     * @type {string}
     */
    this.discretionaryData = "";
}

/**
 * Constructor, creates a new instance of this class.
 * @classdesc This class can be used to add event handlers to your web
 * pages that are capable of intercepting, parsing and rendering signature
 * streams from the Scriptel ScripTouch EasyScript series of devices.
 * @constructor
 */
function ScriptelEasyScript() {
    "use strict";
    /**
     * The list of all available signature parsing algorithms.
     * @public
     * @instance
     * @type {array<SignatureProtocol>}
     */
    this.signatureProtocols = [
        new STNSignatureProtocol()
    ];
    /**
     * The list of all available card parsing algorithms.
     * @public
     * @instance
     * @type {array<SignatureProtocol>}
     */
    this.cardSwipeProtocols = [
        new STNCardSwipeProtocol()
    ];
    /**
     * This property stores the current version of this library.
     * @public
     * @instance
     * @type {string}
     */
    this.libraryVersion = "3.0.98";
    /**
     * This property stores the date on which this library was built.
     * @public
     * @instance
     * @type {string}
     */
    this.libraryBuildDate = "2014-02-17 16:26:40-0500";
    /**
     * The protocol to be used to decode the signature string.
     * @public
     * @instance
     * @type {SignatureProtocol}
     */
    this.signatureProtocol = new STNSignatureProtocol();
    /**
     * The protocol to be used to decode the magnetic strip string.
     * @public
     * @instance
     * @type {CardSwipeProtocol}
     */
    this.cardSwipeProtocol = new STNCardSwipeProtocol();

    /**
     * In the case international keyboards are being used this will contain
     * the specification of the keyboard to convert from.
     * @public
     * @instance
     * @type {string}
     */
    this.fromKeyboardSpec = undefined;

    /**
     * In the case international keyboards are being used this will contain
     * the specification of the keyboard to convert to.
     * @public
     * @instance
     * @type {string}
     */
    this.toKeyboardSpec = undefined;

    /**
     * This object is used to support international keyboards.
     * @public
     * @instance
     * @type {InternationalKeyboard}
     */
    this.internationalKeyboard = undefined;

    /**
     * This callback function is called after capturing, but prior to processing
     * any keyboard data. This can be used to "reconfigure" the keyboard API prior
     * to processing to switch keyboard specifications, protocols, etc.
     * @public
     * @instance
     * @type {function}
     */
    this.configurationCallback = false;

    if (typeof InternationalKeyboard === "function") {
        this.fromKeyboardSpec = "us-basic";
        this.toKeyboardSpec = "us-basic";
        this.internationalKeyboard = new InternationalKeyboard();
    }

    /**
     * A set of callbacks to call upon receiving a signature from the attached elements.
     * @private
     * @instance
     * @type {function}
     */
    this.callbacks = [];
    /**
     * Whether or not we're currently intercepting (blocking) key presses in anticipation of a signature.
     * @private
     * @instance
     * @type {boolean}
     */
    this.intercepting = false;
    /**
     * The keyboard buffer used while intercepting key presses.
     * @private
     * @instance
     * @type {string}
     */
    this.buffer = "";
    /**
     * The maximum time we're willing to wait between characters before we decide what we're capturing isn't a signature.
     * @private
     * @instance
     * @type {number}
     */
    this.timeout = 250;
    /**
     * The time stamp of the last key press.
     * @private
     * @instance
     * @type {number}
     */
    this.lastKey = -1;
    /**
     * This keeps track of the protocol currently being used to decode the capture buffer.
     * @private
     * @instance
     * @type {SignatureProtocol|CardSwipeProtocol}
     */
    this.lastProtocol = false;

    this.lastKeySpace = false;

    //Keyboard handler to register.
    var t = this;
    this.keyEventHandler = function (evt) { 
        t.keyboardHandler(evt);
    };
}
/**
 * This method takes a buffer and attempts to parse it as either a Signature or
 * a card swipe, depending on what protocol it matches.
 * @method
 * @private
 * @param {string} buffer Captured string buffer.
 * @returns {ScriptelSignature|ScriptelCardSwipe} Returns either a signature or card swipe object, depending on the contents of the buffer.
 */
ScriptelEasyScript.prototype.parseEvent = function (buffer) {
    "use strict";
    //Need to determine if this is a card swipe or signature.
    var chr = buffer.charAt(0);
    if (chr === this.translateCharacterTo(this.signatureProtocol.startStream)) {
        return this.parseSignature(buffer, this.fromKeyboardSpec, this.toKeyboardSpec);
    }

    return this.parseCard(buffer, this.fromKeyboardSpec, this.toKeyboardSpec);
};
/**
 * This method attempts to parse a card swipe using the registered card
 * swipe protocol.
 * @method
 * @public
 * @param {string} buffer Card swipe string from the EasyScript device.
 * @param fromKeyboardSpec {string} Keyboard specification to convert from (optional).
 * @param toKeyboardSpec {string} Keyboard specification to convert to (optional).
 * @returns {ScriptelCardSwipe} Parsed card swipe data.
 */
ScriptelEasyScript.prototype.parseCard = function (buffer, fromKeyboardSpec, toKeyboardSpec) {
    "use strict";
    var p = this.cardSwipeProtocol;

    var fromKbd = false;
    var toKbd = false;

    //Keyboard internationalization.
    if (typeof InternationalKeyboard === "function") {
        if (!fromKeyboardSpec) {
            fromKeyboardSpec = this.fromKeyboardSpec;
        }
        if (!toKeyboardSpec) {
            toKeyboardSpec = this.toKeyboardSpec;
        }

        if (this.internationalKeyboard.keymaps[fromKeyboardSpec]) {
            fromKbd = this.internationalKeyboard.keymaps[fromKeyboardSpec];
        } else if (fromKeyboardSpec) {
            throw new SignatureError("Unable to find specification for from keyboard: " + fromKeyboardSpec, 0);
        }

        if (this.internationalKeyboard.keymaps[toKeyboardSpec]) {
            toKbd = this.internationalKeyboard.keymaps[toKeyboardSpec];
        } else if (toKeyboardSpec) {
            throw new SignatureError("Unable to find specification for to keyboard: " + toKeyboardSpec, 0);
        }
        //Lets try to do the conversion, this is a potentially lossy operation, we'll need to perform some correction later.
        buffer = this.internationalKeyboard.translate(buffer, fromKbd, toKbd);
    } else if (fromKeyboardSpec || toKeyboardSpec) {
        throw new SignatureError("Keyboard to or from specification provided, but unable to find scriptel-international-keyboard.js.", 0);
    }

    if (buffer.charAt(0) !== p.startStream) {
        throw new SignatureError("Card swipe stream doesn't start with the proper start character: " + buffer.charAt(0) + "!=" + p.startStream, 0);
    } 
    if (buffer.charAt(buffer.length - 1) !== p.endStream) {
        throw new SignatureError("Card swipe stream doesn't end with the proper end character: " + buffer.charAt(buffer.length - 1) + "!=" + p.endStream, (buffer.length - 1));
    } 
    if (buffer.substring(1, p.sentinel.length + 1).toLowerCase() !== p.sentinel.toLowerCase()) {
            throw new SignatureError("Card swipe stream doesn't start with the correct sentinel.", 1);
    }
    var result = new ScriptelCardSwipe();
    result.protocolVersion = buffer.charAt(8).toUpperCase();
    result.cardData = buffer.substring(10);

    //Check to see if this card is an identification card, if so
    //lets try to parse deeper.
    var i1 = this.parseIdentificationTrackOne(result.cardData);
    var i2 = this.parseIdentificationTrackTwo(result.cardData);
    var i3 = this.parseIdentificationTrackThree(result.cardData);
    if (i1 || i2 || i3) {
        //This appears to be an identification card.
        result.identificationCard = new ScriptelIdentificationCard();
        result.identificationCard.trackOne = i1;
        result.identificationCard.trackTwo = i2;
        result.identificationCard.trackThree = i3;
    }

    //Check to see if this card is a financial card, if so lets
    //try to parse deeper.
    var f1 = this.parseFinancialTrackOne(result.cardData);
    var f2 = this.parseFinancialTrackTwo(result.cardData);
    if (f1 || f2) {
        //This is a financial card.
        result.financialCard = new ScriptelFinancialCard();
        result.financialCard.trackOne = f1;
        result.financialCard.trackTwo = f2;

        var cardNumber = f1 ? f1.accountNumber : f2.accountNumber;
        result.financialCard.cardIssuer = this.checkFinancialCardType(cardNumber);
        result.financialCard.numberValid = this.checkFinancialCardChecksum(cardNumber);
    }

    return result;
};
/**
 * This method uses Luhn's algorithm to verify the checksum on a financial
 * card identification number.
 * @method
 * @public
 * @param {string} cardNumber The identification number of a financial card.
 * @returns {boolean} True if the number passes the checksum, false otherwise.
 */
ScriptelEasyScript.prototype.checkFinancialCardChecksum = function (cardNumber) {
    "use strict";
    var sum = 0, flip = 0, i;
    var table = [[0, 1, 2, 3, 4, 5, 6, 7, 8, 9], [0, 2, 4, 6, 8, 1, 3, 5, 7, 9]];
    var index = 0;
    for (i = cardNumber.length - 1; i >= 0; i--) {
        index = flip++ & 1;
        sum += table[index][parseInt(cardNumber.charAt(i), 10)];
    }
    return sum % 10 === 0;
};
/**
 * This method uses pattern matching to attempt to identify the issuer for
 * a financial card.
 * @method
 * @public
 * @param {string} cardNumber The identification number of a financial card.
 * @returns {string} String describing the card issuer, false if no matches are found.
 */
ScriptelEasyScript.prototype.checkFinancialCardType = function (cardNumber) {
    "use strict";
    var cardTypes = {
        "American Express": /^(34|37)\d{13}$/,
        "Diners Club": /^(30[0-5]\d{11}|36\d{12})$/,
        "Carte Blanche": /^38\d{12}$/,
        "Discover": /^6011\d{12}$/,
        "EnRoute": /^(2131|1800)\d{11}$/,
        "JCB": /^(3\d{15}|(2131|1800)\d{11})$/,
        "Master Card": /^5[1-5]\d{14}$/,
        "Visa": /^4\d{12,15}$/
    };

    var type;
    var regex;
    for (type in cardTypes) {
        if (cardTypes.hasOwnProperty(type)) {
            regex = cardTypes[type];
            if (cardNumber.match(regex)) {
                return type;
            }
        }
    }
    return false;
};
/**
 * This method attempts to parse track one of a financial card based on the specification
 * outlined here: http://en.wikipedia.org/wiki/Magnetic_stripe_card.
 * Since there are many, many issuers this algorithm may not work for all financial cards.
 * @method
 * @public
 * @param {string} trackData The track data to parse.
 * @return {FinancialTrackOneData} Parsed track information on success, false on error.
 */
ScriptelEasyScript.prototype.parseFinancialTrackOne = function (trackData) {
    "use strict";
    var regex = /%[A-Z]{1}(\d{1,19})\^([^\^]{1,30})\^(\d{2})(\d{2})([0-9]{3})([A-Za-z 0-9]*)\?/;
    var match = trackData.match(regex);
    if (match) {
        var data = new FinancialTrackOneData();
        data.accountNumber = match[1];

        var expMonth = parseInt(match[4], 10);
        var expYear = parseInt(match[3], 10) + 2000;
        var expTemp = new Date(expYear, expMonth, 0, 0, 0, 0, 0);
        data.expiration = new Date();
        data.expiration.setTime(expTemp.getTime() - 1);

        data.serviceCode = match[5];
        data.discretionaryData = match[6];

        var name = match[2];
        var idx;
        idx = name.indexOf("/");
        if (idx >= 0) {
            data.lastName = name.substring(0, idx).trim();
            data.firstName = name.substring(idx + 1).trim();
        } else {
            data.firstName = name;
            data.lastName = "";
        }
        return data;
    }
    return false;
};
/**
 * This method attempts to parse track two of a financial card based on the specification
 * outlined here: http://en.wikipedia.org/wiki/Magnetic_stripe_card.
 * Since there are many, many issuers this algorithm may not work for all financial cards.
 * @method
 * @public
 * @param {string} trackData The track data to parse.
 * @return {FinancialTrackTwoData} Parsed track information on success, false on error.
 */
ScriptelEasyScript.prototype.parseFinancialTrackTwo = function (trackData) {
    "use strict";
    var regex = /;(\d{1,19})=(\d{2})(\d{2})(\d{3})([A-Za-z 0-9]*)\?/;
    var match = trackData.match(regex);
    if (match) {
        var data = new FinancialTrackTwoData();
        data.accountNumber = match[1];
        var expMonth = parseInt(match[3], 10);
        var expYear = parseInt(match[2], 10) + 2000;
        var expTemp = new Date(expYear, expMonth, 0, 0, 0, 0, 0);
        data.expiration = new Date();
        data.expiration.setTime(expTemp.getTime() - 1);

        data.serviceCode = match[4];
        data.discretionaryData = match[5];
        return data;
    }
    return false;
};
/**
 * This method attempts to parse track one of an identification card based on the specification
 * outlined here: http://www.aamva.org/?aspxerrorpath=/NR/rdonlyres/66260AD6-64B9-45E9-A253-B8AA32241BE0/0/2005DLIDCardSpecV2FINAL.pdf
 * Since many states issue these cards this may not work for all states with magnetic stripe data.
 * @method
 * @public
 * @param {string} trackData The track data to parse.
 * @return {IdentificationTrackOneData} Parsed track information on success, false on error.
 */
ScriptelEasyScript.prototype.parseIdentificationTrackOne = function (trackData) {
    "use strict";
    var regex = /\%([A-Z]{2})([A-Z\.\-' ]{1,13})\^?([A-Z\.\-' \$]{1,35})\^?([^\?\^]{1,29})\^?\?/;
    var match = trackData.match(regex);
    if (match) {
        var data = new IdentificationTrackOneData();
        data.state = match[1];
        data.city = match[2];

        var bits = match[3].split("$");
        data.lastName = bits[0];
        if (bits[1]) {
            data.firstName = bits[1];
        }
        if (bits[2]) {
            data.middleName = bits[2];
        }
        data.homeAddress = match[4];

        return data;
    }
    return false;
};
/**
 * This method attempts to parse track two of an identification card based on the specification
 * outlined here: http://www.aamva.org/?aspxerrorpath=/NR/rdonlyres/66260AD6-64B9-45E9-A253-B8AA32241BE0/0/2005DLIDCardSpecV2FINAL.pdf
 * Since many states issue these cards this may not work for all states with magnetic stripe data.
 * @method
 * @public
 * @param {string} trackData The track data to parse.
 * @return {IdentificationTrackTwoData} Parsed track information on success, false on error.
 */
ScriptelEasyScript.prototype.parseIdentificationTrackTwo = function (trackData) {
    "use strict";
    var regex = /;(6[0-9]{5})([0-9]{1,13})=([0-9]{4})([0-9]{8})([0-9]{0,5})=?\?/;
    var match = trackData.match(regex);
    if (match) {
        var data = new IdentificationTrackTwoData();
        data.issuerNumber = match[1];
        data.idNumber = match[2] + match[5];

        var expYear = 2000 + parseInt(match[3].substring(0, 2), 10);
        var expMonth = parseInt(match[3].substring(2), 10);
        var expTemp = new Date(expYear, expMonth, 1, 0, 0, 0, 0);
        data.expiration = new Date();
        data.expiration.setTime(expTemp.getTime() - 1);

        var birthYear = parseInt(match[4].substring(0, 4), 10);
        var birthMonth = parseInt(match[4].substring(4, 6), 10) - 1;
        var birthDay = parseInt(match[4].substring(6), 10);

        data.birthDate = new Date(birthYear, birthMonth, birthDay, 0, 0, 0, 0);

        return data;
    }

    return false;
};
/**
 * This method attempts to parse track three of an identification card based on the specification
 * outlined here: http://www.aamva.org/?aspxerrorpath=/NR/rdonlyres/66260AD6-64B9-45E9-A253-B8AA32241BE0/0/2005DLIDCardSpecV2FINAL.pdf
 * Since many states issue these cards this may not work for all states with magnetic stripe data.
 * @method
 * @public
 * @param {string} trackData The track data to parse.
 * @return {IdentificationTrackThreeData} Parsed track information on success, false on error.
 */
ScriptelEasyScript.prototype.parseIdentificationTrackThree = function (trackData) {
    "use strict";
    var regex = /%([0-9]{1})([0-9]{1})([A-Z 0-9]{11})([A-Z 0-9]{2})([A-Z 0-9]{10})([A-Z 0-9]{4})(1|2|M|F)([0-9 ]{3})([0-9 ]{3})([A-Z ]{3})([A-Z ]{3})([^\?]{0,37})\?/;
    var match = trackData.match(regex);
    if (match) {
        var data = new IdentificationTrackThreeData();
        data.cdsVersion = parseInt(match[1], 10);
        data.jurisdictionVersion = parseInt(match[2], 10);
        data.zipCode = match[3].trim();
        data.licenseClass = match[4].trim();
        data.restrictions = match[5].trim();
        data.endorsements = match[6].trim();
        data.sex = (parseInt(match[7], 10) === 1 || match[7] === "M") ? "M" : "F";
        data.height = match[8].trim();
        data.weight = match[9].trim();
        data.hairColor = match[10].trim();
        data.eyeColor = match[11].trim();
        data.discretionaryData = match[12].trim();
        return data;
    }

    return false;
};
/**
 * This method parses an encoded ScripTouch series EasyScript
 * string and returns an object representing the decoded contents.
 * Errors are detected and exceptions are thrown if there is a
 * problem decoding the stream.
 * @method
 * @public
 * @param sig {string} Signature to parse.
 * @param fromKeyboardSpec {string} Keyboard specification to convert from (optional).
 * @param toKeyboardSpec {string} Keyboard specification to convert to (optional).
 * @return {ScriptelSignature} Parsed signature.
 */
ScriptelEasyScript.prototype.parseSignature = function (sig, fromKeyboardSpec, toKeyboardSpec) {
    "use strict";
    var p = this.signatureProtocol;
    if (console && console.time) {
        console.time("Parsing Signature");
    }

    var fromKbd = false;
    var toKbd = false;

    //Keyboard internationalization.
    if (typeof InternationalKeyboard === "function") {
        if (!fromKeyboardSpec) {
            fromKeyboardSpec = this.fromKeyboardSpec;
        }
        if (!toKeyboardSpec) {
            toKeyboardSpec = this.toKeyboardSpec;
        }

        if (this.internationalKeyboard.keymaps[fromKeyboardSpec]) {
            fromKbd = this.internationalKeyboard.keymaps[fromKeyboardSpec];
        } else if (fromKeyboardSpec) {
            throw new SignatureError("Unable to find specification for from keyboard: " + fromKeyboardSpec, 0);
        }

        if (this.internationalKeyboard.keymaps[toKeyboardSpec]) {
            toKbd = this.internationalKeyboard.keymaps[toKeyboardSpec];
        } else if (toKeyboardSpec) {
            throw new SignatureError("Unable to find specification for to keyboard: " + toKeyboardSpec, 0);
        }
        //Lets try to do the conversion, this is a potentially lossy operation, we'll need to perform some correction later.
        sig = this.internationalKeyboard.translate(sig, fromKbd, toKbd);
    } else if (fromKeyboardSpec || toKeyboardSpec) {
        throw new SignatureError("Keyboard to or from specification provided, but unable to find scriptel-international-keyboard.js.", 0);
    }

    //Do some quick and simple error checks.
    if (sig.charAt(0) !== p.startStream) {
        throw new SignatureError("Signature stream doesn't start with the proper start character: " + sig.charAt(0) + "!=" + p.startStream, 0);
    } 
    if (sig.length <= 30) {
        throw new SignatureError("Signature stream is too short", 0);
    } 
    if (sig.charAt(sig.length - 1) !== p.endStream) {
        throw new SignatureError("Signature stream doesn't end with the proper end character: " + sig.charAt(sig.length - 1) + "!=" + p.endStream, (sig.length - 1));
    }
    if (sig.substring(1, p.sentinel.length + 1).toLowerCase() !== p.sentinel.toLowerCase()) {
        throw new SignatureError("Signature stream doesn't start with the correct sentinel.", 1);
    }

    //Detect caps-lock case shift and invert if we need to.
    if (sig.substring(1, p.sentinel.length + 1) !== p.sentinel) {
        sig = ScriptelEasyScript.invertCase(sig);
    }

    //Tokenize the header
    var header = sig.split(" ", 4);
    if (header.length < 4) {
        throw new SignatureError("Invalid header: expecting 4 space-delimited tokens, got " + header.length, 1);
    }

    //Initialize our result object with our header tokens.
    var result = new ScriptelSignature();
    result.protocolVersion = header[1];
    result.model = header[2];
    result.version = header[3];

    //Read the encoded stroke stream and tokenize by stroke.
    var len = header[0].length + header[1].length + header[2].length + header[3].length + 4;
    var encodedString = sig.substring(len, sig.length - 2);
    if (encodedString.length < 4) {
        return result;
    }
    var eStrokes = encodedString.split(p.penUp);
    var pos = len;
    var i, x;
    var encoded;
    var points;
    var ePoint;
    //For each stroke
    for (i = 0; i < eStrokes.length; i++) {
        encoded = eStrokes[i];
        points = [];
        points.length = Math.floor(encoded.length / 4);
        //Read through each point.
        for (x = 0; x < encoded.length; x += 4) {
            ePoint = encoded.substring(x, x + 4);
            if (ePoint.length !== 4) {
                throw new SignatureError("Coordinate invalid size " + ePoint, pos);
            }
            //Add the point to the stroke.
            points[(x / 4)] = this.decodePoint(ePoint, pos, false, false, fromKbd, toKbd);
            pos += 4;
        }
        //Set the stroke equal to the array of points.
        result.strokes[result.strokes.length] = points;
    }
    if (console && console.time) {
        console.timeEnd("Parsing Signature");
    }
    return result;
};
/**
 * This method uses the registered protocol to attempt to decode a single signature
 * point.
 * @private
 * @method
 * @param ePoint {string} Four encoded characters to attempt to match.
 * @param pos {number} The current position in the current stream, optional, used for error reporting.
 * @param abs {boolean} Return the integer points. Optional.
 * @param decode {boolean} Return the most and least significant bytes of the decoded value. Optional.
 * @param fromKbd {KeyboardSpecification} Keyboard specification the string was taken from. Optional.
 * @param toKbd {KeyboardSpecification} Keyboard specification the string is being converted to. Optional.
 * @return {ScriptelCoordinate} An object containing two members: x and y.
 * These members indicate the position of the point as a relative (percentage-based) position across the screen.
 */
ScriptelEasyScript.prototype.decodePoint = function (ePoint, pos, abs, decode, fromKbd, toKbd) {
    "use strict";
    var d = {"x": [-1, -1], "y": [-1, -1]};

    var p = this.signatureProtocol;
    var i, axis, j, k, code, values;
    for (i = 0; i < ePoint.length; i++) {
        code = ePoint.charCodeAt(i);
        for (axis in p.valueTable) {
            if (p.valueTable.hasOwnProperty(axis)) {
                for (j = 0; j < p.valueTable[axis].length; j++) {
                    values = p.valueTable[axis][j];
                    for (k = 0; k < values.length; k++) {
                        if (values[k] === code) {
                            d[axis][j] = k;
                        }
                    }
                }
            }
        }
    }

    d = this.fixPointCoordinate(ePoint, d, fromKbd, toKbd);
    if (d.x[0] < 0 || d.x[1] < 0 || d.y[0] < 0 || d.y[1] < 0) {
        throw new SignatureError("Invalid point detected, missing code point: x1=" + d.x[0] + "  x2=" + d.x[1] + "  y1=" + d.y[0] + "  y2=" + d.y[1], pos);
    }
    if (decode) {
        return d;
    }

    //Constant, theoretical maximum coordinate.
    var max = (21 * 23) + 22;
    var retr = new ScriptelCoordinate(((d.x[0] * 23) + d.x[1]), ((d.y[0] * 23) + d.y[1]));

    if (abs) {
        return retr;
    }

    //Change the integer values to floats representing percentages.
    retr.x = (retr.x / max) * this.signatureProtocol.width;
    retr.y = (retr.y / max) * this.signatureProtocol.height;

    return retr;
};
/**
 * This method is responsible for trying to intellegently "unjumble" keys from
 * international keyboards that don't have shift-modifiers for certain keys causing
 * converstion to create an invalid point as the unshifted point is used.
 * We'll do this by exploiting the fact that signature points always come in with
 * shifted characters first, followed by unshifted. If we find an unshifted character
 * where a shifted character ought to be we know to correct it.
 * @method
 * @private
 * @param ePoint {string} Four encoded characters to attempt to correct and match.
 * @param point {object<string,int>} High and low bytes as interpreted by decodePoint.
 * @param fromKbd {KeyboardSpecification} In the event international keyboard support is enabled, this will contain the keyboard we're converting from.
 * @param toKbd {KeyboardSpecification} In the event international keyboard support is enabled, this will contain the keyboard we're converting to.
 * @return {object<string,int>} Corrected high and low bytes for X and Y decoded from the corrected encoded point.
 */
ScriptelEasyScript.prototype.fixPointCoordinate = function (ePoint, point, fromKbd, toKbd) {
    "use strict";
    if (!fromKbd || !toKbd) {
        //We lack a keyboard specification to do the translation.
        return point;
    }

    if (!(point.x[0] < 0 || point.x[1] < 0 || point.y[0] < 0 || point.y[1] < 0)) {
        //No correction needed.
        return point;
    }
    var p = this.signatureProtocol;

    var shiftOne = ePoint.charAt(0);
    var shiftTwo = ePoint.charAt(1);
    var normalOne = ePoint.charAt(2);
    var normalTwo = ePoint.charAt(3);

    //First Character
    var key = this.internationalKeyboard.getKey(toKbd, shiftOne);
    if (key.modifier !== "shift") {
        shiftOne = toKbd.map[key.key].shift;
    }

    //Second Character
    key = this.internationalKeyboard.getKey(toKbd, shiftTwo);
    if (key.modifier !== "shift") {
        shiftTwo = toKbd.map[key.key].shift;
    }

    //Third Character
    key = this.internationalKeyboard.getKey(toKbd, normalOne);
    if (key.modifier === "shift") {
        normalOne = toKbd.map[key.key].normal;
    }

    //Forth Character
    key = this.internationalKeyboard.getKey(toKbd, normalTwo);
    if (key.modifier === "shift") {
        normalTwo = toKbd.map[key.key].normal;
    }

    ePoint = shiftOne + shiftTwo + normalOne + normalTwo;

    var d = {"x": [-1, -1], "y": [-1, -1]};
    var i, axis, j, k, code, values;
    for (i = 0; i < ePoint.length; i++) {
        code = ePoint.charCodeAt(i);
        for (axis in p.valueTable) {
            if (p.valueTable.hasOwnProperty(axis)) {
                for (j = 0; j < p.valueTable[axis].length; j++) {
                    values = p.valueTable[axis][j];
                    for (k = 0; k < values.length; k++) {
                        if (values[k] === code) {
                            d[axis][j] = k;
                        }
                    }
                }
            }
        }
    }
    return d;
};
/**
 * This method takes an input string and inverts its case.
 * Called when caps lock is on.
 * @method
 * @private
 * @param str {string} String to invert.
 * @return {string} Inverted string.
 */
ScriptelEasyScript.invertCase = function (str) {
    "use strict";
    if (!str) {
        return str;
    }
    var nStr = "";
    var x, c, u;
    for (x = 0; x < str.length; x++) {
        c = str.charAt(x);
        u = c.toLowerCase();
        if (u !== c) {
            nStr += u;
        } else {
            nStr += c.toUpperCase();
        }
    }
    return nStr;
};
/**
 * This method adds a signature listener to an arbitrary DOM element.
 * The listener will listen for key presses and attempt to intercept
 * anything that looks like a signature stream. Most commonly the
 * listener will be attached to the document object.
 * @method
 * @public
 * @param e {DOMElement} Element from the DOM to attach the event listener to.
 */
ScriptelEasyScript.prototype.addSignatureListener = function (e) {
    "use strict";
    var t = this;
    if (e.addEventListener) {
        e.addEventListener("keypress", function (evt) { 
            t.keyEventHandler(evt);
        }, true);
        e.addEventListener("keydown", function (evt) { 
            t.intlSpaceHandler(evt);
        }, true);
    } else if (e.attachEvent) {
        e.attachEvent("onkeypress", function (evt) {
            t.keyEventHandler(evt);
        });
        e.attachEvent("onkeydown", function (evt) {
            t.intlSpaceHandler(evt);
        });
    }
};
/**
 * This method removes the event listener from a specified DOM object.
 * This is useful if you're no longer interested in intercepting signatures.
 * @method
 * @public
 * @param e {DOMElement} Element from the DOM to detach the event listener from.
 */
ScriptelEasyScript.prototype.removeSignatureListener = function (e) {
    "use strict";
    if (e.removeEventListener) {
        e.removeEventListener("keypress", this.keyEventHandler, true);
        e.removeEventListener("keyup", this.intlSpaceHandler, true);
    } else if (e.attachEvent) {
        e.detachEvent("onkeypress", this.keyEventHandler);
        e.detachEvent("onkeyup", this.intlSpaceHandler);
    }
};

/**
 * This method registers a callback function that will be called when a
 * registered signature listener intercepts and successfully parses
 * a signature stream. The function will be passed a signature object.
 * @method
 * @public
 * @param f {function} Function to be called upon receipt of a signature.
 */
ScriptelEasyScript.prototype.registerSignatureCallback = function (f) {
    "use strict";
    this.callbacks[this.callbacks.length] = f;
};

/**
 * This method unregisters a callback.
 * @method
 * @public
 * @param f {function} Function to unregister.
 */
ScriptelEasyScript.prototype.unregisterSignatureCallback = function (f) {
    "use strict";
    var x;
    for (x = this.callbacks.length - 1; x >= 0; x--) {
        if (this.callbacks[x] === f) {
            this.callbacks.splice(x, 1);
        }
    }
};

/**
 * This method takes a ScriptelSignature and Canvas and attempts to draw
 * the signature on the canvas.
 * @method
 * @public
 * @param sig {ScriptelSignature} Signature to draw on the canvas.
 * @param canvas {DOMElement} DOM element pointing to a canvas that the signature should be drawn on.
 * @param style {object<string,string>} Map of attributes to set on the canvas. For example strokeStyle:blue
 * will change the line color to blue. For a list of other attributes see: {@link https://developer.mozilla.org/en-US/docs/Web/API/CanvasRenderingContext2D#Attributes}.
 */
ScriptelEasyScript.prototype.drawSignatureOnCanvas = function (sig, canvas, style) {
    "use strict";
    if (!sig || !canvas) {
        return;
    }

    if (!style) {
        style = {"strokeStyle": "black", "lineWidth": 1};
    }

    if (console && console.time) {
        console.time("Drawing Signature");
    }

    var scale = canvas.width / this.signatureProtocol.width;
    var ctx = canvas.getContext("2d");
    //Copy canvas style
    var key;
    for (key in style) {
        if (style.hasOwnProperty(key)) {
            ctx[key] = style[key];
        }
    }

    var i, j, pt;
    for (i = 0; i < sig.strokes.length; i++) {
        ctx.beginPath();
        //Move to the initial position.
        pt = sig.strokes[i][0];
        ctx.moveTo(pt.x * scale, pt.y * scale);
        for (j = 1; j < sig.strokes[i].length; j++) {
            pt = sig.strokes[i][j];
            //Stoke to the next point(s)
            ctx.lineTo(pt.x * scale, pt.y * scale);
        }
        ctx.stroke();
    }
    if (console && console.timeEnd) {
        console.timeEnd("Drawing Signature");
    }
};

/**
 * This method is what gets attached as an event handler by addSignatureListener.
 * It listens for interesting key presses and will intercept anything that looks
 * like a signature stream preventing it from propagating to the browser if possible.
 * @method
 * @private
 * @param evt {Event} DOM Event containing information about the key press.
 */
ScriptelEasyScript.prototype.keyboardHandler = function (evt) {
    "use strict";
    var chr = String.fromCharCode(evt.charCode);

    //Firefox specific hacks.
    if (typeof InstallTrigger === "object") {
        //Firefox's Quick Search Doesn't like ' and /
        if (chr === "'" || chr === "/") {
            evt.preventDefault();
        }
        //Firefox also doesn't seem to get \r quite right.
        if (chr === String.fromCharCode(0)) {
            chr = "\r";
        }
    }

    //Allow the application using this library to reconfigure this module if we're not currently
    //capturing.
    if (typeof this.configurationCallback === "function" && !this.intercepting) {
        this.configurationCallback(evt, chr);
    }

    if (!this.intercepting && ((chr === this.translateCharacterTo(this.signatureProtocol.startStream)) || (chr === this.translateCharacterTo(this.cardSwipeProtocol.startStream)))) {
        this.lastProtocol = (chr === this.translateCharacterTo(this.signatureProtocol.startStream)) ? this.signatureProtocol : this.cardSwipeProtocol;
        this.intercepting = true;
        this.lastKey = Date.now();
        if (console && console.time) {
            console.time("Capturing Keyboard Events");
        }
    }

    var p = this.lastProtocol;

    if (this.intercepting) {
        if (Date.now() - this.lastKey > this.timeout) {
            //We're no longer intercepting because the timeout has expired.
            this.intercepting = false;
            this.buffer = "";
        } else {
            this.buffer += chr;
            if (this.lastKeySpace && chr !== " ") {
                this.buffer += " ";
            }
        }

        //Prevent the event from firing further if we can.
        if (this.intercepting && evt.cancelable) {
            evt.preventDefault();
        }
        if (chr.charCodeAt(0) === this.translateCharacterTo(p.endStream).charCodeAt(0)) {
            this.intercepting = false;
            this.lastProtocol = false;
            if (console && console.timeEnd) {
                console.timeEnd("Capturing Keyboard Events");
            }
            var event = false;
            try {
                event = this.parseEvent(this.buffer);
            } catch (e) {
                if (console && console.warn) {
                    console.warn("Intercepting what looked like a signature, but an exception was thrown while parsing: ", e);
                }
            }
            if (event) {
                var x;
                for (x = 0; x < this.callbacks.length; x++) {
                    this.callbacks[x](event);
                }
            }
            this.buffer = "";
        }
        this.lastKey = Date.now();
    }
};

/**
 * This method is an event handler for keydown events. This is used in the event
 * international keyboard support is enabled to catch spaces following dead keys
 * which whould normally be lost.
 * @method
 * @private
 * @param evt {KeyboardEvent} Keyboard Event
 */
ScriptelEasyScript.prototype.intlSpaceHandler = function (evt) {
    "use strict";
    if (evt.keyCode === 32) {
        this.lastKeySpace = true;
    } else {
        this.lastKeySpace = false;
    }
};

/**
 * This method takes a signature and converts it to a Base64 encoded data url
 * containing a Scalable Vector Graphics image.
 * @method
 * @public
 * @param sig {ScriptelSignature} Signature to encode.
 * @param scaleFactor {number} Number by which to uniformally scale the signature up or down.
 */
ScriptelEasyScript.prototype.getBase64EncodedSVG = function (sig, scaleFactor) {
    "use strict";
    var width = this.signatureProtocol.width;
    var height = this.signatureProtocol.height;
    var scale = 1;
    if (scaleFactor) {
        scale = scaleFactor;
    }

    var round = function (number, decimals) {
        var multiplier = Math.pow(10, decimals);
        number *= multiplier;
        return Math.round(number) / multiplier;
    };

    var svg = "<svg xmlns=\"http://www.w3.org/2000/svg\" version=\"1.1\" width=\"" + (width * scaleFactor) + "\" height=\"" + (height * scaleFactor) + "\">\n";

    var i, j;
    svg += "<path d=\"";
    for (i = 0; i < sig.strokes.length; i++) {
        //Move to an absolute position
        svg += "M" +  round((sig.strokes[i][0].x * scale), 1) + " " + round((sig.strokes[i][0].y * scale), 1);
        for (j = 0; j < sig.strokes[i].length - 1; j++) {
            //This implementation uses relative paths, absolute paths would use L
            svg += "l" + round((sig.strokes[i][j + 1].x * scale) - (sig.strokes[i][j].x * scale), 1) + " " + round((sig.strokes[i][j + 1].y * scale) - (sig.strokes[i][j].y * scale), 1);
        }
    }
    svg += "\" style=\"stroke-linecap: round;fill:none;\" stroke=\"#000000\" />";
    svg += "</svg>";
    svg = ScriptelEasyScript.btoa(svg);
    return "data:image/svg+xml;base64," + svg;

};

ScriptelEasyScript.btoa = function (data) {
    "use strict";
   /** @preserve
    * base64 encoder
    * MIT, GPL
    * http://phpjs.org/functions/base64_encode
    * + original by: Tyler Akins (http://rumkin.com)
    * + improved by: Bayron Guevara
    * + improved by: Thunder.m
    * + improved by: Kevin van Zonneveld (http://kevin.vanzonneveld.net)
    * + bugfixed by: Pellentesque Malesuada
    * + improved by: Kevin van Zonneveld (http://kevin.vanzonneveld.net)
    * + improved by: Rafal Kukawski (http://kukawski.pl)
    */
    var b64 = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/=", b64a = b64.split(''), o1, o2, o3, h1, h2, h3, h4, bits, i = 0, ac = 0, enc = "", tmp_arr = [];
    do {
        // pack three octets into four hexets
        o1 = data.charCodeAt(i++);
        o2 = data.charCodeAt(i++);
        o3 = data.charCodeAt(i++);

        bits = o1 << 16 | o2 << 8 | o3;

        h1 = bits >> 18 & 0x3f;
        h2 = bits >> 12 & 0x3f;
        h3 = bits >> 6 & 0x3f;
        h4 = bits & 0x3f;

        // use hexets to index into b64, and append result to encoded string
        tmp_arr[ac++] = b64a[h1] + b64a[h2] + b64a[h3] + b64a[h4];
    } while (i < data.length);

    enc = tmp_arr.join('');
    var r = data.length % 3;
    return (r ? enc.slice(0, r - 3) : enc) + '==='.slice(r || 3);
    /** end of base64 encoder MIT, GPL */
};

/**
 * Assuming the internationalization module is loaded this method attempts
 * to translate a character typed in the "from" keyboard to the "to" keyboard.
 * @method
 * @public
 * @return {string} String containing the translated character.
 */
ScriptelEasyScript.prototype.translateCharacterTo = function (chr) {
    "use strict";
    if (this.fromKeyboardSpec === this.toKeyboardSpec) {
        return chr;
    }
    if (typeof InternationalKeyboard === "function") {
        var key = this.internationalKeyboard.getKey(this.toKeyboardSpec, chr);
        var retr = this.internationalKeyboard.keymaps[this.fromKeyboardSpec].map[key.key][key.modifier];
        if (key) {
            return retr;
        }
    }
    return chr;
};

/**
 * This method gets the bounding box around the current signature.
 * @method
 * @public
 * @return {ScriptelBoundingBox} Bounding box describing the limits of the signature.
 */
ScriptelSignature.prototype.getBounds = function () {
    "use strict";
    var retr = {"x1": Infinity, "x2": -1, "y1": Infinity, "y2": -1, "width": 0, "height": 0};
    var i, j, p;
    for (i = 0; i < this.strokes.length; i++) {
        for (j = 0; j < this.strokes[i].length; j++) {
            p = this.strokes[i][j];

            retr.x1 = (p.x < retr.x1) ? p.x : retr.x1;
            retr.x2 = (p.x > retr.x2) ? p.x : retr.x2;

            retr.y1 = (p.y < retr.y1) ? p.y : retr.y1;
            retr.y2 = (p.y > retr.y2) ? p.y : retr.y2;
        }
    }

    retr.width = retr.x2 - retr.x1;
    retr.height = retr.y2 - retr.y1;

    return retr;
};

/**
 * This method takes a signature and crops it to fit in the smallest
 * amount of space possible.
 * @method
 * @public
 */
ScriptelSignature.prototype.crop = function () {
    "use strict";
    var bounds = this.getBounds();
    var i, j, p;
    for (i = 0; i < this.strokes.length; i++) {
        for (j = 0; j < this.strokes[i].length; j++) {
            p = this.strokes[i][j];
            p.x -= bounds.x1;
            p.y -= bounds.y1;
        }
    }
};
