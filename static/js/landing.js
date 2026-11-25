(() => {
  const mobileToggle = document.getElementById('landing-mobile-toggle');
  const mobileMenu = document.getElementById('landing-mobile-menu');
  const mobileLinks = document.querySelectorAll('.landing-mobile-link');

  if (mobileToggle && mobileMenu) {
    mobileToggle.addEventListener('click', () => {
      const isHidden = mobileMenu.classList.contains('hidden');
      mobileMenu.classList.toggle('hidden', !isHidden);
      mobileToggle.setAttribute('aria-expanded', String(isHidden));
    });

    mobileLinks.forEach((link) => {
      link.addEventListener('click', () => {
        mobileMenu.classList.add('hidden');
        mobileToggle.setAttribute('aria-expanded', 'false');
      });
    });
  }

  const contactForm = document.getElementById('contact-form');
  const contactError = document.getElementById('contact-error');
  const contactSuccess = document.getElementById('contact-success');
  const contactResetBtn = document.getElementById('contact-reset-btn');
  const nameInput = document.getElementById('contact-name');
  const emailInput = document.getElementById('contact-email');
  const msgInput = document.getElementById('contact-message');

  if (contactForm) {
    contactForm.addEventListener('submit', (e) => {
      e.preventDefault();
      const name = (nameInput?.value || '').trim();
      const email = (emailInput?.value || '').trim();
      const message = (msgInput?.value || '').trim();

      if (name.length < 2) {
        showError('Please enter your name.');
        return;
      }
      if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)) {
        showError('Please enter a valid email address.');
        return;
      }
      if (message.length < 10) {
        showError('Please enter a message of at least 10 characters.');
        return;
      }

      if (contactError) contactError.classList.add('hidden');
      contactForm.classList.add('hidden');
      if (contactSuccess) contactSuccess.classList.remove('hidden');
      contactForm.reset();
    });
  }

  if (contactResetBtn && contactForm && contactSuccess) {
    contactResetBtn.addEventListener('click', () => {
      contactSuccess.classList.add('hidden');
      contactForm.classList.remove('hidden');
    });
  }

  function showError(msg) {
    if (!contactError) return;
    contactError.textContent = msg;
    contactError.classList.remove('hidden');
  }
})();
