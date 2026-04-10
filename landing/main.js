/* ThreadWeaver Product Page — Scroll reveals + terminal typing */

(function () {
  'use strict';

  // ─── Scroll Reveal (Intersection Observer) ──────────────
  const revealEls = document.querySelectorAll('[data-reveal]');
  if (revealEls.length > 0) {
    const revealObs = new IntersectionObserver(
      (entries) => {
        entries.forEach((entry) => {
          if (entry.isIntersecting) {
            entry.target.classList.add('revealed');
            revealObs.unobserve(entry.target);
          }
        });
      },
      { threshold: 0.15 }
    );
    revealEls.forEach((el) => revealObs.observe(el));
  }

  // ─── Sticky Nav ─────────────────────────────────────────
  const nav = document.querySelector('.nav');
  const hero = document.querySelector('.hero');
  if (nav && hero) {
    const heroBottom = hero.offsetTop + hero.offsetHeight;
    window.addEventListener(
      'scroll',
      () => {
        nav.classList.toggle('visible', window.scrollY > heroBottom - 60);
      },
      { passive: true }
    );
  }

  // ─── Terminal Typing Animation ──────────────────────────
  const termBody = document.getElementById('terminal-body');
  if (termBody) {
    let hasPlayed = false;
    const commands = [
      { prompt: '$ ', text: 'git clone https://github.com/nosqltips/ThreadWeaver', delay: 25 },
      { prompt: '$ ', text: 'cd ThreadWeaver', delay: 30 },
      { prompt: '$ ', text: 'docker compose up -d', delay: 30 },
      { output: 'Creating backend  ... done\nCreating frontend ... done', pause: 400 },
      { prompt: '$ ', text: '# Open http://localhost:3000', delay: 40 },
    ];

    function typeCommands() {
      if (hasPlayed) return;
      hasPlayed = true;
      termBody.textContent = '';
      let totalDelay = 0;

      commands.forEach((cmd) => {
        if (cmd.output) {
          totalDelay += cmd.pause || 300;
          const d = totalDelay;
          setTimeout(() => {
            const span = document.createElement('span');
            span.className = 'output';
            span.textContent = cmd.output + '\n';
            termBody.appendChild(span);
          }, d);
          totalDelay += 100;
        } else {
          // Prompt (instant)
          const promptDelay = totalDelay;
          setTimeout(() => {
            const ps = document.createElement('span');
            ps.className = 'prompt';
            ps.textContent = cmd.prompt;
            termBody.appendChild(ps);
          }, promptDelay);
          totalDelay += 50;

          // Typed characters
          const chars = cmd.text.split('');
          chars.forEach((ch, i) => {
            const charDelay = totalDelay + i * (cmd.delay || 30);
            setTimeout(() => {
              const cs = document.createElement('span');
              cs.className = 'cmd';
              cs.textContent = ch;
              termBody.appendChild(cs);
            }, charDelay);
          });
          totalDelay += chars.length * (cmd.delay || 30) + 200;

          // Newline after command
          const nlDelay = totalDelay;
          setTimeout(() => {
            termBody.appendChild(document.createTextNode('\n'));
          }, nlDelay);
          totalDelay += 50;
        }
      });

      // Blinking cursor at the end
      setTimeout(() => {
        const cursor = document.createElement('span');
        cursor.className = 'cursor';
        cursor.textContent = '\u00A0';
        termBody.appendChild(cursor);
      }, totalDelay + 100);
    }

    const termObs = new IntersectionObserver(
      (entries) => {
        if (entries[0].isIntersecting) {
          typeCommands();
          termObs.disconnect();
        }
      },
      { threshold: 0.4 }
    );
    termObs.observe(termBody);
  }
})();
