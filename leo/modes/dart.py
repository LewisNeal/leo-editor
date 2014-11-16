# Leo colorizer control file for dart mode.
# This file is in the public domain.

# Properties for dart mode.
properties = {
	"commentEnd": "*/",
	"commentStart": "/*",
	"electricKeys": ":",
	"indentCloseBrackets": "]}",
	"indentNextLine": "\\s*(((if|while)\\s*\\(|else\\s*|else\\s+if\\s*\\(|for\\s*\\(.*\\))[^{;]*)",
	"indentOpenBrackets": "{[",
	"lineComment": "//",
	"unalignedCloseBrackets": ")",
	"unalignedOpenBrackets": "(",
	"unindentThisLine": "^.*(default:\\s*|case.*:.*)$",
	"wordBreakChars": ",+-=<>/?^&*",
}

# Attributes dict for dart_dart_literal1 ruleset.
dart_dart_literal1_attributes_dict = {
	"default": "LITERAL1",
	"digit_re": "",
	"escape": "\\",
	"highlight_digits": "true",
	"ignore_case": "true",
	"no_word_sep": "",
}

# Attributes dict for dart_dart_expression ruleset.
dart_dart_expression_attributes_dict = {
	"default": "LITERAL1",
	"digit_re": "(0x[\\p{XDigit}]+[lL]?|[\\p{Digit}]+(e[\\p{Digit}]*)?[lLdDfF]?)",
	"escape": "\\",
	"highlight_digits": "true",
	"ignore_case": "true",
	"no_word_sep": "",
}

# Attributes dict for dart_dart_expression ruleset.
dart_dart_expression_attributes_dict = {
	"default": "LITERAL1",
	"digit_re": "(0x[\\p{XDigit}]+[lL]?|[\\p{Digit}]+(e[\\p{Digit}]*)?[lLdDfF]?)",
	"escape": "\\",
	"highlight_digits": "true",
	"ignore_case": "false",
	"no_word_sep": "",
}

# Dictionary of attributes dictionaries for dart mode.
attributesDictDict = {
	"dart_dart_expression": dart_dart_expression_attributes_dict,
	"dart_dart_literal1": dart_dart_literal1_attributes_dict,
}

# Keywords dict for dart_dart_literal1 ruleset.
dart_dart_literal1_keywords_dict = {}

# Keywords dict for dart_dart_expression ruleset.
dart_dart_expression_keywords_dict = {
	"assertionerror": "keyword4",
	"badnumberformatexception": "keyword4",
	"bool": "keyword3",
	"clock": "keyword4",
	"closureargumentmismatchexception": "keyword4",
	"collection": "keyword4",
	"comparable": "keyword4",
	"const": "keyword1",
	"date": "keyword4",
	"dispatcher": "keyword4",
	"double": "keyword3",
	"duration": "keyword4",
	"emptyqueueexception": "keyword4",
	"exception": "keyword4",
	"expect": "keyword4",
	"expectexception": "keyword4",
	"fallthrougherror": "keyword4",
	"false": "literal2",
	"function": "keyword4",
	"hashable": "keyword4",
	"hashmap": "keyword4",
	"hashset": "keyword4",
	"illegalaccessexception": "keyword4",
	"illegalargumentexception": "keyword4",
	"illegaljsregexpexception": "keyword4",
	"implements": "keyword1",
	"indexoutofrangeexception": "keyword4",
	"int": "keyword3",
	"integerdivisionbyzeroexception": "keyword4",
	"is": "keyword1",
	"isolate": "keyword4",
	"iterable": "keyword4",
	"iterator": "keyword4",
	"linkedhashmap": "keyword4",
	"list": "keyword4",
	"map": "keyword4",
	"match": "keyword4",
	"math": "keyword4",
	"new": "keyword1",
	"nomoreelementsexception": "keyword4",
	"nosuchmethodexception": "keyword4",
	"notimplementedexception": "keyword4",
	"null": "literal2",
	"nullpointerexception": "keyword4",
	"num": "keyword3",
	"object": "keyword4",
	"objectnotclosureexception": "keyword4",
	"outofmemoryexception": "keyword4",
	"pattern": "keyword4",
	"promise": "keyword4",
	"proxy": "keyword4",
	"queue": "keyword4",
	"receiveport": "keyword4",
	"regexp": "keyword4",
	"sendport": "keyword4",
	"set": "keyword4",
	"stackoverflowexception": "keyword4",
	"stopwatch": "keyword4",
	"string": "keyword4",
	"stringbuffer": "keyword4",
	"strings": "keyword4",
	"super": "literal2",
	"this": "literal2",
	"timezone": "keyword4",
	"true": "literal2",
	"typeerror": "keyword4",
	"unsupportedoperationexception": "keyword4",
	"void": "keyword3",
	"wrongargumentcountexception": "keyword4",
}

