const crypto = require('crypto');

// Railway token to add as secret
const token = "00c9be57-884c-4fa6-97db-7bd53180025c";

// Public key from GitHub (base64 encoded)
const publicKeyB64 = "w8JYvynU074Q2pFSRdsMtS/nSGqxguG9z/4iXs0ISQI=";

// Decode the public key
const publicKey = crypto.createPublicKey({
  key: Buffer.from(publicKeyB64, 'base64'),
  format: 'pem',
  type: 'spki'
});

// Encrypt the token using RSA-OAEP with SHA-256 (GitHub's expected algorithm)
const encrypted = crypto.publicEncrypt(
  {
    key: publicKey,
    padding: crypto.constants.RSA_PKCS1_OAEP_PADDING
  },
  Buffer.from(token, 'utf8')
);

// Base64 encode the encrypted value
const encryptedB64 = encrypted.toString('base64');

console.log(JSON.stringify({
  encrypted_value: encryptedB64,
  public_key: publicKeyB64
}));
