"""Animations vectorielles (SVG) pour la maquette Brasseurs de la Jonte.

Injecte, de façon idempotente, dans demos/brasseurs-de-la-jonte/site/index.html :
  1. Héros : vautours fauves qui planent + courants de la Jonte (boucle CSS)
  2. Pictos animés devant chaque chapitre (I → IX)
  3. Roue du moulin qui tourne sur la photo du Moulin
  4. Ligne de crête des Causses qui se dessine au scroll (avant la gamme), vautour en thermique
Puis régénère maquette/index.html (page autonome servie par Vercel).

Tout est aria-hidden, sans interaction, et coupé si prefers-reduced-motion: reduce.
Usage : python3 scripts/vfx.py
"""
from pathlib import Path
import math
import re
import shutil

ROOT = Path(__file__).resolve().parent.parent
SITE = ROOT / "demos/brasseurs-de-la-jonte/site"
SRC = SITE / "index.html"
OUT = ROOT / "maquette"
MARK = "<!--vfx-->"

# --------------------------------------------------------------------------- CSS
CSS = """
/* ===== Animations vectorielles (vfx) ===== */
.vfx-hero{position:absolute;inset:0;z-index:2;width:100%;height:100%;pointer-events:none}
.vfx-hero .bird{color:#F3E7C9;opacity:.42;animation:vf-glide var(--d) linear var(--dl) infinite both}
.vfx-hero .bird path{transform-box:fill-box;transform-origin:50% 50%;animation:vf-flap 4.2s ease-in-out var(--dl) infinite}
.vfx-hero .cur{fill:none;stroke:#78AAB6;stroke-width:1.4;stroke-linecap:round;stroke-dasharray:60 72;opacity:.5;animation:vf-flow var(--d,9s) linear infinite}
@keyframes vf-glide{0%{transform:translate(-180px,var(--y))}50%{transform:translate(720px,calc(var(--y) - 30px))}100%{transform:translate(1640px,calc(var(--y) + 10px))}}
@keyframes vf-flap{0%,72%,100%{transform:scaleY(1)}80%{transform:scaleY(.5)}88%{transform:scaleY(1.08)}}
@keyframes vf-flow{to{stroke-dashoffset:-264}}

.glyph{width:26px;height:26px;flex:none;fill:none;stroke:currentColor;stroke-width:1.6;stroke-linecap:round;stroke-linejoin:round;overflow:visible}
.glyph *{transform-box:view-box}
.g-sway{transform-origin:16px 3px;animation:vf-sway 3.6s ease-in-out infinite}
.g-flap{transform-origin:16px 16px;animation:vf-wing 2.4s ease-in-out infinite}
.g-bub{animation:vf-bub 2.4s ease-in infinite}.g-bub:nth-of-type(2){animation-delay:.8s}.g-bub:nth-of-type(3){animation-delay:1.6s}
.g-turn{transform-origin:16px 16px;animation:vf-turn 5s ease-in-out infinite}
.g-cl{transform-origin:9px 26px;animation:vf-cheerL 3s ease-in-out infinite}.g-cr{transform-origin:23px 26px;animation:vf-cheerR 3s ease-in-out infinite}
.g-spark{animation:vf-spark 3s ease-in-out infinite}
.g-spin{transform-origin:16px 16px;animation:vf-spin 9s linear infinite}
.g-drop{animation:vf-drop 1.8s ease-in infinite}
.g-bounce{transform-origin:16px 28px;animation:vf-bounce 2.2s cubic-bezier(.3,0,.3,1) infinite}
.g-shadow{transform-origin:16px 29.5px;animation:vf-shadow 2.2s cubic-bezier(.3,0,.3,1) infinite}
.g-float{transform-origin:16px 16px;animation:vf-float 4s ease-in-out infinite}
@keyframes vf-sway{0%,100%{transform:rotate(-7deg)}50%{transform:rotate(7deg)}}
@keyframes vf-wing{0%,100%{transform:translateY(0) scaleY(1)}50%{transform:translateY(-1.5px) scaleY(.6)}}
@keyframes vf-bub{0%{transform:translateY(0);opacity:0}15%{opacity:1}100%{transform:translateY(-12px);opacity:0}}
@keyframes vf-turn{0%,40%{transform:rotate(0)}55%,90%{transform:rotate(180deg)}100%{transform:rotate(360deg)}}
@keyframes vf-cheerL{0%,55%,100%{transform:rotate(0)}70%,80%{transform:rotate(14deg)}}
@keyframes vf-cheerR{0%,55%,100%{transform:rotate(0)}70%,80%{transform:rotate(-14deg)}}
@keyframes vf-spark{0%,68%,100%{opacity:0}76%,84%{opacity:1}}
@keyframes vf-spin{to{transform:rotate(360deg)}}
@keyframes vf-drop{0%,30%{transform:translateY(0);opacity:0}40%{opacity:1}100%{transform:translateY(9px);opacity:0}}
@keyframes vf-bounce{0%,100%{transform:translateY(0)}45%{transform:translateY(-5px)}}
@keyframes vf-shadow{0%,100%{transform:scaleX(1);opacity:.9}45%{transform:scaleX(.6);opacity:.4}}
@keyframes vf-float{0%,100%{transform:translate(0,0) rotate(0)}50%{transform:translate(2px,-3px) rotate(-6deg)}}

.mill{position:absolute;right:18px;top:18px;z-index:2;width:clamp(96px,10vw,132px);aspect-ratio:1;border-radius:50%;background:var(--paper);color:var(--jonte);box-shadow:0 10px 30px rgba(20,38,45,.2);overflow:hidden;pointer-events:none}
.mill svg{width:100%;height:100%;display:block;fill:none;stroke:currentColor;stroke-width:2;stroke-linecap:round;stroke-linejoin:round}
.mill .spin{transform-box:view-box;transform-origin:60px 54px;animation:vf-spin 16s linear infinite}
.mill .paddle{fill:var(--hop);stroke:none}
.mill .water{stroke:var(--river);stroke-width:2.4;stroke-dasharray:14 10;animation:vf-flow 3s linear infinite}
.mill .water + .water{animation-duration:4.4s;opacity:.6}
.mill .splash{fill:var(--river);stroke:none;animation:vf-drop 1.6s ease-in infinite}
.mill .splash:nth-of-type(2){animation-delay:.55s}.mill .splash:nth-of-type(3){animation-delay:1.1s}

/* Paysage des Causses : 3 plans en profondeur, gorge de la Jonte, moulin, vautours en orbe */
.ridge{position:relative;width:100%;height:clamp(112px,13.8vw,220px);margin:0 0 clamp(36px,5vw,72px);color:var(--jonte);pointer-events:none}
.ridge svg{position:absolute;inset:0;width:100%;height:100%;overflow:hidden}
.rg-l2 .rg-fill{fill:var(--paper-2)}
.rg-l3 .rg-fill{fill:var(--paper)}
.rg-line{fill:none;stroke:currentColor;stroke-linecap:round;stroke-linejoin:round}
.rg-l1 .rg-line{stroke-width:1;opacity:.3}
.rg-l2 .rg-line{stroke-width:1.1;opacity:.5}
.rg-l3 .rg-line{stroke-width:1.7}
.rg-strata path{fill:none;stroke:currentColor;stroke-width:.9;stroke-linecap:round;opacity:.28;stroke-dasharray:70 12 26 9 110 14}
.rg-river{fill:var(--river);opacity:.3}
.rg-flow{fill:none;stroke:var(--river);stroke-width:1.4;stroke-linecap:round;stroke-dasharray:16 22;animation:vf-flow 4.5s linear infinite}
.rg-flow + .rg-flow{animation-duration:6.5s;opacity:.6}
.rg-mist{fill:#fff;opacity:.6;animation:rg-mist 14s ease-in-out infinite alternate}
.rg-mist + .rg-mist{opacity:.4;animation-duration:19s;animation-delay:-6s}
.rg-mill{fill:var(--paper);stroke:currentColor;stroke-width:1.3;stroke-linejoin:round}
.rg-wheel{fill:none;stroke:currentColor;stroke-width:1.2;transform-origin:676px 216px;animation:vf-spin 7s linear infinite}
.rg-bird{fill:var(--ink-2);opacity:.85}
.rg-ox{animation:rg-ox var(--t) ease-in-out var(--dl) infinite alternate}
.rg-oy{animation:rg-oy var(--t) ease-in-out calc(var(--dl) - var(--t) / 2) infinite alternate}
.rg-bank{animation:rg-bank var(--t) ease-in-out var(--dl) infinite alternate}
.rg-flap{transform-box:fill-box;transform-origin:50% 50%;animation:vf-flap 5.5s ease-in-out var(--dl) infinite}
@keyframes rg-ox{from{transform:translateX(calc(var(--rx) * -1))}to{transform:translateX(var(--rx))}}
@keyframes rg-oy{from{transform:translateY(calc(var(--ry) * -1))}to{transform:translateY(var(--ry))}}
@keyframes rg-bank{from{transform:rotate(-8deg)}to{transform:rotate(8deg)}}
@keyframes rg-mist{from{transform:translateX(-50px)}to{transform:translateX(50px)}}

@media (prefers-reduced-motion:reduce){.vfx-hero *,.glyph *,.mill *,.ridge *{animation:none!important}.vfx-hero .bird{transform:translate(900px,var(--y))}}
"""

