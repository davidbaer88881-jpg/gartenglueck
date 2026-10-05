// Kleine Brücke zwischen Spiel und Android-App (Zurück-Taste, Vollbild, kein Kontextmenü)
(function(){
  document.addEventListener('contextmenu', e => e.preventDefault());
  const C = window.Capacitor;
  if (!C || !C.isNativePlatform || !C.isNativePlatform()) return;
  document.documentElement.classList.add('native-app');
  const P = C.Plugins || {};
  if (P.App){
    P.App.addListener('backButton', () => {
      const handled = typeof window.GG_back === 'function' && window.GG_back();
      if (!handled) P.App.minimizeApp();
    });
  }
})();