# Keywords dict for dart_dart_expression ruleset.
dart_dart_expression_keywords_dict = {
	"abstract": "keyword1",
	"assert": "keyword1",
	"break": "keyword1",
	"case": "keyword1",
	"catch": "keyword1",
	"class": "keyword1",
	"continue": "keyword1",
	"default": "keyword1",
	"do": "keyword1",
	"else": "keyword1",
	"extends": "keyword1",
	"factory": "keyword1",
	"final": "keyword1",
	"finally": "keyword1",
	"for": "keyword1",
	"get": "keyword1",
	"if": "keyword1",
	"import": "keyword1",
	"in": "keyword1",
	"interface": "keyword1",
	"library": "keyword1",
	"negate": "keyword1",
	"operator": "keyword1",
	"return": "keyword1",
	"set": "keyword1",
	"source": "keyword1",
	"static": "keyword1",
	"switch": "keyword1",
	"throw": "keyword1",
	"try": "keyword1",
	"typedef": "keyword1",
	"var": "keyword1",
	"while": "keyword1",
}

# Dictionary of keywords dictionaries for dart mode.
keywordsDictDict = {
	"dart_dart_expression": dart_dart_expression_keywords_dict,
	"dart_dart_literal1": dart_dart_literal1_keywords_dict,
}

# Rules for dart_dart_literal1 ruleset.

def dart_rule0(colorer, s, i):
    return colorer.match_span_regexp(s, i, kind="literal4", begin="\\$\\{", end="}",
        at_line_start=False, at_whitespace_end=False, at_word_start=False,
        delegate="dart::dart_expression",exclude_match=False,
        no_escape=False, no_line_break=False, no_word_break=False)

def dart_rule1(colorer, s, i):
    return colorer.match_seq_regexp(s, i, kind="literal4", regexp="\\$[_a-zA-Z][_a-zA-Z0-9]*",
        at_line_start=False, at_whitespace_end=False, at_word_start=False, delegate="")

# Rules dict for dart_dart_literal1 ruleset.
rulesDict1 = {
	"$": [dart_rule0,dart_rule1,],
}

# Rules for dart_dart_expression ruleset.

def dart_rule2(colorer, s, i):
    return colorer.match_span(s, i, kind="comment3", begin="/**", end="*/",
        at_line_start=False, at_whitespace_end=False, at_word_start=False,
        delegate="",exclude_match=False,
        no_escape=False, no_line_break=False, no_word_break=False)

def dart_rule3(colorer, s, i):
    return colorer.match_span(s, i, kind="comment1", begin="/*", end="*/",
        at_line_start=False, at_whitespace_end=False, at_word_start=False,
        delegate="",exclude_match=False,
        no_escape=False, no_line_break=False, no_word_break=False)

def dart_rule4(colorer, s, i):
    return colorer.match_span(s, i, kind="literal1", begin="@\"\"\"", end="\"\"\"",
        at_line_start=False, at_whitespace_end=False, at_word_start=False,
        delegate="",exclude_match=False,
        no_escape=False, no_line_break=False, no_word_break=False)

def dart_rule5(colorer, s, i):
    return colorer.match_span(s, i, kind="literal1", begin="@'''", end="'''",
        at_line_start=False, at_whitespace_end=False, at_word_start=False,
        delegate="",exclude_match=False,
        no_escape=False, no_line_break=False, no_word_break=False)

def dart_rule6(colorer, s, i):
    return colorer.match_span(s, i, kind="literal1", begin="@\"", end="\"",
        at_line_start=False, at_whitespace_end=False, at_word_start=False,
        delegate="",exclude_match=False,
        no_escape=False, no_line_break=True, no_word_break=False)

def dart_rule7(colorer, s, i):
    return colorer.match_span(s, i, kind="literal1", begin="@'", end="'",
        at_line_start=False, at_whitespace_end=False, at_word_start=False,
        delegate="",exclude_match=False,
        no_escape=False, no_line_break=True, no_word_break=False)

def dart_rule8(colorer, s, i):
    return colorer.match_span(s, i, kind="literal1", begin="\"\"\"", end="\"\"\"",
        at_line_start=False, at_whitespace_end=False, at_word_start=False,
        delegate="dart::dart_literal1",exclude_match=False,
        no_escape=False, no_line_break=False, no_word_break=False)

