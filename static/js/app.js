const state = {
  meta: null,
  filieres: [],
  dateLundi: null,
  filiereId: null,
  grille: {},
  stats: { cours: 0, avec_salle: 0, tronc_commun: 0 },
  editSlot: null,
  forceSave: false,
};

const $ = (sel, root = document) => root.querySelector(sel);
const $$ = (sel, root = document) => [...root.querySelectorAll(sel)];

async function api(url, options = {}) {
  const res = await fetch(url, {
    headers: { "Content-Type": "application/json", ...(options.headers || {}) },
    ...options,
  });
  const ct = res.headers.get("content-type") || "";
  if (ct.includes("application/json")) {
    const data = await res.json();
    if (!res.ok) {
      const err = new Error(data.error || "Erreur API");
      err.status = res.status;
      err.data = data;
      throw err;
    }
    return data;
  }
  if (!res.ok) throw new Error("Erreur serveur");
  return res;
}

function toast(msg, type = "ok") {
  const el = $("#toast");
  el.textContent = msg;
  el.className = `toast show ${type === "ok" ? "" : type}`.trim();
  clearTimeout(toast._t);
  toast._t = setTimeout(() => el.classList.remove("show"), 2800);
}

function toMonday(dateStr) {
  const d = new Date(dateStr + "T12:00:00");
  const day = d.getDay();
  const diff = day === 0 ? -6 : 1 - day;
  d.setDate(d.getDate() + diff);
  return d.toISOString().slice(0, 10);
}

function formatFr(iso) {
  const [y, m, d] = iso.split("-");
  return `${d}/${m}/${y}`;
}

function openModal(id) {
  const el = typeof id === "string" ? $(id) : id;
  if (!el) {
    toast("Fenêtre introuvable", "error");
    return;
  }
  try {
    if (typeof el.showModal === "function") {
      if (!el.open) el.showModal();
    } else {
      el.setAttribute("open", "");
    }
  } catch (err) {
    console.error(err);
    toast("Impossible d'ouvrir la fenêtre", "error");
  }
}

function closeModal(dialog) {
  if (!dialog) return;
  try {
    dialog.close();
  } catch (_) {
    dialog.removeAttribute("open");
  }
}

function bindCloseButtons() {
  $$("[data-close]").forEach((btn) => {
    btn.addEventListener("click", (e) => {
      e.preventDefault();
      closeModal(btn.closest("dialog"));
    });
  });
  $$("dialog").forEach((dlg) => {
    dlg.addEventListener("click", (e) => {
      if (e.target === dlg) dlg.close();
    });
  });
}

async function init() {
  bindCloseButtons();
  // Brancher les boutons immédiatement (même si l'API met du temps)
  wireEvents();

  try {
    state.meta = await api("/api/meta");
  } catch (err) {
    console.error(err);
    toast("Serveur inaccessible — rechargez la page", "error");
    return;
  }

  state.dateLundi = state.meta.semaine_courante;

  const annee = $("#sel-annee");
  annee.innerHTML = state.meta.annees.map((a) => `<option value="${a}">${a}</option>`).join("");
  annee.value = "L1";

  const etab = $("#sel-etab");
  etab.innerHTML = state.meta.etablissements
    .map((e) => `<option value="${e.nom}">${e.nom}</option>`)
    .join("");

  const type = $("#sel-type");
  type.innerHTML = state.meta.types_cours
    .map((t) => `<option value="${t.nom}">${t.nom}</option>`)
    .join("");

  $("#inp-semaine").value = state.dateLundi;
  $("#st-semaine").textContent = formatFr(state.dateLundi);

  await loadFilieres();
  buildScheduleSkeleton();
  await loadGrille();
}

