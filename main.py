import parse
from xml.sax.saxutils import escape
from requests import get
from io import BytesIO
from time import time
from argparse import ArgumentParser
from traceback import print_exc
from PIL import Image, ImageFilter, ImageEnhance
from collections import defaultdict

argparser = ArgumentParser()
argparser.add_argument("--input", type=str, required=True, help="Input file/url path")
argparser.add_argument("--output", type=str, required=True, help='Output file path')
argparser.add_argument("--is-url", action='store_true', help="Image input path is a URL")
args = argparser.parse_args()

if args.is_url:
    print("Fetching image...\n")
    response = get(args.input, stream=True)
    if response.status_code == 200:
        image = Image.open(BytesIO(response.content))
        args.input = escape(args.input, entities={'"': "&quot;"})
    else:
        raise Exception(f"{response.status_code} Error retrieving image!")
else:
    image = Image.open(args.input)

def applyFilter(image, filter):
    blackAndWhite = image.convert('L')

    if filter is None:
        return blackAndWhite
    elif type(filter) == str:
        enhancer = ImageEnhance.Sharpness(blackAndWhite)
        return enhancer.enhance(2.0)
    else:
        return blackAndWhite.filter(filter)

def readQRCode(image, filter, crop=True):
    try:
        parser = None
        start = time()
        passed = False
        modifiedImage = applyFilter(image, filter)
        parser = parse.ImageParser(modifiedImage.load(), modifiedImage.width, modifiedImage.height, args.output)
        rleX = parser.runLengthEncodingX()
        rleY = parser.runLengthEncodingY()

        rotatedImage, rotatedDataValues, isRotated = parser.findFinderPatterns(rleX, 'y', args.input, image)
        
        if isRotated:
            rotatedImage.save('temp.png')
            modifiedImage = applyFilter(rotatedImage, filter)
            parser.updateParserValues(modifiedImage, 0, 0)
            rleX = parser.runLengthEncodingX()
            rleY = parser.runLengthEncodingY()
        
        imageSrc = 'temp.png' if isRotated else args.input
        parser.writer.addSVG(modifiedImage.width, modifiedImage.height)
        parser.writer.addImage(0, 0, modifiedImage.width, modifiedImage.height, imageSrc)

        if crop:
            _, dataValues = parser.findFinderPatterns(rleX, 'y', imageSrc, modifiedImage, False)

            borders = [(0, 0), (0, 0), (0, 0), (0, 0)]
            ltrb = [0, 0, 0, 0]
            finderBlockSize = dataValues['blockSize']
            del dataValues['blockSize']

            for key, val in dataValues.items():
                x, y = val[0], val[1]
                if key == "tl":
                    mostLeft = max(0, x - finderBlockSize * 6)
                    mostTop = max(0, y - finderBlockSize * 6)
                    borders[0] = (mostLeft, mostTop)
                elif key == "tr":
                    mostRight = min(x + finderBlockSize * 13, modifiedImage.width)
                    mostTop = min(max(y - finderBlockSize * 6, 0), borders[0][1])
                    borders[0] = (borders[0][0], mostTop)
                    borders[1] = (mostRight, mostTop)
                    ltrb[1] = mostTop
                    ltrb[2] = mostRight
                elif key == "bl":
                    mostLeft = min(max(x - finderBlockSize * 6, 0), borders[0][0])
                    mostBottom = min(y + finderBlockSize * 11, modifiedImage.height)
                    borders[0] = (mostLeft, borders[0][1])
                    borders[2] = (mostLeft, mostBottom)
                    ltrb[0] = mostLeft
                    ltrb[3] = mostBottom
            
            borders[3] = (borders[1][0], borders[2][1])
            croppedImage = modifiedImage.crop(ltrb)
            croppedImage.save('cropped.png')

            parser.updateParserValues(croppedImage, ltrb[0], ltrb[1])
            rleX = parser.runLengthEncodingX()
            rleY = parser.runLengthEncodingY()

        tX = parser.findTimingPatterns(rleX, 'y')
        tY = parser.findTimingPatterns(rleY, 'x', tX)
        
        if not tX or not tY:
            tY = parser.findTimingPatterns(rleY, 'x')
            tX = parser.findTimingPatterns(rleX, 'y', tY)
        
        finderCoords = defaultdict(list)
        # stored in order [TL, BR]
        timingBox = defaultdict(list)
        
        if tX:
            print("Found timer pattern on the x-axis!")
        if tY:
            print("Found timer pattern on the y-axis!")
        
        assert tY is not None and tX is not None
        parser.blockSize = (tX['blockSize'] + tY['blockSize']) / 2
        
        for idx, item in enumerate(tX["data"]):
            if idx == 0 or idx == len(tX["data"]) - 1:
                key = "tl" if idx == 0 else "tr"
                finderCoords[key].append((item["start"], tX["y"] + parser.blockSize))
                finderCoords[key].append((item["start"] + item["length"], tX["y"] + parser.blockSize))
                if idx == 0:
                    tl = (item["start"], tX["y"])
                    timingBox["x"].append(tl)
                else:
                    br = (item["start"] + item["length"], tX["y"] + parser.blockSize)
                    timingBox["x"].append(br)
            
            parser.writer.addRect(parser.xDiff + item["start"], parser.yDiff + tX["y"], item["length"], parser.blockSize, "none", "gold", 0.4)
        
        for idx, item in enumerate(tY["data"]):
            if idx == len(tY["data"]) - 1:
                finderCoords["bl"].append((tY["x"] + parser.blockSize, item["start"]))
                finderCoords["bl"].append((tY["x"] + parser.blockSize, item["start"] + item["length"]))
                br = (tY["x"] + parser.blockSize, item["start"] + item["length"])
                timingBox["y"].append(br)
            elif idx == 0:
                tl = (tY["x"], item["start"])
                timingBox["y"].append(tl)
        
            parser.writer.addRect(parser.xDiff + tY["x"], parser.yDiff + item["start"], parser.blockSize, item["length"], "none", "gold", 0.4)

        timingList = list(timingBox.values())
        findersPos = {}

        for key, val in finderCoords.items():
            if key == "tl" or key == "tr":
                bl, br = val
                finderSide = abs(bl[0] - br[0])
                tl = (bl[0], bl[1] - finderSide)
                tr = (tl[0] + finderSide, tl[1])
                # writer.addRect(tl[0], tl[1], finderSide, finderSide, "none", "blue", 0.4)
                if key == "tl":
                    parser.startX = bl[0]
                    parser.startY = tl[1]
                    padding = (br[0] + parser.blockSize, br[1] + parser.blockSize)
                    findersPos[key] = [tl, padding]
                elif key == "tr":
                    parser.endX = tr[0]
                    paddingTL = (tl[0] - parser.blockSize, tl[1])
                    paddingBR = (br[0], br[1] + parser.blockSize)
                    findersPos[key] = [paddingTL, paddingBR]
            else:
                tr, br = val
                finderSide = abs(tr[1] - br[1])
                tl = (tr[0] - finderSide, tr[1])
                bl = (tl[0], tl[1] + finderSide)
                # writer.addRect(tl[0], tl[1], finderSide, finderSide, "none", "blue", 0.4)
                paddingTL = (tl[0], tl[1] - parser.blockSize)
                paddingBR = (br[0] + parser.blockSize, br[1])
                findersPos[key] = [paddingTL, paddingBR]
                parser.endY = br[1]

        parser.timingCoords = timingList
        parser.finderCoords = findersPos
        parser.createBlocks()
        parser.findAlignmentPatterns()
        parser.readFormatVersionInfo()
        parser.traverseBlocks()

        startX, startY = len(parser.blocks) - 1, len(parser.blocks[0]) - 1
        parser.readDataBlocks(startX, startY)
        parser.decodeData()
        passed = True
    except Exception:
        print()
        print_exc()
        print()
    finally:
        if parser:
            parser.writer.closeFile()
        end = time()
        duration = round((end - start), 5)
        if passed:
            print("\nProcessing this image took {} seconds.".format(duration))
        else:
            if crop == False:
                print("Processing this image took {} seconds.\n".format(duration))
            else:
                print("Processing this image (cropping) took {} seconds. Trying second option...\n".format(duration))
                return readQRCode(image, filter, False)
        
        return passed

imageFilters = [None, ImageFilter.EDGE_ENHANCE, ImageFilter.SMOOTH, ImageFilter.GaussianBlur, 'sharpness']
for idx, filter in enumerate(imageFilters):
    print(f"Attempt #{idx+1}:")
    if readQRCode(image, filter):
        break