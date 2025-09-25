// --- MODAL SCROLL LOCK FUNCTIONALITY ---
const lockBodyScroll = () => {
    document.body.classList.add('modal-open');
};

const unlockBodyScroll = () => {
    document.body.classList.remove('modal-open');
};

// --- GENERIC HELPERS ---
const showToast = (message, type = 'info') => {
    const toast = document.getElementById('toast');
    toast.textContent = message;
    toast.className = `toast show ${type}`;
    setTimeout(() => { toast.className = 'toast'; }, 4000);
};

const openModal = (modalId) => {
    document.getElementById(modalId).classList.add('active');
    lockBodyScroll();
};

const closeModal = (modalId) => {
    document.getElementById(modalId).classList.remove('active');
    unlockBodyScroll();
};

// Close modal when clicking outside
document.querySelectorAll('.modal-bg').forEach(bg => {
    bg.onclick = (e) => {
        if (e.target === bg) {
            closeModal(bg.id);
        }
    };
});

// Close modal on Escape key
document.addEventListener('keydown', (e) => {
    if (e.key === 'Escape') {
        document.querySelectorAll('.modal-bg.active').forEach(modal => {
            closeModal(modal.id);
        });
    }
});

const setupImagePreview = (inputId, previewId) => {
    const input = document.getElementById(inputId);
    const preview = document.getElementById(previewId);
    input.onchange = () => {
        const [file] = input.files;
        if (file) {
            preview.src = URL.createObjectURL(file);
            preview.style.display = 'block';
        } else {
            preview.style.display = 'none';
        }
    };
};
setupImagePreview('proj_image', 'proj_imagePreview');
setupImagePreview('test_image', 'test_imagePreview');

// --- UNIVERSAL DELETE ---
const confirmDelete = (type, id) => {
    const messages = {
        project: 'This will permanently delete this project and its image. This action cannot be undone.',
        testimonial: 'This will permanently delete this testimonial and its image. This action cannot be undone.',
        message: 'Are you sure you want to delete this customer message? This action cannot be undone.',
    };
    openConfirmModal(`Delete ${type.charAt(0).toUpperCase() + type.slice(1)}`, messages[type], () => deleteItem(type, id));
};

const deleteItem = async (type, id) => {
    try {
        const response = await fetch(`/admin/${type}/delete/${id}`, { method: "POST" });
        const data = await response.json();
        if (data.success) {
            showToast(`${type.charAt(0).toUpperCase() + type.slice(1)} deleted successfully.`, 'success');
            document.querySelector(`.card[data-id='${id}']`)?.remove();
        } else {
            showToast(data.message || `Error deleting ${type}.`, 'error');
        }
    } catch (err) {
        showToast('Network error occurred.', 'error');
    }
};

const openConfirmModal = (title, message, onConfirm) => {
    document.getElementById('confirmTitle').textContent = title;
    document.getElementById('confirmMessage').textContent = message;
    const okBtn = document.getElementById('confirmOkBtn');
    const cancelBtn = document.getElementById('confirmCancelBtn');
    okBtn.onclick = () => { onConfirm(); closeModal('confirmModal'); };
    cancelBtn.onclick = () => closeModal('confirmModal');
    openModal('confirmModal');
};

// --- PROJECT MANAGEMENT ---
const projectForm = document.getElementById('projectForm');
const openProjectModal = () => {
    projectForm.reset();
    document.getElementById('projectModalTitle').textContent = "Add Project";
    document.getElementById('proj_id').value = "";
    document.getElementById('proj_imagePreview').style.display = 'none';
    openModal('projectModalBg');
};
const createProjectCardHTML = (p) => `
    <img class="card-img" src="${p.image ? `/static/uploads/${p.image}` : 'https://placehold.co/400x200/0D3B66/FFFFFF?text=No+Image'}" alt="${p.title}">
    <div class="card-title">${p.title}</div>
    <div class="card-details">${p.description}</div>
    <div class="card-details"><strong>Category:</strong> ${p.category.charAt(0).toUpperCase() + p.category.slice(1)} | <strong>Status:</strong> ${p.status.charAt(0).toUpperCase() + p.status.slice(1)}</div>
    <small class="card-details"><i class="fas fa-calendar"></i> Created: ${p.date_created}</small>
    <div class="card-actions">
        <button class="btn btn-primary" onclick="editProject('${p.id}')"><i class="fas fa-edit"></i> Edit</button>
        <button class="btn btn-danger" onclick="confirmDelete('project', '${p.id}')"><i class="fas fa-trash"></i> Delete</button>
    </div>`;
