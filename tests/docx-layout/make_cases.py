#!/usr/bin/env python3
"""Builds the DOCX layout test cases from sample.docx (a Word 2007 file with
an inline Basic Block List SmartArt that has no cached drawing part).

  make_cases.py OUT_DIR

Cases (all keep the four text paragraphs of the sample):
  01-sample.docx                 the file as Word saved it
  02-smartart-anchor-square.docx SmartArt floating, wrap square, beside text
  03-smartart-anchor-topbottom.docx  floating, wrap top and bottom
  04-smartart-with-drawing.docx  inline SmartArt with Word's cached drawing part
  05-picture-inline.docx         a picture in the same place
  06-picture-anchor-square.docx  a floating picture, wrap square
  07-two-smartarts.docx          inline SmartArt followed by a floating one
"""
import os
import re
import struct
import sys
import zipfile
import zlib

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(HERE, 'sample.docx')
EMU = 914400

def png(w, h):
    rows = []
    for y in range(h):
        row = bytearray(b'\x00')
        for x in range(w):
            row += bytes((60 + x * 180 // w, 110 + y * 100 // h, 190))
        rows.append(bytes(row))
    raw = b''.join(rows)

    def chunk(t, d):
        return struct.pack('>I', len(d)) + t + d + struct.pack('>I', zlib.crc32(t + d) & 0xffffffff)
    return (b'\x89PNG\r\n\x1a\n' + chunk(b'IHDR', struct.pack('>IIBBBBB', w, h, 8, 2, 0, 0, 0))
            + chunk(b'IDAT', zlib.compress(raw)) + chunk(b'IEND', b''))


def read(z):
    return {n: z.read(n) for n in z.namelist()}


def write(path, parts):
    with zipfile.ZipFile(path, 'w', zipfile.ZIP_DEFLATED) as z:
        names = ['[Content_Types].xml'] + [n for n in parts if n != '[Content_Types].xml']
        for n in names:
            z.writestr(n, parts[n])


INLINE_RE = re.compile(r'<wp:inline\b.*?</wp:inline>', re.S)


def graphic(xml):
    return re.search(r'<a:graphic\b.*?</a:graphic>', xml, re.S).group(0)


def anchor(graphic_xml, cx, cy, wrap, docpr_id, name, x_emu=0, y_emu=0, behind=0):
    wraps = {
        'square': '<wp:wrapSquare wrapText="bothSides"/>',
        'topbottom': '<wp:wrapTopAndBottom/>',
    }
    return ('<wp:anchor distT="0" distB="0" distL="114300" distR="114300" simplePos="0" relativeHeight="251659264" '
            'behindDoc="%d" locked="0" layoutInCell="1" allowOverlap="1">'
            '<wp:simplePos x="0" y="0"/>'
            '<wp:positionH relativeFrom="column"><wp:posOffset>%d</wp:posOffset></wp:positionH>'
            '<wp:positionV relativeFrom="paragraph"><wp:posOffset>%d</wp:posOffset></wp:positionV>'
            '<wp:extent cx="%d" cy="%d"/><wp:effectExtent l="0" t="0" r="0" b="0"/>%s'
            '<wp:docPr id="%d" name="%s"/><wp:cNvGraphicFramePr/>%s</wp:anchor>'
            % (behind, x_emu, y_emu, cx, cy, wraps[wrap], docpr_id, name, graphic_xml))


def pic_graphic(rid, cx, cy):
    return ('<a:graphic xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main"><a:graphicData uri="http://schemas.openxmlformats.org/drawingml/2006/picture">'
            '<pic:pic xmlns:pic="http://schemas.openxmlformats.org/drawingml/2006/picture">'
            '<pic:nvPicPr><pic:cNvPr id="0" name="picture.png"/><pic:cNvPicPr/></pic:nvPicPr>'
            '<pic:blipFill><a:blip r:embed="%s"/><a:stretch><a:fillRect/></a:stretch></pic:blipFill>'
            '<pic:spPr><a:xfrm><a:off x="0" y="0"/><a:ext cx="%d" cy="%d"/></a:xfrm>'
            '<a:prstGeom prst="rect"><a:avLst/></a:prstGeom></pic:spPr></pic:pic></a:graphicData></a:graphic>'
            % (rid, cx, cy))


def add_image(parts, rid):
    parts['word/media/image1.png'] = png(240, 140)
    rels = parts['word/_rels/document.xml.rels'].decode()
    rels = rels.replace('</Relationships>',
                        '<Relationship Id="%s" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/image" '
                        'Target="media/image1.png"/></Relationships>' % rid)
    parts['word/_rels/document.xml.rels'] = rels.encode()
    ct = parts['[Content_Types].xml'].decode()
    if 'Extension="png"' not in ct:
        ct = ct.replace('<Default Extension="rels"', '<Default Extension="png" ContentType="image/png"/><Default Extension="rels"')
    parts['[Content_Types].xml'] = ct.encode()


def drawing_part(cx, cy, texts):
    """a Basic Block List drawing the way Word 2010+ caches it: 3 + 2 blocks"""
    gap = cx * 0.03
    w = (cx - 2 * gap) / 3
    h = w * 0.6
    total_h = 2 * h + gap
    top = (cy - total_h) / 2
    shapes = []
    for i, t in enumerate(texts):
        row, col = divmod(i, 3)
        n_in_row = 3 if row == 0 else len(texts) - 3
        left = (cx - (n_in_row * w + (n_in_row - 1) * gap)) / 2 + col * (w + gap)
        y = top + row * (h + gap)
        shapes.append(
            '<dsp:sp modelId="{00000000-0000-0000-0000-00000000000%d}"><dsp:nvSpPr><dsp:cNvPr id="0" name=""/><dsp:cNvSpPr/></dsp:nvSpPr>'
            '<dsp:spPr><a:xfrm><a:off x="%d" y="%d"/><a:ext cx="%d" cy="%d"/></a:xfrm><a:prstGeom prst="rect"><a:avLst/></a:prstGeom>'
            '<a:solidFill><a:schemeClr val="accent1"/></a:solidFill><a:ln w="25400"><a:solidFill><a:schemeClr val="lt1"/></a:solidFill></a:ln></dsp:spPr>'
            '<dsp:style><a:lnRef idx="2"><a:scrgbClr r="0" g="0" b="0"/></a:lnRef><a:fillRef idx="1"><a:scrgbClr r="0" g="0" b="0"/></a:fillRef>'
            '<a:effectRef idx="0"><a:scrgbClr r="0" g="0" b="0"/></a:effectRef><a:fontRef idx="minor"><a:schemeClr val="lt1"/></a:fontRef></dsp:style>'
            '<dsp:txBody><a:bodyPr spcFirstLastPara="0" vert="horz" wrap="square" lIns="64770" tIns="64770" rIns="64770" bIns="64770" numCol="1" spcCol="1270" anchor="ctr" anchorCtr="0"><a:noAutofit/></a:bodyPr>'
            '<a:lstStyle/><a:p><a:pPr algn="ctr"/><a:r><a:rPr lang="en-US" sz="3400"/><a:t>%s</a:t></a:r></a:p></dsp:txBody>'
            '<dsp:txXfrm><a:off x="%d" y="%d"/><a:ext cx="%d" cy="%d"/></dsp:txXfrm></dsp:sp>'
            % (i, left, y, w, h, t, left, y, w, h))
    return ('<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
            '<dsp:drawing xmlns:dgm="http://schemas.openxmlformats.org/drawingml/2006/diagram" '
            'xmlns:dsp="http://schemas.microsoft.com/office/drawing/2008/diagram" '
            'xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main">'
            '<dsp:spTree><dsp:nvGrpSpPr><dsp:cNvPr id="0" name=""/><dsp:cNvGrpSpPr/></dsp:nvGrpSpPr><dsp:grpSpPr/>'
            + ''.join(shapes) + '</dsp:spTree></dsp:drawing>')


def add_drawing(parts):
    data = parts['word/diagrams/data1.xml'].decode()
    texts = re.findall(r'<a:t>([^<]*)</a:t>', data)
    parts['word/diagrams/drawing1.xml'] = drawing_part(5486400, 3200400, texts).encode()
    data = data.replace('<dgm:bg/><dgm:whole/></dgm:dataModel>',
                        '<dgm:bg/><dgm:whole/><dgm:extLst><a:ext uri="http://schemas.microsoft.com/office/drawing/2008/diagram">'
                        '<dsp:dataModelExt xmlns:dsp="http://schemas.microsoft.com/office/drawing/2008/diagram" relId="rId10" minVer="http://schemas.openxmlformats.org/drawingml/2006/diagram"/>'
                        '</a:ext></dgm:extLst></dgm:dataModel>')
    parts['word/diagrams/data1.xml'] = data.encode()
    rels = parts['word/_rels/document.xml.rels'].decode()
    rels = rels.replace('</Relationships>',
                        '<Relationship Id="rId10" Type="http://schemas.microsoft.com/office/2007/relationships/diagramDrawing" '
                        'Target="diagrams/drawing1.xml"/></Relationships>')
    parts['word/_rels/document.xml.rels'] = rels.encode()
    ct = parts['[Content_Types].xml'].decode()
    ct = ct.replace('</Types>', '<Override PartName="/word/diagrams/drawing1.xml" '
                    'ContentType="application/vnd.ms-office.drawingml.diagramDrawing+xml"/></Types>')
    parts['[Content_Types].xml'] = ct.encode()


def main(out):
    os.makedirs(out, exist_ok=True)
    with zipfile.ZipFile(SRC) as z:
        base = read(z)
    doc = base['word/document.xml'].decode()
    inline = INLINE_RE.search(doc).group(0)
    g = graphic(inline)
    cx, cy = 5486400, 3200400

    write(os.path.join(out, '01-sample.docx'), dict(base))

    # floating SmartArt, smaller so text can flow beside it
    for name, wrap in (('02-smartart-anchor-square.docx', 'square'), ('03-smartart-anchor-topbottom.docx', 'topbottom')):
        p = dict(base)
        w2, h2 = (cx // 2, cy // 2) if wrap == 'square' else (cx, cy)
        a = anchor(g, w2, h2, wrap, 1, 'Diagram 1')
        # the anchor goes at the start of the second paragraph, as Word puts it
        d = doc.replace(inline, '')
        d = re.sub(r'<w:p [^>]*><w:r><w:rPr><w:noProof/></w:rPr><w:drawing></w:drawing></w:r></w:p>', '', d)
        paras = list(re.finditer(r'<w:p [^>]*>', d))
        at = paras[1].end()
        d = d[:at] + '<w:r><w:rPr><w:noProof/></w:rPr><w:drawing>' + a + '</w:drawing></w:r>' + d[at:]
        p['word/document.xml'] = d.encode()
        write(os.path.join(out, name), p)

    p = dict(base)
    add_drawing(p)
    write(os.path.join(out, '04-smartart-with-drawing.docx'), p)

    pcx, pcy = 2743200, 1600200
    p = dict(base)
    add_image(p, 'rId11')
    pic_inline = ('<wp:inline distT="0" distB="0" distL="0" distR="0"><wp:extent cx="%d" cy="%d"/>'
                  '<wp:effectExtent l="0" t="0" r="0" b="0"/><wp:docPr id="1" name="Picture 1"/><wp:cNvGraphicFramePr/>%s</wp:inline>'
                  % (pcx, pcy, pic_graphic('rId11', pcx, pcy)))
    p['word/document.xml'] = doc.replace(inline, pic_inline).encode()
    write(os.path.join(out, '05-picture-inline.docx'), p)

    p = dict(base)
    add_image(p, 'rId11')
    d = re.sub(r'<w:p [^>]*><w:r><w:rPr><w:noProof/></w:rPr><w:drawing><wp:inline\b.*?</wp:inline></w:drawing></w:r></w:p>', '', doc, flags=re.S)
    paras = list(re.finditer(r'<w:p [^>]*>', d))
    at = paras[1].end()
    d = d[:at] + '<w:r><w:rPr><w:noProof/></w:rPr><w:drawing>' + anchor(pic_graphic('rId11', pcx, pcy), pcx, pcy, 'square', 1, 'Picture 1') + '</w:drawing></w:r>' + d[at:]
    p['word/document.xml'] = d.encode()
    write(os.path.join(out, '06-picture-anchor-square.docx'), p)

    p = dict(base)
    d = doc
    paras = list(re.finditer(r'<w:p [^>]*>', d))
    at = paras[4].end()
    d = d[:at] + '<w:r><w:rPr><w:noProof/></w:rPr><w:drawing>' + anchor(g, cx // 2, cy // 2, 'square', 2, 'Diagram 2', x_emu=cx // 2) + '</w:drawing></w:r>' + d[at:]
    p['word/document.xml'] = d.encode()
    write(os.path.join(out, '07-two-smartarts.docx'), p)
    for n in sorted(os.listdir(out)):
        with zipfile.ZipFile(os.path.join(out, n)) as z:
            assert z.testzip() is None
        print(n)


if __name__ == '__main__':
    main(sys.argv[1] if len(sys.argv) > 1 else os.path.join(HERE, 'out'))
