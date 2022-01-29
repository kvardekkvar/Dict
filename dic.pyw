import tkinter as tk
import xml.etree.ElementTree as ET
from random import random


class VerticalScrolledFrame(tk.Frame):
    """A pure Tkinter scrollable frame that actually works!
    * Use the 'interior' attribute to place widgets inside the scrollable frame
    * Construct and pack/place/grid normally
    * This frame only allows vertical scrolling

    """

    def __init__(self, parent, *args, **kw):
        tk.Frame.__init__(self, parent, *args, **kw)

        # create a canvas object and a vertical scrollbar for scrolling it
        vscrollbar = tk.Scrollbar(self, orient=tk.VERTICAL)
        vscrollbar.pack(
            fill=tk.Y,
            side=tk.RIGHT,
            expand=tk.FALSE
        )
        canvas = tk.Canvas(self, bd=0, highlightthickness=0,
                           yscrollcommand=vscrollbar.set)
        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=tk.TRUE)
        vscrollbar.config(command=canvas.yview)

        # reset the view
        canvas.xview_moveto(0)
        canvas.yview_moveto(0)

        # create a frame inside the canvas which will be scrolled with it
        self.interior = interior = tk.Frame(canvas)
        interior_id = canvas.create_window(0, 0, window=interior,
                                           anchor=tk.NW)

        # track changes to the canvas and frame width and sync them,
        # also updating the scrollbar
        def _configure_interior(event):
            # update the scrollbars to match the size of the inner frame
            size = (interior.winfo_reqwidth(), interior.winfo_reqheight())
            canvas.config(scrollregion="0 0 %s %s" % size)
            if interior.winfo_reqwidth() != canvas.winfo_width():
                # update the canvas's width to fit the inner frame
                canvas.config(width=interior.winfo_reqwidth())

        interior.bind('<Configure>', _configure_interior)

        def _configure_canvas(event):
            if interior.winfo_reqwidth() != canvas.winfo_width():
                # update the inner frame's width to fill the canvas
                canvas.itemconfigure(interior_id, width=canvas.winfo_width())

        canvas.bind('<Configure>', _configure_canvas)


class Source:

    def __init__(self, text, ids=None):
        self.text = text
        self.id = ids
        self.graph = None
        self.cnt = -1


class Word:

    def __init__(self, text, idw=None, order=0):
        self.text = text
        self.id = idw
        self.order = int(order)

class XmlOperation:

    def __init__(self, s=None, w=None):
        self.s = s
        self.w = w
        
    def load(self):
        dic = {}
        sources = []
        tree = ET.parse('dic.xml')
        root = tree.getroot()
        for child in root:
            if child.attrib['data']:
                s = Source(child.attrib['data'], child.attrib['id'])
                sources.append(s)
                if not child:
                    dic[s.id] = [Word('', '0', 0)]
                for gc in child:
                    s.cnt+=1
                    if s.id in dic.keys():
                        dic[s.id].append(Word(gc.text, gc.attrib['id'], gc.attrib['order']))

                    else:
                        dic[s.id] = [Word(gc.text, gc.attrib['id'], gc.attrib['order'])]
        return dic, sources

    def modify(self, mode, newtext=None):
        s = self.s
        w = self.w
        tree = ET.parse('dic.xml')
        root = tree.getroot()
        if mode == '+s':
            tree = ET.parse('dic.xml')
            root = tree.getroot()
            newnode = ET.Element('source')
            newnode.set('data', s.text)
            newnode.set('id', s.id)
            root.append(newnode)
        else:
            for snode in root.findall('source'):
                if snode.attrib['id'] == s.id:
                    if mode == '+w':                        
                        wordnode = ET.Element('word')
                        wordnode.text = w.text
                        wordnode.set('id', w.id)
                        wordnode.set('order', str(w.order))
                        snode.append(wordnode)
                    if mode == '?w':
                        for wnode in snode:
                            if wnode.text == w.text and wnode.attrib['id'] == w.id:
                                wnode.text = newtext
                                break
                    if mode == '-w':
                        for wnode in snode:
                            if wnode.text == w.text and wnode.attrib['id'] == w.id:
                                snode.remove(wnode)
                                break
                    if mode == '?s':
                        snode.attrib['data'] = newtext
                    if mode == '-s':
                        root.remove(snode)
                        break
        ET.indent(tree, space="\t", level=0)
        tree.write('dic.xml')

    def addword(self):
        self.modify(mode='+w')

    def editword(self, newtext):
        self.modify(mode='?w', newtext=newtext)

    def delword(self):
        self.modify(mode='-w')

    def addsource(self):
        self.modify(mode='+s')

    def editsource(self, newtext):
        self.modify(mode='?s', newtext=newtext)

    def delsource(self):
        self.modify(mode='-s')


