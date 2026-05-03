"""
ml/data_gemini/visualize_quality.py
─────────────────────────────────────
Analyses postnow_training_data_2500.json and produces a self-contained
HTML quality report: charts + sample captions + stats.

Usage:
    python visualize_quality.py
    → opens quality_report.html in your browser
"""

import json
import re
import random
import webbrowser
from collections import Counter
from pathlib import Path

DATA_FILE   = Path(__file__).parent / "postnow_training_data_2500.json"
REPORT_FILE = Path(__file__).parent / "quality_report.html"

# ── Load data ─────────────────────────────────────────────────────────────────
with open(DATA_FILE, encoding="utf-8") as f:
    data = json.load(f)

captions = data["captions"]
print(f"Loaded {len(captions)} captions.")

# ── Analysis ──────────────────────────────────────────────────────────────────

categories   = [c["category"] for c in captions]
cat_counts   = Counter(categories)
cat_order    = ["product_launch", "daily_moment", "promotion", "engagement", "brand_story"]

en_lengths   = [len(c["caption"]["en"]) for c in captions]
km_lengths   = [len(c["caption"]["km"]) for c in captions]

products     = [c["metadata"]["product"] for c in captions]
top_products = Counter(products).most_common(15)

moods        = [c["metadata"]["mood"] for c in captions]
top_moods    = Counter(moods).most_common(12)

occasions    = [c["metadata"]["occasion"] for c in captions]
top_occ      = Counter(occasions).most_common(12)

audiences    = [c["metadata"]["audience"] if "audience" in c["metadata"]
                else c["metadata"].get("target_audience", "unknown")
                for c in captions]
aud_counts   = Counter(audiences).most_common(10)

promos       = [c["metadata"].get("promotion") for c in captions]
promo_counts = Counter(str(p) for p in promos).most_common(12)

def emoji_count(text):
    emoji_pattern = re.compile(
        "[\U0001F300-\U0001F9FF\U00002700-\U000027BF"
        "\U0000FE00-\U0000FE0F\U00002600-\U000026FF]+",
        re.UNICODE
    )
    return len(emoji_pattern.findall(text))

en_emojis = [emoji_count(c["caption"]["en"]) for c in captions]
km_emojis = [emoji_count(c["caption"]["km"]) for c in captions]

# Khmer character ratio in KM captions (higher = more Khmer)
def khmer_ratio(text):
    khmer = sum(1 for ch in text if "\u1780" <= ch <= "\u17FF")
    total = len([ch for ch in text if not ch.isspace()])
    return round(khmer / total * 100, 1) if total > 0 else 0

km_ratios = [khmer_ratio(c["caption"]["km"]) for c in captions]
avg_km_ratio = round(sum(km_ratios) / len(km_ratios), 1)

# Avg lengths
avg_en = round(sum(en_lengths) / len(en_lengths))
avg_km = round(sum(km_lengths) / len(km_lengths))

# Short vs medium captions
short_en  = sum(1 for l in en_lengths if l < 150)
medium_en = sum(1 for l in en_lengths if l >= 150)

# Hashtag counts
en_ht_counts = [len(c["hashtags"].get("en", [])) for c in captions]
km_ht_counts = [len(c["hashtags"].get("km", [])) for c in captions]

# Bucket caption lengths for histogram
def bucket(vals, step=50, max_v=600):
    buckets = list(range(0, max_v + step, step))
    counts  = [0] * (len(buckets) - 1)
    for v in vals:
        for i in range(len(buckets) - 1):
            if buckets[i] <= v < buckets[i+1]:
                counts[i] += 1
                break
    labels = [f"{buckets[i]}-{buckets[i+1]}" for i in range(len(buckets)-1)]
    return labels, counts

len_labels, en_len_counts = bucket(en_lengths)
_,           km_len_counts = bucket(km_lengths)

# Khmer ratio buckets
def km_bucket(vals):
    buckets = [(0,20),(20,40),(40,60),(60,80),(80,100)]
    counts  = [sum(1 for v in vals if lo <= v < hi) for lo,hi in buckets]
    labels  = [f"{lo}-{hi}%" for lo,hi in buckets]
    return labels, counts

km_r_labels, km_r_counts = km_bucket(km_ratios)

