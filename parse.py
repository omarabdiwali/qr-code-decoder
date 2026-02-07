import xmlpy
import traceback
from collections import defaultdict

class ImageParser:
    def __init__(self, data, width, height, writer):
        self.data = data
        self.width = width
        self.height = height
        self.writer = writer
        self.blockSize, self.startX, self.endX, self.startY, self.endY = [None for _ in range(5)]
        self.timingCoords, self.finderCoords, self.mask = None, None, None,
        self.goingUp = True
        self.direction = "left"
        self.blocks = []
        self.qr = []
        self.invalid = set()
    
    def getColorValue(self, val):
        totalValue = sum(val) / 2
        return int(totalValue < 190)

    def diff(self, a, b, threshold):
        return abs(a - b) < threshold
    
    def isLightRoi(self, x, y):
        middleX, middleY = (x + self.blockSize // 2), (y + self.blockSize // 2)
        rgb = self.data[middleX, middleY]
        return self.getColorValue(rgb) == 0

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

    def findTimingPatterns(self, xData, yData):
        timingX = None
        timingY = None
        
        for obj in xData:
            for y, value in obj.items():
                items = value["data"]
                firstItem = items[0]
                startIndex = 1 if firstItem["color"] == 0 else 0
                endIndex = len(items) - 1 if startIndex == 1 else len(items)
                startLength = 0
                
                valid = True
                tempBlockSize = self.blockSize
                totalSize = 0
                totalCount = 0
                
                if len(items) < 5:
                    continue
                                    
                for i in range(startIndex, endIndex):
                    item = items[i]
                    
                    if i == startIndex:
                        if item["color"] != 1:
                            valid = False
                            # print("MISS (start):", item)
                            break
                        
                        startLength = item["length"]
                        tempBlockSize = item["length"] / 7
                    
                    elif i == endIndex - 1:
                        if item["color"] != 1:
                            valid = False
                            # print("MISS:", item)
                            break
                    
                    elif self.diff(item["length"], startLength, tempBlockSize):
                        if i - startIndex < 20 or item["color"] != 1:
                            # print("MISS (idk):", item)
                            valid = False
                            break
                        endIndex = i + 1
                        # print(item)
                        break
                    
                    else:                        
                        if not self.diff(item["length"], tempBlockSize, tempBlockSize):
                            valid = False
                            # print("MISS (size):", item)
                            break
                        else:
                            totalSize += item['length']
                            totalCount += 1
                    
                    # print(y, item)
                
                # print('---------------------------')
                if valid:
                    actualBlockSize = totalSize / totalCount
                    timingX = { "y": y, "data": items[startIndex:endIndex] }
                    self.blockSize = actualBlockSize
                    break
        
            if timingX is not None:
                break

        for obj in yData:
            for x, value in obj.items():
                items = value["data"]
                firstItem = items[0]
                startIndex = 1 if firstItem["color"] == 0 else 0
                endIndex = len(items) - 1 if startIndex == 1 else len(items)
                valid = True
                tempBlockSize = self.blockSize
                totalCount = 0
                totalSize = 0

                startLength = 0
                
                if len(items) < 5:
                    continue
                                    
                for i in range(startIndex, endIndex):
                    item = items[i]
                    
                    if i == startIndex:
                        if item["color"] != 1:
                            valid = False
                            break
                        
                        startLength = item['length']
                        tempBlockSize = tempBlockSize if tempBlockSize is not None else startLength / 7
                    
                    elif i == endIndex - 1:
                        if item["color"] != 1:
                            valid = False
                            break
                    
                    elif self.diff(item["length"], startLength, tempBlockSize):
                        if totalSize < 4 or item["color"] != 1:
                            # print("MISS (idk):", item)
                            valid = False
                            break
                        endIndex = i + 1
                        break
                    
                    else:                        
                        if not self.diff(item["length"], tempBlockSize, tempBlockSize):
                            valid = False
                            break
                        else:
                            totalSize += item["length"]
                            totalCount += 1
                    
                    # print(item)
                
                # print('---------------------------------------------')
                if valid:
                    yBlockSize = totalSize / totalCount
                    self.blockSize = (self.blockSize + yBlockSize) / 2 if self.blockSize is not None else yBlockSize
                    timingY = { "x": x, "data": items[startIndex:endIndex] }
                    break

            if timingY is not None:
                break
        
        return [timingX, timingY]

    def getClosestMatch(self, moving, constant, expectedLength, data, direction='x'):
        currentClosest = None
        currentInfo = []
        currentStartIndex = []
        currentOtherIndex = None

        for obj in data:
            for i, value in obj.items():
                for idx, item in enumerate(value['data']):
                    diff = abs(item["start"] - moving) + abs(i - constant)
                    if currentClosest is None or diff < currentClosest:
                        currentClosest = diff
                        currentStartIndex = idx
                        currentOtherIndex = i
                    
                    if i == round(currentOtherIndex + self.blockSize / 2):
                        currentInfo = value['data']
        
        if currentClosest is None:
            return None
        
        # print(currentInfo[currentStartIndex])
        # print("target: {},{} - found: {},{}".format(moving, constant, currentInfo[currentStartIndex]['start'], currentOtherIndex))
        # print(currentStartIndex, expectedLength)
        
        currentInfo = currentInfo[currentStartIndex:currentStartIndex + expectedLength]
        if self.diff(currentInfo[0]['length'], currentInfo[-1]['length'], self.blockSize):
            currentInfo[-1]['length'] = currentInfo[0]['length']
        
        dataFormat = { currentOtherIndex: { 'data': currentInfo } }
        return self.checkTimingPatternRow(dataFormat, direction)

    def checkTimingPatternRow(self, rowData, direction="x"):
        res = self.findTimingPatterns([rowData] if direction == 'x' else [], [rowData] if direction == 'y' else [])
        return res[0] if direction == 'x' else res[1]

    def findFormatPatterns(self):
        for i in range(0, len(self.blocks) - 5):
            for j in range(0, len(self.blocks[i]) - 5):
                x, y = self.blocks[i][j]
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
    
    def readFormatVersionInfo(self):
        assert len(self.blocks) == len(self.blocks[0])
        formatInfo = []
        formatMask = "101010000010010"
        
        for idx in range(len(self.blocks) - 1, len(self.blocks) - 8, -1):
            row = self.blocks[idx]
            x, y = row[8]
            self.writer.addRect(x, y, self.blockSize, self.blockSize, "none", "purple", 0.3)
            formatInfo.append("0" if self.isLightRoi(x, y) else "1")
            self.addInvalid(idx, 8)
        
        for idx in range(8, -1, -1):
            row = self.blocks[idx]
            x, y = row[8]
            if self.isInvalid(idx, 8)[0]:
                continue
            self.writer.addRect(x, y, self.blockSize, self.blockSize, "none", "purple", 0.3)
            formatInfo.append("0" if self.isLightRoi(x, y) else "1")
            self.addInvalid(idx, 8)

        unmaskedFormat = format(int("".join(formatInfo), 2) ^ int(formatMask, 2), '015b')
        print(unmaskedFormat)
        
        errorCorrectionLevel = unmaskedFormat[:2]
        maskPattern = unmaskedFormat[2:5]
        print("ECL: {}, Mask Pattern: {}".format(errorCorrectionLevel, maskPattern))
        self.mask = int(maskPattern, 2)

    def addInvalid(self, x, y):
        self.invalid.add((x, y))

    def createBlocks(self):
        if self.startX is None or self.startY is None or self.endX is None or self.endY is None or self.blockSize is None:
            print("Needed values are None!")
            return
        
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
        # [TL, BR]
        if (i, j) in self.invalid:
            return [True, "unknown"]

        x, y = self.blocks[i][j]
        x, y = x + self.blockSize / 2, y + self.blockSize / 2

        for item in self.timingCoords:
            p1, p2 = item
            x1, y1 = p1
            x2, y2 = p2
            if x1 <= x <= x2 and y1 <= y <= y2:
                return [True, "timing"]
        
        for item in self.finderCoords:
            p1, p2 = item
            x1, y1 = p1
            x2, y2 = p2
            if x1 <= x <= x2 and y1 <= y <= y2:
                return [True, "finder"]
        
        return [False, ""]    

    def fixPerimeter(self):
        for i in [0, -1]:
            row = self.blocks[i]
            invalid = False
            
            for x, y in row[:7]:
                if self.isLightRoi(x, y):
                    invalid = True
                    break
            
            if invalid:
                print("invalid?", i)
                del self.blocks[-1]
        
        invalidFirstCol = False
        invalidLastCol = False

        for row in self.blocks[:7]:
            for x, y in row:
                if self.isLightRoi(x, y):
                    invalidFirstCol = True
                break
        
        if invalidFirstCol:
            print("invalid? 0")
            for row in self.blocks:
                del row[0]
        
        for row in self.blocks[:7]:
            for x, y in row[::-1]:
                if self.isLightRoi(x, y):
                    invalidLastCol = True
                break
        
        if invalidLastCol:
            print("invalid? -1")
            for row in self.blocks:
                del row[-1]

    def traverseBlocks(self):
        out = xmlpy.XMLBuilder("unmasked.svg")
        out.addSVG(self.width, self.height)

        for i in range(0, len(self.blocks)):
            for j in range(0, len(self.blocks[i])):
                if j <= 8:
                    continue
                pxX, pxY = self.blocks[i][j]
                tX, tY = pxX + (self.blockSize / 4), pxY + (self.blockSize / 2)

                try:
                    if self.isInvalid(i, j)[0]:
                        continue
                    
                    text = "W" if self.isLightRoi(pxX, pxY) else "B"
                    bgColor = "black" if text == "B" else "white"
                    
                    if self.getMaskFunction(i, j):
                        bgColor = "black" if text == "W" else "white"
                    
                    out.addRect(pxX, pxY, self.blockSize, self.blockSize, bgColor, bgColor, 0.3)  
                    self.writer.addRect(pxX, pxY, self.blockSize, self.blockSize, "none", 'orange', 0.3)
                    # self.writer.addText(tX, tY, self.blockSize / 2, "red", text)
                except Exception as e:
                    traceback.print_exc()
                    continue
        
        out.closeNode('svg')
        out.closeFile()
    
    def readData(self, i, j):
        if self.isInvalid(i, j)[0]:
            return

        x, y = self.blocks[i][j]
        info = "0" if self.isLightRoi(x, y) else "1"
        if self.getMaskFunction(i, j):
            info = "0" if "1" else "0"
        
        self.writer.addText(x + (self.blockSize / 4), y + (self.blockSize / 1.3), self.blockSize / 2.5, "red", len(self.qr))
        self.qr.append(info)
    
    def handleInvalidMovement(self, i, j):
        movement = [1, -2] if self.goingUp else [-1, -2]
        i1, j1 = i + movement[0], j + movement[1]
        self.goingUp = not self.goingUp
        self.direction = 'left'
        return [i1, j1]

    def makeMovement(self, i, j):
        if self.direction == 'left':
            self.readData(i, j)
            i1, j1 = i, j - 1
            self.direction = 'up' if self.goingUp else 'down'
            return [i1, j1]
        elif self.direction == 'up':
            self.readData(i, j)
            i1, j1 = i - 1, j + 1
            self.direction = 'left'
            return [i1, j1]
        else:
            self.readData(i, j)
            i1, j1 = i + 1, j + 1
            self.direction = 'left'
            return [i1, j1]            

    def readDataBlocks(self, i, j):      
        try:
            if i < 0 or i >= len(self.blocks) or self.isInvalid(i, j)[1] == 'finder':
                i1, j1 = self.handleInvalidMovement(i, j)
                return self.readDataBlocks(i1, j1)
            if j <= 8:
                return
            
            i1, j1 = self.makeMovement(i, j)
            return self.readDataBlocks(i1, j1) 
        
        except:
            traceback.print_exc()
    
    def getMaskFunction(self, x, y):
        match self.mask:
            case 0: return (x + y) % 2 == 0
            case 1: return x % 2 == 0
            case 2: return y % 3 == 0
            case 3: return (x + y) % 3 == 0
            case 4: return (x // 2 + y // 3) % 2 == 0
            case 5: return (x * y) % 2 + (x * y) % 3 == 0
            case 6: return ((x * y) % 2 + (x * y) % 3) % 2 == 0
            case 7: return ((x + y) % 2 + (x * y) % 3) % 2 == 0
            case _: return False
    
    def addFindersToInvalid(self):
        for i in range(8):
            for j in range(len(self.blocks[0]) - 8, len(self.blocks[0])):
                    x, y = self.blocks[i][j]
                    # self.writer.addRect(x, y, self.blockSize, self.blockSize, 'none', 'red', 0.5)
                    # self.addInvalid(i, j, "Finder")
        