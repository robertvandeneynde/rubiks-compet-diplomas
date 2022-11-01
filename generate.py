#!/usr/bin/env python3
import xml.etree.ElementTree as xmltree
import requests
import sys
import subprocess

generate_empty = True
main_event_id = '333'
reponse = {}
if not generate_empty :
    comp_name = 'SeraingOpen2021'
    response = requests.get('https://www.worldcubeassociation.org/api/v0/competitions/'+ comp_name +'/wcif/public').json()

events_data = [
('333', '3x3x3 Cube', 10, 'time', '3x3x3 Cube'),
('222', '2x2x2 Cube', 20, 'time', '2x2x2 Cube'),
('444', '4x4x4 Cube', 30, 'time', '4x4x4 Cube'),
('555', '5x5x5 Cube', 40, 'time', '5x5x5 Cube'),
('666', '6x6x6 Cube', 50, 'time', '6x6x6 Cube'),
('777', '7x7x7 Cube', 60, 'time', '7x7x7 Cube'),
('333bf', '3x3x3 Blindfolded', 70, 'time', '3x3x3 Blindfolded'),
('333fm', '3x3x3 Fewest Moves', 80, 'number', '3x3x3 Fewest Moves'),
('333oh', '3x3x3 One-Handed', 90, 'time', '3x3x3 One-Handed'),
('clock', 'Clock', 110, 'time', 'Clock'),
('minx', 'Megaminx', 120, 'time', 'Megaminx'),
('pyram', 'Pyraminx', 130, 'time', 'Pyraminx'),
('skewb', 'Skewb', 140, 'time', 'Skewb'),
('sq1', 'Square-1', 150, 'time', 'Square-1'),
('444bf', '4x4x4 Blindfolded', 160, 'time', '4x4x4 Blindfolded'),
('555bf', '5x5x5 Blindfolded', 170, 'time', '5x5x5 Blindfolded'),
('333mbf', '3x3x3 Multi-Blind', 180, 'multi', '3x3x3 Multi-Blind')]

empty_events = ['333', '222', '444', '555', '666', '777','333bf', '333fm', '333oh', 'clock', 'minx', 'pyram', 'skewb', 'sq1']

def find_name_person(person_id) :
    for person in response['persons'] :
        if person['registrantId'] == person_id :
            return person['name']
    raise ValueError("Not found person id : " + str(person_id))

def find_name_event(event_id) :
    for event in events_data :
        if event[0] == event_id :
            return event[1]
    raise ValueError("Not found event id : " + str(event_id))

