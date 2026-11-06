
const DB_NAME = "agentlab-secure-storage";
const STORE_NAME = "credentials";
const DB_VERSION = 1;

const PBKDF2_ITERATIONS = 600_000;
const AES_KEY_LENGTH = 256;

export type Provider =
  | "gemini"
  | "openai"
  | "anthropic"
  | "llama";

type StoredCredential = {
  agentId: string;
  provider: Provider;
  encryptedApiKey: ArrayBuffer;
  salt: Uint8Array;
  iv: Uint8Array;
  iterations: number;
  updatedAt: string;
};

export type CredentialMetadata = {
  agentId: string;
  provider: Provider;
  updatedAt: string;
};

function openDatabase(): Promise<IDBDatabase> {
  return new Promise((resolve, reject) => {
    const request = indexedDB.open(DB_NAME, DB_VERSION);

    request.onupgradeneeded = () => {
      const db = request.result;

      if (!db.objectStoreNames.contains(STORE_NAME)) {
        db.createObjectStore(STORE_NAME, {
          keyPath: "agentId",
        });
      }
    };

    request.onsuccess = () => resolve(request.result);
    request.onerror = () => reject(request.error);
  });
}

async function deriveEncryptionKey(
  password: string,
  salt: Uint8Array,
  iterations: number
): Promise<CryptoKey> {
  const passwordBytes = new TextEncoder().encode(password);

  const material = await crypto.subtle.importKey(
    "raw",
    passwordBytes,
    "PBKDF2",
    false,
    ["deriveKey"]
  );

  return crypto.subtle.deriveKey(
    {
    name: "PBKDF2",
    salt: Uint8Array.from(salt).buffer as ArrayBuffer,
    iterations,
    hash: "SHA-256",
    },
    material,
    {
      name: "AES-GCM",
      length: AES_KEY_LENGTH,
    },
    false,
    ["encrypt", "decrypt"]
  );
}

function saveRecord(
  credential: StoredCredential
): Promise<void> {
  return openDatabase().then(
    (db) =>
      new Promise((resolve, reject) => {
        const transaction = db.transaction(
          STORE_NAME,
          "readwrite"
        );

        transaction.objectStore(STORE_NAME).put(credential);

        transaction.oncomplete = () => {
          db.close();
          resolve();
        };

        transaction.onerror = () => {
          db.close();
          reject(transaction.error);
        };

        transaction.onabort = () => {
          db.close();
          reject(transaction.error);
        };
      })
  );
}

async function readRecord(
  agentId: string
): Promise<StoredCredential | undefined> {
  const db = await openDatabase();

  return new Promise((resolve, reject) => {
    const transaction = db.transaction(
      STORE_NAME,
      "readonly"
    );

    const request = transaction
      .objectStore(STORE_NAME)
      .get(agentId);

    request.onsuccess = () => {
      db.close();
      resolve(request.result);
    };

    request.onerror = () => {
      db.close();
      reject(request.error);
    };
  });
}

export async function saveCredential(
  agentId: string,
  provider: Provider,
  apiKey: string,
  password: string
): Promise<void> {
  if (!agentId || !apiKey.trim()) {
    throw new Error("Agente e chave de API são obrigatórios.");
  }

  if (provider === "llama") {
    throw new Error(
      "O provedor Llama não necessita de chave de API."
    );
  }

  if (password.length < 12) {
    throw new Error(
      "A senha deve possuir pelo menos 12 caracteres."
    );
  }

  const salt = crypto.getRandomValues(new Uint8Array(16));
  const iv = crypto.getRandomValues(new Uint8Array(12));

  const encryptionKey = await deriveEncryptionKey(
    password,
    salt,
    PBKDF2_ITERATIONS
  );

  const encryptedApiKey = await crypto.subtle.encrypt(
    {
      name: "AES-GCM",
      iv,
      additionalData: new TextEncoder().encode(agentId),
    },
    encryptionKey,
    new TextEncoder().encode(apiKey.trim())
  );

  await saveRecord({
    agentId,
    provider,
    encryptedApiKey,
    salt,
    iv,
    iterations: PBKDF2_ITERATIONS,
    updatedAt: new Date().toISOString(),
  });
}

export async function unlockCredential(
  agentId: string,
  password: string
): Promise<{
  provider: Provider;
  apiKey: string;
}> {
  const credential = await readRecord(agentId);

  if (!credential) {
    throw new Error(
      "Nenhuma credencial foi cadastrada para este agente."
    );
  }

  const encryptionKey = await deriveEncryptionKey(
    password,
    credential.salt,
    credential.iterations
  );

  try {
    const decrypted = await crypto.subtle.decrypt(
      {
        name: "AES-GCM",
        iv: Uint8Array.from(credential.iv).buffer as ArrayBuffer,
        additionalData: new TextEncoder().encode(agentId),
      },
      encryptionKey,
      credential.encryptedApiKey
    );

    return {
      provider: credential.provider,
      apiKey: new TextDecoder().decode(decrypted),
    };
  } catch {
    throw new Error(
      "Não foi possível desbloquear a credencial. Verifique a senha."
    );
  }
}

export async function getCredentialMetadata(
  agentId: string
): Promise<CredentialMetadata | null> {
  const credential = await readRecord(agentId);

  if (!credential) return null;

  return {
    agentId: credential.agentId,
    provider: credential.provider,
    updatedAt: credential.updatedAt,
  };
}

export async function deleteCredential(
  agentId: string
): Promise<void> {
  const db = await openDatabase();

  return new Promise((resolve, reject) => {
    const transaction = db.transaction(
      STORE_NAME,
      "readwrite"
    );

    transaction.objectStore(STORE_NAME).delete(agentId);

    transaction.oncomplete = () => {
      db.close();
      resolve();
    };

    transaction.onerror = () => {
      db.close();
      reject(transaction.error);
    };
  });
}
