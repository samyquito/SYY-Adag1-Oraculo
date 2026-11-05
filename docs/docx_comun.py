"""Funciones compartidas por gen_informe.py y gen_manual.py para escribir WordprocessingML."""
import re

from lxml import etree as E

WNS = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"
MNS = "http://schemas.openxmlformats.org/officeDocument/2006/math"
W = "{%s}" % WNS
M = "{%s}" % MNS
XML = "{http://www.w3.org/XML/1998/namespace}space"


def ele(tag, parent=None, **attrs):
    e = E.Element(tag) if parent is None else E.SubElement(parent, tag)
    for k, v in attrs.items():
        e.set(W + k, str(v))
    return e


MONO = "Consolas"


def corrida(p, texto, negrita=False, resaltar=False, mono=False):
    r = ele(W + "r", p)
    if negrita or resaltar or mono:
        pr = ele(W + "rPr", r)
        if mono:
            ele(W + "rFonts", pr, ascii=MONO, hAnsi=MONO, cs=MONO)
        if negrita:
            ele(W + "b", pr, val="1")
            ele(W + "bCs", pr, val="1")
        if mono:
            ele(W + "sz", pr, val=19)
            ele(W + "szCs", pr, val=19)
        if resaltar:
            ele(W + "highlight", pr, val="yellow")
    t = ele(W + "t", r)
    t.text = texto
    t.set(XML, "preserve")


def m_run(padre, texto):
    if not texto:
        return
    r = E.SubElement(padre, M + "r")
    t = E.SubElement(r, M + "t")
    t.text = texto
    t.set(XML, "preserve")


def grupo(s, i):
    assert s[i] == "{", s
    prof, j = 0, i
    while True:
        prof += {"{": 1, "}": -1}.get(s[j], 0)
        if prof == 0:
            return s[i + 1 : j], j + 1
        j += 1


def contenedor(padre, nombre, texto):
    e = E.SubElement(padre, M + nombre)
    llenar(e, texto)


def llenar(padre, s):
    """Interpreta `_{}` y `^{}`. La base es el símbolo anterior, o `∑`/`∏` como n-ario."""
    i, buf = 0, ""
    while i < len(s):
        if s[i] in "_^":
            base, buf = buf[-1:], buf[:-1]
            m_run(padre, buf)
            buf = ""
            sub = sup = None
            while i < len(s) and s[i] in "_^":
                marca = s[i]
                texto, i = grupo(s, i + 1)
                if marca == "_":
                    sub = texto
                else:
                    sup = texto
            if base in "∑∏":
                nary = E.SubElement(padre, M + "nary")
                pr = E.SubElement(nary, M + "naryPr")
                E.SubElement(pr, M + "chr").set(M + "val", base)
                E.SubElement(pr, M + "limLoc").set(M + "val", "undOvr")
                if sup is None:
                    E.SubElement(pr, M + "supHide").set(M + "val", "1")
                contenedor(nary, "sub", sub or "")
                contenedor(nary, "sup", sup or "")
                resto = E.SubElement(nary, M + "e")
                llenar(resto, s[i:])
                return
            nombre = "sSubSup" if sub is not None and sup is not None else ("sSub" if sub is not None else "sSup")
            n = E.SubElement(padre, M + nombre)
            contenedor(n, "e", base)
            if sub is not None:
                contenedor(n, "sub", sub)
            if sup is not None:
                contenedor(n, "sup", sup)
        else:
            buf += s[i]
            i += 1
    m_run(padre, buf)


def en_linea(p, texto):
    """Admite **negrita**, $matemáticas$ y `código`."""
    for parte in re.split(r"(\*\*.+?\*\*|\$[^$]+\$|`[^`]+`)", texto):
        if not parte:
            continue
        if parte.startswith("`"):
            corrida(p, parte[1:-1], mono=True)
        elif parte.startswith("**"):
            for sub in re.split(r"(\$[^$]+\$)", parte[2:-2]):
                if sub.startswith("$"):
                    llenar(E.SubElement(p, M + "oMath"), sub[1:-1])
                elif sub:
                    corrida(p, sub, negrita=True)
        elif parte.startswith("$"):
            llenar(E.SubElement(p, M + "oMath"), parte[1:-1])
        else:
            corrida(p, parte)


def espaciado(ppr, **kw):
    ele(W + "spacing", ppr, line=276, lineRule="auto", **kw)


marcador = [100]


def titulo(nivel, texto):
    p = ele(W + "p")
    ppr = ele(W + "pPr", p)
    ele(W + "pStyle", ppr, val=f"Heading{nivel}")
    ele(W + "keepNext", ppr, val="1")
    ele(W + "keepLines", ppr, val="1")
    if nivel == 1:
        espaciado(ppr, after=80)
    ele(W + "outlineLvl", ppr, val=nivel - 1)
    nombre = f"_sec{marcador[0]}"
    ele(W + "bookmarkStart", p, id=marcador[0], name=nombre)
    ele(W + "bookmarkEnd", p, id=marcador[0])
    marcador[0] += 1
    corrida(p, texto, negrita=nivel == 2)
    return p, nombre


