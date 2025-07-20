import localforage from 'localforage';
import { v4 as uuidv4 } from 'uuid'; 

export const initSession = async () => {
  let sessionId = await localforage.getItem('session_id');

  if (!sessionId) {
    sessionId = uuidv4();  // Create only if it doesn't exist
    await localforage.setItem('session_id', sessionId);
    console.log(' New session created & stored:', sessionId);
  } else {
    console.log(' Existing session resumed:', sessionId);
  }

  return sessionId;
};
