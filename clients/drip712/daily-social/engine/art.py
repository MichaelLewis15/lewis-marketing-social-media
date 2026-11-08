"""Line-art illustrations for Drip712 graphics. Each function returns an <svg> sized to width w.
Palette: navy #15191e, aqua #2a8be0, mist #e2eefa, sand #f1e6da, blush #f2d9cf, gold #c3955a."""

N, A, M, S, B, G = "#15191e", "#2a8be0", "#e2eefa", "#f1e6da", "#f2d9cf", "#c3955a"


def _svg(w, vb, body):
    h = int(w * vb[1] / vb[0])
    return f'<svg width="{w}" height="{h}" viewBox="0 0 {vb[0]} {vb[1]}" xmlns="http://www.w3.org/2000/svg">{body}</svg>'


def drip_bag(w=380):
    return _svg(w, (300, 400), f'''
<circle cx="150" cy="190" r="140" fill="{M}"/>
<line x1="150" y1="18" x2="150" y2="52" stroke="{N}" stroke-width="6" stroke-linecap="round"/>
<path d="M100 52h100a16 16 0 0 1 16 16v130a50 50 0 0 1-50 50h-32a50 50 0 0 1-50-50V68a16 16 0 0 1 16-16z" fill="#fff" stroke="{N}" stroke-width="6"/>
<path d="M90 140h120v58a44 44 0 0 1-44 44h-32a44 44 0 0 1-44-44z" fill="{A}" opacity=".85"/>
<line x1="110" y1="92" x2="150" y2="92" stroke="{N}" stroke-width="5" stroke-linecap="round" opacity=".5"/>
<line x1="110" y1="110" x2="136" y2="110" stroke="{N}" stroke-width="5" stroke-linecap="round" opacity=".5"/>
<rect x="138" y="248" width="24" height="26" rx="6" fill="{N}"/>
<path d="M150 274 C150 320 150 330 186 352 C212 368 236 360 248 340" fill="none" stroke="{N}" stroke-width="5" stroke-linecap="round"/>
<path d="M150 292 c-9 13-13 20-13 26a13 13 0 0 0 26 0c0-6-4-13-13-26z" fill="{A}"/>
''')


def droplet(w=360):
    return _svg(w, (300, 340), f'''
<circle cx="150" cy="190" r="140" fill="{M}"/>
<path d="M150 30 C110 100 70 150 70 210a80 80 0 0 0 160 0c0-60-40-110-80-180z" fill="{A}"/>
<path d="M118 196c0 26 14 44 36 50" fill="none" stroke="#fff" stroke-width="10" stroke-linecap="round" opacity=".8"/>
<circle cx="236" cy="90" r="12" fill="{A}" opacity=".5"/><circle cx="64" cy="120" r="8" fill="{A}" opacity=".4"/>
''')


def snowflake(w=360):
    arms = "".join(f'<g transform="rotate({a} 150 170)"><line x1="150" y1="170" x2="150" y2="62" stroke="{N}" stroke-width="7" stroke-linecap="round"/>'
                   f'<path d="M150 96 l-20-18 M150 96 l20-18 M150 124 l-14-12 M150 124 l14-12" stroke="{A}" stroke-width="6" stroke-linecap="round"/></g>'
                   for a in range(0, 360, 60))
    return _svg(w, (300, 340), f'<circle cx="150" cy="170" r="140" fill="{M}"/>{arms}<circle cx="150" cy="170" r="14" fill="{A}"/>')


def winter_sun(w=380):
    rays = "".join(f'<line x1="150" y1="40" x2="150" y2="62" stroke="{G}" stroke-width="7" stroke-linecap="round" transform="rotate({a} 150 150)"/>' for a in range(0, 360, 30))
    return _svg(w, (300, 320), f'''
<circle cx="150" cy="150" r="140" fill="{S}"/>{rays}
<circle cx="150" cy="150" r="70" fill="{G}" opacity=".9"/>
<path d="M40 250 q55 -40 110 0 t110 0 v60 h-220z" fill="{M}"/>
<path d="M40 262 q55 -40 110 0 t110 0" fill="none" stroke="{N}" stroke-width="5" opacity=".35"/>
<text x="150" y="160" text-anchor="middle" font-family="Fraunces" font-weight="600" font-size="46" fill="#fff">D</text>
''')


