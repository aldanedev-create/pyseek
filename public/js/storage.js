(function () {
  const DB = 'pyseek-local', VERSION = 1;
  function open() { return new Promise((resolve, reject) => { const request = indexedDB.open(DB, VERSION); request.onupgradeneeded = () => { for (const name of ['history', 'saved']) if (!request.result.objectStoreNames.contains(name)) request.result.createObjectStore(name, { keyPath: 'id' }); }; request.onsuccess = () => resolve(request.result); request.onerror = () => reject(request.error); }); }
  async function list(store) { const db = await open(); return new Promise((resolve, reject) => { const request = db.transaction(store).objectStore(store).getAll(); request.onsuccess = () => resolve(request.result.sort((a, b) => (b.createdAt || 0) - (a.createdAt || 0))); request.onerror = () => reject(request.error); }); }
  async function put(store, value) { const db = await open(); return new Promise((resolve, reject) => { const request = db.transaction(store, 'readwrite').objectStore(store).put(value); request.onsuccess = resolve; request.onerror = () => reject(request.error); }); }
  async function clear(store) { const db = await open(); return new Promise((resolve, reject) => { const request = db.transaction(store, 'readwrite').objectStore(store).clear(); request.onsuccess = resolve; request.onerror = () => reject(request.error); }); }
  window.PySeekStorage = { list, put, clear };
})();
