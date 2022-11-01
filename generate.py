#!/usr/bin/env python3
import xml.etree.ElementTree as xmltree

def remove_layer(t, name):
    l = next(
        x for x in t.getroot().findall('./')
        if name == x.attrib.get('{http://www.inkscape.org/namespaces/inkscape}label'))
    
    l.attrib['style'] = 'display:none'

with open('drawing.svg') as f:
    s = f.read()

events = [
    "3×3×3 Rubik's cube",
    "2×2×2 Rubik's cube",
    "4×4×4 Rubik's cube",
    "5×5×5 Rubik's cube",
    "6×6×6 Rubik's cube",
    '3×3×3 Blindfolded',
    '3×3×3 Fewest Moves Challenge',
    '3×3×3 One-Handed',
    'Megaminx',
    'Pyraminx',
    'Skewb',
    'Square-1',
    '4×4×4 Blindfolded',
    '5×5×5 Blindfolded',
    '3×3×3 Multi-Blindfolded',
    "Newcomer Rubik's Cube",
    'Youngest participant']

for nevent, event in enumerate(events):
  for n, m, mv, c, place in [
        (1, 'Gold', 'Shiny Gold', 'ffe858', 'First'),
        (2, 'Silver', 'Honorable Silver', 'cccccc', 'Second'),
        (3, 'Bronze', 'Chocolaty Bronze', 'cd5700', 'Third')]: # cd7f3f
    
    metric = (
        'with a score of' if '3×3×3 Fewest Moves Count' in event or 'Multi-Blindfolded' in event else
        'with a time of' if 'Blindfolded' in event else
        'with an average time of')
    
    s2 = (s
        .replace('ffe858', c)
        .replace('{place}', place)
        .replace('{medal}', '<tspan style="fill:#{}">{}</tspan>'.format(c,mv))
        .replace('{compet}', "Rubik's Cube" if event == "Newcomer Rubik's Cube" else event)
        .replace('{compet_metric}', metric)
        .replace('{as_a}', 'as a newcomer ' if event == "Newcomer Rubik's Cube" else '')
    )
    t = xmltree.ElementTree(xmltree.fromstring(s2))
    if m != 'Gold':
        remove_layer(t, 'Rayons')
    if event != 'Youngest participant':
        remove_layer(t, 'Young text')
    else:
        remove_layer(t, 'Below text')
    t.write('event-{:02}-{}-{}.svg'.format(1+nevent, n, event))
    print('event-{:02}-{}-{}.svg'.format(1+nevent, n, event))
    

