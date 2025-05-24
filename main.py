import serial
import re
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D
import time

ser = serial.Serial('COM5', 9600)
time.sleep(2)

plt.ion()
fig = plt.figure()
ax = fig.add_subplot(111, projection='3d')

x_vals, y_vals, z_vals = [], [], []

try:
    while True:
        line = ser.readline().decode('utf-8', errors='ignore').strip()

        match = re.match(r"Point: X=(-?\d+\.\d+) Y=(-?\d+\.\d+) Z=(-?\d+\.\d+)", line)
        if match:
            x, y, z = map(float, match.groups())
            x_vals.append(x)
            y_vals.append(y)
            z_vals.append(z)

            if len(x_vals) > 100:
                x_vals.pop(0)
                y_vals.pop(0)
                z_vals.pop(0)

            ax.clear()
            ax.scatter(x_vals, y_vals, z_vals, c='blue', marker='o')
            ax.set_xlim(-20, 20)
            ax.set_ylim(-20, 20)
            ax.set_zlim(0, 40)
            ax.set_xlabel('X')
            ax.set_ylabel('Y')
            ax.set_zlabel('Z')
            plt.draw()
            plt.pause(0.01)

except KeyboardInterrupt:
    print("Stopped by user")

finally:
    ser.close()
