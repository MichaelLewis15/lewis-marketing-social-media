# SVG illustrations for Touch of Hope graphics (brand palette)
F = "#2c4a3e"   # forest
F2 = "#3d6152"
S = "#8fae95"   # sage
SL = "#dfe9e0"  # sage light
G = "#c79a45"   # gold
GL = "#f0dcae"  # gold light
R = "#9b4a3f"   # brick/rose
C = "#fbf6ee"   # cream
P = "#7b5c8c"   # advent purple
PK = "#d98aa6"  # advent pink

def sunrise(w=600):
    return f'''<svg viewBox="0 0 600 420" width="{w}" xmlns="http://www.w3.org/2000/svg">
<defs><radialGradient id="sg" cx="50%" cy="100%" r="60%"><stop offset="0" stop-color="#ffe6a8"/><stop offset="1" stop-color="{G}"/></radialGradient></defs>
<g stroke="{G}" stroke-width="6" stroke-linecap="round" opacity=".55">
{''.join(f'<line x1="300" y1="300" x2="{300+260*__import__("math").cos(__import__("math").radians(a))}" y2="{300-260*__import__("math").sin(__import__("math").radians(a))}" stroke-dasharray="2 22"/>' for a in range(15,170,15))}
</g>
<circle cx="300" cy="300" r="120" fill="url(#sg)"/>
<path d="M0 330 Q150 270 300 320 T600 300 V420 H0Z" fill="{S}"/>
<path d="M0 370 Q180 320 330 365 T600 350 V420 H0Z" fill="{F2}"/>
<path d="M0 400 Q200 370 400 398 T600 392 V420 H0Z" fill="{F}"/>
</svg>'''

def big_sun(w=520):
    import math
    rays = ''.join(
        f'<path d="M{260+150*math.cos(math.radians(a-6)):.1f} {260+150*math.sin(math.radians(a-6)):.1f} L{260+250*math.cos(math.radians(a)):.1f} {260+250*math.sin(math.radians(a)):.1f} L{260+150*math.cos(math.radians(a+6)):.1f} {260+150*math.sin(math.radians(a+6)):.1f}Z" fill="{G}" opacity=".85"/>'
        for a in range(0, 360, 30))
    return f'''<svg viewBox="0 0 520 520" width="{w}" xmlns="http://www.w3.org/2000/svg">
<defs><radialGradient id="bs" cx="40%" cy="35%"><stop offset="0" stop-color="#fff3cf"/><stop offset="1" stop-color="#e9b955"/></radialGradient></defs>
{rays}<circle cx="260" cy="260" r="135" fill="url(#bs)"/>
<circle cx="260" cy="260" r="135" fill="none" stroke="#fff" stroke-opacity=".5" stroke-width="4"/>
</svg>'''

def open_book(w=420, ribbon=True):
    rib = f'<path d="M300 70 V250 L282 232 L264 250 V70Z" fill="{R}"/>' if ribbon else ''
    return f'''<svg viewBox="0 0 520 340" width="{w}" xmlns="http://www.w3.org/2000/svg">
<ellipse cx="260" cy="318" rx="230" ry="16" fill="{F}" opacity=".12"/>
<path d="M20 60 Q140 30 258 70 V310 Q140 270 20 300Z" fill="#fff" stroke="{F}" stroke-width="6" stroke-linejoin="round"/>
<path d="M500 60 Q380 30 262 70 V310 Q380 270 500 300Z" fill="#fff" stroke="{F}" stroke-width="6" stroke-linejoin="round"/>
<path d="M20 300 Q140 270 258 310 L260 322 L262 310 Q380 270 500 300 V316 Q380 290 262 326 H258 Q140 290 20 316Z" fill="{F}"/>
<g stroke="{S}" stroke-width="7" stroke-linecap="round">
<path d="M60 110 Q140 92 220 116"/><path d="M60 145 Q140 127 220 151"/><path d="M60 180 Q140 162 200 182"/><path d="M60 215 Q140 197 220 221"/>
<path d="M310 116 Q380 92 460 110"/><path d="M310 151 Q380 127 460 145"/><path d="M330 186 Q390 165 460 180"/><path d="M310 221 Q380 197 460 215"/>
</g>{rib}
</svg>'''

