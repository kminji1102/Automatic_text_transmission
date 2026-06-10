(() => {
  const forms = document.querySelectorAll("[data-send-form]");
  forms.forEach(initSendForm);

  function initSendForm(form) {
    const rows = Array.from(form.querySelectorAll("[data-recipient-row]"));
    const checks = Array.from(form.querySelectorAll("[data-recipient-check]"));
    const search = form.querySelector("[data-recipient-search]");
    const selectAll = form.querySelector("[data-select-all]");
    const clearSelection = form.querySelector("[data-clear-selection]");
    const empty = form.querySelector("[data-filter-empty]");
    const formMessage = form.querySelector("[data-form-message]");
    const messageEditor = form.querySelector("[data-message-editor]");
    const messageCount = form.querySelector("[data-message-count]");
    const dialog = form.querySelector("[data-confirm-dialog]");
    const closeConfirm = form.querySelector("[data-close-confirm]");
    const confirmSubmit = form.querySelector("[data-confirm-submit]");
    const confirmCount = form.querySelector("[data-confirm-count]");

    const updateState = () => {
      const selectedCount = checks.filter((check) => check.checked).length;
      form.querySelectorAll("[data-selected-count]").forEach((node) => {
        node.textContent = String(selectedCount);
      });
      rows.forEach((row) => {
        const check = row.querySelector("[data-recipient-check]");
        row.classList.toggle("is-selected", Boolean(check?.checked));
        row.classList.toggle("is-muted", !check?.checked);
      });
      if (formMessage && selectedCount > 0 && currentMessage()) {
        formMessage.textContent = "";
      }
      return selectedCount;
    };

    const currentMessage = () => (messageEditor?.value || "").trim();

    const updateMessageCount = () => {
      if (messageCount && messageEditor) {
        messageCount.textContent = String(messageEditor.value.length);
      }
      if (formMessage && currentMessage()) {
        formMessage.textContent = "";
      }
    };

    const visibleChecks = () =>
      rows
        .filter((row) => !row.hidden)
        .map((row) => row.querySelector("[data-recipient-check]"))
        .filter(Boolean);

    checks.forEach((check) => {
      check.addEventListener("change", updateState);
    });

    rows.forEach((row) => {
      row.addEventListener("click", (event) => {
        const target = event.target;
        if (!(target instanceof Element)) {
          return;
        }
        if (target instanceof HTMLInputElement || target.closest("a,button")) {
          return;
        }
        const check = row.querySelector("[data-recipient-check]");
        if (!check) {
          return;
        }
        check.checked = !check.checked;
        check.dispatchEvent(new Event("change", { bubbles: true }));
      });
    });

    if (search) {
      search.addEventListener("input", () => {
        const query = search.value.trim().toLowerCase();
        let visibleCount = 0;
        rows.forEach((row) => {
          const matches = !query || row.dataset.search.includes(query);
          row.hidden = !matches;
          if (matches) {
            visibleCount += 1;
          }
        });
        if (empty) {
          empty.hidden = visibleCount !== 0;
        }
      });
    }

    if (selectAll) {
      selectAll.addEventListener("click", () => {
        visibleChecks().forEach((check) => {
          check.checked = true;
        });
        updateState();
      });
    }

    if (clearSelection) {
      clearSelection.addEventListener("click", () => {
        checks.forEach((check) => {
          check.checked = false;
        });
        updateState();
      });
    }

    if (messageEditor) {
      messageEditor.addEventListener("input", updateMessageCount);
    }

    form.addEventListener("submit", (event) => {
      if (form.dataset.confirmed === "true") {
        delete form.dataset.confirmed;
        form.querySelectorAll("button[type='submit']").forEach((button) => {
          button.disabled = true;
          button.textContent = "발송 중...";
        });
        return;
      }

      event.preventDefault();
      const selectedCount = updateState();
      if (selectedCount === 0) {
        if (formMessage) {
          formMessage.textContent = "발송할 대상을 한 명 이상 선택해 주세요.";
        }
        return;
      }
      if (!currentMessage()) {
        if (formMessage) {
          formMessage.textContent = "문자 내용을 입력해 주세요.";
        }
        if (messageEditor) {
          messageEditor.focus();
        }
        return;
      }

      if (confirmCount) {
        confirmCount.textContent = String(selectedCount);
      }

      if (dialog && typeof dialog.showModal === "function") {
        dialog.showModal();
        return;
      }

      if (window.confirm(`${selectedCount}명에게 LMS를 발송합니다.`)) {
        submitConfirmed(form);
      }
    });

    if (closeConfirm && dialog) {
      closeConfirm.addEventListener("click", () => {
        dialog.close();
      });
    }

    if (confirmSubmit) {
      confirmSubmit.addEventListener("click", () => {
        if (dialog) {
          dialog.close();
        }
        submitConfirmed(form);
      });
    }

    updateState();
    updateMessageCount();
  }

  function submitConfirmed(form) {
    form.dataset.confirmed = "true";
    if (typeof form.requestSubmit === "function") {
      form.requestSubmit();
    } else {
      form.submit();
    }
  }
})();
