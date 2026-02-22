import parse
from time import time
from argparse import ArgumentParser
from traceback import print_exc
from PIL import Image, ImageFilter, ImageEnhance
from collections import defaultdict

def readQRCode(filter):
    try:
        start = time()
        passed = False
        parser = ArgumentParser()
        parser.add_argument("--input", type=str, required=True, help="Input file path")
        parser.add_argument("--output", type=str, required=True, help='Output file path')
        args = parser.parse_args()

        useModified = False
        image = Image.open(args.input)
        blackAndWhite = image.convert('L')
        
        if filter is None:
            modifiedImage = blackAndWhite
        elif type(filter) == str:
            enhancer = ImageEnhance.Sharpness(blackAndWhite)
            modifiedImage = enhancer.enhance(2.0)
        else:
            modifiedImage = blackAndWhite.filter(filter)

        parser = parse.ImageParser(modifiedImage.load(), modifiedImage.width, modifiedImage.height, args.output)
        rleX = parser.runLengthEncodingX()
        rleY = parser.runLengthEncodingY()
        finders = parser.findFinderPatterns(rleX, 'y', args.input)
        
        if 'bottom-right' in finders:
            if 'top-left' not in finders:
                modifiedImage = modifiedImage.rotate(180, expand=True)
                image = image.rotate(180, expand=True)
            elif 'top-right' not in finders:
                modifiedImage = modifiedImage.rotate(-90, expand=True)
                image = image.rotate(-90, expand=True)
            elif 'bottom-left' not in finders:
                modifiedImage = modifiedImage.rotate(90, expand=True)
                image = image.rotate(90, expand=True)
            
            image.save('temp.png')
            useModified = True
            parser.updateParserValues(modifiedImage)
            rleX = parser.runLengthEncodingX()
            rleY = parser.runLengthEncodingY()
        
        if useModified:
            parser.writer.addSVG(image.width, image.height)
            parser.writer.addImage(0, 0, image.width, image.height, 'temp.png')
        else:
            parser.writer.addSVG(modifiedImage.width, modifiedImage.height)
            parser.writer.addImage(0, 0, modifiedImage.width, modifiedImage.height, args.input)

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
            
            parser.writer.addRect(item["start"], tX["y"], item["length"], parser.blockSize, "none", "gold", 0.4)
        
        for idx, item in enumerate(tY["data"]):
            if idx == len(tY["data"]) - 1:
                finderCoords["bl"].append((tY["x"] + parser.blockSize, item["start"]))
                finderCoords["bl"].append((tY["x"] + parser.blockSize, item["start"] + item["length"]))
                br = (tY["x"] + parser.blockSize, item["start"] + item["length"])
                timingBox["y"].append(br)
            elif idx == 0:
                tl = (tY["x"], item["start"])
                timingBox["y"].append(tl)
        
            parser.writer.addRect(tY["x"], item["start"], parser.blockSize, item["length"], "none", "gold", 0.4)

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
        passed = True
    except Exception:
        print()
        print_exc()
        print()
    finally:
        parser.writer.closeNode('svg')
        parser.writer.closeFile()
        end = time()
        duration = round((end - start), 5)
        if passed:
            print("\nProcessing this image took {} seconds.".format(duration))
        else:
            print("Processing this image took {} seconds.\n".format(duration))
        
        return passed

imageFilters = [None, ImageFilter.EDGE_ENHANCE, ImageFilter.SMOOTH, ImageFilter.GaussianBlur, 'sharpness']
for idx, filter in enumerate(imageFilters):
    print(f"Attempt #{idx+1}:")
    if readQRCode(filter):
        break