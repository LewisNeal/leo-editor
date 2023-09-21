#@+leo-ver=5-thin
#@+node:ekr.20230529075138.1: * @file ../plugins/importers/base_importer.py
"""base_importer.py: The base Importer class used by almost all importers."""

#@+<< imports, annotations: base_importer.py >>
#@+node:ekr.20230920091345.1: ** << imports, annotations: base_importer.py >>
from __future__ import annotations
import re
from typing import TYPE_CHECKING
from leo.core import leoGlobals as g

if TYPE_CHECKING:
    from leo.core.leoCommands import Commands as Cmdr
    from leo.core.leoNodes import Position, VNode

#@-<< imports, annotations: base_importer.py >>

class ImporterError(Exception):
    pass

#@+others
#@+node:ekr.20230920130003.1: ** class Block
class Block:

    """A class containing data about imported blocks."""

    def __init__(self,
        kind: str, name: str, start: int, start_body: int, end: int, lines: list[str],
    ) -> None:
        self.child_blocks: list[Block] = []
        self.end = end
        self.kind = kind
        self.lines = lines
        self.name = name
        self.parent_v: VNode = None
        self.start = start
        self.start_body = start_body
        self.v: VNode = None

    #@+others
    #@+node:ekr.20230921061842.1: *3* Block.__repr__
    def __repr__(self) -> str:
        kind_name_s = f"{self.kind} {self.name}"
        parent_v_s = self.parent_v.h if self.parent_v else '<no parent_v>'
        v_s = self.v.h if self.v else '<no v>'
        return (
            f"Block: kind/name: {kind_name_s!r} "
            f"{self.start} {self.start_body} {self.end} "
            f"parent_v: {parent_v_s!r} v: {v_s!r}"
        )

    __str__ = __repr__
    #@+node:ekr.20230921061937.1: *3* Block.dump_lines
    def dump_lines(self) -> None:
        g.printObj(self.lines[self.start:self.end], tag=repr(self))
    #@+node:ekr.20230921061932.1: *3* Block.long_repr
    def long_repr(self) -> str:
        """A longer form of Block.__repr__"""
        child_blocks = []
        for child_block in self.child_blocks:
            child_blocks.append(f"{child_block.kind} {child_block.name}")
        child_blocks_s = '\n'.join(child_blocks) if child_blocks else '<no children>'
        return f"{repr(self)} \nchild_blocks: {child_blocks_s}\n"

    #@-others


