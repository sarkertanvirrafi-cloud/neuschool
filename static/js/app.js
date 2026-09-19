(function () {
  const menuToggle = document.querySelector('[data-menu-toggle]');
  const mainNav = document.querySelector('[data-main-nav]');
  if (menuToggle && mainNav) {
    menuToggle.addEventListener('click', () => mainNav.classList.toggle('open'));
  }

  const observer = new IntersectionObserver((entries) => {
    entries.forEach((entry) => {
      if (entry.isIntersecting) {
        entry.target.classList.add('visible');
        observer.unobserve(entry.target);
      }
    });
  }, { threshold: 0.1 });
  document.querySelectorAll('.reveal').forEach((el) => observer.observe(el));

  const stepModal = document.getElementById('stepModal');
  if (stepModal) {
    const badge = document.getElementById('modalBadge');
    const title = document.getElementById('modalTitle');
    const text = document.getElementById('modalText');
    const roadmapText = {
      1: 'Step 1 details will appear here.',
      2: 'Step 2 details will appear here.',
      3: 'Step 3 details will appear here.',
      4: 'Step 4 details will appear here.',
      5: 'Step 5 details will appear here.',
      6: 'Step 6 details will appear here.'
    };
    document.querySelectorAll('.step-node').forEach((node) => {
      node.addEventListener('click', () => {
        const step = node.dataset.step;
        badge.textContent = `STEP ${step}`;
        title.textContent = `STEP ${step}`;
        text.textContent = roadmapText[step];
        stepModal.classList.add('open');
        stepModal.setAttribute('aria-hidden', 'false');
        document.body.style.overflow = 'hidden';
      });
    });
    stepModal.querySelectorAll('[data-close-modal]').forEach((el) => {
      el.addEventListener('click', () => {
        stepModal.classList.remove('open');
        stepModal.setAttribute('aria-hidden', 'true');
        document.body.style.overflow = '';
      });
    });
  }

  const roadPath = document.querySelector('.path-base');
  const roadRunner = document.querySelector('.road-runner');
  if (roadPath && roadRunner && typeof roadPath.getTotalLength === 'function') {
    const total = roadPath.getTotalLength();
    let start = null;
    const move = (time) => {
      if (!start) start = time;
      const progress = ((time - start) % 12000) / 12000;
      const point = roadPath.getPointAtLength(progress * total);
      roadRunner.style.left = `${point.x}px`;
      roadRunner.style.top = `${point.y}px`;
      requestAnimationFrame(move);
    };
    requestAnimationFrame(move);
  }

  const authTabs = document.querySelectorAll('[data-auth-tab]');
  const authForms = document.querySelectorAll('[data-auth-form]');
  authTabs.forEach((tab) => {
    tab.addEventListener('click', () => {
      const mode = tab.dataset.authTab;
      authTabs.forEach((item) => item.classList.toggle('active', item === tab));
      authForms.forEach((form) => form.classList.toggle('hidden', form.dataset.authForm !== mode));
    });
  });

  function csrfToken() {
    return document.querySelector('input[name="csrfmiddlewaretoken"]')?.value || '';
  }

  // DRM playback: the server verifies login + enrollment and only then requests
  // a short-lived VdoCipher OTP. The VdoCipher API secret never reaches JS.
  document.querySelectorAll('[data-drm-play-url]').forEach((button) => {
    button.addEventListener('click', async () => {
      const target = document.getElementById(button.dataset.drmTarget);
      if (!target || button.dataset.loading === '1') return;
      button.dataset.loading = '1';
      const originalText = button.textContent;
      button.textContent = 'SECURING PLAYBACK…';
      button.disabled = true;
      target.innerHTML = '<div class="drm-placeholder"><strong>AUTHENTICATING</strong><span>Creating encrypted playback session…</span></div>';

      try {
        const response = await fetch(button.dataset.drmPlayUrl, {
          method: 'POST',
          headers: {
            'X-CSRFToken': csrfToken(),
            'Accept': 'application/json'
          },
          credentials: 'same-origin'
        });
        const data = await response.json();
        if (!response.ok) throw new Error(data.error || 'Secure playback could not be started.');

        const iframe = document.createElement('iframe');
        iframe.src = data.player_url;
        iframe.title = data.title || 'Secure lecture';
        iframe.allow = 'encrypted-media; fullscreen; autoplay';
        iframe.setAttribute('allowfullscreen', 'true');
        iframe.setAttribute('referrerpolicy', 'strict-origin-when-cross-origin');
        target.innerHTML = '';
        target.appendChild(iframe);
        button.textContent = 'REFRESH SECURE SESSION';
      } catch (error) {
        target.innerHTML = `<div class="drm-error"><strong>PLAYBACK UNAVAILABLE</strong><span>${String(error.message || error)}</span></div>`;
        button.textContent = originalText;
      } finally {
        button.disabled = false;
        button.dataset.loading = '0';
      }
    });
  });

  // Staff browser-to-VdoCipher direct upload. Large video bytes never pass
  // through the Vercel/Django function.
  const drmUploadForm = document.querySelector('[data-drm-upload-form]');
  if (drmUploadForm) {
    const sectionSelect = drmUploadForm.querySelector('[data-drm-section]');
    const subsectionSelect = drmUploadForm.querySelector('[data-drm-subsection]');
    const progressBox = drmUploadForm.querySelector('[data-drm-progress]');
    const progressBar = drmUploadForm.querySelector('[data-drm-progress-bar]');
    const statusText = drmUploadForm.querySelector('[data-drm-status]');
    const submitButton = drmUploadForm.querySelector('button[type="submit"]');

    function filterSubsections() {
      const selectedSection = sectionSelect?.value || '';
      if (!subsectionSelect) return;
      Array.from(subsectionSelect.options).forEach((option) => {
        if (!option.value) {
          option.hidden = false;
          option.disabled = false;
          return;
        }
        const matches = option.dataset.sectionId === selectedSection;
        option.hidden = !matches;
        option.disabled = !matches;
      });
      if (subsectionSelect.selectedOptions[0]?.disabled) subsectionSelect.value = '';
    }
    sectionSelect?.addEventListener('change', filterSubsections);
    filterSubsections();

    function showUploadStatus(message, percent) {
      progressBox?.classList.remove('hidden');
      if (statusText) statusText.textContent = message;
      if (progressBar) progressBar.style.width = `${Math.max(0, Math.min(100, percent))}%`;
    }

    function uploadToVdoCipher(clientPayload, file) {
      return new Promise((resolve, reject) => {
        const formData = new FormData();
        Object.entries(clientPayload).forEach(([key, value]) => {
          if (key !== 'uploadLink' && value !== null && value !== undefined) {
            formData.append(key, value);
          }
        });
        formData.append('success_action_status', '201');
        formData.append('success_action_redirect', '');
        // Per VdoCipher docs, append the file last.
        formData.append('file', file, file.name);

        const xhr = new XMLHttpRequest();
        xhr.open('POST', clientPayload.uploadLink, true);
        xhr.upload.addEventListener('progress', (event) => {
          if (event.lengthComputable) {
            const percent = Math.round((event.loaded / event.total) * 100);
            showUploadStatus(`Uploading encrypted source… ${percent}%`, percent);
          }
        });
        xhr.addEventListener('load', () => {
          if (xhr.status === 201 || xhr.status === 204) resolve();
          else reject(new Error(`Video upload failed (HTTP ${xhr.status}).`));
        });
        xhr.addEventListener('error', () => reject(new Error('Network error during video upload.')));
        xhr.send(formData);
      });
    }

    drmUploadForm.addEventListener('submit', async (event) => {
      event.preventDefault();
      const data = new FormData(drmUploadForm);
      const file = data.get('video_file');
      const title = String(data.get('title') || '').trim();
      if (!(file instanceof File) || !file.size || !title || !data.get('section_id')) return;

      submitButton.disabled = true;
      showUploadStatus('Creating secure upload session…', 3);
      try {
        const credentialResponse = await fetch(drmUploadForm.dataset.uploadCredentialsUrl, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': csrfToken(),
            'Accept': 'application/json'
          },
          credentials: 'same-origin',
          body: JSON.stringify({ title })
        });
        const credentials = await credentialResponse.json();
        if (!credentialResponse.ok) throw new Error(credentials.error || 'Could not create secure upload session.');

        await uploadToVdoCipher(credentials.clientPayload, file);
        showUploadStatus('Upload complete. Saving lecture…', 96);

        const finalizeResponse = await fetch(drmUploadForm.dataset.finalizeUrl, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': csrfToken(),
            'Accept': 'application/json'
          },
          credentials: 'same-origin',
          body: JSON.stringify({
            video_id: credentials.videoId,
            section_id: data.get('section_id'),
            subsection_id: data.get('subsection_id') || '',
            title,
            duration_minutes: data.get('duration_minutes') || 0,
            order: data.get('order') || 1
          })
        });
        const finalData = await finalizeResponse.json();
        if (!finalizeResponse.ok) throw new Error(finalData.error || 'Video uploaded, but lecture metadata could not be saved.');

        showUploadStatus('Secure lecture created. VdoCipher may need time to finish processing the video.', 100);
        window.setTimeout(() => { window.location.href = finalData.redirect; }, 900);
      } catch (error) {
        showUploadStatus(String(error.message || error), 0);
        submitButton.disabled = false;
      }
    });
  }

  document.addEventListener('keydown', (event) => {
    if (event.key === 'Escape' && stepModal?.classList.contains('open')) {
      stepModal.classList.remove('open');
      document.body.style.overflow = '';
    }
  });
})();
