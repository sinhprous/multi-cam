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
q1 = queue.Queue()
q2 = queue.Queue()

form_class = uic.loadUiType("multicam.ui")[0]

isStop = False
low_threshold = False


def grab(cam, queue):
    global running
    global isStop

    capture = cv.VideoCapture(cam)
    while (1):
        while (running):
            capture.grab()
            ret, img = capture.read()
            if not ret:
                break
            if not queue.empty():
                try:
                    queue.get_nowait()
                except:
                    pass
            img = cv.cvtColor(img, cv.COLOR_RGB2BGR)
            queue.put(img)
        while not queue.empty():
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


class formClass(QtGui.QMainWindow, form_class):
    def __init__(self, parent=None):
        QtGui.QMainWindow.__init__(self, parent)
        self.setupUi(self)
        self.center()
        self.startButton.clicked.connect(self.start_streaming)
        self.startButton.setStyleSheet("background: black; color: white;")
        self.thresholdButton.clicked.connect(self.set_threshold)
        self.thresholdButton.setStyleSheet("background: red; color: white;")
        self.Cam_1 = OwnImageWidget(self.Cam_1)
        self.Cam_2 = OwnImageWidget(self.Cam_2)
        self.window_width = 950
        self.window_height = 500
        self.timer = QtCore.QTimer(self)
        self.timer.timeout.connect(self.update_frame)
        self.timer.start(1)

    def center(self):
        qr = self.frameGeometry()
        cp = QtGui.QDesktopWidget().availableGeometry().center()
        qr.moveCenter(cp)
        self.move(qr.topLeft())

    def start_streaming(self):
        global running
        running = True
        capture_thread_1 = threading.Thread(target=grab,
                                            args=("rtsp://admin:iphone3gs@%s:554/onvif1" % self.ipCam_1.text(), q1))
        capture_thread_2 = threading.Thread(target=grab,
                                            args=("rtsp://admin:iphone3gs@%s:554/onvif1" % self.ipCam_2.text(), q2))
        self.ipCam_1.setVisible(False)
        self.ipCam_2.setVisible(False)
        if not capture_thread_1.isAlive():
            capture_thread_1.start()
        if not capture_thread_2.isAlive():
            capture_thread_2.start()
        self.startButton.setEnabled(False)
        self.startButton.setText('Starting...')

    def set_threshold(self):
        global low_threshold
        low_threshold = not low_threshold
        if low_threshold:
            self.thresholdButton.setText('High Threshold')
            self.thresholdButton.setStyleSheet("background: green; color: white;")
        else:
            self.thresholdButton.setText('Low Threshold')
            self.thresholdButton.setStyleSheet("background: red; color: white;")

    def update_frame(self):
        count = 0
        for q in [q1, q2]:
            count += 1
            if not q.empty():
                if running:
                    self.startButton.setText('Camera is live')
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
                if count == 1:
                    self.Cam_1.setImage(image)
                elif count == 2:
                    self.Cam_2.setImage(image)

    def closeEvent(self, event):
        global running
        global isStop

        isStop = True
        running = False
        event.accept()


if __name__ == '__main__':
    app = QtGui.QApplication(sys.argv)
    form5 = formClass()
    form5.setWindowTitle('AntiMatlab')
    form5.show()
    app.exec_()
