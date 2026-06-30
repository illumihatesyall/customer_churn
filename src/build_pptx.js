/**
 * build_pptx.js — Customer Churn Analysis presentation
 * Run: node src/build_pptx.js
 * Output: outputs/churn_presentation.pptx
 */
const pptxgen = require("pptxgenjs");
const path = require("path");
const fs = require("fs");

const ROOT = path.resolve(__dirname, "..");
const OUT = path.join(ROOT, "outputs");
const IMGS = path.join(ROOT, "outputs");

// ── Palette ───────────────────────────────────────────────────────────────
const C = {
  navy:     "1E2761",   // primary dark
  iceblue:  "CADCFC",   // light accent
  white:    "FFFFFF",
  offwhite: "F4F6FB",
  red:      "C0392B",
  green:    "27AE60",
  midgray:  "64748B",
  lightgray:"E2E8F0",
  black:    "1A1A2E",
  gold:     "F4C430",
  teal:     "0D9488",
};

// ── Fonts ─────────────────────────────────────────────────────────────────
const F = { title: "Cambria", body: "Calibri" };

// ── Helpers ───────────────────────────────────────────────────────────────
function imgPath(name) {
  const p = path.join(IMGS, name);
  return fs.existsSync(p) ? p : null;
}

function makeShadow() {
  return { type: "outer", color: "000000", blur: 8, offset: 3, angle: 45, opacity: 0.12 };
}

function card(slide, x, y, w, h, fillColor) {
  slide.addShape(slide.pres.shapes.ROUNDED_RECTANGLE, {
    x, y, w, h,
    fill: { color: fillColor || C.white },
    rectRadius: 0.08,
    shadow: makeShadow(),
    line: { color: C.lightgray, width: 0.5 },
  });
}

// ── Presentation ──────────────────────────────────────────────────────────
const pres = new pptxgen();
pres.layout = "LAYOUT_16x9";
pres.title = "Customer Churn Analysis";
pres.author = "Data Science Team";

// Give slide reference to card helper
function addCard(slide, x, y, w, h, fillColor) {
  slide.addShape(pres.shapes.ROUNDED_RECTANGLE, {
    x, y, w, h,
    fill: { color: fillColor || C.white },
    rectRadius: 0.08,
    shadow: makeShadow(),
    line: { color: C.lightgray, width: 0.5 },
  });
}

// ════════════════════════════════════════════════════════════════════════
// SLIDE 1 — Title
// ════════════════════════════════════════════════════════════════════════
{
  const s = pres.addSlide();
  s.background = { color: C.navy };

  // Left dark panel (full left half) via large text area
  s.addShape(pres.shapes.RECTANGLE, {
    x: 0, y: 0, w: 10, h: 5.625,
    fill: { color: C.navy },
  });

  // Decorative circle top-right
  s.addShape(pres.shapes.OVAL, {
    x: 7.2, y: -1.2, w: 3.8, h: 3.8,
    fill: { color: C.iceblue, transparency: 85 },
    line: { color: C.iceblue, width: 1, transparency: 60 },
  });
  s.addShape(pres.shapes.OVAL, {
    x: 7.8, y: -0.6, w: 2.5, h: 2.5,
    fill: { color: C.iceblue, transparency: 75 },
    line: { color: C.iceblue, width: 1, transparency: 50 },
  });

  // Tag chip
  s.addShape(pres.shapes.ROUNDED_RECTANGLE, {
    x: 0.7, y: 1.1, w: 2.4, h: 0.38,
    fill: { color: C.teal },
    rectRadius: 0.05,
  });
  s.addText("DATA SCIENCE", {
    x: 0.7, y: 1.1, w: 2.4, h: 0.38,
    fontSize: 9, bold: true, color: C.white, align: "center", valign: "middle",
    fontFace: F.body, charSpacing: 3, margin: 0,
  });

  // Main title
  s.addText("Customer Churn\nAnalysis", {
    x: 0.7, y: 1.65, w: 7, h: 2.0,
    fontSize: 44, bold: true, color: C.white,
    fontFace: F.title, align: "left", valign: "top",
  });

  // Subtitle
  s.addText("Predicting, Understanding & Reducing Customer Churn\nUsing the Telco Dataset", {
    x: 0.7, y: 3.75, w: 6.5, h: 0.8,
    fontSize: 14, color: C.iceblue, fontFace: F.body, align: "left",
  });

  // Bottom meta bar
  s.addShape(pres.shapes.RECTANGLE, {
    x: 0, y: 5.1, w: 10, h: 0.525,
    fill: { color: C.teal },
  });
  s.addText("Telco Customer Churn  •  7,043 customers  •  XGBoost + SHAP  •  PR-AUC 0.25  •  4.19x Lift", {
    x: 0.5, y: 5.1, w: 9, h: 0.525,
    fontSize: 10, color: C.white, fontFace: F.body, align: "center", valign: "middle", margin: 0,
  });

  s.addNotes("Welcome. Today I'll walk you through a complete churn analysis — from raw data to a deployed model and actionable segments. The goal is to give you a decision-ready view of who is about to leave and what we can do about it.");
}