# --------------------------------------------------------------------------- Héros
VULTURE = ("M-60,0 C-44,-11 -24,-9 -8,-3 L0,-6 L8,-3 C24,-9 44,-11 60,0 "
           "C52,1 46,3 40,2 L46,6 L36,4 L40,8 L28,4 C20,4 12,5 7,5 L3,11 L-3,11 L-7,5 "
           "C-12,5 -20,4 -28,4 L-40,8 L-36,4 L-46,6 L-40,2 C-46,3 -52,1 -60,0Z")


def bird(d, dl, y, s):
    return (f'<g class="bird" style="--d:{d}s;--dl:{dl}s;--y:{y}px">'
            f'<g transform="scale({s})"><path fill="currentColor" d="{VULTURE}"/></g></g>')


def currents():
    out = []
    for i, (y, amp, d) in enumerate([(690, 14, 9), (722, 10, 12), (752, 8, 15)]):
        pts = f"M-40,{y} C200,{y-amp} 440,{y+amp} 720,{y} S1240,{y-amp} 1480,{y}"
        out.append(f'<path class="cur" style="--d:{d}s" vector-effect="non-scaling-stroke" d="{pts}"/>')
    return "".join(out)


HERO = (MARK + '<svg class="vfx-hero" viewBox="0 0 1440 800" preserveAspectRatio="xMidYMid slice" '
        'aria-hidden="true" focusable="false">'
        + bird(46, -6, 78, .8) + bird(58, -30, 104, .6) + bird(70, -48, 62, .45)
        + currents() + "</svg>")

