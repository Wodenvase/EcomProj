(function(){
  const domain = window.location.hostname;
  if(!domain) return;

  function injectBadge(data){
    if(document.getElementById('hashtrack-badge')) return;
    const badge = document.createElement('div');
    badge.id = 'hashtrack-badge';
    badge.style.cssText = 'position:fixed;right:12px;top:12px;z-index:2147483647;padding:8px 12px;border-radius:6px;color:#fff;font-family:Arial,sans-serif;font-weight:700';
    const color = data.risk_level === 'CRITICAL' ? '#d32f2f' : data.risk_level === 'CAUTION' ? '#fbc02d' : '#388e3c';
    badge.style.background = color;
    badge.innerText = `Trust ${data.trust_score} - ${data.risk_level}`;
    document.body.appendChild(badge);
  }

  chrome.storage.local.get([domain], function(result){
    if(result && result[domain]){
      injectBadge(result[domain]);
      return;
    }

    fetch('http://localhost:8000/analyze', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ url: window.location.href })
    })
    .then(r => r.json())
    .then(data => {
      const store = {};
      store[domain] = data;
      chrome.storage.local.set(store, function(){/* saved */});
      injectBadge(data);
    })
    .catch(err => console.log('HashTrack fetch error', err));
  });
})();
