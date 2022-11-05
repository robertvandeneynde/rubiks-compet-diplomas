#!/usr/bin/env python3
import xml.etree.ElementTree as xmltree
import requests
import sys
import subprocess

# if True: Names will be filled
fill_names = True

# if set: name of the competition in the url 
comp_name = "GanshorenSundayOpen2022" # 'BelgianNationals2022' # 'SeraingOpen2021'

# if set: the list of events that will be generated
# if not set or 'all': all the events of 'comp_name' will be used
#events = ['333', '222', '444', '555', '666', '777', '333bf', '333fm', '333oh', 'clock', 'minx', 'pyram', 'skewb', 'sq1']
events = 'all'

# id of the main event (used for newcomer)
main_event_id = '333'

FUNNY_NAMES_MEDALS = ('Sunny Gold', 'Moony Silver', 'Marsy Bronze')
COLORS_MEDALS = ('ffe858', 'cccccc', 'd45500')    
COLORS_MEDALS_TEXT = ('ffcd08', 'cccccc', 'd45500')

template_file = 'drawing.svg'
output_file = 'all-events.pdf'

# check
if fill_names and not comp_name:
    raise Exception("'comp_name' must be set when 'fill_names == True'")

# script
from collections import namedtuple
EventData = namedtuple("EventData", "id name ranking_method")

EVENTS_DATA = [
    EventData('333',    '3x3x3 Cube',         'time'),
    EventData('222',    '2x2x2 Cube',         'time'),
    EventData('444',    '4x4x4 Cube',         'time'),
    EventData('555',    '5x5x5 Cube',         'time'),
    EventData('666',    '6x6x6 Cube',         'time'),
    EventData('777',    '7x7x7 Cube',         'time'),
    EventData('333bf',  '3x3x3 Blindfolded',  'time'),
    EventData('333fm',  '3x3x3 Fewest Moves', 'number'),
    EventData('333oh',  '3x3x3 One-Handed',   'time'),
    EventData('clock',  'Clock',              'time'),
    EventData('minx',   'Megaminx',           'time'),
    EventData('pyram',  'Pyraminx',           'time'),
    EventData('skewb',  'Skewb',              'time'),
    EventData('sq1',    'Square-1',           'time'),
    EventData('444bf',  '4x4x4 Blindfolded',  'time'),
    EventData('555bf',  '5x5x5 Blindfolded',  'time'),
    EventData('333mbf', '3x3x3 Multi-Blind',  'multi')]

EVENTS_DICT = {e[0]:e for e in EVENTS_DATA}

MEDAL_DATA = list(zip(
    (1, 2, 3),
    ('Gold', 'Silver', 'Bronze'),
    FUNNY_NAMES_MEDALS,
    COLORS_MEDALS,
    COLORS_MEDALS_TEXT,
    ('First', 'Second', 'Third')))    

# general functions
def format_time(time):
    """
    7225 -> "1:12.25"
    """
    total_secs = time / 100
    if total_secs < 60:
        return f'{total_secs:.2f}'
    else:
        mins, secs = divmod(total_secs, 60)
        return f'{mins:.0f}:{secs:05.2f}'

def format_fmc(number):
    return str(number)

def format_multi(multi):
    """
    https://www.worldcubeassociation.org/results/misc/export.html
    """
    s = str(multi).zfill(len('0DDTTTTTMM'))
    if s.startswith('1'):
        raise ValueError(f"Old multi format: {multi}")
    if not s.startswith('0'):
        raise ValueError(f"Wrong multi format: {multi}")
    DD, TTTTT, MM = map(int, (s[1:1+2], s[1+2:1+2+5], s[1+2+5:1+2+5+2]))
    
    difference = 99 - DD
    timeInSeconds = TTTTT
    
    if timeInSeconds == 99999:
        raise ValueError("Unknown result")
    
    missed = MM
    solved = difference + missed
    attempted = solved + missed
    
    mins, secs = divmod(timeInSeconds, 60)
    
    return "{}/{} {}:{}".format(solved, attempted, mins, secs)