def mug(w=300):
    return f'''<svg viewBox="0 0 300 300" width="{w}" xmlns="http://www.w3.org/2000/svg">
<g stroke="{S}" stroke-width="7" stroke-linecap="round" fill="none" opacity=".9">
<path d="M110 70 Q95 45 112 22"/><path d="M150 70 Q135 42 152 15"/><path d="M190 70 Q175 45 192 22"/></g>
<path d="M235 130 h18 a38 38 0 0 1 0 76 h-22" fill="none" stroke="{F}" stroke-width="16"/>
<rect x="60" y="90" width="180" height="180" rx="26" fill="{F}"/>
<rect x="60" y="90" width="180" height="26" rx="13" fill="{F2}"/>
<path d="M150 140 v80 M122 168 h56" stroke="{G}" stroke-width="12" stroke-linecap="round"/>
</svg>'''

def gift(w=360, bow=True):
    return f'''<svg viewBox="0 0 360 360" width="{w}" xmlns="http://www.w3.org/2000/svg">
<ellipse cx="180" cy="338" rx="150" ry="12" fill="{F}" opacity=".14"/>
<rect x="45" y="150" width="270" height="185" rx="12" fill="{F}"/>
<rect x="30" y="112" width="300" height="56" rx="12" fill="{F2}"/>
<rect x="160" y="112" width="40" height="223" fill="{G}"/>
<path d="M180 112 C120 40 60 70 92 108 C110 128 160 118 180 112Z" fill="{G}" stroke="#a87e33" stroke-width="5"/>
<path d="M180 112 C240 40 300 70 268 108 C250 128 200 118 180 112Z" fill="{G}" stroke="#a87e33" stroke-width="5"/>
<circle cx="180" cy="112" r="17" fill="#a87e33"/>
</svg>'''

def open_box(w=440):
    spark = lambda x, y, s: f'<path d="M{x} {y-s} L{x+s*.28} {y-s*.28} L{x+s} {y} L{x+s*.28} {y+s*.28} L{x} {y+s} L{x-s*.28} {y+s*.28} L{x-s} {y} L{x-s*.28} {y-s*.28}Z" fill="{G}"/>'
    return f'''<svg viewBox="0 0 440 400" width="{w}" xmlns="http://www.w3.org/2000/svg">
{spark(110,70,30)}{spark(330,50,22)}{spark(220,30,16)}{spark(380,140,14)}{spark(60,160,12)}
<ellipse cx="220" cy="382" rx="180" ry="14" fill="{F}" opacity=".14"/>
<path d="M70 190 L220 230 L370 190 V340 L220 380 L70 340Z" fill="{F}"/>
<path d="M220 230 V380 L370 340 V190Z" fill="{F2}"/>
<path d="M70 190 L20 130 L170 95 L220 150Z" fill="#a87e33"/>
<path d="M370 190 L420 130 L270 95 L220 150Z" fill="{G}"/>
<path d="M70 190 L220 150 L370 190 L220 230Z" fill="#1f362d"/>
<path d="M140 268 l60 16" stroke="{G}" stroke-width="10" stroke-linecap="round"/>
</svg>'''

def kids(w=520):
    return f'''<svg viewBox="0 0 520 380" width="{w}" xmlns="http://www.w3.org/2000/svg" fill="none" stroke-linecap="round" stroke-linejoin="round">
<g stroke-width="14" opacity=".9">
<path d="M90 190 A170 170 0 0 1 430 190" stroke="{R}"/><path d="M110 190 A150 150 0 0 1 410 190" stroke="{G}"/><path d="M130 190 A130 130 0 0 1 390 190" stroke="{S}"/>
</g>
<path d="M150 250 H370 L340 310 H180Z" fill="#a87e33" stroke="{F}" stroke-width="7"/>
<rect x="210" y="195" width="100" height="55" rx="6" fill="{GL}" stroke="{F}" stroke-width="7"/>
<path d="M200 200 L260 165 L320 200" stroke="{F}" stroke-width="7"/>
<circle cx="240" cy="222" r="7" fill="{F}" stroke="none"/><circle cx="280" cy="222" r="7" fill="{F}" stroke="none"/>
<path d="M40 340 Q90 315 140 340 T240 340 T340 340 T440 340 T520 340" stroke="{S}" stroke-width="8"/>
</svg>'''

