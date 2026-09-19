/* Run immediately after the header so mobile navigation settles before main content. */
(() => {
  'use strict';
  const menuButton = document.querySelector('.nav-toggle');
  const menu = menuButton && document.getElementById(menuButton.getAttribute('aria-controls'));
  if (!menuButton || !menu) return;
  const smallScreen = window.matchMedia('(max-width: 800px)');
  const setMenu = (open) => {
    menuButton.setAttribute('aria-expanded', String(open));
    menu.hidden = smallScreen.matches && !open;
  };
  const adaptMenu = () => setMenu(false);
  menuButton.hidden = false;
  menuButton.addEventListener('click', () => setMenu(menuButton.getAttribute('aria-expanded') !== 'true'));
  document.addEventListener('keydown', (event) => {
    if (event.key === 'Escape' && smallScreen.matches && menuButton.getAttribute('aria-expanded') === 'true') {
      setMenu(false);
      menuButton.focus();
    }
  });
  smallScreen.addEventListener('change', adaptMenu);
  adaptMenu();
})();