# functions that reads "response"
def find_name_person(person_id):
    for person in response['persons']:
        if person['registrantId'] == person_id:
            return person['name']
    raise ValueError(f"Not found person id: {person_id}")

def find_name_event(event_id):
    try:
        return EVENTS_DICT[event_id][1]
    except KeyError:
        raise ValueError(f"Not found event id: {event_id}")

def get_main_event():
    for event in response['events']:
        if event['id'] == main_event_id:
            return event
    raise ValueError(f"No main event found: {main_event_id}")

class SvgLayerNotFound(ValueError):
    pass

class SvgLayerMultiFound(ValueError):
    pass

# svg modification functions
def find_layer(element, name):
    layers = [
        x for x in element.findall('./')
        if 'layer' == x.attrib.get('{http://www.inkscape.org/namespaces/inkscape}groupmode')
        if name == x.attrib.get('{http://www.inkscape.org/namespaces/inkscape}label')]
    
    if len(layers) == 0:
        raise SvgLayerNotFound(f"Layer {name!r} not found")
    if len(layers) > 1:
        raise SvgLayerMultiFound(f"Layer {name!r} is duplicate, please rename")

def remove_layer(tree, name):
    layer = find_layer(tree.getroot(), name)
    layer.attrib['style'] = 'display:none'

# functions related to a event(dict)
def get_main_averages(event:dict, personId):
    return sorted(
        result['average']
        for round in event['rounds']
        for result in round['results']
        if result['personId'] == personId
        if result['average'] > 0)

def compute_name_score_for_event(event:dict, n:int):
    if len(event['rounds']) > 0:
        last_round = event['rounds'][-1]
        if len(last_round['results']) >= n:
            podium = last_round['results'][n-1]
            name = find_name_person(podium['personId'])
            score = (format_fmc(podium['best']) if 'fm' in event['id'] else
                     format_multi(podium['best']) if 'mbf' in event['id'] else
                     format_time(podium['best']) if 'bf' in event['id'] else
                     format_time(podium['average']))
            return name, score
    raise ValueError("Unknown score for event")

def find_metric_for_event(event_id:str):
    return (
        'with a score of' if 'fm' in event_id else
        'with a score of' if 'mbf' in event_id else
        'with a time of' if 'bf' in event_id else
        'with an average time of')

def generate_diploma(*, diploma_number:int, event_id:str=None, event:dict=None, newcomerinfo:list=None, diploma_type:'event empty youngest newcomer'):
    files_generated = []
    for n, m, mv, c, ctext, place in MEDAL_DATA:
        if not fill_names or diploma_type == 'empty' or diploma_type == 'youngest':
            name, score = '', ''
        elif diploma_type == 'newcomer':
            try:
                name, score = newcomerinfo[n-1][0], format_time(newcomerinfo[n-1][1])
            except IndexError:
                print(f"Warning: newcomer number {n} cannot be found")
                name, score = '', ''
        elif diploma_type == 'event':
            try:
                name, score = compute_name_score_for_event(event, n)
            except ValueError as e:
                print(f"Warning: {e}")
                name, score = '', ''
        
        metric = find_metric_for_event(event_id)
        
        compet = ("Rubik's Cube" if diploma_type == 'newcomer' else
                  "Rubik's Cube" if diploma_type == 'youngest' else
                  find_name_event(event_id))
        
        as_a = 'as a newcomer ' if diploma_type == 'newcomer' else ''
        
        new_svg_string = (svg_string
            .replace('{place}', place)
            .replace('{medal}', '<tspan style="fill:#{}">{}</tspan>'.format(ctext, mv))
            .replace('{compet}', compet)
            .replace('{compet_metric}', metric)
            .replace('{name}', name)
            .replace('{result}', score)
            .replace('{as_a}', as_a)
        )
            
        tree = xmltree.ElementTree(xmltree.fromstring(new_svg_string))
        
        remove_layer(tree, 'Gold') if not m == 'Gold' else None
        remove_layer(tree, 'Silver') if not m == 'Silver' else None
        remove_layer(tree, 'Bronze') if not m == 'Bronze' else None
        
        remove_layer(tree, 'Young text') if diploma_type != 'youngest' else None
        remove_layer(tree, 'Below text') if diploma_type == 'youngest' else None
        
        for layer_id in EVENTS_DICT:
            if event_id != layer_id:
                try:
                    remove_layer(layer_id)
                except SvgLayerNotFound:
                    pass
        
        diploma_name = ('youngest' if diploma_type == 'youngest' else
                        'newcomer' if diploma_type == 'newcomer' else
                        event_id)
        
        file_name = 'files/event-{:02}-{}-{}'.format(diploma_number + 1, n, diploma_name)
        tree.write(file_name + '.svg', encoding="utf-8")
        
        # call inkscape --export-type=pdf "$f"
        subprocess.check_output(["inkscape", "--export-type=pdf", file_name + '.svg'])
        #subprocess.check_output(["inkscape", f"--file={file_name}.svg", "--without-gui", f"--export-pdf={file_name}.pdf"])
        
        print(f"{file_name!r} generated")
        
        files_generated += [file_name + '.svg', file_name + '.pdf']
    return files_generated


