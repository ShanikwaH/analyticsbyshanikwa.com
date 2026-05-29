/**
 * interactions.js — Analytics by Shanikwa
 * Site-wide animation, scroll effects, and micro-interactions
 */
(function () {
  'use strict';

  /* ─── 1. Scroll-fade animations ─────────────────────────────────── */
  const FADE_SELECTORS = [
    '.cert-card', '.tl-item', '.benefit-card', '.reflection-card',
    '.stat-item', '.resource-section .resource-art', '.resource-section .resource-info',
    '.js-fade'
  ].join(', ');

  const fadeEls = document.querySelectorAll(FADE_SELECTORS);
  if (fadeEls.length) {
    // Inject minimal base style only once
    if (!document.getElementById('ix-fade-style')) {
      const s = document.createElement('style');
      s.id = 'ix-fade-style';
      s.textContent = `
        .ix-hidden { opacity: 0; transform: translateY(24px); transition: opacity .55s ease, transform .55s ease; }
        .ix-hidden.ix-visible { opacity: 1; transform: none; }
        .ix-hidden.ix-delay-1 { transition-delay: .1s; }
        .ix-hidden.ix-delay-2 { transition-delay: .2s; }
        .ix-hidden.ix-delay-3 { transition-delay: .3s; }
      `;
      document.head.appendChild(s);
    }

    const obs = new IntersectionObserver((entries) => {
      entries.forEach(entry => {
        if (entry.isIntersecting) {
          entry.target.classList.add('ix-visible');
          obs.unobserve(entry.target);
        }
      });
    }, { threshold: 0.08, rootMargin: '0px 0px -32px 0px' });

    fadeEls.forEach((el, i) => {
      el.classList.add('ix-hidden');
      // Stagger siblings in the same parent
      const siblings = Array.from(el.parentElement.children).filter(c => fadeEls !== null);
      const sibIdx = siblings.indexOf(el);
      if (sibIdx === 1) el.classList.add('ix-delay-1');
      else if (sibIdx === 2) el.classList.add('ix-delay-2');
      else if (sibIdx >= 3) el.classList.add('ix-delay-3');
      obs.observe(el);
    });
  }

  /* ─── 2. Stat counter animation ─────────────────────────────────── */
  const statNums = document.querySelectorAll('.stat-num');
  if (statNums.length) {
    const countObs = new IntersectionObserver((entries) => {
      entries.forEach(entry => {
        if (!entry.isIntersecting) return;
        countObs.unobserve(entry.target);
        const el = entry.target;
        const raw = el.textContent.trim();
        const num = parseFloat(raw.replace(/[^\d.]/g, ''));
        const suffix = raw.replace(/[\d.]/g, '');
        if (isNaN(num) || num === 0) return;
        const dur = 1400;
        const start = performance.now();
        (function tick(now) {
          const t = Math.min((now - start) / dur, 1);
          const ease = 1 - Math.pow(1 - t, 3);
          const cur = num < 10 ? (num * ease).toFixed(1) : Math.round(num * ease);
          el.textContent = cur + suffix;
          if (t < 1) requestAnimationFrame(tick);
          else el.textContent = raw;
        })(start);
      });
    }, { threshold: 0.5 });
    statNums.forEach(el => countObs.observe(el));
  }

  /* ─── 3. Nav: scroll-blur + hide-on-scroll-down ─────────────────── */
  const siteNav = document.querySelector('.site-nav');
  if (siteNav) {
    if (!document.getElementById('ix-nav-style')) {
      const s = document.createElement('style');
      s.id = 'ix-nav-style';
      s.textContent = `
        .site-nav { transition: box-shadow .25s, background .25s, transform .3s; }
        .site-nav.nav-scrolled { box-shadow: 0 2px 16px rgba(15,23,42,.09); }
        .nav-hidden { transform: translateY(-100%) !important; }
      `;
      document.head.appendChild(s);
    }
    let lastY = 0;
    window.addEventListener('scroll', () => {
      const y = window.scrollY;
      siteNav.classList.toggle('nav-scrolled', y > 20);
      if (y > lastY && y > 120) {
        siteNav.classList.add('nav-hidden');
      } else {
        siteNav.classList.remove('nav-hidden');
      }
      lastY = y;
    }, { passive: true });
  }

  /* ─── 4. Smooth scroll for same-page anchors ─────────────────────── */
  document.querySelectorAll('a[href^="#"]').forEach(a => {
    a.addEventListener('click', e => {
      const id = a.getAttribute('href');
      if (id === '#') return;
      const target = document.querySelector(id);
      if (target) {
        e.preventDefault();
        const navH = siteNav ? siteNav.offsetHeight : 80;
        const top = target.getBoundingClientRect().top + window.scrollY - navH - 16;
        window.scrollTo({ top, behavior: 'smooth' });
      }
    });
  });

  /* ─── 5. Card hover-lift (CSS-based, JS ensures consistency) ─────── */
  if (!document.getElementById('ix-card-style')) {
    const s = document.createElement('style');
    s.id = 'ix-card-style';
    s.textContent = `
      .cert-card, .benefit-card, .reflection-card, .resource-art {
        transition: transform .22s ease, box-shadow .22s ease !important;
      }
      .cert-card:hover, .benefit-card:hover, .reflection-card:hover {
        transform: translateY(-4px);
        box-shadow: 0 12px 32px rgba(15,23,42,.12) !important;
      }
      .btn, .nav-cta, a.btn {
        transition: transform .18s ease, box-shadow .18s ease, opacity .18s ease !important;
      }
      .btn:hover, .nav-cta:hover {
        transform: translateY(-2px);
        box-shadow: 0 6px 20px rgba(59,130,246,.28) !important;
      }
      .btn:active { transform: translateY(0); }
    `;
    document.head.appendChild(s);
  }

  /* ─── 6. Timeline item stagger on scroll ─────────────────────────── */
  const tlItems = document.querySelectorAll('.tl-item');
  if (tlItems.length) {
    const tlObs = new IntersectionObserver((entries) => {
      entries.forEach((entry, _) => {
        if (entry.isIntersecting) {
          entry.target.style.transitionDelay = (Array.from(tlItems).indexOf(entry.target) % 3) * 0.1 + 's';
          entry.target.classList.add('ix-visible');
          tlObs.unobserve(entry.target);
        }
      });
    }, { threshold: 0.1 });
    tlItems.forEach(el => tlObs.observe(el));
  }

  /* ─── 7. Skill bar trigger (backup if not already on page) ───────── */
  const skillFills = document.querySelectorAll('.skill-fill:not([data-animated])');
  if (skillFills.length) {
    const barObs = new IntersectionObserver((entries) => {
      entries.forEach(entry => {
        if (entry.isIntersecting) {
          const el = entry.target;
          el.style.width = (el.dataset.w || 0) + '%';
          el.dataset.animated = '1';
          barObs.unobserve(el);
        }
      });
    }, { threshold: 0.2 });
    skillFills.forEach(el => { el.style.width = '0'; barObs.observe(el); });
  }

  /* ─── 8. Free-resources form label (Kit form → lead magnet) ──────── */
  // Each Kit embed is scoped by its parent section ID.
  // When Kit delivers the file, it reads the sequence triggered by that form's UID:
  //   section#budget-tracker  → form uid 5f58135989  → Kit Sequence: Faith Budget Tracker
  //   section#bible-study     → form uid 682faa56d5  → Kit Sequence: Bible Study Template
  //   section#career-pivot    → form uid 2662851983  → Kit Sequence: Career Pivot Checklist
  //   section#scripture-memory → form uid 5606bcae44 → Kit Sequence: Scripture Memory Tracker

  /* ─── 9. Resource section scroll reveal (alternating sides) ──────── */
  document.querySelectorAll('.resource-section').forEach((section, i) => {
    const art = section.querySelector('.resource-art');
    const info = section.querySelector('.resource-info');
    if (!art || !info) return;
    const isAlt = section.classList.contains('alt');
    [art, info].forEach((el, j) => {
      el.style.opacity = '0';
      el.style.transform = `translateX(${(isAlt ? (j === 0 ? 1 : -1) : (j === 0 ? -1 : 1)) * 40}px)`;
      el.style.transition = 'opacity .6s ease, transform .6s ease';
      el.style.transitionDelay = (j * 0.15) + 's';
    });
    const secObs = new IntersectionObserver(entries => {
      entries.forEach(e => {
        if (e.isIntersecting) {
          [art, info].forEach(el => {
            el.style.opacity = '1';
            el.style.transform = 'none';
          });
          secObs.unobserve(section);
        }
      });
    }, { threshold: 0.12 });
    secObs.observe(section);
  });

})();