#@+node:ekr.20230529075138.4: ** class Importer
class Importer:
    """
    The base class for almost all of Leo's importers.

    Many importers only define `block_patterns` and `language` class ivars.

    Analyzing **guide lines** (lines without comments and strings)
    greatly simplifies this class and all of Leo's importers.

    Subclasses may override the following methods to recognize blocks:

    Override `i.find_blocks` or `i.find_end_of_block1` to tweak `i.gen_block`.
    Override `i.gen_block` for more control.
    Override `i.import_from_string` for complete control.

    Subclasses may override these methods to handle the incoming text:

    Override `i.check_blanks_and tabs` to suppress warnings.
    Override `i.preprocess_lines` to adjust incoming lines.
    Override `i.regularize_whitespace` to allow mixed tabs and spaces.
    """

    # Don't split classes, functions or methods smaller than this value.
    minimum_block_size = 0  # 0: create all blocks.

    # Must be overridden in subclasses.
    language: str = None

    # May be overridden in subclasses.
    allow_preamble = False
    block_patterns: tuple = tuple()
    string_list: list[str] = ['"', "'"]

    #@+others
    #@+node:ekr.20230529075138.5: *3* i.__init__
    def __init__(self, c: Cmdr) -> None:
        """Importer.__init__"""
        assert self.language, g.callers()  # Do not remove.
        self.c = c  # May be None.
        self.root: Position = None
        delims = g.set_delims_from_language(self.language)
        self.single_comment, self.block1, self.block2 = delims
        self.tab_width = 0  # Must be set later.
    #@+node:ekr.20230529075640.1: *3* i: Generic methods: may be overridden
    #@+node:ekr.20230529075138.36: *4* i.check_blanks_and_tabs
    def check_blanks_and_tabs(self, lines: list[str]) -> bool:  # pragma: no cover (missing test)
        """
        Importer.check_blanks_and_tabs.

        Check for intermixed blank & tabs.

        Subclasses may override this method to suppress this check.
        """
        # Do a quick check for mixed leading tabs/blanks.
        fn = g.shortFileName(self.root.h)
        w = self.tab_width
        blanks = tabs = 0
        for s in lines:
            lws = self.get_str_lws(s)
            blanks += lws.count(' ')
            tabs += lws.count('\t')
        # Make sure whitespace matches @tabwidth directive.
        if w < 0:
            ok = tabs == 0
            message = 'tabs found with @tabwidth %s in %s' % (w, fn)
        elif w > 0:
            ok = blanks == 0
            message = 'blanks found with @tabwidth %s in %s' % (w, fn)
        if ok:
            ok = (blanks == 0 or tabs == 0)
            message = 'intermixed blanks and tabs in: %s' % (fn)
        if not ok:
            if g.unitTesting:
                assert False, message
            else:
                g.es(message)
        return ok
    #@+node:ekr.20230529075138.13: *4* i.compute_headline
    def compute_headline(self, block: Block) -> str:
        """
        Importer.compute_headline.

        Return the headline for the given block.

        Subclasses may override this method as necessary.
        """
        name_s = block.name or f"unnamed {block.kind}"
        return f"{block.kind} {name_s}"
    #@+node:ekr.20230612170928.1: *4* i.create_preamble
    def create_preamble(self, parent: Position, result_blocks: list[Block], result_list: list[str]) -> None:
        """
        Importer.create_preamble: Create one preamble node.

        Subclasses may override this method to create multiple preamble nodes.
        """
        assert self.allow_preamble
        assert parent == self.root
        lines = self.lines
        common_lws = self.compute_common_lws(result_blocks)
        new_start = max(0, result_blocks[0].start_body - 1)
        preamble = lines[:new_start]
        if preamble and any(z for z in preamble):
            child = parent.insertAsLastChild()
            section_name = '<< preamble >>'
            child.h = section_name
            child.b = ''.join(preamble)
            result_list.insert(0, f"{common_lws}{section_name}\n")
            # Adjust this block.
            block_0 = result_blocks[0]
            block_0.start = new_start
    #@+node:ekr.20230529075138.10: *4* i.find_blocks
    def find_blocks(self, i1: int, i2: int) -> list[Block]:
        """
        Importer.find_blocks.

        Find all blocks in the given range of *guide* lines.

        Use the patterns in self.block_patterns to find the start the start of a block.

        Subclasses may override this method for more control.

        Return a list of Blocks, that is, tuples(kind, name, start, start_body, end).
        """
        min_size = self.minimum_block_size
        i, prev_i, results = i1, i1, []
        while i < i2:
            s = self.guide_lines[i]
            i += 1
            # Assume that no pattern matches a compound statement.
            for kind, pattern in self.block_patterns:
                m = pattern.match(s)
                if m:
                    ### g.trace('match line', i, repr(m.group(0)))

                    # cython may include trailing whitespace.
                    name = m.group(1).strip()
                    end = self.find_end_of_block(i, i2)
                    assert i1 + 1 <= end <= i2, (i1, end, i2)

                    # Don't generate small blocks.
                    if min_size == 0 or end - prev_i > min_size:
                        block = Block(kind, name, start=prev_i, start_body=i, end=end, lines=self.lines)
                        results.append(block)
                        i = prev_i = end
                    else:
                        i = end
                    break  # Go on to the next line.
        return results
    #@+node:ekr.20230529075138.11: *4* i.find_end_of_block
    def find_end_of_block(self, i: int, i2: int) -> int:
        """
        Importer.find_end_of_block.

        Return the index of end of the block.
        i: The index of the (guide) line *following* the start of the block.
        i2: The index last (guide) line to be scanned.

        This method assumes that that '{' and '}' delimit blocks.
        Subclasses may override this method as necessary.
        """
        trace = False  ###
        level = 1  # All blocks start with '{'
        tag = 'find_end_of_block'
        if trace:
            print(f"  {tag} 1: {i:3} {self.lines[i-1]!r}")
        assert '{' in self.guide_lines[i - 1]
        while i < i2:
            line = self.guide_lines[i]
            i += 1
            for ch in line:
                if ch == '{':
                    level += 1
                if ch == '}':
                    level -= 1
                    if level == 0:
                        if trace:
                            print(f"  {tag} 2: {i:3} {self.lines[i-1]!r}")
                        return i
        return i2
    #@+node:ekr.20230529075138.14: *4* i.gen_block (iterative)
    def gen_block(self, parent: Position) -> None:
        """
        Importer.gen_block.

        Create all descendant blocks and their parent nodes.

        Five importers override this method.
        """
        todo_list: list[Block] = []  # The todo list.
        result_blocks: list[Block] = []

        # Add an outer block to the results list.
        outer_block = Block('outer', 'outer-block', 0, 0, len(self.lines), self.lines)
        result_blocks.append(outer_block)

        # Add all outer blocks to the to-do list.
        todo_list = self.find_blocks(0, len(self.lines))

        # Link the blocks to the outer block.
        for block in todo_list:
            block.parent_v = parent.v
            outer_block.child_blocks.append(block)

        # Handle blocks until the to-do list is empty.
        while todo_list:

            # Get the next block. This will be the parent block of inner blocks.
            block = todo_list.pop(0)
            parent_v = block.parent_v

            # Allocate and set block.v
            child_v = parent_v.insertAsLastChild()
            child_v.h = self.compute_headline(block)
            block.v = child_v

            # The 'VNode' symbol is only available for type checking.
            assert parent_v.__class__.__name__ == 'VNode'
            assert child_v.__class__.__name__ == 'VNode'

            # Add the block to the results.
            result_blocks.append(block)

            # Find the inner blocks.
            inner_blocks = self.find_blocks(block.start_body, block.end)

            # Link inner blocks and add them to the to-do list.
            for inner_block in inner_blocks:
                # We'll set inner_block.v later!
                block.child_blocks.append(inner_block)
                inner_block.parent_v = child_v
                todo_list.append(inner_block)

        # Post pass: generate all bodies
        self.generate_all_bodies(parent, outer_block, result_blocks)

        # Note: i.gen_lines adds the @language and @tabwidth directives.
    #@+node:ekr.20230920165923.1: *5* i.generate_all_bodies
    def generate_all_bodies(self, parent: Position, outer_block: Block, result_blocks: list[Block]) -> None:
        """
        Generate all bodies from the given blocks.

        The outer_block would suffice to do this, but the redundancy allows consistency checks.

        Generating lines in a post-pass is more flexible.
        """

        # Make sure we only process Blocks and VNodes once.
        seen_blocks: dict[Block, bool] = {}
        seen_vnodes: dict[VNode, bool] = {}

        # An initial sanity check.
        if result_blocks:
            block0 = result_blocks[0]
            assert outer_block == block0, (repr(outer_block), repr(block0))

        # Special case the outer block.
        if outer_block.child_blocks:
          # i.gen_lines adds the @language and @tabwidth directives.
            common_lws = self.compute_common_lws(outer_block.child_blocks)
            parent.v.b = f"{common_lws}@others\n"

        # Handle each block, starting from the outer block.
        todo_list: list[Block] = outer_block.child_blocks
        seen_blocks[outer_block] = True
        while todo_list:
            block = todo_list.pop(0)
            ### print(block.long_repr())
            assert isinstance(block, Block), repr(block)
            v = block.v
            assert v.__class__.__name__ == 'VNode', repr(v)

            # Make sure we handle each block once.
            assert block not in seen_blocks, repr(block)
            seen_blocks[block] = True

            # Make sure we handle each vnode once.
            assert v, repr(block)
            assert v not in seen_vnodes, repr(v)
            seen_vnodes[v] = True

            # Create v.b.
            assert self.lines == block.lines

            # Wrong in general. That's why this method exists!!!
            block_lines = block.lines[block.start:block.start_body]
            if block.child_blocks:
                common_lws = self.compute_common_lws(block.child_blocks)
                block_lines.append(f"{common_lws}@others\n")
            block_lines.extend(block.lines[block.start_body:block.end])

            # Delete extra leading and trailing whitespace.
            v.b = ''.join(block_lines).lstrip('\n').rstrip() + '\n'

            # Add all child blocks to the to-do list.
            todo_list.extend(block.child_blocks)

        # Make sure we've seen all blocks and vnodes.
        for block in result_blocks:
            assert block in seen_blocks, block
            if block.v:
                assert block.v in seen_vnodes, repr(block.v)

        if self.allow_preamble:
            result_list: list = []  ### To do.
            # For python.
            self.create_preamble(parent, result_blocks, result_list)
    #@+node:ekr.20230529075138.15: *4* i.gen_lines (top level)
    def gen_lines(self, lines: list[str], parent: Position) -> None:
        """
        Importer.gen_lines: Allocate lines to the parent and descendant nodes.

        Subclasses may override this method, but none do.
        """
        try:
            assert self.root == parent, (self.root, parent)
            self.lines = lines
            # Delete all children.
            parent.deleteAllChildren()
            # Create the guide lines.
            self.guide_lines = self.make_guide_lines(lines)
            n1, n2 = len(self.lines), len(self.guide_lines)
            assert n1 == n2, (n1, n2)
            # Generate all blocks.
            self.gen_block(parent)
        except ImporterError as e:
            g.trace(f"Importer error: {e}")
            parent.deleteAllChildren()
            parent.b = ''.join(lines)
        except Exception:
            g.trace('Unexpected exception!')
            g.es_exception()
            parent.deleteAllChildren()
            parent.b = ''.join(lines)

        # Add trailing lines.
        parent.b += f"@language {self.language}\n@tabwidth {self.tab_width}\n"
    #@+node:ekr.20230529075138.37: *4* i.import_from_string (driver)
    def import_from_string(self, parent: Position, s: str) -> None:
        """
        Importer.import_from_string.

        parent: An @<file> node containing the absolute path to the to-be-imported file.

        s: The contents of the file.

        The top-level code for almost all importers.

        Overriding this method gives the subclass completed control.
        """
        c = self.c

        # Fix #449: Cloned @auto nodes duplicates section references.
        if parent.isCloned() and parent.hasChildren():  # pragma: no cover (missing test)
            return
        self.root = root = parent.copy()

        # Check for intermixed blanks and tabs.
        self.tab_width = c.getTabWidth(p=root)
        lines = g.splitLines(s)
        ws_ok = self.check_blanks_and_tabs(lines)  # Issues warnings.

        # Regularize leading whitespace
        if not ws_ok:
            lines = self.regularize_whitespace(lines)

        # A hook for xml importer: preprocess lines.
        lines = self.preprocess_lines(lines)

        # Generate all nodes.
        self.gen_lines(lines, parent)

        # A hook for python importer.
        self.postprocess(parent)

        # Importers should never dirty the outline.
        # #1451: Do not change the outline's change status.
        for p in root.self_and_subtree():
            p.clearDirty()
    #@+node:ekr.20230529075138.12: *4* i.make_guide_lines
    def make_guide_lines(self, lines: list[str]) -> list[str]:
        """
        Importer.make_guide_lines.

        Return a list if **guide lines** that simplify the detection of blocks.

        This default method removes all comments and strings from the original lines.

        The perl importer overrides this methods to delete regexes as well
        as comments and strings.
        """
        return self.delete_comments_and_strings(lines[:])
    #@+node:ekr.20230529075138.38: *4* i.preprocess_lines
    def preprocess_lines(self, lines: list[str]) -> list[str]:
        """
        A hook to enable preprocessing lines before calling x.find_blocks.

        Xml_Importer uses this hook to split lines.
        """
        return lines
    #@+node:ekr.20230825095756.1: *4* i.postprocess
    def postprocess(self, parent: Position) -> None:
        """
        Importer.postprocess.  A hook for language-specific post-processing.

        Python_Importer overrides this method.

        **Important**: The RecursiveImportController (RIC) class contains a
                       language-independent postpass that adjusts headlines of
                       *all* imported nodes.
        """
    #@+node:ekr.20230529075138.39: *4* i.regularize_whitespace
    def regularize_whitespace(self, lines: list[str]) -> list[str]:  # pragma: no cover (missing test)
        """
        Importer.regularize_whitespace.

        Regularize leading whitespace in s:
        Convert tabs to blanks or vice versa depending on the @tabwidth in effect.

        Subclasses may override this method to suppress this processing.
        """
        kind = 'tabs' if self.tab_width > 0 else 'blanks'
        kind2 = 'blanks' if self.tab_width > 0 else 'tabs'
        fn = g.shortFileName(self.root.h)
        count, result, tab_width = 0, [], self.tab_width
        if tab_width < 0:  # Convert tabs to blanks.
            for n, line in enumerate(lines):
                i, w = g.skip_leading_ws_with_indent(line, 0, tab_width)
                # Use negative width.
                s = g.computeLeadingWhitespace(w, -abs(tab_width)) + line[i:]
                if s != line:
                    count += 1
                result.append(s)
        elif tab_width > 0:  # Convert blanks to tabs.
            for n, line in enumerate(lines):
                # Use positive width.
                s = g.optimizeLeadingWhitespace(line, abs(tab_width))
                if s != line:
                    count += 1
                result.append(s)
        if count and not g.unitTesting:
            g.es(f"changed leading {kind2} to {kind} in {count} line{g.plural(count)} in {fn}")
        return result
    #@+node:ekr.20230529075138.7: *3* i: Utils
    # Subclasses are unlikely ever to need to override these methods.
    #@+node:ekr.20230529075138.8: *4* i.compute_common_lws
    def compute_common_lws(self, blocks: list[Block]) -> str:
        """
        Return the length of the common leading indentation of all non-blank
        lines in all blocks.

        This method assumes that no leading whitespace contains intermixed tabs and spaces.

        The returned string should consist of all blanks or all tabs.
        """
        if not blocks:
            return ''
        lws_list: list[int] = []
        for block in blocks:
            assert self.lines == block.lines
            lines = self.lines[block.start:block.end]
            for line in lines:
                stripped_line = line.lstrip()
                if stripped_line:  # Skip empty lines
                    lws_list.append(len(line) - len(stripped_line))
        n = min(lws_list) if lws_list else 0
        ws_char = ' ' if self.tab_width < 1 else '\t'
        return ws_char * n
    #@+node:ekr.20230529075138.34: *4* i.create_placeholders
    def create_placeholders(self, level: int, lines_dict: dict, parents: list[Position]) -> None:
        """
        Create placeholder nodes so between the current level (len(parents)) and the desired level.

        The org and otl importers use this method.
        """
        if level <= len(parents):
            return
        n = level - len(parents)
        assert n > 0
        assert level >= 0
        while n > 0:
            n -= 1
            parent = parents[-1]
            child = parent.insertAsLastChild()
            child.h = f"placeholder level {len(parents)}"
            parents.append(child)
            lines_dict[child.v] = []
    #@+node:ekr.20230529075138.9: *4* i.delete_comments_and_strings
    def delete_comments_and_strings(self, lines: list[str]) -> list[str]:
        """
        Delete all comments and strings from the given lines.

        The resulting lines form **guide lines**. The input and guide
        lines are "parallel": they have the same number of lines.

        Analyzing the guide lines instead of the input lines is the
        simplifying trick behind the new importers.
        """
        string_delims = self.string_list
        line_comment, start_comment, end_comment = g.set_delims_from_language(self.language)
        target = ''  # The string ending a multi-line comment or string.
        escape = '\\'
        result = []
        for line in lines:
            result_line, skip_count = [], 0
            for i, ch in enumerate(line):
                if ch == '\n':
                    break  # Avoid appending the newline twice.
                if skip_count > 0:
                    skip_count -= 1  # Skip the character.
                    continue
                if target:
                    if line.startswith(target, i):
                        if len(target) > 1:
                            # Skip the remaining characters of the target.
                            skip_count = len(target) - 1
                        target = ''  # Begin accumulating characters.
                elif ch == escape:
                    skip_count = 1
                    continue
                elif line_comment and line.startswith(line_comment, i):
                    break  # Skip the rest of the line.
                elif any(line.startswith(z, i) for z in string_delims):
                    # Allow multi-character string delimiters.
                    for z in string_delims:
                        if line.startswith(z, i):
                            target = z
                            if len(z) > 1:
                                skip_count = len(z) - 1
                            break
                elif start_comment and line.startswith(start_comment, i):
                    target = end_comment
                    if len(start_comment) > 1:
                        # Skip the remaining characters of the starting comment delim.
                        skip_count = len(start_comment) - 1
                else:
                    result_line.append(ch)
            # End the line and append it to the result.
            if line.endswith('\n'):
                result_line.append('\n')
            result.append(''.join(result_line))
        assert len(result) == len(lines)  # A crucial invariant.
        return result
    #@+node:ekr.20230529075138.42: *4* i.get_str_lws
    def get_str_lws(self, s: str) -> str:
        """Return the characters of the lws of s."""
        m = re.match(r'([ \t]*)', s)
        return m.group(0) if m else ''
    #@+node:ekr.20230529075138.16: *4* i.remove_common_lws
    def remove_common_lws(self, lws: str, p: Position) -> None:
        """Remove the given leading whitespace from all lines of p.b."""
        if len(lws) == 0:
            return
        assert lws.isspace(), repr(lws)
        n = len(lws)
        lines = g.splitLines(p.b)
        result: list[str] = []
        for line in lines:
            stripped_line = line.strip()
            assert not stripped_line or line.startswith(lws), repr(line)
            result.append(line[n:] if stripped_line else line)
        p.b = ''.join(result)
    #@+node:ekr.20230529075138.17: *4* i.trace_blocks & trace_block
    def trace_blocks(self, blocks: list[Block]) -> None:
        """For debugging: trace the list of blocks."""
        if not blocks:
            g.trace('No blocks')
            return
        print('')
        print('Blocks...')
        for block in blocks:
            self.trace_block(block)
        print('End of Blocks')
        print('')

    def trace_block(self, block: Block) -> None:
        """For debugging: trace one block."""
        tag = f"  {block.kind:>10} {block.name:<20} {block.start} {block.start_body2} {block.end}"
        g.printObj(block.lines[block.start:block.end], tag=tag)
    #@-others
#@-others
#@@language python
#@@tabwidth -4
#@@pagewidth 70
#@-leo
