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
    file_path = os.path.abspath(__file__)
    app_path = os.path.dirname(file_path)

xml_path = os.path.join(app_path, 'dic-files', 'dic.xml')
html_path = os.path.join(app_path, 'dic-files', 'dic.html')
settings_path = os.path.join(app_path, 'dic-files', 'dicsettings.txt')

class Source:

    def __init__(self, text, source_id=None):
        self.text = text
        self.id = source_id
        self.graph = None
        self.cnt = -1
        
    def toJSON(self):
        return json.dumps(self, default=lambda o: o.__dict__, 
            sort_keys=True, indent=4)

    def get_id(self):
        return self.id

    def get_text(self):
        return self.text
    
    def set_text(self, new_text):
        self.text = new_text
    
    def increment_counter(self):
        self.cnt+=1
    
    def decrement_counter(self):
        self.cnt-=1
    
    
class Word:

    def __init__(self, text, WordId=None, order=0, parentSource=None):
        self.text = text
        self.id = WordId
        self.order = int(order)
        self.source = parentSource
        
    def toJSON(self):
        return json.dumps(self, default=lambda o: o.__dict__, 
            sort_keys=True, indent=4)
        
    def get_text(self):
        return self.text
    
    def set_text(self, text):
        if text:
            self.text = text
        else:
            #write error-handling logic
            pass
    
    def get_id(self):
        return self.id
    
