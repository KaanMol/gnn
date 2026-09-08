"""Build a curated, source-backed starter notebook for Seed's existing loader.

This is explicit lesson authoring, not automatic extraction of whole articles.
Run from anywhere with Python 3; no third-party dependencies.
"""
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT.parent))
from semantics import operation, validate


# Article title -> supported (subject, relation, object) assertions.
# Class descriptions are properties, not executable definitions or causal rules.
LESSONS = {
    'Solar System': [('Solar System', 'located in', 'Milky Way'), ('Solar System', 'planet count', '8')],
    'Sun': [('Sun', 'is', 'star'), ('Sun', 'located at', 'centre of the Solar System')],
    'Mercury (planet)': [('Mercury', 'is', 'planet')],
    'Venus': [('Venus', 'is', 'planet')],
    'Earth': [('Earth', 'is', 'planet')],
    'Mars': [('Mars', 'is', 'planet')],
    'Jupiter': [('Jupiter', 'is', 'planet'), ('Jupiter', 'is', 'gas giant')],
    'Saturn': [('Saturn', 'is', 'planet'), ('Saturn', 'is', 'gas giant')],
    'Uranus': [('Uranus', 'is', 'planet'), ('Uranus', 'is', 'ice giant')],
    'Neptune': [('Neptune', 'is', 'planet'), ('Neptune', 'orbit', 'Sun')],
    'Moon': [('Moon', 'is', 'natural satellite'), ('Moon', 'orbit', 'Earth')],
    'Phobos (moon)': [('Phobos', 'is', 'natural satellite'), ('Phobos', 'orbit', 'Mars')],
    'Deimos (moon)': [('Deimos', 'is', 'natural satellite'), ('Deimos', 'orbit', 'Mars')],
    'Io (moon)': [('Io', 'is', 'natural satellite'), ('Io', 'orbit', 'Jupiter')],
    'Europa (moon)': [('Europa', 'is', 'natural satellite'), ('Europa', 'orbit', 'Jupiter')],
    'Ganymede (moon)': [('Ganymede', 'is', 'natural satellite'), ('Ganymede', 'orbit', 'Jupiter')],
    'Callisto (moon)': [('Callisto', 'is', 'natural satellite'), ('Callisto', 'orbit', 'Jupiter')],
    'Titan (moon)': [('Titan', 'is', 'natural satellite'), ('Titan', 'orbit', 'Saturn')],
    'Enceladus': [('Enceladus', 'is', 'natural satellite'), ('Enceladus', 'orbit', 'Saturn')],
    'Triton (moon)': [('Triton', 'is', 'natural satellite'), ('Triton', 'orbit', 'Neptune')],
    'Pluto': [('Pluto', 'is', 'dwarf planet'), ('Pluto', 'located in', 'Kuiper belt')],
    'Ceres (dwarf planet)': [('Ceres', 'is', 'dwarf planet'), ('Ceres', 'located in', 'Asteroid belt')],
    'Eris (dwarf planet)': [('Eris', 'is', 'dwarf planet')],
    'Haumea': [('Haumea', 'is', 'dwarf planet')],
    'Makemake': [('Makemake', 'is', 'dwarf planet'), ('Makemake', 'orbit', 'Sun')],
    'Star': [('Sun', 'nearest star to', 'Earth')],
    'Planet': [('planet', 'description', 'large, rounded astronomical body; definitions vary')],
    'Dwarf planet': [('dwarf planet', 'description', 'gravitationally rounded planetary-mass object orbiting the Sun without orbital dominance')],
    'Natural satellite': [('natural satellite', 'also called', 'moon')],
    'Asteroid': [('asteroid', 'description', 'minor planet in the inner Solar System or co-orbital with Jupiter')],
    'Comet': [('comet', 'description', 'icy small Solar System body or interstellar object that releases gases when passing close to the Sun')],
    'Meteoroid': [('meteoroid', 'description', 'small body in outer space, significantly smaller than an asteroid')],
    'Asteroid belt': [('Asteroid belt', 'located between', 'orbits of Mars and Jupiter')],
    'Kuiper belt': [('Kuiper belt', 'located in', 'outer Solar System')],
    'Oort cloud': [('Oort cloud', 'status', 'theorized cloud of icy planetesimals surrounding the Sun')],
    'Orbit': [('orbit', 'description', 'curved trajectory of an object under the influence of an attracting force')],
    'Rotation': [('rotation', 'description', 'movement of an object that leaves at least one point unchanged')],
    'Orbital period': [('orbital period', 'description', 'time an astronomical object takes to complete one orbit around another object')],
    'Orbital eccentricity': [('orbital eccentricity', 'description', 'dimensionless parameter describing how much an orbit deviates from a circle')],
    'Axial tilt': [('axial tilt', 'also called', 'obliquity')],
    'Retrograde and prograde motion': [('retrograde motion', 'description', 'orbital or rotational motion generally opposite to the rotation of the primary')],
    'Gravity': [('gravity', 'is', 'fundamental interaction')],
    'Inertia': [('inertia', 'description', 'tendency to maintain rest or motion unless a force changes velocity')],
    'Tidal force': [('tidal force', 'description', 'difference in gravitational attraction between different points in a gravitational field')],
    'Mass': [('mass', 'SI unit', 'kilogram')],
    'Radius': [('radius', 'description', 'line segment from the centre of a circle or sphere to its perimeter or surface, or the length of that segment')],
    'Temperature': [('temperature', 'measured with', 'thermometer')],
    'Astronomical unit': [('astronomical unit', 'is', 'unit of length')],
    "Kepler's laws of planetary motion": [("Kepler's laws of planetary motion", 'description', 'good approximations for the orbits of planets around the Sun')],
}