# --------------------------------------------------------------------------- Pictos de chapitre
def glyph(inner):
    return f'<svg class="glyph" viewBox="0 0 32 32" aria-hidden="true" focusable="false">{inner}</svg>'


GLYPHS = {
    "I.": glyph('<g class="g-sway"><path d="M16 3v4"/><path d="M16 7c-5 2-7 6-6 10 1 5 4 8 6 11 2-3 5-6 6-11 1-4-1-8-6-10z"/>'
                '<path d="M11 13c2 1 8 1 10 0M10.5 18.5c2 1.2 9 1.2 11 0M12 23.5c2 1 6 1 8 0"/></g>'),
    "II.": glyph('<g class="g-flap"><path d="M2 16c4-3 8-4 12-2l2 1 2-1c4-2 8-1 12 2-4-1-8 0-11 2l-3 3-3-3c-3-2-7-3-11-2z"/></g>'),
    "III.": glyph('<path d="M9 6h14l-2 22H11z"/><path d="M9.5 11h13"/>'
                  '<circle class="g-bub" cx="14" cy="24" r="1"/><circle class="g-bub" cx="18" cy="25" r=".9"/>'
                  '<circle class="g-bub" cx="16" cy="23" r=".8"/>'),
    "IV.": glyph('<g class="g-turn"><path d="M9 4h14M9 28h14M10 4c0 7 12 8 12 12s-12 5-12 12M22 4c0 7-12 8-12 12s12 5 12 12"/>'
                 '<path d="M13 25h6"/></g>'),
    "V.": glyph('<g class="g-cl"><path d="M5 10h8l-1 16H6z"/></g><g class="g-cr"><path d="M19 10h8l-1 16h-6z"/></g>'
                '<path class="g-spark" d="M16 2v3M12.5 4l1.2 1.6M19.5 4l-1.2 1.6"/>'),
    "VI.": glyph('<g class="g-spin"><circle cx="16" cy="16" r="11"/><circle cx="16" cy="16" r="2.5"/>'
                 '<path d="M16 5v8.5M16 18.5V27M5 16h8.5M18.5 16H27M8.2 8.2l6 6M17.8 17.8l6 6M23.8 8.2l-6 6M14.2 17.8l-6 6"/></g>'),
    "VII.": glyph('<path d="M3 8h13a4 4 0 0 1 4 4v4h-4v-3H3z"/><path d="M8 8V4h5v4"/>'
                  '<path class="g-drop" fill="currentColor" d="M18 19c-1 1.4-1.6 2.3-1.6 3a1.6 1.6 0 0 0 3.2 0c0-.7-.6-1.6-1.6-3z"/>'),
    "VIII.": glyph('<ellipse class="g-shadow" cx="16" cy="29.5" rx="4" ry=".8"/>'
                   '<g class="g-bounce"><path d="M16 27s8-7.5 8-13.5a8 8 0 0 0-16 0C8 19.5 16 27 16 27z"/><circle cx="16" cy="13.5" r="3"/></g>'),
    "IX.": glyph('<g class="g-float"><path d="M3 15l26-10-8 22-5-9z"/><path d="M16 18L29 5"/></g>'),
}

