import numpy as np
import cv2
import time


cap = cv2.VideoCapture(1)
#cap.set(3, 320)
#cap.set(4, 200)
#cap.set(5, 30)

startTime = time.time()
timeC = 0
loops = 0

while(True):
    loops += 1
    timeC += time.time() - startTime
    if loops == 100:
        loops = 0
        print "fps is", 100. / timeC
        timeC = 0
#    print "time took:", time.time() - startTime
    startTime = time.time()
    # Capture frame-by-frame
    ret, img = cap.read()

    # Display the resulting frame
#    cv2.imshow('frame',img)
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

# When everything done, release the capture
cap.release()
cv2.destroyAllWindows()