projectForm.onsubmit = async (e) => {
    e.preventDefault();
    const submitBtn = document.getElementById('projSubmitBtn');
    submitBtn.disabled = true;
    submitBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Saving...';
    const formData = new FormData(projectForm);
    const id = formData.get("id");
    const url = id ? `/admin/project/edit/${id}` : "/admin/project/add";
    try {
        const response = await fetch(url, { method: "POST", body: formData });
        const data = await response.json();
        if (data.success) {
            showToast(id ? 'Project updated successfully!' : 'Project added successfully!', 'success');
            const item = data.project;
            const card = document.querySelector(`#projectsList .card[data-id='${item.id}']`);
            if (card) {
                card.innerHTML = createProjectCardHTML(item);
            } else {
                const newCard = document.createElement('div'); newCard.className = 'card'; newCard.dataset.id = item.id;
                newCard.innerHTML = createProjectCardHTML(item);
                const list = document.getElementById('projectsList');
                const noItemsMsg = list.querySelector('div[style*="grid-column"]');
                if (noItemsMsg) noItemsMsg.remove();
                list.prepend(newCard);
            }
            closeModal('projectModalBg');
        } else { showToast(data.message || "An error occurred.", 'error'); }
    } catch (err) {
        showToast('Network error occurred.', 'error');
    } finally { submitBtn.disabled = false; submitBtn.innerHTML = 'Save Project'; }
};
const editProject = async (id) => {
    try {
        const response = await fetch(`/api/project/${id}`);
        const data = await response.json();
        if (data.success) {
            const p = data.project;
            projectForm.reset();
            document.getElementById('projectModalTitle').textContent = "Edit Project";
            document.getElementById('proj_id').value = p.id;
            document.getElementById('proj_title').value = p.title;
            document.getElementById('proj_desc').value = p.description;
            document.getElementById('proj_category').value = p.category;
            document.getElementById('proj_status').value = p.status;
            const preview = document.getElementById('proj_imagePreview');
            if (p.image) {
                preview.src = `/static/uploads/${p.image}`;
                preview.style.display = 'block';
            } else { preview.style.display = 'none'; }
            openModal('projectModalBg');
        } else { showToast('Could not fetch project details.', 'error'); }
    } catch (err) { showToast('Network error occurred.', 'error'); }
};

// --- TESTIMONIAL MANAGEMENT ---
const testimonialForm = document.getElementById('testimonialForm');
const openTestimonialModal = () => {
    testimonialForm.reset();
    document.getElementById('testimonialModalTitle').textContent = "Add Testimonial";
    document.getElementById('test_id').value = "";
    document.getElementById('test_imagePreview').style.display = 'none';
    openModal('testimonialModalBg');
};
const createTestimonialCardHTML = (t) => {
    let stars = '';
    for (let i = 0; i < 5; i++) { stars += `<i class="fas fa-star" style="opacity:${i < t.rating ? 1 : 0.3}"></i>`; }
    return `
        <div style="display: flex; align-items: center; gap: 1.2rem; margin-bottom: 1.5rem;">
            <img class="card-author-img" src="${t.image ? `/static/uploads/${t.image}` : 'https://placehold.co/70x70/EFEFEF/333333?text=?'}" alt="${t.name}">
            <div>
                <div class="card-title" style="margin-bottom: 0.2rem;">${t.name}</div>
                <div class="card-details">${t.company}</div>
            </div>
        </div>
        <div class="rating-stars" data-rating="${t.rating}">${stars}</div>
        <div class="card-message">"${t.text}"</div>
        <small class="card-details"><i class="fas fa-calendar"></i> Created: ${t.date_created}</small>
        <div class="card-actions">
            <button class="btn btn-primary" onclick="editTestimonial('${t.id}')"><i class="fas fa-edit"></i> Edit</button>
            <button class="btn btn-danger" onclick="confirmDelete('testimonial', '${t.id}')"><i class="fas fa-trash"></i> Delete</button>
        </div>`;
};
testimonialForm.onsubmit = async (e) => {
    e.preventDefault();
    const submitBtn = document.getElementById('testSubmitBtn');
    submitBtn.disabled = true;
    submitBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Saving...';
    const formData = new FormData(testimonialForm);
    const id = formData.get("id");
    const url = id ? `/admin/testimonial/edit/${id}` : "/admin/testimonial/add";
    try {
        const response = await fetch(url, { method: "POST", body: formData });
        const data = await response.json();
        if (data.success) {
            showToast(id ? 'Testimonial updated successfully!' : 'Testimonial added successfully!', 'success');
            const item = data.testimonial;
            const card = document.querySelector(`#testimonialsList .card[data-id='${item.id}']`);
            if (card) {
                card.innerHTML = createTestimonialCardHTML(item);
            } else {
                const newCard = document.createElement('div'); newCard.className = 'card'; newCard.dataset.id = item.id;
                newCard.innerHTML = createTestimonialCardHTML(item);
                const list = document.getElementById('testimonialsList');
                const noItemsMsg = list.querySelector('div[style*="grid-column"]');
                if (noItemsMsg) noItemsMsg.remove();
                list.prepend(newCard);
            }
            closeModal('testimonialModalBg');
        } else { showToast(data.message || "An error occurred.", 'error'); }
    } catch (err) {
        showToast('Network error occurred.', 'error');
    } finally { submitBtn.disabled = false; submitBtn.innerHTML = 'Save Testimonial'; }
};
const editTestimonial = async (id) => {
    try {
        const response = await fetch(`/api/testimonial/${id}`);
        const data = await response.json();
        if (data.success) {
            const t = data.testimonial;
            testimonialForm.reset();
            document.getElementById('testimonialModalTitle').textContent = "Edit Testimonial";
            document.getElementById('test_id').value = t.id;
            document.getElementById('test_name').value = t.name;
            document.getElementById('test_company').value = t.company;
            document.getElementById('test_text').value = t.text;
            document.getElementById('test_rating').value = t.rating;
            const preview = document.getElementById('test_imagePreview');
            if (t.image) {
                preview.src = `/static/uploads/${t.image}`;
                preview.style.display = 'block';
            } else { preview.style.display = 'none'; }
            openModal('testimonialModalBg');
        } else { showToast('Could not fetch testimonial details.', 'error'); }
    } catch (err) { showToast('Network error occurred.', 'error'); }
};