function wireEvents() {
  $("#sel-annee").addEventListener("change", () => loadFilieres());
  $("#sel-etab").addEventListener("change", () => loadFilieres());
  $("#sel-filiere").addEventListener("change", async () => {
    state.filiereId = Number($("#sel-filiere").value) || null;
    await loadGrille();
  });

  $("#btn-prev").addEventListener("click", () => shiftWeek(-1));
  $("#btn-next").addEventListener("click", () => shiftWeek(1));
  $("#btn-today").addEventListener("click", async () => {
    state.dateLundi = state.meta.semaine_courante;
    $("#inp-semaine").value = state.dateLundi;
    await loadGrille();
  });
  $("#inp-semaine").addEventListener("change", async () => {
    state.dateLundi = toMonday($("#inp-semaine").value);
    $("#inp-semaine").value = state.dateLundi;
    await loadGrille();
  });

  $("#inp-search").addEventListener("input", () => renderGrille());

  $("#btn-allouer").addEventListener("click", allouerSalles);
  $("#btn-conflits").addEventListener("click", verifierConflits);
  $("#btn-export").addEventListener("click", () => exportPdf("all"));
  $("#btn-export-one").addEventListener("click", () => exportPdf("one"));
  $("#btn-reset").addEventListener("click", resetSemaine);
  $("#btn-copy").addEventListener("click", () => {
    const d = new Date(state.dateLundi + "T12:00:00");
    d.setDate(d.getDate() - 7);
    $("#copy-source").value = d.toISOString().slice(0, 10);
    openModal("#modal-copy");
  });

  $("#btn-salles").addEventListener("click", openSalles);
  $("#btn-effectifs").addEventListener("click", openEffectifs);
  $("#btn-filieres").addEventListener("click", openFilieres);
  $("#btn-help").addEventListener("click", () => openModal("#modal-help"));

  $("#btn-add-salle").addEventListener("click", addSalle);
  $("#form-filiere").addEventListener("submit", addFiliere);
  $("#form-copy").addEventListener("submit", copySemaine);
  $("#form-cours").addEventListener("submit", saveCours);
  $("#btn-clear-slot").addEventListener("click", clearSlot);

  $("#cours-tc").addEventListener("change", () => {
    $("#tc-panel").classList.toggle("hidden", !$("#cours-tc").checked);
  });

  $("#cours-matiere").addEventListener("change", loadEnseignants);
  $("#cours-matiere").addEventListener("blur", loadEnseignants);

  document.addEventListener("keydown", (e) => {
    if (e.target.matches("input, select, textarea")) return;
    if (e.key === "ArrowLeft") shiftWeek(-1);
    if (e.key === "ArrowRight") shiftWeek(1);
    if (e.key.toLowerCase() === "t") {
      state.dateLundi = state.meta.semaine_courante;
      $("#inp-semaine").value = state.dateLundi;
      loadGrille();
    }
    if (e.key === "/") {
      e.preventDefault();
      $("#inp-search").focus();
    }
  });
}

async function shiftWeek(dir) {
  const data = await api(`/api/semaine?date=${state.dateLundi}&dir=${dir > 0 ? "next" : "prev"}`);
  state.dateLundi = data.date_lundi;
  $("#inp-semaine").value = state.dateLundi;
  await loadGrille();
}

async function loadFilieres() {
  const annee = $("#sel-annee").value;
  const etab = $("#sel-etab").value;
  state.filieres = await api(`/api/filieres?annee=${encodeURIComponent(annee)}&etablissement=${encodeURIComponent(etab)}`);
  const sel = $("#sel-filiere");
  if (!state.filieres.length) {
    sel.innerHTML = `<option value="">Aucune filière</option>`;
    state.filiereId = null;
    state.grille = {};
    renderGrille();
    updateStats({ cours: 0, avec_salle: 0, tronc_commun: 0 });
    return;
  }
  sel.innerHTML = state.filieres
    .map((f) => `<option value="${f.id}">${f.nom} (${f.effectif})</option>`)
    .join("");
  const keep = state.filieres.find((f) => f.id === state.filiereId);
  state.filiereId = keep ? keep.id : state.filieres[0].id;
  sel.value = String(state.filiereId);
  await loadGrille();
}

function buildScheduleSkeleton() {
  const root = $("#schedule");
  const jours = state.meta.jours;
  const creneaux = state.meta.creneaux;
  root.innerHTML = "";
  root.appendChild(el("div", { class: "sched-corner", text: "Créneau" }));
  jours.forEach((j) => root.appendChild(el("div", { class: "sched-day", text: j })));

  creneaux.forEach((c) => {
    root.appendChild(el("div", { class: "sched-slot", text: c.label }));
    jours.forEach((j) => {
      const cell = el("div", {
        class: "cell",
        attrs: {
          tabindex: "0",
          role: "gridcell",
          "data-jour": j,
          "data-creneau": c.id,
        },
      });
      cell.addEventListener("dblclick", () => openCoursEditor(j, c.id));
      cell.addEventListener("keydown", (e) => {
        if (e.key === "Enter" || e.key === " ") {
          e.preventDefault();
          openCoursEditor(j, c.id);
        }
      });
      root.appendChild(cell);
    });
  });
}