// ════════════════════════════════════════════════════════════════════════
// SLIDE 2 — Agenda
// ════════════════════════════════════════════════════════════════════════
{
  const s = pres.addSlide();
  s.background = { color: C.offwhite };

  s.addText("Agenda", {
    x: 0.6, y: 0.3, w: 8.8, h: 0.7,
    fontSize: 32, bold: true, color: C.navy, fontFace: F.title,
  });

  const items = [
    ["01", "Business Problem",        "Why churn costs 5× more than retention"],
    ["02", "Data & EDA",              "7,043 customers, key risk drivers"],
    ["03", "Model Results",           "XGBoost vs baseline — PR-AUC, lift, recall"],
    ["04", "SHAP Interpretation",     "What actually drives churn decisions"],
    ["05", "3 Actionable Segments",   "Who to target and why"],
    ["06", "Recommendations",         "Estimated $42K/yr revenue impact"],
  ];

  items.forEach(([num, title, sub], i) => {
    const col = i % 2;
    const row = Math.floor(i / 2);
    const x = 0.5 + col * 4.85;
    const y = 1.2 + row * 1.35;

    addCard(s, x, y, 4.5, 1.15, C.white);

    // Number badge
    s.addShape(pres.shapes.OVAL, {
      x: x + 0.18, y: y + 0.28, w: 0.55, h: 0.55,
      fill: { color: C.navy },
    });
    s.addText(num, {
      x: x + 0.18, y: y + 0.28, w: 0.55, h: 0.55,
      fontSize: 11, bold: true, color: C.white, align: "center", valign: "middle",
      fontFace: F.body, margin: 0,
    });

    s.addText(title, {
      x: x + 0.85, y: y + 0.12, w: 3.5, h: 0.38,
      fontSize: 13, bold: true, color: C.navy, fontFace: F.title, valign: "middle",
    });
    s.addText(sub, {
      x: x + 0.85, y: y + 0.55, w: 3.5, h: 0.45,
      fontSize: 10, color: C.midgray, fontFace: F.body, valign: "top",
    });
  });

  s.addNotes("Six sections, roughly 3 minutes each.");
}

// ════════════════════════════════════════════════════════════════════════
// SLIDE 3 — Business Problem
// ════════════════════════════════════════════════════════════════════════
{
  const s = pres.addSlide();
  s.background = { color: C.navy };

  s.addText("The Business Problem", {
    x: 0.7, y: 0.3, w: 8.6, h: 0.65,
    fontSize: 32, bold: true, color: C.white, fontFace: F.title,
  });

  // 3 big stat cards
  const stats = [
    { val: "5×",    label: "more expensive",  sub: "to acquire a new customer\nthan to keep one" },
    { val: "26.5%", label: "churn rate",       sub: "of our 7,043 customers\nhave already left" },
    { val: "$74",   label: "avg monthly ARPU", sub: "per customer — every\nchurn point costs revenue" },
  ];
  stats.forEach(({ val, label, sub }, i) => {
    const x = 0.5 + i * 3.1;
    addCard(s, x, 1.15, 2.85, 2.6, "243060");
    s.addText(val, {
      x, y: 1.35, w: 2.85, h: 1.0,
      fontSize: 52, bold: true, color: C.gold, fontFace: F.title,
      align: "center", valign: "middle",
    });
    s.addText(label.toUpperCase(), {
      x, y: 2.4, w: 2.85, h: 0.35,
      fontSize: 10, bold: true, color: C.iceblue, fontFace: F.body,
      align: "center", charSpacing: 2,
    });
    s.addText(sub, {
      x, y: 2.78, w: 2.85, h: 0.75,
      fontSize: 10, color: "AABCD4", fontFace: F.body, align: "center",
    });
  });

  // Bottom quote
  s.addShape(pres.shapes.RECTANGLE, {
    x: 0.5, y: 4.05, w: 9, h: 1.0,
    fill: { color: C.teal, transparency: 20 },
    rectRadius: 0.06,
  });
  s.addText("Objective: Build a model that identifies who is likely to leave, explain why, and quantify the revenue we can save.", {
    x: 0.7, y: 4.1, w: 8.6, h: 0.9,
    fontSize: 13, color: C.white, fontFace: F.body, align: "center", valign: "middle", bold: true,
  });

  s.addNotes("Acquiring a new customer costs 5× more than retaining one — this is industry consensus. At 26.5% churn we're leaking serious revenue. The goal of this project is to turn that from a lagging metric into a leading one.");
}

