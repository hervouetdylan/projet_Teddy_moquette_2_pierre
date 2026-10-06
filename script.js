// ---------- Menu mobile ----------
const boutonMenu = document.querySelector('.menu-bouton');
const menu = document.querySelector('.menu');

if (boutonMenu && menu) {
  boutonMenu.addEventListener('click', () => {
    const ouvert = menu.classList.toggle('ouvert');
    boutonMenu.setAttribute('aria-expanded', ouvert);
  });
}

// ---------- Diaporama ----------
const diaporama = document.querySelector('.diaporama');

if (diaporama) {
  const diapos = [...diaporama.querySelectorAll('.diapo')];
  const zonePoints = diaporama.querySelector('.points');
  const DUREE = 5500; // millisecondes entre deux photos
  const mouvementReduit = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
  let courante = 0;
  let minuteur = null;

  // Un repère par photo, créé automatiquement
  const points = diapos.map((_, i) => {
    const point = document.createElement('button');
    point.setAttribute('role', 'tab');
    point.setAttribute('aria-label', `Photo ${i + 1} sur ${diapos.length}`);
    point.addEventListener('click', () => { afficher(i); relancer(); });
    zonePoints.appendChild(point);
    return point;
  });

  function afficher(index) {
    courante = (index + diapos.length) % diapos.length;
    diapos.forEach((d, i) => d.classList.toggle('active', i === courante));
    points.forEach((p, i) => p.setAttribute('aria-selected', i === courante));
  }

  function arreter() { clearInterval(minuteur); }

  function relancer() {
    arreter();
    if (!mouvementReduit) {
      minuteur = setInterval(() => afficher(courante + 1), DUREE);
    }
  }

  diaporama.querySelectorAll('.fleche').forEach((fleche) => {
    fleche.addEventListener('click', () => {
      afficher(courante + Number(fleche.dataset.sens));
      relancer();
    });
  });

  // Pause quand la souris ou le clavier est sur le diaporama
  diaporama.addEventListener('mouseenter', arreter);
  diaporama.addEventListener('mouseleave', relancer);
  diaporama.addEventListener('focusin', arreter);
  diaporama.addEventListener('focusout', relancer);

  afficher(0);
  relancer();
}

// ---------- Curseur avant / après ----------
document.querySelectorAll('.comparateur').forEach((comparateur) => {
  const curseur = comparateur.querySelector('input');
  curseur.addEventListener('input', () => {
    comparateur.style.setProperty('--pos', curseur.value + '%');
  });
});