// --- MESSAGE MANAGEMENT ---
const updateMsgStatus = async (id, status) => {
    try {
        const response = await fetch(`/admin/message/status/${id}`, {
            method: "POST",
            headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
            body: new URLSearchParams({ status })
        });
        const data = await response.json();
        if (data.success) {
            showToast('Message status updated!', 'success');
            const badge = document.querySelector(`#messagesList .card[data-id='${id}'] .status-badge`);
            if (badge) {
                badge.className = `status-badge status-${status.replace(' ', '')}`;
                badge.textContent = status;
            }
        } else { showToast(data.message || "Error updating status.", 'error'); }
    } catch (err) { showToast('Network error occurred.', 'error'); }
};

// --- POPULATE RATING STARS ---
const populateRatingStars = () => {
    document.querySelectorAll('.rating-stars[data-rating]').forEach(container => {
        const rating = parseInt(container.dataset.rating) || 0;
        let starsHTML = '';
        for (let i = 0; i < 5; i++) {
            starsHTML += `<i class="fas fa-star" style="opacity:${i < rating ? 1 : 0.3}"></i>`;
        }
        container.innerHTML = starsHTML;
    });
};

// Initialize on page load
document.addEventListener('DOMContentLoaded', function () {
    populateRatingStars();

    // --- NEW: Dashboard Navigation Logic ---
    const navLinks = document.querySelectorAll('.nav-link');
    const contentSections = document.querySelectorAll('.content-section');

    const switchTab = (targetId) => {
        contentSections.forEach(section => section.classList.remove('active'));
        navLinks.forEach(link => link.classList.remove('active'));

        const targetSection = document.getElementById(targetId);
        const targetLink = document.querySelector(`.nav-link[data-target="${targetId}"]`);

        if (targetSection) targetSection.classList.add('active');
        if (targetLink) targetLink.classList.add('active');
    };

    navLinks.forEach(link => {
        link.addEventListener('click', function (e) {
            e.preventDefault();
            const targetId = this.dataset.target;
            history.pushState(null, null, this.href);
            switchTab(targetId);
        });
    });

    // Handle initial page load based on URL hash
    const handlePageLoad = () => {
        const initialHash = window.location.hash.substring(1);
        const sectionIdFromHash = initialHash ? `${initialHash}-section` : 'dashboard-section';

        if (document.getElementById(sectionIdFromHash)) {
            switchTab(sectionIdFromHash);
        } else {
            switchTab('dashboard-section'); // Fallback to default
        }
    };

    // Handle browser back/forward buttons
    window.addEventListener('popstate', handlePageLoad);

    // Initial load
    handlePageLoad();
});