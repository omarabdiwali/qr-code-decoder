class XMLBuilder:
    def __init__(self, path):
        self.file = open(path, "w")
        self.openNodes = []
    def getPadding(self):
        return "  " * len(self.openNodes) 
    def createAttributes(self, attr):
        for key, value in attr.items():
            self.addAttribute(key, value)
    def createNode(self, node, attr, shouldCloseNode=True, needsNewLine=True):
        self.addNode(node)
        self.createAttributes(attr)
        self.closeAttributes(shouldCloseNode, needsNewLine)
    def writeLine(self, text):
        self.file.write(f"{self.getPadding()}{text}\n")
    def write(self, text):
        self.file.write(f"{text}")
    def addNode(self, node):
        self.file.write(f"{self.getPadding()}<{node}")
        self.openNodes.append(node)
    def addAttribute(self, key, value):
        self.file.write(f' {key}="{value}"')
    def addSVG(self, width, height):
        self.file.write(f'<svg version="1.1" width="{width}" height="{height}" xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink">\n')
        self.openNodes.append('svg')
    def addImage(self, x, y, width, height, href):
        self.file.write(f'{self.getPadding()}<image x="{x}" y="{y}" width="{width}" height="{height}" href="{href}" />\n')
    def addCircle(self, cx, cy, r, fill):
        self.file.write(f'{self.getPadding()}<circle cx="{cx}" cy="{cy}" r="{r}" fill="{fill}" />\n')
    def addRect(self, x, y, width, height, fill, stroke, strokeWidth, opacity=1.0):
        self.file.write(f'{self.getPadding()}<rect x="{x}" y="{y}" width="{width}" height="{height}" fill="{fill}" stroke="{stroke}" stroke-width="{strokeWidth}" fill-opacity="{opacity}" />\n')
    def addText(self, x, y, fontSize, fill, text):
        self.file.write(f'{self.getPadding()}<text x="{x}" y="{y}" font-size="{fontSize}" fill="{fill}">{text}</text>\n')
    def closeAllNodes(self):
        for _ in range(len(self.openNodes)):
            self.closeNode()
    def closeNode(self, padStart=True):
        if len(self.openNodes) > 0:
            node = self.openNodes.pop()
            padding = self.getPadding() if padStart else ""
            self.file.write(f"{padding}</{node}>\n")
    def closeAttributes(self, closeNode, needsNewline=True):
        if len(self.openNodes) > 0:
            value = " />" if closeNode else ">"
            value = f"{value}\n" if needsNewline else value
            self.file.write(value)
            if closeNode:
                self.openNodes.pop()
    def closeFile(self):
        self.closeAllNodes()
        self.file.close()