def candles(w=460):
    def candle(x, h, col, lit=True):
        flame = f'<path d="M{x} {300-h-48} q16 22 0 38 q-16 -16 0 -38z" fill="{G}"/><ellipse cx="{x}" cy="{300-h-24}" rx="34" ry="40" fill="{G}" opacity=".18"/>' if lit else ''
        return f'{flame}<rect x="{x-20}" y="{300-h}" width="40" height="{h}" rx="6" fill="{col}"/><line x1="{x}" y1="{300-h}" x2="{x}" y2="{300-h-10}" stroke="{F}" stroke-width="4"/>'
    leaves = ''.join(f'<ellipse cx="{x}" cy="{y}" rx="34" ry="14" fill="{c}" transform="rotate({r} {x} {y})"/>' for x, y, r, c in [
        (60,310,-20,F),(120,322,15,F2),(190,318,-10,S),(260,322,12,F),(330,318,-12,F2),(400,310,20,S),(95,300,30,S),(365,300,-30,F),(230,330,0,F2)])
    berries = ''.join(f'<circle cx="{x}" cy="{y}" r="9" fill="{R}"/>' for x, y in [(85,325),(160,332),(300,334),(380,325),(230,312)])
    return f'''<svg viewBox="0 0 460 360" width="{w}" xmlns="http://www.w3.org/2000/svg">
{candle(100,150,P)}{candle(185,190,P,False)}{candle(275,190,PK,False)}{candle(360,150,P,False)}
{leaves}{berries}
</svg>'''

def dove(w=420):
    return f'''<svg viewBox="0 0 420 340" width="{w}" xmlns="http://www.w3.org/2000/svg">
<path d="M70 200 C100 120 180 110 230 150 C250 110 300 70 370 60 C340 110 320 150 280 180 C300 200 300 240 260 260 C210 290 130 280 80 250 L30 262 L60 230Z" fill="#fff" stroke="{F}" stroke-width="7" stroke-linejoin="round"/>
<path d="M230 150 C240 170 255 178 280 180" fill="none" stroke="{F}" stroke-width="6" stroke-linecap="round"/>
<circle cx="110" cy="190" r="7" fill="{F}"/>
<path d="M72 196 L40 204 L70 210" fill="{G}"/>
<path d="M40 206 C20 240 30 280 70 300" fill="none" stroke="{S}" stroke-width="6" stroke-linecap="round"/>
<ellipse cx="38" cy="250" rx="18" ry="8" fill="{S}" transform="rotate(-60 38 250)"/>
<ellipse cx="50" cy="282" rx="18" ry="8" fill="{S}" transform="rotate(-30 50 282)"/>
<ellipse cx="26" cy="222" rx="16" ry="7" fill="{S}" transform="rotate(-80 26 222)"/>
</svg>'''

def envelope(w=440):
    return f'''<svg viewBox="0 0 440 320" width="{w}" xmlns="http://www.w3.org/2000/svg">
<ellipse cx="220" cy="304" rx="190" ry="12" fill="{F}" opacity=".14"/>
<rect x="30" y="40" width="380" height="250" rx="16" fill="#fff" stroke="{F}" stroke-width="7"/>
<path d="M36 290 L170 165 M404 290 L270 165" stroke="{S}" stroke-width="6"/>
<path d="M36 46 L220 190 L404 46" fill="{GL}" stroke="{F}" stroke-width="7" stroke-linejoin="round"/>
<path d="M220 205 C190 175 168 200 182 222 L220 256 L258 222 C272 200 250 175 220 205Z" fill="{R}"/>
</svg>'''

def lantern(w=320):
    return f'''<svg viewBox="0 0 320 440" width="{w}" xmlns="http://www.w3.org/2000/svg">
<defs><radialGradient id="lg"><stop offset="0" stop-color="#ffe9a8" stop-opacity=".95"/><stop offset=".55" stop-color="{G}" stop-opacity=".35"/><stop offset="1" stop-color="{G}" stop-opacity="0"/></radialGradient></defs>
<circle cx="160" cy="250" r="160" fill="url(#lg)"/>
<path d="M130 60 a30 30 0 0 1 60 0" fill="none" stroke="{G}" stroke-width="10"/>
<path d="M95 110 H225 L205 70 H115Z" fill="{G}"/>
<rect x="105" y="110" width="110" height="200" rx="10" fill="#fff6dd" stroke="{G}" stroke-width="10"/>
<path d="M160 160 q30 40 0 90 q-30 -50 0 -90z" fill="{G}"/>
<path d="M160 195 q12 18 0 40 q-12 -22 0 -40z" fill="#fff3cf"/>
<line x1="160" y1="110" x2="160" y2="150" stroke="{G}" stroke-width="6"/>
<path d="M95 310 H225 L210 345 H110Z" fill="{G}"/>
</svg>'''