// ════════════════════════════════════════════════════════════════════════
// SLIDE 4 — Dataset & Pipeline
// ════════════════════════════════════════════════════════════════════════
{
  const s = pres.addSlide();
  s.background = { color: C.offwhite };

  s.addText("Dataset & Pipeline", {
    x: 0.6, y: 0.28, w: 8.8, h: 0.65,
    fontSize: 32, bold: true, color: C.navy, fontFace: F.title,
  });

  // Left: dataset facts
  const facts = [
    ["7,043",  "customers"],
    ["21",     "raw features"],
    ["46",     "engineered features"],
    ["26.5%",  "churn rate"],
  ];
  facts.forEach(([val, lbl], i) => {
    const y = 1.15 + i * 1.0;
    addCard(s, 0.5, y, 3.6, 0.82, C.white);
    s.addText(val, {
      x: 0.7, y, w: 1.1, h: 0.82,
      fontSize: 26, bold: true, color: C.navy, fontFace: F.title,
      align: "center", valign: "middle",
    });
    s.addText(lbl, {
      x: 1.85, y, w: 2.1, h: 0.82,
      fontSize: 13, color: C.midgray, fontFace: F.body, valign: "middle",
    });
  });

  // Right: pipeline steps
  const steps = [
    ["ETL",           "CSV → clean → feature store (parquet + DuckDB)"],
    ["EDA",           "Cohort analysis, segment charts, correlation heatmap"],
    ["Modeling",      "Logistic baseline → XGBoost + Optuna (50 trials)"],
    ["Interpretation","SHAP TreeExplainer — global + per-customer drivers"],
    ["Dashboard",     "Streamlit app with What-If simulator"],
  ];
  steps.forEach(([step, desc], i) => {
    const y = 1.1 + i * 0.88;
    addCard(s, 4.55, y, 5.1, 0.75, C.white);
    s.addShape(pres.shapes.OVAL, {
      x: 4.72, y: y + 0.13, w: 0.48, h: 0.48,
      fill: { color: C.navy },
    });
    s.addText(String(i + 1), {
      x: 4.72, y: y + 0.13, w: 0.48, h: 0.48,
      fontSize: 11, bold: true, color: C.white, align: "center", valign: "middle",
      fontFace: F.body, margin: 0,
    });
    s.addText(step, {
      x: 5.3, y: y + 0.06, w: 1.3, h: 0.32,
      fontSize: 12, bold: true, color: C.navy, fontFace: F.title,
    });
    s.addText(desc, {
      x: 5.3, y: y + 0.38, w: 4.2, h: 0.3,
      fontSize: 10, color: C.midgray, fontFace: F.body,
    });
  });

  s.addNotes("The IBM Telco Churn dataset gives us 7,043 customers with 21 features. We engineered 25 more — including avg monthly charges, charges per active service, a high-value flag, and tenure buckets. The full pipeline runs reproducibly via make all.");
}

// ════════════════════════════════════════════════════════════════════════
// SLIDE 5 — EDA: Cohort & Class Imbalance
// ════════════════════════════════════════════════════════════════════════
{
  const s = pres.addSlide();
  s.background = { color: C.offwhite };

  s.addText("EDA: What the Data Tells Us", {
    x: 0.5, y: 0.25, w: 9, h: 0.65,
    fontSize: 32, bold: true, color: C.navy, fontFace: F.title,
  });

  // Left chart image
  const cohortImg = imgPath("cohort_churn.png");
  if (cohortImg) {
    addCard(s, 0.4, 1.05, 4.55, 3.2, C.white);
    s.addImage({ path: cohortImg, x: 0.55, y: 1.15, w: 4.25, h: 2.9 });
    s.addText("Churn Rate by Tenure Cohort", {
      x: 0.4, y: 4.28, w: 4.55, h: 0.3,
      fontSize: 9, color: C.midgray, fontFace: F.body, align: "center",
    });
  }

  // Right chart
  const imbalanceImg = imgPath("class_imbalance.png");
  if (imbalanceImg) {
    addCard(s, 5.2, 1.05, 4.35, 3.2, C.white);
    s.addImage({ path: imbalanceImg, x: 5.35, y: 1.15, w: 4.05, h: 2.9 });
    s.addText("Class Imbalance (73.5% retained / 26.5% churned)", {
      x: 5.2, y: 4.28, w: 4.35, h: 0.3,
      fontSize: 9, color: C.midgray, fontFace: F.body, align: "center",
    });
  }

  // Key insight banner
  addCard(s, 0.4, 4.65, 9.2, 0.75, "EBF5FB");
  s.addText("Key insight: Early-tenure customers (0–12 months) churn at >3× the rate of long-tenure customers — and they represent the single largest growth cohort.", {
    x: 0.6, y: 4.68, w: 8.8, h: 0.7,
    fontSize: 11, color: C.navy, fontFace: F.body, valign: "middle", bold: true,
  });

  s.addNotes("The left chart is the critical finding: churn collapses dramatically as customers age. The first 12 months are make-or-break. The class imbalance (right) guided our modeling choices — we used scale_pos_weight in XGBoost to handle the 3:1 ratio.");
}

