#!/usr/bin/env python3
"""Opens DOCX files in the installed EuroOffice Writer and records how it laid
them out: every paragraph's page and vertical extent, every drawing's place,
size, wrapping, and (SmartArt) the shapes it contains. On the SmartArt
documents it also presses Enter around the SmartArt and resizes it, and
records what moved. Writes OUT/layout.json, OUT/layout.md and screenshots.

  probe.py OUT_DIR DOCX...

Needs the regression helpers of desktop-apps (tools/sos-apps/regression) on
PYTHONPATH, an X display and a test user, like regression.yml.
"""
import json
import os
import sys
import time

import cdp
import sos

DUMP = r"""
var ld = api.WordControl.m_oLogicDocument;
function mm(v){return typeof v==='number'?Math.round(v*10)/10:v;}
function tr(o){var t=o&&o.transform;return t?[mm(t.tx),mm(t.ty)]:null;}
var out={pages: ld.Pages.length, paras:[], drawings:[], modified: !!(api.isDocumentModified&&api.isDocumentModified())};
for (var i=0;i<ld.Content.length;i++){
  var el=ld.Content[i]; var r={i:i, text:(el.GetText?el.GetText():'').slice(0,24)};
  r.pages=[];
  for (var k=0;el.Pages&&k<el.Pages.length;k++){var b=el.Pages[k].Bounds;
    r.pages.push({page:el.GetAbsolutePage(k), top:mm(b.Top), bottom:mm(b.Bottom)});}
  r.lines=el.Lines?el.Lines.length:null;
  r.textLines=[];
  for (var k=0;el.Pages&&k<el.Pages.length;k++){var pg=el.Pages[k];
    for (var l=pg.StartLine;l<=pg.EndLine&&l<el.Lines.length;l++){var ln=el.Lines[l];
      var rs=ln.Ranges.filter(function(q){return q.XEndVisible>q.XVisible+0.5;}).map(function(q){return [mm(q.XVisible),mm(q.XEndVisible)];});
      if(rs.length) r.textLines.push({page:el.GetAbsolutePage(k), top:mm(pg.Y+ln.Top), bottom:mm(pg.Y+ln.Bottom), ranges:rs});}}
  out.paras.push(r);
}
var dr=ld.GetAllDrawingObjects([]);
for (var j=0;j<dr.length;j++){
  var d=dr[j], g=d.GraphicObj, p=d.GetParagraph&&d.GetParagraph();
  var o={inline:d.IsInline(), wrap:d.wrappingType, behind:d.behindDoc, page:d.PageNum,
         para: p?ld.Content.indexOf(p):null, X:mm(d.X), Y:mm(d.Y), W:mm(d.Extent.W), H:mm(d.Extent.H),
         type:g&&g.getObjectType&&g.getObjectType(), name:g&&g.getName&&g.getName()};
  if (g){ o.pos=tr(g); o.ext=[mm(g.extX),mm(g.extY)];
    if (g.spPr&&g.spPr.xfrm){var x=g.spPr.xfrm;o.xfrm=[mm(x.offX),mm(x.offY),mm(x.extX),mm(x.extY)];}
    if (g.getDrawing){ var dd=g.getDrawing(); o.hasDrawingPart=!!dd;
      if (dd){ o.drawingPos=tr(dd); o.drawingExt=[mm(dd.extX),mm(dd.extY)];
        o.shapes=dd.spTree.map(function(s){var c=s.getDocContent&&s.getDocContent(); var sz=null, ln=0;
          if(c){c.SetApplyToAll(true); sz=c.GetCalculatedTextPr().FontSize; c.SetApplyToAll(false);
            c.Content.forEach(function(p){ln+=p.Lines?p.Lines.length:0;});}
          return {pos:tr(s), ext:[mm(s.extX),mm(s.extY)], text:(c?c.GetText():'').slice(0,12), fontSize:sz, lines:ln};});
        var b={l:1e9,t:1e9,r:-1e9,b:-1e9};
        dd.spTree.forEach(function(s){var t=s.transform; if(!t)return; b.l=Math.min(b.l,t.tx);b.t=Math.min(b.t,t.ty);
          b.r=Math.max(b.r,t.tx+s.extX);b.b=Math.max(b.b,t.ty+s.extY);});
        o.shapesBox=[mm(b.l),mm(b.t),mm(b.r),mm(b.b)];
      }
      o.canGenerate=g.isCanGenerateSmartArt?g.isCanGenerateSmartArt():null;
    }
  }
  out.drawings.push(o);
}
return JSON.stringify(out);
"""