def star(w=360):
    return f'''<svg viewBox="0 0 360 360" width="{w}" xmlns="http://www.w3.org/2000/svg">
<defs><radialGradient id="st"><stop offset="0" stop-color="#ffe9a8" stop-opacity=".8"/><stop offset="1" stop-color="{G}" stop-opacity="0"/></radialGradient></defs>
<circle cx="180" cy="180" r="175" fill="url(#st)"/>
<path d="M180 40 L214 140 L320 142 L236 206 L266 310 L180 248 L94 310 L124 206 L40 142 L146 140Z" fill="{G}" stroke="#a87e33" stroke-width="6" stroke-linejoin="round"/>
</svg>'''

def door(w=380):
    return f'''<svg viewBox="0 0 380 480" width="{w}" xmlns="http://www.w3.org/2000/svg">
<path d="M40 470 V170 A150 150 0 0 1 340 170 V470Z" fill="#6b4a2f" stroke="#3e2a1a" stroke-width="10"/>
<path d="M190 30 V470" stroke="#3e2a1a" stroke-width="8"/>
<g stroke="#4f3622" stroke-width="5" opacity=".7"><path d="M80 200 V450 M120 170 V450 M260 170 V450 M300 200 V450"/></g>
<circle cx="170" cy="310" r="10" fill="{G}"/><circle cx="210" cy="310" r="10" fill="{G}"/>
<rect x="120" y="180" width="140" height="170" fill="#f3e6c8" stroke="#a8915e" stroke-width="4" transform="rotate(-3 190 265)"/>
<g stroke="#a8915e" stroke-width="5" stroke-linecap="round" transform="rotate(-3 190 265)"><path d="M140 215 H240 M140 240 H240 M140 265 H225 M140 290 H240 M140 315 H210"/></g>
<circle cx="190" cy="186" r="8" fill="{R}"/>
</svg>'''

def memorial_candle(w=360):
    sprig = ''.join(f'<ellipse cx="{x}" cy="{y}" rx="26" ry="10" fill="{S}" transform="rotate({r} {x} {y})"/>' for x,y,r in [(70,370,-30),(100,345,-50),(130,330,-20),(250,370,30),(220,348,50),(195,333,15)])
    return f'''<svg viewBox="0 0 320 420" width="{w}" xmlns="http://www.w3.org/2000/svg">
<defs><radialGradient id="mg"><stop offset="0" stop-color="#ffe9a8" stop-opacity=".9"/><stop offset=".5" stop-color="{G}" stop-opacity=".22"/><stop offset="1" stop-color="{G}" stop-opacity="0"/></radialGradient></defs>
<circle cx="160" cy="120" r="130" fill="url(#mg)"/>
<path d="M160 50 q34 46 0 86 q-34 -40 0 -86z" fill="{G}"/>
<path d="M160 90 q14 20 0 40 q-14 -20 0 -40z" fill="#fff3cf"/>
<line x1="160" y1="136" x2="160" y2="156" stroke="{F}" stroke-width="5"/>
<rect x="110" y="155" width="100" height="210" rx="12" fill="#fff" stroke="{F}" stroke-width="6"/>
<path d="M118 175 q20 14 42 0 q22 14 42 0" fill="none" stroke="{GL}" stroke-width="6"/>
<path d="M60 395 Q160 330 260 395" fill="none" stroke="{F2}" stroke-width="6" stroke-linecap="round"/>
{sprig}
<rect x="80" y="365" width="160" height="22" rx="11" fill="{F}"/>
</svg>'''

def magnifier(w=420):
    return f'''<svg viewBox="0 0 420 420" width="{w}" xmlns="http://www.w3.org/2000/svg">
<circle cx="170" cy="170" r="130" fill="#fff" stroke="{F}" stroke-width="18"/>
<circle cx="170" cy="170" r="104" fill="{GL}" opacity=".55"/>
<path d="M110 120 a80 80 0 0 1 70 -40" fill="none" stroke="#fff" stroke-width="14" stroke-linecap="round"/>
<text x="170" y="222" text-anchor="middle" font-family="Playfair" font-weight="700" font-size="150" fill="{F}">?</text>
<path d="M265 265 L380 380" stroke="{F}" stroke-width="40" stroke-linecap="round"/>
<path d="M270 270 L300 300" stroke="{G}" stroke-width="40" stroke-linecap="round"/>
</svg>'''

