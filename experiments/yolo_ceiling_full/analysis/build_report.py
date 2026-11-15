"""Build the experiment-2 visual evaluation report (self-contained HTML, images embedded as compressed JPEG)."""
import base64
import io
import json
import zipfile
from pathlib import Path

from PIL import Image, ImageDraw

HERE = Path(__file__).resolve().parent
EXP2 = HERE.parent
PRED = EXP2 / "outputs_exp2/results/yolo26n-obb_full/predictions"
A = json.load(open(HERE / "analysis_exp2.json"))
AU = json.load(open(HERE / "annotation_audit.json"))
M = json.load(open(EXP2 / "outputs_exp2/results/yolo26n-obb_full/metrics.json"))
E1 = json.load(open(EXP2 / "exp1/metrics.json"))


def b64(im: Image.Image, w=960, q=72) -> str:
    im = im.convert("RGB")
    im = im.resize((w, int(im.height * w / im.width)))
    buf = io.BytesIO(); im.save(buf, "JPEG", quality=q, optimize=True)
    return "data:image/jpeg;base64," + base64.b64encode(buf.getvalue()).decode()


def pred(stem_prefix: str) -> str:
    f = next(p for p in PRED.iterdir() if p.name.startswith(stem_prefix))
    return b64(Image.open(f))


def fig(prefix, caption, tag=None):
    t = f'<span class="tag {tag[0]}">{tag[1]}</span>' if tag else ""
    return (f'<figure><img src="{pred(prefix)}" alt="Ground truth (left) and YOLO26 prediction (right): {caption[:80]}" '
            f'loading="lazy"><figcaption>{t}{caption}</figcaption></figure>')


# inconsistent copies of one photo (ground truth drawn on both)
import sys
sys.path.insert(0, str(EXP2.parent / "yolo_ceiling"))
from analyze_dataset import ZIP  # noqa: E402
z = zipfile.ZipFile(ZIP)
members = {Path(n).name: n for n in z.namelist() if "/images/" in n}
COL = {0: (214, 40, 40), 1: (40, 110, 210), 2: (230, 150, 0), 3: (30, 150, 70), 4: (150, 50, 190)}


def gt_img(name):
    im = Image.open(io.BytesIO(z.read(members[name]))).convert("RGB")
    d = ImageDraw.Draw(im); n = 0
    for line in z.read(members[name].replace("/images/", "/labels/").rsplit(".", 1)[0] + ".txt").decode().splitlines():
        p = line.split()
        if len(p) == 9:
            d.polygon([(float(p[1 + 2 * i]) * 640, float(p[2 + 2 * i]) * 640) for i in range(4)], outline=COL[int(p[0])], width=4); n += 1
    return im, n


pair = AU["inconsistent_copy_examples"][1][:2]
(ia, na), (ib, nb) = gt_img(pair[0]), gt_img(pair[1])
both = Image.new("RGB", (1290, 640), "white"); both.paste(ia, (0, 0)); both.paste(ib, (650, 0))
incons_img = b64(both)

ov = M["overall"]; e1o = E1["overall"]; op = M["operating_point"]; e1op = E1["operating_point"]
T = A["test_image_level_conf025"]


def frac(d):
    return f'{d["recall"]}/{d["pos"]}', f'{d["fp_images"]}/{d["neg"]}'


rows_cls = "".join(
    f'<tr><td>{M["per_class"][c]["display"]}</td><td class="n">{E1["per_class"][c]["mAP50"]:.3f}</td>'
    f'<td class="n">{M["per_class"][c]["mAP50"]:.3f}</td><td class="n">{M["per_class"][c]["precision"]:.2f}</td>'
    f'<td class="n">{M["per_class"][c]["recall"]:.2f}</td><td class="n">{op["fn_by_class"][c]}</td></tr>'
    for c in M["per_class"])
il = ""
for name, key in (("YOLO26n exp 2", "yolo26n_exp2"), ("Llama 4 Maverick (current app)", "llama4_maverick"),
                  ("Hybrid: either one flags it", "hybrid_union_conf025")):
    sr, sf = frac(T[key]["surface"]); mr, mf = frac(T[key]["moisture"])
    il += f'<tr><td>{name}</td><td class="n">{sr}</td><td class="n">{sf}</td><td class="n">{mr}</td><td class="n">{mf}</td></tr>'
