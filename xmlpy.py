class XMLBuilder:
    def __init__(self, path):
        self.file = open(path, "w")
    def addNode(self, node):
        self.file.write(f"<{node} ")
    def addSVG(self, width, height):
        self.file.write(f'<svg version="1.1" width="{width}" height="{height}" xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink">\n')
    def addImage(self, x, y, width, height, href):
        self.file.write(f'  <image x="{x}" y="{y}" width="{width}" height="{height}" href="{href}" />\n')
    def addCircle(self, cx, cy, r, fill):
        self.file.write(f'  <circle cx="{cx}" cy="{cy}" r="{r}" fill="{fill}" />\n')
    def addRect(self, x, y, width, height, fill, stroke, strokeWidth):
        self.file.write(f'  <rect x="{x}" y="{y}" width="{width}" height="{height}" fill="{fill}" stroke="{stroke}" stroke-width="{strokeWidth}" />\n')
    def addText(self, x, y, fontSize, fill, text):
        self.file.write(f'  <text x="{x}" y="{y}" font-size="{fontSize}" fill="{fill}">{text}</text>\n')
    def closeNode(self, node):
        self.file.write(f"</{node}>\n")
    def closeFile(self):
        self.file.close()