def main():
    articles = {r['title']: r for r in map(json.loads, (ROOT / 'articles.jsonl').read_text().splitlines())}
    assert set(LESSONS) == set(articles), 'Re-review lessons if the input article set changes.'
    language, evidence = [], []
    for title, claims in LESSONS.items():
        article = articles[title]
        # Preserve a verbatim slice of the converted source including any markers.
        # Choose through the first actual prose paragraph, skipping template-only paragraphs.
        paragraphs = article['text'].split('\n\n')
        first = next(i for i, p in enumerate(paragraphs)
                     if re.sub(r'\[template omitted: [^\]]*\]', '', p).strip())
        excerpt = '\n\n'.join(paragraphs[:first + 1])
        proposal = {'operations': [operation('assert', s, r, o) for s, r, o in claims]}
        validate(proposal)
        assert all(len(v) <= 160 for claim in claims for v in claim)
        original = ('Wikipedia starter lesson: ' + title + '\nSource revision: ' + article['revision_url']
                    + '\nSource timestamp: ' + article['timestamp'] + '\nEvidence passage:\n' + excerpt)
        summary = '; '.join(f'{s} / {r} / {o}' for s, r, o in claims)
        language.append({'source': 'wikipedia-curated-lesson', 'original': original,
                         'translation': proposal, 'interpretation': summary,
                         'answer': 'Prepared lesson; see validation report for import results.'})
        evidence.append({'title': title, 'revision_id': article['revision_id'],
                         'revision_url': article['revision_url'], 'timestamp': article['timestamp'],
                         'evidence': excerpt, 'operations': proposal['operations']})
    (ROOT / 'seed-wikipedia.json').write_text(json.dumps({'sensors': [], 'language': language}, ensure_ascii=False, indent=2) + '\n')
    (ROOT / 'seed-evidence.jsonl').write_text(''.join(json.dumps(r, ensure_ascii=False) + '\n' for r in evidence))
    print(f"Prepared {len(language)} lessons with {sum(len(r['operations']) for r in evidence)} assertions.")


if __name__ == '__main__':
    main()
