 /**
 * Constructor, creates a new instance of this type.
 * @classdesc This class is responsible for providing international keyboard support to the
 * JavaScript Keyboard Wedge API. You shouldn't need to do anything with this
 * class directly. If you don't require international keyboard support you do
 * not need to include this file (though it won't hurt anything if you do).
 * @constructor
 */
function InternationalKeyboard() {
    "use strict";
    /**
     * This map contains a listing of support keyboards and associated key
     * mappings.
     * @public
     * @instance
     * @type {object<string,KeyboardSpecification>}
     */
    this.keymaps = {
        "us-basic": {
            "name": "English (US)",
            "map": {
                "TLDE": {"normal": "`", "shift": "~"},
                "AE01": {"normal": "1", "shift": "!"},
                "AE02": {"normal": "2", "shift": "@"},
                "AE03": {"normal": "3", "shift": "#"},
                "AE04": {"normal": "4", "shift": "$"},
                "AE05": {"normal": "5", "shift": "%"},
                "AE06": {"normal": "6", "shift": "^"},
                "AE07": {"normal": "7", "shift": "&"},
                "AE08": {"normal": "8", "shift": "*"},
                "AE09": {"normal": "9", "shift": "("},
                "AE10": {"normal": "0", "shift": ")"},
                "AE11": {"normal": "-", "shift": "_"},
                "AE12": {"normal": "=", "shift": "+"},
                "AD01": {"normal": "q", "shift": "Q"},
                "AD02": {"normal": "w", "shift": "W"},
                "AD03": {"normal": "e", "shift": "E"},
                "AD04": {"normal": "r", "shift": "R"},
                "AD05": {"normal": "t", "shift": "T"},
                "AD06": {"normal": "y", "shift": "Y"},
                "AD07": {"normal": "u", "shift": "U"},
                "AD08": {"normal": "i", "shift": "I"},
                "AD09": {"normal": "o", "shift": "O"},
                "AD10": {"normal": "p", "shift": "P"},
                "AD11": {"normal": "[", "shift": "{"},
                "AD12": {"normal": "]", "shift": "}"},
                "AC01": {"normal": "a", "shift": "A"},
                "AC02": {"normal": "s", "shift": "S"},
                "AC03": {"normal": "d", "shift": "D"},
                "AC04": {"normal": "f", "shift": "F"},
                "AC05": {"normal": "g", "shift": "G"},
                "AC06": {"normal": "h", "shift": "H"},
                "AC07": {"normal": "j", "shift": "J"},
                "AC08": {"normal": "k", "shift": "K"},
                "AC09": {"normal": "l", "shift": "L"},
                "AC10": {"normal": ";", "shift": ":"},
                "AC11": {"normal": "'", "shift": "\""},
                "AB01": {"normal": "z", "shift": "Z"},
                "AB02": {"normal": "x", "shift": "X"},
                "AB03": {"normal": "c", "shift": "C"},
                "AB04": {"normal": "v", "shift": "V"},
                "AB05": {"normal": "b", "shift": "B"},
                "AB06": {"normal": "n", "shift": "N"},
                "AB07": {"normal": "m", "shift": "M"},
                "AB08": {"normal": ",", "shift": "<"},
                "AB09": {"normal": ".", "shift": ">"},
                "AB10": {"normal": "/", "shift": "?"},
                "BKSL": {"normal": "\\", "shift": "|"},
                "SPCE": {"normal": " ", "shift": " "},
                "RTRN": {"normal": "\r", "shift": "\r"}
            }
        },
        "ca-multi": {
            "name": "Multilingual (Canada)",
            "map": {
                "TLDE": {"normal": "/", "shift": "\\", "altgr": "|"},
                "AE01": {"normal": "1", "shift": "!"},
                "AE02": {"normal": "2", "shift": "@"},
                "AE03": {"normal": "3", "shift": "#"},
                "AE04": {"normal": "4", "shift": "$"},
                "AE05": {"normal": "5", "shift": "%"},
                "AE06": {"normal": "6", "shift": "?"},
                "AE07": {"normal": "7", "shift": "&", "altgr": "{"},
                "AE08": {"normal": "8", "shift": "*", "altgr": "}"},
                "AE09": {"normal": "9", "shift": "(", "altgr": "["},
                "AE10": {"normal": "0", "shift": ")", "altgr": "]"},
                "AE11": {"normal": "-", "shift": "_"},
                "AE12": {"normal": "=", "shift": "+", "altgr": "\u00ac"},
                "AD01": {"normal": "q", "shift": "Q", "altgr": "["},
                "AD02": {"normal": "w", "shift": "W"},
                "AD03": {"normal": "e", "shift": "E"},
                "AD04": {"normal": "r", "shift": "R"},
                "AD05": {"normal": "t", "shift": "T"},
                "AD06": {"normal": "y", "shift": "Y"},
                "AD07": {"normal": "u", "shift": "U"},
                "AD08": {"normal": "i", "shift": "I"},
                "AD09": {"normal": "o", "shift": "O"},
                "AD10": {"normal": "p", "shift": "P"},
                "AD11": {"normal": "\u005e", "shift": "\u00a8", "altgr": "{"},
                "AD12": {"normal": "\u00e7", "shift": "\u00c7", "altgr": "}"},
                "AC01": {"normal": "a", "shift": "A"},
                "AC02": {"normal": "s", "shift": "S"},
                "AC03": {"normal": "d", "shift": "D"},
                "AC04": {"normal": "f", "shift": "F"},
                "AC05": {"normal": "g", "shift": "G"},
                "AC06": {"normal": "h", "shift": "H"},
                "AC07": {"normal": "j", "shift": "J"},
                "AC08": {"normal": "k", "shift": "K"},
                "AC09": {"normal": "l", "shift": "L"},
                "AC10": {"normal": ";", "shift": ":", "altgr": "~"},
                "AC11": {"normal": "\u00e8", "shift": "\u00c8"},
                "AB01": {"normal": "z", "shift": "Z"},
                "AB02": {"normal": "x", "shift": "X"},
                "AB03": {"normal": "c", "shift": "C"},
                "AB04": {"normal": "v", "shift": "V"},
                "AB05": {"normal": "b", "shift": "B"},
                "AB06": {"normal": "n", "shift": "N"},
                "AB07": {"normal": "m", "shift": "M"},
                "AB08": {"normal": ",", "shift": "'"},
                "AB09": {"normal": ".", "shift": "\""},
                "AB10": {"normal": "\u00e9", "shift": "\u00c9"},
                "BKSL": {"normal": "\u00e0", "shift": "\u00c0"},
                "SPCE": {"normal": " ", "shift": " "},
                "RTRN": {"normal": "\r", "shift": "\r"}
            },
            "compositeKeys": {
                //Dead Circumflex Composites:
                //A with Circumflex
                "\u00c2": [{"modifier": "normal", "key": "AD11"}, {"modifier": "shift", "key": "AC01"}],
                //E with Circumflex
                "\u00ca": [{"modifier": "normal", "key": "AD11"}, {"modifier": "shift", "key": "AD03"}],
                //I with Circumflex
                "\u00ce": [{"modifier": "normal", "key": "AD11"}, {"modifier": "shift", "key": "AD08"}],
                //O with Circumflex
                "\u00d4": [{"modifier": "normal", "key": "AD11"}, {"modifier": "shift", "key": "AD09"}],
                //U with Circumflex
                "\u00db": [{"modifier": "normal", "key": "AD11"}, {"modifier": "shift", "key": "AD07"}],
                //a with Circumflex
                "\u00e2": [{"modifier": "normal", "key": "AD11"}, {"modifier": "normal", "key": "AC01"}],
                //e with Circumflex
                "\u00ea": [{"modifier": "normal", "key": "AD11"}, {"modifier": "normal", "key": "AD03"}],
                //i with Circumflex
                "\u00ee": [{"modifier": "normal", "key": "AD11"}, {"modifier": "normal", "key": "AD08"}],
                //o with Circumflex
                "\u00f4": [{"modifier": "normal", "key": "AD11"}, {"modifier": "normal", "key": "AD09"}],
                //u with Circumflex
                "\u00fb": [{"modifier": "normal", "key": "AD11"}, {"modifier": "normal", "key": "AD07"}],

                //C with Circumflex
                "\u0108": [{"modifier": "normal", "key": "AD11"}, {"modifier": "shift", "key": "AB03"}],
                //c with Circumflex
                "\u0109": [{"modifier": "normal", "key": "AD11"}, {"modifier": "normal", "key": "AB03"}],
                //G with Circumflex
                "\u011c": [{"modifier": "normal", "key": "AD11"}, {"modifier": "shift", "key": "AC05"}],
                //g with Circumflex
                "\u011d": [{"modifier": "normal", "key": "AD11"}, {"modifier": "normal", "key": "AC05"}],
                //H with Circumflex
                "\u0124": [{"modifier": "normal", "key": "AD11"}, {"modifier": "shift", "key": "AC06"}],
                //h with Circumflex
                "\u0125": [{"modifier": "normal", "key": "AD11"}, {"modifier": "normal", "key": "AC06"}],
                //J with Circumflex
                "\u0134": [{"modifier": "normal", "key": "AD11"}, {"modifier": "shift", "key": "AC07"}],
                //j with Circumflex
                "\u0135": [{"modifier": "normal", "key": "AD11"}, {"modifier": "normal", "key": "AC07"}],
                //S with Circumflex
                "\u015c": [{"modifier": "normal", "key": "AD11"}, {"modifier": "shift", "key": "AC02"}],
                //s with Circumflex
                "\u015d": [{"modifier": "normal", "key": "AD11"}, {"modifier": "normal", "key": "AC02"}],
                //W with Circumflex
                "\u0174": [{"modifier": "normal", "key": "AD11"}, {"modifier": "shift", "key": "AD02"}],
                //w with Circumflex
                "\u0175": [{"modifier": "normal", "key": "AD11"}, {"modifier": "normal", "key": "AD02"}],
                //Y with Circumflex
                "\u0176": [{"modifier": "normal", "key": "AD11"}, {"modifier": "shift", "key": "AD06"}],
                //y with Circumflex
                "\u0177": [{"modifier": "normal", "key": "AD11"}, {"modifier": "normal", "key": "AD06"}],


                //Dead Diaeresis Composites:
                //A with Diaeresis
                "\u00c4": [{"modifier": "shift", "key": "AD11"}, {"modifier": "shift", "key": "AC01"}],
                //a with Diaeresis
                "\u00e4": [{"modifier": "shift", "key": "AD11"}, {"modifier": "normal", "key": "AC01"}],
                //E with Diaeresis
                "\u00cb": [{"modifier": "shift", "key": "AD11"}, {"modifier": "shift", "key": "AD03"}],
                //E with Diaeresis
                "\u00eb": [{"modifier": "shift", "key": "AD11"}, {"modifier": "normal", "key": "AD03"}],
                //I with Diaeresis
                "\u00cf": [{"modifier": "shift", "key": "AD11"}, {"modifier": "shift", "key": "AD08"}],
                //i with Diaeresis
                "\u00ef": [{"modifier": "shift", "key": "AD11"}, {"modifier": "normal", "key": "AD08"}],
                //O with Diaeresis
                "\u00d6": [{"modifier": "shift", "key": "AD11"}, {"modifier": "shift", "key": "AD09"}],
                //o with Diaeresis
                "\u00f6": [{"modifier": "shift", "key": "AD11"}, {"modifier": "normal", "key": "AD09"}],
                //U with Diaeresis
                "\u00dc": [{"modifier": "shift", "key": "AD11"}, {"modifier": "shift", "key": "AD07"}],
                //u with Diaeresis
                "\u00fc": [{"modifier": "shift", "key": "AD11"}, {"modifier": "normal", "key": "AD07"}],
                //y with Diaeresis
                "\u00ff": [{"modifier": "shift", "key": "AD11"}, {"modifier": "normal", "key": "AD06"}]
                }
        },
        "ca-fr": {
            "name": "French (Canada)",
            "map": {
                "TLDE": {"normal": "#", "shift": "|", "altgr": "\\"},
                "AE01": {"normal": "1", "shift": "!"},
                "AE02": {"normal": "2", "shift": "\"", "altgr": "@"},
                "AE03": {"normal": "3", "shift": "/"},
                "AE04": {"normal": "4", "shift": "$"},
                "AE05": {"normal": "5", "shift": "%"},
                "AE06": {"normal": "6", "shift": "?"},
                "AE07": {"normal": "7", "shift": "&"},
                "AE08": {"normal": "8", "shift": "*"},
                "AE09": {"normal": "9", "shift": "("},
                "AE10": {"normal": "0", "shift": ")"},
                "AE11": {"normal": "-", "shift": "_"},
                "AE12": {"normal": "=", "shift": "+"},
                "AD01": {"normal": "q", "shift": "Q", "altgr": "["},
                "AD02": {"normal": "w", "shift": "W"},
                "AD03": {"normal": "e", "shift": "E"},
                "AD04": {"normal": "r", "shift": "R"},
                "AD05": {"normal": "t", "shift": "T"},
                "AD06": {"normal": "y", "shift": "Y"},
                "AD07": {"normal": "u", "shift": "U"},
                "AD08": {"normal": "i", "shift": "I"},
                "AD09": {"normal": "o", "shift": "O"},
                "AD10": {"normal": "p", "shift": "P"},
                "AD11": {"normal": "\u005e", "shift": "\u005e", "altgr": "{"},
                "AD12": {"normal": "\u00b8", "shift": "\u00a8", "altgr": "}"},
                "AC01": {"normal": "a", "shift": "A"},
                "AC02": {"normal": "s", "shift": "S"},
                "AC03": {"normal": "d", "shift": "D"},
                "AC04": {"normal": "f", "shift": "F"},
                "AC05": {"normal": "g", "shift": "G"},
                "AC06": {"normal": "h", "shift": "H"},
                "AC07": {"normal": "j", "shift": "J"},
                "AC08": {"normal": "k", "shift": "K"},
                "AC09": {"normal": "l", "shift": "L"},
                "AC10": {"normal": ";", "shift": ":", "altgr": "~"},
                "AC11": {"normal": "`", "shift": "`"},
                "AB01": {"normal": "z", "shift": "Z"},
                "AB02": {"normal": "x", "shift": "X"},
                "AB03": {"normal": "c", "shift": "C"},
                "AB04": {"normal": "v", "shift": "V"},
                "AB05": {"normal": "b", "shift": "B"},
                "AB06": {"normal": "n", "shift": "N"},
                "AB07": {"normal": "m", "shift": "M"},
                "AB08": {"normal": ",", "shift": "'"},
                "AB09": {"normal": ".", "shift": "."},
                "AB10": {"normal": "\u00e9", "shift": "\u00c9"},
                "BKSL": {"normal": "<", "shift": ">", "altgr": "]"},
                "SPCE": {"normal": " ", "shift": " "},
                "RTRN": {"normal": "\r", "shift": "\r"}
            },
            "compositeKeys": {
                //Dead Circumflex Composites:
                //A with Circumflex
                "\u00c2": [{"modifier": "normal", "key": "AD11"}, {"modifier": "shift", "key": "AC01"}],
                //E with Circumflex
                "\u00ca": [{"modifier": "normal", "key": "AD11"}, {"modifier": "shift", "key": "AD03"}],
                //I with Circumflex
                "\u00ce": [{"modifier": "normal", "key": "AD11"}, {"modifier": "shift", "key": "AD08"}],
                //O with Circumflex
                "\u00d4": [{"modifier": "normal", "key": "AD11"}, {"modifier": "shift", "key": "AD09"}],
                //U with Circumflex
                "\u00db": [{"modifier": "normal", "key": "AD11"}, {"modifier": "shift", "key": "AD07"}],
                //a with Circumflex
                "\u00e2": [{"modifier": "normal", "key": "AD11"}, {"modifier": "normal", "key": "AC01"}],
                //e with Circumflex
                "\u00ea": [{"modifier": "normal", "key": "AD11"}, {"modifier": "normal", "key": "AD03"}],
                //i with Circumflex
                "\u00ee": [{"modifier": "normal", "key": "AD11"}, {"modifier": "normal", "key": "AD08"}],
                //o with Circumflex
                "\u00f4": [{"modifier": "normal", "key": "AD11"}, {"modifier": "normal", "key": "AD09"}],
                //u with Circumflex
                "\u00fb": [{"modifier": "normal", "key": "AD11"}, {"modifier": "normal", "key": "AD07"}],

                //Dead Cedilla Composites:
                //C with Cedilla
                "\u00c7": [{"modifier": "normal", "key": "AD12"}, {"modifier": "shift", "key": "AB03"}],
                //c with Cedilla
                "\u00e7": [{"modifier": "normal", "key": "AD12"}, {"modifier": "normal", "key": "AB03"}],

                //Dead Diaeresis Composites:
                //A with Diaeresis
                "\u00c4": [{"modifier": "shift", "key": "AD12"}, {"modifier": "shift", "key": "AC01"}],
                //a with Diaeresis
                "\u00e4": [{"modifier": "shift", "key": "AD12"}, {"modifier": "normal", "key": "AC01"}],
                //E with Diaeresis
                "\u00cb": [{"modifier": "shift", "key": "AD12"}, {"modifier": "shift", "key": "AD03"}],
                //E with Diaeresis
                "\u00eb": [{"modifier": "shift", "key": "AD12"}, {"modifier": "normal", "key": "AD03"}],
                //I with Diaeresis
                "\u00cf": [{"modifier": "shift", "key": "AD12"}, {"modifier": "shift", "key": "AD08"}],
                //i with Diaeresis
                "\u00ef": [{"modifier": "shift", "key": "AD12"}, {"modifier": "normal", "key": "AD08"}],
                //O with Diaeresis
                "\u00d6": [{"modifier": "shift", "key": "AD12"}, {"modifier": "shift", "key": "AD09"}],
                //o with Diaeresis
                "\u00f6": [{"modifier": "shift", "key": "AD12"}, {"modifier": "normal", "key": "AD09"}],
                //U with Diaeresis
                "\u00dc": [{"modifier": "shift", "key": "AD12"}, {"modifier": "shift", "key": "AD07"}],
                //u with Diaeresis
                "\u00fc": [{"modifier": "shift", "key": "AD12"}, {"modifier": "normal", "key": "AD07"}],
                //y with Diaeresis
                "\u00ff": [{"modifier": "shift", "key": "AD12"}, {"modifier": "normal", "key": "AD06"}],

                //Dead Grave Composites:
                //A with Grave
                "\u00c0": [{"modifier": "normal", "key": "AC11"}, {"modifier": "shift", "key": "AC01"}],
                //a with Grave
                "\u00e0": [{"modifier": "normal", "key": "AC11"}, {"modifier": "normal", "key": "AC01"}],
                //E with Grave
                "\u00c8": [{"modifier": "normal", "key": "AC11"}, {"modifier": "shift", "key": "AD03"}],
                //E with Grave
                "\u00e8": [{"modifier": "normal", "key": "AC11"}, {"modifier": "normal", "key": "AD03"}],
                //I with Grave
                "\u00cc": [{"modifier": "normal", "key": "AC11"}, {"modifier": "shift", "key": "AD08"}],
                //i with Grave
                "\u00ec": [{"modifier": "normal", "key": "AC11"}, {"modifier": "normal", "key": "AD08"}],
                //O with Grave
                "\u00d2": [{"modifier": "normal", "key": "AC11"}, {"modifier": "shift", "key": "AD09"}],
                //o with Grave
                "\u00f2": [{"modifier": "normal", "key": "AC11"}, {"modifier": "normal", "key": "AD09"}],
                //U with Grave
                "\u00d9": [{"modifier": "normal", "key": "AC11"}, {"modifier": "shift", "key": "AD07"}],
                //u with Grave
                "\u00f9": [{"modifier": "normal", "key": "AC11"}, {"modifier": "normal", "key": "AD07"}]
            }
        }
    };
}
/**
 * This method attempts to parse a string in a given specification and translate
 * it into a series of keystrokes by looking up each key in the associated table
 * in the passed in keyboard specification. Please note that this cannot be done
 * completely reliably on all keyboards due to the fact that some specifications
 * include keys that don't respond to modifiers making it impossible to
 * distinguish the between the modified and unmodified versions of the keys.
 *
 * This method also attempts to interpret chorded keys that come about as a
 * result of "dead" keys. The only caveat to this is that spaces that come after
 * dead keys will be effectively lost. This cannot be repaired after the string
 * has been captured.
 * 
 * This method will work for most characters/keys, but some additional
 * context-specific repair may be required.
 * @method
 * @private
 * @param keyboardSpec {KeyboardSpecification|string} Either a specification or
 * the identifier of a specification to use to perform the conversion.
 * @param str {string} String to convert into keystrokes.
 * @return {array<Keystroke>} Array of keystrokes representing the parsed
 * signature.
 */