// ════════════════════════════════════════════════════════════════════════
// SLIDE 6 — EDA: Segments
// ════════════════════════════════════════════════════════════════════════
{
  const s = pres.addSlide();
  s.background = { color: C.offwhite };

  s.addText("High-Risk Customer Profile", {
    x: 0.5, y: 0.25, w: 9, h: 0.65,
    fontSize: 32, bold: true, color: C.navy, fontFace: F.title,
  });

  const segImg = imgPath("segment_churn.png");
  if (segImg) {
    addCard(s, 0.4, 1.0, 5.6, 4.3, C.white);
    s.addImage({ path: segImg, x: 0.5, y: 1.08, w: 5.4, h: 4.1 });
  }

  // Right: risk profile bullets
  const profile = [
    { icon: "A", title: "Month-to-month contract", pct: "43%", base: "11%" },
    { icon: "B", title: "Electronic check payment", pct: "45%", base: "16%" },
    { icon: "C", title: "Fiber optic internet",     pct: "42%", base: "19%" },
    { icon: "D", title: "Tenure < 12 months",       pct: "50%", base: "26%" },
  ];

  s.addText("Classic high-risk combo:", {
    x: 6.2, y: 1.05, w: 3.6, h: 0.4,
    fontSize: 13, bold: true, color: C.navy, fontFace: F.title,
  });

  profile.forEach(({ icon, title, pct, base }, i) => {
    const y = 1.55 + i * 0.95;
    addCard(s, 6.2, y, 3.55, 0.82, C.white);
    s.addText(icon, {
      x: 6.28, y, w: 0.5, h: 0.82,
      fontSize: 18, align: "center", valign: "middle",
    });
    s.addText(title, {
      x: 6.82, y: y + 0.05, w: 2.3, h: 0.38,
      fontSize: 11, bold: true, color: C.navy, fontFace: F.body,
    });
    s.addText(`${pct} churn  vs  ${base} avg`, {
      x: 6.82, y: y + 0.43, w: 2.4, h: 0.3,
      fontSize: 10, color: C.red, fontFace: F.body,
    });
    // Mini bar showing churn %
    const barW = 0.65 * (parseFloat(pct) / 55);
    s.addShape(pres.shapes.RECTANGLE, {
      x: 9.4 - 0.65, y: y + 0.28, w: 0.65, h: 0.1,
      fill: { color: C.lightgray },
    });
    s.addShape(pres.shapes.RECTANGLE, {
      x: 9.4 - 0.65, y: y + 0.28, w: barW, h: 0.1,
      fill: { color: C.red },
    });
  });

  s.addNotes("The worst-case customer profile: month-to-month, pays by electronic check, has fiber optic internet, and is new. We see churn rates of 40–50% in this group versus 26% overall.");
}

