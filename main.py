import argparse
import traceback
import parse
import xmlpy
from PIL import Image
from collections import defaultdict

try:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=str, required=True, help="Input file path")
    parser.add_argument("--output", type=str, required=True, help='Output file path')
    args = parser.parse_args()

    writer = xmlpy.XMLBuilder(args.output)
    image = Image.open(args.input).convert("RGB")
    parser = parse.ImageParser(image.load(), image.width, image.height)
    writer.addSVG(image.width, image.height)
    writer.addImage(0, 0, image.width, image.height, args.input)

    rleX = parser.runLengthEncodingX()
    rleY = parser.runLengthEncodingY()
    tX, tY = parser.findTimingPatterns(rleX, rleY)
    finderCoords = defaultdict(list)
    
    # stored in order [TL, BR]
    findersBox = defaultdict(list)
    timingBox = defaultdict(list)
    
    timingPatternCoords = []
    
    if tX is None or tY is None:
        print(f"Tx is {'None' if tX is None else 'not None'}")
        print(f"Ty is {'None' if tY is None else 'not None'}")
    else:
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

            writer.addRect(item["start"], tX["y"], item["length"], parser.blockSize, "none", "gold", 0.3)
        
        for idx, item in enumerate(tY["data"]):
            if idx == len(tY["data"]) - 1:
                finderCoords["bl"].append((tY["x"] + parser.blockSize, item["start"]))
                finderCoords["bl"].append((tY["x"] + parser.blockSize, item["start"] + item["length"]))
                br = (tY["x"] + parser.blockSize, item["start"] + item["length"])
                timingBox["y"].append(br)
            elif idx == 0:
                tl = (tY["x"], item["start"])
                timingBox["y"].append(tl)
           
            writer.addRect(tY["x"], item["start"], parser.blockSize, item["length"], "none", "gold", 0.3)

    timingList = list(timingBox.values())
    findersList = []

    for key, val in finderCoords.items():
        if key == "tl" or key == "tr":
            bl, br = val
            finderSide = abs(bl[0] - br[0])
            tl = (bl[0], bl[1] - finderSide)
            tr = (tl[0] + finderSide, tl[1])
            writer.addRect(tl[0], tl[1], finderSide, finderSide, "none", "blue", 0.4)
            if key == "tl":
                parser.startX = bl[0]
                parser.startY = tl[1]
                padding = (br[0] + parser.blockSize, br[1] + parser.blockSize)
                findersList.append([tl, padding])
            elif key == "tr":
                parser.endX = tr[0]
                paddingTL = (tl[0] - parser.blockSize, tl[1])
                paddingBR = (br[0], br[1] + parser.blockSize)
                findersList.append([paddingTL, paddingBR])
        else:
            tr, br = val
            finderSide = abs(tr[1] - br[1])
            tl = (tr[0] - finderSide, tr[1])
            bl = (tl[0], tl[1] + finderSide)
            writer.addRect(tl[0], tl[1], finderSide, finderSide, "none", "blue", 0.4)
            paddingTL = (tl[0], tl[1] - parser.blockSize)
            paddingBR = (br[0] + parser.blockSize, br[1])
            findersList.append([paddingTL, paddingBR])
            parser.endY = br[1]

    parser.timingCoords = timingList
    parser.finderCoords = findersList
    parser.createBlocks()
    parser.findFormatPatterns()
    parser.traverseBlocks(writer)

except Exception as e:
    traceback.print_exc()
finally:
    writer.closeNode('svg')
    writer.closeFile()