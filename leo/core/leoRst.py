#@+leo-ver=4-thin
#@+node:ekr.20090502071837.3:@thin leoRst.py
#@<< docstring >>
#@+node:ekr.20090502071837.4:<< docstring >>
'''Support for restructured text (rST), adapted from rst3 plugin.

For full documentation, see:
http://webpages.charter.net/edreamleo/rstplugin3.html

To generate documents from rST files, Python's docutils_ module must be
installed. The code will use the SilverCity_ syntax coloring package if is is
available.'''
#@nonl
#@-node:ekr.20090502071837.4:<< docstring >>
#@nl

if 0:
    bwm_file = open("bwm_file", "w")

#@<< imports >>
#@+node:ekr.20090502071837.5:<< imports >>
import leo.core.leoGlobals as g
import leo.core.leoTest as leoTest
import leo.core.leoCommands as commands

import os
import HTMLParser
import pprint
import StringIO
import sys

try:
    import leo.plugins.mod_http as mod_http
except ImportError:
    mod_http = None

try:
    import docutils
    import docutils.parsers.rst
    import docutils.core
    import docutils.io
except ImportError:
    docutils = None

try:
    import SilverCity
except ImportError:
    SilverCity = None
#@-node:ekr.20090502071837.5:<< imports >>
#@nl

#@+others
#@+node:ekr.20090502071837.12:code_block
def code_block (name,arguments,options,
    content,lineno,content_offset,block_text,state,state_machine):

    '''Implement the code-block directive for docutils.'''

    try:
        language = arguments [0]
        # See http://aspn.activestate.com/ASPN/Cookbook/Python/Recipe/252170
        module = SilverCity and getattr(SilverCity,language)
        generator = module and getattr(module,language+"HTMLGenerator")
        if generator:
            io = StringIO.StringIO()
            generator().generate_html(io,'\n'.join(content))
            html = '<div class="code-block">\n%s\n</div>\n' % io.getvalue()
        else:
            html = '<div class="code-block">\n%s\n</div>\n' % '<br>\n'.join(content)
        raw = docutils.nodes.raw('',html,format='html')
        return [raw]
    except Exception: # Return html as shown.  Lines are separated by <br> elements.
        g.es_trace('exception in rst3:code_block()')
        g.es_exception()
        return [None]

# See http://docutils.sourceforge.net/spec/howto/rst-directives.html
code_block.arguments = (
    1, # Number of required arguments.
    0, # Number of optional arguments.
    0) # True if final argument may contain whitespace.

# A mapping from option name to conversion function.
if docutils:
    code_block.options = {
        'language':
        docutils.parsers.rst.directives.unchanged # Return the text argument, unchanged.
    }
    code_block.content = 1 # True if content is allowed.

    # Register the directive with docutils.
    docutils.parsers.rst.directives.register_directive('code-block',code_block)
else:
    code_block.options = {}
#@nonl
#@-node:ekr.20090502071837.12:code_block
#@+node:ekr.20090502071837.14:html parser classes
#@+doc
# The parser classes are used to construct the html code for nodes. The 
# algorithm has two phases:
#     1. In the first phase, the html code for each node is identified.
#     2. The second phase identifies all links and checks if these links need 
# to be modified.
# The first phase of scanning is done by the anchor_hmlParserClass. The second 
# phase of this algorithm is
# done with the link_htmlParserClass.
#@-doc
#@@code
#@<< class linkAnchorParserClass >>
#@+node:ekr.20090502071837.15: << class linkAnchorParserClass >>
class linkAnchorParserClass (HTMLParser.HTMLParser):

    '''
    A class to recognize anchors and links in HTML documents.
    A special marker is the "node_marker" which demarkates the border between 
    node and the next.
    '''

    #@    @+others
    #@+node:ekr.20090502071837.16:__init__
    def __init__(self,rst):

        HTMLParser.HTMLParser.__init__(self) # Init the base class.

        self.rst = rst

        # Set ivars from options.  This works only if we don't change nodes!
        self.node_begin_marker      = rst.getOption('node_begin_marker')
        self.clear_http_attributes  = rst.getOption('clear_http_attributes')

        self.current_file = rst.outputFileName
    #@nonl
    #@-node:ekr.20090502071837.16:__init__
    #@+node:ekr.20090502071837.17:is_anchor
    def is_anchor(self, tag, attrs):
        """
        Check if the current tag is an anchor.
        Returns *all* anchors.
        Works with docutils 0.4
        """

        if tag == 'a':
            return True

        if self.is_node_marker(attrs):
            return True
        return tag == "span"
    #@-node:ekr.20090502071837.17:is_anchor
    #@+node:ekr.20090502071837.18:is_link
    def is_link(self, tag, attrs):
        '''
        Return True if tag, attrs is represents a link.
        '''

        if tag != 'a':
            return False

        result = 'href' in dict(attrs)
        return result
    #@-node:ekr.20090502071837.18:is_link
    #@+node:ekr.20090502071837.19:is_node_marker
    def is_node_marker (self,attrs):
        '''
        Return the name of the anchor, if this is an anchor for the beginning of a node,
        False otherwise.
        '''

        d = dict(attrs)
        result = 'id' in d and d['id'].startswith(self.node_begin_marker)
        if result:
            return d['id']
        return result
    #@-node:ekr.20090502071837.19:is_node_marker
    #@-others
#@nonl
#@-node:ekr.20090502071837.15: << class linkAnchorParserClass >>
#@nl

#@+others
#@+node:ekr.20090502071837.20:class htmlParserClass
class htmlParserClass (linkAnchorParserClass):

    '''
    The responsibility of the html parser is:
        1. Find out which html code belongs to which node.
        2. Keep a stack of open tags which apply to the current node.
        3. Keep a list of tags which should be included in the nodes, even
           though they might be closed.
           The <style> tag is one example of that.

    Later, we have to relocate inter-file links: if a reference to another location
    is in a file, we must change the link.

    '''

    #@    @+others
    #@+node:ekr.20090502071837.21:__init__
    def __init__ (self,rst):

        linkAnchorParserClass.__init__(self,rst) # Init the base class.

        self.stack = None
        # The stack contains lists of the form:
            # [text1, text2, previous].
            # text1 is the opening tag
            # text2 is the closing tag
            # previous points to the previous stack element

        self.node_marker_stack = []
        # self.node_marker_stack.pop() returns True for a closing
        # tag if the opening tag identified an anchor belonging to a vnode.

        self.node_code = []
            # Accumulated html code.
            # Once the hmtl code is assigned a vnode, it is deleted here.

        self.deleted_lines = 0 # Number of lines deleted in self.node_code

        self.endpos_pending = False
        # Do not include self.node_code[0:self.endpos_pending] in the html code.

        self.last_position = None
        # Last position; we must attach html code to this node.

        self.last_marker = None
    #@-node:ekr.20090502071837.21:__init__
    #@+node:ekr.20090502071837.22:handle_starttag
    def handle_starttag (self,tag,attrs):
        '''
        1. Find out if the current tag is an achor.
        2. If it is an anchor, we check if this anchor marks the beginning of a new 
           node
        3. If a new node begins, then we might have to store html code for the previous
           node.
        4. In any case, put the new tag on the stack.
        '''
        is_node_marker = False
        if self.is_anchor(tag,attrs) and self.is_node_marker(attrs):
            is_node_marker = self.is_node_marker(attrs)
            # g.trace(tag,attrs)
            line, column = self.getpos()
            if self.last_position:
                lines = self.node_code [:]
                lines [0] = lines [0] [self.startpos:]
                del lines [line-self.deleted_lines-1:]
                # g.trace('Storing in %s...\n%s' % self.last_position, lines)
                mod_http.get_http_attribute(self.last_position).extend(lines)
                #@            << trace the unknownAttribute >>
                #@+node:ekr.20090502071837.23:<< trace the unknownAttribute >>
                if 0:
                    g.pr("rst3: unknownAttributes[self.http_attributename]")
                    g.pr("For:", self.last_position)
                    pprint.pprint(mod_http.get_http_attribute(self.last_position))
                #@nonl
                #@-node:ekr.20090502071837.23:<< trace the unknownAttribute >>
                #@nl
            if self.deleted_lines < line-1:
                del self.node_code [: line-1-self.deleted_lines]
                self.deleted_lines = line-1
                self.endpos_pending = True
        # g.trace("rst2: handle_starttag:", tag, attrs, is_node_marker)
        starttag = self.get_starttag_text()
        self.stack = [starttag, None, self.stack]
        self.node_marker_stack.append(is_node_marker)
    #@nonl
    #@-node:ekr.20090502071837.22:handle_starttag
    #@+node:ekr.20090502071837.24:handle_endtag
    def handle_endtag(self, tag):
        '''
        1. Set the second element of the current top of stack.
        2. If this is the end tag for an anchor for a node,
           store the current stack for that node.
        '''
        self.stack[1] = "</" + tag + ">"

        # g.trace(tag,g.listToString(self.stack))
        if self.endpos_pending:
            line, column = self.getpos()
            self.startpos = self.node_code[0].find(">", column) + 1
            self.endpos_pending = False

        is_node_marker = self.node_marker_stack.pop()

        if is_node_marker and not self.clear_http_attributes:
            self.last_position = self.rst.http_map[is_node_marker]
            if is_node_marker != self.last_marker:
                # if bwm_file: print >> bwm_file, "Handle endtag:", is_node_marker, self.stack
                mod_http.set_http_attribute(self.rst.http_map[is_node_marker], self.stack)
                self.last_marker = is_node_marker
                #bwm: last_marker is not needed?

        self.stack = self.stack[2]
    #@-node:ekr.20090502071837.24:handle_endtag
    #@+node:ekr.20090502071837.25:feed
    def feed(self, line):

        # g.trace(repr(line))

        self.node_code.append(line)

        HTMLParser.HTMLParser.feed(self, line) # Call the base class's feed().
    #@-node:ekr.20090502071837.25:feed
    #@-others