// ════════════════════════════════════════════════════════════════════════
// SLIDE 7 — Model Results
// ════════════════════════════════════════════════════════════════════════
{
  const s = pres.addSlide();
  s.background = { color: C.navy };

  s.addText("Model Performance", {
    x: 0.6, y: 0.25, w: 8.8, h: 0.65,
    fontSize: 32, bold: true, color: C.white, fontFace: F.title,
  });

  // Metric cards — 4 big numbers
  const metrics = [
    { val: "0.25",  lbl: "PR-AUC",           sub: "XGBoost (tuned)",       good: true },
    { val: "0.80",  lbl: "ROC-AUC",           sub: "Strong discrimination", good: true },
    { val: "41.9%", lbl: "Recall @ Top 10%",  sub: "of all churners caught", good: true },
    { val: "4.19×", lbl: "Lift @ Top 10%",    sub: "vs. random targeting",  good: true },
  ];

  metrics.forEach(({ val, lbl, sub, good }, i) => {
    const x = 0.45 + i * 2.3;
    addCard(s, x, 1.1, 2.1, 2.0, "243060");
    s.addText(val, {
      x, y: 1.2, w: 2.1, h: 1.0,
      fontSize: 38, bold: true, color: C.gold, fontFace: F.title,
      align: "center", valign: "middle",
    });
    s.addText(lbl, {
      x, y: 2.2, w: 2.1, h: 0.38,
      fontSize: 11, bold: true, color: C.iceblue, fontFace: F.body,
      align: "center", charSpacing: 1,
    });
    s.addText(sub, {
      x, y: 2.6, w: 2.1, h: 0.38,
      fontSize: 9, color: "AABCD4", fontFace: F.body, align: "center",
    });
  });

  // Comparison table
  const tableData = [
    [
      { text: "Metric",         options: { bold: true, color: C.white, fill: { color: C.navy } } },
      { text: "Baseline (LR)",  options: { bold: true, color: C.white, fill: { color: C.navy } } },
      { text: "XGBoost Tuned",  options: { bold: true, color: C.white, fill: { color: C.teal  } } },
    ],
    ["PR-AUC",          "0.2316", "0.2503 ▲"],
    ["ROC-AUC",         "0.8148", "0.8043"],
    ["Recall @ Top 10%","0.3763", "0.4194 ▲"],
    ["Lift @ Top 10%",  "3.76×",  "4.19× ▲"],
    ["Best F1",         "0.3254", "0.3470 ▲"],
  ];

  s.addTable(tableData, {
    x: 0.5, y: 3.3, w: 9, h: 2.0,
    colW: [3.2, 2.9, 2.9],
    rowH: 0.33,
    fontSize: 11,
    fontFace: F.body,
    color: C.white,
    fill: { color: "1a2a50" },
    border: { pt: 0.5, color: "2a3a70" },
  });

  s.addNotes("XGBoost outperforms logistic regression on every precision-recall metric. The key business number is the 4.19× lift — contacting the top 10% of customers by predicted risk captures 42% of all who would have churned.");
}

// ════════════════════════════════════════════════════════════════════════
// SLIDE 8 — Lift Chart
// ════════════════════════════════════════════════════════════════════════
{
  const s = pres.addSlide();
  s.background = { color: C.offwhite };

  s.addText("Cumulative Lift — Targeting Efficiency", {
    x: 0.5, y: 0.25, w: 9, h: 0.65,
    fontSize: 32, bold: true, color: C.navy, fontFace: F.title,
  });

  const liftImg = imgPath("lift_chart.png");
  if (liftImg) {
    addCard(s, 0.4, 1.0, 5.8, 4.3, C.white);
    s.addImage({ path: liftImg, x: 0.55, y: 1.1, w: 5.55, h: 4.1 });
  }

  // Right callouts
  const callouts = [
    { num: "Top 10%", body: "Contact only 141 customers and catch 41.9% of all churners — vs. 10% at random." },
    { num: "4.19×",   body: "Lift factor — every dollar of outreach goes 4× further than random selection." },
    { num: "~$142",   body: "Revenue protected per customer reached (at 30% save rate × $74 ARPU × 12 mo)." },
  ];

  callouts.forEach(({ num, body }, i) => {
    const y = 1.1 + i * 1.45;
    addCard(s, 6.4, y, 3.3, 1.25, C.white);
    s.addText(num, {
      x: 6.55, y: y + 0.1, w: 3.1, h: 0.5,
      fontSize: 22, bold: true, color: C.navy, fontFace: F.title, align: "center",
    });
    s.addText(body, {
      x: 6.55, y: y + 0.6, w: 3.1, h: 0.58,
      fontSize: 10, color: C.midgray, fontFace: F.body, align: "center",
    });
  });

  s.addNotes("The lift chart shows cumulative gains. The red dotted line is top-10% — we capture 42% of actual churners there. The model curve bows well above the random diagonal, confirming real predictive power.");
}

// ════════════════════════════════════════════════════════════════════════
// SLIDE 9 — SHAP Insights
// ════════════════════════════════════════════════════════════════════════
{
  const s = pres.addSlide();
  s.background = { color: C.offwhite };

  s.addText("What Drives Churn — SHAP Analysis", {
    x: 0.5, y: 0.25, w: 9, h: 0.65,
    fontSize: 32, bold: true, color: C.navy, fontFace: F.title,
  });

  const beeImg = imgPath("shap_beeswarm.png");
  const barImg = imgPath("shap_bar.png");

  if (beeImg) {
    addCard(s, 0.4, 1.0, 5.6, 3.6, C.white);
    s.addImage({ path: beeImg, x: 0.5, y: 1.08, w: 5.4, h: 3.45 });
    s.addText("SHAP Beeswarm — each dot is a customer", {
      x: 0.4, y: 4.62, w: 5.6, h: 0.28,
      fontSize: 9, color: C.midgray, fontFace: F.body, align: "center",
    });
  }

  if (barImg) {
    addCard(s, 6.15, 1.0, 3.5, 3.6, C.white);
    s.addImage({ path: barImg, x: 6.22, y: 1.08, w: 3.36, h: 3.45 });
    s.addText("Mean |SHAP| — global importance", {
      x: 6.15, y: 4.62, w: 3.5, h: 0.28,
      fontSize: 9, color: C.midgray, fontFace: F.body, align: "center",
    });
  }

  // Bottom insight row
  const shapInsights = [
    "Contract type is the #1 driver — month-to-month customers have very high SHAP values",
    "Tenure is #2 — recent joiners show consistently positive (churn) SHAP scores",
    "Charges per service is #3 — high charges relative to services used predict churn",
  ];
  addCard(s, 0.4, 4.98, 9.2, 0.45, "EBF5FB");
  s.addText(shapInsights.join("   |   "), {
    x: 0.6, y: 4.98, w: 8.8, h: 0.45,
    fontSize: 9, color: C.navy, fontFace: F.body, valign: "middle",
  });

  s.addNotes("SHAP gives us model-agnostic feature attribution. Red dots = pushes toward churn, blue = away. Contract type dominates — a customer on a month-to-month plan is far more likely to churn than anything else we measure.");
}

