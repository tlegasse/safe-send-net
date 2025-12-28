class SafeSend {
    constructor() {
        this.encoder = new TextEncoder("utf-8");
        this.decoder = new TextDecoder("utf-8");

        this.setupElements()
        this.setupEncrpytionVals()
        this.setupListeners()
    }

    setupElements() {
        this.userInput = document.getElementById("raw")
        this.decryptSubmit = document.getElementById("decrypt-submit")
        this.encrypted = document.getElementById("encrypted")
    }

    async setupEncrpytionVals() {
        this.iv = window.crypto.getRandomValues(new Uint8Array(12));
        this.key = await window.crypto.subtle.generateKey(
            { name: "AES-GCM", length: 256 },
            true,
            ["encrypt", "decrypt"]
        );
    }

    async exportKey() {
        const raw = await window.crypto.subtle.exportKey("raw", this.key);
        return btoa(String.fromCharCode(...new Uint8Array(raw)));
    }

    async importKey(base64) {
        const raw = Uint8Array.from(atob(base64), c => c.charCodeAt(0));
        return await window.crypto.subtle.importKey(
            "raw",
            raw,
            "AES-GCM",
            false,
            ["decrypt"]
        );
    }

    async triggerEncryption() {
        const payload = this.userInput.value
        const encryptedPayload = await this.getEncryptedPayload(payload)

        encrypted.value = JSON.stringify({
            keyStr: await this.exportKey(),
            iv: btoa(String.fromCharCode(...this.iv)),
            payload: encryptedPayload
        })
    }

    async triggerDecryption() {
        const encryptedStr = encrypted.value
        const { keyStr, iv: ivBase64, payload } = JSON.parse(encryptedStr)
        const iv = Uint8Array.from(atob(ivBase64), c => c.charCodeAt(0));
        this.key = await this.importKey(keyStr)

        console.log(await this.getDecryptedPayload(payload, iv))
    }

    async getEncryptedPayload(payload) {
        const encryptedPayload = await window.crypto.subtle.encrypt(
            {
                name: "AES-GCM",
                iv: this.iv
            },
            this.key,
            this.encoder.encode(payload)
        );

        let buffer = new Uint8Array(encryptedPayload, 0, encryptedPayload.byteLength);
        const base64 = btoa(String.fromCharCode(...buffer));
        return base64
    }

    async getDecryptedPayload(payload, iv) {
        payload = Uint8Array.from(atob(payload), c => c.charCodeAt(0));

        let decrypted = await window.crypto.subtle.decrypt(
            {
                name: "AES-GCM",
                iv
            },
            this.key,
            payload.buffer
        );

        const arr = new Uint8Array(decrypted)
        return this.decoder.decode(arr)
    }

    setupListeners() {
        this.userInput.addEventListener("change", () => this.triggerEncryption())
        this.encrypted.addEventListener("change", () => this.triggerDecryption())
    }
}

document.addEventListener("DOMContentLoaded", () => {
    new SafeSend()
})
