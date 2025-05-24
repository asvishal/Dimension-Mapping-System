import pyqtgraph as pg
import pyqtgraph.opengl as gl
from pyqtgraph.Qt import QtCore, QtWidgets
import serial
import numpy as np

ser = serial.Serial('COM5', 9600)
app = QtWidgets.QApplication([])

w = gl.GLViewWidget()
w.show()
w.setWindowTitle('Real-Time 3D Point Cloud with Bounding Box')
w.setCameraPosition(distance=40)
grid = gl.GLGridItem()
w.addItem(grid)

points = np.empty((0, 3))
scatter = gl.GLScatterPlotItem(pos=points, color=(0, 1, 0, 1), size=5)
w.addItem(scatter)

edges = [
    (0, 1), (1, 2), (2, 3), (3, 0),
    (4, 5), (5, 6), (6, 7), (7, 4),
    (0, 4), (1, 5), (2, 6), (3, 7)
]

box_lines = []
for _ in edges:
    line = gl.GLLinePlotItem(color=(1, 0, 0, 1), width=2.0)
    w.addItem(line)
    box_lines.append(line)

def update():
    global points
    try:
        line = ser.readline().decode('utf-8', errors='ignore').strip()
        if line.startswith("Point:"):
            parts = line.replace("Point:", "").split()
            x = float(parts[0].split('=')[1])
            y = float(parts[1].split('=')[1])
            z = float(parts[2].split('=')[1])
            new_point = np.array([[x, y, z]])
            points = np.vstack((points, new_point))
            if len(points) > 1000:
                points = points[-1000:]
            scatter.setData(pos=points)

            if len(points) >= 8:
                # Compute bounding box
                min_vals = np.min(points, axis=0)
                max_vals = np.max(points, axis=0)
                x0, y0, z0 = min_vals
                x1, y1, z1 = max_vals

                corners = np.array([
                    [x0, y0, z0], [x1, y0, z0], [x1, y1, z0], [x0, y1, z0],
                    [x0, y0, z1], [x1, y0, z1], [x1, y1, z1], [x0, y1, z1]
                ])

                for idx, (i, j) in enumerate(edges):
                    box_lines[idx].setData(pos=np.array([corners[i], corners[j]]))
            else:
                for line in box_lines:
                    line.setData(pos=np.zeros((0, 3)))
    except Exception as e:
        print("Parse error:", e)

timer = QtCore.QTimer()
timer.timeout.connect(update)
timer.start(10)
QtWidgets.QApplication.instance().exec_()
