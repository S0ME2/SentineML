/* SentinelML UI: dependency free, same origin API client. */
(() => {
  "use strict";
  const state = {
    projects: [],
    datasets: [],
    models: [],
    directions: [],
    runs: [],
    filtered: [],
    selected: new Set(),
    sort: { key: "id", dir: -1 },
    currentRun: null,
    detail: null,
    resource: null,
    action: null,
    activityPeriod: 14,
    activityDate: null,
    loading: false,
    notesDrafts: new Map(),
  };
  const $ = (selector, root = document) => root.querySelector(selector);
  const $$ = (selector, root = document) => [
    ...root.querySelectorAll(selector),
  ];
  const text = (value) => (value == null || value === "" ? "—" : String(value));
  const escapeCsv = (value) => {
    const raw =
      value == null
        ? ""
        : String(value).replace(
            /[\u0000-\u0008\u000b\u000c\u000e-\u001f\u007f]/g,
            " ",
          );
    return /^[=+\-@\t\r\n]/.test(raw) || /^[=+\-@]/.test(raw.trimStart())
      ? `'${raw}`
      : raw;
  };
  const csvCell = (value) => {
    const safe = escapeCsv(value);
    return /[",\r\n]/.test(safe) ? `"${safe.replaceAll('"', '""')}"` : safe;
  };
  const fmtDate = (value) =>
    value
      ? new Intl.DateTimeFormat(undefined, {
          dateStyle: "medium",
          timeStyle: "short",
        }).format(new Date(value))
      : "—";
  const byId = (items, id) => items.find((item) => item.id === Number(id));
  const nameFor = (items, id, fallback = `#${id}`) => {
    const item = byId(items, id);
    return item
      ? [item.name, item.version].filter(Boolean).join(" · ")
      : fallback;
  };

  async function api(path, options = {}) {
    const response = await fetch(path, {
      headers: {
        "Content-Type": "application/json",
        ...(options.headers || {}),
      },
      ...options,
    });
    if (!response.ok) {
      let message = `Request failed (${response.status})`;
      try {
        const body = await response.json();
        message = Array.isArray(body.detail)
          ? body.detail
              .map(
                (item) =>
                  `${item.loc?.slice(1).join(".") || "Input"}: ${item.msg}`,
              )
              .join("; ")
          : body.detail || message;
      } catch (_) {
        /* response had no JSON */
      }
      throw new Error(message);
    }
    if (response.status === 204) return null;
    return response.json();
  }

  function toast(message, isError = false) {
    const node = $("#toast");
    node.textContent = message;
    node.classList.toggle("error-toast", isError);
    node.classList.remove("hidden");
    window.clearTimeout(toast.timer);
    toast.timer = window.setTimeout(() => node.classList.add("hidden"), 3600);
  }
  function setView(name) {
    $$(".view").forEach((view) =>
      view.classList.toggle("active", view.id === `view-${name}`),
    );
    $$(".nav button").forEach((button) => {
      button.classList.toggle("active", button.dataset.nav === name);
      if (button.dataset.nav === name)
        button.setAttribute("aria-current", "page");
      else button.removeAttribute("aria-current");
    });
    $("#crumb").textContent =
      name === "detail"
        ? "Run detail"
        : name.charAt(0).toUpperCase() + name.slice(1);
  }
  function showError(container, error, retry) {
    container.replaceChildren();
    const node = document.createElement("div");
    node.className = "error";
    const message = document.createElement("span");
    message.textContent = error.message || String(error);
    node.append(message);
    if (retry) {
      const button = document.createElement("button");
      button.className = "button small";
      button.type = "button";
      button.textContent = "Retry";
      button.addEventListener("click", retry);
      node.append(button);
    }
    container.append(node);
  }
  function setSelectOptions(select, items, allLabel) {
    const current = select.value;
    select.replaceChildren();
    const all = document.createElement("option");
    all.value = "all";
    all.textContent = allLabel;
    select.append(all);
    items.forEach((item) => {
      const option = document.createElement("option");
      option.value = item.id;
      option.textContent = item.name;
      select.append(option);
    });
    if ([...select.options].some((option) => option.value === current))
      select.value = current;
  }

  async function loadWorkspace() {
    if (state.loading) return;
    state.loading = true;
    const refresh = $('[data-action="refresh-runs"]');
    refresh.disabled = true;
    refresh.setAttribute("aria-busy", "true");
    $("#sync-status").textContent = "Syncing…";
    $("#sync-status").dataset.state = "loading";
    const tableState = $("#table-state");
    tableState.className = "loading";
    tableState.textContent = "Loading workspace…";
    tableState.classList.remove("hidden");
    $("#run-table-wrap").classList.add("hidden");
    try {
      const [projects, datasets, models, directions, runs] = await Promise.all([
        api("/projects/"),
        api("/datasets/"),
        api("/models/"),
        api("/metric-directions/"),
        api("/runs/"),
      ]);
      Object.assign(state, { projects, datasets, models, directions, runs });
      state.selected.forEach((id) => {
        if (!runs.some((run) => run.id === id)) state.selected.delete(id);
      });
      renderSummary();
      setSelectOptions($("#project-filter"), projects, "All projects");
      renderRuns();
      renderProjects();
      renderCatalog();
      updateOnboarding();
      const updated = new Intl.DateTimeFormat(undefined, {
        hour: "2-digit",
        minute: "2-digit",
      }).format(new Date());
      $("#sync-status").textContent = `Updated ${updated}`;
      $("#sync-status").dataset.state = "success";
    } catch (error) {
      showError(tableState, error, loadWorkspace);
      $("#sync-status").textContent = "Sync failed";
      $("#sync-status").dataset.state = "error";
    } finally {
      state.loading = false;
      refresh.disabled = false;
      refresh.removeAttribute("aria-busy");
    }
  }
  function renderSummary() {
    $("#sum-total").textContent = state.runs.length;
    $("#sum-running").textContent = state.runs.filter(
      (run) => run.status === "running",
    ).length;
    $("#sum-completed").textContent = state.runs.filter(
      (run) => run.status === "completed",
    ).length;
    $("#sum-projects").textContent = state.projects.length;
    renderInsights();
  }
  function localDay(value) {
    if (!value) return null;
    const date = new Date(value);
    if (!Number.isFinite(date.getTime())) return null;
    return `${date.getFullYear()}-${String(date.getMonth() + 1).padStart(2, "0")}-${String(date.getDate()).padStart(2, "0")}`;
  }
  function renderInsights() {
    const counts = new Map();
    state.runs.forEach((run) => {
      const day = localDay(run.start_time);
      if (day) counts.set(day, (counts.get(day) || 0) + 1);
    });
    const days = Array.from({ length: state.activityPeriod }, (_, index) => {
      const date = new Date();
      date.setHours(0, 0, 0, 0);
      date.setDate(date.getDate() - state.activityPeriod + 1 + index);
      return {
        key: localDay(date),
        date,
        count: counts.get(localDay(date)) || 0,
      };
    });
    const total = days.reduce((sum, day) => sum + day.count, 0);
    const max = Math.max(1, ...days.map((day) => day.count));
    $("#activity-total").textContent = total;
    $("#activity-caption").textContent =
      `runs in the last ${state.activityPeriod} days`;
    $("#activity-hover").textContent = "";
    const chart = $("#activity-chart");
    chart.replaceChildren();
    chart.style.setProperty("--day-count", days.length);
    days.forEach((day) => {
      const bar = document.createElement("button");
      bar.type = "button";
      bar.className = "activity-bar";
      bar.dataset.day = day.key;
      bar.dataset.count = day.count;
      bar.setAttribute("aria-pressed", String(state.activityDate === day.key));
      const label = `${new Intl.DateTimeFormat(undefined, { month: "short", day: "numeric", year: "numeric" }).format(day.date)}: ${day.count} runs started`;
      bar.setAttribute("aria-label", label);
      const fill = document.createElement("span");
      fill.className = "activity-fill";
      fill.style.setProperty("--bar-scale", day.count / max);
      const dot = document.createElement("span");
      dot.className = "activity-baseline";
      bar.append(fill, dot);
      const describe = () => {
        $("#activity-hover").textContent = label;
      };
      bar.addEventListener("mouseenter", describe);
      bar.addEventListener("focus", describe);
      bar.addEventListener("click", () => {
        state.activityDate = state.activityDate === day.key ? null : day.key;
        $$(".activity-bar").forEach((item) =>
          item.setAttribute(
            "aria-pressed",
            String(item.dataset.day === state.activityDate),
          ),
        );
        renderRuns();
      });
      chart.append(bar);
    });
    chart.onmouseleave = () => {
      if (!chart.contains(document.activeElement))
        $("#activity-hover").textContent = "";
    };
    const axis = $("#activity-axis");
    axis.replaceChildren();
    [days[0], days[Math.floor(days.length / 2)], days.at(-1)].forEach((day) => {
      const label = document.createElement("span");
      label.textContent = new Intl.DateTimeFormat(undefined, {
        month: "short",
        day: "numeric",
      }).format(day.date);
      axis.append(label);
    });
    const completed = state.runs.filter(
      (run) => run.status === "completed",
    ).length;
    const rate = state.runs.length
      ? Math.round((completed / state.runs.length) * 100)
      : 0;
    $("#completion-rate").textContent = state.runs.length ? `${rate}%` : "—";
    $("#completion-ring").setAttribute(
      "stroke-dasharray",
      `${rate} ${100 - rate}`,
    );
    $("#health-caption").textContent =
      `${completed} of ${state.runs.length} runs completed`;
    const controls = $("#status-controls");
    controls.replaceChildren();
    ["running", "completed", "waiting", "failed", "cancelled"].forEach(
      (status) => {
        const button = document.createElement("button");
        button.type = "button";
        button.dataset.statusFilter = status;
        button.setAttribute(
          "aria-pressed",
          String($("#status-filter").value === status),
        );
        const name = statusNode(status);
        const count = document.createElement("strong");
        count.textContent = state.runs.filter(
          (run) => run.status === status,
        ).length;
        button.append(name, count);
        button.addEventListener("click", () => {
          $("#status-filter").value =
            $("#status-filter").value === status ? "all" : status;
          renderRuns();
        });
        controls.append(button);
      },
    );
  }

  function filteredRuns() {
    const project = $("#project-filter").value;
    const status = $("#status-filter").value;
    const query = ($("#run-search").value || $("#global-search").value)
      .trim()
      .toLowerCase();
    const result = state.runs.filter(
      (run) =>
        (project === "all" || String(run.project_id) === project) &&
        (status === "all" || run.status === status) &&
        (!state.activityDate ||
          localDay(run.start_time) === state.activityDate) &&
        (!query ||
          [
            run.id,
            run.status,
            run.notes,
            nameFor(state.projects, run.project_id),
            nameFor(state.models, run.model_id),
            nameFor(state.datasets, run.dataset_id),
          ]
            .join(" ")
            .toLowerCase()
            .includes(query)),
    );
    const { key, dir } = state.sort;
    return result.sort((a, b) => {
      const av =
        key === "project_id"
          ? nameFor(state.projects, a[key])
          : key === "model_id"
            ? nameFor(state.models, a[key])
            : key === "dataset_id"
              ? nameFor(state.datasets, a[key])
              : a[key] || "";
      const bv =
        key === "project_id"
          ? nameFor(state.projects, b[key])
          : key === "model_id"
            ? nameFor(state.models, b[key])
            : key === "dataset_id"
              ? nameFor(state.datasets, b[key])
              : b[key] || "";
      return av === bv ? 0 : (av > bv ? 1 : -1) * dir;
    });
  }
  function updateOnboarding() {
    const onboarding = $("#onboarding");
    if (state.runs.length) {
      onboarding.classList.add("hidden");
      return;
    }
    onboarding.classList.remove("hidden");
    const next = !state.projects.length
      ? "project"
      : !state.models.length
        ? "model"
        : !state.datasets.length
          ? "dataset"
          : !state.directions.length
            ? "metric-direction"
            : "run";
    const labels = {
      project: [
        "Create your first project",
        "Start by naming the question your lab is exploring.",
      ],
      model: [
        "Add a model",
        "Register the model version used by your experiments.",
      ],
      dataset: [
        "Add a dataset",
        "Register a versioned dataset before logging a run.",
      ],
      run: [
        "Log your first run",
        "Your context is ready. Record the first experiment.",
      ],
      "metric-direction": [
        "Register a metric",
        "Name a result and choose whether lower or higher is better before logging it.",
      ],
    };
    $("#onboarding-title").textContent = labels[next][0];
    $("#onboarding-copy").textContent = labels[next][1];
    $("#onboarding-action").textContent = labels[next][0];
    $("#onboarding-action").onclick = () => openResource(next);
  }
  function statusNode(status) {
    const node = document.createElement("span");
    node.className = `status ${status}`;
    node.textContent = status;
    return node;
  }
  function renderRuns() {
    state.filtered = filteredRuns();
    $("#registry-count").textContent =
      `${state.filtered.length} of ${state.runs.length} runs`;
    $("#day-filter").classList.toggle("hidden", !state.activityDate);
    $("#day-filter-label").textContent = state.activityDate
      ? `Started on ${state.activityDate}`
      : "";
    $$("[data-status-filter]").forEach((button) =>
      button.setAttribute(
        "aria-pressed",
        String(button.dataset.statusFilter === $("#status-filter").value),
      ),
    );
    const body = $("#run-body");
    body.replaceChildren();
    $("#run-table-wrap").classList.toggle("hidden", !state.filtered.length);
    $("#table-state").classList.toggle(
      "hidden",
      Boolean(state.filtered.length),
    );
    if (!state.filtered.length) {
      $("#table-state").className = "empty";
      $("#table-state").textContent = state.runs.length
        ? "No runs match these filters."
        : "No runs yet.";
    }
    state.filtered.forEach((run) => {
      const row = document.createElement("tr");
      const selectCell = document.createElement("td");
      const checkbox = document.createElement("input");
      checkbox.type = "checkbox";
      checkbox.className = "compare-select";
      checkbox.checked = state.selected.has(run.id);
      checkbox.setAttribute(
        "aria-label",
        `Select run ${run.id} for comparison`,
      );
      checkbox.addEventListener("change", () => {
        if (checkbox.checked) {
          if (state.selected.size >= 4) {
            checkbox.checked = false;
            toast("Compare up to four runs.", true);
            return;
          }
          state.selected.add(run.id);
        } else state.selected.delete(run.id);
        renderRuns();
      });
      selectCell.append(checkbox);
      row.append(selectCell);
      const runCell = document.createElement("td");
      const link = document.createElement("button");
      link.className = "run-link mono";
      link.type = "button";
      link.textContent = `run-${run.id}`;
      link.addEventListener("click", () => openDetail(run.id));
      runCell.append(link);
      row.append(runCell);
      [
        nameFor(state.projects, run.project_id),
        statusNode(run.status),
        nameFor(state.models, run.model_id),
        nameFor(state.datasets, run.dataset_id),
        fmtDate(run.start_time),
      ].forEach((value) => {
        const cell = document.createElement("td");
        if (value instanceof Node) cell.append(value);
        else cell.textContent = value;
        row.append(cell);
      });
      const actionCell = document.createElement("td");
      const detail = document.createElement("button");
      detail.className = "button small";
      detail.type = "button";
      detail.textContent = "Open";
      detail.addEventListener("click", () => openDetail(run.id));
      actionCell.append(detail);
      row.append(actionCell);
      [...row.cells].forEach((cell, index) => {
        cell.dataset.label = [
          "Select",
          "Run",
          "Project",
          "Status",
          "Model",
          "Dataset",
          "Started",
          "Actions",
        ][index];
      });
      body.append(row);
    });
    const selectAll = $("#select-all");
    const selectable = state.filtered.length > 0;
    const selectedVisible = state.filtered.filter((run) =>
      state.selected.has(run.id),
    ).length;
    selectAll.checked =
      selectable && selectedVisible === Math.min(4, state.filtered.length);
    selectAll.indeterminate = selectedVisible > 0 && !selectAll.checked;
    selectAll.disabled = !selectable;
    renderCompareBar();
  }
  function renderCompareBar() {
    const existing = $(".compare-bar");
    if (existing) existing.remove();
    if (state.selected.size) {
      const bar = document.createElement("div");
      bar.className = "compare-bar";
      bar.textContent = `${state.selected.size} run${state.selected.size === 1 ? "" : "s"} selected`;
      const spacer = document.createElement("span");
      spacer.className = "toolbar-spacer";
      const clear = document.createElement("button");
      clear.className = "button ghost small";
      clear.type = "button";
      clear.textContent = "Clear";
      clear.addEventListener("click", () => {
        state.selected.clear();
        renderRuns();
      });
      const compare = document.createElement("button");
      compare.className = "button primary small";
      compare.type = "button";
      compare.textContent = "Compare selected";
      compare.disabled = state.selected.size < 2;
      compare.addEventListener("click", () => {
        if (state.selected.size >= 2) openComparison();
      });
      bar.append(spacer, clear, compare);
      $(".panel").prepend(bar);
    }
  }
  function renderProjects() {
    const root = $("#projects-list");
    root.replaceChildren();
    if (!state.projects.length) {
      root.className = "panel empty";
      root.textContent = "No projects yet.";
      return;
    }
    root.className = "summary-grid";
    state.projects.forEach((project) => {
      const card = document.createElement("article");
      card.className = "summary-card project-card";
      card.tabIndex = 0;
      card.setAttribute("role", "button");
      card.setAttribute("aria-label", `Open project ${project.name}`);
      const title = document.createElement("h2");
      title.textContent = project.name;
      const desc = document.createElement("p");
      desc.textContent = project.description || "No description yet";
      const count = document.createElement("strong");
      count.className = "accent";
      count.textContent = `${state.runs.filter((run) => run.project_id === project.id).length} runs`;
      const open = () => {
        $("#project-filter").value = project.id;
        setView("experiments");
        renderRuns();
      };
      card.append(title, desc, count);
      card.addEventListener("click", open);
      card.addEventListener("keydown", (event) => {
        if (event.key === "Enter" || event.key === " ") {
          event.preventDefault();
          open();
        }
      });
      root.append(card);
    });
  }
  function catalogCard(title, items, action) {
    const panel = document.createElement("section");
    panel.className = "panel";
    const head = document.createElement("div");
    head.className = "panel-head";
    const h = document.createElement("h2");
    h.textContent = title;
    const button = document.createElement("button");
    button.className = "button small";
    button.type = "button";
    button.textContent = `New ${action}`;
    button.addEventListener("click", () => openResource(action));
    head.append(h, button);
    const body = document.createElement("div");
    body.className = "panel-body item-list";
    if (!items.length) {
      body.textContent = `No ${title.toLowerCase()} yet.`;
    }
    items.forEach((item) => {
      const row = document.createElement("div");
      row.className = "item";
      const left = document.createElement("div");
      const name = document.createElement("div");
      name.className = "name";
      name.textContent = item.name;
      const small = document.createElement("small");
      small.textContent =
        typeof item.maximize === "boolean"
          ? item.maximize
            ? "Maximize · higher is better"
            : "Minimize · lower is better"
          : [item.version, item.model_type, item.description]
              .filter(Boolean)
              .join(" · ") || "Reusable registry item";
      left.append(name, small);
      row.append(left);
      body.append(row);
    });
    panel.append(head, body);
    return panel;
  }
  function renderCatalog() {
    const root = $("#catalog-list");
    root.replaceChildren(
      catalogCard("Models", state.models, "model"),
      catalogCard("Datasets", state.datasets, "dataset"),
      catalogCard("Metric directions", state.directions, "metric-direction"),
    );
  }

  function field(label, name, type = "text", options = {}) {
    const wrapper = document.createElement("div");
    wrapper.className = "field";
    const labelNode = document.createElement("label");
    labelNode.htmlFor = `field-${name}`;
    labelNode.textContent = label;
    wrapper.append(labelNode);
    let input;
    if (type === "textarea") input = document.createElement("textarea");
    else if (type === "select") {
      input = document.createElement("select");
      options.choices.forEach(([value, labelText]) => {
        const option = document.createElement("option");
        option.value = value;
        option.textContent = labelText;
        input.append(option);
      });
    } else {
      input = document.createElement("input");
      input.type = type;
    }
    input.id = `field-${name}`;
    input.name = name;
    input.autocomplete = "off";
    if (options.required) input.required = true;
    if (options.placeholder) input.placeholder = options.placeholder;
    if (options.step) input.step = options.step;
    if (options.min != null) input.min = options.min;
    if (options.max != null) input.max = options.max;
    wrapper.append(input);
    if (options.hint) {
      const hint = document.createElement("small");
      hint.textContent = options.hint;
      wrapper.append(hint);
    }
    return wrapper;
  }
  const forms = {
    project: {
      title: "New project",
      fields: () => [
        field("Name", "name", "text", {
          required: true,
          placeholder: "e.g. Search ranking v2",
        }),
        field("Description", "description", "textarea", {
          placeholder: "What question is this project answering?",
        }),
      ],
      submit: (data) =>
        api("/projects/", { method: "POST", body: JSON.stringify(data) }),
    },
    dataset: {
      title: "New dataset",
      fields: () => [
        field("Name", "name", "text", { required: true }),
        field("Version", "version", "text", {
          required: true,
          placeholder: "v1.0",
        }),
        field("Source", "source"),
        field("Description", "description", "textarea"),
      ],
      submit: (data) =>
        api("/datasets/", { method: "POST", body: JSON.stringify(data) }),
    },
    model: {
      title: "New model",
      fields: () => [
        field("Name", "name", "text", { required: true }),
        field("Version", "version", "text", { required: true }),
        field("Model type", "model_type", "text", {
          placeholder: "transformer, xgboost…",
        }),
        field("Description", "description", "textarea"),
      ],
      submit: (data) =>
        api("/models/", { method: "POST", body: JSON.stringify(data) }),
    },
    "metric-direction": {
      title: "New metric direction",
      fields: () => [
        field("Metric name", "name", "text", {
          required: true,
          placeholder: "val_accuracy",
        }),
        field("Direction", "maximize", "select", {
          choices: [
            ["true", "Maximize (higher is better)"],
            ["false", "Minimize (lower is better)"],
          ],
        }),
      ],
      submit: (data) =>
        api("/metric-directions/", {
          method: "POST",
          body: JSON.stringify({ ...data, maximize: data.maximize === "true" }),
        }),
    },
    run: {
      title: "Log a new run",
      fields: () => {
        const projectChoices = state.projects.map((item) => [
          String(item.id),
          item.name,
        ]);
        const datasetChoices = state.datasets.map((item) => [
          String(item.id),
          `${item.name} · ${item.version}`,
        ]);
        const modelChoices = state.models.map((item) => [
          String(item.id),
          `${item.name} · ${item.version}`,
        ]);
        return [
          field("Project", "project_id", "select", { choices: projectChoices }),
          field("Model", "model_id", "select", { choices: modelChoices }),
          field("Dataset", "dataset_id", "select", { choices: datasetChoices }),
          field("Notes", "notes", "textarea"),
        ];
      },
      submit: (data) =>
        api("/runs/", {
          method: "POST",
          body: JSON.stringify({
            ...data,
            project_id: Number(data.project_id),
            model_id: Number(data.model_id),
            dataset_id: Number(data.dataset_id),
          }),
        }),
    },
  };
  function openResource(resource) {
    const config = forms[resource];
    if (!config) return;
    state.resource = resource;
    $("#dialog-eyebrow").textContent =
      resource === "run" ? "Experiment registry" : "Workspace catalog";
    $("#dialog-title").textContent = config.title;
    $("#form-submit").textContent = resource === "run" ? "Log run" : "Create";
    $("#form-error").textContent = "";
    const fields = $("#form-fields");
    fields.replaceChildren(...config.fields());
    if (resource === "run" && $("#project-filter").value !== "all") {
      $("#field-project_id").value = $("#project-filter").value;
    }
    $("#form-dialog").showModal();
    window.setTimeout(
      () =>
        $(
          "#form-dialog input, #form-dialog select, #form-dialog textarea",
        )?.focus(),
      0,
    );
  }
  function formData() {
    return Object.fromEntries(new FormData($("#resource-form")).entries());
  }
  async function submitResource(event) {
    event.preventDefault();
    const config = forms[state.resource];
    const submit = $("#form-submit");
    submit.disabled = true;
    $("#form-error").textContent = "";
    try {
      await config.submit(formData());
      $("#form-dialog").close();
      await loadWorkspace();
      if (
        state.resource === "metric-direction" &&
        $("#view-detail").classList.contains("active")
      ) {
        await openDetail(state.currentRun);
      }
    } catch (error) {
      $("#form-error").textContent = error.message;
    } finally {
      submit.disabled = false;
    }
  }

  async function openDetail(runId) {
    state.currentRun = Number(runId);
    setView("detail");
    $("#detail-state").className = "loading";
    $("#detail-state").textContent = "Loading run context…";
    $("#detail-content").classList.add("hidden");
    try {
      const [run, parameters, metrics] = await Promise.all([
        api(`/runs/${runId}`),
        api(`/runs/${runId}/parameters/`),
        api(`/runs/${runId}/metrics/`),
      ]);
      if (state.currentRun !== Number(runId)) return;
      state.detail = { run, parameters, metrics };
      renderDetail();
    } catch (error) {
      showError($("#detail-state"), error, () => openDetail(runId));
    }
  }
  function renderDetail() {
    const { run, parameters, metrics } = state.detail;
    $("#detail-title").textContent = `run-${run.id}`;
    $("#detail-subtitle").textContent =
      `${nameFor(state.projects, run.project_id)} · ${nameFor(state.models, run.model_id)} · ${nameFor(state.datasets, run.dataset_id)}`;
    $("#detail-state").classList.add("hidden");
    const root = $("#detail-content");
    root.classList.remove("hidden");
    root.replaceChildren();
    const overview = document.createElement("section");
    overview.className = "panel";
    const head = document.createElement("div");
    head.className = "panel-head";
    const title = document.createElement("h2");
    title.textContent = "Run context";
    const status = statusNode(run.status);
    head.append(title, status);
    const body = document.createElement("div");
    body.className = "panel-body";
    const grid = document.createElement("div");
    grid.className = "kv-grid";
    [
      ["Project", nameFor(state.projects, run.project_id)],
      ["Model", nameFor(state.models, run.model_id)],
      ["Dataset", nameFor(state.datasets, run.dataset_id)],
      ["Started", fmtDate(run.start_time)],
      ["Finished", fmtDate(run.end_time)],
      ["Reason", run.reason || "—"],
      [
        "Ignored",
        run.is_ignored
          ? `Yes${run.ignore_reason ? ` · ${run.ignore_reason}` : ""}`
          : "No",
      ],
    ].forEach(([label, value]) => {
      const item = document.createElement("div");
      item.className = "kv";
      const l = document.createElement("label");
      l.textContent = label;
      const p = document.createElement("p");
      p.textContent = value;
      item.append(l, p);
      grid.append(item);
    });
    body.append(grid);
    const notesForm = document.createElement("form");
    notesForm.className = "notes-form";
    const notesField = field("Run notes", "run-notes", "textarea");
    const notesInput = $("textarea", notesField);
    notesInput.value = state.notesDrafts.get(run.id) ?? run.notes ?? "";
    const saveNotes = document.createElement("button");
    saveNotes.className = "button small";
    saveNotes.textContent = "Save notes";
    const notesFeedback = document.createElement("p");
    notesFeedback.setAttribute("role", "status");
    const updateDraft = () => {
      if (notesInput.value === (run.notes || "")) state.notesDrafts.delete(run.id);
      else state.notesDrafts.set(run.id, notesInput.value);
      notesFeedback.textContent = state.notesDrafts.has(run.id)
        ? "Unsaved notes."
        : "";
    };
    notesInput.addEventListener("input", updateDraft);
    updateDraft();
    notesForm.append(notesField, saveNotes, notesFeedback);
    notesForm.addEventListener("submit", async (event) => {
      event.preventDefault();
      saveNotes.disabled = true;
      const submittedNotes = notesInput.value;
      try {
        const saved = await api(`/runs/${run.id}`, {
          method: "PATCH",
          body: JSON.stringify({ notes: submittedNotes }),
        });
        Object.assign(run, saved);
        const cached = byId(state.runs, run.id);
        if (cached) Object.assign(cached, saved);
        if (state.notesDrafts.get(run.id) === submittedNotes)
          state.notesDrafts.delete(run.id);
        renderRuns();
        if (notesInput.isConnected) {
          updateDraft();
          if (!state.notesDrafts.has(run.id))
            notesFeedback.textContent = "Notes saved.";
        }
      } catch (error) {
        notesFeedback.textContent = error.message;
      } finally {
        saveNotes.disabled = false;
      }
    });
    body.append(notesForm);
    const actions = document.createElement("div");
    actions.className = "detail-actions";
    actions.style.marginTop = "20px";
    lifecycleActions(run, actions);
    const exportButton = document.createElement("button");
    exportButton.className = "button small";
    exportButton.type = "button";
    exportButton.textContent = "Export detail JSON";
    exportButton.addEventListener("click", () =>
      downloadJson(`sentinelml-run-${run.id}.json`, {
        run,
        parameters,
        metrics,
      }),
    );
    actions.append(exportButton);
    body.append(actions);
    overview.append(head, body);
    const params = listPanel(
      "Parameters",
      parameters,
      "parameter",
      run.status === "waiting",
    );
    const mets = listPanel(
      "Metrics",
      metrics,
      "metric",
      run.status === "running",
    );
    const side = document.createElement("div");
    side.style.display = "grid";
    side.style.gap = "16px";
    side.append(params, mets);
    root.replaceChildren(overview, side);
  }
  function lifecycleActions(run, root) {
    const add = (label, action, className = "button small") => {
      const button = document.createElement("button");
      button.className = className;
      button.type = "button";
      button.textContent = label;
      button.addEventListener("click", () => runAction(action));
      root.append(button);
    };
    if (run.status === "waiting") {
      add("Start run", "start", "button primary small");
      add("Cancel", "cancel", "button small");
    }
    if (run.status === "running") {
      add("Complete", "complete", "button primary small");
      add("Mark failed", "fail", "button small danger");
      add("Cancel", "cancel", "button small");
    }
    if (
      run.status === "completed" ||
      run.status === "failed" ||
      run.status === "cancelled"
    )
      add(
        run.is_ignored ? "Unignore" : "Ignore",
        run.is_ignored ? "unignore" : "ignore",
        "button small",
      );
  }
  function listPanel(title, items, kind, editable) {
    const panel = document.createElement("section");
    panel.className = "panel";
    const head = document.createElement("div");
    head.className = "panel-head";
    const h = document.createElement("h2");
    h.textContent = title;
    head.append(h);
    const body = document.createElement("div");
    body.className = "panel-body";
    const list = document.createElement("div");
    list.className = "item-list";
    let editItem;
    if (!items.length) {
      const empty = document.createElement("p");
      empty.className = "lede";
      empty.textContent = `No ${title.toLowerCase()} recorded.`;
      list.append(empty);
    }
    items.forEach((item) => {
      const row = document.createElement("div");
      row.className = "item";
      const left = document.createElement("div");
      const name = document.createElement("div");
      name.className = "name";
      name.textContent = item.name;
      const small = document.createElement("small");
      small.textContent = item.notes || item.value_type || "";
      left.append(name, small);
      const val = document.createElement("span");
      val.className = "value";
      val.textContent =
        kind === "metric" ? Number(item.value).toPrecision(6) : item.value;
      row.append(left, val);
      if (editable) {
        const edit = document.createElement("button");
        edit.type = "button";
        edit.className = "button small";
        edit.textContent = "Edit";
        edit.setAttribute("aria-label", `Edit ${kind} ${item.name}`);
        edit.addEventListener("click", () => editItem(item));
        row.append(edit);
      }
      list.append(row);
    });
    body.append(list);
    if (editable) {
      const form = document.createElement("form");
      form.className = "inline-form";
      const input = document.createElement("input");
      input.name = `${kind}_name`;
      input.autocomplete = "off";
      input.required = true;
      input.maxLength = 255;
      input.placeholder = kind === "metric" ? "metric name" : "parameter name";
      input.setAttribute("aria-label", `${kind} name`);
      const value = document.createElement("input");
      value.name = `${kind}_value`;
      value.autocomplete = "off";
      value.required = true;
      value.placeholder = "value";
      value.setAttribute("aria-label", `${kind} value`);
      if (kind === "metric") {
        value.type = "number";
        value.step = "any";
        value.inputMode = "decimal";
      } else value.maxLength = 255;
      const submit = document.createElement("button");
      submit.className = "button small";
      submit.type = "submit";
      submit.textContent = "Add";
      let editingId = null;
      const cancelEdit = document.createElement("button");
      cancelEdit.type = "button";
      cancelEdit.className = "button small hidden";
      cancelEdit.textContent = "Cancel edit";
      cancelEdit.addEventListener("click", () => {
        editingId = null;
        form.reset();
        submit.textContent = "Add";
        cancelEdit.classList.add("hidden");
        errorMessage.textContent = "";
        input.focus();
      });
      editItem = (item) => {
        editingId = item.id;
        input.value = item.name;
        value.value = item.value;
        submit.textContent = "Save";
        cancelEdit.classList.remove("hidden");
        errorMessage.textContent = "";
        value.focus();
      };
      const inputLabel = document.createElement("label");
      inputLabel.textContent = `${kind === "metric" ? "Metric" : "Parameter"} name`;
      inputLabel.append(input);
      const valueLabel = document.createElement("label");
      valueLabel.textContent = "Value";
      valueLabel.append(value);
      const errorMessage = document.createElement("p");
      errorMessage.className = "inline-error";
      errorMessage.setAttribute("role", "alert");
      form.append(inputLabel, valueLabel, submit, cancelEdit, errorMessage);
      if (kind === "metric") {
        const choices = document.createElement("datalist");
        choices.id = "registered-metrics";
        input.setAttribute("list", choices.id);
        state.directions.forEach((direction) => {
          const option = document.createElement("option");
          option.value = direction.name;
          choices.append(option);
        });
        const register = document.createElement("button");
        register.type = "button";
        register.className = "button small";
        register.textContent = "Register a metric";
        register.addEventListener("click", () => openResource("metric-direction"));
        const hint = document.createElement("p");
        hint.className = "lede";
        hint.textContent = "Choose a registered metric, or register a name and direction first.";
        body.append(hint, register, choices);
      }
      form.addEventListener("submit", async (event) => {
        event.preventDefault();
        if (kind === "metric" && !Number.isFinite(Number(value.value))) {
          toast("Metric value must be a finite number.", true);
          return;
        }
        submit.disabled = true;
        cancelEdit.disabled = true;
        $$(".item button", list).forEach((button) => (button.disabled = true));
        const runId = state.currentRun;
        const bodyData =
          kind === "metric"
            ? { name: input.value, value: Number(value.value) }
            : { name: input.value, value: value.value };
        try {
          await api(
            `/runs/${runId}/${kind === "metric" ? "metrics" : "parameters"}/${editingId ?? ""}`,
            { method: editingId === null ? "POST" : "PATCH", body: JSON.stringify(bodyData) },
          );
          if (
            state.currentRun === runId &&
            $("#view-detail").classList.contains("active")
          ) await openDetail(runId);
        } catch (error) {
          errorMessage.textContent = error.message;
        } finally {
          submit.disabled = false;
          cancelEdit.disabled = false;
          $$(".item button", list).forEach((button) => (button.disabled = false));
        }
      });
      body.append(form);
    }
    panel.append(head, body);
    return panel;
  }
  async function runAction(action) {
    state.action = action;
    const needsReason = ["fail", "cancel", "ignore"].includes(action);
    if (!needsReason) return executeAction(action, "");
    $("#action-title").textContent =
      action === "ignore"
        ? "Ignore run"
        : action === "fail"
          ? "Mark run failed"
          : "Cancel run";
    $("#action-reason-label").textContent =
      action === "ignore" ? "Ignore reason" : "Reason";
    $("#action-reason").value = "";
    $("#action-reason").required = action === "fail" || action === "ignore";
    $("#action-error").textContent = "";
    $("#action-dialog").showModal();
    $("#action-reason").focus();
  }
  async function executeAction(action, reason) {
    if (state.mutating) return;
    state.mutating = true;
    const runId = state.currentRun;
    const confirm = $('#action-form button[type="submit"]');
    confirm.disabled = true;
    $$("#detail-content .detail-actions button").forEach(
      (button) => (button.disabled = true),
    );
    try {
      let path = `/runs/${runId}/${action}`;
      if (reason)
        path +=
          action === "ignore"
            ? `?ignore_reason=${encodeURIComponent(reason)}`
            : `?reason=${encodeURIComponent(reason)}`;
      await api(path, { method: "POST" });
      $("#action-dialog").close();
      await loadWorkspace();
      if (state.currentRun === runId) await openDetail(runId);
    } catch (error) {
      $("#action-error").textContent = error.message;
      $("#action-dialog").close();
      const detailState = $("#detail-state");
      detailState.className = "";
      showError(detailState, error, () => openDetail(state.currentRun));
    } finally {
      confirm.disabled = false;
      state.mutating = false;
      $$("#detail-content .detail-actions button").forEach(
        (button) => (button.disabled = false),
      );
    }
  }
  function download(filename, content, type) {
    const link = document.createElement("a");
    link.href = URL.createObjectURL(new Blob([content], { type }));
    link.download = filename;
    link.click();
    URL.revokeObjectURL(link.href);
  }
  function downloadJson(filename, data) {
    download(filename, JSON.stringify(data, null, 2), "application/json");
  }
  function exportCsv() {
    const headers = [
      "run_id",
      "project",
      "model",
      "dataset",
      "status",
      "start_time",
      "end_time",
      "notes",
      "ignored",
    ];
    const rows = state.filtered.map((run) =>
      [
        run.id,
        nameFor(state.projects, run.project_id),
        nameFor(state.models, run.model_id),
        nameFor(state.datasets, run.dataset_id),
        run.status,
        run.start_time,
        run.end_time,
        run.notes,
        run.is_ignored,
      ]
        .map(csvCell)
        .join(","),
    );
    download(
      "sentinelml-filtered-runs.csv",
      [headers.join(","), ...rows].join("\r\n") + "\r\n",
      "text/csv;charset=utf-8",
    );
    toast(
      `Exported ${state.filtered.length} filtered run${state.filtered.length === 1 ? "" : "s"} (current filters + basic metadata).`,
    );
  }
  function exportJson() {
    downloadJson("sentinelml-filtered-runs.json", state.filtered);
    toast(
      `Exported ${state.filtered.length} filtered run${state.filtered.length === 1 ? "" : "s"} (current filters + basic metadata).`,
    );
  }
  async function openComparison() {
    setView("compare");
    const root = $("#comparison");
    if (state.selected.size < 2) {
      root.className = "panel empty";
      root.textContent =
        "Select two to four runs in Experiments to compare their context and results.";
      return;
    }
    root.className = "panel";
    root.replaceChildren();
    const loading = document.createElement("div");
    loading.className = "loading";
    loading.textContent = "Loading run context…";
    root.append(loading);
    try {
      const details = await Promise.all(
        [...state.selected].map(async (id) => ({
          ...(await api(`/runs/${id}`)),
          parameters: await api(`/runs/${id}/parameters/`),
          metrics: await api(`/runs/${id}/metrics/`),
        })),
      );
      renderComparison(details, root);
    } catch (error) {
      showError(root, error, openComparison);
    }
  }

  function renderComparison(details, root) {
    root.replaceChildren();
    const head = document.createElement("div");
    head.className = "panel-head";
    const title = document.createElement("h2");
    title.textContent = `${details.length} selected runs`;
    const exportButton = document.createElement("button");
    exportButton.className = "button small";
    exportButton.type = "button";
    exportButton.textContent = "Export comparison JSON";
    exportButton.addEventListener("click", () =>
      downloadJson("sentinelml-comparison.json", details),
    );
    head.append(title, exportButton);
    root.append(head);
    const scopes = new Set(
      details.map((detail) => `${detail.project_id}:${detail.dataset_id}`),
    );
    if (scopes.size > 1) {
      const warning = document.createElement("div");
      warning.className = "error";
      warning.textContent =
        "These runs use different projects or datasets. Metric values may not be directly comparable.";
      root.append(warning);
    }
    const body = document.createElement("div");
    body.className = "panel-body table-wrap";
    const allParams = [
      ...new Set(
        details.flatMap((detail) => detail.parameters.map((item) => item.name)),
      ),
    ];
    const metrics = [
      ...new Set(
        details.flatMap((detail) => detail.metrics.map((item) => item.name)),
      ),
    ].map((name) => ({
      name,
      direction: state.directions.find((item) => item.name === name),
    }));
    const table = document.createElement("table");
    table.className = "compare-table";
    const thead = document.createElement("thead");
    const headerRow = document.createElement("tr");
    ["Field", ...details.map((detail) => `run-${detail.id}`)].forEach(
      (value) => {
        const cell = document.createElement("th");
        cell.textContent = value;
        headerRow.append(cell);
      },
    );
    thead.append(headerRow);
    table.append(thead);
    const tbody = document.createElement("tbody");
    const addRows = (label, names, getter) => {
      const group = document.createElement("tr");
      const groupCell = document.createElement("th");
      groupCell.colSpan = details.length + 1;
      groupCell.textContent = label;
      group.append(groupCell);
      tbody.append(group);
      names.forEach((name) => {
        const values = details.map((detail) => getter(detail, name));
        const row = document.createElement("tr");
        const nameCell = document.createElement("td");
        nameCell.textContent = name;
        row.append(nameCell);
        values.forEach((value) => {
          const cell = document.createElement("td");
          cell.textContent =
            typeof value === "number"
              ? String(Number(value.toPrecision(6)))
              : text(value);
          if (typeof value === "number") cell.title = String(value);
          if (values.some((other) => String(other) !== String(value)))
            cell.className = "diff";
          row.append(cell);
        });
        tbody.append(row);
      });
    };
    addRows(
      "Run metadata",
      ["status", "ignored", "project", "model", "dataset", "notes"],
      (detail, name) =>
        ({
          status: detail.status,
          ignored: detail.is_ignored ? "Yes" : "No",
          project: nameFor(state.projects, detail.project_id),
          model: nameFor(state.models, detail.model_id),
          dataset: nameFor(state.datasets, detail.dataset_id),
          notes: detail.notes,
        })[name],
    );
    addRows(
      "Parameters",
      allParams,
      (detail, name) =>
        detail.parameters.find((item) => item.name === name)?.value,
    );
    addRows(
      "Metrics · direction in brackets",
      metrics.map(
        (metric) =>
          `${metric.name} [${metric.direction ? (metric.direction.maximize ? "maximize" : "minimize") : "direction unknown"}]`,
      ),
      (detail, label) =>
        detail.metrics.find(
          (item) => item.name === label.slice(0, label.lastIndexOf(" [")),
        )?.value,
    );
    table.append(tbody);
    body.append(table);
    root.append(body);
    if (!metrics.length) return;
    const chart = document.createElement("div");
    chart.className = "panel-body";
    const heading = document.createElement("h3");
    heading.textContent =
      "Scalar metric comparison · position within selected range";
    heading.style.marginBottom = "15px";
    chart.append(heading);
    const bars = document.createElement("div");
    bars.className = "bar-chart";
    metrics.forEach((metricInfo) => {
      const values = details
        .map((detail) =>
          Number(
            detail.metrics.find((item) => item.name === metricInfo.name)?.value,
          ),
        )
        .filter(Number.isFinite);
      const low = Math.min(...values);
      const high = Math.max(...values);
      const scale = Math.max(Math.abs(low), Math.abs(high), 1);
      const span = high / scale - low / scale;
      const range = document.createElement("p");
      range.className = "chart-range";
      range.textContent = `${metricInfo.name}: ${low} to ${high}${span === 0 ? " (all equal)" : ""}`;
      bars.append(range);
      details.forEach((detail) => {
        const metric = detail.metrics.find(
          (item) => item.name === metricInfo.name,
        );
        if (!metric) return;
        const row = document.createElement("div");
        row.className = "bar-row";
        const label = document.createElement("span");
        label.textContent = `run-${detail.id} · ${metricInfo.name}`;
        const track = document.createElement("div");
        track.className = "bar-track";
        const fill = document.createElement("div");
        fill.className = "bar-fill";
        fill.style.left = `${span === 0 ? 50 : ((Number(metric.value) / scale - low / scale) / span) * 100}%`;
        track.append(fill);
        const value = document.createElement("span");
        value.className = "mono";
        value.textContent = Number(metric.value).toPrecision(6);
        row.append(label, track, value);
        bars.append(row);
      });
    });
    chart.append(bars);
    root.append(chart);
  }

  $$("[data-period]").forEach((button) =>
    button.addEventListener("click", () => {
      state.activityPeriod = Number(button.dataset.period);
      state.activityDate = null;
      $$("[data-period]").forEach((item) =>
        item.setAttribute("aria-pressed", String(item === button)),
      );
      renderInsights();
      renderRuns();
    }),
  );
  $("#clear-day").addEventListener("click", () => {
    state.activityDate = null;
    $$(".activity-bar").forEach((item) =>
      item.setAttribute("aria-pressed", "false"),
    );
    renderRuns();
  });
  $("#resource-form").addEventListener("submit", submitResource);
  $("#action-form").addEventListener("submit", (event) => {
    event.preventDefault();
    executeAction(state.action, $("#action-reason").value.trim());
  });
  $$("[data-close-dialog]").forEach((button) =>
    button.addEventListener("click", () => $("#form-dialog").close()),
  );
  $$("[data-close-action]").forEach((button) =>
    button.addEventListener("click", () => $("#action-dialog").close()),
  );
  $$("dialog").forEach((dialog) =>
    dialog.addEventListener("click", (event) => {
      if (event.target === dialog) dialog.close();
    }),
  );
  $$("[data-nav]").forEach((button) =>
    button.addEventListener("click", () => {
      const target = button.dataset.nav;
      if (
        target === "experiments" ||
        target === "projects" ||
        target === "catalog"
      )
        setView(target);
      else if (target === "compare") {
        openComparison();
      }
    }),
  );
  $$('[data-action="new-project"]').forEach((button) =>
    button.addEventListener("click", () => openResource("project")),
  );
  $$('[data-action="new-dataset"]').forEach((button) =>
    button.addEventListener("click", () => openResource("dataset")),
  );
  $$('[data-action="new-model"]').forEach((button) =>
    button.addEventListener("click", () => openResource("model")),
  );
  $$('[data-action="new-run"]').forEach((button) =>
    button.addEventListener("click", () =>
      state.projects.length && state.models.length && state.datasets.length
        ? openResource("run")
        : toast("Create a project, model, and dataset first.", true),
    ),
  );
  $('[data-action="refresh-runs"]').addEventListener("click", loadWorkspace);
  $('[data-action="export-csv"]').addEventListener("click", exportCsv);
  $('[data-action="export-json"]').addEventListener("click", exportJson);
  ["#run-search", "#global-search"].forEach((selector) =>
    $(selector).addEventListener("input", () => {
      const value = $(selector).value;
      $("#run-search").value = value;
      $("#global-search").value = value;
      renderRuns();
    }),
  );
  ["#project-filter", "#status-filter"].forEach((selector) =>
    $(selector).addEventListener("change", renderRuns),
  );
  $$("#run-table-wrap th button").forEach((button) =>
    button.addEventListener("click", () => {
      const key = button.dataset.sort;
      state.sort = {
        key,
        dir: state.sort.key === key ? state.sort.dir * -1 : 1,
      };
      renderRuns();
    }),
  );
  $("#select-all").addEventListener("change", (event) => {
    state.filtered.forEach((run) => {
      if (event.target.checked && state.selected.size < 4)
        state.selected.add(run.id);
      else if (!event.target.checked) state.selected.delete(run.id);
    });
    renderRuns();
  });
  document.addEventListener("keydown", (event) => {
    if (
      (event.key === "/" ||
        (event.key.toLowerCase() === "k" &&
          (event.metaKey || event.ctrlKey))) &&
      document.activeElement?.tagName !== "INPUT" &&
      document.activeElement?.tagName !== "TEXTAREA" &&
      !document.querySelector("dialog[open]")
    ) {
      event.preventDefault();
      $("#global-search").focus();
    }
  });
  window.addEventListener("beforeunload", (event) => {
    if (!state.notesDrafts.size) return;
    event.preventDefault();
    event.returnValue = "";
  });
  loadWorkspace();
})();