def shield(w=360):
    return _svg(w, (300, 340), f'''
<circle cx="150" cy="170" r="140" fill="{M}"/>
<path d="M150 50 l90 32 v70 c0 66-44 112-90 132 c-46-20-90-66-90-132 V82z" fill="#fff" stroke="{N}" stroke-width="7" stroke-linejoin="round"/>
<path d="M150 74 l68 24 v54 c0 50-32 86-68 102z" fill="{A}" opacity=".85"/>
<path d="M112 170 l26 26 50-56" fill="none" stroke="{N}" stroke-width="10" stroke-linecap="round" stroke-linejoin="round"/>
''')


def sparkle(w=360):
    def star(x, y, s, c):
        return f'<path d="M{x} {y-s} C{x+s*.15} {y-s*.15} {x+s*.15} {y-s*.15} {x+s} {y} C{x+s*.15} {y+s*.15} {x+s*.15} {y+s*.15} {x} {y+s} C{x-s*.15} {y+s*.15} {x-s*.15} {y+s*.15} {x-s} {y} C{x-s*.15} {y-s*.15} {x-s*.15} {y-s*.15} {x} {y-s}z" fill="{c}"/>'
    return _svg(w, (300, 320), f'<circle cx="150" cy="160" r="140" fill="{B}"/>{star(140,170,92,G)}{star(222,84,36,A)}{star(70,82,24,N)}{star(232,236,20,G)}')


def battery(w=380):
    return _svg(w, (320, 300), f'''
<circle cx="160" cy="150" r="140" fill="{M}"/>
<rect x="56" y="96" width="190" height="108" rx="22" fill="#fff" stroke="{N}" stroke-width="7"/>
<rect x="246" y="128" width="18" height="44" rx="6" fill="{N}"/>
<rect x="72" y="112" width="50" height="76" rx="10" fill="{A}"/><rect x="128" y="112" width="50" height="76" rx="10" fill="{A}"/><rect x="184" y="112" width="46" height="76" rx="10" fill="{A}" opacity=".35"/>
<path d="M160 60 l-18 32 h24 l-16 30" fill="none" stroke="{G}" stroke-width="7" stroke-linecap="round" stroke-linejoin="round"/>
''')


def chair(w=380):
    return _svg(w, (320, 320), f'''
<circle cx="160" cy="160" r="140" fill="{B}"/>
<path d="M96 70 h70 a20 20 0 0 1 20 20 v100 h-90z" fill="#fff" stroke="{N}" stroke-width="7" stroke-linejoin="round"/>
<path d="M86 190 h150 a20 20 0 0 1 0 40 h-150 a20 20 0 0 1 0-40z" fill="{A}" stroke="{N}" stroke-width="7"/>
<path d="M110 230 l-14 56 M214 230 l14 56" stroke="{N}" stroke-width="8" stroke-linecap="round"/>
<path d="M196 120 q24 22 0 44 M214 104 q40 38 0 76" fill="none" stroke="{G}" stroke-width="6" stroke-linecap="round"/>
''')


def house(w=380):
    return _svg(w, (320, 310), f'''
<circle cx="160" cy="160" r="140" fill="{M}"/>
<path d="M60 150 L160 64 L260 150" fill="none" stroke="{N}" stroke-width="8" stroke-linecap="round" stroke-linejoin="round"/>
<path d="M84 140 v120 h152 v-120" fill="#fff" stroke="{N}" stroke-width="7" stroke-linejoin="round"/>
<rect x="138" y="196" width="44" height="64" rx="4" fill="{A}"/>
<rect x="102" y="168" width="28" height="28" rx="4" fill="{G}" opacity=".7"/><rect x="190" y="168" width="28" height="28" rx="4" fill="{G}" opacity=".7"/>
<circle cx="236" cy="96" r="10" fill="{A}"/><circle cx="262" cy="118" r="8" fill="{A}" opacity=".6"/><circle cx="214" cy="80" r="7" fill="{A}" opacity=".5"/>
''')


def gift(w=360):
    return _svg(w, (300, 320), f'''
<circle cx="150" cy="170" r="140" fill="{B}"/>
<rect x="66" y="130" width="168" height="140" rx="10" fill="#fff" stroke="{N}" stroke-width="7"/>
<rect x="56" y="104" width="188" height="40" rx="10" fill="{A}" stroke="{N}" stroke-width="7"/>
<rect x="138" y="104" width="24" height="166" fill="{G}"/>
<path d="M150 104 c-30-50-74-30-56 -6 c10 12 40 8 56 6z M150 104 c30-50 74-30 56 -6 c-10 12-40 8-56 6z" fill="none" stroke="{N}" stroke-width="7" stroke-linejoin="round"/>
''')