def parrafo(texto):
    p = ele(W + "p")
    espaciado(ele(W + "pPr", p), before=120, after=120)
    en_linea(p, texto)
    return p


def vineta(texto, num_id):
    p = ele(W + "p")
    ppr = ele(W + "pPr", p)
    num = ele(W + "numPr", ppr)
    ele(W + "ilvl", num, val=0)
    ele(W + "numId", num, val=num_id)
    espaciado(ppr, before=60, after=60)
    ele(W + "ind", ppr, left=720, hanging=360)
    en_linea(p, texto)
    return p


def ecuacion(texto):
    p = ele(W + "p")
    ppr = ele(W + "pPr", p)
    espaciado(ppr, before=120, after=120)
    ele(W + "jc", ppr, val="center")
    llenar(E.SubElement(p, M + "oMath"), texto)
    return p


def pendiente(texto):
    p = ele(W + "p")
    espaciado(ele(W + "pPr", p), before=120, after=120)
    corrida(p, texto, negrita=True, resaltar=True)
    return p


IMAGENES = []


def imagen(nombre, ancho_px, alto_px):
    rid = f"rIdImg{len(IMAGENES) + 1}"
    IMAGENES.append((rid, nombre))
    cx = 5486400
    cy = cx * alto_px // ancho_px
    n = 100 + len(IMAGENES)
    p = ele(W + "p")
    ppr = ele(W + "pPr", p)
    espaciado(ppr, before=120, after=60)
    ele(W + "jc", ppr, val="center")
    r = ele(W + "r", p)
    r.append(E.fromstring(
        '<w:drawing xmlns:w="%s" '
        'xmlns:wp="http://schemas.openxmlformats.org/drawingml/2006/wordprocessingDrawing" '
        'xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main" '
        'xmlns:pic="http://schemas.openxmlformats.org/drawingml/2006/picture" '
        'xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships">'
        '<wp:inline distT="0" distB="0" distL="0" distR="0"><wp:extent cx="%d" cy="%d"/>'
        '<wp:effectExtent l="0" t="0" r="0" b="0"/><wp:docPr id="%d" name="%s"/>'
        '<wp:cNvGraphicFramePr><a:graphicFrameLocks noChangeAspect="1"/></wp:cNvGraphicFramePr>'
        '<a:graphic><a:graphicData uri="http://schemas.openxmlformats.org/drawingml/2006/picture">'
        '<pic:pic><pic:nvPicPr><pic:cNvPr id="%d" name="%s"/><pic:cNvPicPr/></pic:nvPicPr>'
        '<pic:blipFill><a:blip r:embed="%s"/><a:stretch><a:fillRect/></a:stretch></pic:blipFill>'
        '<pic:spPr><a:xfrm><a:off x="0" y="0"/><a:ext cx="%d" cy="%d"/></a:xfrm>'
        '<a:prstGeom prst="rect"><a:avLst/></a:prstGeom></pic:spPr></pic:pic>'
        '</a:graphicData></a:graphic></wp:inline></w:drawing>'
        % (WNS, cx, cy, n, nombre, n, nombre, rid, cx, cy)))
    return p


def leyenda(texto):
    p = ele(W + "p")
    ppr = ele(W + "pPr", p)
    espaciado(ppr, before=0, after=160)
    ele(W + "jc", ppr, val="center")
    r = ele(W + "r", p)
    pr = ele(W + "rPr", r)
    ele(W + "i", pr, val="1")
    ele(W + "sz", pr, val="18")
    t = ele(W + "t", r)
    t.text = texto
    t.set(XML, "preserve")
    return p