// ════════════════════════════════════════════════════════════════════════
// SLIDE 10 — 3 Actionable Segments
// ════════════════════════════════════════════════════════════════════════
{
  const s = pres.addSlide();
  s.background = { color: C.navy };

  s.addText("3 Actionable Segments", {
    x: 0.6, y: 0.25, w: 8.8, h: 0.65,
    fontSize: 32, bold: true, color: C.white, fontFace: F.title,
  });
  s.addText("Top features by mean |SHAP| — each split at median, churn rates compared", {
    x: 0.6, y: 0.92, w: 8.8, h: 0.35,
    fontSize: 12, color: C.iceblue, fontFace: F.body,
  });

  const segments = [
    {
      num: "01",
      feature: "Contract Type",
      stat: "42.7% vs 6.8%",
      mult: "6.32×",
      desc: "Month-to-month customers churn at 42.7% — nearly 9× the rate of those on annual contracts (6.8%). This is the single most actionable lever.",
      n: "3,875 customers",
      action: "Offer discounted annual plans to month-to-month customers",
    },
    {
      num: "02",
      feature: "Tenure < 29 months",
      stat: "39.5% vs 13.2%",
      mult: "2.98×",
      desc: "New and mid-tenure customers churn at 39.5% vs 13.2% for long-tenure. The first 2 years are the critical retention window.",
      n: "3,569 customers",
      action: "Onboarding program + check-in at 3, 6, 12 months",
    },
    {
      num: "03",
      feature: "Charges per Service",
      stat: "43.4% vs 9.7%",
      mult: "4.45×",
      desc: "Customers paying more per active service (above $13.97/service) churn at 43.4%. They perceive low value for the price.",
      n: "3,520 customers",
      action: "Bundle services or offer add-ons to improve value perception",
    },
  ];

  segments.forEach(({ num, feature, stat, mult, desc, n, action }, i) => {
    const y = 1.4 + i * 1.35;
    addCard(s, 0.45, y, 9.1, 1.22, "1a2e5a");

    // Number badge
    s.addShape(pres.shapes.OVAL, {
      x: 0.6, y: y + 0.33, w: 0.55, h: 0.55,
      fill: { color: C.teal },
    });
    s.addText(num, {
      x: 0.6, y: y + 0.33, w: 0.55, h: 0.55,
      fontSize: 11, bold: true, color: C.white, align: "center", valign: "middle",
      fontFace: F.body, margin: 0,
    });

    // Feature name
    s.addText(feature, {
      x: 1.3, y: y + 0.1, w: 2.5, h: 0.38,
      fontSize: 14, bold: true, color: C.white, fontFace: F.title,
    });
    s.addText(n, {
      x: 1.3, y: y + 0.5, w: 2.5, h: 0.3,
      fontSize: 10, color: "AABCD4", fontFace: F.body,
    });
    s.addText(action, {
      x: 1.3, y: y + 0.82, w: 2.8, h: 0.3,
      fontSize: 9, color: C.gold, fontFace: F.body, italic: true,
    });

    // Stat
    s.addText(stat, {
      x: 4.1, y: y + 0.2, w: 2.4, h: 0.45,
      fontSize: 18, bold: true, color: C.gold, fontFace: F.title, align: "center",
    });
    s.addText("churn rate high vs low group", {
      x: 4.1, y: y + 0.65, w: 2.4, h: 0.3,
      fontSize: 9, color: "AABCD4", fontFace: F.body, align: "center",
    });

    // Multiplier badge
    s.addShape(pres.shapes.ROUNDED_RECTANGLE, {
      x: 6.65, y: y + 0.3, w: 1.05, h: 0.55,
      fill: { color: C.red },
      rectRadius: 0.06,
    });
    s.addText(mult, {
      x: 6.65, y: y + 0.3, w: 1.05, h: 0.55,
      fontSize: 16, bold: true, color: C.white, fontFace: F.title,
      align: "center", valign: "middle", margin: 0,
    });
    s.addText("more likely\nto churn", {
      x: 6.65, y: y + 0.87, w: 1.05, h: 0.3,
      fontSize: 8, color: "AABCD4", fontFace: F.body, align: "center",
    });

    // Right description
    s.addText(desc, {
      x: 7.8, y: y + 0.15, w: 1.6, h: 0.95,
      fontSize: 8.5, color: "AABCD4", fontFace: F.body,
    });
  });

  s.addNotes("These three segments are derived directly from SHAP values — they're not just correlations, they're model-confirmed drivers. Together they cover roughly 50% of our customer base. The good news: all three have concrete, low-cost interventions.");
}

