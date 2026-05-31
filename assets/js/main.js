/* ============================================================
   NetraMesh Labs — main.js
   Vanilla JS, no dependencies. No tracking, no data storage
   (only a UI language preference in localStorage).
   ============================================================ */
(function () {
  "use strict";

  document.documentElement.classList.remove("no-js");
  var prefersReduced = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
  // Defined here (not later) because applyLang() runs on load and triggers scrambling.
  var SCRAMBLE_CHARS = "!<>-_\\/[]{}=+*^?#01_netramesh";

  /* ---------- 1. Navbar scroll state ---------- */
  var nav = document.getElementById("nav");
  function onScroll() {
    if (window.scrollY > 24) nav.classList.add("is-scrolled");
    else nav.classList.remove("is-scrolled");
  }
  window.addEventListener("scroll", onScroll, { passive: true });
  onScroll();

  /* ---------- 2. Mobile menu ---------- */
  var burger = document.getElementById("navBurger");
  var navLinks = document.getElementById("navLinks");
  function closeMenu() {
    burger.classList.remove("is-open");
    navLinks.classList.remove("is-open");
    burger.setAttribute("aria-expanded", "false");
  }
  burger.addEventListener("click", function () {
    var open = burger.classList.toggle("is-open");
    navLinks.classList.toggle("is-open", open);
    burger.setAttribute("aria-expanded", open ? "true" : "false");
  });
  navLinks.querySelectorAll("a").forEach(function (a) {
    a.addEventListener("click", closeMenu);
  });
  document.addEventListener("keydown", function (e) {
    if (e.key === "Escape") closeMenu();
  });

  /* ---------- 3. Bilingual toggle (ID / EN) ---------- */
  var STORAGE_KEY = "nm-lang";
  var langToggle = document.getElementById("langToggle");
  var opts = langToggle ? langToggle.querySelectorAll(".lang-toggle__opt") : [];

  function applyLang(lang) {
    if (lang !== "id" && lang !== "en") lang = "en";
    document.documentElement.lang = lang;
    document.querySelectorAll("[data-en]").forEach(function (el) {
      var val = el.getAttribute("data-" + lang);
      if (val !== null) el.textContent = val;
    });
    document.querySelectorAll("[data-en-ph]").forEach(function (el) {
      var ph = el.getAttribute("data-" + lang + "-ph");
      if (ph !== null) el.setAttribute("placeholder", ph);
    });
    opts.forEach(function (o) {
      o.classList.toggle("is-active", o.getAttribute("data-lang") === lang);
    });
    scrambleTargets();
    try { localStorage.setItem(STORAGE_KEY, lang); } catch (e) {}
  }

  var saved = "en";
  try { saved = localStorage.getItem(STORAGE_KEY) || "en"; } catch (e) {}
  applyLang(saved);

  if (langToggle) {
    langToggle.addEventListener("click", function () {
      applyLang(document.documentElement.lang === "en" ? "id" : "en");
    });
  }

  /* ---------- 4. Scroll reveal ---------- */
  var reveals = document.querySelectorAll(".reveal");
  if ("IntersectionObserver" in window && !prefersReduced) {
    var io = new IntersectionObserver(function (entries) {
      entries.forEach(function (entry) {
        if (entry.isIntersecting) {
          entry.target.classList.add("is-visible");
          io.unobserve(entry.target);
        }
      });
    }, { threshold: 0.12, rootMargin: "0px 0px -40px 0px" });
    reveals.forEach(function (el) { io.observe(el); });
  } else {
    reveals.forEach(function (el) { el.classList.add("is-visible"); });
  }

  /* ---------- 5. Animated stat counters ---------- */
  function animateCount(el) {
    var target = parseInt(el.getAttribute("data-count"), 10) || 0;
    if (prefersReduced) { el.textContent = String(target); return; }
    var dur = 1400, start = null;
    function step(ts) {
      if (start === null) start = ts;
      var p = Math.min((ts - start) / dur, 1);
      var eased = 1 - Math.pow(1 - p, 3);
      el.textContent = String(Math.round(target * eased));
      if (p < 1) requestAnimationFrame(step);
    }
    requestAnimationFrame(step);
  }
  var nums = document.querySelectorAll(".stat__num");
  if ("IntersectionObserver" in window) {
    var io2 = new IntersectionObserver(function (entries) {
      entries.forEach(function (entry) {
        if (entry.isIntersecting) { animateCount(entry.target); io2.unobserve(entry.target); }
      });
    }, { threshold: 0.6 });
    nums.forEach(function (el) { io2.observe(el); });
  } else {
    nums.forEach(animateCount);
  }

  /* ---------- 6. Footer year ---------- */
  var yearEl = document.getElementById("year");
  if (yearEl) yearEl.textContent = String(new Date().getFullYear());

  /* ---------- 7. Contact form -> mailto (no backend, no storage) ---------- */
  var form = document.getElementById("demoForm");
  if (form) {
    form.addEventListener("submit", function (e) {
      e.preventDefault();
      var status = document.getElementById("formStatus");
      var isID = document.documentElement.lang === "id";

      if (!form.checkValidity()) {
        form.reportValidity();
        return;
      }

      var name = form.name.value.trim();
      var email = form.email.value.trim();
      var company = form.company.value.trim();
      var message = form.message.value.trim();

      var subject = "Demo request — " + (company || name || "NetraMesh");
      var bodyLines = [
        "Name: " + name,
        "Email: " + email,
        "Organization: " + (company || "-"),
        "",
        (message || "(No additional details provided.)")
      ];
      var href = "mailto:hello@netramesh.com" +
        "?subject=" + encodeURIComponent(subject) +
        "&body=" + encodeURIComponent(bodyLines.join("\r\n"));

      window.location.href = href;

      status.textContent = isID
        ? "Aplikasi email Anda akan terbuka dengan pesan yang sudah terisi."
        : "Your email client will open with a pre-filled message.";
      status.classList.add("is-ok");
    });
  }

  /* ---------- 8. Hero mesh network animation ---------- */
  var canvas = document.getElementById("meshCanvas");
  if (canvas && canvas.getContext && !prefersReduced) {
    var ctx = canvas.getContext("2d");
    var dpr = Math.min(window.devicePixelRatio || 1, 2);
    var W = 0, H = 0, nodes = [], raf = null, mouse = { x: -9999, y: -9999 };
    var packets = [], tick = 0;

    var COLOR_LINE = "30,136,229";
    var COLOR_NODE = "100,180,255";

    function size() {
      var rect = canvas.getBoundingClientRect();
      W = rect.width; H = rect.height;
      canvas.width = Math.floor(W * dpr);
      canvas.height = Math.floor(H * dpr);
      ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
      seed();
    }

    function seed() {
      var density = Math.max(28, Math.min(70, Math.floor((W * H) / 22000)));
      nodes = []; packets = [];
      for (var i = 0; i < density; i++) {
        nodes.push({
          x: Math.random() * W,
          y: Math.random() * H,
          vx: (Math.random() - 0.5) * 0.35,
          vy: (Math.random() - 0.5) * 0.35,
          r: Math.random() * 1.6 + 1
        });
      }
    }

    function frame() {
      ctx.clearRect(0, 0, W, H);
      var maxDist = 150;

      for (var i = 0; i < nodes.length; i++) {
        var n = nodes[i];
        n.x += n.vx; n.y += n.vy;
        if (n.x < 0 || n.x > W) n.vx *= -1;
        if (n.y < 0 || n.y > H) n.vy *= -1;

        // mouse interaction (subtle attraction)
        var mdx = mouse.x - n.x, mdy = mouse.y - n.y;
        var md = Math.sqrt(mdx * mdx + mdy * mdy);
        if (md < 160 && md > 0) {
          n.x += (mdx / md) * 0.4;
          n.y += (mdy / md) * 0.4;
        }
      }

      for (var a = 0; a < nodes.length; a++) {
        for (var b = a + 1; b < nodes.length; b++) {
          var dx = nodes[a].x - nodes[b].x;
          var dy = nodes[a].y - nodes[b].y;
          var dist = Math.sqrt(dx * dx + dy * dy);
          if (dist < maxDist) {
            var alpha = (1 - dist / maxDist) * 0.5;
            ctx.strokeStyle = "rgba(" + COLOR_LINE + "," + alpha.toFixed(3) + ")";
            ctx.lineWidth = 1;
            ctx.beginPath();
            ctx.moveTo(nodes[a].x, nodes[a].y);
            ctx.lineTo(nodes[b].x, nodes[b].y);
            ctx.stroke();
          }
        }
      }

      for (var k = 0; k < nodes.length; k++) {
        var p = nodes[k];
        ctx.fillStyle = "rgba(" + COLOR_NODE + ",0.9)";
        ctx.beginPath();
        ctx.arc(p.x, p.y, p.r, 0, Math.PI * 2);
        ctx.fill();
      }

      // Travelling packets along short edges (data flow)
      tick++;
      if (tick % 22 === 0 && packets.length < 14 && nodes.length > 2) {
        var s = nodes[(Math.floor(tick / 22) * 7) % nodes.length];
        var nearest = null, best = 9999;
        for (var t = 0; t < nodes.length; t++) {
          if (nodes[t] === s) continue;
          var ddx = nodes[t].x - s.x, ddy = nodes[t].y - s.y;
          var d2 = ddx * ddx + ddy * ddy;
          if (d2 < best && d2 > 100) { best = d2; nearest = nodes[t]; }
        }
        if (nearest && best < 160 * 160) packets.push({ from: s, to: nearest, p: 0 });
      }
      for (var pi = packets.length - 1; pi >= 0; pi--) {
        var pk = packets[pi];
        pk.p += 0.018;
        if (pk.p >= 1) { packets.splice(pi, 1); continue; }
        var px = pk.from.x + (pk.to.x - pk.from.x) * pk.p;
        var py = pk.from.y + (pk.to.y - pk.from.y) * pk.p;
        ctx.fillStyle = "rgba(103,192,255,0.95)";
        ctx.shadowColor = "rgba(30,136,229,0.9)";
        ctx.shadowBlur = 8;
        ctx.beginPath();
        ctx.arc(px, py, 2.2, 0, Math.PI * 2);
        ctx.fill();
        ctx.shadowBlur = 0;
      }

      raf = requestAnimationFrame(frame);
    }

    function start() { if (!raf) frame(); }
    function stop() { if (raf) { cancelAnimationFrame(raf); raf = null; } }

    window.addEventListener("resize", size);
    canvas.addEventListener("pointermove", function (e) {
      var rect = canvas.getBoundingClientRect();
      mouse.x = e.clientX - rect.left;
      mouse.y = e.clientY - rect.top;
    });
    canvas.addEventListener("pointerleave", function () { mouse.x = -9999; mouse.y = -9999; });

    // Pause animation when hero is off-screen (perf)
    if ("IntersectionObserver" in window) {
      new IntersectionObserver(function (entries) {
        entries.forEach(function (en) { en.isIntersecting ? start() : stop(); });
      }, { threshold: 0 }).observe(canvas);
    }

    size();
    start();
  }

  /* ---------- 9. Text scramble (decrypt) effect ---------- */
  function scrambleEl(el) {
    var target = el.textContent;
    if (prefersReduced) { el.textContent = target; return; }
    var len = target.length, frame = 0, queue = [];
    for (var i = 0; i < len; i++) {
      var start = Math.floor(Math.random() * 12);
      var end = start + Math.floor(Math.random() * 14) + 6;
      queue.push({ ch: target[i], start: start, end: end, rnd: "" });
    }
    function run() {
      var out = "", done = 0;
      for (var j = 0; j < queue.length; j++) {
        var q = queue[j];
        if (frame >= q.end) { done++; out += q.ch; }
        else if (frame >= q.start) {
          if (!q.rnd || Math.random() < 0.28) q.rnd = SCRAMBLE_CHARS[Math.floor(Math.random() * SCRAMBLE_CHARS.length)];
          out += '<span class="scr">' + q.rnd + "</span>";
        } else { out += q.ch === " " ? " " : ""; }
      }
      el.innerHTML = out; // content is from our own data attributes only
      if (done < queue.length) { frame++; requestAnimationFrame(run); }
      else { el.textContent = target; }
    }
    run();
  }
  function scrambleTargets() {
    document.querySelectorAll("[data-scramble]").forEach(scrambleEl);
  }
  // initial run shortly after load
  if (!prefersReduced) { requestAnimationFrame(scrambleTargets); }

  /* ---------- 10. Scroll progress bar ---------- */
  var bar = document.getElementById("scrollProgress");
  if (bar) {
    var rafBar = false;
    window.addEventListener("scroll", function () {
      if (rafBar) return; rafBar = true;
      requestAnimationFrame(function () {
        var h = document.documentElement;
        var max = h.scrollHeight - h.clientHeight;
        bar.style.width = (max > 0 ? (h.scrollTop / max) * 100 : 0) + "%";
        rafBar = false;
      });
    }, { passive: true });
  }

  /* ---------- 11. Hero spotlight follows pointer ---------- */
  var hero = document.getElementById("home");
  var spot = document.getElementById("spotlight");
  if (hero && spot && !prefersReduced) {
    hero.addEventListener("pointermove", function (e) {
      var r = hero.getBoundingClientRect();
      spot.style.setProperty("--mx", (e.clientX - r.left) + "px");
      spot.style.setProperty("--my", (e.clientY - r.top) + "px");
    });
  }

  /* ---------- 12. Live SOC console (simulated, no real data) ---------- */
  var consoleBody = document.getElementById("consoleBody");
  if (consoleBody) {
    var EVENTS = [
      [["t", "$ "], ["mod", "netramesh"], ["dim", " stream --live --mesh"]],
      [["t", "[siem] "], ["dim", "ingesting "], ["mod", "4,128"], ["dim", " events/s"]],
      [["t", "[cmdb] "], ["dim", "assets resolved "], ["ok", "12,640 online"]],
      [["t", "[ueba] "], ["dim", "anomaly score "], ["warn", "0.94"], ["dim", " → svc-bot@corp"]],
      [["crit", "[alert] "], ["dim", "T1021 lateral movement detected"]],
      [["t", "[sandbox] "], ["dim", "detonating sample "], ["warn", "a1f9..eD"], ["dim", " → "], ["crit", "malicious"]],
      [["t", "[soar] "], ["dim", "playbook "], ["mod", "isolate-host"], ["dim", " triggered"]],
      [["t", "[ir]   "], ["dim", "host "], ["mod", "WIN-DC-02"], ["dim", " "], ["ok", "contained"]],
      [["t", "[vuln] "], ["dim", "CVE-2026-3148 "], ["warn", "CVSS 9.8"], ["dim", " patched"]],
      [["ok", "✓ "], ["dim", "threat neutralized in "], ["ok", "2.1s"]],
      [["dim", "— mesh idle · monitoring —"]]
    ];
    var ei = 0;
    // Reduced-motion: render a static snapshot instead of animating
    if (prefersReduced) {
      EVENTS.forEach(function (parts) {
        var line = document.createElement("div");
        line.className = "console__line";
        line.style.animation = "none";
        line.style.opacity = "1";
        line.style.transform = "none";
        parts.forEach(function (p) {
          var span = document.createElement("span");
          span.className = p[0];
          span.textContent = p[1];
          line.appendChild(span);
        });
        consoleBody.appendChild(line);
      });
      return;
    }
    function typeLine(parts, done) {
      var line = document.createElement("div");
      line.className = "console__line";
      var cursor = document.createElement("span");
      cursor.className = "console__cursor";
      line.appendChild(cursor);
      consoleBody.appendChild(line);
      // keep console scrolled to newest, cap line count
      while (consoleBody.children.length > 11) consoleBody.removeChild(consoleBody.firstChild);

      var pi = 0;
      function nextPart() {
        if (pi >= parts.length) {
          cursor.remove();
          setTimeout(done, 480);
          return;
        }
        var cls = parts[pi][0], txt = parts[pi][1], ci = 0;
        var span = document.createElement("span");
        span.className = cls;
        line.insertBefore(span, cursor);
        function typeChar() {
          if (ci < txt.length) {
            span.textContent += txt[ci++]; // static strings only
            setTimeout(typeChar, 14 + Math.random() * 26);
          } else { pi++; nextPart(); }
        }
        typeChar();
      }
      nextPart();
    }
    function loop() {
      typeLine(EVENTS[ei], function () {
        ei = (ei + 1) % EVENTS.length;
        setTimeout(loop, ei === 0 ? 1400 : 260);
      });
    }
    // Start only when console is in view
    if ("IntersectionObserver" in window) {
      var started = false;
      new IntersectionObserver(function (entries) {
        entries.forEach(function (en) {
          if (en.isIntersecting && !started) { started = true; loop(); }
        });
      }, { threshold: 0.2 }).observe(consoleBody);
    } else { loop(); }
  }

  /* ---------- 13. 3D tilt on product cards ---------- */
  if (!prefersReduced && window.matchMedia("(pointer: fine)").matches) {
    document.querySelectorAll(".grid--products .card").forEach(function (card) {
      card.addEventListener("pointermove", function (e) {
        var r = card.getBoundingClientRect();
        var rx = ((e.clientY - r.top) / r.height - 0.5) * -7;
        var ry = ((e.clientX - r.left) / r.width - 0.5) * 7;
        card.style.transform = "translateY(-6px) rotateX(" + rx.toFixed(2) + "deg) rotateY(" + ry.toFixed(2) + "deg)";
      });
      card.addEventListener("pointerleave", function () { card.style.transform = ""; });
    });
  }

  /* ---------- 14. Magnetic buttons ---------- */
  if (!prefersReduced && window.matchMedia("(pointer: fine)").matches) {
    document.querySelectorAll("[data-magnetic]").forEach(function (btn) {
      btn.addEventListener("pointermove", function (e) {
        var r = btn.getBoundingClientRect();
        var x = (e.clientX - r.left - r.width / 2) * 0.3;
        var y = (e.clientY - r.top - r.height / 2) * 0.4;
        btn.style.transform = "translate(" + x.toFixed(1) + "px," + y.toFixed(1) + "px)";
      });
      btn.addEventListener("pointerleave", function () { btn.style.transform = ""; });
    });
  }

  /* ---------- 15. Live "threats blocked today" counter ---------- */
  var threatEl = document.getElementById("threatCount");
  if (threatEl) {
    function fmt(n) { return n.toLocaleString("en-US"); }
    // Seed from time-of-day so "today" feels real and grows on each reload
    var d = new Date();
    var secsToday = d.getHours() * 3600 + d.getMinutes() * 60 + d.getSeconds();
    var count = 18420 + Math.floor(secsToday * 13.74);

    if (prefersReduced) {
      threatEl.textContent = fmt(count);
    } else {
      // count-up from a slightly lower base for a live feel
      var from = Math.floor(count * 0.992), start = null, dur = 1400;
      function up(ts) {
        if (start === null) start = ts;
        var p = Math.min((ts - start) / dur, 1);
        var eased = 1 - Math.pow(1 - p, 3);
        threatEl.textContent = fmt(Math.round(from + (count - from) * eased));
        if (p < 1) requestAnimationFrame(up);
        else tickThreats();
      }
      function tickThreats() {
        count += Math.floor(Math.random() * 7) + 1;
        threatEl.textContent = fmt(count);
        threatEl.classList.remove("bump");
        void threatEl.offsetWidth; // reflow to restart animation
        threatEl.classList.add("bump");
        setTimeout(tickThreats, 900 + Math.random() * 1300);
      }
      requestAnimationFrame(up);
    }
  }

  /* ---------- 16. Command palette (press "/" or Ctrl/Cmd+K) ---------- */
  var cmdk = document.getElementById("cmdk");
  if (cmdk) {
    var cmdkInput = document.getElementById("cmdkInput");
    var cmdkList = document.getElementById("cmdkList");
    var cmdkEmpty = document.getElementById("cmdkEmpty");
    var cmdkFab = document.getElementById("cmdkFab");
    var cmItems = Array.prototype.slice.call(cmdkList.querySelectorAll(".cmdk__item"));
    var activeIdx = 0;
    var lastFocus = null;

    function visible() { return cmItems.filter(function (it) { return !it.hidden; }); }

    function setActive(i) {
      var vis = visible();
      cmItems.forEach(function (it) { it.classList.remove("is-active"); it.setAttribute("aria-selected", "false"); });
      if (!vis.length) { activeIdx = 0; return; }
      activeIdx = (i + vis.length) % vis.length;
      vis[activeIdx].classList.add("is-active");
      vis[activeIdx].setAttribute("aria-selected", "true");
      vis[activeIdx].scrollIntoView({ block: "nearest" });
    }

    function filterCmd(q) {
      q = q.trim().toLowerCase();
      var any = false;
      cmItems.forEach(function (it) {
        var hay = (it.textContent + " " + it.getAttribute("data-action")).toLowerCase();
        var match = !q || hay.indexOf(q) >= 0;
        it.hidden = !match;
        if (match) any = true;
      });
      cmdkEmpty.hidden = any;
      setActive(0);
    }

    function openCmdk() {
      if (!cmdk.hidden) return;
      lastFocus = document.activeElement;
      cmdk.hidden = false;
      document.body.style.overflow = "hidden";
      cmdkInput.value = "";
      filterCmd("");
      cmdkInput.focus();
    }
    function closeCmdk() {
      if (cmdk.hidden) return;
      cmdk.hidden = true;
      document.body.style.overflow = "";
      if (lastFocus && lastFocus.focus) lastFocus.focus();
    }

    function runAction(action) {
      closeCmdk();
      switch (action) {
        case "lang": applyLang(document.documentElement.lang === "en" ? "id" : "en"); break;
        case "email": window.location.href = "mailto:hello@netramesh.com"; break;
        case "top": window.location.hash = "#home"; break;
        default: window.location.hash = "#" + action; // products/solutions/platform/about/contact
      }
    }

    cmItems.forEach(function (it) {
      it.addEventListener("click", function () { runAction(it.getAttribute("data-action")); });
    });
    cmdk.addEventListener("click", function (e) {
      if (e.target.hasAttribute("data-cmdk-close")) closeCmdk();
    });
    if (cmdkFab) cmdkFab.addEventListener("click", openCmdk);

    cmdkInput.addEventListener("input", function () { filterCmd(cmdkInput.value); });

    cmdkInput.addEventListener("keydown", function (e) {
      if (e.key === "ArrowDown") { e.preventDefault(); setActive(activeIdx + 1); }
      else if (e.key === "ArrowUp") { e.preventDefault(); setActive(activeIdx - 1); }
      else if (e.key === "Enter") {
        e.preventDefault();
        var vis = visible();
        if (vis[activeIdx]) runAction(vis[activeIdx].getAttribute("data-action"));
      }
    });

    document.addEventListener("keydown", function (e) {
      var tag = (e.target && e.target.tagName) || "";
      var typing = tag === "INPUT" || tag === "TEXTAREA" || (e.target && e.target.isContentEditable);
      // Open with "/" (when not typing) or Ctrl/Cmd+K
      if (!cmdk.hidden) {
        if (e.key === "Escape") { e.preventDefault(); closeCmdk(); }
        return;
      }
      if ((e.key === "k" || e.key === "K") && (e.metaKey || e.ctrlKey)) { e.preventDefault(); openCmdk(); }
      else if (e.key === "/" && !typing && !e.metaKey && !e.ctrlKey) { e.preventDefault(); openCmdk(); }
    });
  }

  /* ---------- 17. Product preview — dashboard tabs + clickable cards ---------- */
  var appTabs = document.querySelectorAll(".appwin__tab");
  var appViews = document.querySelectorAll(".dashview");
  if (appTabs.length && appViews.length) {
    function activateView(view) {
      appTabs.forEach(function (t) {
        var on = t.getAttribute("data-view") === view;
        t.classList.toggle("is-active", on);
        t.setAttribute("aria-selected", on ? "true" : "false");
      });
      appViews.forEach(function (v) {
        var on = v.getAttribute("data-view") === view;
        v.classList.toggle("is-active", on);
        v.hidden = !on;
      });
    }
    appTabs.forEach(function (tab) {
      tab.addEventListener("click", function () { activateView(tab.getAttribute("data-view")); });
    });

    // Product cards jump to their related console view
    var preview = document.getElementById("preview");
    document.querySelectorAll(".card[data-goto]").forEach(function (card) {
      function go() {
        activateView(card.getAttribute("data-goto"));
        if (preview) preview.scrollIntoView({ behavior: prefersReduced ? "auto" : "smooth", block: "start" });
      }
      card.addEventListener("click", go);
      card.addEventListener("keydown", function (e) {
        if (e.key === "Enter" || e.key === " ") { e.preventDefault(); go(); }
      });
    });
  }

  /* ---------- 18. Apply data-* sizing/colors (CSP-safe; no inline style attrs) ---------- */
  document.querySelectorAll("[data-h]").forEach(function (el) { el.style.setProperty("--h", el.getAttribute("data-h")); });
  document.querySelectorAll("[data-w]").forEach(function (el) { el.style.setProperty("--w", el.getAttribute("data-w")); });
  document.querySelectorAll("[data-i]").forEach(function (el) { el.style.setProperty("--i", el.getAttribute("data-i")); });
  document.querySelectorAll("[data-bg]").forEach(function (el) { el.style.background = el.getAttribute("data-bg"); });

  /* ---------- 19. Scroll-spy — highlight active nav link ---------- */
  var navAnchors = document.querySelectorAll('.nav__links > a[href^="#"]');
  if (navAnchors.length && "IntersectionObserver" in window) {
    var linkById = {};
    var spySections = [];
    navAnchors.forEach(function (a) {
      var id = a.getAttribute("href").slice(1);
      var sec = id && document.getElementById(id);
      if (sec) { linkById[id] = a; spySections.push(sec); }
    });
    function setActiveLink(id) {
      navAnchors.forEach(function (a) { a.classList.toggle("is-active", a === linkById[id]); });
    }
    var spy = new IntersectionObserver(function (entries) {
      entries.forEach(function (en) { if (en.isIntersecting) setActiveLink(en.target.id); });
    }, { rootMargin: "-74px 0px -72% 0px", threshold: 0 });
    spySections.forEach(function (s) { spy.observe(s); });
  }

  /* ---------- 20. Name-story mesh: chaos → woven, controlled mesh ---------- */
  var sc = document.getElementById("storyMesh");
  if (sc && sc.getContext) {
    var sctx = sc.getContext("2d");
    var sdpr = Math.min(window.devicePixelRatio || 1, 2);
    var SW2 = 0, SH2 = 0, sn = [], sedges = [], link = 0, c = 0, entered = false, sraf = null, stick = 0, spk = [];

    function ssize() {
      var r = sc.getBoundingClientRect();
      SW2 = r.width; SH2 = r.height;
      sc.width = Math.floor(SW2 * sdpr); sc.height = Math.floor(SH2 * sdpr);
      sctx.setTransform(sdpr, 0, 0, sdpr, 0, 0);
      seedStory();
    }
    function seedStory() {
      var n = Math.max(16, Math.min(34, Math.round(SW2 / 30)));
      var cols = Math.max(4, Math.round(Math.sqrt(n * SW2 / Math.max(SH2, 1))));
      var rows = Math.ceil(n / cols);
      link = (SW2 / cols) * 1.55;
      sn = []; spk = [];
      var k = 0;
      for (var r = 0; r < rows; r++) {
        for (var col = 0; col < cols; col++) {
          if (k >= n) break;
          var hx = (col + 0.5) / cols * SW2 + (Math.random() - 0.5) * (SW2 / cols) * 0.5;
          var hy = (r + 0.5) / rows * SH2 + (Math.random() - 0.5) * (SH2 / rows) * 0.5;
          sn.push({
            hx: hx, hy: hy,
            x: Math.random() * SW2, y: Math.random() * SH2,
            vx: (Math.random() - 0.5) * 1.4, vy: (Math.random() - 0.5) * 1.4,
            ph: Math.random() * 6.28, dx: 0, dy: 0
          });
          k++;
        }
      }
      sedges = [];
      for (var i = 0; i < sn.length; i++)
        for (var j = i + 1; j < sn.length; j++) {
          var d = Math.hypot(sn[i].hx - sn[j].hx, sn[i].hy - sn[j].hy);
          if (d < link) sedges.push([i, j]);
        }
    }
    function easeInOut(t) { return t < 0.5 ? 2 * t * t : 1 - Math.pow(-2 * t + 2, 2) / 2; }

    function drawStory(staticMode) {
      sctx.clearRect(0, 0, SW2, SH2);
      var e = staticMode ? 1 : easeInOut(c);
      stick++;
      // resolve display positions
      for (var i = 0; i < sn.length; i++) {
        var p = sn[i];
        if (!staticMode) {
          p.x += p.vx; p.y += p.vy;
          if (p.x < 0 || p.x > SW2) p.vx *= -1;
          if (p.y < 0 || p.y > SH2) p.vy *= -1;
        }
        var breathe = staticMode ? 0 : Math.sin(stick * 0.02 + p.ph) * 3;
        p.dx = p.x + (p.hx + breathe - p.x) * e;
        p.dy = p.y + (p.hy - breathe - p.y) * e;
      }
      // edges (tighten as it converges)
      for (var k2 = 0; k2 < sedges.length; k2++) {
        var a = sn[sedges[k2][0]], b = sn[sedges[k2][1]];
        var dd = Math.hypot(a.dx - b.dx, a.dy - b.dy);
        var lim = link * 1.25;
        if (dd < lim) {
          var al = e * (1 - dd / lim) * 0.6;
          if (al > 0.01) {
            sctx.strokeStyle = "rgba(30,136,229," + al.toFixed(3) + ")";
            sctx.lineWidth = 1;
            sctx.beginPath(); sctx.moveTo(a.dx, a.dy); sctx.lineTo(b.dx, b.dy); sctx.stroke();
          }
        }
      }
      // nodes
      for (var m = 0; m < sn.length; m++) {
        var nb = 0.45 + 0.45 * e;
        sctx.fillStyle = "rgba(103,192,255," + nb.toFixed(3) + ")";
        sctx.beginPath(); sctx.arc(sn[m].dx, sn[m].dy, 1.8 + 0.8 * e, 0, 6.2832); sctx.fill();
      }
      // control pulses once woven
      if (!staticMode && e > 0.9 && sedges.length) {
        if (stick % 26 === 0 && spk.length < 5) spk.push({ ed: sedges[(stick * 7) % sedges.length], p: 0 });
        for (var s2 = spk.length - 1; s2 >= 0; s2--) {
          var pk = spk[s2]; pk.p += 0.03;
          if (pk.p >= 1) { spk.splice(s2, 1); continue; }
          var na = sn[pk.ed[0]], nc = sn[pk.ed[1]];
          var px = na.dx + (nc.dx - na.dx) * pk.p, py = na.dy + (nc.dy - na.dy) * pk.p;
          sctx.fillStyle = "rgba(160,210,255,0.95)";
          sctx.beginPath(); sctx.arc(px, py, 2, 0, 6.2832); sctx.fill();
        }
      }
    }
    function loopStory() {
      if (c < 1) c += 0.0065;
      drawStory(false);
      sraf = requestAnimationFrame(loopStory);
    }
    function startStory() { if (!sraf) loopStory(); }
    function stopStory() { if (sraf) { cancelAnimationFrame(sraf); sraf = null; } }

    window.addEventListener("resize", ssize);
    ssize();

    if (prefersReduced) {
      c = 1; drawStory(true);
    } else if ("IntersectionObserver" in window) {
      new IntersectionObserver(function (entries) {
        entries.forEach(function (en) {
          if (en.isIntersecting) { c = 0; startStory(); }   // replay the chaos→order story each time it enters
          else stopStory();
        });
      }, { threshold: 0.25 }).observe(sc);
    } else { startStory(); }
  }
})();
