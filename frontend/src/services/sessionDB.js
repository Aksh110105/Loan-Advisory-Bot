import { openDB } from 'idb';

const dbPromise = openDB('sessionStore', 1, {
  upgrade(db) {
    db.createObjectStore('sessions', { keyPath: 'id' });
    db.createObjectStore('intents', { keyPath: 'timestamp' });
  }
});

export const SessionDB = {
  async getSession() {
    return (await dbPromise).get('sessions', 'current');
  },
  async saveIntent(intent) {
    (await dbPromise).add('intents', {
      ...intent,
      timestamp: Date.now()
    });
  }
};