function el(tag, { class: cls, text, html, attrs } = {}) {
  const node = document.createElement(tag);
  if (cls) node.className = cls;
  if (text != null) node.textContent = text;
  if (html != null) node.innerHTML = html;
  if (attrs) Object.entries(attrs).forEach(([k, v]) => node.setAttribute(k, v));
  return node;
}

async function loadGrille() {
  if (!state.filiereId) return;
  const data = await api(`/api/grille?filiere_id=${state.filiereId}&date_lundi=${state.dateLundi}`);
  state.grille = data.grille || {};
  state.stats = data.stats || state.stats;
  $("#st-semaine").textContent = formatFr(state.dateLundi);
  updateStats(state.stats);
  renderGrille();
}

function updateStats(stats) {
  $("#st-cours").textContent = stats.cours ?? 0;
  $("#st-salles").textContent = stats.avec_salle ?? 0;
  $("#st-tc").textContent = stats.tronc_commun ?? 0;
}

function renderGrille() {
  const q = ($("#inp-search").value || "").trim().toLowerCase();
  $$(".cell").forEach((cell) => {
    const jour = cell.dataset.jour;
    const creneau = cell.dataset.creneau;
    const key = `${jour}|${creneau}`;
    const cours = state.grille[key];
    cell.classList.remove("filled", "tc", "dimmed");
    cell.innerHTML = "";

    if (!cours || !cours.matiere) {
      cell.appendChild(el("span", { class: "empty", text: "Ajouter…" }));
      if (q) cell.classList.add("dimmed");
      return;
    }

    cell.classList.add("filled");
    if (cours.groupe_tc) cell.classList.add("tc");
    cell.appendChild(el("div", { class: "matiere", text: cours.matiere }));
    cell.appendChild(el("div", { class: "enseignant", text: cours.enseignant }));
    if (cours.salle_nom) {
      cell.appendChild(el("div", { class: "salle", text: `Salle ${cours.salle_nom}` }));
    }
    if (cours.groupe_tc) {
      cell.appendChild(el("span", { class: "badge-tc", text: "Tronc commun" }));
    }

    if (q) {
      const hay = `${cours.matiere} ${cours.enseignant} ${cours.salle_nom || ""}`.toLowerCase();
      if (!hay.includes(q)) cell.classList.add("dimmed");
    }
  });
}

async function openCoursEditor(jour, creneau) {
  if (!state.filiereId) {
    toast("Sélectionnez une filière", "warn");
    return;
  }
  state.editSlot = { jour, creneau };
  state.forceSave = false;
  const key = `${jour}|${creneau}`;
  const cours = state.grille[key];
  const label = state.meta.creneaux.find((c) => c.id === creneau)?.label || creneau;
  $("#slot-label").textContent = `${jour} · ${label}`;
  $("#cours-matiere").value = cours?.matiere || "";
  $("#cours-enseignant").value = cours?.enseignant || "";
  $("#conflict-box").classList.add("hidden");
  $("#cours-tc").checked = Boolean(cours?.groupe_tc);
  $("#tc-panel").classList.toggle("hidden", !cours?.groupe_tc);

  await populateMatieres();
  await loadEnseignants();
  await populateTcList(cours);

  openModal("#modal-cours");
  $("#cours-matiere").focus();
}

async function populateMatieres() {
  const list = await api(
    `/api/suggestions/matieres?filiere_id=${state.filiereId}&date_lundi=${state.dateLundi}`
  );
  $("#list-matieres").innerHTML = list.map((m) => `<option value="${escapeAttr(m)}"></option>`).join("");
}

async function loadEnseignants() {
  const matiere = $("#cours-matiere").value.trim();
  const data = await api(
    `/api/suggestions/enseignants?matiere=${encodeURIComponent(matiere)}&filiere_id=${state.filiereId}`
  );
  $("#list-enseignants").innerHTML = data.enseignants
    .map((e) => `<option value="${escapeAttr(e)}"></option>`)
    .join("");
  if (data.dernier && !$("#cours-enseignant").value) {
    $("#cours-enseignant").value = data.dernier;
  }
}

