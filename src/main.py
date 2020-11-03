#!/usr/bin/env python3.7

import magic
import zipfile
import rarfile
import gui
from PyQt5 import QtWidgets, QtCore
from PyQt5.QtWidgets import QAbstractSlider
from PyQt5.QtGui import QPixmap
from PyQt5.QtCore import Qt

class MangaViewer(QtWidgets.QMainWindow, gui.Ui_MainWindow):
    resized = QtCore.pyqtSignal()
    curImage = ""
    def __init__(self):
        super().__init__()
        self.setupUi(self)
        self.resized.connect(self.drawImage)
        self.scrollArea.verticalScrollBar().actionTriggered.connect(self.scrolled)
        self.statusbar.setVisible(False)

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_H or event.key() == Qt.Key_P or event.key() == Qt.Key_Backspace:
            self.prevImage()
        elif event.key() == Qt.Key_L or event.key() == Qt.Key_N or event.key() == Qt.Key_Space:
            self.nextImage()
        elif event.key() == Qt.Key_J:
            self.scrollArea.verticalScrollBar().triggerAction(QAbstractSlider.SliderSingleStepAdd)
        elif event.key() == Qt.Key_K:
            self.scrollArea.verticalScrollBar().triggerAction(QAbstractSlider.SliderSingleStepSub)
        elif event.key() == Qt.Key_B:
            self.statusbar.setVisible(not self.statusbar.isVisible())
            self.drawImage()
        elif event.key() == Qt.Key_S:
            self.firstImage()
        elif event.key() == Qt.Key_E:
            self.lastImage()

    def scrolled(self, action):
        scrollbar = self.scrollArea.verticalScrollBar()

        if scrollbar.value() == scrollbar.maximum():
            if action == QAbstractSlider.SliderSingleStepAdd or action == QAbstractSlider.SliderPageStepAdd or action == QAbstractSlider.SliderToMaximum:
                self.nextImage()

        if scrollbar.value() == scrollbar.minimum():
            if action == QAbstractSlider.SliderSingleStepSub or action == QAbstractSlider.SliderPageStepSub or action == QAbstractSlider.SliderToMinimum:
                self.prevImage()

    def setArchive(self, archive):
        self.archive = archive

    def setImage(self, data, name):
        self.statusbar.showMessage(name)
        self.curImage = data

    def drawImage(self):
        if (self.curImage == ""):
            return

        pixmap = QPixmap()
        pixmap.loadFromData(self.curImage)

        # best fit
        if (self.statusbar.isVisible()):
            pixmap = pixmap.scaled(self.width(), self.height() - self.statusbar.height(), Qt.KeepAspectRatio, Qt.SmoothTransformation)
        else:
            pixmap = pixmap.scaled(self.width(), self.height(), Qt.KeepAspectRatio, Qt.SmoothTransformation)

        self.label.setPixmap(pixmap)

    def setScrollBar(self, top):
        scrollbar = self.scrollArea.verticalScrollBar()
        if top:
            scrollbar.setValue(scrollbar.minimum())
        else:
            scrollbar.setValue(scrollbar.maximum())

    def firstImage(self):
        self.setImage(self.archive.getFirstImage(), self.archive.curFile)
        self.drawImage()
        self.setScrollBar(True);

    def lastImage(self):
        self.setImage(self.archive.getLastImage(), self.archive.curFile)
        self.drawImage()
        self.setScrollBar(True);

    def nextImage(self):
        self.setImage(self.archive.getNextImage(), self.archive.curFile)
        self.drawImage()
        self.setScrollBar(True);

    def prevImage(self):
        self.setImage(self.archive.getPrevImage(), self.archive.curFile)
        self.drawImage()
        self.setScrollBar(False);

    def resizeEvent(self, event):
        self.resized.emit()
        return super(MangaViewer, self).resizeEvent(event)

class MangaArchive():
    def __init__(self, path, mimetype):
        if mimetype == "application/zip":
            self.archive = zipfile.ZipFile(path, mode='r', compression=zipfile.ZIP_DEFLATED)
        elif mimetype == "application/x-rar":
            self.archive = rarfile.RarFile(path)

        self.index = 0

    def checkFile(self):
        try:
            mimetype = magic.from_buffer(self.archive.read(self.curFile), mime=True)
            return "image" in mimetype;
        except:
            return False

    def getFirstImage(self):
        self.index = 0
        self.curFile = self.archive.namelist()[self.index]
        if (self.checkFile()):
            return self.archive.read(self.curFile)
        else:
            return self.getNextImage()

    def getLastImage(self):
        self.index = len(self.archive.namelist()) - 1
        self.curFile = self.archive.namelist()[self.index]
        if (self.checkFile()):
            return self.archive.read(self.curFile)
        else:
            return self.getPrevImage()

    def getNextImage(self):
        self.index = self.index + 1
        if (self.index == len(self.archive.namelist())):
            # TODO next archive
            self.getPrevImage()

        self.curFile = self.archive.namelist()[self.index]
        if (self.checkFile()):
            return self.archive.read(self.curFile)
        else:
            return self.getNextImage()

    def getPrevImage(self):
        self.index = self.index - 1
        self.curFile = self.archive.namelist()[self.index]
        if (self.checkFile()):
            return self.archive.read(self.curFile)
        elif self.index == 0:
            return self.getNextImage()
        elif self.index < 0:
            # TODO prev archive
            self.index = self.index + 1
            self.curFile = self.archive.namelist()[self.index]
            return self.archive.read(self.curFile)
        else:
            return self.getPrevImage()

def main():
    import sys

    if (len(sys.argv) > 1 and len(sys.argv[1]) > 0):
        if sys.argv[1] == "-h" or sys.argv[1] == "--help":
            print("Usage: " + sys.argv[0] + " /path/to/zip/or/rar/archive")
            print("Keybinds:")
            print("\tPrevious Image: H, P, Backspace")
            print("\tNext Image: L, N, Space")
            print("\tScroll Down: J, Down, Page Down")
            print("\tScroll Up: K, Up, Page Up")
            print("\tToggle Statusbar: B")
            print("\tFirst Image: S")
            print("\tLast Image: E")
            sys.exit()

        mimetype = magic.from_file(sys.argv[1], mime=True)
        if mimetype == "application/zip" or mimetype == "application/x-rar":
            archive = MangaArchive(sys.argv[1], mimetype)
    else:
        print("Usage: " + sys.argv[0] + " /path/to/zip/or/rar/archive")
        sys.exit()

    app = QtWidgets.QApplication(sys.argv)
    window = MangaViewer()
    
    window.setArchive(archive)
    window.firstImage()
    window.show()

    sys.exit(app.exec_())

if __name__ == '__main__':
    main()