def dart_rule9(colorer, s, i):
    return colorer.match_span(s, i, kind="literal1", begin="'''", end="'''",
        at_line_start=False, at_whitespace_end=False, at_word_start=False,
        delegate="dart::dart_literal1",exclude_match=False,
        no_escape=False, no_line_break=False, no_word_break=False)

def dart_rule10(colorer, s, i):
    return colorer.match_span(s, i, kind="literal1", begin="\"", end="\"",
        at_line_start=False, at_whitespace_end=False, at_word_start=False,
        delegate="dart::dart_literal1",exclude_match=False,
        no_escape=False, no_line_break=True, no_word_break=False)

def dart_rule11(colorer, s, i):
    return colorer.match_span(s, i, kind="literal1", begin="'", end="'",
        at_line_start=False, at_whitespace_end=False, at_word_start=False,
        delegate="dart::dart_literal1",exclude_match=False,
        no_escape=False, no_line_break=True, no_word_break=False)

def dart_rule12(colorer, s, i):
    return colorer.match_seq(s, i, kind="operator", seq="=",
        at_line_start=False, at_whitespace_end=False, at_word_start=False, delegate="")

def dart_rule13(colorer, s, i):
    return colorer.match_seq(s, i, kind="operator", seq="!",
        at_line_start=False, at_whitespace_end=False, at_word_start=False, delegate="")

def dart_rule14(colorer, s, i):
    return colorer.match_seq(s, i, kind="operator", seq=">=",
        at_line_start=False, at_whitespace_end=False, at_word_start=False, delegate="")

def dart_rule15(colorer, s, i):
    return colorer.match_seq(s, i, kind="operator", seq="<=",
        at_line_start=False, at_whitespace_end=False, at_word_start=False, delegate="")

def dart_rule16(colorer, s, i):
    return colorer.match_seq(s, i, kind="operator", seq="+",
        at_line_start=False, at_whitespace_end=False, at_word_start=False, delegate="")

def dart_rule17(colorer, s, i):
    return colorer.match_seq(s, i, kind="operator", seq="-",
        at_line_start=False, at_whitespace_end=False, at_word_start=False, delegate="")

def dart_rule18(colorer, s, i):
    return colorer.match_seq(s, i, kind="operator", seq="/",
        at_line_start=False, at_whitespace_end=False, at_word_start=False, delegate="")

def dart_rule19(colorer, s, i):
    return colorer.match_seq(s, i, kind="operator", seq="*",
        at_line_start=False, at_whitespace_end=False, at_word_start=False, delegate="")

def dart_rule20(colorer, s, i):
    return colorer.match_seq(s, i, kind="operator", seq=">",
        at_line_start=False, at_whitespace_end=False, at_word_start=False, delegate="")

def dart_rule21(colorer, s, i):
    return colorer.match_seq(s, i, kind="operator", seq="<",
        at_line_start=False, at_whitespace_end=False, at_word_start=False, delegate="")

def dart_rule22(colorer, s, i):
    return colorer.match_seq(s, i, kind="operator", seq="%",
        at_line_start=False, at_whitespace_end=False, at_word_start=False, delegate="")

def dart_rule23(colorer, s, i):
    return colorer.match_seq(s, i, kind="operator", seq="&",
        at_line_start=False, at_whitespace_end=False, at_word_start=False, delegate="")

def dart_rule24(colorer, s, i):
    return colorer.match_seq(s, i, kind="operator", seq="|",
        at_line_start=False, at_whitespace_end=False, at_word_start=False, delegate="")

def dart_rule25(colorer, s, i):
    return colorer.match_seq(s, i, kind="operator", seq="^",
        at_line_start=False, at_whitespace_end=False, at_word_start=False, delegate="")

def dart_rule26(colorer, s, i):
    return colorer.match_seq(s, i, kind="operator", seq="<<",
        at_line_start=False, at_whitespace_end=False, at_word_start=False, delegate="")

def dart_rule27(colorer, s, i):
    return colorer.match_seq(s, i, kind="operator", seq=">>>",
        at_line_start=False, at_whitespace_end=False, at_word_start=False, delegate="")

def dart_rule28(colorer, s, i):
    return colorer.match_seq(s, i, kind="operator", seq=">>",
        at_line_start=False, at_whitespace_end=False, at_word_start=False, delegate="")

def dart_rule29(colorer, s, i):
    return colorer.match_seq(s, i, kind="operator", seq="~/",
        at_line_start=False, at_whitespace_end=False, at_word_start=False, delegate="")

def dart_rule30(colorer, s, i):
    return colorer.match_seq(s, i, kind="operator", seq=".",
        at_line_start=False, at_whitespace_end=False, at_word_start=False, delegate="")