def tabla(filas, anchos=(2500, 1600, 1400, 3525), borde="000000", fondo_encabezado=None, tamano=None):
    """Tabla de ancho fijo. La primera fila es el encabezado, en negrita."""
    tbl = ele(W + "tbl")
    pr = ele(W + "tblPr", tbl)
    ele(W + "tblW", pr, w=sum(anchos), type="dxa")
    bordes = ele(W + "tblBorders", pr)
    for lado in ("top", "left", "bottom", "right", "insideH", "insideV"):
        ele(W + lado, bordes, val="single", sz=8, space=0, color=borde)
    ele(W + "tblLayout", pr, type="fixed")
    if tamano is not None:
        margenes = ele(W + "tblCellMar", pr)
        for lado, w in (("top", 40), ("left", 100), ("bottom", 40), ("right", 100)):
            ele(W + lado, margenes, w=w, type="dxa")
    grid = ele(W + "tblGrid", tbl)
    for a in anchos:
        ele(W + "gridCol", grid, w=a)
    for f, fila in enumerate(filas):
        tr = ele(W + "tr", tbl)
        if fondo_encabezado:
            trpr = ele(W + "trPr", tr)
            ele(W + "cantSplit", trpr, val="1")  # una fila no se parte entre páginas
            if f == 0:
                ele(W + "tblHeader", trpr, val="1")
        for a, celda in zip(anchos, fila):
            tc = ele(W + "tc", tr)
            tcpr = ele(W + "tcPr", tc)
            ele(W + "tcW", tcpr, w=a, type="dxa")
            if f == 0 and fondo_encabezado:
                ele(W + "shd", tcpr, val="clear", color="auto", fill=fondo_encabezado)
            p = ele(W + "p", tc)
            if tamano is None:
                corrida(p, celda, negrita=f == 0, resaltar=celda == "[pendiente]")
            else:
                espaciado(ele(W + "pPr", p), before=20, after=20)
                if f == 0:
                    corrida(p, celda, negrita=True)
                else:
                    en_linea(p, celda)
                for r in p.iter(W + "r"):
                    rpr = r.find(W + "rPr")
                    if rpr is None:
                        rpr = E.Element(W + "rPr")
                        r.insert(0, rpr)
                    if rpr.find(W + "sz") is not None:
                        continue
                    ele(W + "sz", rpr, val=tamano)
                    ele(W + "szCs", rpr, val=tamano)
    return tbl


def indice(entradas, fldprop):
    salida = []
    for pos, (nivel, texto, nombre) in enumerate(entradas):
        p = ele(W + "p")
        ppr = ele(W + "pPr", p)
        espaciado(ppr, before=40)
        if nivel == 2:
            ele(W + "ind", ppr, left=360)
        if pos == 0:
            r = ele(W + "r", p)
            ele(W + "fldChar", r, fldCharType="begin", dirty="true")
            r = ele(W + "r", p)
            it = ele(W + "instrText", r)
            # \o usa el nivel de esquema: funciona aunque Word traduzca "Heading 1" a "Título 1".
            it.text = ' TOC \\o "1-2" \\h \\u \\z '
            it.set(XML, "preserve")
            r = ele(W + "r", p)
            ele(W + "fldChar", r, fldCharType="separate")
        h = ele(W + "hyperlink", p, anchor=nombre)
        corrida(h, texto, negrita=nivel == 1)
        if pos == len(entradas) - 1:
            r = ele(W + "r", p)
            ele(W + "fldChar", r, fldCharType="end")
        salida.append(p)
    return salida


def es_vineta(numbering, num_id):
    r = E.fromstring(numbering)
    abstracto = r.xpath(f"w:num[@w:numId='{num_id}']/w:abstractNumId/@w:val", namespaces={"w": WNS})[0]
    return r.xpath(f"w:abstractNum[@w:abstractNumId='{abstracto}']/w:lvl[@w:ilvl='0']/w:numFmt/@w:val",
                   namespaces={"w": WNS})[0]


def codigo(texto, borde="BFBFBF", fondo="F2F2F2"):
    """Bloque de código: un párrafo por línea, con el mismo borde para que Word los una."""
    lineas = texto.strip("\n").split("\n")
    salida = []
    for i, linea in enumerate(lineas):
        p = ele(W + "p")
        ppr = ele(W + "pPr", p)
        bordes = ele(W + "pBdr", ppr)
        for lado in ("top", "left", "bottom", "right"):
            ele(W + lado, bordes, val="single", sz=4, space=4, color=borde)
        ele(W + "shd", ppr, val="clear", color="auto", fill=fondo)
        ele(W + "spacing", ppr, before=120 if i == 0 else 0, after=120 if i == len(lineas) - 1 else 0,
            line=240, lineRule="auto")
        ele(W + "ind", ppr, left=144, right=144)
        r = ele(W + "r", p)
        pr = ele(W + "rPr", r)
        ele(W + "rFonts", pr, ascii=MONO, hAnsi=MONO, cs=MONO)
        ele(W + "sz", pr, val=18)
        ele(W + "szCs", pr, val=18)
        t = ele(W + "t", r)
        t.text = linea or " "
        t.set(XML, "preserve")
        salida.append(p)
    return salida


def nota(texto, color="808080", fondo="F7F7F7"):
    """Párrafo destacado con una barra gris a la izquierda."""
    p = ele(W + "p")
    ppr = ele(W + "pPr", p)
    bordes = ele(W + "pBdr", ppr)
    ele(W + "left", bordes, val="single", sz=18, space=8, color=color)
    ele(W + "shd", ppr, val="clear", color="auto", fill=fondo)
    espaciado(ppr, before=160, after=160)
    ele(W + "ind", ppr, left=200, right=144)
    en_linea(p, texto)
    return p


def numerado(texto, num_id):
    """Elemento de una lista numerada; `num_id` debe apuntar a una lista decimal."""
    return vineta(texto, num_id)
