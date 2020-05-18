import cv2
import numpy as np
import time

## simple sprocket detection algorithm
## returns the detected sprocket position
## relative to vertical scan center and left horizontal edge
def detectSprocketPos(img, roi = [0.01,0.09,0.2,0.8],
                           thresholds = [0.5,0.2],
                           filterSize = 25,
                           maxSize = 0.3,
                           horizontal = False):

    ## inital preparations
    
    # get the size of the image     
    dy,dx,dz = img.shape

    # convert roi coords to real image coords
    x0 = int(roi[0]*dx)
    x1 = int(roi[1]*dx)
    
    y0 = int(roi[2]*dy)
    y1 = int(roi[3]*dy)        

    # cutting out the strip to work with
    # we're using the full scan heigth to simplify computations
    sprocketStrip = img[:,x0:x1,:]

    # now calculating the vertical sobel edges
    sprocketEdges = np.absolute(cv2.Sobel(sprocketStrip,cv2.CV_64F,0,1,ksize=3))

    # by averaging horizontally, only promient horizontal edges
    # show up in the histogram
    histogram     = np.mean(sprocketEdges,axis=(1,2))

    # smoothing the histogram to make signal more stable.
    # sigma==0 -> it is autocalculated
    smoothedHisto = cv2.GaussianBlur(histogram,(1,filterSize),0)

    ## now analyzing the smoothed histogram
    
    # everything is relative to the detected maximum of the histogram
    # we only work in the region where the sprocket is expected
    maxPeakValue   = smoothedHisto[y0:y1].max()

    # the outer threshold is used to search for high peaks from the outside
    # it should be as high as possible in order to suppress that the algorithm
    # locks onto bright imprints of the film stock
    outerThreshold = thresholds[0]*maxPeakValue

    # the inner threshold is used to really search for the boundaries of
    # the sprocket. Implicitly it is assumed here that the area within
    # the sprocket is very evenly lit. If a lot of dust is present in
    # the material, this threshold should be raised higher
    innerThreshold = thresholds[1]*maxPeakValue

    # searching for the sprocket from the outside, first from below
    # we start not right at the border of the histogram in order to
    # avoid locking at bad cuts which look like tiny sprockets
    # to the algorithm    
    outerLow       = y0
    for y in range(y0,y1):
        if smoothedHisto[y]>outerThreshold:
            outerLow = y                 
            break
        
    # now searching from above
    outerHigh      = y1
    for y in range(y1,outerLow,-1):
        if smoothedHisto[y]>outerThreshold:
            outerHigh = y
            break

    # simple check for valid sprocket size. We require it
    # to be less than a third of the total scan height.
    # Otherwise, we give up and start the inner search
    # just from the center of the frame. This could be
    # improved - usually, the sprocket size stays pretty constant
    if (outerHigh-outerLow)<0.3*dy:
        searchCenter = (outerHigh+outerLow)//2
    else:
        searchCenter = dy//2

    # searching sprocket borders from the inside of the sprocket.
    # For this, the above found potential center of the sprocket
    # is used as a starting point to search for the sprocket edges 
    innerLow = searchCenter
    for y in range(searchCenter,outerLow,-1):
        if smoothedHisto[y]>innerThreshold:
            innerLow = y
            break
            
    innerHigh = searchCenter
    for y in range(searchCenter,outerHigh):
        if smoothedHisto[y]>innerThreshold:
            innerHigh = y
            break

    # a simple sanity check again. We make sure that the
    # sprocket is larger than maxSize and smaller than
    # the outer boundaries detected. If so, not correction
    # is applied to the image
    sprocketSize    = innerHigh-innerLow
    maxSprocketSize = int(maxSize*dy)
    if sprocketSize>maxSize and sprocketSize<(outerHigh-outerLow) :
        sprocketCenter = (innerHigh+innerLow)//2
    else:
        sprocketCenter = dy//2
        sprocketSize   = 0
        
    # now try to find the sprocket edge on the right side
    # if requested. Only if a sprocket is detected at that point
    # Not optimized, quick hack...
    xShift = 0
    if horizontal and sprocketSize>0:
        # calculate the region-of-interest
        
        # we start from the left edge of our previous roi
        # and look two times the
        rx0 = x0
        rx1 = x0 + 2*(x1-x0)

        # we use only a part of the whole sprocket height
        ry = int(0.8*sprocketSize)
        ry0 = sprocketCenter-ry//2
        ry1 = sprocketCenter+ry//2

        # cutting out the roi
        horizontalStrip = img[ry0:ry1,rx0:rx1,:]

        # edge detection
        horizontalEdges = np.absolute(cv2.Sobel(horizontalStrip,cv2.CV_64F,1,0,ksize=3))

        # evidence accumulation
        histoHori       = np.mean(horizontalEdges,axis=(0,2))
        smoothedHori    = cv2.GaussianBlur(histoHori,(1,5),0)

        # normalizing things
        maxPeakValueH   = smoothedHori.max()
        thresholdHori   = thresholds[1]*maxPeakValueH
        
        # now searching for the border
        xShift = 0
        for x in range((x1-x0)//2,len(smoothedHori)):
            if smoothedHori[x]>thresholdHori:
                xShift = x                 
                break
            
        # readjust calculated shift
        xShift = x1 - xShift
        
    return (xShift,dy//2-sprocketCenter)


## simple image transformation
def shiftImg(img,xShift,yShift):
    
    # create transformation matrix
    M = np.float32([[1,0,xShift],[0,1,yShift]])

    # ... and warp the image accordingly
    return cv2.warpAffine(img,M,(img.shape[1],img.shape[0]))

## test routine if called as script
if __name__ == '__main__':

    # get the input image
    inputImg       = cv2.imread('input.jpg')

    # time the processing
    tic            = time.time()
    
    # run sprocket detection routine
    shiftX, shiftY = detectSprocketPos(inputImg, horizontal=True)
    
    # shift the image into its place
    outputImage    = shiftImg(inputImg,shiftX,shiftY)
    toc            = time.time()

    # now output some test information
    dy,dx,dz = outputImage.shape
    print('Sprocket-Detection in %3.1f msec, img-Size %d x %d'%((toc-tic)*1000,dx,dy))
    print('Applied shifts: (%d,%d)'%(shiftX,shiftY))

    # finally, write out the result
    cv2.imwrite('output.jpg',outputImage)
