import numpy as np
import cv2
import Person
import time
import urllib2,urllib
import datetime
import math
import urlparse



class Counter:
    def __init__(self):
        # Each rocket has an (x,y) position.
        self.x = 0
        self.y = 0
    def downloadFile(self,urlString):

        if not urlString:
            url = "https://s3-ap-southeast-2.amazonaws.com/leonardoau/v1.mp4"
        else:
            url = urlString

        file_name = url.split('/')[-1]
        print "testd", file_name , "--",url
        urlSplitList = urlparse.urlparse(url)
        pathArray = urlSplitList.path.split("/")
        pathArray[-1] =  urllib.quote_plus(pathArray[-1])
        print pathArray
        print urlSplitList
        url = urlSplitList.scheme + "://" + urlSplitList.hostname + "/" + '/'.join(pathArray)
        u = urllib2.urlopen(url)
        f = open(file_name, 'wb')
        meta = u.info()
        file_size = int(meta.getheaders("Content-Length")[0])
        print "Downloading: %s Bytes: %s" % (file_name, file_size)

        file_size_dl = 0
        block_sz = 8192
        while True:
            buffer = u.read(block_sz)
            if not buffer:
                break

            file_size_dl += len(buffer)
            f.write(buffer)
            status = r"%10d  [%3.2f%%]" % (file_size_dl, file_size_dl * 100. / file_size)
            status = status + chr(8) * (len(status) + 1)
            print status,

        f.close()

    def calculateCounter(self,url):
        countList = []
        existCountList = []
        self.downloadFile(url)
    #Contadores de entrada y salida
        cnt_up   = 0
        cnt_down = 0
        file_name = url.split('/')[-1]
        print "testc",file_name
        #cap = cv2.VideoCapture(0)
        cap = cv2.VideoCapture(file_name)

        #Propiedades del video
        cap.set(3,1280)
        cap.set(4,1024)
        cap.set(15, 0.1)

        #Imprime las propiedades de captura a consola
        for i in range(19):
            print i, cap.get(i)

        w = cap.get(3)
        h = cap.get(4)
        frameArea = h*w
        areaTH = frameArea/250
        print 'Area Threshold', areaTH

        #Lineas de entrada/salida
        line_up = int(2*(h/5))
        line_down   = int(3*(h/5))

        up_limit =   int(1*(h/5))
        down_limit = int(4*(h/5))

        print "Red line y:",str(line_down)
        print "Blue line y:", str(line_up)
        line_down_color = (255,0,0)
        line_up_color = (0,0,255)
        pt1 =  [0, line_down];
        pt2 =  [w, line_down];
        pts_L1 = np.array([pt1,pt2], np.int32)
        pts_L1 = pts_L1.reshape((-1,1,2))
        pt3 =  [0, line_up];
        pt4 =  [w, line_up];
        pts_L2 = np.array([pt3,pt4], np.int32)
        pts_L2 = pts_L2.reshape((-1,1,2))

        pt5 =  [0, up_limit];
        pt6 =  [w, up_limit];
        pts_L3 = np.array([pt5,pt6], np.int32)
        pts_L3 = pts_L3.reshape((-1,1,2))
        pt7 =  [0, down_limit];
        pt8 =  [w, down_limit];
        pts_L4 = np.array([pt7,pt8], np.int32)
        pts_L4 = pts_L4.reshape((-1,1,2))

        #Substractor de fondo
        fgbg = cv2.BackgroundSubtractorMOG()
        #createBackgroundSubtractorMOG2(detectShadows = False)

        #Elementos estructurantes para filtros morfoogicos
        kernelOp = np.ones((3,3),np.uint8)
        kernelOp2 = np.ones((5,5),np.uint8)
        kernelCl = np.ones((11,11),np.uint8)

        #Variables
        font = cv2.FONT_HERSHEY_SIMPLEX
        persons = []
        max_p_age = 5
        pid = 1

        starttime = datetime.datetime.now()
        frameCount = 0
        #cv.CV_CAP_PROP_FRAME_COUNT
        length = int(cap.get(cv2.cv.CV_CAP_PROP_FRAME_COUNT))
        fps = cap.get(cv2.cv.CV_CAP_PROP_FPS)

        while(cap.isOpened()):
        ##for image in camera.capture_continuous(rawCapture, format="bgr", use_video_port=True):
            #Lee una imagen de la fuente de video
            ret, frame = cap.read()
        ##    frame = image.array
            print "hiii"
            frameCount += 1
           #  print (frame,fps)
            for i in persons:
                i.age_one() #age every person one frame
            #########################
            #   PRE-PROCESAMIENTO   #
            #########################

            #Aplica substraccion de fondo
            fgmask = fgbg.apply(frame)
            fgmask2 = fgbg.apply(frame)

            #Binariazcion para eliminar sombras (color gris)
            try:
                ret,imBin= cv2.threshold(fgmask,200,255,cv2.THRESH_BINARY)
                ret,imBin2 = cv2.threshold(fgmask2,200,255,cv2.THRESH_BINARY)
                #Opening (erode->dilate) para quitar ruido.
                mask = cv2.morphologyEx(imBin, cv2.MORPH_OPEN, kernelOp)
                mask2 = cv2.morphologyEx(imBin2, cv2.MORPH_OPEN, kernelOp)
                #Closing (dilate -> erode) para juntar regiones blancas.
                mask =  cv2.morphologyEx(mask , cv2.MORPH_CLOSE, kernelCl)
                mask2 = cv2.morphologyEx(mask2, cv2.MORPH_CLOSE, kernelCl)
            except:
                print('EOF')
                print 'UP:',cnt_up
                print 'DOWN:',cnt_down
                countList.append({"out":cnt_up, "inside": cnt_down})
                return countList
                break
            #################
            #   CONTORNOS   #
            #################

            # RETR_EXTERNAL returns only extreme outer flags. All child contours are left behind.
            contours0, hierarchy = cv2.findContours(mask2,cv2.RETR_EXTERNAL,cv2.CHAIN_APPROX_SIMPLE)
            for cnt in contours0:
                area = cv2.contourArea(cnt)
                if area > areaTH:
                    #################
                    #   TRACKING    #
                    #################

                    #Falta agregar condiciones para multipersonas, salidas y entradas de pantalla.

                    M = cv2.moments(cnt)
                    cx = int(M['m10']/M['m00'])
                    cy = int(M['m01']/M['m00'])
                    x,y,w,h = cv2.boundingRect(cnt)

                    new = True
                    if cy in range(up_limit,down_limit):
                        for i in persons:
                            if abs(cx-i.getX()) <= w and abs(cy-i.getY()) <= h:
                                # el objeto esta cerca de uno que ya se detecto antes
                                new = False
                                i.updateCoords(cx,cy)   #actualiza coordenadas en el objeto and resets age
                                if i.going_UP(line_down,line_up) == True:
                                    if not (i.getId() in  existCountList):
                                        existCountList.append(i.getId())
                                        cnt_up += 1;
                                        enduptime = datetime.datetime.now()
                                        duration = frameCount/fps #(enduptime - starttime )
                                        #print duration
                                        datetime.timedelta(0, 8, 562000)
                                        timeFrame = divmod(duration, 60)
                                        mmssTime =  str(int(timeFrame[0]))+ " Minute " + str(int(math.ceil(timeFrame[1]))) + " Seconds"
                                        print mmssTime, new
                                        countList.append({"action": "going outside side", "time": mmssTime })
                                        print "ID:",i.getId(),'crossed going up at',time.strftime("%c")


                                elif i.going_DOWN(line_down,line_up) == True:
                                    if not i.getId() in existCountList:
                                        existCountList.append(i.getId())
                                        cnt_down += 1;
                                        enddowntime = datetime.datetime.now()
                                        duration = frameCount/fps #(enddowntime - starttime  )
                                        datetime.timedelta(0, 8, 562000)
                                        #print duration
                                        timeFrame = divmod(duration, 60)
                                        mmssTime = str(int(timeFrame[0])) + " Minute " + str(
                                            int(math.ceil(timeFrame[1]))) + " Seconds"
                                        print mmssTime, new
                                        countList.append({"action": "coming in side", "time": mmssTime})
                                        print "ID:",i.getId(),'crossed going down at',time.strftime("%c")
                                break
                            if i.getState() == '1':
                                if i.getDir() == 'down' and i.getY() > down_limit:
                                    i.setDone()
                                elif i.getDir() == 'up' and i.getY() < up_limit:
                                    i.setDone()

                            if i.timedOut():
                                #sacar i de la lista persons
                                index = persons.index(i)
                                persons.pop(index)
                                del i     #liberar la memoria de i
                        if new == True:
                            p = Person.MyPerson(pid,cx,cy, max_p_age)
                            persons.append(p)
                            pid += 1
                    #################
                    #   DIBUJOS     #
                    #################
                    cv2.circle(frame,(cx,cy), 5, (0,0,255), -1)
                    img = cv2.rectangle(frame,(x,y),(x+w,y+h),(0,255,0),2)
                    #cv2.drawContours(frame, cnt, -1, (0,255,0), 3)


        cap.release()
        cv2.destroyAllWindows()
        return countList

