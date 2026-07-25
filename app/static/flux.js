/* /flux — le bassin versant des grandes masses.
 *
 * Les lacs sont les stocks (leur aire dit combien), les rivières les débits
 * (leur largeur dit le débit, les particules le sens du courant). Le scénario
 * « Aujourd'hui » est calculé côté serveur depuis nos données ; les trois autres
 * sont pédagogiques et le disent.
 */
(function () {
  "use strict";

  const NS = "http://www.w3.org/2000/svg";
  const svg = document.getElementById("bassin");
  const data = JSON.parse(document.getElementById("bassin-data").textContent);
  const sobre = window.matchMedia("(prefers-reduced-motion: reduce)").matches;

  const LACS = data.lacs;
  const RIVIERES = data.rivieres.map(r => Object.assign({}, r));
  const SCENARIOS = data.scenarios;

  const parId = {};
  LACS.forEach(l => { parId[l.id] = l; l.r = Math.max(12, 3.2 * Math.sqrt(l.stock)); });

  const nf = (v, d) => v.toLocaleString("fr-FR", { minimumFractionDigits: d, maximumFractionDigits: d });
  const fmtStock = v => nf(v, v < 10 ? 1 : 0);
  const fmtDebit = v => nf(Math.round(v * 10) / 10, 1);
  const fmtDate = iso => iso.split("-").reverse().join("/");
  const largeur = f => 2.5 + 9 * Math.sqrt(Math.abs(f));

  function el(nom, attrs, parent) {
    const e = document.createElementNS(NS, nom);
    for (const k in attrs) e.setAttribute(k, attrs[k]);
    if (parent) parent.appendChild(e);
    return e;
  }

  /* générateur pseudo-aléatoire à graine : la forme des lacs doit rester stable */
  function mulberry32(a) {
    return function () {
      a |= 0; a = (a + 0x6D2B79F5) | 0;
      let t = Math.imul(a ^ (a >>> 15), 1 | a);
      t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t;
      return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
    };
  }

  /* contour organique du lac — un cercle serait un camembert, un blob est un lac */
  function blobPath(cx, cy, r, graine) {
    const rnd = mulberry32(graine);
    const n = 10, pts = [];
    for (let i = 0; i < n; i++) {
      const a = (i / n) * Math.PI * 2;
      const rr = r * (1 + 0.16 * (rnd() - 0.5));
      pts.push([cx + Math.cos(a) * rr, cy + Math.sin(a) * rr]);
    }
    let d = "";
    for (let i = 0; i < n; i++) {
      const p0 = pts[(i - 1 + n) % n], p1 = pts[i], p2 = pts[(i + 1) % n], p3 = pts[(i + 2) % n];
      const c1 = [p1[0] + (p2[0] - p0[0]) / 6, p1[1] + (p2[1] - p0[1]) / 6];
      const c2 = [p2[0] - (p3[0] - p1[0]) / 6, p2[1] - (p3[1] - p1[1]) / 6];
      if (i === 0) d += `M ${p1[0].toFixed(1)} ${p1[1].toFixed(1)} `;
      d += `C ${c1[0].toFixed(1)} ${c1[1].toFixed(1)} ${c2[0].toFixed(1)} ${c2[1].toFixed(1)} ${p2[0].toFixed(1)} ${p2[1].toFixed(1)} `;
    }
    return d + "Z";
  }

  /* points d'accroche répartis sur le bord du lac, triés pour éviter les croisements */
  const ETALEMENT = 0.85;
  function ancrages() {
    LACS.forEach(l => { l.sortantes = []; l.entrantes = []; });
    RIVIERES.forEach(rv => { parId[rv.de].sortantes.push(rv); parId[rv.vers].entrantes.push(rv); });
    LACS.forEach(l => {
      l.sortantes.sort((a, b) => parId[a.vers].y - parId[b.vers].y);
      l.sortantes.forEach((rv, i) => {
        const f = l.sortantes.length === 1 ? 0.5 : i / (l.sortantes.length - 1);
        const a = -ETALEMENT + f * 2 * ETALEMENT;
        rv.p1 = [l.x + Math.cos(a) * l.r * 0.95, l.y + Math.sin(a) * l.r * 0.95];
      });
      l.entrantes.sort((a, b) => parId[a.de].y - parId[b.de].y);
      l.entrantes.forEach((rv, i) => {
        const f = l.entrantes.length === 1 ? 0.5 : i / (l.entrantes.length - 1);
        const a = Math.PI + ETALEMENT - f * 2 * ETALEMENT;
        rv.p2 = [l.x + Math.cos(a) * l.r * 0.95, l.y + Math.sin(a) * l.r * 0.95];
      });
    });
  }

  function traceRiviere(rv) {
    const [x1, y1] = rv.p1, [x2, y2] = rv.p2;
    const dx = x2 - x1, courbe = rv.courbe || 0;
    return `M ${x1} ${y1} C ${x1 + dx * 0.4} ${y1 + courbe}, ${x2 - dx * 0.4} ${y2 + courbe}, ${x2} ${y2}`;
  }

  /* échantillonnage du tracé : anime les particules sans getPointAtLength à chaque image */
  function echantillonne(d) {
    const tmp = el("path", { d });
    svg.appendChild(tmp);
    const len = tmp.getTotalLength();
    const pas = 6, pts = [];
    for (let s = 0; s <= len; s += pas) {
      const p = tmp.getPointAtLength(s);
      pts.push([p.x, p.y]);
    }
    svg.removeChild(tmp);
    const normales = pts.map((p, i) => {
      const a = pts[Math.max(0, i - 1)], b = pts[Math.min(pts.length - 1, i + 1)];
      const dx = b[0] - a[0], dy = b[1] - a[1], n = Math.hypot(dx, dy) || 1;
      return [-dy / n, dx / n];
    });
    return { len, pas, pts, normales };
  }

  /* ---------- construction de la scène ---------- */

  ancrages();

  const gLits = el("g", {}, svg);
  const gChenaux = el("g", {}, svg);
  const gParticules = el("g", {}, svg);
  const gLacs = el("g", {}, svg);
  const gEtiquettes = el("g", {}, svg);
  const gSurvol = el("g", {}, svg);

  [["Les sources", 150], ["Les collecteurs", 500], ["Les mers d’actifs", 980]].forEach(([t, x]) => {
    el("text", { x, y: 34, "text-anchor": "middle", class: "col-titre" }, gEtiquettes).textContent = t;
  });

  RIVIERES.forEach(rv => {
    rv.cur = rv.base; rv.cible = rv.base;
    rv.d = traceRiviere(rv);
    rv.geom = echantillonne(rv.d);
    const col = `var(--${rv.couleur})`;
    rv.lit = el("path", { d: rv.d, fill: "none", "stroke-linecap": "round", opacity: 0.14 }, gLits);
    rv.lit.style.stroke = col;
    rv.chenal = el("path", { d: rv.d, fill: "none", "stroke-linecap": "round", opacity: 0.42 }, gChenaux);
    rv.chenal.style.stroke = col;
    rv.groupe = el("g", {}, gParticules);
    rv.particules = [];
    rv.chevrons = el("g", {}, gParticules);
    rv.survol = el("path", { d: rv.d, fill: "none", stroke: "rgba(0,0,0,0)", "stroke-width": 26 }, gSurvol);
    rv.survol.style.cursor = "help";
    rv.survol.addEventListener("pointermove", ev => montreBulle(ev, bulleRiviere(rv)));
    rv.survol.addEventListener("pointerleave", cacheBulle);
  });

  LACS.forEach((l, i) => {
    const col = `var(--${l.couleur})`;
    l.blob = el("path", { d: blobPath(l.x, l.y, l.r, 100 + i * 7) }, gLacs);
    l.blob.style.fill = col;
    l.blob.style.opacity = l.etage === "mers" ? 0.38 : 0.45;
    l.blob.style.stroke = col;
    l.blob.style.strokeWidth = 1.6;
    l.blob.style.cursor = "help";
    l.blob.addEventListener("pointermove", ev => montreBulle(ev, bulleLac(l)));
    l.blob.addEventListener("pointerleave", cacheBulle);

    /* la part que notre base mesure vraiment : un cœur éclairé dans l'estimation,
       cerné de la couleur du fond pour que les deux surfaces ne se touchent pas */
    if (l.part_mesuree && l.part_mesuree.stock > 0) {
      const rm = Math.max(5, l.r * Math.sqrt(Math.min(1, l.part_mesuree.stock / l.stock)));
      const anneau = el("path", { d: blobPath(l.x, l.y, rm + 2, 400 + i * 7) }, gLacs);
      anneau.style.fill = "var(--surface)";
      const coeur = el("path", { d: blobPath(l.x, l.y, rm, 400 + i * 7) }, gLacs);
      coeur.style.fill = "var(--brass)";
      coeur.style.opacity = 0.85;
      coeur.style.cursor = "help";
      coeur.addEventListener("pointermove", ev => montreBulle(ev, bulleLac(l)));
      coeur.addEventListener("pointerleave", cacheBulle);
    }

    /* étiquette directe sur chaque lac : l'identité ne repose jamais sur la couleur seule.
       Un lac qui porte un cœur mesuré passe son étiquette dessous : le cœur occupe le centre. */
    const dedans = l.r >= 34 && l.etage !== "mers" && !l.part_mesuree;
    let tx = l.x, ty, ancre = "middle";
    if (dedans) { ty = l.y - 3; }
    else if (l.etage === "mers") { tx = l.x + l.r + 10; ty = l.y + 1; ancre = "start"; }
    else { ty = l.y + l.r + 16; }
    el("text", { x: tx, y: ty, "text-anchor": ancre, class: "lac-nom" }, gEtiquettes).textContent = l.nom;
    const val = el("text", { x: tx, y: ty + 15, "text-anchor": ancre, class: "lac-val" }, gEtiquettes);
    val.textContent = `${l.provenance === "mesure" ? "" : "≈ "}${fmtStock(l.stock)} T$`;
    if (l.part_mesuree) {
      const mes = el("text", { x: tx, y: ty + 29, "text-anchor": ancre, class: "lac-mesure" }, gEtiquettes);
      mes.textContent = `dont ${fmtStock(l.part_mesuree.stock)} T$ mesurés`;
    }
  });

  /* ---------- bulles ---------- */

  const bulle = document.getElementById("tooltip");
  const ETIQUETTE = { mesure: "mesuré", documente: "ordre de grandeur documenté", lu: "lu dans les cours" };

  function bulleLac(l) {
    let html = `<strong>${l.nom}</strong><br>${l.provenance === "mesure" ? "" : "≈ "}${fmtStock(l.stock)} T$ ` +
               `<em>(${ETIQUETTE[l.provenance]})</em>`;
    if (l.mesure) html += `<br>${l.mesure.detail} — au ${fmtDate(l.mesure.date)}`;
    else html += `<br>${l.source}`;
    if (l.part_mesuree) {
      html += `<br><br><strong>${fmtStock(l.part_mesuree.stock)} T$ mesurés</strong> par notre base : ` +
              `${l.part_mesuree.detail}, au ${fmtDate(l.part_mesuree.date)}.`;
    }
    return html + `<br><br>${l.note}`;
  }

  function bulleRiviere(rv) {
    const f = rv.cur, de = parId[rv.de].nom, vers = parId[rv.vers].nom;
    const sens = f < -0.02 ? `<strong>${vers} → ${de}</strong><br>Rivière inversée — l’argent en sort`
                           : `<strong>${de} → ${vers}</strong>`;
    return `${sens} : ≈ ${fmtDebit(Math.abs(f))} T$/an <em>(débit illustratif)</em>` +
           `<br>Seule la largeur relative est pilotée par les données du scénario en cours.`;
  }

  function montreBulle(ev, html) {
    bulle.innerHTML = html;
    bulle.classList.add("on");
    const marge = 14;
    let x = ev.clientX + marge, y = ev.clientY + marge;
    const r = bulle.getBoundingClientRect();
    if (x + r.width > window.innerWidth - 8) x = ev.clientX - r.width - marge;
    if (y + r.height > window.innerHeight - 8) y = ev.clientY - r.height - marge;
    bulle.style.left = x + "px"; bulle.style.top = y + "px";
  }
  function cacheBulle() { bulle.classList.remove("on"); }

  /* ---------- légende ---------- */

  const LEGENDE = [
    ["flux-neutre", "Épargne en route (pas encore investie)"],
    ["c-actions", "Actions"], ["c-oblig", "Obligations"], ["c-or", "Or"],
    ["c-crypto", "Bitcoin"], ["c-mone", "Monétaire"],
  ];
  document.getElementById("legende").innerHTML =
    LEGENDE.map(([c, t]) => `<span class="chip"><span class="swatch" style="background:var(--${c})"></span>${t}</span>`).join("") +
    `<span class="chip"><span class="puce" style="background:var(--brass)"></span>Part réellement mesurée par notre base</span>`;

  /* ---------- particules ---------- */

  function refaisParticules(rv) {
    rv.groupe.textContent = "";
    rv.particules = [];
    if (sobre) return;
    const f = Math.abs(rv.cible);
    if (f < 0.03) return;
    const n = Math.max(2, Math.min(36, Math.round(rv.geom.len / 34 * (0.4 + Math.min(f, 5) / 2.2))));
    const rnd = mulberry32(rv.id.length * 1013 + Math.round(rv.geom.len));
    const w = largeur(rv.cible);
    for (let i = 0; i < n; i++) {
      const c = el("circle", { r: (1.1 + rnd() * 1.2).toFixed(2), opacity: 0.85 }, rv.groupe);
      c.style.fill = `var(--${rv.couleur})`;
      rv.particules.push({
        el: c,
        s: rnd() * rv.geom.len,
        lat: (rnd() - 0.5) * w * 0.7,
        v: 40 + 26 * Math.sqrt(f) * (0.75 + rnd() * 0.5),
      });
    }
  }

  /* sans animation, le sens du courant doit rester lisible : des chevrons le portent */
  function dessineChevrons(rv) {
    rv.chevrons.textContent = "";
    if (!sobre) return;
    const sens = rv.cur < 0 ? -1 : 1;
    [0.3, 0.55, 0.8].forEach(t => {
      const i = Math.round((t * rv.geom.len) / rv.geom.pas);
      const p = rv.geom.pts[Math.min(i, rv.geom.pts.length - 1)];
      const nrm = rv.geom.normales[Math.min(i, rv.geom.normales.length - 1)];
      const tx = nrm[1] * sens, ty = -nrm[0] * sens;
      const s = 5 + largeur(rv.cur) * 0.25;
      const d = `M ${p[0] - tx * s - nrm[0] * s} ${p[1] - ty * s - nrm[1] * s} ` +
                `L ${p[0] + tx * s} ${p[1] + ty * s} ` +
                `L ${p[0] - tx * s + nrm[0] * s} ${p[1] - ty * s + nrm[1] * s}`;
      const c = el("path", { d, fill: "none", "stroke-width": 2.4, "stroke-linecap": "round" }, rv.chevrons);
      c.style.stroke = `var(--${rv.couleur})`;
    });
  }

  /* ---------- scénarios ---------- */

  const boutons = document.getElementById("scenarios");
  boutons.innerHTML = Object.entries(SCENARIOS).map(([cle, scn]) =>
    `<button data-scn="${cle}" type="button">${scn.label}` +
    `<span class="tag">${scn.nature === "donnees" ? "nos données" : "pédagogique"}</span></button>`
  ).join("");

  let actif = "aujourdhui";

  function appliqueScenario(cle) {
    actif = cle;
    const scn = SCENARIOS[cle];
    document.getElementById("scenario-note").innerHTML = scn.note;
    boutons.querySelectorAll("button").forEach(b => b.classList.toggle("active", b.dataset.scn === cle));
    RIVIERES.forEach(rv => {
      rv.cible = rv.base * (scn.mult[rv.id] !== undefined ? scn.mult[rv.id] : 1);
      refaisParticules(rv);
      if (sobre) rv.cur = rv.cible;
    });
    remplisTableau();
    if (sobre) { dessineLargeurs(); RIVIERES.forEach(dessineChevrons); }
  }

  function dessineLargeurs() {
    RIVIERES.forEach(rv => {
      const w = largeur(rv.cur) * Math.min(1, Math.abs(rv.cur) * 12 + 0.05);
      rv.lit.setAttribute("stroke-width", (w * 1.7).toFixed(2));
      rv.chenal.setAttribute("stroke-width", w.toFixed(2));
    });
  }

  function remplisTableau() {
    const lignes = RIVIERES.map(rv => {
      const f = rv.cible, de = parId[rv.de].nom, vers = parId[rv.vers].nom;
      const libelle = f < 0 ? `${vers} → ${de} <span class="source">(inversée)</span>` : `${de} → ${vers}`;
      return `<tr><td>${libelle}</td><td class="num">${fmtDebit(Math.abs(f))}</td></tr>`;
    }).join("");
    document.getElementById("table-rivieres").innerHTML =
      `<thead><tr><th>Rivière — ${SCENARIOS[actif].label}</th><th class="num">T$/an</th></tr></thead>` +
      `<tbody>${lignes}</tbody>`;
  }

  boutons.querySelectorAll("button").forEach(b =>
    b.addEventListener("click", () => appliqueScenario(b.dataset.scn)));

  /* ---------- boucle d'animation ---------- */

  let precedent = performance.now();
  function image(maintenant) {
    const dt = Math.min(0.05, (maintenant - precedent) / 1000);
    precedent = maintenant;
    RIVIERES.forEach(rv => {
      rv.cur += (rv.cible - rv.cur) * Math.min(1, dt * 2.4);
      const sens = rv.cur < 0 ? -1 : 1;
      const vitesse = Math.min(1, Math.abs(rv.cur) * 6 + 0.05);
      rv.particules.forEach(p => {
        p.s = (p.s + sens * p.v * vitesse * dt + rv.geom.len) % rv.geom.len;
        const i = Math.min(rv.geom.pts.length - 1, Math.round(p.s / rv.geom.pas));
        const pt = rv.geom.pts[i], nrm = rv.geom.normales[i];
        p.el.setAttribute("transform",
          `translate(${(pt[0] + nrm[0] * p.lat).toFixed(1)},${(pt[1] + nrm[1] * p.lat).toFixed(1)})`);
      });
    });
    dessineLargeurs();
    requestAnimationFrame(image);
  }

  const ancre = location.hash.replace("#", "");
  appliqueScenario(SCENARIOS[ancre] ? ancre : "aujourdhui");
  RIVIERES.forEach(rv => { rv.cur = rv.cible; });
  dessineLargeurs();
  if (!sobre) requestAnimationFrame(image);
})();