def book_stack(w=400):
    return f'''<svg viewBox="0 0 400 360" width="{w}" xmlns="http://www.w3.org/2000/svg">
<ellipse cx="200" cy="344" rx="170" ry="12" fill="{F}" opacity=".14"/>
<rect x="50" y="270" width="300" height="66" rx="8" fill="{F}"/><rect x="62" y="282" width="10" height="42" fill="{G}"/>
<rect x="80" y="210" width="260" height="60" rx="8" fill="{R}" transform="rotate(-3 210 240)"/><rect x="96" y="222" width="190" height="8" fill="#fff" opacity=".5" transform="rotate(-3 210 240)"/>
<rect x="60" y="150" width="270" height="62" rx="8" fill="{S}" transform="rotate(2 195 181)"/>
<rect x="110" y="60" width="74" height="96" rx="6" fill="{G}" transform="rotate(-12 147 108)"/>
<path d="M130 74 v62 M114 96 h34" stroke="#fff" stroke-width="8" stroke-linecap="round" transform="rotate(-12 147 108)"/>
<path d="M300 40 l10 24 l26 2 l-20 17 l6 26 l-22 -14 l-22 14 l6 -26 l-20 -17 l26 -2z" fill="{G}"/>
</svg>'''

def flag(w=460):
    import math
    pts=[]
    for i in range(0,41):
        x=40+i*9; pts.append((x, 60+14*math.sin(i/6)))
    stripes=''
    for k in range(7):
        y0=k*30
        top=' '.join(f'{x:.1f},{y+y0:.1f}' for x,y in pts)
        bot=' '.join(f'{x:.1f},{y+y0+30:.1f}' for x,y in reversed(pts))
        stripes+=f'<polygon points="{top} {bot}" fill="{R if k%2==0 else "#fff"}"/>'
    canton=' '.join(f'{x:.1f},{y:.1f}' for x,y in pts[:19])+' '+' '.join(f'{x:.1f},{y+120:.1f}' for x,y in reversed(pts[:19]))
    stars=''.join(f'<circle cx="{58+c*22+(r%2)*11}" cy="{82+r*22+14*math.sin((58+c*22-40)/54)}" r="5" fill="#fff"/>' for r in range(4) for c in range(6 if r%2==0 else 5))
    return f'''<svg viewBox="0 0 460 330" width="{w}" xmlns="http://www.w3.org/2000/svg">
<rect x="26" y="40" width="10" height="290" rx="5" fill="{F}"/><circle cx="31" cy="36" r="10" fill="{G}"/>
{stripes}<polygon points="{canton}" fill="{F}"/>{stars}
</svg>'''

def leaf(w=360, col=None):
    col=col or G
    return f'''<svg viewBox="0 0 360 360" width="{w}" xmlns="http://www.w3.org/2000/svg">
<path d="M180 20 L205 95 L265 60 L250 135 L330 130 L280 190 L320 225 L235 235 L245 300 L180 255 L115 300 L125 235 L40 225 L80 190 L30 130 L110 135 L95 60 L155 95 Z" fill="{col}"/>
<path d="M180 70 V340" stroke="#00000033" stroke-width="8" stroke-linecap="round"/>
<path d="M180 160 L250 120 M180 200 L265 190 M180 160 L110 120 M180 200 L95 190" stroke="#00000026" stroke-width="6" stroke-linecap="round"/>
</svg>'''

def wheat(w=360):
    grains=''
    for side in (-1,1):
        for k in range(7):
            y=70+k*34; grains+=f'<ellipse cx="{180+side*20}" cy="{y}" rx="13" ry="26" fill="{G}" transform="rotate({side*28} {180+side*20} {y})"/>'
    return f'''<svg viewBox="0 0 360 440" width="{w}" xmlns="http://www.w3.org/2000/svg">
<path d="M180 40 V430" stroke="#a87e33" stroke-width="8" stroke-linecap="round"/>
<ellipse cx="180" cy="40" rx="12" ry="26" fill="{G}"/>{grains}
<path d="M180 330 Q120 300 90 330 Q130 350 180 345Z" fill="{S}"/><path d="M180 360 Q240 330 270 360 Q230 380 180 375Z" fill="{F2}"/>
</svg>'''

def bag(w=380):
    return f'''<svg viewBox="0 0 380 420" width="{w}" xmlns="http://www.w3.org/2000/svg">
<ellipse cx="190" cy="404" rx="160" ry="12" fill="{F}" opacity=".14"/>
<path d="M130 130 V100 a60 60 0 0 1 120 0 V130" fill="none" stroke="{F}" stroke-width="16" stroke-linecap="round"/>
<path d="M60 130 H320 L300 398 H80 Z" fill="{F}"/>
<path d="M60 130 H320 L316 170 H64 Z" fill="{F2}"/>
<path d="M190 250 C160 215 125 240 140 270 L190 318 L240 270 C255 240 220 215 190 250Z" fill="{G}"/>
</svg>'''