PLACE = r"""
var ld = api.WordControl.m_oLogicDocument; var i=%d, end=%s;
ld.RemoveSelection();
var p=ld.Content[i];
if (end) p.MoveCursorToEndPos(false); else p.MoveCursorToStartPos(false);
ld.CurPos.ContentPos=i; ld.Selection.Use=false;
ld.UpdateSelection(); ld.UpdateInterface(); ld.UpdateRulers();
try { ld.private_UpdateCursorXY(true, true, true); } catch (e) {}
var a=document.getElementById('area_id'); if(a) a.focus();
return true;
"""

RESIZE = r"""
var ld = api.WordControl.m_oLogicDocument; var dr=ld.GetAllDrawingObjects([]); var d=dr[%d];
ld.RemoveSelection(); ld.SelectDrawings([d], d.GetParagraph().GetParent());
var pr=new Asc.asc_CImgProperty(); pr.put_Width(%f); pr.put_Height(%f);
api.ImgApply(pr); return true;
"""


def overlaps(lay):
    """text that is drawn on top of a drawing: a line range of a paragraph
    (other than an inline drawing's own paragraph) that crosses the box of
    the drawing's shapes on the same page"""
    found = []
    for k, d in enumerate(lay['drawings']):
        box = d.get('shapesBox') or (d.get('pos') and [d['pos'][0], d['pos'][1], d['pos'][0] + d['ext'][0], d['pos'][1] + d['ext'][1]])
        if not box or d.get('behind'):
            continue
        for p in lay['paras']:
            if p['i'] == d['para'] and d['inline']:
                continue
            for ln in p.get('textLines', []):
                if ln['page'] != d['page'] or ln['top'] >= box[3] - 0.5 or ln['bottom'] <= box[1] + 0.5:
                    continue
                for x0, x1 in ln['ranges']:
                    if x0 < box[2] - 0.5 and x1 > box[0] + 0.5:
                        found.append({'drawing': k, 'para': p['i'], 'line': [ln['top'], ln['bottom'], x0, x1], 'box': box})
    return found


def broken_words(lay):
    """SmartArt blocks holding one word that is laid out on more than one line"""
    out = []
    for k, d in enumerate(lay.get('drawings', [])):
        for j, sh in enumerate(d.get('shapes') or []):
            words = sh['text'].split()
            if len(words) == 1 and sh.get('lines', 0) > 1:
                out.append({'drawing': k, 'shape': j, 'text': words[0], 'lines': sh['lines'], 'fontSize': sh.get('fontSize')})
    return out


def shot(ed, name):
    os.makedirs(os.path.join(sos.OUT, 'shots'), exist_ok=True)
    ed.page.screenshot(os.path.join(sos.OUT, 'shots', name + '.png'))


def dump(ed):
    s = ed.js(DUMP)
    return json.loads(s) if s else None


def errors(ed):
    ed.page.pump(0.5)
    out = []
    for e in ed.page.events:
        if e.get('method') == 'Runtime.exceptionThrown':
            d = e['params']['exceptionDetails']
            out.append((d.get('exception', {}).get('description') or d.get('text', ''))[:400])
        elif e.get('method') == 'Runtime.consoleAPICalled' and e['params'].get('type') == 'error':
            out.append(' '.join(str(a.get('value', a.get('description', ''))) for a in e['params'].get('args', []))[:400])
    return out


