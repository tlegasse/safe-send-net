# Introduction
This projects comprises 2 CDK stacks:
- `server` - Provides provisions for the lambda functions and DB server powering the experienc.
- `client` - Provides provisions for the client application, A.K.A. the website.

The front-end is responsible for all encryption.
Only the payload (encrypted) and iv value are sent to the server, as well as the wait value in seconds.
An example encrypted string would look like so:
```
{
  "keyStr": "OgjxY9l9RE19uAN4VQ/5iRhSOebyhUcPdRI5gkrYJAY=",
  "iv": "TUDoeRVf2YGA2WhS",
  "payload": "0TMqVRymzYuJr+kPHsbZWRNZ62Q9eInY"
}
```

# Static content
Some content, such as lambda function code and the front-end app are served statically.
They live in the `static` directory

ServerStack.GetSecretUrl = https://22erbbnurht77kwkxzmfbkqp240laulz.lambda-url.us-east-1.on.aws/
ServerStack.PutSecretUrl = https://fz5bva7ou3qhoyuhzsz6km2r5u0dgjet.lambda-url.us-east-1.on.aws/
