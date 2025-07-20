export const saveChat = async (sessionId, message) => {
  // Save to IndexedDB
  await localforage.setItem(`chat_${sessionId}`, 
    [...(await localforage.getItem(`chat_${sessionId}`) || []), message]
  );

  // Sync with backend
  await api.post('/chats', {
    session_id: sessionId,
    ...message
  });
};

export const safeSync = async (sessionId) => {
  try {
    const localData = await localforage.getItem(`chat_${sessionId}`);
    await api.post('/chats/sync', localData);
  } catch (error) {
    console.error('Sync failed, maintaining local copy:', error);
    localforage.setItem(`pending_sync_${sessionId}`, true);
  }
};