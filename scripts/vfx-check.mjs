// Vérif rapide des animations vectorielles : erreurs console, débordement horizontal, captures.
// Usage : node scripts/vfx-check.mjs http://localhost:4175/ /tmp/vfx
import { chromium } from "playwright-core";
import { mkdirSync } from "node:fs";

const url = process.argv[2] || "http://localhost:4175/";
const out = process.argv[3] || "/tmp/vfx";
mkdirSync(out, { recursive: true });
const browser = await chromium.launch({ channel: "chrome" });
let fail = 0;
for (const w of [1440, 390]) {
  const page = await browser.newPage({ viewport: { width: w, height: w > 500 ? 900 : 844 } });
  const errs = [];
  page.on("pageerror", e => errs.push(String(e)));
  page.on("console", m => m.type() === "error" && errs.push(m.text()));
  await page.goto(url, { waitUntil: "networkidle" });
  await page.waitForTimeout(1500);
  await page.screenshot({ path: `${out}/hero-${w}.jpg`, quality: 70 });
  const info = await page.evaluate(() => ({
    overflow: document.documentElement.scrollWidth - innerWidth,
    birds: document.querySelectorAll(".vfx-hero .bird").length,
    glyphs: document.querySelectorAll(".chap .glyph").length,
    anim: getComputedStyle(document.querySelector(".mill .spin")).animationName,
  }));
  for (const sel of ["#gamme", "#moulin", "#tireuses"]) {
    await page.locator(sel).scrollIntoViewIfNeeded();
    await page.evaluate(s => document.querySelector(s).scrollIntoView(), sel);
    await page.waitForTimeout(2600);
    await page.screenshot({ path: `${out}${sel.replace("#", "/")}-${w}.jpg`, quality: 70 });
  }
  const ridgeDrawn = await page.evaluate(() => [...document.querySelectorAll(".ridge .rg-line")].every(p => !p.style.strokeDashoffset || p.style.strokeDashoffset === "0px" || p.style.strokeDashoffset === "0"));
  console.log(w, JSON.stringify({ ...info, ridgeDrawn, errors: errs }));
  if (info.overflow > 0 || errs.length || info.glyphs !== 9 || !ridgeDrawn) fail = 1;
  await page.close();
}
await browser.close();
console.log(fail ? "VFX CHECK FAIL" : "VFX CHECK PASS");
process.exit(fail);
