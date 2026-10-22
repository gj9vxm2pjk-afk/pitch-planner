"""Opponent-name rules shared by opposition.py, clean_opponents.py and sync_tables.py.

ALIAS: spelling variants (lower case) -> the name we show. NOT_CLUB: labels that are events or admin, not clubs.
tidy() is deliberately cautious: it only changes a cell it is sure about (spelling, capitals, an A/H/away/home/@ground tag that
agrees with the Venue) and returns everything else unchanged.
"""
import re

# variant spelling (lower case) -> the name we show
ALIAS = {
    "t'dale": 'Tynedale', 'tdale': 'Tynedale', 'tyndale': 'Tynedale', "w'end": 'Wallsend', 'wend': 'Wallsend',
    'n shields': 'North Shields', 'pp': 'Percy Park', 'ppark': 'Percy Park', 'pont': 'Ponteland', 'novo': 'Novos',
    'novocastrians': 'Novos', 'wovos': 'Novos', 'jarrovarians': 'Jarrovians', 'bishop auck': 'Bishop Auckland',
    'north allerton': 'Northallerton', 'horden': 'Peterlee & Horden', 'peterlee': 'Peterlee & Horden',
    'hartlepool rovers': 'Hartlepool Rovers', 'poppy sword consett': 'Consett',
}
# names that look like a typo or a one-off: shown in the Notes column (Blyton and Creighton checked with the club coordinator: both fine)
SUSPECT = {}
# whole labels that are events, training or admin, not clubs (regex, matched on the lower-case raw text)
NOT_CLUB = re.compile(r'fest|cup|league|leag |training|train\b|paddock|tour\b|swap|moved|game request|friendly|fnl|^tour$|second stage|joint')
# words/brackets that only describe the fixture, removed before the club name is read
NOISE = [r'\([^)]*\)', r'@\s*\w[\w ]*', r'\bhome-?w/e\b', r'\bneed to be away\b', r'\b(away|home)\b', r'\s-\s*cc\b', r'\bcc\b', r'\b[0-9]+s\b', r'\ba$']

def clean_parts(raw):
    """Club names in an Opponent cell, or ([], reason) when it is not a club."""
    t = raw.strip()
    if not t: return [], ''
    low = t.lower()
    if low in ('tbc', 'tba'): return [], 'opponent not decided yet (TBC)'
    if NOT_CLUB.search(re.sub(r'\([^)]*\)', '', low)): return [], 'event, training or admin label'   # a bracket such as (Tour) does not hide the club
    if re.fullmatch(r'[\d\s]+', low): return [], 'just a number: check what it is'
    inner = re.fullmatch(r'\(([^)]+)\)\s*.*', t)                 # "(Percy Park) Away": the club is the bracketed part
    if inner: low = inner.group(1).lower()
    low = re.sub(r'horden\s*/\s*peterlee|peterlee\s*/\s*horden', 'peterlee and horden', low)
    for pat in NOISE: low = re.sub(pat, ' ', low)
    parts = [p.strip(" .-") for p in re.split(r'\s*/\s*|\s*&\s*|\s+and\s+', low)]
    parts = [re.sub(r'\s+a$', '', re.sub(r'\s+', ' ', p)).strip() for p in parts if p]
    if any(re.match(r'u\d+\b|colts|\d(st|nd) xv', p) for p in parts): return [], 'a WBR team name, not a club'
    parts = [p for p in parts if p]
    names = []
    for p in parts:
        if p == 'peterlee and horden': names.append('Peterlee & Horden'); continue
        names.append(ALIAS.get(p) or ' '.join(w.capitalize() for w in p.split()))
    return names, ''

TAG = re.compile(r"\s*\(\s*(a|h)\s*\)|\s*\b(away|home)\b|\s*@\s*([a-z][a-z' ]*)", re.I)
UNSURE = re.compile(r"[()/&]|\s-\s|\band\b|\s(a|[0-9]+s)$|^[\d\s]*$")        # brackets, joint fixtures, A-team suffixes, bare numbers
# Clubs the coordinator has checked. tidy() only rewrites a name to one of these; add a club here when a new one appears.
KNOWN_CLUBS = {'Alnwick', 'Ashington', 'Billingham', 'Bishop Auckland', 'Blaydon', 'Blyth', 'Blyton', 'Consett', 'Creighton', 'Darlington', 'Durham City', 'Egremont', 'Gateshead', 'Gosforth', 'Guisborough', 'Hartlepool', 'Hartlepool Rovers', 'Houghton', 'Jarrovians', 'Keswick', 'Middlesbrough', 'Morpeth', 'North Shields', 'North Valkyries', 'Northallerton', 'Northern', 'Novos', 'Penrith', 'Percy Park', 'Peterlee & Horden', 'Ponteland', 'Ryton', 'Sunderland', 'Tynedale', 'Wallsend', 'Wensleydale', 'Workington'}
LEAVE = {'tbc', 'tba', ''}

def tidy(opp, venue='', notes=''):
    """(opponent, notes) after cleaning, or the inputs unchanged when there is any doubt."""
    t = (opp or '').strip()
    low = t.lower()
    if low in LEAVE or NOT_CLUB.search(low): return opp, notes
    tags = [m.group(0).strip() for m in TAG.finditer(low)]
    base = re.sub(r'\s+', ' ', TAG.sub('', low)).strip(' .-')
    if not base or UNSURE.search(base): return opp, notes
    v = (venue or '').strip().lower()
    note = []
    for tag in tags:
        k = tag.strip('() ').lower()
        if k in ('a', 'away'): ok, text = v == 'away', 'Away'
        elif k in ('h', 'home'): ok, text = v.startswith('home'), 'Home'
        elif tag.startswith('@'): ok, text = v == 'away', '@ ' + ' '.join(w.capitalize() for w in tag[1:].split())
        else: return opp, notes
        if not ok: return opp, notes                       # the tag contradicts the venue: leave it for the warning
        note.append(text)
    club = ALIAS.get(base) or ' '.join(w.capitalize() for w in base.split())
    if club not in KNOWN_CLUBS: return opp, notes
    new_notes = notes
    for n in note:
        if n.lower() not in (new_notes or '').lower(): new_notes = f'{new_notes}; {n}' if new_notes else n
    return club, new_notes