class LabelSource(tk.Label):
    instances = []
    slaves = []

    def __init__(self, parent=None, source='None', frame_words_content=None, dic=None, myapp=None, *args, **kw):
        tk.Label.__init__(self, parent, *args, **kw)
        self.__class__.instances.append(self)
        self.bind('<Button-1>', self.click)
        self.bind('<Button-2>', self.rightclick)
        self.bind('<Button-3>', self.rightclick)
        self.source = source
        self.frame_words_content = frame_words_content
        self.dic = dic
        self.myapp = myapp

    def click(self, event):
        self.config(bg='red')
        for other in self.__class__.instances:
            if id(self) != id(other):
                other.config(bg='#f0f0ed')

        for sl in self.slaves:
            sl.destroy()

        self.__class__.slaves = []
        for w in self.dic[self.source.id]:
            news = LabelWord(parent=self.frame_words_content.interior, w=w, myapp=self.myapp, anchor='w', source=self.source)
            news.pack(fill='both')
            self.slaves.append(news)

        self.myapp.activesource = self.source

    def rightclick(self, event):
        DialogWord(self, self.source, dtype='s')


class LabelWord(tk.Label):
    def __init__(self, parent=None, source='None', frame_words_content=None, dic=None, w=Word('', '0'), myapp=None,
                 *args, **kw):
        tk.Label.__init__(self, parent, text=w.text, *args, **kw)
        
        #test
        self.bind('<Button-1>', self.move1up) 
        self.bind('<Button-2>', self.rightclick)
        self.bind('<Button-3>', self.rightclick)
        self.source = source
        self.w = w
        self.myapp = myapp
        if not dic:
            self.dic = self.myapp.dic
        else:
            self.dic = dic
        

    def rightclick(self, event):
        DialogWord(self, self.w, dtype='w')
        
    def move1up(self, event):
        
        index = self.w.order
        
        if self.w.order == 0:
            return
        
        #reorder
        for sl in self.source.graph.slaves:
            if sl.w.order==index-1:
                sl.w.order, self.w.order = self.w.order, sl.w.order
            sl.destroy()
            
        #display
        for i in sorted(self.dic[self.source.id], key=lambda w: w.order):
            self.myapp.addgraphword(self.source, i)
            
        #rewerite to xml -- not implemented yet
       
class DialogWord:
    exists = 0

    def __init__(self, parent=None, o=None, dtype='w'):
        if self.exists:
            return
        DialogWord.exists = 1

        self.parent = parent
        self.o = o
        self.dtype = dtype

        self.popup = tk.Toplevel(parent)
        self.popup.overrideredirect(True)
        x, y = parent.winfo_rootx(), parent.winfo_rooty()
        self.popup.geometry("+%d+%d" % (x, y + 20))

        f_top = tk.Frame(self.popup)
        f_bot = tk.Frame(self.popup)
        button_delete = tk.Button(f_top, text='Delete')
        button_edit = tk.Button(f_top, text='Edit')
        button_nothing = tk.Button(f_top, text='Do nothing')
        self.entry_edit = tk.Entry(f_bot, fg="black", bg="white")

        f_top.pack()
        f_bot.pack()
        self.entry_edit.pack(side='bottom', fill='x')
        button_delete.pack(side='right')
        button_nothing.pack(side='right')
        button_edit.pack(side='right')

        self.popup.update_idletasks()

        self.entry_edit.configure(width=int(f_top.winfo_reqwidth() / 146 * 23.5))  # need to change that

        self.popup.grab_set()
        self.popup.bind("<Button-1>", self.clickoutside)
        self.popup.bind("<Button-2>", self.clickoutside)
        self.popup.bind("<Button-3>", self.clickoutside)

        button_delete.bind("<Button-1>", self.delete)
        button_nothing.bind("<Button-1>", self.close)
        button_edit.bind("<Button-1>", self.edit)

        self.entry_edit.delete(0, tk.END)
        self.entry_edit.insert(0, self.o.text)

    def clickoutside(self, event):
        if event.widget == self.popup:
            if (event.x < 0 or event.x > self.popup.winfo_width() or
                    event.y < 0 or event.y > self.popup.winfo_height()):
                self.close()

    def edit(self, event=None):

        newtext = self.entry_edit.get()
        if newtext != '':

            if self.dtype == 'w':
                XmlOperation(s=self.parent.myapp.activesource, w=self.o).editword(newtext=newtext)

                for sl in LabelSource.slaves:
                    if sl.w.id == self.o.id:
                        sl['text'] = newtext
            if self.dtype == 's':
                if newtext in map(lambda x: x.text, self.parent.myapp.sources):
                    return

                XmlOperation(s=self.o).editsource(newtext=newtext)

                for sl in LabelSource.instances:
                    if sl.source.id == self.o.id:
                        sl['text'] = newtext

            self.o.text = newtext
            self.close()
        else:
            self.entry_edit.delete(0, tk.END)
            self.entry_edit.insert(0, self.w.text)

    def delete(self, event=None):
        if self.dtype == 'w':
            self.parent.myapp.delword(self.parent.w)
        if self.dtype == 's':
            self.parent.myapp.delsource(self.o)
            LabelSource.instances.remove(self.parent)
            self.parent.myapp.sources.remove(self.o)
            if self.o == self.parent.myapp.activesource:
                for sl in LabelSource.slaves:
                    sl.destroy()

        self.parent.destroy()
        self.close()

    def close(self, event=None):
        self.popup.destroy()
        DialogWord.exists = 0


