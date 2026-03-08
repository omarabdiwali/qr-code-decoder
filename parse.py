import xmlpy
from PIL import Image
from traceback import print_exc
from collections import defaultdict
from math import ceil, dist, atan2, degrees

class ImageParser:
    def __init__(self, data, width, height, path):
        self.data = data
        self.width = width
        self.height = height
        self.writer = xmlpy.XMLBuilder(path)
        self.ecl = 1
        self.blockSize, self.startX, self.endX, self.startY, self.endY = [None for _ in range(5)]
        self.timingCoords, self.finderCoords, self.mask = None, {}, None
        self.color = "none"
        self.goingUp = True
        self.direction = "left"
        self.blocks = []
        self.version = None
        self.qr = []
        self.xDiff, self.yDiff = 0, 0
        self.invalid = set()
        self.eclMap = { 0: 'M', 1: 'L', 2: 'H', 3: 'Q' }
        self.qrDataBlocks = {
            "1-L": [(1, 19)], "1-M": [(1, 16)], "1-Q": [(1, 13)], "1-H": [(1, 9)],
            "2-L": [(1, 34)], "2-M": [(1, 28)], "2-Q": [(1, 22)], "2-H": [(1, 16)],
            "3-L": [(1, 55)], "3-M": [(1, 44)], "3-Q": [(2, 17)], "3-H": [(2, 13)],
            "4-L": [(1, 80)], "4-M": [(2, 32)], "4-Q": [(2, 24)], "4-H": [(4, 9)],
            "5-L": [(1, 108)], "5-M": [(2, 43)], "5-Q": [(2, 15), (2, 16)], "5-H": [(2, 11), (2, 12)],
            "6-L": [(2, 68)], "6-M": [(4, 27)], "6-Q": [(4, 19)], "6-H": [(4, 15)],
            "7-L": [(2, 78)], "7-M": [(4, 31)], "7-Q": [(2, 14), (4, 15)], "7-H": [(4, 13), (1, 14)],
            "8-L": [(2, 97)], "8-M": [(2, 38), (2, 39)], "8-Q": [(4, 18), (2, 19)], "8-H": [(4, 14), (2, 15)],
            "9-L": [(2, 116)], "9-M": [(3, 36), (2, 37)], "9-Q": [(4, 16), (4, 17)], "9-H": [(4, 12), (4, 13)],
            "10-L": [(2, 68), (2, 69)], "10-M": [(4, 43), (1, 44)], "10-Q": [(6, 19), (2, 20)], "10-H": [(6, 15), (2, 16)],
            "11-L": [(4, 81)], "11-M": [(1, 50), (4, 51)], "11-Q": [(4, 22), (4, 23)], "11-H": [(3, 12), (8, 13)],
            "12-L": [(2, 92), (2, 93)], "12-M": [(6, 36), (2, 37)], "12-Q": [(4, 20), (6, 21)], "12-H": [(7, 14), (4, 15)],
            "13-L": [(4, 107)], "13-M": [(8, 37), (1, 38)], "13-Q": [(8, 20), (4, 21)], "13-H": [(12, 11), (4, 12)],
            "14-L": [(3, 115), (1, 116)], "14-M": [(4, 40), (5, 41)], "14-Q": [(11, 16), (5, 17)], "14-H": [(11, 12), (5, 13)],
            "15-L": [(5, 87), (1, 88)], "15-M": [(5, 41), (5, 42)], "15-Q": [(5, 24), (7, 25)], "15-H": [(11, 12), (7, 13)],
            "16-L": [(5, 98), (1, 99)], "16-M": [(7, 45), (3, 46)], "16-Q": [(15, 19), (2, 20)], "16-H": [(3, 15), (13, 16)],
            "17-L": [(1, 107), (5, 108)], "17-M": [(10, 46), (1, 47)], "17-Q": [(1, 22), (15, 23)], "17-H": [(2, 14), (17, 15)],
            "18-L": [(5, 120), (1, 121)], "18-M": [(9, 43), (4, 44)], "18-Q": [(17, 22), (1, 23)], "18-H": [(2, 14), (19, 15)],
            "19-L": [(3, 113), (4, 114)], "19-M": [(3, 44), (11, 45)], "19-Q": [(17, 21), (4, 22)], "19-H": [(9, 13), (16, 14)],
            "20-L": [(3, 107), (5, 108)], "20-M": [(3, 41), (13, 42)], "20-Q": [(15, 24), (5, 25)], "20-H": [(15, 15), (10, 16)],
            "21-L": [(4, 116), (4, 117)], "21-M": [(17, 42)], "21-Q": [(17, 22), (6, 23)], "21-H": [(19, 16), (6, 17)],
            "22-L": [(2, 111), (7, 112)], "22-M": [(17, 46)], "22-Q": [(7, 24), (16, 25)], "22-H": [(34, 13)],
            "23-L": [(4, 121), (5, 122)], "23-M": [(4, 47), (14, 48)], "23-Q": [(11, 24), (14, 25)], "23-H": [(16, 15), (14, 16)],
            "24-L": [(6, 117), (4, 118)], "24-M": [(6, 45), (14, 46)], "24-Q": [(11, 24), (16, 25)], "24-H": [(30, 16), (2, 17)],
            "25-L": [(8, 106), (4, 107)], "25-M": [(8, 47), (13, 48)], "25-Q": [(7, 24), (22, 25)], "25-H": [(22, 15), (13, 16)],
            "26-L": [(10, 114), (2, 115)], "26-M": [(19, 46), (4, 47)], "26-Q": [(28, 22), (6, 23)], "26-H": [(33, 16), (4, 17)],
            "27-L": [(8, 122), (4, 123)], "27-M": [(22, 45), (3, 46)], "27-Q": [(8, 23), (26, 24)], "27-H": [(12, 15), (28, 16)],
            "28-L": [(3, 117), (10, 118)], "28-M": [(3, 45), (23, 46)], "28-Q": [(4, 24), (31, 25)], "28-H": [(11, 15), (31, 16)],
            "29-L": [(7, 116), (7, 117)], "29-M": [(21, 45), (7, 46)], "29-Q": [(1, 23), (37, 24)], "29-H": [(19, 15), (26, 16)],
            "30-L": [(5, 115), (10, 116)], "30-M": [(19, 47), (10, 48)], "30-Q": [(15, 24), (25, 25)], "30-H": [(23, 15), (25, 16)],
            "31-L": [(13, 115), (3, 116)], "31-M": [(2, 46), (29, 47)], "31-Q": [(42, 24), (1, 25)], "31-H": [(23, 15), (28, 16)],
            "32-L": [(17, 115)], "32-M": [(10, 46), (23, 47)], "32-Q": [(10, 24), (35, 25)], "32-H": [(19, 15), (35, 16)],
            "33-L": [(17, 115), (1, 116)], "33-M": [(14, 46), (21, 47)], "33-Q": [(29, 24), (19, 25)], "33-H": [(11, 15), (46, 16)],
            "34-L": [(13, 115), (6, 116)], "34-M": [(14, 46), (23, 47)], "34-Q": [(44, 24), (7, 25)], "34-H": [(59, 16), (1, 17)],
            "35-L": [(12, 121), (7, 122)], "35-M": [(12, 47), (26, 48)], "35-Q": [(39, 24), (14, 25)], "35-H": [(22, 15), (41, 16)],
            "36-L": [(6, 121), (14, 122)], "36-M": [(6, 47), (34, 48)], "36-Q": [(46, 24), (10, 25)], "36-H": [(2, 15), (64, 16)],
            "37-L": [(17, 122), (4, 123)], "37-M": [(29, 46), (14, 47)], "37-Q": [(49, 24), (10, 25)], "37-H": [(24, 15), (46, 16)],
            "38-L": [(4, 122), (18, 123)], "38-M": [(13, 46), (32, 47)], "38-Q": [(48, 24), (14, 25)], "38-H": [(42, 15), (32, 16)],
            "39-L": [(20, 117), (4, 118)], "39-M": [(40, 47), (7, 48)], "39-Q": [(43, 24), (22, 25)], "39-H": [(10, 15), (67, 16)],
            "40-L": [(19, 118), (6, 119)], "40-M": [(18, 47), (31, 48)], "40-Q": [(34, 24), (34, 25)], "40-H": [(20, 15), (61, 16)]
        }
        self.alnumMap = [
            '0', '1', '2', '3', '4', '5', '6', '7', '8', '9', 
            'A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'J', 
            'K', 'L', 'M', 'N', 'O', 'P', 'Q', 'R', 'S', 'T', 
            'U', 'V', 'W', 'X', 'Y', 'Z', ' ', '$', '%', '*', 
            '+', '-', '.', '/', ':'
        ]
    
    def updateParserValues(self, image, xDiff, yDiff):
        self.data = image.load()
        self.width = image.width
        self.height = image.height
        self.xDiff = xDiff
        self.yDiff = yDiff

    def getColorValue(self, val):
        return int(val < 125)

    def diff(self, a, b, threshold):
        return abs(a - b) < threshold
    
    def isLightRoi(self, x, y):
        middleX, middleY = (x + self.blockSize // 2), (y + self.blockSize // 2)
        value = self.data[middleX, middleY]
        return self.getColorValue(value) == 0

    def runLengthEncodingX(self):
        encoded = []
        for y in range(self.height):
            rowData = defaultdict(dict)
            lastItem = self.getColorValue(self.data[0, y])
            count = 1
            for x in range(1, self.width):
                curVal = self.getColorValue(self.data[x, y])
                if lastItem != curVal:
                    if "data" not in rowData[y]:
                        rowData[y]["data"] = []
                    
                    rowData[y]["data"].append({ "start": x-count, "length": count, "color": lastItem })
                    count = 0
                
                count += 1
                lastItem = curVal

            if "data" not in rowData[y]:
                rowData[y]["data"] = []
            
            rowData[y]["data"].append({ "start": x-count+1, "length": count, "color": lastItem })
            encoded.append(rowData)
        
        return encoded

    def runLengthEncodingY(self):
        encoded = []
        for x in range(self.width):
            colData = defaultdict(dict)
            lastItem = self.getColorValue(self.data[x, 0])
            count = 1
            for y in range(1, self.height):
                curVal = self.getColorValue(self.data[x, y])
                if lastItem != curVal:
                    if 'data' not in colData[x]:
                        colData[x]['data'] = []

                    colData[x]["data"].append({ "start": y-count, "length": count, "color": lastItem })
                    count = 0
                
                count += 1
                lastItem = curVal

            if 'data' not in colData[x]:
                colData[x]['data'] = []
                        
            colData[x]["data"].append({ "start": y-count+1, "length": count, "color": lastItem })
            encoded.append(colData)
        
        return encoded  

    def findTimingPatterns(self, data, otherAxis, otherTimingPattern=None):
        timingPatterns = {}
        rowsParsed = {}
        
        for obj in data:
            for otherVal, value in obj.items():
                items = value["data"]
                startIndex = 0
                while startIndex < len(items) - 7:
                    totalCount = 0
                    totalSize = 0
                    curDiff = 0
                    startLength = 0
                    endLength = 0
                    
                    currentIndex = startIndex
                    valid = True
                    tempBlockSize = self.blockSize

                    while currentIndex < len(items):
                        item = items[currentIndex]
                        if currentIndex == startIndex:
                            if item['color'] != 1:
                                valid = False
                                break
                            
                            startLength = item['length']
                            tempBlockSize = startLength / 7
                        
                        elif currentIndex == len(items) - 1:
                            if item['color'] != 1 or totalCount < 6 or not self.diff(item['length'], startLength, tempBlockSize):
                                valid = False
                                break

                            endLength = item['length']
                            curDiff += abs(endLength - startLength)
                            break
                        
                        elif self.diff(item["length"], startLength, tempBlockSize):
                            if totalCount < 6 or item['color'] != 1:
                                valid = False
                                break

                            endLength = item['length']
                            curDiff += abs(endLength - startLength)
                            break
                        
                        else:
                            if item['length'] >= startLength:
                                valid = False
                                break
                            if not self.diff(item["length"], tempBlockSize, tempBlockSize):
                                valid = False
                                break
                            else:
                                totalSize += item["length"]
                                totalCount += 1
                                curDiff += abs(item['length'] - tempBlockSize)
                        
                        currentIndex += 1
                    
                    if valid and totalCount > 6:
                        xBlockSize = (totalSize + startLength + endLength) / (totalCount + 14)
                        dataSection = items[startIndex:currentIndex + 1]
                        struct = { otherAxis: otherVal, 'data': dataSection, 'blockSize': xBlockSize, 'startPos': dataSection[0]['start'] }
                        foundMatch = False
                        
                        for key in timingPatterns.keys():
                            keyOtherVal, keyStartPos, keyBlockSize = list(map(float, key.split("-")))
                            itemStartPos = struct["startPos"]
                            threshold = min(xBlockSize, keyBlockSize) * 0.1

                            if self.diff(keyStartPos, itemStartPos, 7) and self.diff(xBlockSize, keyBlockSize, threshold):
                                if self.diff(otherVal, keyOtherVal, ceil(min(xBlockSize, keyBlockSize))) and otherVal not in rowsParsed[key]:
                                    timingPatterns[key].append(struct)
                                    rowsParsed[key].add(otherVal)
                                    foundMatch = True
                                    break
                        
                        if not foundMatch:
                            key = f"{otherVal}-{struct['startPos']}-{xBlockSize}"
                            timingPatterns[key] = [struct]
                            rowsParsed[key] = set([otherVal])
                    
                    startIndex += 1
        
        validTiming = None
        largestGroup = 0
        smallestDiff = 10

        # print(timingPatterns.keys(), [len(v) for v in timingPatterns.values()])
        
        for value in timingPatterns.values():
            blockSize = value[0]['blockSize']

            if len(value) >= largestGroup:
                if otherTimingPattern:
                    targetBlockSize = otherTimingPattern['blockSize']
                    xRle = { value[0]['y']: value[0]['data'] } if otherAxis == 'y' else { otherTimingPattern['y']: otherTimingPattern['data'] }
                    yRle = { value[0]['x']: value[0]['data'] } if otherAxis == 'x' else { otherTimingPattern['x']: otherTimingPattern['data'] }
                
                    if self.diff(blockSize, targetBlockSize, smallestDiff) and self.checkIntersection(xRle, yRle):
                        largestGroup = len(value)
                        smallestDiff = abs(targetBlockSize - blockSize)
                        validTiming = value[0]
                
                elif len(value) > largestGroup:
                    largestGroup = len(value)
                    validTiming = value[0]
    
        if validTiming is not None:
            items = [validTiming['startPos'], validTiming[otherAxis]] if otherAxis == 'y' else [validTiming[otherAxis], validTiming['startPos']]
            timingPatternDir = "Timing Pattern X" if otherAxis == 'y' else "Timing Pattern Y"
            print(timingPatternDir)
            print("Returning: ({}, {}) - {}\n".format(items[0], items[1], validTiming['blockSize']))
        
        return validTiming

    def checkIntersection(self, xRle, yRle):
        sharedPositions = set()
        
        for y, xSegments in xRle.items():
            for x in range(xSegments[0]["start"], xSegments[-1]["start"] + xSegments[-1]["length"]):
                sharedPositions.add((x, y))

        for x, ySegments in yRle.items():
            for y in range(ySegments[0]["start"], ySegments[-1]["start"] + ySegments[-1]["length"]):
                if (x, y) in sharedPositions:
                    return True
        
        return False

    def findAlignmentPatterns(self):
        for i in range(0, len(self.blocks) - 5):
            for j in range(0, len(self.blocks[i]) - 5):
                if (i, j) in self.invalid:
                    continue
                
                patternCoords = []
                valid = True

                for a in range(5):
                    for b in range(5):
                        x1, y1 = self.blocks[i + a][j + b]
                        shouldBeBlack = (a == 0) or (a == 4) or (b == 0) or (b == 4) or (a == b and a == 5 // 2)
                        if not self.isLightRoi(x1, y1) != shouldBeBlack:
                            valid = False
                            break
                        patternCoords.append((i + a, j + b))
                    if not valid:
                        break
                
                if valid:
                    for coord in patternCoords:
                        self.addInvalid(coord[0], coord[1])
    
    def findFinderPatterns(self, data, otherAxis, path, image, changeImage=True):
        finderPatterns = {}
        rowsParsed = {}

        for obj in data:
            for otherVal, value in obj.items():
                items = value["data"]
                startIndex = 0
                while startIndex < len(items) - 4:
                    if items[startIndex]['color'] != 1:
                        startIndex += 1
                        continue

                    aLen, bLen, cLen, dLen, eLen = [i['length'] for i in items[startIndex:startIndex + 5]]
                    estBlockSize = cLen / 3
                    valid = [self.diff(i, estBlockSize, estBlockSize * 0.5) for i in [aLen, bLen, dLen, eLen]]
                    
                    if False in valid:
                        startIndex += 2
                        continue
                    
                    estBlockSize = (aLen + bLen + cLen + dLen + eLen) / 7
                    dataSection = items[startIndex:startIndex + 5]
                    struct = { otherAxis: otherVal, 'startPos': dataSection[0]['start'], 'blockSize': estBlockSize, 'data': dataSection }
                    foundMatch = False

                    for key in finderPatterns.keys():
                        keyStartPos, keyOtherVal, keyBlockSize = list(map(float, key.split("-")))
                        itemStartPos = struct["startPos"]
                        threshold = min(estBlockSize, keyBlockSize) * 0.1

                        if self.diff(keyStartPos, itemStartPos, 7) and self.diff(estBlockSize, keyBlockSize, threshold):
                            if self.diff(otherVal, keyOtherVal, ceil(min(estBlockSize, keyBlockSize) * 3)) and otherVal not in rowsParsed[key]:
                                    finderPatterns[key].append(struct)
                                    rowsParsed[key].add(otherVal)
                                    foundMatch = True
                                    break
                        
                    if not foundMatch:
                        key = f"{struct["startPos"]}-{otherVal}-{estBlockSize}"
                        finderPatterns[key] = [struct]
                        rowsParsed[key] = set([otherVal])

                    startIndex += 2

        keyAndSize = [(x, len(finderPatterns[x])) for x in finderPatterns.keys()]
        keyAndSize.sort(key=lambda x:(-x[1]))
        clrs = ["red", "green", "blue"]
        points = []
        idx = 0
        avgBlockSize = 0

        if changeImage:
            finderPatternsVisualization = xmlpy.XMLBuilder('finderVisual.svg')
            finderPatternsVisualization.addSVG(self.width, self.height)
            finderPatternsVisualization.addImage(0, 0, self.width, self.height, path)

        classify = {}
        currentLargest = { "key": "", "size": 0 }

        for key, _ in keyAndSize[:6]:
            keyStartPos, keyOtherVal, keyBlockSize = list(map(float, key.split("-")))
            foundMatch = False

            for blockSize in classify.keys():
                threshold = min(blockSize, keyBlockSize) * 0.25
                if self.diff(blockSize, keyBlockSize, threshold):
                    classify[blockSize].append((keyStartPos, keyOtherVal, keyBlockSize))
                    curSize = len(classify[blockSize])
                    
                    if currentLargest["key"] == blockSize:
                        currentLargest["size"] += 1
                    elif curSize > currentLargest["size"]:
                        currentLargest["key"] = blockSize
                        currentLargest["size"] = curSize
                    
                    foundMatch = True
                    break
            
            if not foundMatch:
                classify[keyBlockSize] = [(keyStartPos, keyOtherVal, keyBlockSize)]
                if currentLargest["key"] == "":
                    currentLargest["key"] = keyBlockSize
                    currentLargest["size"] += 1
            idx += 1
        
        for item in classify[currentLargest["key"]][:3]:
            points.append((item[0], item[1]))
            avgBlockSize += item[2]
            if changeImage:
                finderPatternsVisualization.addCircle(item[0], item[1], item[2] / 4, clrs[idx % len(clrs)])
                finderPatternsVisualization.addText(item[0], item[1], item[2] / 1.5, 'gray', f"({item[0]},{item[1]})")
        
        avgBlockSize /= 3.0

        if changeImage:
            finderPatternsVisualization.closeFile()
            newImage, dataPoints = self.rotateImage(points, image)
            dataPoints["blockSize"] = avgBlockSize
            return [newImage, dataPoints]
        else:
            dataPoints = self.getPointsPos(points)
            dataPoints["blockSize"] = avgBlockSize
            return [None, dataPoints]

    def getPointsPos(self, points):
        dataPoints = {}
        tl = min(points, key=lambda p: sum(dist(p, other) for other in points))
        dataPoints["tl"] = tl
        otherPoints = [p for p in points if p != tl]
        pA, pB = otherPoints
        v1 = (pA[0] - tl[0], pA[1] - tl[1])
        v2 = (pB[0] - tl[0], pB[1] - tl[1])
        crossProduct = v1[0] * v2[1] - v1[1] * v2[0]

        if crossProduct < 0:
            dataPoints["tr"] = pB
            dataPoints["bl"] = pA
        else:
            dataPoints["tr"] = pA
            dataPoints["bl"] = pB
        
        return dataPoints

    def rotateImage(self, points, image):
        dataPoints = self.getPointsPos(points)
        tl = min(points, key=lambda p: sum(dist(p, other) for other in points))
        otherPoints = [p for p in points if p != tl]
        pA, pB = otherPoints
        angleA = atan2(pA[1] - tl[1], pA[0] - tl[0])
        angleB = atan2(pB[1] - tl[1], pB[0] - tl[0])

        if dataPoints["tr"] == pB:
            targetAngle = degrees(angleB)
        else:
            targetAngle = degrees(angleA)

        return [image.rotate(targetAngle, resample=Image.BICUBIC, expand=True, fillcolor='white'), dataPoints]

    def readFormatVersionInfo(self):
        assert len(self.blocks) == len(self.blocks[0])
        formatInfo = []
        formatMask = "101010000010010"
        
        for idx in range(len(self.blocks) - 1, len(self.blocks) - 8, -1):
            row = self.blocks[idx]
            x, y = row[8]
            self.writer.addRect(self.xDiff + x, self.yDiff + y, self.blockSize, self.blockSize, "none", "purple", 0.5)
            formatInfo.append("0" if self.isLightRoi(x, y) else "1")
            self.addInvalid(idx, 8)
        
        for idx in range(8, -1, -1):
            row = self.blocks[idx]
            x, y = row[8]
            if self.isInvalid(idx, 8):
                continue
            self.writer.addRect(self.xDiff + x, self.yDiff + y, self.blockSize, self.blockSize, "none", "purple", 0.5)
            formatInfo.append("0" if self.isLightRoi(x, y) else "1")
            self.addInvalid(idx, 8)
        
        for idx in range(8):
            row = self.blocks[8]
            x, y = row[idx]
            if self.isInvalid(8, idx):
                continue
            self.writer.addRect(self.xDiff + x, self.yDiff + y, self.blockSize, self.blockSize, "none", "green", 0.5)
            self.addInvalid(8, idx)
        
        for idx in range(len(self.blocks) - 8, len(self.blocks)):
            row = self.blocks[8]
            x, y = row[idx]
            if self.isInvalid(8, idx):
                continue
            self.writer.addRect(self.xDiff + x, self.yDiff + y, self.blockSize, self.blockSize, "none", "green", 0.5)
            self.addInvalid(8, idx)

        # Added invalid position to singular remainder bit
        self.addInvalid(len(self.blocks) - 8, 8)

        unmaskedFormat = format(int("".join(formatInfo), 2) ^ int(formatMask, 2), '015b')
        errorCorrectionLevel = int(unmaskedFormat[:2], 2)
        maskPattern = int(unmaskedFormat[2:5], 2)
        self.ecl = self.eclMap[errorCorrectionLevel]
        self.mask = maskPattern
        self.readVersion()
        
        print("\nECL: {}\nVersion: {}\nMask Pattern: {}\n".format(self.ecl, self.version, self.mask))

    def addInvalid(self, x, y):
        self.invalid.add((x, y))

    def createBlocks(self):
        if self.startX is None or self.startY is None or self.endX is None or self.endY is None or self.blockSize is None:
            raise Exception("Needed values for createBlocks are None!")
        
        y = self.startY
        while y < self.endY:
            rowData = []
            x = self.startX
            while x < self.endX:
                rowData.append((x, y))
                x += self.blockSize
            
            self.blocks.append(rowData)
            y += self.blockSize
        
        self.fixPerimeter()

    def isInvalid(self, i, j):
        if (i, j) in self.invalid:
            return True

        x, y = self.blocks[i][j]
        x, y = x + self.blockSize / 2, y + self.blockSize / 2

        for item in self.timingCoords:
            p1, p2 = item
            x1, y1 = p1
            x2, y2 = p2
            if x1 <= x <= x2 and y1 <= y <= y2:
                return True
        
        for _, item in self.finderCoords.items():
            p1, p2 = item
            x1, y1 = p1
            x2, y2 = p2
            
            if x1 <= x <= x2 and y1 <= y <= y2:
                return True
        
        return False

    def fixPerimeter(self):
        for i in [0, -1]:
            row = self.blocks[i]
            invalid = False
            
            for x, y in row[:7]:
                try:
                    if self.isLightRoi(x, y):
                        invalid = True
                        break
                except:
                    invalid = True
                    break
            
            if invalid:
                print("Deleted first row" if i == 0 else "Deleted last row")
                del self.blocks[i]
        
        invalidFirstCol = False
        invalidLastCol = False

        for row in self.blocks[:7]:
            x, y = row[0]
            invalidFirstCol = self.isLightRoi(x, y)
            if invalidFirstCol:
                break
        
        if invalidFirstCol:
            print("Deleted first column")
            for row in self.blocks:
                del row[0]
        
        for row in self.blocks[:7]:
            x, y = row[-1]
            invalidLastCol = self.isLightRoi(x, y)
            if invalidLastCol:
                break
        
        if invalidLastCol:
            print("Deleted last column")
            for row in self.blocks:
                del row[-1]

    def traverseBlocks(self):
        out = xmlpy.XMLBuilder("unmasked.svg")
        out.addSVG(self.width, self.height)

        for i in range(0, len(self.blocks)):
            for j in range(0, len(self.blocks[i])):
                pxX, pxY = self.blocks[i][j]

                try:
                    if self.isInvalid(i, j):
                        continue
                    
                    text = "W" if self.isLightRoi(pxX, pxY) else "B"
                    bgColor = "black" if text == "B" else "white"
                    if self.applyMask(i, j):
                        bgColor = "black" if text == "W" else "white"
                    
                    out.addRect(pxX, pxY, self.blockSize, self.blockSize, bgColor, 'red', 1)

                except:
                    print_exc()
                    out.closeFile()
                    raise Exception("Error traversing blocks!")
        
        out.closeFile()
    
    def readVersion(self):
        size = len(self.blocks)
        calcVersion = (size - 17) // 4
        self.version = calcVersion
        if calcVersion < 7:
            return

        for j in range(6):
            for i in range(size - 11, size - 8):
                x, y = self.blocks[i][j]
                x1, y1 = self.blocks[j][i]
                self.writer.addRect(self.xDiff + x, self.yDiff + y, self.blockSize, self.blockSize, 'none', 'orange', 0.5)
                self.writer.addRect(self.xDiff + x1, self.yDiff + y1, self.blockSize, self.blockSize, 'none', 'orange', 0.5)
                self.addInvalid(i, j)
                self.addInvalid(j, i)
        
    def readData(self, i, j):
        if self.isInvalid(i, j) or j < 0:
            if i == 8 and j == 8 and self.goingUp:
                i1, j1 = i + 1, j - 3
                self.direction = 'left'
                self.goingUp = not self.goingUp
                return [i1, j1] 
            elif i == len(self.blocks) - 8 and j == 8 and not self.goingUp:
                i1, j1 = i - 1, j - 3
                self.direction = 'left'
                self.goingUp = not self.goingUp
                return [i1, j1]            
            
            return

        x, y = self.blocks[i][j]
        info = "0" if self.isLightRoi(x, y) else "1"
        text = "W" if info == "0" else "B"
        textColor = "black" if info == "0" else "black"

        if self.applyMask(i, j):
            info = "1" if info == "0" else "0"
        
        count = len(self.qr)
        idx = count % 8

        if idx == 0:
            self.color = 'cyan' if self.color == 'red' or self.color == "none" else 'red'

        self.writer.addRect(self.xDiff + x, self.yDiff + y, self.blockSize, self.blockSize, self.color, 'yellow', 0.1, 0.6)
        self.writer.addText(x + (self.blockSize / 4) + self.xDiff, y + (self.blockSize / 1.3) + self.yDiff, self.blockSize / 5, textColor, len(self.qr))
        self.qr.append(info)
    
    def handleInvalidMovement(self, i, j):
        movement = [1, -2] if self.goingUp else [-1, -2]
        i1, j1 = i + movement[0], j + movement[1]
        self.goingUp = not self.goingUp
        self.direction = 'left'
        return [i1, j1]

    def makeMovement(self, i, j):
        resp = self.readData(i, j)
        if resp:
            return resp
        
        if self.direction == 'left':
            i1, j1 = i, j - 1
            self.direction = 'up' if self.goingUp else 'down'
        elif self.direction == 'up':
            i1, j1 = i - 1, j + 1
            self.direction = 'left'
        else:
            i1, j1 = i + 1, j + 1
            self.direction = 'left'

        return [i1, j1]

    def iterateDataBlocks(self, i, j):      
        try:
            if i < 0 or i >= len(self.blocks):
                i1, j1 = self.handleInvalidMovement(i, j)
                return [i1, j1, True]
            if j < -1:
                return [0, 0, False]
            
            i1, j1 = self.makeMovement(i, j)
            return [i1, j1, True]
        
        except:
            print_exc()
    
    def readDataBlocks(self, i, j):
        run = True
        while run:
            i, j, run = self.iterateDataBlocks(i, j)

        self.decodeData()

    def applyMask(self, i, j):
        match self.mask:
            case 0:
                return (i + j) % 2 == 0
            case 1:
                return i % 2 == 0
            case 2:
                return j % 3 == 0
            case 3:
                return (i + j) % 3 == 0
            case 4:
                return ((i // 2) + (j // 3)) % 2 == 0
            case 5:
                return ((i * j) % 2) + ((i * j) % 3) == 0
            case 6:
                return (((i * j) % 2) + ((i * j) % 3)) % 2 == 0
            case 7:
                return (((i + j) % 2) + ((i * j) % 3)) % 2 == 0
            case _:
                raise ValueError("Invalid mask pattern")
    
    def getDataBlockSizes(self):
        key = f"{self.version}-{self.ecl}"
        struct = self.qrDataBlocks.get(key, [])
        blockSizes = []
        changeIndex = None

        for count, size in struct:
            if len(blockSizes) > 0:
                changeIndex = len(blockSizes)
            for _ in range(count):
                blockSizes.append(size)
        
        return [blockSizes, changeIndex]
    
    def decodeInterleaved(self, blockSizes, changeIndex):
        assert len(blockSizes) > 0
        errorBlocks = len(blockSizes)
        totalData = sum(blockSizes)
        bitstring = "".join(self.qr)
        codewords = [int(bitstring[i:i+8], 2) for i in range(0, len(bitstring), 8)]
        roundRobin = defaultdict(list)
        rawData = codewords[:totalData]
        turnNegativeIndex = totalData - (totalData % errorBlocks)

        for i, byte in enumerate(rawData):
            key = i % errorBlocks if i < turnNegativeIndex else changeIndex + (i % errorBlocks)
            roundRobin[key].append(byte)
        
        dataStream = []
        for key in range(errorBlocks):
            dataStream += roundRobin[key]
        
        dataBits = "".join([f"{b:08b}" for b in dataStream])
        return [dataBits, "".join(self.qr)[len(dataBits):]]

    def decodeData(self):
        blockSizes, changeIndex = self.getDataBlockSizes()
        bitstring, errorBits = self.decodeInterleaved(blockSizes, changeIndex)

        startIndex = 0
        result = ""

        while startIndex < len(bitstring) - 4:
            encoding = int(bitstring[startIndex : startIndex + 4], 2)
            startIndex += 4

            if encoding == 0:
                break
        
            match encoding:
                case 1:
                    length = 0
                    if self.version < 10:
                        length = int(bitstring[startIndex:startIndex + 10], 2)
                        startIndex += 10
                    elif self.version < 27:
                        length = int(bitstring[startIndex:startIndex + 12], 2)
                        startIndex += 12
                    else:
                        length = int(bitstring[startIndex:startIndex + 14], 2)
                        startIndex += 14
                    
                    data = []
                    print(f"Encoding: Numeric - Length: {length}")
                    
                    for i in range(0, length, 3):
                        remLength = min(length - i, 3)
                        changes = { 3: 10, 2: 7, 1: 4 }
                        digits = bitstring[startIndex:startIndex + changes[remLength]]
                        byte = str(int(digits, 2)).rjust(remLength, "0")
                        data.append(byte)
                        startIndex += changes[remLength]
                    
                    result += "".join(data)
                
                case 2:
                    length = 0
                    if self.version < 10:
                        length = int(bitstring[startIndex:startIndex + 9], 2)
                        startIndex += 9
                    elif self.version < 27:
                        length = int(bitstring[startIndex:startIndex + 11], 2)
                        startIndex += 11
                    else:
                        length = int(bitstring[startIndex:startIndex + 13], 2)
                        startIndex += 13
                    
                    data = []
                    print(f"Encoding: Alphanumeric - Length: {length}")

                    for i in range(0, length, 2):
                        remLength = min(length - i, 2)
                        if remLength == 2:
                            bits = bitstring[startIndex:startIndex + 11]
                            deci = int(bits, 2)
                            firstCharIdx, secondCharIdx = deci // 45, deci % 45
                            
                            if firstCharIdx < len(self.alnumMap):
                                data.append(self.alnumMap[firstCharIdx])
                            else:
                                print("Invalid:", firstCharIdx)
                            
                            data.append(self.alnumMap[secondCharIdx])
                            startIndex += 11
                        else:
                            bits = bitstring[startIndex : startIndex + 6]
                            val = int(bits, 2)
                            if val < len(self.alnumMap):
                                data.append(self.alnumMap[val])
                            
                            startIndex += 6
                    
                    result += "".join(data)

                case 4:
                    length = 0
                    if self.version < 10:
                        length = int(bitstring[startIndex:startIndex + 8], 2)
                        startIndex += 8
                    else:
                        length = int(bitstring[startIndex:startIndex + 16], 2)
                        startIndex += 16                
                    
                    data = bytearray()
                    print(f"Encoding: Byte - Length: {length}")
                    
                    for _ in range(length):
                        char = bitstring[startIndex:startIndex+8]
                        if char:
                            byte = int(char, 2)
                            data.append(byte)
                        
                        startIndex += 8
                    
                    result += data.decode('utf-8', errors='replace')
                
                case 8:
                    length = 0
                    if self.version < 10:
                        length = int(bitstring[startIndex:startIndex + 8], 2)
                        startIndex += 8
                    elif self.version < 27:
                        length = int(bitstring[startIndex:startIndex + 10], 2)
                        startIndex += 10
                    else:
                        length = int(bitstring[startIndex:startIndex + 12], 2)
                        startIndex += 12
                    
                    data = bytearray()
                    print(f"Encoding: Kanji - Length: {length}")

                    for _ in range(length):
                        char = bitstring[startIndex : startIndex + 13]
                        val = int(char, 2)

                        high = val // 0xC0
                        low = val % 0xC0
                        res = (high << 8) | low

                        if res <= 0x1E00:
                            res += 0x8140
                        else:
                            res += 0xC140
                        
                        h = (res >> 8) & 0xFF
                        l = res & 0xFF
                        
                        data.extend(bytes([h, l]))
                        startIndex += 13
                    
                    result += data.decode('shift_jis', errors='replace')
                    
                case _:
                    if result:
                        print(f"\nCurrent Result:{result}")
                    raise Exception(f"Unimplemented encoding type: {encoding}")

        print(f"\n{result}")