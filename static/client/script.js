class SafeSendApp {
    createUrl   = 'https://22erbbnurht77kwkxzmfbkqp240laulz.lambda-url.us-east-1.on.aws/'
    retrieveUrl = 'https://fz5bva7ou3qhoyuhzsz6km2r5u0dgjet.lambda-url.us-east-1.on.aws/'
    appState
    appStateEncrypt = 'encrypt'
    appStateDecrypt = 'decrypt'
    secretId

    constructor() {
        this.encoder = new TextEncoder("utf-8");
        this.decoder = new TextDecoder("utf-8");

        this.setupElements()
        this.setupEncrpytionVals()
        this.setupListeners()
        this.retrieveUrlParams()
        this.setupAppState()
    }

    setupElements() {
        this.appRoot = document.querySelector(".safe-send")
        this.userInput = document.getElementById("userInput")

        this.expirySelector = document.getElementById("expiry")
        this.encryptSubmit = document.getElementById("encryptButton")
        this.shareUrl = document.getElementById("url")
        this.copyToast = document.getElementById("copyToast")

        this.decryptSubmit = document.getElementById("revealButton")
        this.decryptMessageContent = document.getElementById("decryptedMessage")
        this.decryptMessageContainer = document.querySelector(".safe-send__decrypted-message")

        this.resetAppElements = document.querySelectorAll(".reset-app")
    }

    async setupAppState() {
        const url = new URL(window.location.href)
        const params = new URLSearchParams(url.search)

        const id = params.get("id")
        const rawKey = window.location.hash.replace("#", "")
        if (id && rawKey) {
            this.secretId = id
            this.key = await this.importKey(rawKey)
        }

        this.appState = id && rawKey ? this.appStateDecrypt : this.appStateEncrypt

        this.appRoot.dataset.state = this.appState
    }

    retrieveUrlParams() {
        const url = new URL(window.location)
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
        const expiry = this.expirySelector.value

        const exportedKey = await this.exportKey()

        const bodyContent = {
            iv: btoa(String.fromCharCode(...this.iv)),
            payload: encryptedPayload,
            expiry: parseInt(expiry)
        }

        const response = await fetch(this.createUrl, {
            method: 'PUT',
            headers: {
                "Content-Type": "application/x-www-form-urlencoded",
            },
            body: JSON.stringify(bodyContent)
        })

        if (!response.ok) {
            throw new Error(`Response status: ${response.status}`);
        }

        const result = await response.json();

        const shareUrl = `${window.location.origin}/?id=${result.id}#${exportedKey}`
        this.shareUrl.innerHTML = shareUrl
        this.appRoot.classList.add("form-submitted")
    }

    async triggerDecryption() {
        const response = await fetch(`${this.retrieveUrl}/?id=${this.secretId}`)
        this.appRoot.classList.add("decoded-response-returned")

        if (!this.decryptMessageContainer) return
        this.decryptMessageContainer.classList.add("display")

        if (!response.ok) {
            this.decryptMessageContainer.dataset.statusCode = response.status
            this.decryptMessageContainer.classList.add("error")

            throw new Error(`Response status: ${response.status}`);
        }

        const result = await response.json();

        const { payload } = result
        const iv = Uint8Array.from(atob(result.iv), c => c.charCodeAt(0));

        const retrievedMessage = await this.getDecryptedPayload(payload, iv)
        this.decryptMessageContent.innerHTML = retrievedMessage
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

    triggerShareButtonClick() {
        const visibleClass = "visible"

        navigator.clipboard.writeText(this.shareUrl.innerHTML)
        this.copyToast.classList.add(visibleClass)

        setTimeout(() => {
            this.copyToast.classList.remove(visibleClass)
        }, 1500)
    }

    resetApp() {
        this.setupEncrpytionVals()

        this.appRoot.removeAttribute("data-state")
        this.appRoot.classList.remove("form-submitted")
        this.appRoot.classList.remove("decoded-response-returned")
        this.decryptMessageContainer.classList.remove("error")
        this.decryptMessageContainer.classList.remove("display")
        this.decryptMessageContainer.removeAttribute("data-status-code")
    }

    setupListeners() {
        this.encryptSubmit.addEventListener("click", () => this.triggerEncryption())
        this.decryptSubmit.addEventListener("click", () => this.triggerDecryption())
        this.shareUrl.addEventListener("click", () => this.triggerShareButtonClick())

        for (const ele of this.resetAppElements) {
            ele.addEventListener("click", () => this.resetApp())
        }
    }
}

document.addEventListener("DOMContentLoaded", () => {
    new SafeSendApp()

    const yearSelector = document.getElementById("year")
    yearSelector.innerHTML = (new Date).getFullYear()
})
