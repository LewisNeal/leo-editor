# -*- coding: utf-8 -*-
#@+leo-ver=5-thin
#@+node:ekr.20181103094900.1: * @file leoflexx.py
#@@first
#@@language python
#@@tabwidth -4
'''
A Stand-alone prototype for Leo using flexx.

Flexx docs: testers, demos, howtos
https://flexx.readthedocs.io/en/stable/examples/
'''
import leo.core.leoGlobals as g
assert g
from flexx import flx
#@+others
#@+node:ekr.20181103151350.1: ** init
def init():
    # At present, leoflexx is not a true plugin.
    # I am executing leoflexx.py from an external script.
    return False
#@+node:ekr.20181104082130.1: ** class LeoMainWindow
class LeoMainWindow(flx.Widget):
    
    def init(self):
        with flx.VBox():
            with flx.HBox(flex=1):
                flx.Label(text='Tree')
                LeoTree(flex=1)
                flx.Label(text='Log')
                LeoLog(flex=1)
            flx.Label(text='Body')
            LeoBody(flex=1)
            flx.Label(text='Minibuffer')
            LeoMiniBuffer()
            flx.Label(text='Status Line')
            LeoStatusLine()
#@+node:ekr.20181104082138.1: ** class LeoTree
class LeoTree(flx.Widget):

    CSS = '''
    .flx-TreeWidget {
        background: #000;
        color: #afa;
    }
    '''
    
    #@+others
    #@+node:ekr.20181104080854.2: *3* tree.init
    def init(self):
        with flx.HSplit():
            self.label = flx.Label(flex=1, style='overflow-y: scroll;')
            with flx.TreeWidget(flex=1, max_selected=1) as self.tree:
                for t in ['foo', 'bar', 'spam', 'eggs']:
                    with flx.TreeItem(text=t, checked=None):
                        for i in range(4):
                            item2 = flx.TreeItem(text=t + ' %i' % i, checked=False)
                            if i == 2:
                                with item2:
                                    flx.TreeItem(title='A', text='more info on A')
                                    flx.TreeItem(title='B', text='more info on B')

        
    #@+node:ekr.20181104080854.3: *3* tree.on_event
    @flx.reaction(
        'tree.children**.checked',
        'tree.children**.selected',
        'tree.children**.collapsed',
    )
    def on_event(self, *events):
        for ev in events:
            print(ev.source, ev.type)
            id_ = ev.source.title or ev.source.text
            kind = '' if ev.new_value else 'un-'
            text = '%10s: %s' % (id_, kind + ev.type)
            self.label.set_html(text + '<br />' + self.label.html)
    #@-others
#@+node:ekr.20181104082144.1: ** class LeoBody
class LeoBody(flx.Widget):
    pass
#@+node:ekr.20181104082149.1: ** class LeoLog
class LeoLog(flx.Widget):
    pass
#@+node:ekr.20181104082154.1: ** class LeoMiniBuffer
class LeoMiniBuffer(flx.Widget):
    pass
#@+node:ekr.20181104082201.1: ** class LeoStatusLine
class LeoStatusLine(flx.Widget):
    pass
#@-others
if __name__ == '__main__':
    # Use `--flexx-webruntime=browser` to run in browser.
    flx.launch(LeoMainWindow)
    flx.run()
    ###
        # # Runs in browser.
        # # `python -m flexx stop 49190` stops the server.
        # flx.App(LeoWapp).launch('firefox-browser')
        # flx.start()
#@-leo
