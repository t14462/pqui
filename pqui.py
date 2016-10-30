#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys, os, re, getpass, math
from PyQt5.QtWidgets import (QMainWindow, QProgressBar,
    QPushButton, QComboBox, QMessageBox, QAction, QFileDialog, QApplication, QLabel)
from PyQt5.QtGui import QIcon, QPixmap, QPainter, QColor, QBrush
from PyQt5.QtCore import Qt
from subprocess import Popen, PIPE, DEVNULL



OVERFLOW_METER_STYLE = """
QProgressBar{
    border: 0;
    background: red;
    color: transparent;
    display: none;
}

QProgressBar::chunk {
    background-color: green;
}
"""


APP_PATH = os.path.dirname(os.path.realpath(__file__))

OFFSET_Y = 50


class p(QMainWindow):

    fname = ''
    fsize = 0
    devsize = 0
    offsetX = 0.00

    def __init__(self):
        super().__init__()

        self.initUI()



    def fillDevList(self):

      self.usblist.clear()
      with Popen("lsblk -d -o RM,RO,NAME,SIZE,MODEL | grep '^ 1  0 sd[b-z]'",
      shell=True,
      stdout=PIPE,
      stderr=DEVNULL,
      bufsize=1,
      universal_newlines=True) as lsrem:
        for item in lsrem.stdout:
          if item != '':
            item = re.sub(" +", " ", item)
            item = item.strip()
            item = item.split(' ',4)
            self.usblist.addItem(item[-1] + '  (' + item[3] + ')  ' + item[2])



    def devSize(self):

      device = str(self.usblist.currentText())
      device = re.sub(".+ (sd[b-z])$", r"\1", device)

      with Popen("lsblk -bd -o SIZE /dev/" + device + " | grep '^[0-9]'",
        shell=True,
        stdout=PIPE,
        stderr=DEVNULL,
        bufsize=1,
        universal_newlines=True) as asksize:
        for number in asksize.stdout:
          p.devsize = int(number.strip(),10)

        self.overflowMeter()


    def showDialog(self):

      p.fname = QFileDialog.getOpenFileName(self, 'Open Disk Image', '',"Disk Images (*.raw *.img *.iso *.dmg)")[0]

      if p.fname != '' and os.path.isfile(p.fname):
        with open(p.fname, 'r') as f:
          f.seek(0, os.SEEK_END)
          p.fsize = f.tell()

          self.overflowMeter()


    def initUI(self):

        self.pbar = QProgressBar(self)
        self.pbar.setGeometry(30, 100, 300, 25)

        self.start = QPushButton('Start', self)
        self.start.setGeometry(56, 135, 100, 25)
        self.start.clicked.connect(self.doAction)

        self.fopen = QPushButton('Open', self)
        self.fopen.setGeometry(193, 135, 100, 25)
        self.fopen.clicked.connect(self.showDialog)

        self.refresh = QPushButton('R', self)
        self.refresh.setGeometry(303, 15, 25, 25)
        self.refresh.clicked.connect(self.fillDevList)

        #self.ovm = QProgressBar(self)
        #self.ovm.setGeometry(30, OFFSET_Y, 300, 36)
        #self.ovm.setValue(80)
        #self.ovm.setStyleSheet(OVERFLOW_METER_STYLE)

        pixmap = QPixmap(APP_PATH+"/triangle.png")
        pixmap = pixmap.scaled(22, 22, Qt.KeepAspectRatio)
        self.arrow = QLabel(self)
        self.arrow.setPixmap(pixmap)
        self.arrow.setStyleSheet('QLabel {margin-left: 20px;}')
        self.arrow.move(0, OFFSET_Y+18)

        self.usblist = QComboBox(self)
        self.usblist.setGeometry(30, 15, 273, 25)
        self.usblist.currentIndexChanged.connect(self.devSize)
        self.fillDevList()

        #openFile = QAction(QIcon(APP_PATH+'/open.png'), 'Open', self)
        #openFile.setShortcut('Ctrl+O')
        #openFile.setStatusTip('Open new File')
        #openFile.triggered.connect(self.showDialog)

        #menubar = self.menuBar()
        #fileMenu = menubar.addMenu('&File')
        #fileMenu.addAction(openFile)

        self.statusBar()

        self.setGeometry(300, 300, 360, 250)
        self.setWindowTitle('PyQt USB Imager')
        self.show()



    def WriteItTwice(self, process):

          bOffset = p.fsize%100
          percent = (p.fsize - bOffset) / 100

          for line in process.stderr:

            if re.search("^[0-9]+ ", line):

              bytes = re.sub("^([0-9]+) .+", r"\1", line)
              bytes = bytes.strip()
              
              if bytes != "":

                bytes = int(bytes,10)
                self.pbar.setValue((bytes+bOffset)/percent)
                
                if bytes+bOffset >= p.fsize:
                  self.start.setText('DONE!')
                  self.start.setStyleSheet('QPushButton {font-weight: bold; color: green;}')
                  
                  msgdone = QMessageBox.question(self, 'Message',
                  "DONE!", QMessageBox.Ok)
                  if msgdone == QMessageBox.Ok:
                    self.start.setStyleSheet('')
                    self.start.setText('Start')
                    self.start.setDisabled(False)
                    self.usblist.setDisabled(False)
              
            self.statusBar().showMessage(line)





    def overflowMeter(self):

      clamp = lambda n, minn, maxn: max(min(maxn, n), minn)

      device = str(self.usblist.currentText())
      device = re.sub(".+ (sd[b-z])$", r"\1", device)

      if p.fname != '' and device != '' and os.path.isfile(p.fname):

        if p.devsize > p.fsize:

          p.offsetX = (300*0.8) * (p.fsize / p.devsize)

          self.statusBar().setStyleSheet("QStatusBar{color: green;}")
          self.statusBar().showMessage(p.fname.split('/')[-1]+": OK!")

        else:

          mult = 0.2
          p.offsetX = math.sqrt((p.fsize / p.devsize)) * mult
          p.offsetX = p.offsetX - (p.fsize / p.devsize) * 0.02
          p.offsetX = (clamp(p.offsetX, mult, 1.0) * 60) + 240

          self.statusBar().setStyleSheet("QStatusBar{font-weight: bold; color: red;}")
          self.statusBar().showMessage(p.fname.split('/')[-1]+" bigger than Flash!")

      else:

        p.offsetX = 0
        self.statusBar().setStyleSheet("")
        self.statusBar().showMessage("")

      p.offsetX = int(p.offsetX - (p.offsetX % 1))

      self.arrow.move(p.offsetX, OFFSET_Y+18)



    def doAction(self):

      self.statusBar().setStyleSheet("")

      device = str(self.usblist.currentText())
      device = re.sub(".+ (sd[b-z])$", r"\1", device)

      if p.fname != '' and device != '' and os.path.isfile(p.fname):

        self.usblist.setDisabled(True)
        self.start.setDisabled(True)

        if p.fname.split('/')[-1].split('.')[-1] == "dmg":

          try:
            os.remove("/home/"+getpass.getuser()+"/"+p.fname.split('/')[-1].split('.')[0]+".img")
          except OSError:
            pass

          with Popen(["dmg2img", "-V", "-i", p.fname, "-o", "/home/"+getpass.getuser()+"/"+p.fname.split('/')[-1].split('.')[0]+".img"],
          stdout=PIPE,
          stderr=DEVNULL,
          bufsize=1,
          universal_newlines=True) as proc:
            for line in proc.stdout:
              if re.search("%", line):
                line = re.sub(" +", " ", line)
                line = int(line.split(' ')[-1].split('.')[0])
                self.pbar.setValue(line)

          with open("/home/"+getpass.getuser()+"/"+p.fname.split('/')[-1].split('.')[0]+".img", 'r') as f:
            f.seek(0, os.SEEK_END)
            p.fsize = f.tell()

          self.overflowMeter()

          if p.devsize > p.fsize:

            with Popen(["pkexec", "dd", "status=progress", "if=/home/"+getpass.getuser()+"/"+p.fname.split('/')[-1].split('.')[0]+".img", "of=/dev/"+device, "bs=8M", "conv=notrunc,sync"],
              stdout=DEVNULL,
              stderr=PIPE,
              bufsize=1,
              universal_newlines=True) as proc:
                self.WriteItTwice(proc)

          else:
            msgOverflow = QMessageBox.question(self, 'Message',
            "OVERFLOW!", QMessageBox.Ok)
            if msgOverflow == QMessageBox.Ok:
              self.start.setDisabled(False)
              self.usblist.setDisabled(False)

          try:
            os.remove("/home/"+getpass.getuser()+"/"+p.fname.split('/')[-1].split('.')[0]+".img")
          except OSError:
            pass


        else:
        
          with Popen(["pkexec", "dd", "if="+p.fname, "of=/dev/"+device, "bs=8M", "conv=notrunc,sync", "status=progress"],
          stdout=DEVNULL,
          stderr=PIPE,
          bufsize=1,
          universal_newlines=True) as proc:
            self.WriteItTwice(proc)






    def paintEvent(self, e):

        qp = QPainter()
        qp.begin(self)
        self.drawRectangles(qp)
        qp.end()


    def drawRectangles(self, qp):

        col = QColor(0, 255, 0, 255)
        qp.setPen(col)
        qp.setBrush(col)
        qp.drawRect(30, OFFSET_Y, 240, 36)

        col = QColor(255, 0, 0, 255)
        qp.setPen(col)
        qp.setBrush(col)
        qp.drawRect(270, OFFSET_Y, 60, 36)





if __name__ == '__main__':

    app = QApplication(sys.argv)
    ex = p()
    sys.exit(app.exec_())
