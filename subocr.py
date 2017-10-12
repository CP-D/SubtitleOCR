# -*- coding: utf-8 -*-
"""
python subocr.py filepath y1 y2 lang [start point] [end point]
"""

from PIL import Image
import cv2
import pytesseract
import codecs
import sys, os

def frame2hms(frame, fps):
    seconds = 1. / fps * (frame - 0.5)
    hour = int(seconds) / 3600
    minute = (int(seconds) - hour * 3600) / 60
    second = seconds - hour * 3600 - minute * 60
    return "%02d"%(hour) + ":" + "%02d"%(minute) + ":" + "%05.2f"%(second)

def hms2frame(hms, fps):
    h, m, s = hms.split(":")
    seconds = int(h) * 3600 + int(m) * 60 + int(s)
    return int(seconds * fps)

def ocr(cap, frame, y1, y2, lang):
    cap.set(cv2.cv.CV_CAP_PROP_POS_FRAMES, frame)
    ret, frame = cap.read()
    if frame is None:
        return None
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    subimg = gray[y1:y2, :]
    retval, image2 = cv2.threshold(subimg, 250, 255, cv2.THRESH_BINARY)
    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (3, 3))
    image3 = cv2.dilate(image2, kernel)
    pilimg = Image.fromarray(image3)
    chars = pytesseract.image_to_string(pilimg, lang)
    return chars

def is_similar(str1, str2):
    if str1 is None or str2 is None:
        return False
    if len(str1) < 3 or len(str2) < 3:
        return str1 == str2
    return str1[:3] == str2[:3] or str1[-3:] == str2[-3:]

if __name__ == "__main__":
    arg_len = len(sys.argv)

    # open the video file and the sub file
    if arg_len < 5:
        print "Absolute file path, recognition range y1, y2 and language option is required."
        exit(1)
    else:
        video_path = sys.argv[1]
        cap = cv2.VideoCapture(video_path)
        f = codecs.open(os.path.splitext(video_path)[0] + ".ass", 'a', 'utf-8')
        y1 = int(sys.argv[2])
        y2 = int(sys.argv[3])
        lang = sys.argv[4]
        if not cap.isOpened():
            print "Video file is not opened correctly."
            exit(1)
        fps = cap.get(cv2.cv.CV_CAP_PROP_FPS)

    # set default value
    start_frame = 0
    right_frame = 1
    end_frame = cap.get(cv2.cv.CV_CAP_PROP_FRAME_COUNT)

    # get the start point and the end point
    if arg_len > 5:
        start_hms = sys.argv[5]
        start_frame = hms2frame(start_hms, fps)
        right_frame = start_frame + 1
    if arg_len > 6:
        end_hms = sys.argv[6]
        end_frame = hms2frame(end_hms, fps)

    current_chars = ocr(cap, start_frame, y1, y2, lang)
    chars = current_chars

    # recognize subtitles, get timecodes and write to the file with a loop
    while True:
        while is_similar(chars, current_chars):
            left_frame = right_frame
            right_frame += 12
            if right_frame > end_frame:
                right_frame = end_frame
                chars = None
                break
            chars = ocr(cap, right_frame, y1, y2, lang)
        nextchars = chars

        while right_frame != left_frame + 1:
            mid_frame = (right_frame + left_frame) / 2
            chars = ocr(cap, mid_frame, y1, y2, lang)
            if is_similar(chars, current_chars):
                left_frame = mid_frame
            else:
                right_frame = mid_frame

        if current_chars != "":
            f.write("Dialogue: 0,")
            f.write(frame2hms(start_frame, fps) + "," + frame2hms(left_frame, fps) + ",Default,,0,0,0,,")
            f.write(current_chars.replace("\n","") + "\n")
            print frame2hms(start_frame, fps) + " --> " + frame2hms(left_frame, fps) + " " + current_chars.replace("\n","")

        if nextchars is None:
            break;

        current_chars = nextchars
        chars = nextchars
        start_frame = right_frame
        right_frame += 1

    f.close()