async function populateTcList(cours) {
  const etab = $("#sel-etab")?.value || "";
  const all = await api(
    `/api/filieres?etablissement=${encodeURIComponent(etab)}`
  );
  let selected = [];
  if (cours?.groupe_tc) {
    const info = await api(
      `/api/tronc-commun/${state.filiereId}?date_lundi=${state.dateLundi}&jour=${encodeURIComponent(state.editSlot.jour)}&creneau=${encodeURIComponent(state.editSlot.creneau)}`
    );
    selected = info.filiere_ids || [];
  }

  const byYear = {};
  all.forEach((f) => {
    (byYear[f.annee] ||= []).push(f);
  });

  const box = $("#tc-list");
  box.innerHTML = "";
  Object.keys(byYear)
    .sort()
    .forEach((annee) => {
      box.appendChild(el("div", { class: "tc-year", text: annee }));
      const allBtn = el("label", { class: "tc-item" });
      allBtn.innerHTML = `<input type="checkbox" data-year="${annee}" class="tc-all" /> Toutes`;
      box.appendChild(allBtn);
      byYear[annee].forEach((f) => {
        const lab = el("label", { class: "tc-item" });
        const checked = selected.includes(f.id) || f.id === state.filiereId ? "checked" : "";
        lab.innerHTML = `<input type="checkbox" class="tc-f" value="${f.id}" data-year="${annee}" ${checked} /> ${escapeHtml(f.nom)}`;
        box.appendChild(lab);
      });
      allBtn.querySelector("input").addEventListener("change", (e) => {
        $$(`.tc-f[data-year="${annee}"]`).forEach((cb) => {
          cb.checked = e.target.checked;
        });
      });
    });
}

function escapeHtml(s) {
  return String(s)
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;");
}

function escapeAttr(s) {
  return escapeHtml(s).replaceAll("'", "&#39;");
}

async function saveCours(e) {
  e.preventDefault();
  const matiere = $("#cours-matiere").value.trim();
  const enseignant = $("#cours-enseignant").value.trim();
  if (!matiere || !enseignant) {
    toast("Matière et enseignant requis", "warn");
    return;
  }

  const filieres_tc = $("#cours-tc").checked
    ? $$(".tc-f:checked").map((c) => Number(c.value))
    : [];

  const payload = {
    filiere_id: state.filiereId,
    date_lundi: state.dateLundi,
    jour: state.editSlot.jour,
    creneau: state.editSlot.creneau,
    matiere,
    enseignant,
    filieres_tc,
    force: state.forceSave,
  };

  try {
    const data = await api("/api/cours", { method: "POST", body: JSON.stringify(payload) });
    state.grille = data.grille;
    state.stats = data.stats;
    updateStats(state.stats);
    renderGrille();
    closeModal($("#modal-cours"));
    toast("Cours enregistré");
    state.forceSave = false;
  } catch (err) {
    if (err.status === 409 && err.data?.warning === "conflit_enseignant") {
      const box = $("#conflict-box");
      const list = (err.data.conflits || [])
        .map((c) => `• ${c.filiere} — ${c.matiere}`)
        .join("<br>");
      box.innerHTML = `<strong>Conflit enseignant</strong><br>${list}<br><br>
        <button type="button" class="btn soft" id="btn-force">Enregistrer quand même</button>`;
      box.classList.remove("hidden");
      $("#btn-force").onclick = () => {
        state.forceSave = true;
        $("#form-cours").requestSubmit();
      };
      toast("Conflit détecté", "warn");
      return;
    }
    toast(err.message || "Erreur", "error");
  }
}

async function clearSlot() {
  if (!state.editSlot) return;
  const key = `${state.editSlot.jour}|${state.editSlot.creneau}`;
  const cours = state.grille[key];
  if (cours?.id) {
    await api(
      `/api/cours/${cours.id}?date_lundi=${state.dateLundi}&jour=${encodeURIComponent(state.editSlot.jour)}`,
      { method: "DELETE" }
    );
  } else {
    await api("/api/cours", {
      method: "POST",
      body: JSON.stringify({
        filiere_id: state.filiereId,
        date_lundi: state.dateLundi,
        jour: state.editSlot.jour,
        creneau: state.editSlot.creneau,
        matiere: "",
        enseignant: "",
      }),
    });
  }
  closeModal($("#modal-cours"));
  await loadGrille();
  toast("Créneau vidé");
}

async function allouerSalles() {
  if (!state.filiereId) {
    toast("Sélectionnez une filière", "warn");
    return;
  }
  try {
    const data = await api("/api/allouer", {
      method: "POST",
      body: JSON.stringify({ date_lundi: state.dateLundi, filiere_id: state.filiereId }),
    });
    state.grille = data.grille;
    state.stats = data.stats;
    updateStats(state.stats);
    renderGrille();
    const failed = data.rapport?.failed?.length || 0;
    if (failed) {
      const reasons = [...new Set(data.rapport.failed.map((f) => f.reason))].join(" · ");
      toast(`${data.message || "Allocation partielle"} — ${reasons}`, "warn");
    } else {
      toast(data.message || "Salles allouées");
    }
  } catch (err) {
    toast(err.message || "Allocation échouée", "error");
  }
}