def dart_rule31(colorer, s, i):
    return colorer.match_seq(s, i, kind="operator", seq=";",
        at_line_start=False, at_whitespace_end=False, at_word_start=False, delegate="")

def dart_rule32(colorer, s, i):
    return colorer.match_seq(s, i, kind="operator", seq="]",
        at_line_start=False, at_whitespace_end=False, at_word_start=False, delegate="")

def dart_rule33(colorer, s, i):
    return colorer.match_seq(s, i, kind="operator", seq="[",
        at_line_start=False, at_whitespace_end=False, at_word_start=False, delegate="")

def dart_rule34(colorer, s, i):
    return colorer.match_seq(s, i, kind="operator", seq="}",
        at_line_start=False, at_whitespace_end=False, at_word_start=False, delegate="")

def dart_rule35(colorer, s, i):
    return colorer.match_seq(s, i, kind="operator", seq="{",
        at_line_start=False, at_whitespace_end=False, at_word_start=False, delegate="")

def dart_rule36(colorer, s, i):
    return colorer.match_mark_previous(s, i, kind="function", pattern="(",
        at_line_start=False, at_whitespace_end=False, at_word_start=False, exclude_match=False)

def dart_rule37(colorer, s, i):
    return colorer.match_seq(s, i, kind="operator", seq=")",
        at_line_start=False, at_whitespace_end=False, at_word_start=False, delegate="")

def dart_rule38(colorer, s, i):
    return colorer.match_keywords(s, i)

# Rules dict for dart_dart_expression ruleset.
rulesDict2 = {
	"!": [dart_rule13,],
	"\"": [dart_rule8,dart_rule10,],
	"%": [dart_rule22,],
	"&": [dart_rule23,],
	"'": [dart_rule9,dart_rule11,],
	"(": [dart_rule36,],
	")": [dart_rule37,],
	"*": [dart_rule19,],
	"+": [dart_rule16,],
	"-": [dart_rule17,],
	".": [dart_rule30,],
	"/": [dart_rule2,dart_rule3,dart_rule18,],
	"0": [dart_rule38,],
	"1": [dart_rule38,],
	"2": [dart_rule38,],
	"3": [dart_rule38,],
	"4": [dart_rule38,],
	"5": [dart_rule38,],
	"6": [dart_rule38,],
	"7": [dart_rule38,],
	"8": [dart_rule38,],
	"9": [dart_rule38,],
	";": [dart_rule31,],
	"<": [dart_rule15,dart_rule21,dart_rule26,],
	"=": [dart_rule12,],
	">": [dart_rule14,dart_rule20,dart_rule27,dart_rule28,],
	"@": [dart_rule4,dart_rule5,dart_rule6,dart_rule7,dart_rule38,],
	"A": [dart_rule38,],
	"B": [dart_rule38,],
	"C": [dart_rule38,],
	"D": [dart_rule38,],
	"E": [dart_rule38,],
	"F": [dart_rule38,],
	"G": [dart_rule38,],
	"H": [dart_rule38,],
	"I": [dart_rule38,],
	"J": [dart_rule38,],
	"K": [dart_rule38,],
	"L": [dart_rule38,],
	"M": [dart_rule38,],
	"N": [dart_rule38,],
	"O": [dart_rule38,],
	"P": [dart_rule38,],
	"Q": [dart_rule38,],
	"R": [dart_rule38,],
	"S": [dart_rule38,],
	"T": [dart_rule38,],
	"U": [dart_rule38,],
	"V": [dart_rule38,],
	"W": [dart_rule38,],
	"X": [dart_rule38,],
	"Y": [dart_rule38,],
	"Z": [dart_rule38,],
	"[": [dart_rule33,],
	"]": [dart_rule32,],
	"^": [dart_rule25,],
	"a": [dart_rule38,],
	"b": [dart_rule38,],
	"c": [dart_rule38,],
	"d": [dart_rule38,],
	"e": [dart_rule38,],
	"f": [dart_rule38,],
	"g": [dart_rule38,],
	"h": [dart_rule38,],
	"i": [dart_rule38,],
	"j": [dart_rule38,],
	"k": [dart_rule38,],
	"l": [dart_rule38,],
	"m": [dart_rule38,],
	"n": [dart_rule38,],
	"o": [dart_rule38,],
	"p": [dart_rule38,],
	"q": [dart_rule38,],
	"r": [dart_rule38,],
	"s": [dart_rule38,],
	"t": [dart_rule38,],
	"u": [dart_rule38,],
	"v": [dart_rule38,],
	"w": [dart_rule38,],
	"x": [dart_rule38,],
	"y": [dart_rule38,],
	"z": [dart_rule38,],
	"{": [dart_rule35,],
	"|": [dart_rule24,],
	"}": [dart_rule34,],
	"~": [dart_rule29,],
}

