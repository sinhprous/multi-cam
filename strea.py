from PyQt4 import QtCore, QtGui, uic
import sys
import cv2 as cv
import numpy as np
import threading
import time
import queue
import os
import subprocess as sp

import os
os.environ["OPENCV_FFMPEG_CAPTURE_OPTIONS"] = "rtsp_transport;udp"


running = False
running1 = False
faceid_thread = None
q = queue.Queue()

form_class = uic.loadUiType("form1.ui")[0]

font = cv.FONT_HERSHEY_SIMPLEX

# iniciate id counter
id = 0
minW = 64.0
minH = 48.0

isStop = False


def grab(cam, cam1, queue, width, height, fps):
    global running
    global running1
    global minW
    global minH
    global isStop

    capture = cv.VideoCapture(cam)
    capture.set(cv.CAP_PROP_FRAME_WIDTH, width)
    capture.set(cv.CAP_PROP_FRAME_HEIGHT, height)
    capture.set(cv.CAP_PROP_FPS, fps)
    capture.set(3, 640)  # set video widht
    capture.set(4, 480)  # set video height

    # Define min window size to be recognized as a face
    minW = 0.1 * capture.get(3)
    minH = 0.1 * capture.get(4)

    capture1 = cv.VideoCapture(cam1)
    while (1):
        while (running):
            capture.grab()
            retval, img = capture.retrieve(0)
            if not queue.empty():
                try:
                    queue.get_nowait()
                except:
                    pass
            queue.put(img)
        while not q.empty():
            queue.get_nowait()
        while (running1):
            capture1.grab()
            ret, img = capture1.read()
            if not ret:
                break
            if not queue.empty():
                try:
                    queue.get_nowait()
                except:
                    pass
            queue.put(img)
        while not q.empty():
            queue.get_nowait()
        while isStop:
            sys.exit()


class OwnImageWidget(QtGui.QWidget):
    def __init__(self, parent=None):
        super(OwnImageWidget, self).__init__(parent)
        self.image = None

    def setImage(self, image):
        self.image = image
        sz = image.size()
        self.setMinimumSize(sz)
        self.update()

    def paintEvent(self, event):
        qp = QtGui.QPainter()
        qp.begin(self)
        if self.image:
            qp.drawImage(QtCore.QPoint(0, 0), self.image)
        qp.end()


class form1Class(QtGui.QMainWindow, form_class):
    def __init__(self, parent=None):
        QtGui.QMainWindow.__init__(self, parent)
        self.setupUi(self)
        self.center()
        self.startButton1.clicked.connect(self.start_clicked1)
        self.startButton1.setStyleSheet("background: black")
        self.Cam_1 = OwnImageWidget(self.Cam_1)
        self.window_width = 620  # self.ImgWidget.frameSize().width()
        self.window_height = 400  # self.ImgWidget.frameSize().height()
        self.timer = QtCore.QTimer(self)
        self.timer.timeout.connect(self.update_frame)
        self.timer.start(1)

    def center(self):
        qr = self.frameGeometry()
        cp = QtGui.QDesktopWidget().availableGeometry().center()
        qr.moveCenter(cp)
        self.move(qr.topLeft())

    def start_clicked1(self):
        global running
        global running1
        running1 = True
        running = False
        if not capture_thread.isAlive():
            capture_thread.start()
        self.startButton1.setEnabled(False)
        self.startButton1.setText('Starting...')

    def update_frame(self):
        global minW
        global minH
        global names
        # global recognizer
        if not q.empty():
            if running:
                self.startButton.setText('Camera is live')
            if running1:
                self.startButton1.setText('Camera is live')
            img = q.get()

            img_height, img_width, img_colors = img.shape
            scale_w = float(self.window_width) / float(img_width)
            scale_h = float(self.window_height) / float(img_height)
            scale = min([scale_w, scale_h])

            if scale == 0:
                scale = 1

            img = cv.resize(img, None, fx=scale, fy=scale, interpolation=cv.INTER_CUBIC)
            height, width, bpc = img.shape
            bpl = bpc * width
            image = QtGui.QImage(img.data, width, height, bpl, QtGui.QImage.Format_RGB888)
            self.Cam_1.setImage(image)

    def closeEvent(self, event):
        global running
        global running1
        global isStop

        isStop = True
        running = False
        running1 = False
        event.accept()
        self.parent().show()


capture_thread = threading.Thread(target=grab, args=(0, "rtsp://192.168.1.38:5554/camera", q, 1280, 720, 30))
if __name__ == '__main__':
    app = QtGui.QApplication(sys.argv)
    form5 = form1Class()
    form5.setWindowTitle('Form 5')
    form5.show()
    app.exec_()