async function verifierConflits() {
  try {
    const q = state.filiereId ? `&filiere_id=${state.filiereId}` : "";
    const data = await api(`/api/conflits?date_lundi=${state.dateLundi}${q}`);
    const n = data.conflits?.length || 0;
    if (!n) {
      toast("Aucun conflit enseignant cette semaine");
      return;
    }
    const lines = data.conflits
      .slice(0, 8)
      .map((c) => `${c.jour} ${c.creneau} — ${c.enseignant} (${c.cours.length} cours)`)
      .join("\n");
    alert(`${n} conflit(s) enseignant(s) :\n\n${lines}`);
    toast(`${n} conflit(s) détecté(s)`, "warn");
  } catch (err) {
    toast(err.message || "Vérification impossible", "error");
  }
}

async function resetSemaine() {
  if (!state.filiereId) return;
  if (!confirm("Supprimer tous les cours de cette semaine pour la filière ?")) return;
  try {
    const data = await api("/api/reinitialiser", {
      method: "POST",
      body: JSON.stringify({ filiere_id: state.filiereId, date_lundi: state.dateLundi }),
    });
    state.grille = data.grille;
    state.stats = data.stats;
    updateStats(state.stats);
    renderGrille();
    toast("Semaine réinitialisée");
  } catch (err) {
    toast(err.message || "Réinitialisation échouée", "error");
  }
}

async function copySemaine(e) {
  e.preventDefault();
  if (!state.filiereId) {
    toast("Sélectionnez une filière", "warn");
    return;
  }
  try {
    const source = toMonday($("#copy-source").value);
    const data = await api("/api/copier-semaine", {
      method: "POST",
      body: JSON.stringify({
        filiere_id: state.filiereId,
        date_source: source,
        date_cible: state.dateLundi,
      }),
    });
    state.grille = data.grille;
    state.stats = data.stats;
    updateStats(state.stats);
    renderGrille();
    closeModal($("#modal-copy"));
    if (!data.copied) {
      toast("Aucun cours à copier depuis cette semaine", "warn");
    } else {
      toast(`${data.copied} cours copiés`);
    }
  } catch (err) {
    toast(err.message || "Copie échouée", "error");
  }
}

async function exportPdf(mode) {
  if (!state.filiereId && mode === "one") {
    toast("Sélectionnez une filière", "warn");
    return;
  }

  const payload = {
    mode: mode === "all" ? "zip" : mode,
    date_lundi: state.dateLundi,
    etablissement: $("#sel-etab")?.value || null,
    type_cours: $("#sel-type")?.value || null,
  };
  if (mode === "one") {
    payload.filiere_id = state.filiereId;
  }

  toast(mode === "one" ? "Génération du PDF…" : "Génération du ZIP…");

  try {
    const res = await fetch("/api/export-pdf", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });
    if (!res.ok) {
      let msg = "Export échoué";
      try {
        const err = await res.json();
        if (err?.error) msg = err.error;
      } catch (_) {}
      toast(msg, "error");
      return;
    }

    const blob = await res.blob();
    const cd = res.headers.get("Content-Disposition") || "";
    const match = /filename="?([^"]+)"?/i.exec(cd);
    const fallback =
      mode === "one"
        ? `emploi_du_temps_${state.dateLundi}.pdf`
        : `EDT_${state.dateLundi}.zip`;
    const filename = match?.[1] || fallback;

    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = filename;
    a.click();
    URL.revokeObjectURL(url);
    toast(mode === "one" ? "PDF téléchargé" : "Archive ZIP téléchargée");
  } catch (e) {
    toast("Export échoué", "error");
  }
}

async function openSalles() {
  try {
    openModal("#modal-salles");
    await refreshSalles();
  } catch (err) {
    toast(err.message || "Impossible d'ouvrir les salles", "error");
  }
}

