/**
 * DocGuard AI — entrance-animation shim (small IIFE)
 *
 * Faithful to the spec's supplied IIFE: content must never stay invisible.
 * The entrance animations are pure CSS keyframes; this shim ensures every
 * `.animate-fade-in-up` element reaches its visible end state even when the
 * keyframe animation never fires (reduced motion stripping, animation-cap
 * mismatches, or a broken stylesheet).
 *
 * Because React mounts the nodes asynchronously, the shim watches the DOM
 * and re-checks whenever new nodes appear, then arms a short safety timeout
 * per node and one global backstop.
 */
(function () {
  if (typeof window === 'undefined' || typeof document === 'undefined') return;

  var ANIM_CLASS = 'animate-fade-in-up';
  var SAFETY_MS = 1600;

  function ensureVisible(el) {
    el.classList.remove(ANIM_CLASS);
    el.style.opacity = '1';
    el.style.transform = 'none';
  }

  function animationDeclared(el) {
    try {
      var name = window.getComputedStyle(el).animationName || 'none';
      return name && name !== 'none';
    } catch (e) {
      return false;
    }
  }

  function handle(el) {
    if (animationDeclared(el)) {
      // Keyframes are live — let them run, but backstop visibility.
      setTimeout(ensureVisible, SAFETY_MS, el);
    } else {
      // No animation applied (reduced motion, engine gap): reveal now.
      ensureVisible(el);
    }
  }

  function scan(root) {
    var nodes = root.querySelectorAll('.' + ANIM_CLASS);
    for (var i = 0; i < nodes.length; i++) handle(nodes[i]);
  }

  function start() {
    scan(document);

    // Watch for React-mounting nodes.
    var observer = new MutationObserver(function (mutations) {
      for (var i = 0; i < mutations.length; i++) {
        var added = mutations[i].addedNodes;
        for (var j = 0; j < added.length; j++) {
          var node = added[j];
          if (node.nodeType === 1) {
            if (node.classList && node.classList.contains(ANIM_CLASS)) handle(node);
            if (node.querySelectorAll) scan(node);
          }
        }
      }
    });

    try {
      observer.observe(document.documentElement, { childList: true, subtree: true });
    } catch (e) {
      /* no-op */
    }

    // Global backstop a little later.
    setTimeout(function () { scan(document); }, SAFETY_MS + 400);
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', start);
  } else {
    start();
  }
})();