stain = A["missed_stain_images_of"][0]
vo = "".join(f'<tr><td class="n">{r["conf"]:.2f}</td><td class="n">{r["precision"]:.2f}</td><td class="n">{r["recall"]:.2f}</td>'
             f'<td class="n">{r["f1"]:.2f}</td><td class="n">{r["tp"]}</td><td class="n">{r["fp"]}</td></tr>' for r in A["valid_object_curve"])
vi = "".join(f'<tr><td class="n">{r["conf"]:.2f}</td><td class="n">{r["yolo_surface"]}</td><td class="n">{r["hybrid_surface"]}</td>'
             f'<td class="n">{r["yolo_moisture"]}</td><td class="n">{r["hybrid_moisture"]}</td></tr>'
             for r in A["valid_image_curve"] if r["conf"] in (0.05, 0.1, 0.2, 0.25, 0.3, 0.4))
LV = A["llama_valid"]
ovl = AU["cross_class_overlap_by_pair"]

html = f"""<title>Ceiling Detector Review</title>
<meta name="claude:viewport-fit-sides" content="cover">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=IBM+Plex+Sans:wght@400;500;600&family=IBM+Plex+Mono:wght@400;500&family=Space+Grotesk:wght@500;600&display=swap">
<style>
/* Layout: one reading column of findings; evidence figures (GT | prediction) run full column width */
:root {{
  --bg: #f6f7f8; --surface: #ffffff; --fg: #1c2127; --muted: #5b6570; --line: #dde1e5;
  --accent: #1f6f8b; --good: #2e7d4f; --warn: #a86400; --bad: #b3261e;
  --display: "Space Grotesk", "Segoe UI", system-ui, sans-serif;
  --body: "IBM Plex Sans", "Segoe UI", system-ui, sans-serif;
  --mono: "IBM Plex Mono", ui-monospace, Consolas, monospace;
}}
@media (prefers-color-scheme: dark) {{ :root:not([data-theme="light"]) {{
  --bg: #12161a; --surface: #1a2026; --fg: #e4e8ec; --muted: #9aa5b0; --line: #2c343c;
  --accent: #5fb3cf; --good: #6cc792; --warn: #e0a85a; --bad: #f08a80; color-scheme: dark }} }}
:root[data-theme="dark"] {{
  --bg: #12161a; --surface: #1a2026; --fg: #e4e8ec; --muted: #9aa5b0; --line: #2c343c;
  --accent: #5fb3cf; --good: #6cc792; --warn: #e0a85a; --bad: #f08a80; color-scheme: dark }}
body {{ background: var(--bg); color: var(--fg); font: 15px/1.6 var(--body); }}
main {{ max-width: 1000px; margin: 0 auto; padding-block: 32px 64px;
  padding-left: max(16px, env(safe-area-inset-left, 0px)); padding-right: max(16px, env(safe-area-inset-right, 0px));
  display: grid; gap: 36px; }}
h1, h2, h3 {{ font-family: var(--display); text-wrap: balance; line-height: 1.2; margin: 0; }}
h1 {{ font-size: 2rem; }} h2 {{ font-size: 1.35rem; }} h3 {{ font-size: 1.05rem; }}
section {{ display: grid; gap: 14px; min-width: 0; }}
p {{ margin: 0; max-width: 70ch; }} .muted {{ color: var(--muted); }}
.eyebrow {{ font: 500 .75rem var(--mono); letter-spacing: .08em; text-transform: uppercase; color: var(--accent); }}
.verdict {{ background: var(--surface); border: 1px solid var(--line); border-left: 4px solid var(--accent);
  padding: 18px 20px; display: grid; gap: 10px; border-radius: 6px; }}
.verdict ul {{ margin: 0; padding-left: 1.2em; display: grid; gap: 6px; }}
.tablewrap {{ overflow-x: auto; }}
table {{ border-collapse: collapse; width: 100%; font-size: .9rem; background: var(--surface); }}
th, td {{ text-align: left; padding: 7px 10px; border-bottom: 1px solid var(--line); vertical-align: top; }}
th {{ font: 500 .78rem var(--mono); color: var(--muted); letter-spacing: .03em; }}
td.n {{ font-family: var(--mono); font-variant-numeric: tabular-nums; white-space: nowrap; }}
tr.hl td {{ background: color-mix(in srgb, var(--accent) 10%, transparent); }}
figure {{ margin: 0; display: grid; gap: 6px; }}
figure img {{ width: 100%; height: auto; border: 1px solid var(--line); border-radius: 4px; display: block; }}
figcaption {{ font-size: .9rem; color: var(--muted); max-width: 80ch; }}
.figs {{ display: grid; gap: 22px; }}
.tag {{ display: inline-block; font: 500 .72rem var(--mono); padding: 1px 7px; border-radius: 3px; margin-right: 8px;
  border: 1px solid currentColor; letter-spacing: .03em; }}
.tag.good {{ color: var(--good); }} .tag.warn {{ color: var(--warn); }} .tag.bad {{ color: var(--bad); }}
.stats {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(190px, 1fr)); gap: 12px; }}
.stat {{ background: var(--surface); border: 1px solid var(--line); padding: 12px 14px; border-radius: 6px; display: grid; gap: 2px; min-width: 0; }}
.stat b {{ font: 600 1.4rem var(--display); }} .stat span {{ font-size: .85rem; color: var(--muted); }}
.note {{ font-size: .85rem; color: var(--muted); border-top: 1px solid var(--line); padding-top: 12px; }}
code {{ font-family: var(--mono); font-size: .88em; }}
</style>
<main>
<header style="display:grid;gap:10px">
  <div class="eyebrow">FixIt Madison · YOLO26n-OBB experiment 2 · evaluation review</div>
  <h1>Ceiling Detector Review</h1>
  <p class="muted">Experiment 2 (155 training photos) on the same 50 held-out test images as experiment 1 and the current
  Llama 4 Maverick pipeline. Test findings use only the saved artifacts from the single test evaluation (confidence 0.25);
  threshold and hybrid tuning use the 36 validation images. Nothing was retrained or re-evaluated on test.</p>
</header>

<div class="verdict">
  <h2>Verdict</h2>
  <ul>
    <li><b>Do not integrate YOLO as a standalone detector.</b> Object-level recall is 0.13 at confidence 0.25
      ({op['true_positives']} of {op['true_positives'] + op['false_negatives']} damage boxes), and validation tuning
      cannot fix it (best F1 0.27).</li>
    <li><b>A narrow hybrid looks useful:</b> adding YOLO's crack/hole flags to Llama found surface damage in
      {frac(T['hybrid_union_conf025']['surface'])[0]} test images versus {frac(T['llama4_maverick']['surface'])[0]} for Llama alone,
      with {frac(T['hybrid_union_conf025']['surface'])[1]} false-positive images versus {frac(T['llama4_maverick']['surface'])[1]}.
      Validation agrees in direction (+2 images, +1 false positive). For moisture, Llama alone is better.</li>
    <li><b>The dataset is the main limit, not the model size.</b> All {AU['boxes']:,} boxes are axis-aligned (the OBB format
      carries no orientation), the moisture classes are labelled on top of each other, holes are tiny, and copies of the
      same photo are labelled inconsistently.</li>
    <li><b>Next experiment: fix the data</b> (relabel a focused crack/hole/stain set, merge or define the moisture
      classes, add real clean ceilings and fixture negatives), not YOLO26s.</li>
  </ul>
</div>

<section>
  <h2>Measured results on the same 50 test images</h2>
  <div class="stats">
    <div class="stat"><span>mAP50</span><b>{e1o['mAP50']:.3f} → {ov['mAP50']:.3f}</b><span>exp 1 → exp 2</span></div>
    <div class="stat"><span>mAP50-95</span><b>{e1o['mAP50-95']:.3f} → {ov['mAP50-95']:.3f}</b><span>exp 1 → exp 2</span></div>
    <div class="stat"><span>Boxes found at conf 0.25</span><b>{e1op['true_positives']} → {op['true_positives']}</b><span>of 230 labelled</span></div>
    <div class="stat"><span>Inference</span><b>{M['speed_ms_per_image']['inference']:.0f} ms</b><span>per image on the A10G (Llama ≈ 5.5 s)</span></div>
  </div>
  <div class="tablewrap"><table>
    <tr><th>class</th><th>mAP50 exp 1</th><th>mAP50 exp 2</th><th>precision</th><th>recall</th><th>missed boxes (conf 0.25)</th></tr>
    {rows_cls}
  </table></div>
  <p class="muted">Training: 1.8 min on an NVIDIA A10G, early stop at epoch 28 (best validation epoch 13), same as
  experiment 1's 28 epochs. The test images are identical, so the gain comes from training (40 more distinct photos;
  patience 15 vs 10 did not lengthen the run), not from a different test set. With 11-20 test images per class, per-class
  differences of a few hundredths are within noise.</p>
</section>

<section>
  <h2>Image level: does the image get flagged?</h2>
  <p>Crack and hole map to the app's <code>DAMAGED_SURFACES</code>; damp, mold-like discoloration and stain map to
  <code>WATER_DAMAGE_MOLD</code> (or <code>LEAK_PLUMBING</code>).</p>
  <div class="tablewrap"><table>
    <tr><th>test images (fixed conf 0.25)</th><th>surface found</th><th>surface false-positive images</th><th>moisture found</th><th>moisture false-positive images</th></tr>
    {il}
  </table></div>
  <p class="muted">Missed stain images (of {A['missed_stain_images_of'][1]}): YOLO {stain['yolo26n_exp2']}, Llama {stain['llama4_maverick']},
  hybrid {stain['hybrid']}.</p>
</section>

<section>
  <h2>Correct detections</h2>
  <div class="figs">
    {fig("28-shutterstock", "Crack: two boxes follow the crack line (0.35, 0.37). Confidence is low even when correct.", ("good", "crack"))}
    {fig("96-neighbors", "Damp patch and stain on the same water damage. The damp/stain split is the dataset's own ambiguity.", ("good", "damp · stain"))}
    {fig("54-damp-proof", "Mold-like discoloration spots found (0.57, 0.32). A visual finding only, never a mold diagnosis.", ("good", "mold-like"))}
  </div>
</section>

<section>
  <h2>Crack and hole images YOLO catches that Llama misses</h2>
  <p>{len(A['yolo_only_surface'])} test images: 3 clear, 1 debatable label, 1 lucky. Llama catches {len(A['llama_only_surface'])} that YOLO misses.</p>
  <div class="figs">
    {fig("27-plasterer", "Hole at 0.94: the strongest YOLO-only catch. The crack boxes on the right are on a plasterboard offcut in the person's hand (false positives).", ("good", "hole"))}
    {fig("6-cracked-ceiling", "Large real cracks found. Note the air vent detected as a hole (0.57): vents, detectors and lights look like holes to this model.", ("good", "crack"))}
    {fig("77-shutterstock", "Cracked, peeling corner found (0.84, 0.73).", ("good", "crack"))}
    {fig("53--742ba90e", "Gap along the crown molding: the dataset labels it a crack, and YOLO agrees. Whether a tenant should report this is debatable.", ("warn", "label"))}
    {fig("28_JPG", "Counted as a catch, but the crack box sits on a black line across the photo, not on the labelled damage.", ("warn", "lucky"))}
  </div>
</section>

<section>
  <h2>Most important false positives</h2>
  <p>{op['false_positives']} false-positive boxes at conf 0.25: {op['fp_by_kind']['wrong class']} wrong class, {op['fp_by_kind']['no matching']} with no matching label.
  Many are scoring artifacts rather than hallucinations.</p>
  <div class="figs">
    {fig("1-damp_causes", "Labelled damp patch, predicted stain (0.69). Right place, and visually it is a water stain. The moisture classes overlap.", ("warn", "class ambiguity"))}
    {fig("31-drywall-crack", "Real crack, but YOLO's two tight boxes don't overlap the label's one loose box enough, so a correct find counts as two false positives.", ("warn", "box granularity"))}
  </div>
</section>

<section>
  <h2>Most important false negatives</h2>
  <p>{op['false_negatives']} labelled boxes missed at conf 0.25, most of them mold-like ({op['fn_by_class']['ceiling_mold']}) and crack ({op['fn_by_class']['ceiling_crack']}).</p>
  <div class="figs">
    {fig("97-black-mold", "Large, obvious dark mold-like patches and nothing detected. The clearest real failure.", ("bad", "real miss"))}
    {fig("89WATE", "Huge discoloration around a smoke detector missed; the small hole is called mold-like (0.31).", ("bad", "real miss"))}
    {fig("56-ceiling-leakage", "Obvious hole missed; a crack box lands beside it.", ("bad", "real miss"))}
    {fig("98-maxresdefault", "Ring-shaped water stain labelled \"mold\" in the dataset; the thin crack through it is also missed.", ("warn", "label error"))}
  </div>
</section>

<section>
  <h2>Do the labels cover the damage?</h2>
  <div class="stats">
    <div class="stat"><span>Axis-aligned boxes</span><b>{AU['box_orientation']['axis_aligned']:,} / {AU['boxes']:,}</b><span>zero rotated: "OBB" without orientation</span></div>
    <div class="stat"><span>Overlapping labels, two classes</span><b>{AU['cross_class_overlap_pairs']}</b><span>pairs, {ovl.get('damp+mold', 0)} of them damp + mold-like</span></div>
    <div class="stat"><span>Median hole box</span><b>{AU['median_box_area_pct_by_class']['ceiling_hole']}%</b><span>of the image (≈18×18 px at 640)</span></div>
    <div class="stat"><span>Photos labelled differently across copies</span><b>{AU['copies_with_different_box_counts']} / {AU['photos_with_copies']}</b><span>{AU['copies_with_different_class_sets']} with different classes</span></div>
  </div>
  <figure><img src="{incons_img}" alt="Two copies of the same photo with different ground-truth boxes" loading="lazy">
    <figcaption>Two copies of the same stain photo in the dataset: {na} boxes (left) versus {nb} boxes (right), with
    different classes for the same marks (red crack, blue damp, orange hole, green mold-like, purple stain).</figcaption></figure>
  <p>Diagonal cracks get large upright rectangles that are mostly clean ceiling, so a tight, correct prediction often
  fails the 0.5 overlap test. {AU['whole_image_boxes']} boxes cover most of the image, and {AU['tiny_boxes']} cover less than 0.2%.
  These problems cap any model trained on this data and also make the scores understate some correct detections.</p>
</section>

<section>
  <h2>Threshold tuning on validation (36 images)</h2>
  <div class="tablewrap"><table>
    <tr><th>conf</th><th>precision</th><th>recall</th><th>F1</th><th>TP</th><th>FP</th></tr>{vo}
  </table></div>
  <p>No threshold makes YOLO a good box detector: raising it buys precision only by losing recall. Image-level hybrid on
  validation (Llama alone: surface {LV['surface']}, moisture {LV['moisture']}):</p>
  <div class="tablewrap"><table>
    <tr><th>YOLO conf</th><th>YOLO surface</th><th>hybrid surface</th><th>YOLO moisture</th><th>hybrid moisture</th></tr>{vi}
  </table></div>
  <p class="muted">Each cell: images found / positives | false-positive images / negatives. At 0.20–0.25 the surface hybrid
  adds 2 of 20 images for 1 extra false positive; lower thresholds add false positives quickly. 0.25 is a reasonable
  setting for a crack/hole helper, to be confirmed on new photos.</p>
</section>

<section>
  <h2>Recommendation</h2>
  <ul style="margin:0;padding-left:1.2em;display:grid;gap:8px;max-width:75ch">
    <li><b>Keep Llama as the detector in the app.</b> Don't integrate YOLO before the demo.</li>
    <li><b>Next experiment: improve the dataset, not the model size.</b> Relabel a focused set (cracks with rotated
      boxes, holes, stains; one consistent label per photo), merge damp + mold-like + stain or write clear rules for
      them, and add real clean ceilings plus vents, smoke detectors and lights as negatives. With 155 distinct photos
      and noisy labels, YOLO26s would mostly fit the noise; it is worth testing only after the data is fixed, or as a
      cheap side run (about 2 GPU minutes) that doesn't block the data work.</li>
    <li><b>Also try a standard axis-aligned YOLO26 detector</b> on the same split: the labels have no orientation, so
      it is the better-matched task.</li>
    <li><b>Later, a hybrid crack/hole helper</b> (YOLO at conf 0.25 OR Llama) could add surface recall, but confirm it
      on new photos first; the +5 images on test are from small samples.</li>
  </ul>
</section>

<p class="note">Data: Roboflow "Ceiling" v1 (CC BY 4.0, universe.roboflow.com/scipublic/ceiling-y9dkm). Model:
Ultralytics YOLO26n-OBB 8.4.196 (AGPL-3.0). Figures: ground truth (left) and YOLO26 prediction (right), from
the single test evaluation. "Mold-like discoloration" describes appearance only; neither model diagnoses mold.
Exploratory: test-set hybrid numbers use the fixed 0.25 threshold from the original evaluation; tuning used validation only.</p>
</main>
"""
out = HERE / "exp2_visual_report.html"
out.write_text(html, encoding="utf-8")
print(out, round(out.stat().st_size / 1e6, 2), "MB")
