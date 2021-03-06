import sys
import shutil
import os
import csv
import datetime
import numpy as np
import pandas as pd
import pyqtgraph.exporters
import pyqtgraph as pg
from PyQt5 import QtWidgets as qtw
from PyQt5 import QtCore as qtc
from PyQt5 import QtGui as qtg

import scipy.signal

from PDF import PDF
from about import Ui_Form
from layout import Ui_MainWindow


class About(qtw.QWidget):
    def __init__(self):
        super().__init__()
        self.ui = Ui_Form()
        self.ui.setupUi(self)

        self.show()


class MainWindow(qtw.QMainWindow):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)

        self.filenames = ['', '', '']
        self.graphChannels = [self.ui.signal1Graph,
                              self.ui.signal2Graph, self.ui.signal3Graph]
        self.spectrogramChannels = [
            self.ui.spectrogram1Graph, self.ui.spectrogram2Graph, self.ui.spectrogram3Graph]
        self.timers = [self.ui.timer1, self.ui.timer2, self.ui.timer3]
        self.pen = [pg.mkPen(color=(255, 0, 0), width=1), pg.mkPen(
            color=(0, 255, 0), width=1), pg.mkPen(color=(0, 0, 255), width=1)]

        self.PLOT_DIR = 'Plots'
        self.PDF_DIR = 'PDFs'
        self.amplitude = [[], [], []]
        self.time = [[], [], []]

        self.upToDatePlots = [[], [], []]
        self.spectrogramData = [None, None, None]
        self.pointsToAppend = [0, 0, 0]
        self.isResumed = [False, False, False]
        self.setChannelChecked = [self.ui.showChannel1,
                                  self.ui.showChannel2, self.ui.showChannel3]
        self.channelComponents = [self.ui.channel1,
                                  self.ui.channel2, self.ui.channel3]

        self.CHANNEL1 = 0
        self.CHANNEL2 = 1
        self.CHANNEL3 = 2

        self.ui.showChannel1.setChecked(True)
        self.ui.showChannel2.setChecked(True)
        self.ui.showChannel3.setChecked(True)
        self.ui.channel1.show()
        self.ui.channel2.show()
        self.ui.channel3.show()

        self.ui.showChannel1.stateChanged.connect(
            lambda: self.toggle(self.CHANNEL1))
        self.ui.showChannel2.stateChanged.connect(
            lambda: self.toggle(self.CHANNEL2))
        self.ui.showChannel3.stateChanged.connect(
            lambda: self.toggle(self.CHANNEL3))

        self.ui.actionAbout.triggered.connect(lambda: self.showAbout())
        self.ui.actionExit.triggered.connect(lambda: self.close())
        self.ui.actionNew.triggered.connect(lambda: self.create_new_window())

        self.ui.actionOpenChannel1.triggered.connect(
            lambda: self.browse(self.CHANNEL1))
        self.ui.playBtn1.clicked.connect(lambda: self.play(self.CHANNEL1))
        self.ui.pauseBtn1.clicked.connect(lambda: self.pause(self.CHANNEL1))
        self.ui.focusBtn1.clicked.connect(
            lambda: self.graphChannels[self.CHANNEL1].getPlotItem().enableAutoRange())
        self.ui.zoomInBtn1.clicked.connect(lambda: self.zoomin(self.CHANNEL1))
        self.ui.zoomOutBtn1.clicked.connect(
            lambda: self.zoomout(self.CHANNEL1))
        self.ui.clearBtn1.clicked.connect(lambda: self.clear(self.CHANNEL1))

        self.ui.actionOpenChannel2.triggered.connect(
            lambda: self.browse(self.CHANNEL2))
        self.ui.playBtn2.clicked.connect(lambda: self.play(self.CHANNEL2))
        self.ui.pauseBtn2.clicked.connect(lambda: self.pause(self.CHANNEL2))
        self.ui.focusBtn2.clicked.connect(
            lambda: self.graphChannels[self.CHANNEL2].getPlotItem().enableAutoRange())
        self.ui.zoomInBtn2.clicked.connect(lambda: self.zoomin(self.CHANNEL2))
        self.ui.zoomOutBtn2.clicked.connect(
            lambda: self.zoomout(self.CHANNEL2))
        self.ui.clearBtn2.clicked.connect(lambda: self.clear(self.CHANNEL2))

        self.ui.actionOpenChannel3.triggered.connect(
            lambda: self.browse(self.CHANNEL3))
        self.ui.playBtn3.clicked.connect(lambda: self.play(self.CHANNEL3))
        self.ui.pauseBtn3.clicked.connect(lambda: self.pause(self.CHANNEL3))
        self.ui.focusBtn3.clicked.connect(
            lambda: self.graphChannels[self.CHANNEL3].getPlotItem().enableAutoRange())
        self.ui.zoomInBtn3.clicked.connect(lambda: self.zoomin(self.CHANNEL3))
        self.ui.zoomOutBtn3.clicked.connect(
            lambda: self.zoomout(self.CHANNEL3))
        self.ui.clearBtn3.clicked.connect(lambda: self.clear(self.CHANNEL3))

        self.ui.generatePDF.clicked.connect(lambda: self.generatePDF())

        self.show()

    def showAbout(self) -> None:
        self.about = About()
        self.about.show()

    def play(self, channel: int) -> None:
        if not self.amplitude[channel]:
            self.browse(channel)
        if not self.isResumed[channel]:
            self.timers[channel].start()
            self.isResumed[channel] = True

    def pause(self, channel: int) -> None:
        if not self.amplitude[channel]:
            self.browse(channel)
        if self.isResumed[channel]:
            self.timers[channel].stop()
            self.isResumed[channel] = False

    def clear(self, channel: int) -> None:
        if self.amplitude[channel]:
            self.graphChannels[channel].removeItem(self.upToDatePlots[channel])
            self.spectrogramChannels[channel].removeItem(
                self.spectrogramData[channel])
            self.timers[channel].stop()
            self.isResumed[channel] = False
            self.amplitude[channel] = []
            self.time[channel] = []
            self.upToDatePlots[channel] = []
            self.spectrogramData[channel] = None

    def toggle(self, channel: int) -> None:
        if(self.channelComponents[channel].isVisible()):
            self.channelComponents[channel].hide()
            self.setChannelChecked[channel].setChecked(False)
            self.clear(channel)
        else:
            self.setChannelChecked[channel].setChecked(True)
            self.channelComponents[channel].show()

    def create_new_window(self):
        self.newWindow = MainWindow()
        self.newWindow.show()

    def browse(self, channel: int) -> None:
        self.toggle(channel)

        # self.clear(channel)
        self.filenames[channel] = qtw.QFileDialog.getOpenFileName(
            None, 'Load Signal', './', "Raw Data(*.csv *.xls *.txt)")
        path = self.filenames[channel][0]
        self.openFile(path, channel)

    def openFile(self, path: str, channel: int) -> None:
        with open(path, 'r') as csv_file:
            csv_reader = csv.reader(csv_file, delimiter=',')
            for line in csv_reader:
                self.amplitude[channel].append(float(line[1]))
                self.time[channel].append(float(line[0]))
        self.isResumed[channel] = True

        self.plotGraph(channel)
        self.plotSpectrogram(channel)

    def plotGraph(self, channel: int) -> None:
        self.upToDatePlots[channel] = self.graphChannels[channel].plot(
            self.time[channel], self.amplitude[channel], name='CH1', pen=self.pen[channel])
        self.graphChannels[channel].plotItem.setLimits(
            xMin=0, xMax=1.0, yMin=min(self.amplitude[channel]), yMax=max(self.amplitude[channel]))

        self.pointsToAppend[channel] = 0
        self.timers[channel].setInterval(150)
        self.timers[channel].timeout.connect(lambda: self.updatePlot(channel))
        self.timers[channel].start()

    def updatePlot(self, channel: int) -> None:
        xaxis = self.time[channel][:self.pointsToAppend[channel]]
        yaxis = self.amplitude[channel][:self.pointsToAppend[channel]]
        self.pointsToAppend[channel] += 20
        if self.pointsToAppend[channel] > len(self.time[channel]):
            self.timers[channel].stop()

        if self.time[channel][self.pointsToAppend[channel]] > 1.0:
            self.graphChannels[channel].setLimits(xMax=max(
                xaxis, default=0))
        self.graphChannels[channel].plotItem.setXRange(
            max(xaxis, default=0)-1.0, max(xaxis, default=0))

        self.upToDatePlots[channel].setData(xaxis, yaxis)

    def plotSpectrogram(self, channel: int) -> None:
        pyqtgraph.setConfigOptions(imageAxisOrder='row-major')
        fs = 1 / (self.time[channel][1] - self.time[channel][0])
        yaxis = np.array(self.amplitude[channel])
        f, t, Sxx = scipy.signal.spectrogram(yaxis, fs)
        self.spectrogramData[channel] = self.spectrogramChannels[channel].addPlot(
        )

        # Item for displaying image data
        img = pg.ImageItem()
        self.spectrogramData[channel].addItem(img)
        # Add a histogram with which to control the gradient of the image
        hist = pg.HistogramLUTItem()
        # Link the histogram to the image
        hist.setImageItem(img)
        # If you don't add the histogram to the window, it stays invisible, but I find it useful.
        self.spectrogramChannels[channel].addItem(
            self.spectrogramData[channel])
        # Show the window
        self.spectrogramChannels[channel].show()
        # Fit the min and max levels of the histogram to the data available
        hist.setLevels(np.min(Sxx), np.max(Sxx))
        # This gradient is roughly comparable to the gradient used by Matplotlib
        # You can adjust it and then save it using hist.gradient.saveState()
        hist.gradient.restoreState(
            {'mode': 'rgb',
             'ticks': [(0.5, (0, 182, 188, 255)),
                       (1.0, (246, 111, 0, 255)),
                       (0.0, (75, 0, 113, 255))]
             })
        # hist.gradient.showTicks(False)
        # hist.shape
        # hist.layout.setContentsMargins(0, 0, 0, 0)
        # hist.vb.setMouseEnabled(x=False, y=False)

        # hist.vb.setMenuEnabled(False)
        # hist.shape
        # Sxx contains the amplitude for each pixel
        img.setImage(Sxx)
        # Scale the X and Y Axis to time and frequency (standard is pixels)
        img.scale(t[-1]/np.size(Sxx, axis=1),
                  f[-1]/np.size(Sxx, axis=0))
        # Limit panning/zooming to the spectrogram
        self.spectrogramData[channel].setLimits(
            xMin=0, xMax=t[-1], yMin=0, yMax=f[-1])
        # Add labels to the axis
        # self.spectrogramData[channel].setLabel('bottom', "Time", units='s')
        # If you include the units, Pyqtgraph automatically scales the axis and adjusts the SI prefix (in this case kHz)
        # self.spectrogramData[channel].setLabel('left', "Frequency", units='Hz')

    def zoomin(self, channel: int) -> None:
        self.graphChannels[channel].plotItem.getViewBox().scaleBy((0.75, 0.75))

    def zoomout(self, channel: int) -> None:
        self.graphChannels[channel].plotItem.getViewBox().scaleBy((1.25, 1.25))

    def generatePDF(self):
        images = [0, 0, 0]
        Idx = 0
        for channel in range(3):
            if self.amplitude[channel]:
                images[channel] = 1
                Idx += 1
            else:
                self.toggle(channel)

        if not Idx:
            qtw.QMessageBox.information(
                self, 'failed', 'You have to plot a signal first')
            return

        try:
            shutil.rmtree(self.PLOT_DIR)
            os.mkdir(self.PLOT_DIR)
        except FileNotFoundError:
            os.mkdir(self.PLOT_DIR)

        for channel in range(3):
            if images[channel]:
                exporter = pg.exporters.ImageExporter(
                    self.graphChannels[channel].plotItem)
                exporter.parameters()[
                    'width'] = self.graphChannels[channel].plotItem.width()
                exporter.export(f'{self.PLOT_DIR}/plot-{channel}.png')

                exporter = pg.exporters.ImageExporter(
                    self.spectrogramChannels[channel].scene())
                exporter.export(f'{self.PLOT_DIR}/spec-{channel}.png')

        pdf = PDF()
        plots_per_page = pdf.construct(self.PLOT_DIR)

        for elem in plots_per_page:
            pdf.print_page(elem, self.PLOT_DIR)

        now = datetime.datetime.now()
        now = f'{now:%Y-%m-%d %H-%M-%S.%f %p}'
        try:
            os.mkdir(self.PDF_DIR)
        except:
            pass
        pdf.output(f'{self.PDF_DIR}/{now}.pdf', 'F')
        try:
            shutil.rmtree(self.PLOT_DIR)
        except:
            pass

        qtw.QMessageBox.information(self, 'success', 'PDF has been created')


if __name__ == '__main__':
    app = qtw.QApplication(sys.argv)
    mw = MainWindow()
    sys.exit(app.exec_())
