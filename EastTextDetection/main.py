# app.py
from flask import Flask, render_template, flash, request, redirect
from werkzeug.utils import secure_filename
import os
from imutils.object_detection import non_max_suppression
import numpy as np
import time
import cv2
import glob
import ntpath
import glob
import glob
import os
import pydicom as dicom
import cv2
import numpy as np
net = cv2.dnn.readNet("static/saved_model/East_model.pb")

# import magic
import urllib.request

app = Flask(__name__)

UPLOAD_FOLDER = 'static/images'
filenames = []
app.secret_key = "Cairocoders-Ednalan"
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024

ALLOWED_EXTENSIONS = set(['png', 'jpg', 'jpeg', 'dcm'])


def text_detector(image, filename):
    print("text detector filename ", filename)
    validating_value = 0
    orig = image
    (H, W) = image.shape[:2]
    (newW, newH) = (640, 320)
    rW = W / float(newW)
    rH = H / float(newH)
    image = cv2.resize(image, (newW, newH))
    (H, W) = image.shape[:2]
    layerNames = [
        "feature_fusion/Conv_7/Sigmoid",
        "feature_fusion/concat_3"]
    blob = cv2.dnn.blobFromImage(image, 1.0, (W, H), (123.68, 116.78, 103.94), swapRB=True, crop=False)
    net.setInput(blob)
    (scores, geometry) = net.forward(layerNames)
    (numRows, numCols) = scores.shape[2:4]
    rects = []
    confidences = []
    for y in range(0, numRows):
        scoresData = scores[0, 0, y]
        xData0 = geometry[0, 0, y]
        xData1 = geometry[0, 1, y]
        xData2 = geometry[0, 2, y]
        xData3 = geometry[0, 3, y]
        anglesData = geometry[0, 4, y]

        for x in range(0, numCols):
            if scoresData[x] < 0.5:
                continue
            (offsetX, offsetY) = (x * 4.0, y * 4.0)
            angle = anglesData[x]
            cos = np.cos(angle)
            sin = np.sin(angle)
            h = xData0[x] + xData2[x]
            w = xData1[x] + xData3[x]
            endX = int(offsetX + (cos * xData1[x]) + (sin * xData2[x]))
            endY = int(offsetY - (sin * xData1[x]) + (cos * xData2[x]))
            startX = int(endX - w)
            startY = int(endY - h)
            rects.append((startX, startY, endX, endY))
            confidences.append(scoresData[x])
        boxes = non_max_suppression(np.array(rects), probs=confidences)
        for (startX, startY, endX, endY) in boxes:
            startX = int(startX * rW)
            startY = int(startY * rH)
            endX = int(endX * rW)
            endY = int(endY * rH)
            cv2.rectangle(orig, (startX, startY), (endX, endY), (0, 255, 0), 3)
            validating_value = endY
    print(validating_value)
    if validating_value == 0:
        print("Text Not Present")
        print("Deleted file are : ", filenames)
        print("++++++++++++++++++++++++++++++++++++++++++")
    else:
        print("Text is there")
        filenames.append(filename)
        print("Deleting ......")
        os.remove(os.path.join("static/images/", filename))
        print("++++++++++++++++++++++++++++++++++++++++++")
        print("Deleted file are : ", filenames)

    return orig, filenames

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


@app.route('/')
def upload_form():
    return render_template('upload.html')


@app.route('/', methods=['POST'])
def upload_file():
    filenames.clear()
    if request.method == 'POST':
        # check if the post request has the files part
        if 'files[]' not in request.files:
            flash('No file part')
            return redirect(request.url)
        files = request.files.getlist('files[]')
        for file in files:
            if file and allowed_file(file.filename):
                filename = secure_filename(file.filename)
                file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
                ##############File is in Folder by now########################
                for i in os.listdir("static/images"):
                    if i.endswith("dcm"):
                        print("dcm files", i)
                        image_path = i
                        print(os.getcwd())

                        ds = dicom.dcmread(os.path.join("static/images/", i))
                        pixel_array_numpy = ds.pixel_array
                        image_format = '.jpg'  # or '.png'
                        image_path = image_path.replace('.dcm', image_format)
                        cv2.imwrite(image_path, pixel_array_numpy)
                        print("image_path", image_path)
                        image = cv2.imread(image_path)
                        # print(image)
                        array = [image]
                        for i in range(0, 1):
                            for img in array:
                                imageO = cv2.resize(img, (640, 320), interpolation=cv2.INTER_AREA)
                                imageX = imageO
                                orig = text_detector(imageO, image_path)

                    else:
                        print(os.getcwd())
                        print(i)
                        image = cv2.imread(os.path.join("static/images/", i))
                        #print(image)
                        array = [image]
                        for j in range(0, 1):
                            for img in array:
                                imageO = cv2.resize(img, (640, 320), interpolation=cv2.INTER_AREA)
                                imageX = imageO
                                print("sending this filename to ", i)
                                orig = text_detector(imageO, i)

                x = ',   '.join(filenames)
                print("Deleted files are ", x)
                print(os.getcwd())
                for file in os.listdir('/Users/nimesh/Downloads/Work/1_Mine/NewTextDetector'):
                    if file.endswith('.jpg'):
                        os.remove(file)
                    else:
                        pass

        if filenames:
            flash(' ERROR : Below file contain Text and could not be Uploaded ', "ERROR")
            flash(x)
        else:
            flash("File(s) Successfully uploaded")

        #flash(filenames)
        return redirect('/')


if __name__ == '__main__':
    app.run(debug=True)