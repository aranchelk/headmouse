import numpy as np
import cv2
import time

cap = cv2.VideoCapture(1)
time.sleep(1)
ret, img = cap.read()

gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

cv2.imwrite('./test.jpg', gray)
# When everything done, release the capture
cap.release()
cv2.destroyAllWindows()