# --------------------------------------------------------------------------- Roue du moulin
def mill():
    paddles = "".join(
        f'<rect class="paddle" x="56" y="8" width="8" height="11" rx="1.5" transform="rotate({k*30} 60 54)"/>'
        for k in range(12))
    spokes = "".join(
        f'<path d="M{60+8*math.cos(a):.1f} {54+8*math.sin(a):.1f}L{60+30*math.cos(a):.1f} {54+30*math.sin(a):.1f}"/>'
        for a in (i * math.pi / 4 for i in range(8)))
    return (MARK + '<div class="mill" aria-hidden="true"><svg viewBox="0 0 120 120" focusable="false">'
            f'<g class="spin"><circle cx="60" cy="54" r="34"/><circle cx="60" cy="54" r="30"/><circle cx="60" cy="54" r="8"/>{spokes}{paddles}</g>'
            '<circle class="splash" cx="30" cy="84" r="2"/><circle class="splash" cx="36" cy="88" r="1.6"/><circle class="splash" cx="26" cy="90" r="1.4"/>'
            '<path class="water" d="M-4 98c10-5 20 5 30 0s20-5 30 0 20 5 30 0 20-5 30 0 10 3 10 0"/>'
            '<path class="water" d="M-4 108c10-4 20 4 30 0s20-4 30 0 20 4 30 0 20-4 30 0 10 3 10 0"/>'
            '</svg></div>')