def format_time(time) :
    secs = time/100
    if secs < 60 :
        return f'{secs:.2f}'
    else :
        mins = int(secs//60)
        secs = secs%60
        return f'{mins}:{secs:05.2f}'
    
    

# for event in response['events'] :
    # print(find_name_event(event['id']))
    # last_round = event['rounds'][-1]
    # for i,podium in enumerate(last_round['results'][:3]) :
        # print("Position", i+1)
        # print(find_name_person(podium['personId']))
        # print("Best", podium['best']/100)
        # print("Average", podium['average']/100)
        # print()


#sys.exit()

def remove_layer(t, name):
    l = next(
        x for x in t.getroot().findall('./')
        if name == x.attrib.get('{http://www.inkscape.org/namespaces/inkscape}label'))
    
    l.attrib['style'] = 'display:none'

with open('drawing.svg',encoding="UTF-8") as f:
    s = f.read()

# events = [
    # "3×3×3 Rubik's cube",
    # "2×2×2 Rubik's cube",
    # "4×4×4 Rubik's cube",
    # "5×5×5 Rubik's cube",
    # "6×6×6 Rubik's cube",
    # "7×7×7 Rubik's cube",
    # '3×3×3 Blindfolded',
    # '3×3×3 One-Handed',
    # 'Megaminx',
    # 'Pyraminx',
    # 'Skewb',
    # 'Square-1',
    # "Newcomer Rubik's Cube",
    # 'Youngest participant']

def get_main_event() :
    for event in response['events']:
        if event['id'] == main_event_id :
            return event
        raise ValueError("No main event found : " + str(main_event_id))

def get_main_averages(event, personId) :
    averages = []
    for round in event['rounds'] :
        for result in round['results'] :
            if result['personId'] == personId and result['average'] > 0 :
                averages.append(result['average'])

    averages.sort()
    return averages

def generate_for_newcomers(nevent) :
    newcomers = []
    if not generate_empty :
        for person in response['persons'] :
            if person['wcaId'] is None : # or person['wcaId'].startswith('2021'):
                id = person['registrantId']
                name = person['name']
                averages = get_main_averages(get_main_event(), id)
                if len(averages) != 0 :
                    newcomers.append((name, averages[0]))
        newcomers.sort(key=lambda y: y[1])
    generate_svg_for_newcomers(nevent, newcomers)

def generate_svg_for_event(nevent, event) :
    for n, m, mv, c, ctext, place in [
        (1, 'Gold', 'Sunny Gold', 'ffe858', 'ffcd08', 'First'),
        (2, 'Silver', 'Moony Silver', 'cccccc', 'cccccc', 'Second'),
        (3, 'Bronze', 'Marsy Bronze', 'd45500', 'd45500', 'Third')]: # cd5700 cd7f3f
    
        name = ''
        score = ''
        if len(event['rounds']) > 0 :
            last_round = event['rounds'][-1]
            if len(last_round['results']) >= n :
                podium = last_round['results'][n-1]
                name = find_name_person(podium['personId'])
                score = format_time(podium['best'] if 'bf' in event['id'] else podium['average'])

        metric = (
            'with a score of' if 'fm' in event or 'mbf' in event else
            'with a time of' if 'bf' in event['id'] else
            'with an average time of')
        
        s2 = (s
            .replace('ffe858', c)
            .replace('{place}', place)
            .replace('{medal}', '<tspan style="fill:#{}">{}</tspan>'.format(ctext,mv))
            .replace('{compet}', "Rubik's Cube" if event['id'] == "Newcomer Rubik's Cube" else find_name_event(event['id']))
            .replace('{compet_metric}', metric)
            .replace('{name}', name)
            .replace('{result}', score)
            .replace('{as_a}', 'as a newcomer ' if event['id'] == "Newcomer Rubik's Cube" else '')
        )
        t = xmltree.ElementTree(xmltree.fromstring(s2))
        
        remove_layer(t, 'Gold') if not m == 'Gold' else None
        remove_layer(t, 'Silver') if not m == 'Silver' else None
        remove_layer(t, 'Bronze') if not m == 'Bronze' else None
        
        if m != 'Gold':
            remove_layer(t, 'Rayons')
        if event != 'Youngest participant':
            remove_layer(t, 'Young text')
        else:
            remove_layer(t, 'Below text')
        file_name = 'event-{:02}-{}-{}.svg'.format(1+nevent, n, event['id'])
        t.write(file_name,encoding="UTF-8")
        # call inkscape --export-type=pdf "$f"
        subprocess.check_output(["inkscape", "--export-type=pdf", file_name])
        print(file_name)

def generate_svg_for_empty_event(nevent, event) :
    for n, m, mv, c, ctext, place in [
        (1, 'Gold', 'Sunny Gold', 'ffe858', 'ffcd08', 'First'),
        (2, 'Silver', 'Moony Silver', 'cccccc', 'cccccc', 'Second'),
        (3, 'Bronze', 'Marsy Bronze', 'd45500', 'd45500', 'Third')]: # cd5700 cd7f3f
    
        name = ''
        score = ''

        metric = (
            'with a score of' if 'fm' in event or 'mbf' in event else
            'with a time of' if 'bf' in event else
            'with an average time of')
        
        s2 = (s
            .replace('ffe858', c)
            .replace('{place}', place)
            .replace('{medal}', '<tspan style="fill:#{}">{}</tspan>'.format(ctext,mv))
            .replace('{compet}', find_name_event(event))
            .replace('{compet_metric}', metric)
            .replace('{name}', name)
            .replace('{result}', score)
            .replace('{as_a}', '')
        )
        t = xmltree.ElementTree(xmltree.fromstring(s2))
        
        remove_layer(t, 'Gold') if not m == 'Gold' else None
        remove_layer(t, 'Silver') if not m == 'Silver' else None
        remove_layer(t, 'Bronze') if not m == 'Bronze' else None
        
        if m != 'Gold':
            remove_layer(t, 'Rayons')
        remove_layer(t, 'Young text')
        file_name = 'event-{:02}-{}-{}.svg'.format(1+nevent, n, event)
        t.write(file_name,encoding="UTF-8")
        # call inkscape --export-type=pdf "$f"
        subprocess.check_output(["inkscape", "--export-type=pdf", file_name])
        print(file_name)


def generate_svg_for_newcomers(nevent, info) :
    for n, m, mv, c, place in [
        (1, 'Gold', 'Sunny Gold', 'ffe858', 'First'),
        (2, 'Silver', 'Moony Silver', 'cccccc', 'Second'),
        (3, 'Bronze', 'Marsy Bronze', 'd45500', 'Third')]: # cd5700 cd7f3f
        
        if generate_empty or len(info) < n :
            name = ''
            score = ''
        else :
            name = info[n-1][0]
            score = format_time(info[n-1][1])

        metric = 'with an average time of'
        
        s2 = (s
            .replace('ffe858', c)
            .replace('{place}', place)
            .replace('{medal}', '<tspan style="fill:#{}">{}</tspan>'.format(c,mv))
            .replace('{compet}', "Rubik's Cube")
            .replace('{compet_metric}', metric)
            .replace('{name}', name)
            .replace('{result}', score)
            .replace('{as_a}', 'as a newcomer ')
        )
        t = xmltree.ElementTree(xmltree.fromstring(s2))
        
        remove_layer(t, 'Gold') if not m == 'Gold' else None
        remove_layer(t, 'Silver') if not m == 'Silver' else None
        remove_layer(t, 'Bronze') if not m == 'Bronze' else None
        
        if m != 'Gold':
            remove_layer(t, 'Rayons')
    
        remove_layer(t, 'Young text')
  
        file_name = 'event-{:02}-{}-{}.svg'.format(1+nevent, n, "Newcomer Rubik's Cube")
        t.write(file_name,encoding="UTF-8")
        # call inkscape --export-type=pdf "$f"
        subprocess.check_output(["inkscape", "--export-type=pdf", file_name])
        print(file_name)

def generate_svg_for_youngest(nevent) :
    for n, m, mv, c, place in [
        (1, 'Gold', 'Sunny Gold', 'ffe858', 'First'),
        (2, 'Silver', 'Moony Silver', 'cccccc', 'Second'),
        (3, 'Bronze', 'Marsy Bronze', 'd45500', 'Third')]: # cd5700 cd7f3f
        

        name = ''
        score = ''

        metric = 'with an average time of'
        
        s2 = (s
            .replace('ffe858', c)
            .replace('{place}', place)
            .replace('{medal}', '<tspan style="fill:#{}">{}</tspan>'.format(c,mv))
            .replace('{compet}', "Rubik's Cube")
            .replace('{compet_metric}', metric)
            .replace('{name}', name)
            .replace('{result}', score)
            .replace('{as_a}', '')
        )
        t = xmltree.ElementTree(xmltree.fromstring(s2))
        
        remove_layer(t, 'Gold') if not m == 'Gold' else None
        remove_layer(t, 'Silver') if not m == 'Silver' else None
        remove_layer(t, 'Bronze') if not m == 'Bronze' else None
        
        if m != 'Gold':
            remove_layer(t, 'Rayons')
    
        remove_layer(t, 'Below text')
  
        file_name = 'event-{:02}-{}-{}.svg'.format(1+nevent, n, 'Youngest participant')
        t.write(file_name,encoding="UTF-8")
        # call inkscape --export-type=pdf "$f"
        subprocess.check_output(["inkscape", "--export-type=pdf", file_name])
        print(file_name)

if generate_empty :
    for nevent, event in enumerate(empty_events):
        generate_svg_for_empty_event(nevent, event)
else :
    for nevent, event in enumerate(response['events']):
        generate_svg_for_event(nevent, event)

more_events_id = len(empty_events)
if not generate_empty :
    more_events_id = len(response['events'])

#generate_for_newcomers(more_events_id)
#more_events_id += 1
#generate_svg_for_youngest(more_events_id)

#call pdf merger
subprocess.check_output(["pdftk", "event*.pdf", "cat", "output", "all-events.pdf"])
    