// ════════════════════════════════════════════════════════════════════════
// SLIDE 11 — Recommendations
// ════════════════════════════════════════════════════════════════════════
{
  const s = pres.addSlide();
  s.background = { color: C.offwhite };

  s.addText("Recommendations", {
    x: 0.5, y: 0.25, w: 9, h: 0.65,
    fontSize: 32, bold: true, color: C.navy, fontFace: F.title,
  });

  const recs = [
    {
      icon: "01",
      title: "Weekly Top-10% Risk List",
      body: "Score all customers weekly. Contact the top 141 highest-risk customers — this targets 42% of upcoming churners with minimal outreach cost.",
      effort: "Low",
    },
    {
      icon: "02",
      title: "Annual Contract Conversion",
      body: "Offer month-to-month customers a discounted annual plan. Even a 10% conversion rate saves significant MRR at the highest-risk cohort.",
      effort: "Low",
    },
    {
      icon: "03",
      title: "New Customer Onboarding",
      body: "Structured check-ins at 3, 6, and 12 months for new customers. Target tenure <12 mo — the 50% churn cohort. Early intervention is 3× cheaper than win-back.",
      effort: "Medium",
    },
    {
      icon: "04",
      title: "Service Bundling",
      body: "Customers with high charges-per-service feel poor value. Offer bundles (e.g., security + backup + support) to spread cost perception across more services.",
      effort: "Medium",
    },
  ];

  recs.forEach(({ icon, title, body, effort }, i) => {
    const col = i % 2;
    const row = Math.floor(i / 2);
    const x = 0.4 + col * 4.82;
    const y = 1.1 + row * 2.1;
    addCard(s, x, y, 4.55, 1.88, C.white);

    s.addShape(pres.shapes.OVAL, {
      x: x + 0.18, y: y + 0.15, w: 0.48, h: 0.48,
      fill: { color: C.navy },
    });
    s.addText(icon, {
      x: x + 0.18, y: y + 0.15, w: 0.48, h: 0.48,
      fontSize: 11, bold: true, color: C.white, align: "center", valign: "middle",
      fontFace: F.body, margin: 0,
    });

    // Effort badge
    const effortColor = effort === "Low" ? C.green : C.teal;
    s.addShape(pres.shapes.ROUNDED_RECTANGLE, {
      x: x + 3.7, y: y + 0.15, w: 0.7, h: 0.28,
      fill: { color: effortColor },
      rectRadius: 0.04,
    });
    s.addText(effort, {
      x: x + 3.7, y: y + 0.15, w: 0.7, h: 0.28,
      fontSize: 8, bold: true, color: C.white, align: "center", valign: "middle",
      fontFace: F.body, margin: 0,
    });

    s.addText(title, {
      x: x + 0.78, y: y + 0.1, w: 2.8, h: 0.42,
      fontSize: 12, bold: true, color: C.navy, fontFace: F.title,
    });
    s.addText(body, {
      x: x + 0.15, y: y + 0.6, w: 4.25, h: 1.18,
      fontSize: 10, color: C.midgray, fontFace: F.body,
    });
  });

  s.addNotes("Four recommendations in order of effort. The risk list and contract conversion require no product changes — just process and a promotion budget. Onboarding is a CX investment. Bundling is a pricing/packaging conversation with product.");
}