class XmlOperation:

    def __init__(self, source=None, word=None):
        self.source = source
        self.word = word

        
        
    def load(self):
        dic = {}
        sources = []
        tree = ET.parse(xml_path)
        root = tree.getroot()
        
        for child in root:
            
            child_data = child.attrib['data']
            child_id = child.attrib['id']
            
            if child_data:
                source = Source(child_data, child_id)
                sources.append(source)
                
                if not child:
                    dic[child_id] = [Word('', '0', 0)]
                    
                for grandchild in child:
                    grandchild_text = grandchild.text
                    grandchild_id = grandchild.attrib['id']
                    grandchild_order = grandchild.attrib['order']
                    source.increment_counter()
                    
                    word = Word(grandchild_text, grandchild_id, grandchild_order, source)
                    if child_id in dic.keys():
                        dic[child_id].append(word)
                    else:
                        dic[child_id] = [word]
                        
        return dic, sources


    def modify(self, mode, newtext=None):
        s = self.source
        w = self.word
        tree = ET.parse(xml_path)
        root = tree.getroot()
        if mode == '+s':
            tree = ET.parse(xml_path)
            root = tree.getroot()
            newnode = ET.Element('source')
            newnode.set('data', s.get_text())
            newnode.set('id', s.get_id)
            root.append(newnode)
        else:
            for snode in root.findall('source'):
                if snode.attrib['id'] == s.id:
                    if mode == '+w':                        
                        wordnode = ET.Element('word')
                        wordnode.text = w.get_text()
                        wordnode.set('id', w.get_id())
                        wordnode.set('order', str(w.order))
                        snode.append(wordnode)
                    if mode == '?w':
                        for wnode in snode:
                            if wnode.text == w.get_text() and wnode.attrib['id'] == w.get_id():
                                wnode.text = newtext
                                break
                    if mode == '-w':
                        word_to_delete=None
                        for wnode in snode:
                            oldorder = int(wnode.attrib['order'])
                            if oldorder > w.order:
                                wnode.attrib['order'] = str(oldorder - 1)
                            if wnode.text == w.get_text() and wnode.attrib['id'] == w.get_id():
                                word_to_delete = wnode
                        snode.remove(word_to_delete)
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
    
            with open(xml_path, "wb") as f:
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
        tree = ET.parse(xml_path)
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
    
            with open(xml_path, "wb") as f:
                    f.write(xmlstr.encode('utf-8'))
        except Exception as e:
            print('Misdemeanor: ', e)
            print(traceback.format_exc())

    def syncXml(e):
        myfile = xml_path
        settings = open(settings_path, "r")
        token = settings.readline().rstrip()
        settings.close()
        
        endpoint = 'http://178.209.46.147/api/dic/xml'
        headers = {'authorization':token}
        file =  open(myfile,'r', encoding="utf-8")
        request_body = file.read().encode("utf-8")
        requests.post(endpoint, headers=headers, data=request_body)
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
    
    def getSourceById(self, source_id):
        SourceObjects = [s for s in self.sources if s.id == source_id]
        return SourceObjects[0]
    
    def getWordById(self, word_id):
        for source in self.sources:
            source_id = source.get_id()
            for word in self.dic[source_id]:
                if word.get_id() == word_id:
                    return word

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
    def getWords(self, source_id):
        print('searching source ' + source_id)
        source = self.getSourceById(source_id)
        response = []
        message = []
        for w in sorted(self.dic[source_id], key=lambda w: w.order):
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
    def addWord(self, word_text, source_id):
        source=self.getSourceById(source_id)
        print('Request to add word ' + word_text + ' --> ' + source.get_text())
        word_id = str(int(random() * 10000000000))
        source.increment_counter()
        word = Word(word_text, word_id, source.cnt, source)
        
        
        if source.text is None or word.get_text() == '':
            print('No source or no word specified')
        else:
            if self.dic[source_id] and self.dic[source_id][0].text == '':
                self.dic[source_id] = [word]
            else:
                self.dic[source_id] += [word]
            XmlOperation(source, word).addword()
            print("Word added")

    
    @handle_exceptions
    def editWord(self, new_text, changed_word_id, active_source_id):
        if new_text != '':
                source = self.getSourceById(active_source_id)
                changed_word = self.getWordById(changed_word_id)
                XmlOperation(source, changed_word).editword(newtext=new_text)
                changed_word.set_text(new_text)
                #this was not updated
                #stange that dic is not updated
                return {'message':'Word updated'}
        return {'message':'Empty words not written'}
                
    @handle_exceptions
    def deleteWord(self, word_id, source_id):
        source = self.getSourceById(source_id)
        word = self.getWordById(word_id)
        
        if source.text is None or word.text == '':
            return  {'message': 'Strange things happen'}
        else:
            order = word.order
            for another_word in self.dic[source.id]:
                if another_word.order > order:
                    another_word.order -= 1
            
            self.dic[source.id].remove(word)
            source.decrement_counter()
            XmlOperation(source, word).delword()
            print("Word deleted: " + word.text)
        return  {'message': 'Word deleted'}
    
    @handle_exceptions
    def addSource(self, new_source):
        print('Request to add source: ', new_source)
        if new_source and new_source not in map(lambda x: x.get_text(), self.sources):
            source_id = str(int(random() * 10000000000))
            source = Source(new_source, source_id)
            XmlOperation(source).addsource()
            self.sources.append(source)
            self.dic[source_id] = [Word('', '0')]
            print('Added source: ', new_source)
            return
        print("Source not added")
       
 
    @handle_exceptions        
    def editSource(self, new_text, changed_source_id=None, changed_word=None):
            if new_text != '':
                if new_text in map(lambda x: x.text, self.sources):
                    return {'message': 'Source exists'}
                source = self.getSourceById(changed_source_id)
                XmlOperation(source).editsource(new_text)
                source.text = new_text
                return {'message': 'Source edited'}

    @handle_exceptions
    def deleteSource(self, source_id):

        source = self.getSourceById(source_id)       
        del self.dic[source_id]
        XmlOperation(source).delsource()
        self.sources.remove(source)
        print("Source deleted: " + source.text)
        return {'message': 'Source deleted'}
    
    @handle_exceptions
    def moveWordOneUp(self, word_id, source_id):
        word = self.getWordById(word_id)
        source = self.getSourceById(source_id)
        index = word.order
        
        if word.order == 0:
            return {'message':"Word is 1st"}
        
        for another_word in self.dic[source.id]:
            if another_word.order == index-1:
                another_word.order, word.order = word.order, another_word.order

    
        XmlOperation(source).swapwords(index-1, index)
        return {'message':'moved 1 up'}
    
api = Api()
webview.create_window('Dic 2.0', html_path, js_api=api)
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
                
    
        XmlOperation(self.source).swapwords(index-1, index)
        
    def move1down(self, event=None):
        index = self.w.order
        for sl in self.source.graph.slaves:
            if sl.winfo_exists() and sl.w.order == index + 1:
                sl.move1up('down')
                break
                    

'''