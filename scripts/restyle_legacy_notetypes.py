import json
from pathlib import Path

import requests


def invoke(action, **params):
    r = requests.post('http://127.0.0.1:8765', json={'action': action, 'version': 6, 'params': params}).json()
    if r.get('error'):
        raise RuntimeError(f'{action}: {r["error"]}')
    return r['result']


def main() -> None:
    core_css = json.loads((Path(__file__).parent.parent / 'src' / 'jpvocab' / 'notetype_snapshot.json').read_text(encoding='utf-8'))['css']

    backup = {}
    for model in ['TOEIC Formatted', 'N3 Grammar+', 'N2 Grammar v3']:
        backup[model] = {
            'templates': invoke('modelTemplates', modelName=model),
            'css': invoke('modelStyling', modelName=model)['css'],
        }
    backup_path = Path(__file__).parent / 'backup_legacy_notetypes_before_restyle.json'
    backup_path.write_text(json.dumps(backup, ensure_ascii=False, indent=2), encoding='utf-8')
    print(f'backup written to {backup_path}')

    invoke('updateModelStyling', model={'name': 'TOEIC Formatted', 'css': core_css})
    invoke('updateModelTemplates', model={
        'name': 'TOEIC Formatted',
        'templates': {
            'Card 1': {
                'Front': '<div class="card"><div class="cardClr">{{Front}}</div></div>',
                'Back': '<div class="card"><div class="cardClr">{{Front}}</div><hr>{{Back}}</div>',
            }
        }
    })
    print('TOEIC Formatted restyled')

    invoke('updateModelStyling', model={'name': 'N3 Grammar+', 'css': core_css})
    invoke('updateModelTemplates', model={
        'name': 'N3 Grammar+',
        'templates': {
            'Card 1': {
                'Front': '<div class="card"><div class="cardClr">{{ExpressionClean}}</div></div>',
                'Back': '<div class="card"><div class="cardClr">{{Expression}}</div><hr>{{Reading}}<hr>{{Meaning}}<hr>{{Pattern}}<hr>{{Connection}}</div>',
            }
        }
    })
    print('N3 Grammar+ restyled')

    n2_templates = invoke('modelTemplates', modelName='N2 Grammar v3')
    n2_card_name = list(n2_templates.keys())[0]
    invoke('updateModelStyling', model={'name': 'N2 Grammar v3', 'css': core_css})
    invoke('updateModelTemplates', model={
        'name': 'N2 Grammar v3',
        'templates': {
            n2_card_name: {
                'Front': '<div class="card"><div class="cardClr">{{ExpressionClean}}</div></div>',
                'Back': '<div class="card"><div class="cardClr">{{Expression}}</div><hr>{{Reading}}<hr>{{Meaning}}<hr>{{Pattern}}<hr>{{Connection}}</div>',
            }
        }
    })
    print(f'N2 Grammar v3 restyled (card name: {n2_card_name})')


if __name__ == '__main__':
    main()
