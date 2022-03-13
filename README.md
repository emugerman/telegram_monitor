## Getting Started

Install the following python lib:

```
pip install -r requirements.txt
```

### Prerequisites

Create API access account at: 

https://my.telegram.org/

More details here:

https://docs.telethon.dev/en/latest/basic/signing-in.html#signing-in

Edit the following lines in the code:

```python
self.api_id = "your_api_id"
self.api_hash = "your_api_hash"
self.account_phone = "yhour_phone_number" # in the format of +97254....
```

In case you have 2FA on the telegram account, edit the following code:

```python
await client.sign_in(password=r'your_2fa_password')
```

It will persist a `session` object in `/files` so in subsequent runs, you won't need the telegram password.