def calendar(w=360):
    return _svg(w, (300, 320), f'''
<circle cx="150" cy="170" r="140" fill="{M}"/>
<rect x="62" y="80" width="176" height="176" rx="18" fill="#fff" stroke="{N}" stroke-width="7"/>
<path d="M62 98 a18 18 0 0 1 18-18 h140 a18 18 0 0 1 18 18 v30 h-176z" fill="{A}"/>
<line x1="104" y1="62" x2="104" y2="96" stroke="{N}" stroke-width="8" stroke-linecap="round"/><line x1="196" y1="62" x2="196" y2="96" stroke="{N}" stroke-width="8" stroke-linecap="round"/>
<text x="150" y="222" text-anchor="middle" font-family="Fraunces" font-weight="600" font-size="78" fill="{N}">1</text>
''')


def heart(w=360):
    return _svg(w, (300, 300), f'''
<circle cx="150" cy="150" r="140" fill="{B}"/>
<path d="M150 236 C60 176 64 98 110 88 c22-5 36 8 40 24 c4-16 18-29 40-24 c46 10 50 88-40 148z" fill="{A}" stroke="{N}" stroke-width="7" stroke-linejoin="round"/>
<path d="M98 130 q6-20 26-22" fill="none" stroke="#fff" stroke-width="8" stroke-linecap="round" opacity=".8"/>
''')


def question(w=340):
    return _svg(w, (300, 300), f'''
<circle cx="150" cy="150" r="140" fill="{M}"/>
<path d="M70 92 h160 a20 20 0 0 1 20 20 v80 a20 20 0 0 1-20 20 h-90 l-40 34 v-34 h-30 a20 20 0 0 1-20-20 v-80 a20 20 0 0 1 20-20z" fill="#fff" stroke="{N}" stroke-width="7" stroke-linejoin="round"/>
<text x="150" y="186" text-anchor="middle" font-family="Fraunces" font-weight="600" font-size="88" fill="{A}">?</text>
''')


def leaf(w=360):
    return _svg(w, (300, 320), f'''
<circle cx="150" cy="170" r="140" fill="{S}"/>
<path d="M80 250 C70 150 140 80 240 70 C250 170 180 240 80 250z" fill="{A}" opacity=".9"/>
<path d="M80 250 C130 190 170 140 220 96" fill="none" stroke="{N}" stroke-width="6" stroke-linecap="round"/>
<path d="M120 200 l-6-36 M150 168 l-4-40 M180 134 l0-30 M120 200 l34 2 M150 168 l36 0 M180 134 l30 -4" stroke="{N}" stroke-width="4" stroke-linecap="round" opacity=".5"/>
''')


def clock(w=360):
    return _svg(w, (300, 300), f'''
<circle cx="150" cy="150" r="140" fill="{M}"/>
<circle cx="150" cy="150" r="92" fill="#fff" stroke="{N}" stroke-width="7"/>
<path d="M150 150 L150 92 M150 150 L194 172" stroke="{N}" stroke-width="9" stroke-linecap="round"/>
<path d="M150 58 A92 92 0 0 1 242 150 L150 150z" fill="{A}" opacity=".35"/>
<circle cx="150" cy="150" r="9" fill="{G}"/>
''')


def card(w=380):
    return _svg(w, (320, 300), f'''
<circle cx="160" cy="150" r="140" fill="{S}"/>
<rect x="48" y="86" width="224" height="140" rx="18" fill="{N}"/>
<rect x="48" y="118" width="224" height="26" fill="{A}"/>
<rect x="72" y="172" width="70" height="12" rx="6" fill="#fff" opacity=".6"/><rect x="72" y="194" width="40" height="10" rx="5" fill="#fff" opacity=".4"/>
<circle cx="236" cy="190" r="16" fill="{G}"/>
''')


def party(w=380):
    return _svg(w, (320, 320), f'''
<circle cx="160" cy="170" r="140" fill="{B}"/>
<path d="M120 270 L170 110 L230 250z" fill="{A}" stroke="{N}" stroke-width="7" stroke-linejoin="round"/>
<path d="M150 170 l50 26 M138 210 l70 34" stroke="#fff" stroke-width="8" stroke-linecap="round" opacity=".8"/>
<circle cx="90" cy="110" r="10" fill="{G}"/><circle cx="250" cy="90" r="8" fill="{A}"/><circle cx="70" cy="190" r="7" fill="{N}"/>
<path d="M210 70 l10 -20 M240 130 l24 -6 M110 70 l-10-18" stroke="{G}" stroke-width="7" stroke-linecap="round"/>
''')


ARTS = {k: v for k, v in globals().items() if callable(v) and not k.startswith("_")}
