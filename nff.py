
# coding: utf-8

# In[1]:

import wx
import os
import binascii
import struct
import sys
import numpy as np

from __future__ import with_statement

class Form(wx.Panel):
    
    rev = '\0\0\0'
    partNum = np.uint32(0)
    filePath = '0'
    nfName = 0
    checkSum = 0

    def __init__(self, *args, **kwargs):
        super(Form, self).__init__(*args, **kwargs)
        
        
        self.createControls()
        self.bindEvents()
        self.doLayout()
        
    def createControls(self):
        
        self.logger = wx.TextCtrl(self, style=wx.TE_MULTILINE|wx.TE_READONLY)
        self.checkSumDisplay = wx.TextCtrl(self, style=wx.TE_MULTILINE|wx.TE_READONLY) 
        
        self.generateButton = wx.Button(self, label = "Generate .nff file")
        
        
        self.openButton = wx.Button(self, label = "Open .bin File")        
        
        self.pnLabel = wx.StaticText(self, label = "Enter Part Number:")
        self.pnTextCtrl = wx.TextCtrl(self, value = "")
        self.cb = wx.CheckBox(self, label = 'Copy Part Number')
        
        self.revTextCtrl = wx.TextCtrl(self, value = "")
        self.revLabel = wx.StaticText(self, label = "Enter Revision: ")
        
        self.checksumLabel = wx.StaticText(self, label = "CRC-32 Checksum: ")
        
        self.nfTextCtrl = wx.TextCtrl(self, value = "")
        self.nfLabel = wx.StaticText(self,label = "Enter new name: ")
        
    def bindEvents(self):
        for control, event, handler in             [(self.openButton,wx.EVT_BUTTON, self.onOpen),
             (self.cb, wx.EVT_CHECKBOX, self.onChecked),
             (self.generateButton, wx.EVT_BUTTON, self.onGenerate),
             (self.pnTextCtrl, wx.EVT_TEXT, self.onPnEntered),
             (self.nfTextCtrl, wx.EVT_TEXT, self.onNfEntered),
             (self.revTextCtrl, wx.EVT_TEXT, self.onRevEntered)]:
            control.Bind(event, handler)
            
    def doLayout(self):
        raise NotImplementedError

    def onOpen(self, event):
        self.dirname = ''
        dlg = wx.FileDialog(self, "Choose a file", self.dirname, "", "*.*", 
                           wx.OPEN)
        if dlg.ShowModal() == wx.ID_OK:
            self.filename = dlg.GetFilename()
            self.dirname = dlg.GetDirectory()
            self.filePath = os.path.join(self.dirname, self.filename)
            self.checkSum = CRC32_from_file(self.filePath)
            self.__log1(self.checkSum)
        dlg.Destroy()
        
    def onPnEntered(self,event):
        self.partNum = event.GetString()
        #self.__log('pn: %s\n' %self.partNum)  #dont need to log every character 
        
    def onRevEntered(self,event):
        self.rev = event.GetString()
        #self.__log('rev: %s\n' %self.rev)
    
    def __log(self, message):
        ''' Private method to append a string to the logger text
            control. '''
        self.logger.AppendText('%s\n'%message)
    
    def __log1(self, message):
        self.checkSumDisplay.AppendText('Checksum: %s\n' %self.checkSum)
        
    def onGenerate(self,event):
        if(len(self.rev) > 3):
            self.__log('Revision text can only be 3 characters!')
        elif (int(self.partNum) > np.uint32(0xFFFFFFFF) ):
            self.__log('Part number can only be 4 bytes long!')    
        elif (self.filePath == '0'):
            self.__log('Pick a file!\n')
        else:
            self.__log('Generating .nff file')
            Prepend_BIN(self.filePath, 
                        self.partNum,
                        self.rev,
                        self.nfName)

    def onNfEntered(self, event):
        self.nfName = event.GetString()
        
    def onChecked(self,event):
        self.cb = event.GetEventObject()
        if (self.cb.GetValue()):
            #self.__log1('%s' %self.partnum)
            self.nfTextCtrl.Clear()
            self.nfTextCtrl.AppendText(self.partNum)
        else:
            self.nfTextCtrl.Clear()
        
        

class DataEntry(Form):
    def doLayout(self):
    
        boxSizer = wx.BoxSizer(orient=wx.HORIZONTAL)
        gridSizer = wx.FlexGridSizer(rows=15, cols=2, vgap=10,hgap=10)
        
        expandOption = dict(flag=wx.EXPAND)
        noOptions = dict()
        emptySpace = ((0, 0), noOptions)
        
        #set order for spacing 
        for control, options in             [(self.pnLabel, noOptions),(self.pnTextCtrl, expandOption),
             (self.revLabel, noOptions),(self.revTextCtrl, expandOption),
             (self.nfLabel, noOptions),(self.nfTextCtrl, expandOption),
             (self.cb, noOptions),
             emptySpace,
             (self.checksumLabel, noOptions),
             (self.checkSumDisplay, noOptions),
             (self.openButton, dict(flag=wx.ALIGN_CENTER)),
             emptySpace,
             (self.generateButton, dict(flag=wx.ALIGN_CENTER))]:
            gridSizer.Add(control, **options)
        #add options in frame class above
        
        for control, options in             [(gridSizer, dict(border=5, flag = wx.ALL)),
             (self.logger, dict(border=5, flag=wx.ALL|wx.EXPAND, 
                proportion=1))]:
            boxSizer.Add(control, **options)
        
        self.SetSizerAndFit(boxSizer)


class MainFrame(wx.Frame):
    def __init__(self, *args, **kwargs):
        super(MainFrame, self).__init__(*args,**kwargs)
        
        #menu stuff
        self.CreateStatusBar()
        filemenu = wx.Menu()
        menuExit = filemenu.Append(wx.ID_EXIT, "E&xit", "Terminate the program")
        menuBar = wx.MenuBar()
        menuBar.Append(filemenu, "&File")
        self.SetMenuBar(menuBar)
        self.Show(1)        
        
        notebook = wx.Notebook(self)
        form1 = DataEntry(notebook)
        notebook.AddPage(form1, 'Generating .nff file...')
        self.SetClientSize(notebook.GetBestSize())

def Prepend_BIN(filename, partNum, rev, nfName):

    while (len(rev) < 4): #Pad rev with null characters
        rev += '\0'
    #while (sys.getsizeof(partNum) < 4):
        #partNum += '\0'
        
    NFF =  CRC32_from_file(filename) ##get CRC32 checksum
    firmSize = '\0\0\0\0' ## ^^
    newFile = nfName + ".nff" ##file output name


    partNum = int(partNum) #string to int
    partNum = struct.pack('<L', partNum) #convert to little endian hex

    NFF = int(NFF, 16) #convert CRC32 to int
    NFF = struct.pack('<L', NFF) #convert back to little end. hex


    with open(filename, "rb") as old, open(newFile, "wb") as new:
        new.write("NILFISK\0")
        new.write(partNum) #part number hex 
        new.write(rev) #firmware revision
        new.write(firmSize) #dont know if need?
        new.write(NFF) #input crc32 checkusm
        new.write(old.read()) #fill with all the other .bin data    

#generate CRC-32 checksum, don't know how it works
def CRC32_from_file(filename):
    buf = open(filename,'rb').read()
    buf = (binascii.crc32(buf) & 0xFFFFFFFF)
    string =  "%08X" % buf
    return string    

if __name__ == '__main__':
    app = wx.App(0)
    frame = MainFrame(None, title='Prepend header for .nff files')
    frame.Show()
    app.MainLoop()