# Random samples per category
random.seed(7)
samples = {}
for cat in cat_order:
    pool = [c for c in captions if c["category"] == cat]
    samples[cat] = random.sample(pool, min(3, len(pool)))

# ── HTML builder helpers ──────────────────────────────────────────────────────

def js_arr(lst):
    return json.dumps(lst)

def js_labels(lst):
    return json.dumps([str(x) for x in lst])

CAT_COLORS = {
    "product_launch": "#C8A27C",
    "daily_moment":   "#7FA39C",
    "promotion":      "#E83F6F",
    "engagement":     "#2274A5",
    "brand_story":    "#5A3E2B",
}

def cat_badge(cat):
    color = CAT_COLORS.get(cat, "#999")
    label = cat.replace("_", " ").title()
    return f'<span style="background:{color};color:#fff;border-radius:4px;padding:2px 8px;font-size:12px;font-weight:600">{label}</span>'

def sample_card(c):
    en = c["caption"]["en"].replace("\n", "<br>")
    km = c["caption"]["km"].replace("\n", "<br>")
    en_ht = " ".join(c["hashtags"].get("en", []))
    km_ht = " ".join(c["hashtags"].get("km", []))
    return f"""
<div style="border:1px solid #e0d6cc;border-radius:10px;padding:16px;margin-bottom:14px;background:#fffaf6">
  <div style="margin-bottom:8px">{cat_badge(c['category'])}
    <span style="color:#888;font-size:12px;margin-left:10px">ID #{c['id']} · {c['metadata'].get('mood','')} · {c['metadata'].get('occasion','')}</span>
  </div>
  <div style="display:grid;grid-template-columns:1fr 1fr;gap:12px">
    <div>
      <div style="font-size:11px;font-weight:700;color:#5A3E2B;margin-bottom:4px">🇬🇧 ENGLISH</div>
      <div style="font-size:13px;line-height:1.6;color:#333">{en}</div>
      <div style="margin-top:6px;font-size:11px;color:#7FA39C">{en_ht}</div>
    </div>
    <div>
      <div style="font-size:11px;font-weight:700;color:#5A3E2B;margin-bottom:4px">🇰🇭 KHMER</div>
      <div style="font-size:13px;line-height:1.6;color:#333">{km}</div>
      <div style="margin-top:6px;font-size:11px;color:#7FA39C">{km_ht}</div>
    </div>
  </div>
</div>"""

# ── Build HTML ────────────────────────────────────────────────────────────────

sample_html = ""
for cat in cat_order:
    sample_html += f'<h3 style="color:#5A3E2B;margin-top:28px">{cat.replace("_"," ").title()} — 3 Random Samples</h3>'
    for c in samples[cat]:
        sample_html += sample_card(c)

