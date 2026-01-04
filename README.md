# Safe Send
A privacy first, second and third secrets sharing application.

## Why?
This is the real world, if the general user perceives even slight friction in following security protocol sharing sensetive data, it's going in an email in plain text.
It happens constantly, and especially now, data leaks happen constantly, and prying eyes are always on us. Enter Safe Send, my take on an essential security practice, snappy and secure secrets sharing.
To provide a secure environment, the following features are provided:
- A zero trust means of sharing potentially secure data.
- Secret deletion upon access or expiry.
- No production logging.
- Scalable AWS hosting.

## How?
This projects leverages CDK to implement an infrastructure as a service hosting platofrm.
It comprises the following Cloud Formation stacks

### Client
An S3 hosted, cloudfront distributed website.
All encryption is performed by native browser SubtleCrypt API's.
Secrets are passed to the server after encryption with an expiry time.
After encrypted data is stored, a sharable URL containing both the secret's UUID and a secret key stored after the URL hash.
Accessing the URL with the UUID and key present presents the user the ability to recall the secret (if still live) and decrypt.

### Server
There are two hosted functions corresponding to read and write actions.

#### `secrets-create`
Validates and stores secrets.

#### `secrets-get`
Retrieves, validates and destroys stored functions.

## License
Source code is available for review and security auditing purposes only.
No license is granted for use, modification, distribution or deployment.

This is intended to change in the future as the project matures.