# Rules for dart_dart_expression ruleset.

def dart_rule39(colorer, s, i):
    return colorer.match_seq(s, i, kind="comment2", seq="//-->",
        at_line_start=False, at_whitespace_end=False, at_word_start=False, delegate="")

def dart_rule40(colorer, s, i):
    return colorer.match_eol_span(s, i, kind="comment2", seq="//",
        at_line_start=False, at_whitespace_end=False, at_word_start=False,
        delegate="", exclude_match=False)

def dart_rule41(colorer, s, i):
    return colorer.match_eol_span(s, i, kind="keyword2", seq="#!",
        at_line_start=False, at_whitespace_end=False, at_word_start=False,
        delegate="", exclude_match=False)

def dart_rule42(colorer, s, i):
    return colorer.match_seq(s, i, kind="keyword2", seq="#library",
        at_line_start=False, at_whitespace_end=False, at_word_start=False, delegate="")

def dart_rule43(colorer, s, i):
    return colorer.match_seq(s, i, kind="keyword2", seq="#import",
        at_line_start=False, at_whitespace_end=False, at_word_start=False, delegate="")

def dart_rule44(colorer, s, i):
    return colorer.match_seq(s, i, kind="keyword2", seq="#source",
        at_line_start=False, at_whitespace_end=False, at_word_start=False, delegate="")

def dart_rule45(colorer, s, i):
    return colorer.match_seq(s, i, kind="keyword2", seq="#resource",
        at_line_start=False, at_whitespace_end=False, at_word_start=False, delegate="")

def dart_rule46(colorer, s, i):
    return colorer.match_keywords(s, i)


# Rules dict for dart_dart_expression ruleset.
rulesDict3 = {
	"#": [dart_rule41,dart_rule42,dart_rule43,dart_rule44,dart_rule45,],
	"/": [dart_rule39,dart_rule40,],
	"0": [dart_rule46,],
	"1": [dart_rule46,],
	"2": [dart_rule46,],
	"3": [dart_rule46,],
	"4": [dart_rule46,],
	"5": [dart_rule46,],
	"6": [dart_rule46,],
	"7": [dart_rule46,],
	"8": [dart_rule46,],
	"9": [dart_rule46,],
	"@": [dart_rule46,],
	"A": [dart_rule46,],
	"B": [dart_rule46,],
	"C": [dart_rule46,],
	"D": [dart_rule46,],
	"E": [dart_rule46,],
	"F": [dart_rule46,],
	"G": [dart_rule46,],
	"H": [dart_rule46,],
	"I": [dart_rule46,],
	"J": [dart_rule46,],
	"K": [dart_rule46,],
	"L": [dart_rule46,],
	"M": [dart_rule46,],
	"N": [dart_rule46,],
	"O": [dart_rule46,],
	"P": [dart_rule46,],
	"Q": [dart_rule46,],
	"R": [dart_rule46,],
	"S": [dart_rule46,],
	"T": [dart_rule46,],
	"U": [dart_rule46,],
	"V": [dart_rule46,],
	"W": [dart_rule46,],
	"X": [dart_rule46,],
	"Y": [dart_rule46,],
	"Z": [dart_rule46,],
	"a": [dart_rule46,],
	"b": [dart_rule46,],
	"c": [dart_rule46,],
	"d": [dart_rule46,],
	"e": [dart_rule46,],
	"f": [dart_rule46,],
	"g": [dart_rule46,],
	"h": [dart_rule46,],
	"i": [dart_rule46,],
	"j": [dart_rule46,],
	"k": [dart_rule46,],
	"l": [dart_rule46,],
	"m": [dart_rule46,],
	"n": [dart_rule46,],
	"o": [dart_rule46,],
	"p": [dart_rule46,],
	"q": [dart_rule46,],
	"r": [dart_rule46,],
	"s": [dart_rule46,],
	"t": [dart_rule46,],
	"u": [dart_rule46,],
	"v": [dart_rule46,],
	"w": [dart_rule46,],
	"x": [dart_rule46,],
	"y": [dart_rule46,],
	"z": [dart_rule46,],
}

# x.rulesDictDict for dart mode.
rulesDictDict = {
	"dart_dart_expression": rulesDict3,
	"dart_dart_literal1": rulesDict1,
}

# Import dict for dart mode.
importDict = {
	"dart_dart_expression": ["dart_dart_expression::dart_expression",],
}

