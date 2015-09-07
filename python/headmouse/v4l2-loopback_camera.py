#!/usr/bin/env python

# Intended to be run with v4l2 loopback camera
# sudo modprobe v4l2loopback
# ffmpeg -f video4linux2 -input_format mjpeg -s 640x480 -i /dev/video1 -vcodec rawvideo -pix_fmt gray -threads 0 -f v4l2 /dev/video2

import cv2
import time

cap = cv2.VideoCapture(2)

def simple_fps(calc_interval):
    last_time = float(time.time())
    fps = None
    frames = 0

    while True:
        yield fps
        frames += 1
        current_time = float(time.time())
        interval = current_time - last_time

        if (interval > calc_interval):

            #calculate fps
            fps = frames / interval

            #reset start values
            last_time = current_time
            frames = 0

        else:
            fps = None


fps = simple_fps(1)

def print_unless_none(value):
    if value is not None:
        print value

while(True):
    ret, frame = cap.read()
    print_unless_none(fps.next())

    # Our operations on the frame come here
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

    # Display the resulting frame
    cv2.imshow('frame',frame)
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

# When everything done, release the capture
cap.release()
cv2.destroyAllWindows()


#     def __init__(self, **kwargs):
#         self.window_id = str(uuid.uuid4())
#         print '__init__()'
#
#         cap = cv2.VideoCapture(kwargs['device_id'])
#
#         cap.set(3, kwargs['width'])
#         cap.set(4, kwargs['height'])
#         #cap.set(cv2.cv.CV_CAP_PROP_FPS, 30.0)
#
#         #cap.set(8, kwargs['format_'])
#         #cap.set(cv2.cv.CV_CAP_PROP_FOURCC ,cv2.cv.CV_FOURCC('M', 'J', 'P', 'G'))
#         #cap.set(cv2.cv.CV_CAP_PROP_FOURCC ,cv2.cv.CV_FOURCC('M', 'P', 'E', 'G'))
#         #cap.set(5, 60)
#
#
#         self.cap = cap
#
#     def __enter__(self):
#         print '__enter__()'
#         return self
#
#     def show_window(self):
#         ret, frame = cam.cap.read()
#         cv2.imshow(self.window_id, frame)
#
#     def get_image(self):
#         return_code, image = self.cap.read()
#         self.show_window()
#         #print self.cap.get(cv2.cv.CV_CAP_PROP_FPS)
#         return image
#
#     def __exit__(self, exc_type, exc_val, exc_tb):
#         print 'Bye.'
#         self.cap.release()
#         cv2.destroyWindow(self.window_id)
#
#
#
# if __name__ == "__main__":
#     camera_config = {
#         'device_id':1,
#         'width':320,
#         'height':200,
#         'fps':60,
#         'format_':1
#     }
#
#
#     with Camera(**camera_config) as cam:
#         #print dir(cam)
#         #ret, frame = cam.cap.read()
#         #cv2.imshow('frame', frame)
#
#         cam.show_window()
#
#         try:
#             while True:
#                 cam.get_image()
#                 cam.show_window()
#
#                 fps_stat = fps.next()
#                 if fps_stat is not None:
#                     print fps_stat
#
#         except KeyboardInterrupt:
#           # do nothing here
#           pass
#
#
