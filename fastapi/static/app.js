(function () {
  const allowedExtensions = [".mp4", ".avi", ".mov", ".mkv"];
  const translations = {
    en: {
      heroTitle: "Video Upload & Retrieval Console",
      heroSubtitle: "Choose a database before querying. Uploading a new video automatically creates and switches to a fresh database.",
      databaseSectionTitle: "1. Select Database",
      databaseSectionDesc: "Query stays disabled until a database is selected.",
      refreshListBtn: "Refresh",
      currentDatabaseLabel: "Current Database",
      configuredDefaultLabel: "Configured Default Database",
      notSelected: "Not selected",
      currentDbMetaEmpty: "Select one from the list below, or upload a new video to create one automatically.",
      databaseListLabel: "Local Database List",
      loadingDatabases: "Loading database list...",
      noDatabases: "No database available",
      selectDatabasePlaceholder: "Choose a database",
      useSelectedDatabaseBtn: "Use Selected Database",
      databaseHint: "A newly uploaded video will also be auto-selected after indexing finishes.",
      uploadSectionTitle: "2. Upload Video & Build Database",
      uploadSectionDesc: "Drag and drop is supported. Allowed formats: MP4, AVI, MOV, MKV. Maximum file size: {maxUploadMB} MB per file.",
      dropZoneAria: "Drag videos here or click to choose files",
      dropZoneTitle: "Drag videos here, or click to choose files",
      noFileSelected: "No file selected",
      selectedFilesSummary: "{count} files · {preview}{remain}",
      modelLabel: "Model",
      targetClassesPlaceholder: "person,car",
      waitingUpload: "Waiting for upload",
      uploadBtn: "Upload and Create Database",
      querySectionTitle: "3. Query",
      querySectionDesc: "Query is only available after a database has been selected.",
      queryDbStateEmpty: "No database selected",
      queryDbStateSelected: "Current database: {label}",
      queryInputLabel: "Query",
      queryInputPlaceholder: "For example: a group of people stands near the left-side bleachers",
      topKLabel: "Top K",
      queryBtnDisabled: "Choose a database first",
      queryBtnEnabled: "Run Query",
      queryRequirementAlert: "Select a database first, or upload a new video and wait for the database to be created.",
      feedbackTitle: "Activity",
      feedbackInit: "Page loaded. Reading service status...",
      queryResultTitle: "Query Result",
      queryResultInit: "Results will appear here after the query finishes.",
      serviceChecking: "Checking service status...",
      serviceHealthy: "Service is healthy. Execution mode: {mode}",
      serviceHealthFailed: "Failed to read service status",
      statusRefreshed: "Status refreshed. You can select a database, or upload a new video to build one.",
      statusRefreshFailed: "Status refresh failed: {message}",
      selectVideoFirst: "Please choose at least one video file first.",
      fileTypeUnsupported: "Unsupported file type. Please upload MP4, AVI, MOV, or MKV.",
      fileTooLarge: "File is too large. Maximum allowed size is {size}.",
      fileReadySingle: "1 file selected. Ready to upload.",
      fileReadyBatch: "{count} files selected. Ready to upload.",
      uploadStart: "Uploading {count} files and creating one shared database. Please wait...",
      uploadProgressUnknown: "Uploading...",
      uploadProgressPercent: "Uploading: {percent}%",
      uploadProcessing: "Upload finished. Server is processing and building the database...",
      uploadSyncing: "Database created. Syncing the new dataset to the page...",
      uploadDone: "Upload finished. One shared database has been created and selected automatically.",
      uploadSuccess: "Upload succeeded\njob_id: {jobId}\nrefine_mode: {refineMode}\nfile_count: {fileCount}\nevents_count: {eventsCount}\nclip_count: {clipCount}",
      uploadQueryHint: "Switched to the new shared database for {fileCount} files.\nYou can query immediately across the whole batch.",
      uploadFailed: "Upload failed",
      uploadFailedWithMessage: "Upload failed: {message}",
      uploadRequestFailed: "Upload request failed. Please verify the service is running.",
      chooseDatabaseFromList: "Please choose a database from the list first.",
      databaseSelectFailed: "Database selection failed",
      databaseSelectFailedWithMessage: "Database selection failed: {message}",
      databaseSwitched: "Switched to database: {label}",
      queryNeedDatabase: "Please select a database before querying.",
      queryNeedText: "Please enter a query.",
      queryRunning: "Running query. Please wait...",
      queryDone: "Query finished in {elapsedMs} ms.",
      queryFailed: "Query failed.",
      queryFailedWithMessage: "Query failed: {message}",
      queryResultFormat:
        "answer:\n{answer}\n\nelapsed_ms: {elapsedMs}\n\nnode_trace:\n{nodeTrace}\n\nrows:\n{rows}",
      dbMeta: "SQLite: {sqlitePath}\nChroma: {chromaPath}\nNamespace: {namespace}",
      dbSourceUploaded: "uploaded",
      dbSourceConfigured: "configured",
    },
    zh: {
      heroTitle: "视频上传与检索控制台",
      heroSubtitle: "先选择数据库，再执行查询。上传新视频后会自动创建并切换到该视频对应的新数据库。",
      databaseSectionTitle: "1. 选择数据库",
      databaseSectionDesc: "未选中数据库前，查询功能保持禁用。",
      refreshListBtn: "刷新列表",
      currentDatabaseLabel: "当前选中数据库",
      configuredDefaultLabel: "当前配置数据库",
      notSelected: "未选择",
      currentDbMetaEmpty: "请先从下方列表中选择，或上传新视频自动创建。",
      databaseListLabel: "本地数据库列表",
      loadingDatabases: "正在加载数据库列表...",
      noDatabases: "暂无可用数据库",
      selectDatabasePlaceholder: "请选择一个数据库",
      useSelectedDatabaseBtn: "使用选中的数据库",
      databaseHint: "上传视频成功后也会自动选中对应的新数据库。",
      uploadSectionTitle: "2. 上传视频并建库",
      uploadSectionDesc: "支持拖拽上传。允许格式：MP4、AVI、MOV、MKV。每个文件大小上限 {maxUploadMB} MB。",
      dropZoneAria: "拖拽视频到这里或点击选择文件",
      dropZoneTitle: "拖拽视频到这里，或点击选择多个文件",
      noFileSelected: "尚未选择文件",
      selectedFilesSummary: "已选择 {count} 个文件 · {preview}{remain}",
      modelLabel: "模型",
      targetClassesPlaceholder: "person,car",
      waitingUpload: "等待上传",
      uploadBtn: "上传并创建数据库",
      querySectionTitle: "3. 查询",
      querySectionDesc: "只有在数据库已选中时才能执行查询。",
      queryDbStateEmpty: "当前未选择数据库",
      queryDbStateSelected: "当前数据库：{label}",
      queryInputLabel: "查询文本",
      queryInputPlaceholder: "例如：a group of people stands near the left-side bleachers",
      topKLabel: "返回条数",
      queryBtnDisabled: "请先选择数据库",
      queryBtnEnabled: "开始查询",
      queryRequirementAlert: "需要先选择数据库，或者上传新视频完成自动建库后，才能开始查询。",
      feedbackTitle: "运行反馈",
      feedbackInit: "页面已加载，正在读取服务状态。",
      queryResultTitle: "查询结果",
      queryResultInit: "完成查询后，结果会显示在这里。",
      serviceChecking: "正在检查服务状态...",
      serviceHealthy: "服务正常，执行模式：{mode}",
      serviceHealthFailed: "服务状态获取失败",
      statusRefreshed: "状态已刷新。可以选择数据库，或上传新视频自动建库。",
      statusRefreshFailed: "状态刷新失败：{message}",
      selectVideoFirst: "请先选择至少一个视频文件。",
      fileTypeUnsupported: "文件类型不支持，请上传 MP4、AVI、MOV 或 MKV。",
      fileTooLarge: "文件过大，单文件大小不能超过 {size}。",
      fileReadySingle: "已选择 1 个文件，可以开始上传。",
      fileReadyBatch: "已选择 {count} 个文件，可以开始上传。",
      uploadStart: "开始上传 {count} 个文件并创建共用数据库，请稍候...",
      uploadProgressUnknown: "正在上传...",
      uploadProgressPercent: "上传中：{percent}%",
      uploadProcessing: "文件上传完成，服务端正在处理并创建数据库...",
      uploadSyncing: "数据库已创建，正在把新数据集同步到页面...",
      uploadDone: "上传完成，共用数据库已创建并自动切换。",
      uploadSuccess: "上传成功\njob_id: {jobId}\nrefine_mode: {refineMode}\nfile_count: {fileCount}\nevents_count: {eventsCount}\nclip_count: {clipCount}",
      uploadQueryHint: "已自动切换到这批文件共用的新数据库。\n现在可以直接跨整批视频查询。",
      uploadFailed: "上传失败。",
      uploadFailedWithMessage: "上传失败：{message}",
      uploadRequestFailed: "上传请求失败，请检查服务是否正常运行。",
      chooseDatabaseFromList: "请先从列表中选择一个数据库。",
      databaseSelectFailed: "数据库选择失败",
      databaseSelectFailedWithMessage: "数据库选择失败：{message}",
      databaseSwitched: "已切换数据库：{label}",
      queryNeedDatabase: "请先选择数据库后再查询。",
      queryNeedText: "请输入查询内容。",
      queryRunning: "正在查询，请稍候...",
      queryDone: "查询完成，耗时 {elapsedMs} ms。",
      queryFailed: "查询失败。",
      queryFailedWithMessage: "查询失败：{message}",
      queryResultFormat:
        "answer:\n{answer}\n\nelapsed_ms: {elapsedMs}\n\nnode_trace:\n{nodeTrace}\n\nrows:\n{rows}",
      dbMeta: "SQLite: {sqlitePath}\nChroma: {chromaPath}\nNamespace: {namespace}",
      dbSourceUploaded: "上传生成",
      dbSourceConfigured: "当前配置",
    },
  };
  const state = {
    selectedFiles: [],
    currentDatabase: null,
    databases: [],
    serviceHealthy: false,
    language: window.APP_CONFIG.defaultLanguage || "en",
  };

  const el = {
    html: document.documentElement,
    serviceStatusDot: document.getElementById("service-status-dot"),
    serviceStatusText: document.getElementById("service-status-text"),
    langEnBtn: document.getElementById("lang-en-btn"),
    langZhBtn: document.getElementById("lang-zh-btn"),
    currentDbLabel: document.getElementById("current-db-label"),
    currentDbMeta: document.getElementById("current-db-meta"),
    databaseSelect: document.getElementById("database-select"),
    refreshDatabasesBtn: document.getElementById("refresh-databases-btn"),
    selectDatabaseBtn: document.getElementById("select-database-btn"),
    databaseHint: document.getElementById("database-hint"),
    dropZone: document.getElementById("drop-zone"),
    fileInput: document.getElementById("file-input"),
    selectedFileText: document.getElementById("selected-file-text"),
    modelPathInput: document.getElementById("model-path-input"),
    trackerInput: document.getElementById("tracker-input"),
    confInput: document.getElementById("conf-input"),
    iouInput: document.getElementById("iou-input"),
    refineModeSelect: document.getElementById("refine-mode-select"),
    refineModelInput: document.getElementById("refine-model-input"),
    targetClassesInput: document.getElementById("target-classes-input"),
    uploadBtn: document.getElementById("upload-btn"),
    uploadProgressBar: document.getElementById("upload-progress-bar"),
    uploadProgressText: document.getElementById("upload-progress-text"),
    queryDbState: document.getElementById("query-db-state"),
    queryInput: document.getElementById("query-input"),
    topKInput: document.getElementById("top-k-input"),
    queryBtn: document.getElementById("query-btn"),
    queryRequirementAlert: document.getElementById("query-requirement-alert"),
    feedbackBox: document.getElementById("feedback-box"),
    queryResult: document.getElementById("query-result"),
  };

  function t(key, vars = {}) {
    const pack = translations[state.language] || translations.en;
    const fallback = translations.en[key] || key;
    const template = pack[key] || fallback;
    return template.replace(/\{(\w+)\}/g, (_, name) => String(vars[name] ?? ""));
  }

  function applyStaticTranslations() {
    el.html.lang = state.language === "zh" ? "zh-CN" : "en";
    document.querySelectorAll("[data-i18n]").forEach((node) => {
      if (node.dataset.i18n === "uploadSectionDesc") {
        node.textContent = t("uploadSectionDesc", {
          maxUploadMB: Math.round(window.APP_CONFIG.maxUploadBytes / (1024 * 1024)),
        });
        return;
      }
      node.textContent = t(node.dataset.i18n);
    });
    document.querySelectorAll("[data-i18n-placeholder]").forEach((node) => {
      node.setAttribute("placeholder", t(node.dataset.i18nPlaceholder));
    });
    el.dropZone.setAttribute("aria-label", t("dropZoneAria"));
    el.serviceStatusText.textContent = state.serviceHealthy
      ? el.serviceStatusText.textContent
      : t("serviceChecking");
    el.langEnBtn.classList.toggle("active", state.language === "en");
    el.langZhBtn.classList.toggle("active", state.language === "zh");
  }

  function setLanguage(language) {
    state.language = language === "zh" ? "zh" : "en";
    window.localStorage.setItem("capstone_fastapi_lang", state.language);
    applyStaticTranslations();
    setSelectedFiles(state.selectedFiles);
    renderDatabaseOptions();
    updateQueryState();
  }

  function setFeedback(message) {
    el.feedbackBox.textContent = message;
  }

  function setResult(message) {
    el.queryResult.textContent = message;
  }

  function setUploadProgress(percent, message) {
    const normalized = Math.max(0, Math.min(100, Math.round(percent)));
    el.uploadProgressBar.style.width = `${normalized}%`;
    el.uploadProgressBar.textContent = `${normalized}%`;
    el.uploadProgressText.textContent = message;
  }

  function resetUploadProgress() {
    setUploadProgress(0, t("waitingUpload"));
  }

  function formatBytes(size) {
    if (!Number.isFinite(size)) return "-";
    const units = ["B", "KB", "MB", "GB"];
    let value = size;
    let unit = units[0];
    for (let i = 0; i < units.length; i += 1) {
      unit = units[i];
      if (value < 1024 || i === units.length - 1) break;
      value /= 1024;
    }
    return `${value.toFixed(value >= 10 ? 0 : 1)} ${unit}`;
  }

  function safeJson(value) {
    return JSON.stringify(value, null, 2);
  }

  function localizedSource(source) {
    return source === "configured" ? t("dbSourceConfigured") : t("dbSourceUploaded");
  }

  function displayDatabaseLabel(item) {
    if (!item) return "";
    if (item.id === "configured-default") {
      return t("configuredDefaultLabel");
    }
    return item.label || item.id || "";
  }

  function updateServiceStatus(healthy, text) {
    state.serviceHealthy = healthy;
    el.serviceStatusDot.className = "status-dot";
    if (healthy) {
      el.serviceStatusDot.classList.add("online");
    } else {
      el.serviceStatusDot.classList.add("warning");
    }
    el.serviceStatusText.textContent = text;
  }

  function updateQueryState() {
    const selected = state.currentDatabase;
    const hasSelectedDb = Boolean(selected && selected.id);
    el.queryBtn.disabled = !hasSelectedDb;
    el.queryBtn.textContent = hasSelectedDb ? t("queryBtnEnabled") : t("queryBtnDisabled");
    el.queryRequirementAlert.classList.toggle("d-none", hasSelectedDb);
    el.queryDbState.textContent = hasSelectedDb
      ? t("queryDbStateSelected", { label: displayDatabaseLabel(selected) })
      : t("queryDbStateEmpty");
    el.currentDbLabel.textContent = hasSelectedDb ? displayDatabaseLabel(selected) : t("notSelected");
    el.currentDbMeta.textContent = hasSelectedDb
      ? t("dbMeta", {
          sqlitePath: selected.sqlite_path,
          chromaPath: selected.chroma_path,
          namespace: selected.chroma_namespace,
        })
      : t("currentDbMetaEmpty");
  }

  function renderDatabaseOptions() {
    const items = state.databases;
    el.databaseSelect.innerHTML = "";
    if (!items.length) {
      const option = document.createElement("option");
      option.value = "";
      option.textContent = t("noDatabases");
      el.databaseSelect.appendChild(option);
      return;
    }
    const placeholder = document.createElement("option");
    placeholder.value = "";
    placeholder.textContent = t("selectDatabasePlaceholder");
    el.databaseSelect.appendChild(placeholder);

    items.forEach((item) => {
      const option = document.createElement("option");
      option.value = item.id;
      option.textContent = `${displayDatabaseLabel(item)} [${localizedSource(item.source)}]`;
      if (state.currentDatabase && state.currentDatabase.id === item.id) {
        option.selected = true;
      }
      el.databaseSelect.appendChild(option);
    });
  }

  async function loadCurrentDatabase() {
    const response = await fetch("/api/v1/databases/current", { cache: "no-store" });
    if (!response.ok) {
      throw new Error(t("serviceHealthFailed"));
    }
    const payload = await response.json();
    state.currentDatabase = payload.selected_database || null;
    updateQueryState();
  }

  async function loadDatabases() {
    const response = await fetch("/api/v1/databases", { cache: "no-store" });
    if (!response.ok) {
      throw new Error(t("databaseSelectFailed"));
    }
    const payload = await response.json();
    state.databases = payload.databases || [];
    renderDatabaseOptions();
  }

  async function loadHealth() {
    const response = await fetch("/healthz", { cache: "no-store" });
    if (!response.ok) {
      throw new Error(t("serviceHealthFailed"));
    }
    const payload = await response.json();
    updateServiceStatus(true, t("serviceHealthy", { mode: payload.execution_mode }));
  }

  async function refreshAllStatus() {
    try {
      await loadHealth();
      await loadCurrentDatabase();
      await loadDatabases();
      setFeedback(t("statusRefreshed"));
    } catch (error) {
      updateServiceStatus(false, t("serviceHealthFailed"));
      setFeedback(t("statusRefreshFailed", { message: error.message }));
    }
  }

  function validateFile(file) {
    if (!file) {
      throw new Error(t("selectVideoFirst"));
    }
    const lowerName = String(file.name || "").toLowerCase();
    const matches = allowedExtensions.some((ext) => lowerName.endsWith(ext));
    if (!matches) {
      throw new Error(t("fileTypeUnsupported"));
    }
    if (file.size > window.APP_CONFIG.maxUploadBytes) {
      throw new Error(t("fileTooLarge", { size: formatBytes(window.APP_CONFIG.maxUploadBytes) }));
    }
  }

  function upsertDatabaseOption(item) {
    if (!item || !item.id) return;
    const others = state.databases.filter((entry) => entry.id !== item.id);
    state.databases = [{ ...item, selected: true }, ...others.map((entry) => ({ ...entry, selected: false }))];
    state.currentDatabase = { ...item, selected: true };
    renderDatabaseOptions();
    updateQueryState();
  }

  function validateFiles(files) {
    if (!files.length) {
      throw new Error(t("selectVideoFirst"));
    }
    files.forEach((file) => validateFile(file));
  }

  function setSelectedFiles(files) {
    state.selectedFiles = files;
    if (!files.length) {
      el.selectedFileText.textContent = t("noFileSelected");
      return;
    }
    if (files.length === 1) {
      const file = files[0];
      el.selectedFileText.textContent = `${file.name} · ${formatBytes(file.size)}`;
      return;
    }
    const preview = files.slice(0, 3).map((file) => file.name).join(", ");
    const remain = files.length > 3 ? ` +${files.length - 3}` : "";
    el.selectedFileText.textContent = t("selectedFilesSummary", {
      count: files.length,
      preview,
      remain,
    });
  }

  function bindDragAndDrop() {
    const onDragEnter = (event) => {
      event.preventDefault();
      el.dropZone.classList.add("drag-active");
    };
    const onDragLeave = (event) => {
      event.preventDefault();
      if (event.target === el.dropZone || event.relatedTarget === null) {
        el.dropZone.classList.remove("drag-active");
      }
    };
    const onDragOver = (event) => {
      event.preventDefault();
      el.dropZone.classList.add("drag-active");
    };
    const onDrop = (event) => {
      event.preventDefault();
      el.dropZone.classList.remove("drag-active");
      const files = event.dataTransfer && event.dataTransfer.files ? Array.from(event.dataTransfer.files) : [];
      try {
        validateFiles(files);
        setSelectedFiles(files);
        setFeedback(files.length === 1 ? t("fileReadySingle") : t("fileReadyBatch", { count: files.length }));
      } catch (error) {
        setFeedback(error.message);
        setSelectedFiles([]);
      }
    };
    ["dragenter", "dragover"].forEach((name) => {
      el.dropZone.addEventListener(name, onDragEnter);
    });
    el.dropZone.addEventListener("dragleave", onDragLeave);
    el.dropZone.addEventListener("drop", onDrop);
    el.dropZone.addEventListener("click", () => el.fileInput.click());
    el.dropZone.addEventListener("keydown", (event) => {
      if (event.key === "Enter" || event.key === " ") {
        event.preventDefault();
        el.fileInput.click();
      }
    });
    el.fileInput.addEventListener("change", (event) => {
      const files = event.target.files ? Array.from(event.target.files) : [];
      try {
        validateFiles(files);
        setSelectedFiles(files);
        setFeedback(files.length === 1 ? t("fileReadySingle") : t("fileReadyBatch", { count: files.length }));
      } catch (error) {
        setFeedback(error.message);
        setSelectedFiles([]);
      }
    });
  }

  function uploadVideo() {
    try {
      validateFiles(state.selectedFiles);
    } catch (error) {
      setFeedback(error.message);
      return;
    }

    const formData = new FormData();
    state.selectedFiles.forEach((file) => formData.append("files", file));
    formData.append("tracker", el.trackerInput.value.trim() || "botsort_reid");
    formData.append("model_path", el.modelPathInput.value.trim() || "n");
    formData.append("conf", el.confInput.value.trim() || "0.25");
    formData.append("iou", el.iouInput.value.trim() || "0.25");
    formData.append("refine_mode", el.refineModeSelect.value);
    formData.append("refine_model", el.refineModelInput.value.trim() || "gpt-5.4-mini");
    formData.append("import_to_db", "true");
    if (el.targetClassesInput.value.trim()) {
      formData.append("target_classes", el.targetClassesInput.value.trim());
    }

    const xhr = new XMLHttpRequest();
    xhr.open("POST", "/api/v1/video/upload", true);
    xhr.upload.addEventListener("progress", (event) => {
      if (!event.lengthComputable) {
        el.uploadProgressText.textContent = t("uploadProgressUnknown");
        return;
      }
      const rawPercent = Math.min(100, Math.round((event.loaded / event.total) * 100));
      const displayPercent = rawPercent >= 100 ? 95 : rawPercent;
      setUploadProgress(displayPercent, t("uploadProgressPercent", { percent: displayPercent }));
    });
    xhr.addEventListener("loadstart", () => {
      el.uploadBtn.disabled = true;
      resetUploadProgress();
      setFeedback(t("uploadStart", { count: state.selectedFiles.length }));
    });
    xhr.addEventListener("load", async () => {
      el.uploadBtn.disabled = false;
      try {
        const payload = JSON.parse(xhr.responseText || "{}");
        if (xhr.status < 200 || xhr.status >= 300) {
          throw new Error(payload.detail || "上传失败");
        }
        setUploadProgress(96, t("uploadProcessing"));
        if (payload.selected_database) {
          upsertDatabaseOption(payload.selected_database);
        }
        setUploadProgress(98, t("uploadSyncing"));
        await Promise.all([loadCurrentDatabase(), loadDatabases()]);
        setUploadProgress(100, t("uploadDone"));
        setFeedback(
          t("uploadSuccess", {
            jobId: payload.job_id,
            refineMode: payload.refine_mode,
            fileCount: payload.file_count,
            eventsCount: payload.events_count,
            clipCount: payload.clip_count,
          })
        );
        const queryHint = t("uploadQueryHint", { fileCount: payload.file_count, filename: payload.filename });
        setResult(queryHint);
        setSelectedFiles([]);
        el.fileInput.value = "";
        window.setTimeout(() => resetUploadProgress(), 400);
      } catch (error) {
        resetUploadProgress();
        el.uploadProgressText.textContent = t("uploadFailed");
        setFeedback(t("uploadFailedWithMessage", { message: error.message }));
      }
    });
    xhr.addEventListener("error", () => {
      el.uploadBtn.disabled = false;
      resetUploadProgress();
      el.uploadProgressText.textContent = t("uploadFailed");
      setFeedback(t("uploadRequestFailed"));
    });
    xhr.send(formData);
  }

  async function selectDatabase() {
    const databaseId = el.databaseSelect.value;
    if (!databaseId) {
      setFeedback(t("chooseDatabaseFromList"));
      return;
    }
    el.selectDatabaseBtn.disabled = true;
    try {
      const response = await fetch("/api/v1/databases/select", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ database_id: databaseId }),
      });
      const payload = await response.json();
      if (!response.ok) {
        throw new Error(payload.detail || t("databaseSelectFailed"));
      }
      state.currentDatabase = payload.selected_database;
      updateQueryState();
      await loadDatabases();
      setFeedback(t("databaseSwitched", { label: displayDatabaseLabel(payload.selected_database) }));
    } catch (error) {
      setFeedback(t("databaseSelectFailedWithMessage", { message: error.message }));
    } finally {
      el.selectDatabaseBtn.disabled = false;
    }
  }

  async function runQuery() {
    const query = el.queryInput.value.trim();
    if (!state.currentDatabase) {
      setFeedback(t("queryNeedDatabase"));
      return;
    }
    if (!query) {
      setFeedback(t("queryNeedText"));
      return;
    }

    el.queryBtn.disabled = true;
    setResult(t("queryRunning"));
    try {
      const response = await fetch("/api/v1/query", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          query,
          include_rows: true,
          top_k_rows: Number(el.topKInput.value || 3),
        }),
      });
      const payload = await response.json();
      if (!response.ok) {
        throw new Error(payload.detail || t("queryFailed"));
      }
      const resultText = t("queryResultFormat", {
        answer: payload.answer || "",
        elapsedMs: payload.elapsed_ms,
        nodeTrace: (payload.node_trace || []).join(" -> "),
        rows: safeJson(payload.rows || []),
      });
      setResult(resultText);
      setFeedback(t("queryDone", { elapsedMs: payload.elapsed_ms }));
    } catch (error) {
      setResult(t("queryFailed"));
      setFeedback(t("queryFailedWithMessage", { message: error.message }));
    } finally {
      updateQueryState();
    }
  }

  function bindLanguageSwitch() {
    el.langEnBtn.addEventListener("click", () => setLanguage("en"));
    el.langZhBtn.addEventListener("click", () => setLanguage("zh"));
  }

  const savedLanguage = window.localStorage.getItem("capstone_fastapi_lang");
  if (savedLanguage) {
    state.language = savedLanguage === "zh" ? "zh" : "en";
  }
  applyStaticTranslations();
  bindDragAndDrop();
  bindLanguageSwitch();
  el.refreshDatabasesBtn.addEventListener("click", refreshAllStatus);
  el.selectDatabaseBtn.addEventListener("click", selectDatabase);
  el.uploadBtn.addEventListener("click", uploadVideo);
  el.queryBtn.addEventListener("click", runQuery);

  refreshAllStatus();
})();
