import pyqtgraph as pg
import pyqtgraph.opengl as gl
from pyqtgraph.Qt import QtCore, QtGui
import serial
import numpy as np

# Serial port config
ser = serial.Serial('COM5', 9600)

from pyqtgraph.Qt import QtWidgets
app = QtWidgets.QApplication([])

w = gl.GLViewWidget()
w.show()
w.setWindowTitle('Real-Time 3D Point Cloud')
w.setCameraPosition(distance=20)

g = gl.GLGridItem()
w.addItem(g)

# Initialize Blank Points
points = np.zeros((1000, 3))
sp = gl.GLScatterPlotItem(pos=points, color=(1,1,1,1), size=5)
w.addItem(sp)

def update():
    global points
    line = ser.readline().decode('utf-8', errors='ignore').strip()
    if line.startswith("Point:"):
        try:
            parts = line.replace("Point:", "").split()
            x = float(parts[0].split('=')[1])
            y = float(parts[1].split('=')[1])
            z = float(parts[2].split('=')[1])
            new_point = np.array([[x, y, z]])
            points = np.vstack((points, new_point))
            if len(points) > 1000:  # keep last 1000
                points = points[-1000:]
            sp.setData(pos=points)
        except Exception as e:
            print("Parse error:", e)

timer = QtCore.QTimer()
timer.timeout.connect(update)
timer.start(10)

QtWidgets.QApplication.instance().exec_()
