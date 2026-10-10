"""Show ten explicit unresolved legacy examples; do not change selection."""

from __future__ import annotations

import hashlib
import html
import json

from research_tools.commons_colours import OUTPUT, ROOT

SAMPLES = (
    (20264780, 0, "Maßangabe: 225 × 130 cm", "Knapp außerhalb der bisherigen Grenze."),
    (149657860, 0, "Maßangabe: 97,2 × 56,2 cm", "Ein weiterer knapper Grenzfall."),
    (
        114833882,
        0,
        "Maßangabe: 132 × 76,2 cm",
        "Nur rund 0,06 Prozentpunkte über der Grenze.",
    ),
    (
        21878879,
        0,
        "Quelle: w1892 × h1092 cm",
        "Die Einheit ist auffällig; Verhältnis unverändert. Keine korrigierten Maße erfunden.",
    ),
    (
        60909660,
        1,
        "Maßangabe: 32,7 × 19,1 cm",
        "Die Quelle enthält zusätzlich leicht abweichende Zollmaße.",
    ),
    (
        81309955,
        2,
        "Bildträger: 21,9 × 12,7 cm",
        "Hier sind die Bildträgermaße gemeint, nicht der ebenfalls genannte Holzkragen.",
    ),
    (
        118810806,
        0,
        "Maßangabe: 53,2 × 28,9 cm",
        "Das Fotoverhältnis ist enger als das angegebene Werkverhältnis.",
    ),
    (
        34254029,
        0,
        "Bildträger: 71,5 × 42 cm",
        "Quelle nennt ausdrücklich den Bildträger (drager).",
    ),
    (
        38742234,
        0,
        "Maßangabe: 248 × 147 cm",
        "Deutlichere Abweichung; kein direkter Vergleich mit einem Museumoriginal erfolgt.",
    ),
    (
        29864826,
        1,
        "Quelle: 200 × 123,5 cm (Complete)",
        "Größte Abweichung in dieser Stichprobe; Quelle nennt ausdrücklich Complete.",
    ),
)


