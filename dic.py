import tkinter as tk
import xml.etree.ElementTree as ET

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


class MyLabel(tk.Label):
    instances=[]
    def __init__(self, parent=None, *args, **kw):
        tk.Label.__init__(self, parent, *args, **kw)            
        self.__class__.instances.append(self)
        self.bind('<Button-1>', self.click)
        
    def click(self, event):
        self.config(bg='red')
        for other in self.__class__.instances:
            if id(self) != id(other):
                other.config(bg='#f0f0ed')

class MyApp():
    sources=set()
    dic={}
    sources_graphical=[]
    def __init__(self):
        window = tk.Tk()
        greeting = tk.Label(text="My dict")
        greeting.pack()

        self.frame_sources=tk.Frame(window)
        self.frame_sources_content=VerticalScrolledFrame(self.frame_sources)
        self.entry_sources = tk.Entry(self.frame_sources, fg="black", bg="white", width=50)
        
        button_sources = tk.Button(self.frame_sources,text="Add source")
        button_sources.bind('<Button-1>',self.addsource)

        #self.scroll_sources=tk.Scrollbar(self.frame_sources)
        
        
        frame_words=tk.Frame()
        entry_words = tk.Entry(frame_words, fg="black", bg="white", width=50)
        button_words = tk.Button(frame_words,text="Add word")
        
        self.loaddata()
        
        #self.scroll_sources.pack(side=tk.RIGHT, fill=tk.Y)
        self.frame_sources.pack(side=tk.LEFT, fill=tk.X)
        self.frame_sources_content.pack(fill=tk.X)
        self.entry_sources.pack(side=tk.BOTTOM)
        button_sources.pack(side=tk.BOTTOM)

        entry_words.pack()
        button_words.pack()

        frame_words.pack(side=tk.RIGHT)
        
        window.mainloop()
        
    def addsource(self, event):
        s = self.entry_sources.get()
        if s and s not in self.sources:
            tree=ET.parse('dic.xml')
            root=tree.getroot()
            newnode=ET.Element('source')
            newnode.set('data', s)
            root.append(newnode)
            tree.write('dic.xml')
            self.addgraphsource(s)
            self.sources.add(s)
    def addgraphsource(self,s):
        news=MyLabel(self.frame_sources_content.interior, text=s[:64])    
        news.pack(fill=tk.X)
    def loaddata(self):
        tree=ET.parse('dic.xml')
        root=tree.getroot()
        for child in root:
            if child.attrib['data']:
                s=child.attrib['data']
                self.sources.add(s)
                self.addgraphsource(s)
                for gc in child:
                    if s in self.dic.keys():
                        self.dic[s].append(gc.text)
                    else:
                        self.dic[s]=[gc.text]
MyApp()