class MyApp:
    sources = []
    dic = {}
    sources_graphical = []

    def __init__(self):
        window = tk.Tk()
        window.title('Wordlist')
        greeting = tk.Label(text="My dict")
        greeting.pack()

        self.activesource = None

        self.frame_sources = tk.Frame(window)
        self.frame_sources_content = VerticalScrolledFrame(self.frame_sources)
        self.entry_sources = tk.Entry(self.frame_sources, fg="black", bg="white", width=50)

        button_sources = tk.Button(self.frame_sources, text="Add source")
        button_sources.bind('<Button-1>', self.addsource)
        self.entry_sources.bind('<Return>', self.addsource)
        self.entry_sources.bind('<Button-2>', lambda x: self.entry_sources.insert(0, window.clipboard_get()))
        self.entry_sources.bind('<Button-3>', lambda x: self.entry_sources.insert(0, window.clipboard_get()))

        self.frame_words = tk.Frame(window)
        self.frame_words_content = VerticalScrolledFrame(self.frame_words)
        self.entry_words = tk.Entry(self.frame_words, fg="black", bg="white", width=50)
        button_words = tk.Button(self.frame_words, text="Add word")
        button_words.bind('<Button-1>', self.addword)
        self.entry_words.bind('<Return>', self.addword)
        self.entry_words.bind('<Button-2>', lambda x: self.entry_words.insert(0, window.clipboard_get()))
        self.entry_words.bind('<Button-3>', lambda x: self.entry_words.insert(0, window.clipboard_get()))
        self.loaddata()

        self.frame_sources.pack(side=tk.LEFT)
        self.frame_sources_content.pack(fill=tk.X)
        self.entry_sources.pack(side=tk.BOTTOM)
        button_sources.pack(side=tk.BOTTOM)

        self.frame_words.pack(side=tk.RIGHT, fill=tk.X)
        self.frame_words_content.pack(fill='both')

        button_words.pack()
        self.entry_words.pack()
        window.mainloop()

    def loaddata(self):
        
        self.dic, self.sources = XmlOperation().load()
        for s in self.sources:
            self.addgraphsource(s)

    def addsource(self, event):
        stext = self.entry_sources.get()
        if stext and stext not in map(lambda x: x.text, self.sources):
            ids = str(int(random() * 10000000000))
            s = Source(stext, ids)
            XmlOperation(s=s).addsource()
            self.addgraphsource(s)
            self.sources.append(s)
            self.dic[s.id] = [Word('', '0')]
        self.entry_sources.delete(0, tk.END)

    def addword(self, event):
        s = self.activesource
        idw = str(int(random() * 10000000000))
        s.cnt = s.cnt + 1
        w = Word(self.entry_words.get(), idw, s.cnt)
        if s.text is None or w.text == '':
            pass
            # tk.messagebox.showinfo('No source or no word', 'Select a source or type in a word')
        else:
            if self.dic[s.id] and self.dic[s.id][0].text == '':
                self.dic[s.id] = [w]
                for sl in LabelSource.slaves:
                    sl.destroy()
            else:
                self.dic[s.id] += [w]
            self.addgraphword(s, w)
            XmlOperation(s, w).addword()
        self.entry_words.delete(0, tk.END)

    def delword(self, w, s=None):
        if s is None:
            s = self.activesource
        w = w
        if s.text is None or w.text == '':
            pass
        else:
            self.dic[s.id].remove(w)
            s.cnt-=1
            XmlOperation(s, w).delword()
            

    def delsource(self, s):
        for w in self.dic[s.id]:
            self.delword(w, s)
        del self.dic[s.id]
        XmlOperation(s).delsource()

    def addgraphsource(self, s):
        newst = LabelSource(self.frame_sources_content.interior, text=s.text[:64], source=s,
                            frame_words_content=self.frame_words_content, dic=self.dic, myapp=self)
        s.graph = newst
        newst.pack(fill='x', expand=tk.TRUE)

    def addgraphword(self, s, w):
        news = LabelWord(parent=self.frame_words_content.interior, w=w, myapp=self, anchor='w', source=s)
        LabelSource.slaves.append(news)
        news.pack(fill='both')


MyApp()