#@nonl
#@-node:ekr.20090502071837.20:class htmlParserClass
#@+node:ekr.20090502071837.26:class anchor_htmlParserClass
class anchor_htmlParserClass (linkAnchorParserClass):

    '''
    This htmlparser does the first step of relocating: finding all the anchors within the html nodes.

    Each anchor is mapped to a tuple:
        (current_file, position).

    Filters out markers which mark the beginning of the html code for a node.
    '''

    #@    @+others
    #@+node:ekr.20090502071837.27: __init__
    def __init__ (self,rst,p):

        linkAnchorParserClass.__init__(self,rst)

        self.p = p.copy()
        self.anchor_map = rst.anchor_map
    #@-node:ekr.20090502071837.27: __init__
    #@+node:ekr.20090502071837.28:handle_starttag
    def handle_starttag(self, tag, attrs):
        '''
        1. Find out if the current tag is an achor.
        2. If the current tag is an anchor, update the mapping;
             anchor -> (filename, p)
        '''
        if not self.is_anchor(tag, attrs):
            return

        if self.current_file not in self.anchor_map:
            self.anchor_map[self.current_file] = (self.current_file, self.p)
            simple_name = g.os_path_split(self.current_file)[1]
            self.anchor_map[simple_name] = self.anchor_map[self.current_file]
            # if bwm_file: print >> bwm_file, "anchor(1): current_file:", self.current_file, "position:", self.p, "Simple name:", simple_name
            # Not sure what to do here, exactly. Do I need to manipulate
            # the pathname?

        for name, value in attrs:
            if name == 'name' or tag == 'span' and name == 'id':
                if not value.startswith(self.node_begin_marker):
                    # if bwm_file: print >> bwm_file, "anchor(2):", value, self.p
                    self.anchor_map[value] = (self.current_file, self.p.copy())
    #@-node:ekr.20090502071837.28:handle_starttag
    #@-others
#@nonl
#@-node:ekr.20090502071837.26:class anchor_htmlParserClass
#@+node:ekr.20090502071837.29:class link_htmlParserClass
class link_htmlparserClass (linkAnchorParserClass):

    '''This html parser does the second step of relocating links:
    1. It scans the html code for links.
    2. If there is a link which links to a previously processed file
       then this link is changed so that it now refers to the node.
    '''

    #@    @+others
    #@+node:ekr.20090502071837.30:__init__
    def __init__ (self,rst,p):

        linkAnchorParserClass.__init__(self,rst)

        self.p = p.copy()
        self.anchor_map = rst.anchor_map
        self.replacements = []
    #@nonl
    #@-node:ekr.20090502071837.30:__init__
    #@+node:ekr.20090502071837.31:handle_starttag
    def handle_starttag(self, tag, attrs):
        '''
        1. Find out if the current tag is an achor.
        2. If the current tag is an anchor, update the mapping;
             anchor -> p
            Update the list of replacements for the document.
        '''
        # if bwm_file: print >> bwm_file, "Is link?", tag, attrs
        if not self.is_link(tag, attrs):
            return

        marker = self.node_begin_marker
        for name, value in attrs:
            if name == 'href':
                href = value
                href_parts = href.split("#")
                if len(href_parts) == 1:
                    href_a = href_parts[0]
                else:
                    href_a = href_parts[1]
                # if bwm_file: print >> bwm_file, "link(1):", name, value, href_a
                if not href_a.startswith(marker):
                    if href_a in self.anchor_map:
                        href_file, href_node = self.anchor_map[href_a]
                        http_node_ref = mod_http.node_reference(href_node)
                        line, column = self.getpos()
                        # if bwm_file: print >> bwm_file, "link(2):", line, column, href, href_file, http_node_ref
                        self.replacements.append((line, column, href, href_file, http_node_ref))
    #@nonl
    #@-node:ekr.20090502071837.31:handle_starttag
    #@+node:ekr.20090502071837.32:get_replacements
    def get_replacements(self):

        return self.replacements
    #@nonl
    #@-node:ekr.20090502071837.32:get_replacements
    #@-others
#@nonl
#@-node:ekr.20090502071837.29:class link_htmlParserClass
#@-others
#@nonl
#@-node:ekr.20090502071837.14:html parser classes
#@+node:ekr.20090502071837.33:class rstCommands
#@+at
# This plugin optionally stores information for the http plugin. Each node can
# have one additional attribute, with the name rst_http_attributename, which 
# is a
# list. The first three elements are stack of tags, the rest is html code::
# 
#     [<tag n start>, <tag n end>, <other stack elements>, <html line 1>, 
# <html line 2>, ...]
# 
# <other stack elements has the same structure::
# 
#     [<tag n-1 start>, <tag n-1 end>, <other stack elements>]
#@-at
#@@c

