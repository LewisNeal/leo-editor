#@+leo-ver=5-thin
#@+node:ekr.20230529075138.1: * @file ../plugins/importers/base_importer.py
"""base_importer.py: The base Importer class used by almost all importers."""
from __future__ import annotations
import io
import re
from typing import Dict, List, Tuple, TYPE_CHECKING
from leo.core import leoGlobals as g

if TYPE_CHECKING:
    from leo.core.leoCommands import Commands as Cmdr
    from leo.core.leoNodes import Position

Block = Tuple[str, str, int, int, int]  # (kind, name, start, start_body, end)
StringIO = io.StringIO

class ImporterError(Exception):
    pass

#@+others
#@+node:ekr.20230529075138.4: ** class Importer
class Importer:
    """
    The base class for many of Leo's importers.
    """

    # To be removed...
    # Don't split classes, functions or methods smaller than this value.
    SPLIT_THRESHOLD = 10
    minimum_block_size = 0  # 0: create all blocks.

    # Must be overridden in subclasses.
    language: str = None
    block_patterns: Tuple = tuple()

    # May be overridden in subclasses.
    level_up_ch = '{'
    level_down_ch = '}'
    string_list: List[str] = ['"', "'"]

    #@+others
    #@+node:ekr.20230529075138.5: *3* i.__init__ & reloadSettings
    def __init__(self, c: Cmdr) -> None:
        """Importer.__init__"""
        assert self.language, g.callers()  # Do not remove.
        self.c = c  # May be None.
        self.root: Position = None
        delims = g.set_delims_from_language(self.language)
        self.single_comment, self.block1, self.block2 = delims
        self.tab_width = 0  # Must be set later.

        # Settings...
        self.reloadSettings()

    def reloadSettings(self) -> None:
        c = self.c
        if not c:  # pragma: no cover (defensive)
            return
        getBool = c.config.getBool
        c.registerReloadSettings(self)
        self.add_context = getBool("add-context-to-headlines")
        self.add_file_context = getBool("add-file-context-to-headlines")
        self.at_auto_warns_about_leading_whitespace = getBool('at_auto_warns_about_leading_whitespace')
        self.warn_about_underindented_lines = True
    #@+node:ekr.20230529075640.1: *3* i: Generic methods: may be overridden
    #@+node:ekr.20230529075138.36: *4* i.check_blanks_and_tabs
    def check_blanks_and_tabs(self, lines: List[str]) -> bool:  # pragma: no cover (missing test)
        """Check for intermixed blank & tabs."""
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
                self.report(message)
            else:
                g.es(message)
        return ok
    #@+node:ekr.20230529075138.11: *4* i.find_end_of_block
    def find_end_of_block(self, i: int, i2: int) -> int:
        """
        Importer.find_end_of_block.

        This is a *generic* end-of-block finder. May be overridden in subclasses.
        This method assumes that that '{' and '}' delimit blocks.

        i is the index (within the *guide* lines) of the line *following* the start of the block.
        Return the index of end of the block.
        """
        level = 1  # All blocks start with '{'
        while i < i2:
            line = self.guide_lines[i]
            i += 1
            for ch in line:
                if ch == '{':
                    level += 1
                if ch == '}':
                    level -= 1
                    if level == 0:
                        return i
        return i2
    #@+node:ekr.20230529075138.37: *4* i.import_from_string (driver)
    def import_from_string(self, parent: Position, s: str) -> None:
        """
        The common top-level code for almost all importers.
        
        Overriding this method gives the importer completed control.
        """
        c = self.c
        # Fix #449: Cloned @auto nodes duplicates section references.
        if parent.isCloned() and parent.hasChildren():  # pragma: no cover (missing test)
            return
        self.root = root = parent.copy()

        # Check for intermixed blanks and tabs.
        self.tab_width = c.getTabWidth(p=root)
        lines = g.splitLines(s)
        ws_ok = self.check_blanks_and_tabs(lines)  # Only issues warnings.

        # Regularize leading whitespace
        if not ws_ok:
            lines = self.regularize_whitespace(lines)

        # A hook for xml importer: preprocess lines.
        lines = self.preprocess_lines(lines)

        # Generate all nodes.
        self.new_gen_lines(lines, parent)

        # Importers should never dirty the outline.
        # #1451: Do not change the outline's change status.
        for p in root.self_and_subtree():
            p.clearDirty()
    #@+node:ekr.20230529075138.14: *4* i.gen_block
    def gen_block(self, block: Block, parent: Position) -> None:
        """
        Importer.gen_block.
        
        Subclasses may override this method to gain more control over how they
        recognize the start and end of blocks.

        Create all descendant blocks and their parent nodes.
        """
        lines = self.lines
        kind, name, start, start_body, end = block
        assert start <= start_body <= end, (start, start_body, end)

        # Find all blocks in the body of this block.
        blocks = self.find_blocks(start_body, end)
        if 0:
            self.trace_blocks(blocks)
        if blocks:
            # Start with the head: lines[start : start_start_body].
            result_list = lines[start:start_body]
            # Add indented @others.
            common_lws = self.compute_common_lws(blocks)
            result_list.extend([f"{common_lws}@others\n"])

            # Recursively generate the inner nodes/blocks.
            last_end = end
            for block in blocks:
                child_kind, child_name, child_start, child_start_body, child_end = block
                last_end = child_end
                # Generate the child containing the new block.
                child = parent.insertAsLastChild()
                child.h = self.compute_headline(block)
                self.gen_block(block, child)
                # Remove common_lws.
                self.remove_common_lws(common_lws, child)
            # Add any tail lines.
            result_list.extend(lines[last_end:end])
        else:
            result_list = lines[start:end]
        # Delete extra leading and trailing whitespace.
        parent.b = ''.join(result_list).lstrip('\n').rstrip() + '\n'
    #@+node:ekr.20230529075138.15: *4* i.new_gen_lines (top level)
    def new_gen_lines(self, lines: List[str], parent: Position) -> None:
        """
        Importer.gen_lines: a rewrite of Importer.gen_lines.

        Allocate lines to parent.b and descendant nodes.
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
            # Start the recursion.
            block = ('outer', 'parent', 0, 0, len(lines))
            self.gen_block(block, parent=parent)
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
    #@+node:ekr.20230529075138.38: *4* i.preprocess_lines
    def preprocess_lines(self, lines: List[str]) -> List[str]:
        """
        A hook to enable preprocessing lines before calling x.find_blocks.
        """
        return lines
    #@+node:ekr.20230529075138.39: *4* i.regularize_whitespace
    def regularize_whitespace(self, lines: List[str]) -> List[str]:  # pragma: no cover (missing test)
        """
        Regularize leading whitespace in s:
        Convert tabs to blanks or vice versa depending on the @tabwidth in effect.
        """
        kind = 'tabs' if self.tab_width > 0 else 'blanks'
        kind2 = 'blanks' if self.tab_width > 0 else 'tabs'
        fn = g.shortFileName(self.root.h)
        count, result, tab_width = 0, [], self.tab_width
        self.ws_error = False  # 2016/11/23
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
        if count:
            self.ws_error = True  # A flag to check.
            if not g.unitTesting:
                # g.es_print('Warning: Intermixed tabs and blanks in', fn)
                # g.es_print('Perfect import test will ignoring leading whitespace.')
                g.es('changed leading %s to %s in %s line%s in %s' % (
                    kind2, kind, count, g.plural(count), fn))
            if g.unitTesting:  # Sets flag for unit tests.
                self.report('changed %s lines' % count)
        return result
    #@+node:ekr.20230529075138.7: *3* i: Utils
    #@+node:ekr.20230529075138.8: *4* i.compute_common_lws
    def compute_common_lws(self, blocks: List[Block]) -> str:
        """
        Return the length of the common leading indentation of all non-blank
        lines in all blocks.

        This method assumes that no leading whitespace contains intermixed tabs and spaces:

        The returned string should consist of all blanks or all tabs.
        """
        if not blocks:
            return ''
        lws_list: List[int] = []
        for block in blocks:
            kind, name, start, start_body, end = block
            lines = self.lines[start:end]
            for line in lines:
                stripped_line = line.lstrip()
                if stripped_line:  # Skip empty lines
                    lws_list.append(len(line[: -len(stripped_line)]))
        n = min(lws_list) if lws_list else 0
        ws_char = ' ' if self.tab_width < 1 else '\t'
        return ws_char * n
    #@+node:ekr.20230529075138.13: *4* i.compute_headline
    def compute_headline(self, block: Block) -> str:

        child_kind, child_name, child_start, child_start_body, child_end = block
        return f"{child_kind} {child_name}" if child_name else f"unnamed {child_kind}"

    #@+node:ekr.20230529075138.34: *4* i.create_placeholders
    def create_placeholders(self, level: int, lines_dict: Dict, parents: List[Position]) -> None:
        """
        Create placeholder nodes so between the current level (len(parents)) and the desired level.

        Used by the org and otl importers.
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
    def delete_comments_and_strings(self, lines: List[str]) -> list[str]:
        """Delete all comments and strings from the given lines."""
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
    #@+node:ekr.20230529075138.6: *4* i.error, report, warning
    def error(self, s: str) -> None:  # pragma: no cover
        """Issue an error and cause a unit test to fail."""
        if g.unitTesting:
            print(s)
            assert False, s
        else:
            g.error(s)

    def report(self, message: str) -> None:  # pragma: no cover
        self.warning(message)

    def warning(self, s: str) -> None:  # pragma: no cover
        if not g.unitTesting:
            g.warning('Warning:', s)
    #@+node:ekr.20230529075138.10: *4* i.find_blocks
    def find_blocks(self, i1: int, i2: int) -> List[Block]:
        """
        Importer.find_blocks: override Importer.find_blocks.

        Find all blocks in the given range of *guide* lines from which blanks
        and tabs have been deleted.

        This is a *generic* block finder. May be overridden in subclasses.
        Use the patterns in self.block_patterns to find the start the start of a block.

        Return a list of Blocks, that is, tuples(name, start, start_body, end).
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
                    # cython may include trailing whitespace.
                    name = m.group(1).strip()
                    end = self.find_end_of_block(i, i2)
                    assert i1 + 1 <= end <= i2, (i1, end, i2)
                    # Don't generate small blocks.
                    if min_size == 0 or end - prev_i > min_size:
                        results.append((kind, name, prev_i, i, end))
                        i = prev_i = end
                    else:
                        i = end
                    break
        return results
    #@+node:ekr.20230529075138.42: *4* i.get_str_lws
    def get_str_lws(self, s: str) -> str:
        """Return the characters of the lws of s."""
        m = re.match(r'([ \t]*)', s)
        return m.group(0) if m else ''
    #@+node:ekr.20230529075138.12: *4* i.make_guide_lines
    def make_guide_lines(self, lines: List[str]) -> List[str]:
        """
        Return a list if **guide lines** that simplify the detection of blocks.

        This default method removes all comments and strings from the original lines.
        """
        return self.delete_comments_and_strings(lines[:])
    #@+node:ekr.20230529075138.16: *4* i.remove_common_lws
    def remove_common_lws(self, lws: str, p: Position) -> None:
        """Remove the given leading whitespace from all lines of p.b."""
        if len(lws) == 0:
            return
        assert lws.isspace(), repr(lws)
        n = len(lws)
        lines = g.splitLines(p.b)
        result: List[str] = []
        for line in lines:
            stripped_line = line.strip()
            assert not stripped_line or line.startswith(lws), repr(line)
            result.append(line[n:] if stripped_line else line)
        p.b = ''.join(result)
    #@+node:ekr.20230529075138.17: *4* i.trace_blocks
    def trace_blocks(self, blocks: List[Block]) -> None:

        if not blocks:
            g.trace('No blocks')
            return
        print('')
        print('Blocks...')
        lines = self.lines
        for z in blocks:
            kind2, name2, start2, start_body2, end2 = z
            tag = f"  {kind2:>10} {name2:<20} {start2:4} {start_body2:4} {end2:4}"
            g.printObj(lines[start2:end2], tag=tag)
        print('End of Blocks')
        print('')
    #@-others
#@-others
#@@language python
#@@tabwidth -4
#@@pagewidth 70
#@-leo