def undo(ed):
    ed.js("api.Undo(); return true;")
    time.sleep(1.5)


def press_enter(ed, para, end=False):
    ed.js(PLACE % (para, 'true' if end else 'false'))
    time.sleep(0.5)
    ed.page.key('Enter', 'Enter', 13, text='\r')
    time.sleep(2)


def main(out, files):
    sos.OUT = out
    if hasattr(sos, 'winplat'):
        sos.winplat.OUT = out
    os.makedirs(out, exist_ok=True)
    sos.enable_devtools()
    results = []
    for f in files:
        name = os.path.splitext(os.path.basename(f))[0]
        r = {'file': os.path.basename(f)}
        results.append(r)
        sos.kill_all()
        before = sos.doc_ids()
        sos.launch('writer', f)
        t = sos.wait_target(sos.is_doc, 150, exclude=before)
        if not t:
            r['error'] = 'no editor'
            continue
        ed = sos.Editor(t, 'writer')
        r['ready'] = ed.wait_ready()
        time.sleep(3)
        r['open'] = lay = dump(ed)
        r['overlaps'] = overlaps(lay) if lay else None
        if lay and lay['drawings']:
            # bring the first drawing into view (cursor at the end of its paragraph)
            ed.js(PLACE % (lay['drawings'][0]['para'], 'true'))
            time.sleep(1)
        shot(ed, name + '-0-open')
        if lay and lay['drawings'] and name.startswith(('01', '04', '05')):
            dp = lay['drawings'][0]['para']
            steps = {}
            # Enter at the end of the paragraph above the drawing
            press_enter(ed, dp - 1, end=True)
            steps['enter_above'] = dump(ed)
            shot(ed, name + '-1-enter-above')
            undo(ed)
            # Enter right before the drawing (start of its paragraph)
            press_enter(ed, dp, end=False)
            steps['enter_before'] = dump(ed)
            shot(ed, name + '-2-enter-before')
            undo(ed)
            # Enter at the start of the paragraph after the drawing
            press_enter(ed, dp + 1, end=False)
            steps['enter_after'] = dump(ed)
            shot(ed, name + '-3-enter-after')
            undo(ed)
            # resize the drawing to 2/3 of its size
            d0 = lay['drawings'][0]
            try:
                ed.js_strict(RESIZE % (0, d0['W'] * 2 / 3, d0['H'] * 2 / 3))
                time.sleep(2)
                steps['resize'] = dump(ed)
                shot(ed, name + '-4-resize')
                undo(ed)
            except Exception as e:
                steps['resize'] = {'error': str(e)}
            steps['after_undo'] = dump(ed)
            r['steps'] = steps
            if name.startswith('01'):
                # save as DOCX the way a user does, reopen, compare
                m0 = os.path.getmtime(f)
                # one character in the empty last paragraph, so there is a change to save
                ed.js(PLACE % (len(lay['paras']) - 1, 'true'))
                time.sleep(0.5)
                ed.page.type_text('x')
                time.sleep(1)
                ed.page.shortcut('S')
                saved = sos.wait_file(f, since=m0 + 0.001, secs=60)
                r['saved'] = bool(saved)
                r['errors_before_reopen'] = errors(ed)
                ed.close()
                sos.kill_all()
                before = sos.doc_ids()
                sos.launch('writer', f)
                t = sos.wait_target(sos.is_doc, 150, exclude=before)
                if t:
                    ed = sos.Editor(t, 'writer')
                    r['reopen_ready'] = ed.wait_ready()
                    time.sleep(3)
                    r['reopen'] = dump(ed)
                    r['reopen_overlaps'] = overlaps(r['reopen']) if r['reopen'] else None
                    shot(ed, name + '-5-reopened')
        r['errors'] = errors(ed)
        try:
            ed.js("api.asc_setDocumentModified && api.asc_setDocumentModified(false); return 1")
        except Exception:
            pass
        ed.close()
        sos.kill_all()
    problems = []
    for r in results:
        if not r.get('ready'):
            problems.append('%s: did not open' % r['file'])
        if r.get('errors'):
            problems.append('%s: JavaScript errors %s' % (r['file'], r['errors'][:3]))
        if r.get('overlaps'):
            problems.append('%s: text over a drawing %s' % (r['file'], r['overlaps'][:3]))
        if r.get('open') and broken_words(r['open']):
            problems.append('%s: words broken inside SmartArt blocks %s' % (r['file'], broken_words(r['open'])))
        if r.get('reopen_overlaps'):
            problems.append('%s: text over a drawing after save + reopen' % r['file'])
        for k, st in (r.get('steps') or {}).items():
            if st and 'error' not in st:
                if overlaps(st):
                    problems.append('%s %s: text over a drawing' % (r['file'], k))
                bw = broken_words(st)
                if bw:
                    problems.append('%s %s: words broken inside SmartArt blocks %s' % (r['file'], k, bw))
            elif st:
                problems.append('%s %s: %s' % (r['file'], k, st['error']))
    with open(os.path.join(out, 'layout.json'), 'w') as fh:
        json.dump(results, fh, indent=1)
    with open(os.path.join(out, 'layout.md'), 'w') as fh:
        fh.write('## DOCX layout probe\n\n')
        fh.write('**%s**\n\n' % ('PASS: no problems found' if not problems else 'FAIL'))
        for pr in problems:
            fh.write('- %s\n' % pr)
        fh.write('\n')
        for r in results:
            lay = r.get('open') or {}
            fh.write('### %s\n\n' % r['file'])
            fh.write('- loaded: %s, pages: %s, JS errors: %d\n' % (r.get('ready'), lay.get('pages'), len(r.get('errors') or [])))
            for e in (r.get('errors') or [])[:5]:
                fh.write('  - `%s`\n' % e.replace('\n', ' ')[:300])
            for p in lay.get('paras', []):
                fh.write('- para %d `%s` %s lines=%s\n' % (p['i'], p['text'], p['pages'], p['lines']))
            for d in lay.get('drawings', []):
                fh.write('- drawing: %s\n' % json.dumps({k: d.get(k) for k in ('name', 'inline', 'wrap', 'para', 'page', 'X', 'Y', 'W', 'H', 'pos', 'ext', 'xfrm', 'hasDrawingPart', 'drawingPos', 'drawingExt', 'shapesBox', 'canGenerate')}))
            fh.write('- overlaps: %s\n' % json.dumps(r.get('overlaps')))
            if 'saved' in r:
                ro = r.get('reopen') or {}
                fh.write('- saved with Ctrl+S: %s; reopened: %s, pages %s; drawings %s; overlaps %s\n' % (
                    r['saved'], r.get('reopen_ready'), ro.get('pages'),
                    json.dumps([{k: d.get(k) for k in ('inline', 'para', 'pos', 'ext', 'shapesBox')} for d in ro.get('drawings', [])]),
                    json.dumps(r.get('reopen_overlaps'))))
            for k, s in (r.get('steps') or {}).items():
                if not s or 'error' in s:
                    fh.write('- %s: %s\n' % (k, s))
                    continue
                d = s['drawings'][0] if s.get('drawings') else {}
                fh.write('- %s: paras %s; drawing para %s pos %s ext %s shapesBox %s; overlaps %s; block fonts %s lines %s\n' % (
                    k, [(p['i'], p['pages'][0]['top'] if p['pages'] else None) for p in s['paras']],
                    d.get('para'), d.get('pos'), d.get('ext'), d.get('shapesBox'), len(overlaps(s)),
                    [x.get('fontSize') for x in d.get('shapes') or []], [x.get('lines') for x in d.get('shapes') or []]))
            fh.write('\n')
    print(open(os.path.join(out, 'layout.md')).read())
    return 1 if problems else 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1], sys.argv[2:]))