class rstCommands:

    '''A class to write rst markup in Leo outlines.'''

    #@    @+others
    #@+node:ekr.20090502071837.34: Birth & init
    #@+node:ekr.20090502071837.35: ctor (rstClass)
    def __init__ (self,c):

        global SilverCity

        self.c = c
        #@    << init ivars >>
        #@+node:ekr.20090502071837.36:<< init ivars >>
        self.silverCityWarningGiven = False

        # The options dictionary.
        self.optionsDict = {}
        self.option_prefix = '@rst-option'

        # Formatting...
        self.code_block_string = ''
        self.node_counter = 0
        self.topLevel = 0
        self.topNode = None
        self.use_alternate_code_block = SilverCity is None

        # Http support...
        self.nodeNumber = 0
        # All nodes are numbered so that unique anchors can be generated.

        self.http_map = {} 
        # Keys are named hyperlink targets.  Value are positions.
        # The targets mark the beginning of the html code specific
        # for this position.

        self.anchor_map = {}
        # Maps anchors (generated by this module) to positions

        self.rst3_all = False
        # Set to True by the button which processes all @rst trees.

        # For writing.
        self.atAutoWrite = False # True, special cases for writeAtAutoFile.
        self.atAutoWriteUnderlines = '' # Forced underlines for writeAtAutoFile.
        self.defaultEncoding = 'utf-8'
        self.leoDirectivesList = g.globalDirectiveList
        self.encoding = self.defaultEncoding
        self.ext = None # The file extension.
        self.outputFileName = None # The name of the file being written.
        self.outputFile = None # The open file being written.
        self.path = '' # The path from any @path directive.
        self.source = None # The written source as a string.
        #@nonl
        #@-node:ekr.20090502071837.36:<< init ivars >>
        #@nl
        self.createDefaultOptionsDict()
        self.initOptionsFromSettings() # Still needed.
        self.initHeadlineCommands() # Only needs to be done once.
        self.initSingleNodeOptions()
    #@-node:ekr.20090502071837.35: ctor (rstClass)
    #@+node:ekr.20090502071837.102: getPublicCommands
    def getPublicCommands (self):        

        c = self.c

        return {
            'rst3': self.rst3, # Formerly write-restructured-text.
        }
    #@-node:ekr.20090502071837.102: getPublicCommands
    #@+node:ekr.20090511055302.5792:finishCreate
    def finishCreate(self):

        c = self.c
        d = self.getPublicCommands()
        c.commandsDict.update(d)
    #@-node:ekr.20090511055302.5792:finishCreate
    #@+node:ekr.20090502071837.38:initHeadlineCommands
    def initHeadlineCommands (self):

        '''Init the list of headline commands used by writeHeadline.'''

        self.headlineCommands = [
            self.getOption('code_prefix'),
            self.getOption('doc_only_prefix'),
            self.getOption('default_path_prefix'),
            self.getOption('rst_prefix'),
            self.getOption('ignore_headline_prefix'),
            self.getOption('ignore_headlines_prefix'),
            self.getOption('ignore_node_prefix'),
            self.getOption('ignore_tree_prefix'),
            self.getOption('option_prefix'),
            self.getOption('options_prefix'),
            self.getOption('show_headline_prefix'),
            # # Suggested by Hemanth P.S.: prevent @file nodes from creating headings.
            # self.getOption('keep_at_file_prefix'),
            # self.getOption('strip_at_file_prefix'),
        ]
    #@nonl
    #@-node:ekr.20090502071837.38:initHeadlineCommands
    #@+node:ekr.20090502071837.39:initSingleNodeOptions
    def initSingleNodeOptions (self):

        self.singleNodeOptions = [
            'ignore_this_headline',
            'ignore_this_node',
            'ignore_this_tree',
            'preformat_this_node',
            'show_this_headline',
        ]
    #@nonl
    #@-node:ekr.20090502071837.39:initSingleNodeOptions
    #@+node:ekr.20090502071837.40:munge
    def munge (self,name):

        '''Convert an option name to the equivalent ivar name.'''

        i = g.choose(name.startswith('rst'),3,0)

        while i < len(name) and name[i].isdigit():
            i += 1

        if i < len(name) and name[i] == '_':
            i += 1

        s = name[i:].lower()
        s = s.replace('-','_')

        return s
    #@nonl
    #@-node:ekr.20090502071837.40:munge
    #@-node:ekr.20090502071837.34: Birth & init
    #@+node:ekr.20090511055302.5793:rst3 command
    def rst3 (self,event=None):

        '''Write all @rst nodes.'''

        # This used to be the called the write-restructured-text command.

        self.processTopTree(self.c.p)
    #@-node:ekr.20090511055302.5793:rst3 command
    #@+node:ekr.20090502071837.41:options...
    #@+node:ekr.20090502071837.42:createDefaultOptionsDict
    def createDefaultOptionsDict(self):

        # Warning: changing the names of options changes the names of the corresponding ivars.

        self.defaultOptionsDict = {
            # Http options...
            'rst3_clear_http_attributes':   False,
            'rst3_http_server_support':     False,
            'rst3_http_attributename':      'rst_http_attribute',
            'rst3_node_begin_marker':       'http-node-marker-',
            # Path options...
            'rst3_default_path': None, # New in Leo 4.4a4 # Bug fix: must be None, not ''.
            'rst3_stylesheet_name': 'default.css',
            'rst3_stylesheet_path': None, # Bug fix: must be None, not ''.
            'rst3_publish_argv_for_missing_stylesheets': None,
            # Global options...
            'rst3_code_block_string': '',
            'rst3_number_code_lines': True,
            'rst3_underline_characters': '''#=+*^~"'`-:><_''',
            'rst3_verbose':True,
            'rst3_write_intermediate_file': False, # Used only if generate_rst is True.
            # Mode options...
            'rst3_code_mode': False, # True: generate rst markup from @code and @doc parts.
            'rst3_doc_only_mode': False, # True: generate only from @doc parts.
            'rst3_generate_rst': True, # True: generate rst markup.  False: generate plain text.
            'rst3_generate_rst_header_comment': True,
                # True generate header comment (requires generate_rst option)
            # Formatting options that apply to both code and rst modes....
            'rst3_show_headlines': True,  # Can be set by @rst-no-head headlines.
            'rst3_show_organizer_nodes': True,
            'rst3_show_options_nodes': False,
            'rst3_show_sections': True,
            'rst3_strip_at_file_prefixes': True,
            'rst3_show_doc_parts_in_rst_mode': True,
            # Formatting options that apply only to code mode.
            'rst3_show_doc_parts_as_paragraphs': False,
            'rst3_show_leo_directives': True,
            'rst3_show_markup_doc_parts': False,
            'rst3_show_options_doc_parts': False,
            # *Names* of headline commands...
            'rst3_code_prefix':             '@rst-code',     # Enter code mode.
            'rst3_doc_only_prefix':         '@rst-doc-only', # Enter doc-only mode.
            'rst3_rst_prefix':              '@rst',          # Enter rst mode.
            'rst3_ignore_headline_prefix':  '@rst-no-head',
            'rst3_ignore_headlines_prefix': '@rst-no-headlines',
            'rst3_ignore_node_prefix':      '@rst-ignore-node',
            'rst3_ignore_prefix':           '@rst-ignore',
            'rst3_ignore_tree_prefix':      '@rst-ignore-tree',
            'rst3_option_prefix':           '@rst-option',
            'rst3_options_prefix':          '@rst-options',
            'rst3_preformat_prefix':        '@rst-preformat',
            'rst3_show_headline_prefix':    '@rst-head',
        }
    #@nonl
    #@-node:ekr.20090502071837.42:createDefaultOptionsDict
    #@+node:ekr.20090502071837.43:dumpSettings (debugging)
    def dumpSettings (self):

        d = self.optionsDict
        keys = d.keys() ; keys.sort()

        g.pr('present settings...')
        for key in keys:
            g.pr('%20s %s' % (key,d.get(key)))
    #@nonl
    #@-node:ekr.20090502071837.43:dumpSettings (debugging)
    #@+node:ekr.20090502071837.44:getOption
    def getOption (self,name):

        bwm = False
        if bwm:
            g.trace("bwm: getOption self:%s, name:%s, value:%s" % (
                self, name, self.optionsDict.get(name)))

        return self.optionsDict.get(name)
    #@nonl
    #@-node:ekr.20090502071837.44:getOption
    #@+node:ekr.20090502071837.45:initCodeBlockString
    def initCodeBlockString(self,p):

        # New in Leo 4.4.4: do this here, not in initWrite:
        c = self.c
        d = c.scanAllDirectives(p)
        language = d.get('language')
        if language is None: language = 'python'
        else: language = language.lower()
        syntax = SilverCity is not None

        # g.trace('language',language,'language.title()',language.title(),p.h)

        s = self.getOption('code_block_string')
        if s:
            self.code_block_string = s.replace('\\n','\n')
        elif syntax and language in ('python','ruby','perl','c'):
            self.code_block_string = '**code**:\n\n.. code-block:: %s\n' % language.title()
        else:
            self.code_block_string = '**code**:\n\n.. class:: code\n..\n\n::\n'
    #@-node:ekr.20090502071837.45:initCodeBlockString
    #@+node:ekr.20090502071837.46:preprocessTree & helpers
    def preprocessTree (self,root):

        self.tnodeOptionDict = {}

        # Bug fix 12/4/05: must preprocess parents too.
        for p in root.parents_iter():
            self.preprocessNode(p)

        for p in root.self_and_subtree_iter():
            self.preprocessNode(p)

        if 0:
            g.trace(root.h)
            for key in self.tnodeOptionDict.keys():
                g.trace(key)
                g.printDict(self.tnodeOptionDict.get(key))
    #@nonl
    #@+node:ekr.20090502071837.47:preprocessNode
    def preprocessNode (self,p):

        d = self.tnodeOptionDict.get(p.v.t)
        if d is None:
            d = self.scanNodeForOptions(p)
            self.tnodeOptionDict [p.v.t] = d
    #@nonl
    #@-node:ekr.20090502071837.47:preprocessNode
    #@+node:ekr.20090502071837.48:parseOptionLine
    def parseOptionLine (self,s):

        '''Parse a line containing name=val and return (name,value) or None.

        If no value is found, default to True.'''

        s = s.strip()
        if s.endswith(','): s = s[:-1]
        # Get name.  Names may contain '-' and '_'.
        i = g.skip_id(s,0,chars='-_')
        name = s [:i]
        if not name: return None
        j = g.skip_ws(s,i)
        if g.match(s,j,'='):
            val = s [j+1:].strip()
            # g.trace(val)
            return name,val
        else:
            # g.trace('*True')
            return name,'True'
    #@nonl
    #@-node:ekr.20090502071837.48:parseOptionLine
    #@+node:ekr.20090502071837.49:scanForOptionDocParts
    def scanForOptionDocParts (self,p,s):

        '''Return a dictionary containing all options from @rst-options doc parts in p.
        Multiple @rst-options doc parts are allowed: this code aggregates all options.
        '''

        d = {} ; n = 0 ; lines = g.splitLines(s)
        while n < len(lines):
            line = lines[n] ; n += 1
            if line.startswith('@'):
                i = g.skip_ws(line,1)
                for kind in ('@rst-options','@rst-option'):
                    if g.match_word(line,i,kind):
                        # Allow options on the same line.
                        line = line[i+len(kind):]
                        d.update(self.scanOption(p,line))
                        # Add options until the end of the doc part.
                        while n < len(lines):
                            line = lines[n] ; n += 1 ; found = False
                            for stop in ('@c','@code', '@'):
                                if g.match_word(line,0,stop):
                                    found = True ; break
                            if found:
                                break
                            else:
                                d.update(self.scanOption(p,line))
                        break
        return d
    #@nonl
    #@-node:ekr.20090502071837.49:scanForOptionDocParts
    #@+node:ekr.20090502071837.50:scanHeadlineForOptions
    def scanHeadlineForOptions (self,p):

        '''Return a dictionary containing the options implied by p's headline.'''

        h = p.h.strip()

        if p == self.topNode:
            return {} # Don't mess with the root node.
        elif g.match_word(h,0,self.getOption('option_prefix')): # '@rst-option'
            s = h [len(self.option_prefix):]
            return self.scanOption(p,s)
        elif g.match_word(h,0,self.getOption('options_prefix')): # '@rst-options'
            return self.scanOptions(p,p.b)
        else:
            # Careful: can't use g.match_word because options may have '-' chars.
            i = g.skip_id(h,0,chars='@-')
            word = h[0:i]

            for prefix,ivar,val in (
                ('code_prefix','code_mode',True), # '@rst-code'
                ('doc_mode_prefix','doc_only_mode',True), # @rst-doc-only.
                ('default_path_prefix','default_prefix',''), # '@rst-default-path'
                ('rst_prefix','code_mode',False), # '@rst'
                ('ignore_headline_prefix','ignore_this_headline',True), # '@rst-no-head'
                ('show_headline_prefix','show_this_headline',True), # '@rst-head'  
                ('ignore_headlines_prefix','show_headlines',False), # '@rst-no-headlines'
                ('ignore_prefix','ignore_this_tree',True),      # '@rst-ignore'
                ('ignore_node_prefix','ignore_this_node',True), # '@rst-ignore-node'
                ('ignore_tree_prefix','ignore_this_tree',True), # '@rst-ignore-tree'
                ('preformat_prefix','preformat_this_node',True), # '@rst-preformat
            ):
                prefix = self.getOption(prefix)
                if prefix and word == prefix: # Do _not_ munge this prefix!
                    d = { ivar: val }
                    if ivar != 'code_mode':
                        d ['code_mode'] = False # Enter rst mode.
                        d ['doc_only_mode'] = False
                    # Special case: Treat a bare @rst like @rst-no-head
                    if h == self.getOption('rst_prefix'):
                        d ['ignore_this_headline'] = True
                    # g.trace(repr(h),repr(prefix),ivar,d)
                    return d

            if h.startswith('@rst'):
                g.trace('word',word,'rst_prefix',self.getOption('rst_prefix'))
                g.trace('unknown kind of @rst headline',p.h)

            return {}
    #@-node:ekr.20090502071837.50:scanHeadlineForOptions
    #@+node:ekr.20090502071837.51:scanNodeForOptions
    def scanNodeForOptions (self,p):

        '''Return a dictionary containing all the option-name:value entries in p.

        Such entries may arise from @rst-option or @rst-options in the headline,
        or from @ @rst-options doc parts.'''

        h = p.h

        d = self.scanHeadlineForOptions(p)

        d2 = self.scanForOptionDocParts(p,p.b)

        # A fine point: body options over-ride headline options.
        d.update(d2)

        return d
    #@nonl
    #@-node:ekr.20090502071837.51:scanNodeForOptions
    #@+node:ekr.20090502071837.52:scanOption
    def scanOption (self,p,s):

        '''Return { name:val } if s is a line of the form name=val.
        Otherwise return {}'''

        if not s.strip() or s.strip().startswith('..'): return {}

        data = self.parseOptionLine(s)

        if data:
            name,val = data
            fullName = 'rst3_' + self.munge(name)
            if fullName in self.defaultOptionsDict.keys():
                if   val.lower() == 'true': val = True
                elif val.lower() == 'false': val = False
                # g.trace('%24s %8s %s' % (self.munge(name),val,p.h))
                return { self.munge(name): val }
            else:
                g.es_print('ignoring unknown option: %s' % (name),color='red')
                return {}
        else:
            g.trace(repr(s))
            s2 = 'bad rst3 option in %s: %s' % (p.h,s)
            g.es_print(s2,color='red')
            return {}
    #@-node:ekr.20090502071837.52:scanOption
    #@+node:ekr.20090502071837.53:scanOptions
    def scanOptions (self,p,s):

        '''Return a dictionary containing all the options in s.'''

        d = {}

        for line in g.splitLines(s):
            d2 = self.scanOption(p,line)
            if d2: d.update(d2)

        return d
    #@nonl
    #@-node:ekr.20090502071837.53:scanOptions
    #@-node:ekr.20090502071837.46:preprocessTree & helpers
    #@+node:ekr.20090502071837.54:scanAllOptions & helpers
    # Once an option is seen, no other related options in ancestor nodes have any effect.

    def scanAllOptions(self,p):

        '''Scan position p and p's ancestors looking for options,
        setting corresponding ivars.
        '''

        self.initOptionsFromSettings() # Must be done on every node.
        self.handleSingleNodeOptions(p)
        seen = self.singleNodeOptions[:] # Suppress inheritance of single-node options.

        # g.trace('-'*20)
        for p in p.self_and_parents_iter():
            d = self.tnodeOptionDict.get(p.v.t,{})
            # g.trace(p.h,d)
            for key in d.keys():
                ivar = self.munge(key)
                if not ivar in seen:
                    seen.append(ivar)
                    val = d.get(key)
                    self.setOption(key,val,p.h)

        # self.dumpSettings()
        if self.rst3_all:
            self.setOption("generate_rst", True, "rst3_all")
            self.setOption("generate_rst_header_comment",True, "rst3_all")
            self.setOption("http_server_support", True, "rst3_all")
            self.setOption("write_intermediate_file", True, "rst3_all")
    #@+node:ekr.20090502071837.55:initOptionsFromSettings
    def initOptionsFromSettings (self):

        c = self.c ; d = self.defaultOptionsDict
        keys = d.keys() ; keys.sort()

        for key in keys:
            for getter,kind in (
                (c.config.getBool,'@bool'),
                (c.config.getString,'@string'),
                (d.get,'default'),
            ):
                val = getter(key)
                if kind == 'default' or val is not None:
                    self.setOption(key,val,'initOptionsFromSettings')
                    break
        # Special case.
        if self.getOption('http_server_support') and not mod_http:
            g.es('No http_server_support: can not import mod_http plugin',color='red')
            self.setOption('http_server_support',False)
    #@-node:ekr.20090502071837.55:initOptionsFromSettings
    #@+node:ekr.20090502071837.56:handleSingleNodeOptions
    def handleSingleNodeOptions (self,p):

        '''Init the settings of single-node options from the tnodeOptionsDict.

        All such options default to False.'''

        d = self.tnodeOptionDict.get(p.v.t, {} )

        for ivar in self.singleNodeOptions:
            val = d.get(ivar,False)
            #g.trace('%24s %8s %s' % (ivar,val,p.h))
            self.setOption(ivar,val,p.h)

    #@-node:ekr.20090502071837.56:handleSingleNodeOptions
    #@-node:ekr.20090502071837.54:scanAllOptions & helpers
    #@+node:ekr.20090502071837.57:setOption
    def setOption (self,name,val,tag):

        # if name == 'rst3_underline_characters':
            # g.trace(name,val,g.callers(4))

        ivar = self.munge(name)

        # bwm = False
        # if bwm:
            # if not self.optionsDict.has_key(ivar):
                # g.trace('init %24s %20s %s %s' % (ivar, val, tag, self))
            # elif self.optionsDict.get(ivar) != val:
                # g.trace('set  %24s %20s %s %s' % (ivar, val, tag, self))

        self.optionsDict [ivar] = val
    #@-node:ekr.20090502071837.57:setOption
    #@-node:ekr.20090502071837.41:options...
    #@+node:ekr.20090502071837.58:write methods (leoRst)
    #@+node:ekr.20090502071837.59: Top-level write code
    #@+node:ekr.20090502071837.60:initWrite
    def initWrite (self,p,encoding=None):

        self.initOptionsFromSettings() # Still needed.

        # Set the encoding from any parent @encoding directive.
        # This can be overridden by @rst-option encoding=whatever.
        c = self.c
        d = c.scanAllDirectives(p)
        self.encoding = encoding or d.get('encoding') or self.defaultEncoding
        self.path = d.get('path') or ''

        # g.trace('path:',self.path)
    #@-node:ekr.20090502071837.60:initWrite
    #@+node:ekr.20090512153903.5803:writeAtAutoFile (rstCommands)
    def writeAtAutoFile (self,p,fileName,outputFile):

        '''Write an @auto tree containing imported rST code.
        The caller will close the output file.'''

        try:
            self.atAutoWrite = True
            self.initAtAutoWrite(p,fileName,outputFile)
            self.topNode = p.copy() # Indicate the top of this tree.
            self.topLevel = p.level()
            after = p.nodeAfterTree()
            p = p.firstChild() # A (temporary?) hack: ignore the root node.
            while p and p != after:
                self.writeNode(p) # side effect: advances p
        finally:
            self.atAutoWrite = False
    #@+node:ekr.20090513073632.5733:setAtAutoWriteOptions
    def initAtAutoWrite(self,p,fileName,outputFile):

        # Set up for a standard write.
        self.createDefaultOptionsDict()
        self.tnodeOptionDict = {}
        self.scanAllOptions(p)
        self.initWrite(p)
        self.preprocessTree(p) # Allow @ @rst-options, for example.

        # Do the overrides.
        self.outputFile = outputFile
        self.outputFileName = fileName

        # Set underlining characters.
        d = self.tnodeOptionDict.get(p.v.t) # Set by preprocessTree.
        underlines = d.get('underline_characters')
        if underlines:
            self.atAutoWriteUnderlines = underlines
        else:
            d = p.v.u.get('rst-import',{})
            underlines2 = d.get('underlines2','#')
            underlines1 = d.get('underlines1','=+*^~"\'`-:><_') # The standard defaults.
            if len(underlines2) > 1:
                underlines2 = underlines2[0]
                g.trace('too many top-level underlines, using %s' % (
                    underlines2),color='blue')
            self.atAutoWriteUnderlines = underlines2 + underlines1
            self.underlines1 = underlines1
            self.underlines2 = underlines2

    #@-node:ekr.20090513073632.5733:setAtAutoWriteOptions
    #@-node:ekr.20090512153903.5803:writeAtAutoFile (rstCommands)
    #@+node:ekr.20090502071837.61:writeNormalTree
    def writeNormalTree (self,p,toString=False):

        self.initWrite(p)

        # Always write to a string first.
        self.outputFile = StringIO.StringIO()
        self.writeTree(p)
        self.source = self.stringOutput = self.outputFile.getvalue()

        # Copy to a file if requested.
        if not toString:
            # Comput the output file name *after* calling writeTree.
            self.outputFileName = self.computeOutputFileName(self.outputFileName)
            self.outputFile = open(self.outputFileName,'w')
            self.outputFile.write(self.stringOutput)
            self.outputFile.close()

        return True
    #@-node:ekr.20090502071837.61:writeNormalTree
    #@+node:ekr.20090502071837.62:processTopTree
    def processTopTree (self,p,justOneFile=False):

        c = self.c ; current = p.copy()

        for p in current.self_and_parents_iter():
            h = p.h
            if h.startswith('@rst') and not h.startswith('@rst-'):
                self.processTree(p,ext=None,toString=False,justOneFile=justOneFile)
                break
        else:
            self.processTree(current,ext=None,toString=False,justOneFile=justOneFile)

        g.es_print('done',color='blue')
    #@nonl
    #@-node:ekr.20090502071837.62:processTopTree
    #@+node:ekr.20090502071837.63:processTree
    def processTree(self,p,ext,toString,justOneFile):

        '''Process all @rst nodes in a tree.'''

        self.preprocessTree(p)
        found = False ; self.stringOutput = ''
        p = p.copy() ; after= p.nodeAfterTree()
        while p and p != after:
            h = p.h.strip()
            if g.match_word(h,0,"@rst"):
                self.outputFileName = h[4:].strip()
                if (
                    (self.outputFileName and self.outputFileName[0] != '-') or
                    (toString and not self.outputFileName)
                ):
                    found = True
                    self.topLevel = p.level() # Define toplevel separately for each rst file.
                    if toString:
                        self.ext = ext
                    else:
                        self.ext = g.os_path_splitext(self.outputFileName)[1].lower()
                    # g.trace('ext',self.ext,self.outputFileName)
                    if self.ext in ('.htm','.html','.tex','.pdf'):
                        ok = self.writeSpecialTree(p,toString=toString,justOneFile=justOneFile)
                    else:
                        ok = self.writeNormalTree(p,toString=toString)
                    self.scanAllOptions(p) # Restore the top-level verbose setting.
                    if toString:
                        return p.copy(),self.stringOutput
                    else:
                        if ok: self.report(self.outputFileName)
                    p.moveToNodeAfterTree()
                else:
                    p.moveToThreadNext()
            else: p.moveToThreadNext()
        if not found:
            g.es('No @rst nodes in selected tree',color='blue')
        return None,None
    #@-node:ekr.20090502071837.63:processTree
    #@+node:ekr.20090502071837.64:writeSpecialTree
    def writeSpecialTree (self,p,toString,justOneFile):

        c = self.c
        isHtml = self.ext in ('.html','.htm')
        if isHtml and not SilverCity:
            if not self.silverCityWarningGiven:
                self.silverCityWarningGiven = True
                g.es('SilverCity not present so no syntax highlighting')

        self.initWrite(p,encoding=g.choose(isHtml,'utf-8','iso-8859-1'))
        self.outputFile = StringIO.StringIO()
        self.writeTree(p)
        self.source = self.outputFile.getvalue()
        self.outputFile = None

        if not toString:
            # Compute this here for use by intermediate file.
            self.outputFileName = self.computeOutputFileName(self.outputFileName)

            # Create the directory if it doesn't exist.
            theDir, junk = g.os_path_split(self.outputFileName)
            theDir = c.os_path_finalize(theDir)
            if not g.os_path_exists(theDir):
                ok = g.makeAllNonExistentDirectories(theDir,c=c,force=False)
                if not ok:
                    g.es_print('did not create:',theDir,color='red')
                    return False

            # if not os.access(theDir,os.F_OK):
                # os.mkdir(theDir)

            if self.getOption('write_intermediate_file'):
                name = self.outputFileName + '.txt'
                f = open(name,'w')
                f.write(self.source)
                f.close()
                self.report(name)

        try:
            output = self.writeToDocutils(self.source)
            ok = True
        except Exception:
            g.pr('Exception in docutils')
            g.es_exception()
            ok = False

        if ok:
            if isHtml:
                import re
                idxTitle = output.find('<title></title>')
                if idxTitle > -1:
                    m = re.search('<h1>([^<]*)</h1>', output)
                    if not m:
                        m = re.search('<h1><[^>]+>([^<]*)</a></h1>', output)
                    if m:
                        output = output.replace(
                            '<title></title>',
                            '<title>%s</title>' % m.group(1)
                        )


            if toString:
                self.stringOutput = output
            else:
                # Write the file to the directory containing the .leo file.
                f = open(self.outputFileName,'w')
                f.write(output)
                f.close()
                self.http_endTree(self.outputFileName, p, justOneFile=justOneFile)

        return ok
    #@-node:ekr.20090502071837.64:writeSpecialTree
    #@+node:ekr.20090502071837.65:writeToDocutils (sets argv) & helper
    def writeToDocutils (self,s):

        '''Send s to docutils using the writer implied by self.ext and return the result.'''

        openDirectory = self.c.frame.openDirectory
        overrides = {'output_encoding': self.encoding }

        # Compute the args list if the stylesheet path does not exist.
        styleSheetArgsDict = self.handleMissingStyleSheetArgs()

        for ext,writer in (
            ('.html','html'),
            ('.htm','html'),
            ('.tex','latex'),
            ('.pdf','leo_pdf'),
        ):
            if self.ext == ext:
                break
        else:
            g.es_print('unknown docutils extension: %s' % (self.ext),color='red')
            return ''

        # Make the stylesheet path relative to the directory containing the output file.
        rel_stylesheet_path = self.getOption('stylesheet_path') or ''

        # New in Leo 4.5: The rel_stylesheet_path is relative to the open directory.
        stylesheet_path = g.os_path_finalize_join(
            self.c.frame.openDirectory,rel_stylesheet_path)

        path = g.os_path_finalize_join(
            stylesheet_path,self.getOption('stylesheet_name'))

        res = ""
        if g.os_path_exists(path):
            if self.ext != '.pdf':
                overrides['stylesheet'] = path
                overrides['stylesheet_path'] = None
        elif styleSheetArgsDict:
            g.es_print('using publish_argv_for_missing_stylesheets',
                styleSheetArgsDict)
            overrides.update(styleSheetArgsDict)
                # MWC add args to settings
        elif rel_stylesheet_path == stylesheet_path:
            g.es_print('stylesheet not found: %s' % (path),color='red')
        else:
            g.es_print('stylesheet not found\n',path,color='red')
            if self.path:g.es_print('@path:', self.path)
            g.es_print('open path:',self.c.frame.openDirectory)
            if rel_stylesheet_path:
                g.es_print('relative path:', rel_stylesheet_path)
        try:
            # All paths now come through here.
            res = docutils.core.publish_string(source=s,
                    reader_name='standalone',
                    parser_name='restructuredtext',
                    writer_name=writer,
                    settings_overrides=overrides)
        except docutils.ApplicationError, error:
            g.es_print('Error (%s): %s' % (error.__class__.__name__, error))
        return res
    #@+node:ekr.20090502071837.66:handleMissingStyleSheetArgs
    def handleMissingStyleSheetArgs (self,s=None):

        '''Parse the publish_argv_for_missing_stylesheets option,
        returning a dict containing the parsed args.'''

        d = {}
        if not s:
            s = self.getOption('publish_argv_for_missing_stylesheets')
        if not s: return d

        args = s.strip()
        if args.find(',') == -1:
            args = [args]
        else:
            args = args.split(',')

        for arg in args:
            data = arg.split('=')
            if len(data) == 1:
                key = data[0]
                d[str(key)] = ""
            elif len(data) == 2:
                key,value = data
                d[str(key)] = str(value)
            else:
                g.es_print('bad option: %s' % s,color='red')
                break

        return d
    #@-node:ekr.20090502071837.66:handleMissingStyleSheetArgs
    #@-node:ekr.20090502071837.65:writeToDocutils (sets argv) & helper
    #@+node:ekr.20090502071837.67:writeNodeToString (New in 4.4.1)
    def writeNodeToString (self,p=None,ext=None):

        '''Scan p's tree (defaults to presently selected tree) looking for @rst nodes.
        Convert the first node found to an ouput of the type specified by ext.

        The @rst may or may not be followed by a filename; the filename is *ignored*,
        and its type does not affect ext or the output generated in any way.

        ext should start with a period:  .html, .tex or None (specifies rst output).

        Returns p, s, where p is the position of the @rst node and s is the converted text.'''

        c = self.c ; current = p or c.p

        for p in current.self_and_parents_iter():
            if p.h.startswith('@rst'):
                return self.processTree(p,ext=ext,toString=True,justOneFile=True)
        else:
            return self.processTree(current,ext=ext,toString=True,justOneFile=True)
    #@nonl
    #@-node:ekr.20090502071837.67:writeNodeToString (New in 4.4.1)
    #@-node:ekr.20090502071837.59: Top-level write code
    #@+node:ekr.20090502071837.68:getDocPart
    def getDocPart (self,lines,n):

        # g.trace('n',n,repr(''.join(lines)))

        result = []
        #@    << Append whatever follows @doc or @space to result >>
        #@+node:ekr.20090502071837.69:<< Append whatever follows @doc or @space to result >>
        if n > 0:
            line = lines[n-1]
            if line.startswith('@doc'):
                s = line[4:].lstrip()
            elif line.startswith('@'):
                s = line[1:].lstrip()
            else:
                s = ''

            # New in Leo 4.4.4: remove these special tags.
            for tag in ('@rst-options','@rst-option','@rst-markup'):
                if g.match_word(s,0,tag):
                    s = s[len(tag):].strip()

            if s.strip():
                result.append(s)
        #@-node:ekr.20090502071837.69:<< Append whatever follows @doc or @space to result >>
        #@nl
        while n < len(lines):
            s = lines [n] ; n += 1
            if g.match_word(s,0,'@code') or g.match_word(s,0,'@c'):
                break
            result.append(s)
        return n, result
    #@nonl
    #@-node:ekr.20090502071837.68:getDocPart
    #@+node:ekr.20090502071837.70:skip_literal_block
    def skip_literal_block (self,lines,n):

        s = lines[n] ; result = [s] ; n += 1
        indent = g.skip_ws(s,0)

        # Skip lines until a non-blank line is found with same or less indent.
        while n < len(lines):
            s = lines[n]
            indent2 = g.skip_ws(s,0)
            if s and not s.isspace() and indent2 <= indent:
                break # We will rescan lines [n]
            n += 1
            result.append(s)

        # g.printList(result,tag='literal block')
        return n, result
    #@nonl
    #@-node:ekr.20090502071837.70:skip_literal_block
    #@+node:ekr.20090502071837.71:writeBody & helpers
    def writeBody (self,p):

        # remove trailing cruft and split into lines.
        ### lines = p.b.rstrip().split('\n')
        lines = g.splitLines(p.b)

        if self.getOption('code_mode'):
            if not self.getOption('show_options_doc_parts'):
                lines = self.handleSpecialDocParts(lines,'@rst-options',
                    retainContents=False)
            if not self.getOption('show_markup_doc_parts'):
                lines = self.handleSpecialDocParts(lines,'@rst-markup',
                    retainContents=False)
            if not self.getOption('show_leo_directives'):
                lines = self.removeLeoDirectives(lines)
            lines = self.handleCodeMode(lines)
        elif self.getOption('doc_only_mode'):
            # New in version 1.15
            lines = self.handleDocOnlyMode(p,lines)
        else:
            lines = self.handleSpecialDocParts(lines,'@rst-options',
                retainContents=False)
            lines = self.handleSpecialDocParts(lines,'@rst-markup',
                retainContents=self.getOption('generate_rst'))
            if self.getOption('show_doc_parts_in_rst_mode') is True:
                pass  # original behaviour, treat as plain text
            elif self.getOption('show_doc_parts_in_rst_mode'):
                # use value as class for content
                lines = self.handleSpecialDocParts(lines,None,
                    retainContents=True, asClass=self.getOption('show_doc_parts_in_rst_mode'))
            else:  # option evaluates to false, cut them out
                lines = self.handleSpecialDocParts(lines,None,
                    retainContents=False)
            lines = self.removeLeoDirectives(lines)
            if self.getOption('generate_rst') and self.getOption('use_alternate_code_block'):
                lines = self.replaceCodeBlockDirectives(lines)

        if 1:
            # Preserve rst whitespace: uses lines = g.splitLines(p.b)
            s = ''.join(lines)
            if not self.atAutoWrite:
                # s += '\n\n' # Make sure all nodes end with a blank line.
                # Don't accumulate more and more trailing newlines!
                s = g.ensureTrailingNewlines(s,2)
            self.write(s)
        else:
            # Old code: uses lines = p.b.rstrip().split('\n')
            s = '\n'.join(lines).strip()
            if s:
                self.write('%s\n\n' % s)
    #@nonl
    #@+node:ekr.20090502071837.72:handleCodeMode & helper
    def handleCodeMode (self,lines):

        '''Handle the preprocessed body text in code mode as follows:

        - Blank lines are copied after being cleaned.
        - @ @rst-markup lines get copied as is.
        - Everything else gets put into a code-block directive.'''

        result = [] ; n = 0 ; code = []
        while n < len(lines):
            s = lines [n] ; n += 1
            if (
                self.isSpecialDocPart(s,'@rst-markup') or
                (self.getOption('show_doc_parts_as_paragraphs') and self.isSpecialDocPart(s,None))
            ):
                if code:
                    self.finishCodePart(result,code)
                    code = []
                result.append('')
                n, lines2 = self.getDocPart(lines,n)
                result.extend(lines2)
            elif not s.strip() and not code:
                pass # Ignore blank lines before the first code block.
            elif not code: # Start the code block.
                result.append('')
                result.append(self.code_block_string)
                code.append(s)
            else: # Continue the code block.
                code.append(s)

        if code:
            self.finishCodePart(result,code)
            code = []
        return self.rstripList(result)
    #@nonl
    #@+node:ekr.20090502071837.73:formatCodeModeLine
    def formatCodeModeLine (self,s,n,numberOption):

        if not s.strip(): s = ''

        if numberOption:
            return '\t%d: %s' % (n,s)
        else:
            return '\t%s' % s
    #@nonl
    #@-node:ekr.20090502071837.73:formatCodeModeLine
    #@+node:ekr.20090502071837.74:rstripList
    def rstripList (self,theList):

        '''Removed trailing blank lines from theList.'''

        s = '\n'.join(theList).rstrip()
        return s.split('\n')
    #@nonl
    #@-node:ekr.20090502071837.74:rstripList
    #@+node:ekr.20090502071837.75:finishCodePart
    def finishCodePart (self,result,code):

        numberOption = self.getOption('number_code_lines')
        code = self.rstripList(code)
        i = 0
        for line in code:
            i += 1
            result.append(self.formatCodeModeLine(line,i,numberOption))
    #@nonl
    #@-node:ekr.20090502071837.75:finishCodePart
    #@-node:ekr.20090502071837.72:handleCodeMode & helper
    #@+node:ekr.20090502071837.76:handleDocOnlyMode
    def handleDocOnlyMode (self,p,lines):

        '''Handle the preprocessed body text in doc_only mode as follows:

        - Blank lines are copied after being cleaned.
        - @ @rst-markup lines get copied as is.
        - All doc parts get copied.
        - All code parts are ignored.'''

        ignore              = self.getOption('ignore_this_headline')
        showHeadlines       = self.getOption('show_headlines')
        showThisHeadline    = self.getOption('show_this_headline')
        showOrganizers      = self.getOption('show_organizer_nodes')

        result = [] ; n = 0
        while n < len(lines):
            s = lines [n] ; n += 1
            if self.isSpecialDocPart(s,'@rst-options'):
                n, lines2 = self.getDocPart(lines,n) # ignore.
            elif self.isAnyDocPart(s):
                # Handle any other doc part, including @rst-markup.
                n, lines2 = self.getDocPart(lines,n)
                if lines2: result.extend(lines2)
        if not result: result = []
        if showHeadlines:
            if result or showThisHeadline or showOrganizers or p == self.topNode:
                # g.trace(len(result),p.h)
                self.writeHeadlineHelper(p)
        return result
    #@nonl
    #@-node:ekr.20090502071837.76:handleDocOnlyMode
    #@+node:ekr.20090502071837.77:isAnyDocPart
    def isAnyDocPart (self,s):

        if s.startswith('@doc'):
            return True
        elif not s.startswith('@'):
            return False
        else:
            return len(s) == 1 or s[1].isspace()
    #@nonl
    #@-node:ekr.20090502071837.77:isAnyDocPart
    #@+node:ekr.20090502071837.78:isSpecialDocPart
    def isSpecialDocPart (self,s,kind):

        '''Return True if s is a special doc part of the indicated kind.

        If kind is None, return True if s is any doc part.'''

        if s.startswith('@') and len(s) > 1 and s[1].isspace():
            if kind:
                i = g.skip_ws(s,1)
                result = g.match_word(s,i,kind)
            else:
                result = True
        elif not kind:
            result = g.match_word(s,0,'@doc') or g.match_word(s,0,'@')
        else:
            result = False

        return result
    #@nonl
    #@-node:ekr.20090502071837.78:isSpecialDocPart
    #@+node:ekr.20090502071837.79:isAnySpecialDocPart
    def isAnySpecialDocPart (self,s):

        for kind in (
            '@rst-markup',
            '@rst-option',
            '@rst-options',
        ):
            if self.isSpecialDocPart(s,kind):
                return True

        return False
    #@-node:ekr.20090502071837.79:isAnySpecialDocPart
    #@+node:ekr.20090502071837.80:removeLeoDirectives
    def removeLeoDirectives (self,lines):

        '''Remove all Leo directives, except within literal blocks.'''

        n = 0 ; result = []
        while n < len(lines):
            s = lines [n] ; n += 1
            if s.strip().endswith('::'):
                n, lit = self.skip_literal_block(lines,n-1)
                result.extend(lit)
            elif s.startswith('@') and not self.isAnySpecialDocPart(s):
                for key in self.leoDirectivesList:
                    if g.match_word(s,0,key):
                        # g.trace('removing %s' % s)
                        break
                else:
                    result.append(s)
            else:
                result.append(s)

        return result
    #@nonl
    #@-node:ekr.20090502071837.80:removeLeoDirectives
    #@+node:ekr.20090502071837.81:handleSpecialDocParts
    def handleSpecialDocParts (self,lines,kind,retainContents,asClass=None):

        # g.trace(kind,g.listToString(lines))

        result = [] ; n = 0
        while n < len(lines):
            s = lines [n] ; n += 1
            if s.strip().endswith('::'):
                n, lit = self.skip_literal_block(lines,n-1)
                result.extend(lit)
            elif self.isSpecialDocPart(s,kind):
                n, lines2 = self.getDocPart(lines,n)
                if retainContents:
                    result.extend([''])
                    if asClass:
                        result.extend(['.. container:: '+asClass, ''])
                        if 'literal' in asClass.split():
                            result.extend(['  ::', ''])
                        for l2 in lines2: result.append('    '+l2)
                    else:
                        result.extend(lines2)
                    result.extend([''])
            else:
                result.append(s)

        return result
    #@-node:ekr.20090502071837.81:handleSpecialDocParts
    #@+node:ekr.20090502071837.82:replaceCodeBlockDirectives
    def replaceCodeBlockDirectives (self,lines):

        '''Replace code-block directive, but not in literal blocks.'''

        n = 0 ; result = []
        while n < len(lines):
            s = lines [n] ; n += 1
            if s.strip().endswith('::'):
                n, lit = self.skip_literal_block(lines,n-1)
                result.extend(lit)
            else:
                i = g.skip_ws(s,0)
                if g.match(s,i,'..'):
                    i = g.skip_ws(s,i+2)
                    if g.match_word(s,i,'code-block'):
                        if 1: # Create a literal block to hold the code.
                            result.append('::\n')
                        else: # This 'annotated' literal block is confusing.
                            result.append('%s code::\n' % s[i+len('code-block'):])
                    else:
                        result.append(s)
                else:
                    result.append(s)

        return result
    #@nonl
    #@-node:ekr.20090502071837.82:replaceCodeBlockDirectives
    #@-node:ekr.20090502071837.71:writeBody & helpers
    #@+node:ekr.20090502071837.83:writeHeadline & helper
    def writeHeadline (self,p):

        '''Generate an rST section if options permit it.
        Remove headline commands from the headline first,
        and never generate an rST section for @rst-option and @rst-options.'''

        docOnly             =  self.getOption('doc_only_mode')
        ignore              = self.getOption('ignore_this_headline')
        showHeadlines       = self.getOption('show_headlines')
        showThisHeadline    = self.getOption('show_this_headline')
        showOrganizers      = self.getOption('show_organizer_nodes')

        if (
            p == self.topNode or
            ignore or
            docOnly or # handleDocOnlyMode handles this.
            not showHeadlines and not showThisHeadline or
            # docOnly and not showOrganizers and not thisHeadline or
            not p.h.strip() and not showOrganizers or
            not p.b.strip() and not showOrganizers
        ):
            return

        self.writeHeadlineHelper(p)
    #@nonl
    #@+node:ekr.20090502071837.84:writeHeadlineHelper
    def writeHeadlineHelper (self,p):

        ### h = p.h.strip()
        h = p.h
        if not self.atAutoWrite:
            h = h.strip()

        # Remove any headline command before writing the headline.
        i = g.skip_ws(h,0) ###
        i = g.skip_id(h,0,chars='@-')
        word = h [:i].strip() ###
        if word:
            # Never generate a section for @rst-option or @rst-options or @rst-no-head.
            if word in (
                self.getOption('option_prefix'),
                self.getOption('options_prefix'),
                self.getOption('ignore_headline_prefix'), # Bug fix: 2009-5-13
                self.getOption('ignore_headlines_prefix'),  # Bug fix: 2009-5-13
            ):
                return
            # Remove all other headline commands from the headline.
            for prefix in self.headlineCommands:
                if word == prefix:
                    h = h [len(word):].strip()
                    break

            # New in Leo 4.4.4.
            if word.startswith('@'):
                if self.getOption('strip_at_file_prefixes'):
                    for s in ('@auto','@file','@nosent','@thin',):
                        if g.match_word(word,0,s):
                            h = h [len(s):].strip()

        if not h.strip(): return

        if self.getOption('show_sections'):
            if self.getOption('generate_rst'):
                self.write(self.underline(h,p)) # Used by @auto-rst.
            else:
                self.write('\n%s\n\n' % h)
        else:
            self.write('\n**%s**\n\n' % h.replace('*',''))
    #@nonl
    #@-node:ekr.20090502071837.84:writeHeadlineHelper
    #@-node:ekr.20090502071837.83:writeHeadline & helper
    #@+node:ekr.20090502071837.85:writeNode
    def writeNode (self,p):

        '''Format a node according to the options presently in effect.'''

        self.initCodeBlockString(p)
        self.scanAllOptions(p)

        if 0:
            g.trace('%24s code_mode %s' % (p.h,self.getOption('code_mode')))

        h = p.h.strip()

        if self.getOption('preformat_this_node'):
            self.http_addNodeMarker(p)
            self.writePreformat(p)
            p.moveToThreadNext()
        elif self.getOption('ignore_this_tree'):
            p.moveToNodeAfterTree()
        elif self.getOption('ignore_this_node'):
            p.moveToThreadNext()
        elif g.match_word(h,0,'@rst-options') and not self.getOption('show_options_nodes'):
            p.moveToThreadNext()
        else:
            self.http_addNodeMarker(p)
            self.writeHeadline(p)
            self.writeBody(p)
            p.moveToThreadNext()
    #@-node:ekr.20090502071837.85:writeNode
    #@+node:ekr.20090502071837.86:writePreformat
    def writePreformat (self,p):

        '''Write p's body text lines as if preformatted.

         ::

            line 1
            line 2 etc.
        '''

        # g.trace(p.h,g.callers())

        lines = p.b.split('\n')
        lines = [' '*4 + z for z in lines]
        lines.insert(0,'::\n')

        s = '\n'.join(lines)
        if s.strip():
            self.write('%s\n\n' % s)
    #@-node:ekr.20090502071837.86:writePreformat
    #@+node:ekr.20090502071837.87:writeTree
    def writeTree(self,p):

        '''Write p's tree to self.outputFile.'''

        self.scanAllOptions(p)

        # g.trace(self.getOption('generate_rst_header_comment'))

        if self.getOption('generate_rst'):
            if self.getOption('generate_rst_header_comment'):
                self.write(self.rstComment(
                    'rst3: filename: %s\n\n' % self.outputFileName))

        # We can't use an iterator because we may skip parts of the tree.
        p = p.copy() # Only one copy is needed for traversal.
        self.topNode = p.copy() # Indicate the top of this tree.
        after = p.nodeAfterTree()
        while p and p != after:
            self.writeNode(p) # Side effect: advances p.
    #@-node:ekr.20090502071837.87:writeTree
    #@-node:ekr.20090502071837.58:write methods (leoRst)
    #@+node:ekr.20090502071837.88:Utils
    #@+node:ekr.20090502071837.89:computeOutputFileName
    def computeOutputFileName (self,fileName):

        openDirectory = self.c.frame.openDirectory
        default_path = self.getOption('default_path')

        if default_path:
            path = g.os_path_finalize_join(self.path,default_path,fileName)
        elif self.path:
            path = g.os_path_finalize_join(self.path,fileName)
        elif openDirectory:
            path = g.os_path_finalize_join(self.path,openDirectory,fileName)
        else:
            path = g.os_path_finalize_join(fileName)

        return path
    #@nonl
    #@-node:ekr.20090502071837.89:computeOutputFileName
    #@+node:ekr.20090502071837.90:encode
    def encode (self,s):

        return g.toEncodedString(s,encoding=self.encoding,reportErrors=True)
    #@nonl
    #@-node:ekr.20090502071837.90:encode
    #@+node:ekr.20090502071837.91:report
    def report (self,name):

        if self.getOption('verbose'):

            name = g.os_path_finalize(name)

            g.es_print('wrote: %s' % (name),color="blue")
    #@nonl
    #@-node:ekr.20090502071837.91:report
    #@+node:ekr.20090502071837.92:rstComment
    def rstComment (self,s):

        return '.. %s' % s
    #@nonl
    #@-node:ekr.20090502071837.92:rstComment
    #@+node:ekr.20090502071837.93:underline (leoRst)
    def underline (self,s,p):

        '''Return the underlining string to be used at the given level for string s.
        This includes the headline, and possibly a leading overlining line.
        '''

        trace = False and not g.unitTesting

        if self.atAutoWrite:
            # We *might* generate overlines for top-level sections.
            u = self.atAutoWriteUnderlines
            level = p.level()-self.topLevel

            # This is tricky. The index n depends on several factors.
            if self.underlines2:
                level -= 1 # There *is* a double-underlined section.
                n = level
            else:
                n = level-1
            if 0 <= n < len(u): ch = u[n]
            else: ch = u[-1]
            n = max(4,len(s))
            if trace: g.trace(self.topLevel,p.level(),level,repr(ch),p.h)
            if level == 0:
                return '%s\n%s\n%s\n' % (ch*n,p.h,ch*n)
            else:
                return '%s\n%s\n' % (p.h,ch*n)
        else:
            # The user is responsible for top-level overlining.
            u = self.getOption('underline_characters') #  '''#=+*^~"'`-:><_'''
            level = max(0,p.level()-self.topLevel)
            level = min(level+1,len(u)-1) # Reserve the first character for explicit titles.
            ch = u [level]
            if trace: g.trace(self.topLevel,p.level(),level,repr(ch),p.h)
            n = max(4,len(s))
            return '%s\n%s\n\n' % (p.h.strip(),ch*n)
    #@-node:ekr.20090502071837.93:underline (leoRst)
    #@+node:ekr.20090502071837.94:write (leoRst)
    def write (self,s):

        s = self.encode(s)

        # g.trace(repr(s),g.callers(2))

        self.outputFile.write(s)
    #@-node:ekr.20090502071837.94:write (leoRst)
    #@-node:ekr.20090502071837.88:Utils
    #@+node:ekr.20090502071837.95:Support for http plugin
    #@+node:ekr.20090502071837.96:http_addNodeMarker
    def http_addNodeMarker (self,p):

        if (
            self.getOption('http_server_support') and
            self.getOption('generate_rst')
        ):
            self.nodeNumber += 1
            anchorname = "%s%s" % (self.getOption('node_begin_marker'),self.nodeNumber)
            s = "\n\n.. _%s:\n\n" % anchorname
            self.write(s)
            self.http_map [anchorname] = p.copy()
            # if bwm_file: print >> bwm_file, "addNodeMarker", anchorname, p
    #@nonl
    #@-node:ekr.20090502071837.96:http_addNodeMarker
    #@+node:ekr.20090502071837.97:http_endTree & helpers
    # Was http_support_main

    def http_endTree (self,filename,p,justOneFile):

        '''Do end-of-tree processing to support the http plugin.'''

        if (
            self.getOption('http_server_support') and
            self.getOption('generate_rst')
        ):
            self.set_initial_http_attributes(filename)
            self.find_anchors(p)
            if justOneFile:
                self.relocate_references(p.self_and_subtree_iter)

            g.es_print('html updated for http plugin',color="blue")

            if self.getOption('clear_http_attributes'):
                g.es_print("http attributes cleared")
    #@nonl
    #@+node:ekr.20090502071837.98:set_initial_http_attributes
    def set_initial_http_attributes (self,filename):

        f = open(filename)
        parser = htmlParserClass(self)

        for line in f.readlines():
            parser.feed(line)

        f.close()
    #@nonl
    #@-node:ekr.20090502071837.98:set_initial_http_attributes
    #@+node:ekr.20090502071837.99:find_anchors
    def find_anchors (self, p):

        '''Find the anchors in all the nodes.'''

        for p1, attrs in self.http_attribute_iter(p):
            html = mod_http.reconstruct_html_from_attrs(attrs)
            # g.trace(pprint.pprint(html))
            parser = anchor_htmlParserClass(self, p1)
            for line in html:
                try:
                    parser.feed(line)
                # bwm: changed to unicode(line)
                except:
                    line = ''.join([ch for ch in line if ord(ch) <= 127])
                    # filter out non-ascii characters.
                    # bwm: not quite sure what's going on here.
                    parser.feed(line)        
        # g.trace(g.dictToString(self.anchor_map,tag='anchor_map'))
    #@nonl
    #@-node:ekr.20090502071837.99:find_anchors
    #@+node:ekr.20090502071837.100:relocate_references
    #@+at 
    #@nonl
    # Relocate references here if we are only running for one file.
    # 
    # Otherwise we must postpone the relocation until we have processed all 
    # files.
    #@-at
    #@@c

    def relocate_references (self, iterator_generator):

        for p in iterator_generator():
            attr = mod_http.get_http_attribute(p)
            if not attr:
                continue
            # g.trace('before',p.h,attr)
            # if bwm_file:
                # print >> bwm_file
                # print >> bwm_file, "relocate_references(1): Position, attr:"
                # pprint.pprint((p, attr), bwm_file)
            http_lines = attr [3:]
            parser = link_htmlparserClass(self,p)
            for line in attr [3:]:
                try:
                    parser.feed(line)
                except:
                    line = ''.join([ch for ch in line if ord(ch) <= 127])
                    parser.feed(line)
            replacements = parser.get_replacements()
            replacements.reverse()
            if not replacements:
                continue
            # if bwm_file:
                # print >> bwm_file, "relocate_references(2): Replacements:"
                # pprint.pprint(replacements, bwm_file)
            for line, column, href, href_file, http_node_ref in replacements:
                # if bwm_file: 
                    # print >> bwm_file, "relocate_references(3): line:", line,
                    # "Column:", column, "href:", href, "href_file:",
                    # href_file, "http_node_ref:", http_node_ref
                marker_parts = href.split("#")
                if len(marker_parts) == 2:
                    marker = marker_parts [1]
                    replacement = u"%s#%s" % (http_node_ref,marker)
                    try:
                        attr [line + 2] = attr [line + 2].replace(u'href="%s"' % href, u'href="%s"' % replacement)
                    except:
                        g.es("Skipped ", attr[line + 2])
                else:
                    filename = marker_parts [0]
                    try:
                        attr [line + 2] = attr [line + 2].replace(u'href="%s"' % href,u'href="%s"' % http_node_ref)
                    except:
                        g.es("Skipped", attr[line+2])
        # g.trace('after %s\n\n\n',attr)
    #@nonl
    #@-node:ekr.20090502071837.100:relocate_references
    #@+node:ekr.20090502071837.101:http_attribute_iter
    def http_attribute_iter (self, p):
        """
        Iterator for all the nodes which have html code.
        Look at the descendents of p.
        Used for relocation.
        """

        for p1 in p.self_and_subtree_iter():
            attr = mod_http.get_http_attribute(p1)
            if attr:
                yield (p1.copy(),attr)
    #@nonl
    #@-node:ekr.20090502071837.101:http_attribute_iter
    #@-node:ekr.20090502071837.97:http_endTree & helpers
    #@-node:ekr.20090502071837.95:Support for http plugin
    #@-others
#@-node:ekr.20090502071837.33:class rstCommands
#@-others
#@-node:ekr.20090502071837.3:@thin leoRst.py
#@-leo
