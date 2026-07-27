import requests

ANKICONNECT_URL = "http://127.0.0.1:8765"


def invoke(action: str, **params) -> object:
    r = requests.post(ANKICONNECT_URL, json={"action": action, "version": 6, "params": params}).json()
    if r.get("error"):
        raise RuntimeError(f"{action}: {r['error']}")
    return r["result"]


AFMT = (
    '<div class="card">'
    '<div class="cardClr">{{Expression}}</div>'
    '<hr>{{Reading}}'
    '<hr><b style="font-size:1.3em">{{Construction}}</b>'
    '<hr>{{Meaning}}'
    '<hr><span style="color:var(--fg-subtle)">Конструкция:</span> {{PatternForm}}<br>'
    '<span style="color:var(--fg-subtle)">Значение:</span> {{PatternMeaning}}'
    '<hr><span style="color:var(--fg-subtle)">Примеры:</span><br>{{Connection}}'
    '</div>'
)
QFMT = '<div class="card"><div class="cardClr">{{ExpressionClean}}</div></div>'


def main() -> None:
    for model, card_key in [("N3 Grammar+", "Card 1"), ("N2 Grammar v3", "N2 Card")]:
        css = invoke("modelStyling", modelName=model)["css"]
        if "--fg-subtle" not in css:
            css = css.rstrip() + "\n:root { --fg-subtle: #8a7c6a; }\n"
            invoke("updateModelStyling", model={"name": model, "css": css})
        invoke("updateModelTemplates", model={
            "name": model,
            "templates": {card_key: {"Front": QFMT, "Back": AFMT}},
        })
        print(f"{model} template updated")


if __name__ == "__main__":
    main()