InternationalKeyboard.prototype.parseString = function (keyboardSpec, str) {
    "use strict";
    var spec = false;
    if (typeof keyboardSpec === "object") {
        spec = keyboardSpec;
    } else if (typeof keyboardSpec === "string") {
        spec = this.keymaps[keyboardSpec];
    }

    if (!spec) {
        return false;
    }

    var keystrokes = [];
    var i, j, chr, strokes;
    for (i = 0; i < str.length; i++) {
        chr = str.charAt(i);
        strokes = this.getKeyStrokes(spec, chr);
        if (strokes) {
            for (j = 0; j < strokes.length; j++) {
                keystrokes[keystrokes.length] = strokes[j];
            }
        } else {
            throw new Error("Warning: unable to map :" + chr);
        }
    }

    return keystrokes;
};
/**
 * This method will attempt to get all keystrokes associated with a particular
 * character given a keyboard specification.
 * @method
 * @private
 * @param keyboard {KeyboardSpecification} Keyboard to use to interpret character.
 * @param chr {string} Character to interpret.
 * @return {array<Keystroke>} An array of keystrokes representing the keys
 * required to generate that character.
 */
InternationalKeyboard.prototype.getKeyStrokes = function (keyboard, chr) {
    "use strict";
    var key, keyChar;

    //Look through all of the normal keys.
    key = this.getKey(keyboard, chr);
    if (key) {
        return [key];
    }

    //Nothing found, it's possible this is a chord key.
    if (keyboard.compositeKeys) {
        for (keyChar in keyboard.compositeKeys) {
            if (keyboard.compositeKeys.hasOwnProperty(keyChar)) {
                if (keyChar === chr) {
                    return keyboard.compositeKeys[keyChar];
                }
            }
        }
    }

    //We're unable to map this key. Possibly the wrong keyboard spec?
    return false;
};
/**
 * This method attempts to find a "normal" key for a character in a keyboard
 * specification.
 * @private
 * @method
 * @param keyboardSpec {KeyboardSpecification} Keyboard specification to search for character.
 * @param chr {string} Character to search for.
 * @return {Keystroke} Keystroke if found, false otherwise.
 */