# --------------------------------------------------------------------------- Ligne de crête
def ridge():
    """Coupe de la vallée : Aigoual au loin, Causses Méjean / Noir, gorge de la Jonte avec le moulin."""
    far = ("M0,112 C140,92 260,84 380,92 C470,98 520,72 620,68 C720,64 790,88 880,84 "
           "C990,78 1060,56 1170,62 C1280,68 1360,86 1440,80")
    mid = ("M0,132 C200,128 380,126 560,122 C600,122 622,140 652,160 C684,178 756,178 788,160 "
           "C818,142 842,118 882,116 C1100,110 1300,112 1440,116")
    # plateaux tabulaires + falaises quasi verticales de la gorge
    front = ("M0,150 C40,148 60,146 90,146 L520,140 C540,140 548,146 552,156 L566,196 "
             "C572,212 584,222 606,226 L834,226 C856,222 868,212 874,196 L890,150 "
             "C894,140 904,136 920,136 L1440,142")
    strata = ["M24,172 C180,168 360,166 536,164", "M16,194 C200,190 380,188 550,186",
              "M30,216 C220,212 400,210 558,208", "M900,166 C1080,168 1260,170 1420,172",
              "M886,188 C1080,190 1260,192 1430,194", "M878,210 C1080,212 1260,214 1436,216"]

    def layer(cls, top):
        return (f'<g class="{cls}"><path class="rg-fill" d="{top} L1440,300 L0,300Z"/>'
                f'<path class="rg-line" d="{top}"/></g>')

    def bird(t, dl, rx, ry, cx, cy, s):
        return (f'<g class="rg-ox" style="--t:{t}s;--dl:{dl}s;--rx:{rx}px">'
                f'<g class="rg-oy" style="--t:{t}s;--dl:{dl}s;--ry:{ry}px">'
                f'<g transform="translate({cx} {cy})"><g class="rg-bank" style="--t:{t}s;--dl:{dl}s">'
                f'<g class="rg-flap" style="--dl:{dl}s"><path class="rg-bird" transform="scale({s})" d="{VULTURE}"/></g>'
                '</g></g></g></g>')

    spokes = "".join(f'<path d="M{676+8*math.cos(a):.1f} {216+8*math.sin(a):.1f}L{676-8*math.cos(a):.1f} {216-8*math.sin(a):.1f}"/>'
                     for a in (0, math.pi / 4, math.pi / 2, 3 * math.pi / 4))
    return (MARK + '<div class="ridge" aria-hidden="true">'
            '<svg viewBox="0 0 1440 240" preserveAspectRatio="xMidYMax slice" focusable="false">'
            '<defs><linearGradient id="rgHaze" x1="0" y1="0" x2="0" y2="1">'
            '<stop offset="0" style="stop-color:var(--paper-3)"/><stop offset=".7" style="stop-color:var(--paper)"/></linearGradient></defs>'
            + layer("rg-l1", far).replace('class="rg-fill"', 'class="rg-fill" fill="url(#rgHaze)"')
            + layer("rg-l2", mid)
            + '<ellipse class="rg-mist" cx="720" cy="198" rx="160" ry="7"/><ellipse class="rg-mist" cx="760" cy="184" rx="90" ry="5"/>'
            + layer("rg-l3", front).replace('</g>', '<g class="rg-strata">' + "".join(f'<path d="{d}"/>' for d in strata) + '</g></g>', 1)
            + '<path class="rg-river" d="M606,226 C650,222 690,229 730,224 C770,220 806,228 834,226 L834,240 L606,240Z"/>'
            '<path class="rg-flow" d="M614,231 C650,228 690,234 730,230 S800,228 828,232"/>'
            '<path class="rg-flow" d="M630,234 C670,232 700,236 740,233 S800,232 820,234"/>'
            '<g class="rg-millg"><path class="rg-mill" d="M640,225V204L654,194L668,204V225Z"/><path class="rg-mill" d="M651,225v-9h6v9"/>'
            f'<g class="rg-wheel"><circle cx="676" cy="216" r="8"/><circle cx="676" cy="216" r="2"/>{spokes}</g></g>'
            '<g class="rg-birds">'
            + bird(11, -2, 150, 22, 720, 72, .34) + bird(14, -9, 105, 16, 790, 50, .25) + bird(17, -5, 200, 28, 660, 96, .29)
            + '</g></svg></div>')