# functions that generate pdfs
def generate_svg_for_event(nevent:int, event:dict):
    return generate_diploma(diploma_number=nevent,
                            event_id=event['id'],
                            event=event,
                            diploma_type='event')

def generate_svg_for_empty_event(nevent, event_id:str):
    return generate_diploma(diploma_number=nevent,
                            event_id=event_id,
                            diploma_type='empty')
        
def generate_svg_for_newcomers(nevent):
    return generate_diploma(diploma_number=nevent,
                            event_id='333',
                            diploma_type='newcomer',
                            newcomerinfo=get_newcomers_info())

def generate_svg_for_youngest(nevent):
    return generate_diploma(diploma_number=nevent,
                            event_id='333',
                            diploma_type='youngest')

# functions for newcomers
def get_newcomers_info():
    if not fill_names:
        return []
    
    newcomers = []
    for person in response['persons']:
        if person['wcaId'] is None:
            averages = get_main_averages(get_main_event(), person['registrantId'])
            if len(averages) != 0:
                newcomers.append((person['name'], averages[0]))
    newcomers.sort(key=lambda y: y[1])
    return newcomers

# script
if comp_name:
    print(f"Fetching data from wca for competition {comp_name!r}...")
    response = requests.get(f'https://www.worldcubeassociation.org/api/v0/competitions/{comp_name}/wcif/public').json()
    print("Done !")
    comp_event_ids = [event['id'] for event in response['events']]

    if events == 'all' or not events:
        event_ids = comp_event_ids
    else:
        event_ids = events
    
    if event_ids:
        if not set(event_ids) <= set(comp_event_ids):
            raise Exception('Those events do not exist in the competition: {}'.format(set(event_ids) - set(comp_event_ids)))
else:
    if events == 'all' or not events:
        raise Exception("When 'comp_name' is not set, 'events' must be set")
    else:
        event_ids = events
    
with open(template_file, encoding="UTF-8") as f:
    svg_string = f.read()

import os
if not os.path.isdir('files'):
    os.mkdir('files')

files_generated = []
if comp_name:
    events_dict = {event['id']: event for event in response['events']}
    events_list = [events_dict[event_id] for event_id in event_ids]
    for nevent, event in enumerate(events_list):
        files_generated += generate_svg_for_event(nevent, event)
else:
    for nevent, event_id in enumerate(event_ids):
        files_generated += generate_svg_for_empty_event(nevent, event_id)

more_event_ids = len(event_ids)

files_generated += generate_svg_for_newcomers(more_event_ids)
files_generated += generate_svg_for_youngest(more_event_ids + 1)

#call pdf merger
#import glob
#subprocess.check_output(["pdftk", "files/event*.pdf", "cat", "output", output_file])
#subprocess.check_output(["pdftk", *sorted(glob.glob("files/event*.pdf")), "cat", "output", output_file])
is_pdf = lambda filename: filename.endswith(".pdf")
subprocess.check_output(["pdftk", *filter(is_pdf, files_generated), "cat", "output", output_file])
print(f"{output_file!r} generated")
