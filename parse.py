from collections import defaultdict

class ImageParser:
    def __init__(self, data, width, height):
        self.data = data
        self.width = width
        self.height = height
        self.blockSize, self.startX, self.endX, self.startY, self.endY = [None for _ in range(5)]
        self.timingCoords, self.finderCoords = None, None
        self.blocks = []
        self.invalid = set()
    
    def getColorValue(self, val):
        totalValue = sum(val) / 2
        return int(totalValue < 190)

    def diff(self, a, b, threshold):
        return abs(a - b) <= threshold

    def getSection(self, x, y):
        middleX = self.width / 2
        middleY = self.height / 2
        if x < middleX:
            return "tl" if y < middleY else "bl"
        else:
            return "tr" if y < middleY else "br"
    
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
                valid = True
                tempBlockSize = self.blockSize
                totalSize = 0
                totalCount = 0
                
                if len(items) < 3:
                    continue
                                    
                for i in range(startIndex, endIndex):
                    item = items[i]
                    if i == startIndex or i == endIndex - 1:
                        if item["color"] != 1:
                            print("MISS (start/last):", item)
                            valid = False
                            break
                        else:
                            print(item)
                    else:
                        if tempBlockSize is None:
                            tempBlockSize = items[i-1]["length"] / 7
                        
                        if not self.diff(item["length"], tempBlockSize, tempBlockSize / 2):
                            print("MISS (size):", item)
                            valid = False
                            break
                        else:
                            totalSize += item['length']
                            totalCount += 1
                            print(item)
                
                print("------------------------------------------------")
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
                
                if len(items) < 3:
                    continue
                    
                print(x)
                
                for i in range(startIndex, endIndex):
                    item = items[i]
                    if i == startIndex or i == endIndex - 1:
                        if item["color"] != 1:
                            print("MISS (start/last):", item)
                            valid = False
                            break
                        else:
                            print(item)
                    else:
                        if tempBlockSize is None:
                            tempBlockSize = items[i-1]["length"] / 7
                        
                        if not self.diff(item["length"], tempBlockSize, tempBlockSize / 2):
                            print("MISS (size):", item)
                            valid = False
                            break
                        else:
                            print(item)
                            totalSize += item["length"]
                            totalCount += 1
                
                print("------------------------------------------------")
                if valid:
                    yBlockSize = totalSize / totalCount
                    self.blockSize = (self.blockSize + yBlockSize) / 2 if self.blockSize is not None else yBlockSize
                    timingY = { "x": x, "data": items[startIndex:endIndex] }
                    break

            if timingY is not None:
                break
        
        return [timingX, timingY]

    def findFormatPatterns(self):
        for i in range(0, len(self.blocks) - 5):
            for j in range(0, len(self.blocks[i]) - 5):
                x, y = self.blocks[i][j]
                if (x, y) in self.invalid:
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
                        patternCoords.append((x1, y1))
                    if not valid:
                        break
                
                if valid:
                    for coord in patternCoords:
                        self.addInvalid(coord[0], coord[1])
    
    def addInvalid(self, x, y):
        mX, mY = x + (self.blockSize) / 2, y + (self.blockSize / 2)
        self.invalid.add((mX, mY))
    
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

    def isInvalid(self, x, y):
        # [TL, BR]
        if (x, y) in self.invalid:
            return True

        for item in self.timingCoords:
            p1, p2 = item
            x1, y1 = p1
            x2, y2 = p2
            if x1 <= x <= x2 and y1 <= y <= y2:
                return True
        
        for item in self.finderCoords:
            p1, p2 = item
            x1, y1 = p1
            x2, y2 = p2
            if x1 <= x <= x2 and y1 <= y <= y2:
                return True
        
        return False
    
    def traverseBlocks(self, writer):
        for x in range(len(self.blocks) - 1, -1, -1):
            for y in range(len(self.blocks[x]) - 1, -1, -1):
                pxX, pxY = self.blocks[x][y]
                mX, mY = pxX + (self.blockSize / 2), pxY + (self.blockSize / 2)
                tX, tY = pxX + (self.blockSize / 4), pxY + (self.blockSize / 4)
                try:
                    inValid = self.isInvalid(mX, mY)
                    text = "X" if inValid else "W" if self.isLightRoi(pxX, pxY) else "B"
                    color = "red" if inValid else "purple"
                    writer.addRect(pxX, pxY, self.blockSize, self.blockSize, "none" if not inValid else "red", "skyblue", 0.3)  
                    not inValid and writer.addText(tX, tY + self.blockSize / 2, self.blockSize / 2, color, text)
                except:
                    continue
