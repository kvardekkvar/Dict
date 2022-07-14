import xml.etree.ElementTree as ET
from xml.dom import minidom
from random import random
import requests

import webview
import traceback
import json
import sys
import os


if getattr(sys, 'frozen', False):
    app_path = os.path.dirname(sys.executable)
else:
    app_path = os.path.dirname(os.path.abspath(__file__))

xmlfilepath = os.path.join(app_path, 'dic-files', 'dic.xml')
htmlfilepath = os.path.join(app_path, 'dic-files', 'dic.html')
settingsfilepath = os.path.join(app_path, 'dic-files', 'dicsettings.txt')

class Source:

    def __init__(self, text, SourceId=None):
        self.text = text
        self.id = SourceId
        self.graph = None
        self.cnt = -1
        
    def toJSON(self):
        return json.dumps(self, default=lambda o: o.__dict__, 
            sort_keys=True, indent=4)


class Word:

    def __init__(self, text, WordId=None, order=0, parentSource=None):
        self.text = text
        self.id = WordId
        self.order = int(order)
        self.source = parentSource
        
    def toJSON(self):
        return json.dumps(self, default=lambda o: o.__dict__, 
            sort_keys=True, indent=4)

class XmlOperation:

    def __init__(self, s=None, w=None):
        self.s = s
        self.w = w
        
        
    def load(self):
        dic = {}
        sources = []
        tree = ET.parse(xmlfilepath)
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
                        dic[s.id].append(Word(gc.text, gc.attrib['id'], gc.attrib['order'], s))

                    else:
                        dic[s.id] = [Word(gc.text, gc.attrib['id'], gc.attrib['order'], s)]
        return dic, sources


    def modify(self, mode, newtext=None):
        s = self.s
        w = self.w
        tree = ET.parse(xmlfilepath)
        root = tree.getroot()
        if mode == '+s':
            tree = ET.parse(xmlfilepath)
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
                        wtobedeleted=None
                        for wnode in snode:
                            oldorder = int(wnode.attrib['order'])
                            if oldorder > w.order:
                                wnode.attrib['order'] = str(oldorder - 1)
                            if wnode.text == w.text and wnode.attrib['id'] == w.id:
                                wtobedeleted = wnode
                        snode.remove(wtobedeleted)
                    if mode == '?s':
                        snode.attrib['data'] = newtext
                    if mode == '-s':
                        root.remove(snode)
                        break
        #ET.indent(tree, space="\t", level=0)      #works only in py3.9
        #tree.write('dic.xml') 
        
        try:
            xmlstr = ET.tostring(root, 'utf-8')
            xmlstr=ET.XML(xmlstr)
            self.strip(xmlstr)
            xmlstr = self.prettify(xmlstr)
    
            with open(xmlfilepath, "wb") as f:
                    f.write(xmlstr.encode('utf-8'))
        except Exception as e:
            print('Misdemeanor: ', e)
            print(traceback.format_exc())

    def prettify(self,elem):
         """
             Return a pretty-printed XML string for the Element.
         """
         rough_string = ET.tostring(elem, 'utf-8')
         reparsed = minidom.parseString(rough_string)
         return reparsed.toprettyxml(indent="\t")

    def strip(self,elem):
        for elem in elem.iter():
            if(elem.text):
                elem.text = elem.text.strip()
            if(elem.tail):
                elem.tail = elem.tail.strip()

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

    def swapwords(self, index1, index2):
        s = self.s
        w = self.w
        tree = ET.parse(xmlfilepath)
        root = tree.getroot()
        for snode in root.findall('source'):
            if snode.attrib['id'] == s.id:
                cnt = 0
                for wnode in snode:
                    if wnode.attrib['order'] == str(index1):
                        wnode.attrib['order'] = str(index2)
                        cnt+=1
                        continue
                    if wnode.attrib['order'] == str(index2):
                        wnode.attrib['order'] = str(index1)
                        cnt+=1
                    if cnt == 2:
                        break
       #ET.indent(tree, space="\t", level=0)
       #tree.write('dic.xml')
        try:
            xmlstr = ET.tostring(root, 'utf-8')
            xmlstr=ET.XML(xmlstr)
            self.strip(xmlstr)
            xmlstr = self.prettify(xmlstr)
    
            with open(xmlfilepath, "wb") as f:
                    f.write(xmlstr.encode('utf-8'))
        except Exception as e:
            print('Misdemeanor: ', e)
            print(traceback.format_exc())

    def syncXml(e):
        myfile = xmlfilepath
        settings = open(settingsfilepath, "r")
        token = settings.readline().rstrip()
        settings.close()
        
        endpoint = 'http://178.209.46.147/api/dic/xml'
        file =  open(myfile,'r', encoding="utf-8")
        x = requests.post(endpoint, headers={'authorization':token}, data=file.read().encode("utf-8")
)
        file.close()
        return