html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<title>POSTNOW Dataset Quality Report</title>
<script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.0/dist/chart.umd.min.js"></script>
<style>
  body {{ font-family: 'Helvetica Neue', Arial, sans-serif; margin:0; background:#f8f4ef; color:#333 }}
  .header {{ background:linear-gradient(135deg,#5A3E2B,#C8A27C); color:#fff; padding:32px 40px }}
  .header h1 {{ margin:0; font-size:26px }}
  .header p  {{ margin:6px 0 0; opacity:.85; font-size:14px }}
  .container {{ max-width:1200px; margin:0 auto; padding:30px 24px }}
  .grid-2 {{ display:grid; grid-template-columns:1fr 1fr; gap:20px; margin-bottom:20px }}
  .grid-3 {{ display:grid; grid-template-columns:1fr 1fr 1fr; gap:20px; margin-bottom:20px }}
  .card {{ background:#fff; border-radius:12px; padding:20px; box-shadow:0 1px 6px rgba(0,0,0,.07) }}
  .card h3 {{ margin:0 0 16px; font-size:14px; color:#5A3E2B; text-transform:uppercase; letter-spacing:.5px }}
  .stat-row {{ display:flex; gap:16px; margin-bottom:20px }}
  .stat {{ flex:1; background:#fff; border-radius:12px; padding:20px; text-align:center; box-shadow:0 1px 6px rgba(0,0,0,.07) }}
  .stat .num {{ font-size:32px; font-weight:700; color:#C8A27C }}
  .stat .lbl {{ font-size:12px; color:#888; margin-top:4px }}
  canvas {{ max-height:280px }}
  h2 {{ color:#5A3E2B; border-bottom:2px solid #C8A27C; padding-bottom:8px; margin-top:36px }}
  .quality-bar {{ background:#eee; border-radius:6px; height:10px; overflow:hidden; margin:4px 0 10px }}
  .quality-bar-fill {{ height:100%; border-radius:6px; background:linear-gradient(90deg,#C8A27C,#5A3E2B) }}
  table {{ width:100%; border-collapse:collapse; font-size:13px }}
  th {{ background:#f0e8df; color:#5A3E2B; padding:8px 12px; text-align:left }}
  td {{ padding:7px 12px; border-bottom:1px solid #f0e8df }}
  tr:hover td {{ background:#fffaf6 }}
</style>
</head>
<body>

<div class="header">
  <h1>☕ POSTNOW — Dataset Quality Report</h1>
  <p>postnow_training_data_2500.json · {len(captions):,} bilingual captions · EN + KH · mBART fine-tuning</p>
</div>

<div class="container">

<!-- STAT ROW -->
<div class="stat-row" style="margin-top:24px">
  <div class="stat"><div class="num">{len(captions):,}</div><div class="lbl">Total Captions</div></div>
  <div class="stat"><div class="num">{avg_en}</div><div class="lbl">Avg EN Length (chars)</div></div>
  <div class="stat"><div class="num">{avg_km}</div><div class="lbl">Avg KM Length (chars)</div></div>
  <div class="stat"><div class="num">{avg_km_ratio}%</div><div class="lbl">Avg Khmer Script Ratio</div></div>
  <div class="stat"><div class="num">{len(set(products))}</div><div class="lbl">Unique Products</div></div>
  <div class="stat"><div class="num">{len(set(occasions))}</div><div class="lbl">Unique Occasions</div></div>
</div>

<!-- ROW 1: Category distribution + KM ratio -->
<div class="grid-2">
  <div class="card">
    <h3>Category Distribution</h3>
    <canvas id="catPie"></canvas>
  </div>
  <div class="card">
    <h3>Khmer Script % in KM Captions</h3>
    <canvas id="kmRatio"></canvas>
  </div>
</div>

<!-- ROW 2: Caption length histograms -->
<div class="grid-2">
  <div class="card">
    <h3>English Caption Length Distribution (chars)</h3>
    <canvas id="enLen"></canvas>
  </div>
  <div class="card">
    <h3>Khmer Caption Length Distribution (chars)</h3>
    <canvas id="kmLen"></canvas>
  </div>
</div>

<!-- ROW 3: Top products + top moods -->
<div class="grid-2">
  <div class="card">
    <h3>Top 15 Products</h3>
    <canvas id="topProducts"></canvas>
  </div>
  <div class="card">
    <h3>Top 12 Moods</h3>
    <canvas id="topMoods"></canvas>
  </div>
</div>

<!-- ROW 4: Occasions + Promotions -->
<div class="grid-2">
  <div class="card">
    <h3>Top 12 Occasions</h3>
    <canvas id="topOcc"></canvas>
  </div>
  <div class="card">
    <h3>Top Promotion Types</h3>
    <canvas id="topPromos"></canvas>
  </div>
</div>

<!-- ROW 5: Audience + short vs medium -->
<div class="grid-2">
  <div class="card">
    <h3>Target Audience Split</h3>
    <canvas id="audChart"></canvas>
  </div>
  <div class="card" style="display:flex;flex-direction:column;justify-content:center">
    <h3>Caption Length Mix (EN)</h3>
    <div style="margin-bottom:16px">
      <div style="font-size:13px;color:#555;margin-bottom:4px">Short (&lt;150 chars): <strong>{short_en}</strong> ({round(short_en/len(captions)*100)}%)</div>
      <div class="quality-bar"><div class="quality-bar-fill" style="width:{round(short_en/len(captions)*100)}%"></div></div>
      <div style="font-size:13px;color:#555;margin-bottom:4px">Medium (≥150 chars): <strong>{medium_en}</strong> ({round(medium_en/len(captions)*100)}%)</div>
      <div class="quality-bar"><div class="quality-bar-fill" style="width:{round(medium_en/len(captions)*100)}%"></div></div>
    </div>
    <h3>Avg Hashtag Count</h3>
    <div style="font-size:13px;color:#555">
      🇬🇧 English: <strong>{round(sum(en_ht_counts)/len(en_ht_counts),1)}</strong> tags/caption<br>
      🇰🇭 Khmer: <strong>{round(sum(km_ht_counts)/len(km_ht_counts),1)}</strong> tags/caption
    </div>
    <h3 style="margin-top:16px">Emoji Usage</h3>
    <div style="font-size:13px;color:#555">
      🇬🇧 Avg emojis/caption: <strong>{round(sum(en_emojis)/len(en_emojis),1)}</strong><br>
      🇰🇭 Avg emojis/caption: <strong>{round(sum(km_emojis)/len(km_emojis),1)}</strong>
    </div>
  </div>
</div>

<!-- QUALITY CHECKS -->
<h2>Quality Checks</h2>
<div class="card" style="margin-bottom:20px">
<table>
<tr><th>Check</th><th>Result</th><th>Status</th></tr>
<tr><td>Total captions = 2,500</td><td>{len(captions)}</td><td>{'✅' if len(captions)==2500 else '❌'}</td></tr>
<tr><td>product_launch = 600</td><td>{cat_counts['product_launch']}</td><td>{'✅' if cat_counts['product_launch']==600 else '❌'}</td></tr>
<tr><td>daily_moment = 700</td><td>{cat_counts['daily_moment']}</td><td>{'✅' if cat_counts['daily_moment']==700 else '❌'}</td></tr>
<tr><td>promotion = 500</td><td>{cat_counts['promotion']}</td><td>{'✅' if cat_counts['promotion']==500 else '❌'}</td></tr>
<tr><td>engagement = 400</td><td>{cat_counts['engagement']}</td><td>{'✅' if cat_counts['engagement']==400 else '❌'}</td></tr>
<tr><td>brand_story = 300</td><td>{cat_counts['brand_story']}</td><td>{'✅' if cat_counts['brand_story']==300 else '❌'}</td></tr>
<tr><td>All captions have EN caption</td><td>{sum(1 for c in captions if c['caption'].get('en',''))}</td><td>{'✅' if all(c['caption'].get('en') for c in captions) else '❌'}</td></tr>
<tr><td>All captions have KM caption</td><td>{sum(1 for c in captions if c['caption'].get('km',''))}</td><td>{'✅' if all(c['caption'].get('km') for c in captions) else '❌'}</td></tr>
<tr><td>All captions have EN hashtags</td><td>{sum(1 for c in captions if c['hashtags'].get('en'))}</td><td>{'✅' if all(c['hashtags'].get('en') for c in captions) else '❌'}</td></tr>
<tr><td>All captions have KM hashtags</td><td>{sum(1 for c in captions if c['hashtags'].get('km'))}</td><td>{'✅' if all(c['hashtags'].get('km') for c in captions) else '❌'}</td></tr>
<tr><td>Unique product IDs (no duplicates)</td><td>{len(set(c['id'] for c in captions))}</td><td>{'✅' if len(set(c['id'] for c in captions))==len(captions) else '❌'}</td></tr>
<tr><td>Avg Khmer script ratio ≥ 20%</td><td>{avg_km_ratio}%</td><td>{'✅' if avg_km_ratio >= 20 else '❌'}</td></tr>
<tr><td>Unique products used</td><td>{len(set(products))}</td><td>{'✅' if len(set(products)) >= 10 else '❌'}</td></tr>
<tr><td>Unique occasions used</td><td>{len(set(occasions))}</td><td>{'✅' if len(set(occasions)) >= 10 else '❌'}</td></tr>
</table>
</div>

<!-- SAMPLE CAPTIONS -->
<h2>Sample Captions (3 per Category)</h2>
{sample_html}

</div><!-- /container -->

<script>
const CAT_COLORS = ['#C8A27C','#7FA39C','#E83F6F','#2274A5','#5A3E2B'];

// 1. Category pie
new Chart(document.getElementById('catPie'), {{
  type:'doughnut',
  data:{{
    labels:{js_labels([c.replace('_',' ').title() for c in cat_order])},
    datasets:[{{data:{js_arr([cat_counts[c] for c in cat_order])},backgroundColor:CAT_COLORS,borderWidth:2}}]
  }},
  options:{{plugins:{{legend:{{position:'right'}}}}}}
}});

// 2. KM ratio bar
new Chart(document.getElementById('kmRatio'), {{
  type:'bar',
  data:{{
    labels:{js_labels(km_r_labels)},
    datasets:[{{label:'Captions',data:{js_arr(km_r_counts)},backgroundColor:'#7FA39C',borderRadius:6}}]
  }},
  options:{{plugins:{{legend:{{display:false}}}},scales:{{y:{{beginAtZero:true}}}}}}
}});

// 3. EN length hist
new Chart(document.getElementById('enLen'), {{
  type:'bar',
  data:{{
    labels:{js_labels(len_labels)},
    datasets:[{{label:'EN Captions',data:{js_arr(en_len_counts)},backgroundColor:'#C8A27C',borderRadius:4}}]
  }},
  options:{{plugins:{{legend:{{display:false}}}},scales:{{y:{{beginAtZero:true}}}}}}
}});

// 4. KM length hist
new Chart(document.getElementById('kmLen'), {{
  type:'bar',
  data:{{
    labels:{js_labels(len_labels)},
    datasets:[{{label:'KM Captions',data:{js_arr(km_len_counts)},backgroundColor:'#5A3E2B',borderRadius:4}}]
  }},
  options:{{plugins:{{legend:{{display:false}}}},scales:{{y:{{beginAtZero:true}}}}}}
}});

// 5. Top products
new Chart(document.getElementById('topProducts'), {{
  type:'bar',
  data:{{
    labels:{js_labels([p[0] for p in top_products])},
    datasets:[{{label:'Count',data:{js_arr([p[1] for p in top_products])},backgroundColor:'#E83F6F',borderRadius:4}}]
  }},
  options:{{indexAxis:'y',plugins:{{legend:{{display:false}}}},scales:{{x:{{beginAtZero:true}}}}}}
}});

// 6. Top moods
new Chart(document.getElementById('topMoods'), {{
  type:'bar',
  data:{{
    labels:{js_labels([m[0] for m in top_moods])},
    datasets:[{{label:'Count',data:{js_arr([m[1] for m in top_moods])},backgroundColor:'#2274A5',borderRadius:4}}]
  }},
  options:{{indexAxis:'y',plugins:{{legend:{{display:false}}}},scales:{{x:{{beginAtZero:true}}}}}}
}});

// 7. Top occasions
new Chart(document.getElementById('topOcc'), {{
  type:'bar',
  data:{{
    labels:{js_labels([o[0] for o in top_occ])},
    datasets:[{{label:'Count',data:{js_arr([o[1] for o in top_occ])},backgroundColor:'#C8A27C',borderRadius:4}}]
  }},
  options:{{indexAxis:'y',plugins:{{legend:{{display:false}}}},scales:{{x:{{beginAtZero:true}}}}}}
}});

// 8. Promotions
new Chart(document.getElementById('topPromos'), {{
  type:'bar',
  data:{{
    labels:{js_labels([p[0] for p in promo_counts])},
    datasets:[{{label:'Count',data:{js_arr([p[1] for p in promo_counts])},backgroundColor:'#7FA39C',borderRadius:4}}]
  }},
  options:{{indexAxis:'y',plugins:{{legend:{{display:false}}}},scales:{{x:{{beginAtZero:true}}}}}}
}});

// 9. Audience
new Chart(document.getElementById('audChart'), {{
  type:'doughnut',
  data:{{
    labels:{js_labels([a[0] for a in aud_counts])},
    datasets:[{{data:{js_arr([a[1] for a in aud_counts])},
      backgroundColor:['#C8A27C','#7FA39C','#E83F6F','#2274A5','#5A3E2B',
                       '#D4A017','#6B4226','#3D5A80','#B5838D','#264653'],
      borderWidth:2}}]
  }},
  options:{{plugins:{{legend:{{position:'right'}}}}}}
}});
</script>
</body>
</html>"""

# ── Save and open ─────────────────────────────────────────────────────────────
with open(REPORT_FILE, "w", encoding="utf-8") as f:
    f.write(html)

print(f"✅  Report saved → {REPORT_FILE}")
webbrowser.open(f"file://{REPORT_FILE}")
print("    Opened in browser.")