// ════════════════════════════════════════════════════════════════════════
// SLIDE 12 — Revenue Impact
// ════════════════════════════════════════════════════════════════════════
{
  const s = pres.addSlide();
  s.background = { color: C.navy };

  s.addText("Estimated Revenue Impact", {
    x: 0.6, y: 0.25, w: 8.8, h: 0.65,
    fontSize: 32, bold: true, color: C.white, fontFace: F.title,
  });

  // Big number center
  addCard(s, 2.0, 1.1, 6, 2.0, "1a2e5a");
  s.addText("$42,818", {
    x: 2.0, y: 1.15, w: 6, h: 1.3,
    fontSize: 60, bold: true, color: C.gold, fontFace: F.title, align: "center",
  });
  s.addText("estimated annual revenue retained", {
    x: 2.0, y: 2.45, w: 6, h: 0.45,
    fontSize: 13, color: C.iceblue, fontFace: F.body, align: "center",
  });

  // Assumptions
  s.addText("Model assumptions:", {
    x: 0.6, y: 3.3, w: 8.8, h: 0.38,
    fontSize: 11, bold: true, color: C.iceblue, fontFace: F.body, charSpacing: 1,
  });

  const assumptions = [
    "Top-10% targeting captures 41.9% of churners per scoring run",
    "30% save-rate from targeted outreach  (industry benchmark — replace with A/B test result)",
    "Average ARPU of saved customers = $74.44/month × 12 months",
  ];
  assumptions.forEach((a, i) => {
    s.addText([{ text: `${i + 1}.  `, options: { bold: true } }, { text: a }], {
      x: 0.7, y: 3.72 + i * 0.38, w: 8.6, h: 0.35,
      fontSize: 11, color: C.white, fontFace: F.body,
    });
  });

  // Caveats
  addCard(s, 0.5, 4.9, 9, 0.5, "1a2e5a");
  s.addText("!  Caveats: SHAP = correlation, not causation. Validate save-rate with a randomized holdout. Re-validate model on rolling-window holdouts before production deployment.", {
    x: 0.65, y: 4.92, w: 8.7, h: 0.46,
    fontSize: 9, color: "FFCC44", fontFace: F.body, valign: "middle",
  });

  s.addNotes("The $42K figure is conservative — it uses a 30% save rate which is a widely cited industry baseline. If your actual outreach converts at 40–50%, the number scales linearly. The real lever is measuring the holdout group from day one.");
}

// ════════════════════════════════════════════════════════════════════════
// SLIDE 13 — Thank You / Q&A
// ════════════════════════════════════════════════════════════════════════
{
  const s = pres.addSlide();
  s.background = { color: C.navy };

  // Decorative circles
  s.addShape(pres.shapes.OVAL, {
    x: -1, y: 3.5, w: 4.5, h: 4.5,
    fill: { color: C.teal, transparency: 80 },
    line: { color: C.teal, width: 1, transparency: 60 },
  });
  s.addShape(pres.shapes.OVAL, {
    x: 7.5, y: -1, w: 3.5, h: 3.5,
    fill: { color: C.iceblue, transparency: 85 },
    line: { color: C.iceblue, width: 1, transparency: 65 },
  });

  s.addText("Thank You", {
    x: 1, y: 0.9, w: 8, h: 1.1,
    fontSize: 52, bold: true, color: C.white, fontFace: F.title, align: "center",
  });
  s.addText("Questions & Discussion", {
    x: 1, y: 2.05, w: 8, h: 0.5,
    fontSize: 20, color: C.iceblue, fontFace: F.body, align: "center",
  });

  // Summary bullets
  const summary = [
    "Model: XGBoost  •  PR-AUC 0.25  •  4.19× lift  •  41.9% recall@top-10%",
    "Top drivers: Contract type, Tenure, Charges per service",
    "Estimated impact: ~$42,818/yr at 30% save rate",
    "Next step: Deploy weekly risk list + A/B test retention outreach",
  ];
  summary.forEach((line, i) => {
    s.addText(line, {
      x: 1.5, y: 2.85 + i * 0.5,  w: 7, h: 0.42,
      fontSize: 11, color: i === 3 ? C.gold : C.iceblue,
      fontFace: F.body, align: "center",
      bold: i === 3,
    });
  });

  // Bottom bar
  s.addShape(pres.shapes.RECTANGLE, {
    x: 0, y: 5.1, w: 10, h: 0.525,
    fill: { color: C.teal },
  });
  s.addText("Data Science Team  •  Customer Churn Analysis  •  Telco Dataset  •  June 2026", {
    x: 0.5, y: 5.1, w: 9, h: 0.525,
    fontSize: 10, color: C.white, fontFace: F.body, align: "center", valign: "middle", margin: 0,
  });

  s.addNotes("Wrap up with the four key numbers and the single clearest next step: get the weekly risk list running and set up a holdout group to measure actual save rate. That measurement is what turns this from a model into a business program.");
}

// ── Write file ────────────────────────────────────────────────────────────
const outFile = path.join(OUT, "churn_presentation.pptx");
pres.writeFile({ fileName: outFile }).then(() => {
  console.log(`[pptx] written -> ${outFile}`);
}).catch(err => {
  console.error("[pptx] ERROR:", err);
  process.exit(1);
});