class Api:
    def handle_exceptions(f):
        def wrapper(*args, **kw):
            try:
                return f(*args, **kw)
            except Exception as e:
                print('Misdemeanor: ', e)
                print(traceback.format_exc())
        return wrapper

    def getSourceByText(self, text):
        SourceObjects = [s for s in self.sources if s.text == text]
        return SourceObjects[0]
    
    def getSourceById(self, ids):
        SourceObjects = [s for s in self.sources if s.id == ids]
        return SourceObjects[0]
    
    def getWordById(self, idw):
        for s in self.sources:
            for w in self.dic[s.id]:
                if w.id == idw:
                    return w

    def __init__(self):
        self.dic, self.sources = XmlOperation().load()
        
    @handle_exceptions
    def getSources(self):    
        response = []
        for s in self.sources:
            #response.append(s.text)
            response.append(s.toJSON())
        print('Retrieved sources. ')
        return {'content':response, 'message': response}

    
    
    @handle_exceptions
    def getWords(self, sourceId):
        print('searching source ' + sourceId)
        source = self.getSourceById(sourceId)
        response = []
        message = []
        for w in sorted(self.dic[sourceId], key=lambda w: w.order):
            message.append(w.text)
            response.append(w.toJSON())
        print('Retrieved words for source = ' + str(source.text) +' : ' + str(message))
        return {'content':response, 'message': message}
    
    @handle_exceptions
    def syncXml(self):
        XmlOperation().syncXml()
        response='200'
        return {
            'message': 'Sync successful'
        }


    @handle_exceptions
    def addWord(self, wordtext, sourceId):
        source=self.getSourceById(sourceId)
        print('Request to add word ' + wordtext + ' --> ' + source.text)
        idw = str(int(random() * 10000000000))
        source.cnt = source.cnt + 1
        w = Word(wordtext, idw, source.cnt, source)
        if source.text is None or w.text == '':
            print('No source or no word specified')
        else:
            if self.dic[source.id] and self.dic[source.id][0].text == '':
                self.dic[source.id] = [w]
            else:
                self.dic[source.id] += [w]
            XmlOperation(source, w).addword()
            print("Word added")

    
    @handle_exceptions
    def editWord(self, newtext, changedwordId, activesourceId):
        if newtext != '':
                s = self.getSourceById(activesourceId)
                w = self.getWordById(changedwordId)
                XmlOperation(s=s, w=w).editword(newtext=newtext)
                w.text = newtext
                #this was not updated
                #stange that dic is not updated
                return {'message':'Word updated'}
        return {'message':'Empty words not written'}
                
    @handle_exceptions
    def deleteWord(self, wordId, sourceId):
        s = self.getSourceById(sourceId)
        w = self.getWordById(wordId)
        
        if s.text is None or w.text == '':
            return  {'message': 'Strange things happen'}
        else:
            order = w.order
            for otherword in self.dic[s.id]:
                if otherword.order>order:
                    otherword.order-=1
            self.dic[s.id].remove(w)
            s.cnt-=1
            XmlOperation(s, w).delword()
            print("Word deleted: " + w.text)
        return  {'message': 'Word deleted'}
    
    @handle_exceptions
    def addSource(self, newSource):
        print('Request to add source: ', newSource)
        if newSource and newSource not in map(lambda x: x.text, self.sources):
            ids = str(int(random() * 10000000000))
            s = Source(newSource, ids)
            XmlOperation(s=s).addsource()
            self.sources.append(s)
            self.dic[s.id] = [Word('', '0')]
            print('Added source: ', newSource)
            return
        print("Source not added")
        
    @handle_exceptions        
    def editSource(self, newtext, changedSourceId=None, changedword=None, dtype='s'):
            if newtext != '':
                if dtype == 'w':
                    XmlOperation(s=self.parent.myapp.activesource, w=self.o).editword(newtext=newtext)
                    #this was not updated
                    
                if dtype == 's':
                    if newtext in map(lambda x: x.text, self.sources):
                        return {'message': 'Source exists'}
                    o = self.getSourceById(changedSourceId)
                    XmlOperation(s=o).editsource(newtext=newtext)
                    o.text = newtext
                    return {'message': 'Source edited'}
    
    @handle_exceptions
    def deleteSource(self, sourceId, dtype='s'):
        if dtype == 'w':
            self.parent.myapp.delword(self.parent.w)
        if dtype == 's':
            s = self.getSourceById(sourceId)
            #dictempcopy = self.dic[s.id].copy()
            #for w in dictempcopy:
            #    self.deleteWord(w.id, s.id)         
            del self.dic[s.id]
            XmlOperation(s).delsource()
            self.sources.remove(s)
            print("Source deleted: " + s.text)
        return {'message': 'Source deleted'}
    
    @handle_exceptions
    def moveWordOneUp(self, wordId, sourceId):
        w = self.getWordById(wordId)
        s = self.getSourceById(sourceId)
        index = w.order
        
        if w.order == 0:
            return {'message':"Word is 1st"}
        
        for otherw in self.dic[s.id]:
            if otherw.order == index-1:
                otherw.order, w.order = w.order, otherw.order

    
        XmlOperation(s=s).swapwords(index-1, index)
        return {'message':'moved 1 up'}
    
api = Api()
webview.create_window('Dic 2.0', htmlfilepath, js_api=api)
webview.start(debug=True)

'''

    


class LabelWord(tk.Label):

    def move1up(self, event=None):
        
        index = self.w.order
        
        if self.w.order == 0:
            return
        
        for sl in self.source.graph.slaves:
            if sl.winfo_exists() and sl.w.order == index-1:
                sl.w.order, self.w.order = self.w.order, sl.w.order
            sl.destroy()
            
        for i in sorted(self.dic[self.source.id], key=lambda w: w.order):
            news = self.myapp.addgraphword(self.source, i)
            if i.order == index - 1 and event != 'down':
                news.focus_set()
            if i.order == index and event == 'down':
                news.focus_set()
                
    
        XmlOperation(s=self.source).swapwords(index-1, index)
        
    def move1down(self, event=None):
        index = self.w.order
        for sl in self.source.graph.slaves:
            if sl.winfo_exists() and sl.w.order == index + 1:
                sl.move1up('down')
                break
                    

'''