def render() -> None:
    path = ROOT / "research/commons-baseline-held-proposal-2026-10-10.json"
    receipt_bytes = path.read_bytes()
    records = {r["id"]: r for r in json.loads(receipt_bytes)["records"]}
    cards = []
    samples = []
    for number, (page_id, measure_index, label, note) in enumerate(SAMPLES, 1):
        row = records[page_id]
        thumbnail = OUTPUT / f"{page_id}.jpg"
        if hashlib.sha256(thumbnail.read_bytes()).hexdigest() != row["thumbnail_sha256"]:
            raise ValueError("sample thumbnail differs from retained review")
        work = row["retained_catalogue_entry"]
        file_ratio = work["width"] / work["height"]
        work_ratio = row["physical_measurements"][measure_index]["ratio"]
        deviation = (work_ratio / (16 / 9) - 1) * 100
        source = f"https://commons.wikimedia.org/wiki/Special:Redirect/page/{page_id}"
        cards.append(
            f'<article><div class="picture"><img src="{page_id}.jpg" '
            f'alt="{html.escape(row["title"], quote=True)}"></div>'
            f'<div class="body"><span class="number">Beispiel {number}</span>'
            f'<h2>{html.escape(row["title"])}</h2><p class="artist">'
            f"{html.escape(row['artist'])}</p><dl>"
            f"<dt>Bilddatei</dt><dd>{work['width']} × {work['height']} px "
            f"· Verhältnis {file_ratio:.3f}:1</dd><dt>Werk laut Quelle</dt>"
            f"<dd>{html.escape(label)} · {work_ratio:.3f}:1</dd>"
            f'<dt>Werkmaß ↔ 16:9</dt><dd class="delta">{deviation:+.2f} % '
            f"(bisherige Grenze ±2,5 %)</dd></dl>"
            f'<p class="note">{html.escape(note)}</p><a href="{source}" '
            f'target="_blank" rel="noopener noreferrer">Commons-Quelle öffnen ↗</a>'
            "</div></article>"
        )
        samples.append(
            dict(
                id=page_id,
                thumbnail_sha256=row["thumbnail_sha256"],
                source_markup_sha256=row["source_markup_sha256"],
                measurement_index=measure_index,
                quoted_label=label,
                work_ratio=work_ratio,
                file_ratio=file_ratio,
                work_deviation_percent=deviation,
                explanatory_note=note,
            )
        )
    markup = (
        '<!doctype html><html lang="de"><meta charset="utf-8">'
        '<meta name="viewport" content="width=device-width,initial-scale=1">'
        "<title>Frame Gallery · 10 Bestands-Stichproben</title><style>"
        ":root{color-scheme:light dark;font-family:system-ui;"
        "background:light-dark(#f7f5f0,#11151b);color:light-dark(#17202a,#eef2f6)}"
        "body{max-width:1400px;margin:0 auto;padding:32px}"
        "h1{font-size:clamp(26px,4vw,40px);margin-bottom:12px}"
        "header p{max-width:1000px;line-height:1.65}"
        ".notice{padding:18px 22px;border-left:4px solid #d6a645;"
        "background:light-dark(#fff4d9,#302a1a);border-radius:8px;"
        "line-height:1.6;margin:24px 0}.grid{display:grid;"
        "grid-template-columns:repeat(2,minmax(0,1fr));gap:24px}"
        "article{background:light-dark(white,#1c232c);border-radius:16px;"
        "overflow:hidden;border:1px solid light-dark(#deddd7,#344050)}"
        ".picture{background:#090c10;aspect-ratio:16/9;display:flex;"
        "align-items:center;justify-content:center}"
        ".picture img{width:100%;height:100%;object-fit:contain}"
        ".body{padding:22px}.number{font-size:13px;opacity:.7}"
        "h2{font-size:21px;margin:8px 0}"
        ".artist{margin:0 0 18px;opacity:.85}dl{font-size:14px;line-height:1.7}"
        "dt{font-weight:600;margin-top:8px}dd{margin:0}"
        ".delta{color:light-dark(#855308,#ffcf76)}.note{font-size:14px;"
        "line-height:1.6;opacity:.85}a{color:light-dark(#07678e,#88d3ff)}"
        "footer{margin:32px 0;line-height:1.7}"
        "@media(max-width:780px){body{padding:18px}"
        ".grid{grid-template-columns:1fr}}"
        '</style><header><a href="gallery.html">← Zur gesamten Vorschau</a>'
        "<h1>10 Stichproben aus dem bisherigen Katalog</h1>"
        "<p>Bewusst gemischte Beispiele aus den 56 ungeklärten Bestandsfällen: "
        "knappe Grenzfälle, bekannte Künstler und größere Formatabweichungen. "
        "Alle gezeigten Dateien selbst liegen innerhalb unseres bisherigen 16:9-Bands. "
        "Die Bildfelder haben auf jeder Fensterbreite exakt 16:9; "
        "die Vorschau selbst fügt keine zusätzlichen breiteren Felder hinzu. "
        "Die Prüfung wurde durch abweichende "
        "<em>angegebene Werkmaße</em> ausgelöst.</p>"
        '<div class="notice"><strong>Kein bewiesener Beschnitt.</strong> '
        "Abweichungen können auch aus gerundeten oder falschen Angaben, "
        "unterschiedlichen "
        "Messumfängen, Reproduktionsrändern oder Verzerrung entstehen. Diese Vorschau "
        "beweist weder einen Crop noch dessen Ursache. Ich habe keinen dieser Einträge "
        "aus deiner installierten App entfernt oder umgepinnt. "
        "Mit deiner ausdrücklichen Freigabe vom 10. Oktober werden diese 56 Fälle "
        "im lokalen Update-Katalog vorläufig zurückgestellt und ersetzt; "
        "IDs, Quellen und Sendeverlauf bleiben erhalten.</div>"
        '</header><main class="grid">' + "".join(cards) + "</main>"
        "<footer>Zur Einordnung: 16:9 = 1,778:1. Mit ±2,5 % liegt das Band bei "
        "ungefähr 1,733–1,822:1. Der Prozentwert bezieht sich auf den Unterschied "
        "zwischen <em>Werkmaß-Verhältnis und 16:9</em>, nicht auf eine behauptete "
        "Menge abgeschnittener Bildfläche. Maßangaben sind aus den lokal gespeicherten "
        "Commons-Quellen; kein frisch überprüfter Museumskatalog. "
        "Die Bilder werden hier vollständig mit contain angezeigt, "
        "nicht zugeschnitten.</footer></html>"
    )
    for name in ("legacy-samples.html", "legacy-samples-receipt.json"):
        previous = OUTPUT / name
        if previous.exists():
            payload = previous.read_bytes()
            digest = hashlib.sha256(payload).hexdigest()
            archive = OUTPUT / f"retained-{digest}-{name}"
            if not archive.exists():
                archive.write_bytes(payload)
    (OUTPUT / "legacy-samples.html").write_text(markup)
    (OUTPUT / "legacy-samples-receipt.json").write_text(
        json.dumps(
            dict(
                schema=1,
                purpose="Ten explicit examples for user decision; no selection mutation",
                source_receipt_sha256=hashlib.sha256(receipt_bytes).hexdigest(),
                html_sha256=hashlib.sha256(markup.encode()).hexdigest(),
                samples=samples,
            ),
            indent=2,
        )
        + "\n"
    )
    print(json.dumps(dict(samples=len(samples), html=str(OUTPUT / "legacy-samples.html"))))


if __name__ == "__main__":
    render()