# --------------------------------------------------------------------------- JS (dessin au scroll)
JS_ANCHOR = "    // Pièce maîtresse : la vallée se dessine"
JS = """    // vfx : le paysage des Causses se construit au scroll, puis parallaxe douce entre les plans
    const rg = document.querySelector(".ridge");
    if (rg) {
      const q = s => rg.querySelectorAll(s);
      const lines = q(".rg-line");
      lines.forEach(p => { p.dataset.len = Math.ceil(p.getTotalLength()); });
      const tl = gsap.timeline({ scrollTrigger: { trigger: rg, start: "top 88%", once: true } });
      tl.from(q(".rg-fill"), { opacity: 0, y: 28, duration: 1.2, ease: "power3.out", stagger: .16 })
        .fromTo(lines, { strokeDasharray: (i, p) => p.dataset.len, strokeDashoffset: (i, p) => p.dataset.len },
          { strokeDashoffset: 0, duration: 1.8, ease: "power2.inOut", stagger: .15,
            onComplete() { lines.forEach(p => { p.style.strokeDasharray = ""; p.style.strokeDashoffset = ""; }); } }, .2)
        .from(q(".rg-strata path"), { opacity: 0, duration: .8, stagger: .05 }, 1.1)
        .from(q(".rg-river, .rg-flow, .rg-mist"), { opacity: 0, duration: 1 }, 1.2)
        .from(q(".rg-millg"), { opacity: 0, y: 10, duration: .7, ease: "back.out(2)" }, 1.5)
        .from(q(".rg-birds > g"), { opacity: 0, duration: 1.2, stagger: .3 }, 1.6);
      [[".rg-l1", 14], [".rg-l2", 7], [".rg-birds", 20]].forEach(([s, v]) =>
        gsap.fromTo(rg.querySelector(s), { y: -v }, { y: v, ease: "none",
          scrollTrigger: { trigger: rg, start: "top bottom", end: "bottom top", scrub: true } }));
    }
"""


def inject(html: str) -> str:
    if MARK in html:
        raise SystemExit("vfx déjà injecté dans site/index.html (rien à faire).")
    css_end = html.index("</style>")
    html = html[:css_end] + CSS + html[css_end:]
    # 1. héros
    html = re.sub(r'(<img src="img/hero-moulin\.jpg"[^>]*>)', lambda m: m.group(1) + "\n  " + HERO, html, count=1)
    # 2. pictos de chapitre
    for num, svg in GLYPHS.items():
        html = html.replace(f'<p class="chap lab"><i>{num}</i>', f'<p class="chap lab">{svg}<i>{num}</i>', 1)
    # 3. roue du moulin sur la photo
    html = re.sub(r'(<figure class="visit__photo fig">)', lambda m: m.group(1) + mill(), html, count=1)
    # 4. ligne de crête en tête de la gamme
    html = html.replace('<section class="sec" id="gamme" aria-labelledby="gamT">\n  <div class="wrap">',
                        '<section class="sec" id="gamme" aria-labelledby="gamT">\n  <div class="wrap">' + ridge(), 1)
    # JS
    if JS_ANCHOR not in html:
        raise SystemExit("ancre JS introuvable")
    html = html.replace(JS_ANCHOR, JS + JS_ANCHOR, 1)
    for check in ("vfx-hero", 'class="glyph"', 'class="mill"', 'class="ridge"', 'q(".rg-line")', "rg-birds"):
        assert check in html, check
    assert html.count('class="glyph"') == 9, html.count('class="glyph"')
    return html


def standalone(frag: str) -> str:
    i = frag.index('<a class="skip"')
    return ('<!doctype html>\n<html lang="fr">\n<head>\n<meta charset="utf-8">\n'
            + frag[:i] + "</head>\n<body>\n" + frag[i:] + "\n</body>\n</html>\n")


def main():
    html = SRC.read_text(encoding="utf-8")
    if MARK not in html:
        html = inject(html)
        SRC.write_text(html, encoding="utf-8")
        print("site/index.html : animations injectées")
    OUT.mkdir(exist_ok=True)
    (OUT / "index.html").write_text(standalone(html), encoding="utf-8")
    shutil.copytree(SITE / "img", OUT / "img", dirs_exist_ok=True)
    print("maquette/index.html régénéré")


if __name__ == "__main__":
    main()
