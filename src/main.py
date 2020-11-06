#!/usr/bin/env python3

import magic
import zipfile
import rarfile
import gui
import os
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
        vscrollBar = self.scrollArea.verticalScrollBar()
        vscrollBar.actionTriggered.connect(self.scrolled)
        self.statusbar.setVisible(False)

    def keyPressEvent(self, event):
        vscrollBar = self.scrollArea.verticalScrollBar()
        if (event.key() == Qt.Key_H or
                event.key() == Qt.Key_P or
                event.key() == Qt.Key_Backspace):
            self.prevImage()
        elif (event.key() == Qt.Key_L or
                event.key() == Qt.Key_N or
                event.key() == Qt.Key_Space):
            self.nextImage()
        elif event.key() == Qt.Key_J:
            vscrollBar.triggerAction(QAbstractSlider.SliderSingleStepAdd)
        elif event.key() == Qt.Key_K:
            vscrollBar.triggerAction(QAbstractSlider.SliderSingleStepSub)
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
            if (action == QAbstractSlider.SliderSingleStepAdd or
                    action == QAbstractSlider.SliderPageStepAdd or
                    action == QAbstractSlider.SliderToMaximum):
                self.nextImage()

        if scrollbar.value() == scrollbar.minimum():
            if (action == QAbstractSlider.SliderSingleStepSub or
                    action == QAbstractSlider.SliderPageStepSub or
                    action == QAbstractSlider.SliderToMinimum):
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
        displayHeight = self.height()
        if (self.statusbar.isVisible()):
            displayHeight = self.height() - self.statusbar.height()

        pixmap = pixmap.scaled(self.width(),
                               displayHeight,
                               Qt.KeepAspectRatio,
                               Qt.SmoothTransformation)

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
        self.setScrollBar(True)

    def lastImage(self):
        self.setImage(self.archive.getLastImage(), self.archive.curFile)
        self.drawImage()
        self.setScrollBar(True)

    def nextImage(self):
        nextImage = self.archive.getNextImage()
        if nextImage is not None:
            self.setImage(nextImage, self.archive.curFile)
        else:
            directory = Directory(self.archive)
            nextArchive = directory.getNextArchive(self.archive)
            if nextArchive is not None:
                self.archive.close()
                self.archive = Archive(nextArchive)
                self.firstImage()
                return
            else:
                self.setImage(self.curImage, self.archive.curFile)
        self.drawImage()
        self.setScrollBar(True)

    def prevImage(self):
        prevImage = self.archive.getPrevImage()
        if prevImage is not None:
            self.setImage(prevImage, self.archive.curFile)
        else:
            directory = Directory(self.archive)
            prevArchive = directory.getPrevArchive(self.archive)
            if prevArchive is not None:
                self.archive.close()
                self.archive = Archive(prevArchive)
                self.lastImage()
                return
            else:
                self.setImage(self.curImage, self.archive.curFile)

        self.drawImage()
        self.setScrollBar(False)

    def resizeEvent(self, event):
        self.resized.emit()
        return super(MangaViewer, self).resizeEvent(event)


class Archive():
    def __init__(self, path):
        self.path = os.path.abspath(path)
        self.mimetype = magic.from_file(path, mime=True)
        if self.mimetype == "application/zip":
            self.archive = zipfile.ZipFile(path,
                                           mode='r',
                                           compression=zipfile.ZIP_DEFLATED)
        elif self.mimetype == "application/x-rar":
            self.archive = rarfile.RarFile(path)
        else:
            self.filelist = None
            self.index = 0
            return None
        self.filelist = self.archive.namelist()
        self.filelist.sort()
        self.index = 0

    def close(self):
        self.archive.close()

    def checkFile(self):
        try:
            mimetype = magic.from_buffer(self.archive.read(self.curFile),
                                         mime=True)
            return "image" in mimetype
        except magic.MagicException:
            return False
        except TypeError:
            return False

    def getFirstImage(self):
        self.index = 0
        self.curFile = self.filelist[self.index]
        if (self.checkFile()):
            return self.archive.read(self.curFile)
        else:
            return self.getNextImage()

    def getLastImage(self):
        self.index = len(self.filelist) - 1
        self.curFile = self.filelist[self.index]
        if (self.checkFile()):
            return self.archive.read(self.curFile)
        else:
            return self.getPrevImage()

    def getNextImage(self):
        self.index = self.index + 1
        if (self.index >= len(self.filelist)):
            self.index = self.index - 1
            return None

        self.curFile = self.filelist[self.index]
        if (self.checkFile()):
            return self.archive.read(self.curFile)
        else:
            return self.getNextImage()

    def getPrevImage(self):
        self.index = self.index - 1
        if (self.index < 0):
            self.index = self.index + 1
            return None

        self.curFile = self.filelist[self.index]
        if (self.checkFile()):
            return self.archive.read(self.curFile)
        else:
            return self.getPrevImage()


class Directory():
    def __init__(self, archive):
        self.directory = sorted(os.scandir(os.path.dirname(archive.path)),
                                key=lambda e: e.name)

    def getNextArchive(self, archive):
        foundCurrent = False
        for entry in self.directory:
            if entry.is_file():
                if foundCurrent:
                    if isArchive(entry.path):
                        return entry.path
                if entry.name == os.path.basename(archive.path):
                    foundCurrent = True
        return None

    def getPrevArchive(self, archive):
        foundCurrent = False
        lastArchive = None

        for entry in self.directory:
            if entry.is_file():
                if entry.name == os.path.basename(archive.path):
                    return lastArchive
                if isArchive(entry.path):
                    lastArchive = entry.path
        return None


def isArchive(archive):
    try:
        mimetype = magic.from_file(archive, mime=True)
        return mimetype == "application/zip" or mimetype == "application/x-rar"
    except magic.MagicException:
        return False
    except TypeError:
        return False


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

        infile = sys.argv[1]
        archive = None
        if os.path.exists(infile) and os.path.isfile(infile):
            archive = Archive(infile)

        if archive is None or archive.filelist is None:
            print("Usage: " + sys.argv[0] + " /path/to/zip/or/rar/archive")
            sys.exit()
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