async function openEffectifs() {
  try {
    openModal("#modal-effectifs");
    const etab = $("#sel-etab")?.value || "";
    const rows = await api(`/api/effectifs?etablissement=${encodeURIComponent(etab)}`);
    const tbody = $("#table-effectifs tbody");
    if (!rows.length) {
      tbody.innerHTML = `<tr><td colspan="3" class="muted">Aucune filière</td></tr>`;
      return;
    }
    tbody.innerHTML = rows
      .map(
        (r) => `<tr>
      <td>${escapeHtml(r.annee + " — " + r.nom)}</td>
      <td><input type="number" min="0" value="${r.effectif}" data-eff="${r.id}" style="width:6rem" /></td>
      <td><button type="button" class="btn soft" data-save-eff="${r.id}">OK</button></td>
    </tr>`
      )
      .join("");
    $$("[data-save-eff]").forEach((btn) => {
      btn.addEventListener("click", async () => {
        const input = $(`[data-eff="${btn.dataset.saveEff}"]`);
        try {
          await api(`/api/effectifs/${btn.dataset.saveEff}`, {
            method: "PUT",
            body: JSON.stringify({ effectif: Number(input.value) }),
          });
          toast("Effectif mis à jour");
          await loadFilieres();
        } catch (err) {
          toast(err.message || "Erreur", "error");
        }
      });
    });
  } catch (err) {
    toast(err.message || "Impossible d'ouvrir les effectifs", "error");
  }
}

async function openFilieres() {
  try {
    openModal("#modal-filieres");
    await refreshFilieresManage();
  } catch (err) {
    toast(err.message || "Impossible d'ouvrir les filières", "error");
  }
}

async function refreshSalles() {
  const salles = await api("/api/salles");
  const tbody = $("#table-salles tbody");
  if (!salles.length) {
    tbody.innerHTML = `<tr><td colspan="3" class="muted">Aucune salle — ajoutez-en pour l'allocation automatique.</td></tr>`;
    return;
  }
  tbody.innerHTML = salles
    .map(
      (s) => `<tr>
      <td>${escapeHtml(s.nom)}</td>
      <td>${s.capacite}</td>
      <td><button type="button" class="btn danger-ghost" data-del-salle="${s.id}">Suppr.</button></td>
    </tr>`
    )
    .join("");
  $$("[data-del-salle]").forEach((btn) => {
    btn.addEventListener("click", async () => {
      if (!confirm("Supprimer cette salle ?")) return;
      try {
        await api(`/api/salles/${btn.dataset.delSalle}`, { method: "DELETE" });
        await refreshSalles();
        toast("Salle supprimée");
      } catch (err) {
        toast(err.message || "Suppression échouée", "error");
      }
    });
  });
}

async function addSalle() {
  const nom = $("#salle-nom").value.trim();
  const capacite = Number($("#salle-cap").value);
  try {
    await api("/api/salles", { method: "POST", body: JSON.stringify({ nom, capacite }) });
    $("#salle-nom").value = "";
    $("#salle-cap").value = "";
    await refreshSalles();
    toast("Salle ajoutée");
  } catch (err) {
    toast(err.message, "error");
  }
}

async function refreshFilieresManage() {
  const annee = $("#sel-annee").value;
  const etab = $("#sel-etab").value;
  const list = await api(`/api/filieres?annee=${encodeURIComponent(annee)}&etablissement=${encodeURIComponent(etab)}`);
  const ul = $("#list-filieres-manage");
  ul.innerHTML = list
    .map(
      (f) => `<li>
      <span>${escapeHtml(f.nom)} <small class="muted">(${f.effectif})</small></span>
      <button type="button" class="btn danger-ghost" data-del-f="${f.id}">Suppr.</button>
    </li>`
    )
    .join("") || `<li class="muted">Aucune filière</li>`;
  $$("[data-del-f]").forEach((btn) => {
    btn.addEventListener("click", async () => {
      if (!confirm("Supprimer cette filière et ses cours ?")) return;
      try {
        await api(`/api/filieres/${btn.dataset.delF}`, { method: "DELETE" });
        await refreshFilieresManage();
        await loadFilieres();
        toast("Filière supprimée");
      } catch (err) {
        toast(err.message || "Suppression échouée", "error");
      }
    });
  });
}

async function addFiliere(e) {
  e.preventDefault();
  const nom = $("#filiere-nom").value.trim();
  const effectif = Number($("#filiere-eff").value || 0);
  try {
    await api("/api/filieres", {
      method: "POST",
      body: JSON.stringify({
        nom,
        effectif,
        annee: $("#sel-annee").value,
        etablissement: $("#sel-etab").value,
      }),
    });
    $("#filiere-nom").value = "";
    $("#filiere-eff").value = "0";
    await refreshFilieresManage();
    await loadFilieres();
    toast("Filière ajoutée");
  } catch (err) {
    toast(err.message, "error");
  }
}

init().catch((err) => {
  console.error(err);
  toast("Impossible de démarrer l'application", "error");
});