InternationalKeyboard.prototype.getKey = function (keyboardSpec, chr) {
    "use strict";
    var keyboard = false;
    var key, modifier, keyChar, keySpec;
    if (typeof keyboardSpec === "object") {
        keyboard = keyboardSpec;
    } else if (typeof keyboardSpec === "string") {
        keyboard = this.keymaps[keyboardSpec];
    }
    for (key in keyboard.map) {
        if (keyboard.map.hasOwnProperty(key)) {
            keySpec = keyboard.map[key];
            for (modifier in keySpec) {
                if (keySpec.hasOwnProperty(modifier)) {
                    keyChar = keySpec[modifier];
                    if (keyChar === chr) {
                        return { "modifier":  modifier, "key": key };
                    }
                }
            }
        }
    }
    return false;
};
/**
 * This method takes an array of keyboard strokes and attempts to turn it into
 * a string based on the passed in keyboard specification.
 * @method
 * @private
 * @param keyboardSpec {KeyboardSpecification} Keyboard specification to use to
 * convert keystrokes to characters.
 * @param strokes {array<Keystroke>} Keystrokes to interpret.
 * @return {string} String representing the characters generated when keystrokes
 * where interpreted.
 */
InternationalKeyboard.prototype.translateKeystrokes = function (keyboardSpec, strokes) {
    "use strict";
    var spec = false;
    if (typeof keyboardSpec === "object") {
        spec = keyboardSpec;
    } else if (typeof keyboardSpec === "string") {
        spec = this.keymaps[keyboardSpec];
    }

    if (!spec) {
        return false;
    }
    var i;
    var str = "";
    var stroke;
    for (i = 0; i < strokes.length; i++) {
        stroke = strokes[i];
        if (spec.map && spec.map[stroke.key] && spec.map[stroke.key][stroke.modifier]) {
            str += spec.map[stroke.key][stroke.modifier];
        } else {
            throw new Error("Warning: unable to find key with spec " + stroke.key + ":" + stroke.modifier);
        }
    }
    return str;
};
/**
 * This method will attempt to convert a string from one keyboard specification
 * to another.
 * @method
 * @public
 * @param str {string} String to convert from.
 * @param fromSpec {KeyboardSpecification|string} Either a keyboard
 * specification or a string containing the name of a keyboard specification
 * that will be used to convert the characters to keystrokes.
 * @param toSpec {KeyboardSpecification|string} Either a keyboard
 * specification or a string containing the name of a keyboard specification
 * that will be used to convert the keystrokes back to characters.
 * @return {string} String representing the translated string.
 */
InternationalKeyboard.prototype.translate = function (str, fromSpec, toSpec) {
    "use strict";
    var strokes = this.parseString(fromSpec, str);
    if (!strokes) {
        return false;
    }
    return this.translateKeystrokes(toSpec, strokes);
};
