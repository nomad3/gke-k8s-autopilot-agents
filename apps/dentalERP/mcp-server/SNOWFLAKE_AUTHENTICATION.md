# ❄️ Snowflake Authentication Guide

Complete guide to authenticating with Snowflake from the MCP Server.

---

## 🔐 Authentication Methods Overview

Snowflake supports multiple authentication methods. Our MCP Server implementation supports all of them:

### 1. **Username & Password** (Simplest - Good for Development)
- **Pros**: Easy to set up, no additional configuration
- **Cons**: Less secure, passwords can be exposed
- **Use case**: Development, testing, getting started

### 2. **Key-Pair Authentication** (Recommended for Production)
- **Pros**: More secure (private key never transmitted), supports key rotation
- **Cons**: Requires key generation and management
- **Use case**: Production deployments, CI/CD pipelines

### 3. **OAuth** (Enterprise)
- **Pros**: Centralized identity management, SSO integration
- **Cons**: Complex setup, requires OAuth provider
- **Use case**: Enterprise deployments with existing OAuth infrastructure

### 4. **Programmatic Access Tokens (PAT)** (Snowflake 2024+)
- **Pros**: Simple, no password exposure
- **Cons**: Newer feature, token management required
- **Use case**: Automation, service accounts

---

## 📊 Comparison: Python Connector vs REST API

Our implementation uses **snowflake-connector-python**, which is the **recommended approach**:

| Feature | Python Connector | SQL REST API |
|---------|-----------------|--------------|
| **Performance** | ✅ Native, optimized | ⚠️ HTTP overhead |
| **Authentication** | ✅ All methods | ✅ All methods |
| **Connection Pooling** | ✅ Built-in | ❌ Manual |
| **Result Streaming** | ✅ Efficient | ⚠️ Pagination required |
| **Async Support** | ⚠️ Limited | ✅ Native HTTP async |
| **Maturity** | ✅ Very mature | ✅ Mature |
| **Use Case** | **Backend services** | API-only environments |

**Recommendation**: Use `snowflake-connector-python` (what we have) for backend services. Use SQL REST API only if you can't install native libraries.

---

## 🚀 Method 1: Username & Password (Current Implementation)

### Setup (5 minutes)

**1. Get credentials from Snowflake**
- Username: Your Snowflake username (e.g., `ADMIN` or your email)
- Password: Your Snowflake password

**2. Configure `.env`**
```bash
SNOWFLAKE_ACCOUNT=xy12345.us-east-1.aws
SNOWFLAKE_USER=ADMIN
SNOWFLAKE_PASSWORD=YourSecurePassword123!
SNOWFLAKE_WAREHOUSE=COMPUTE_WH
SNOWFLAKE_DATABASE=DENTAL_ERP_DW
SNOWFLAKE_SCHEMA=PUBLIC
SNOWFLAKE_ROLE=ACCOUNTADMIN
```

**3. Test**
```bash
./test-snowflake.sh
```

**Pros**: Quick to set up, works immediately
**Cons**: Password stored in environment variable

---

## 🔑 Method 2: Key-Pair Authentication (Recommended for Production)

### Setup (10 minutes)

**1. Generate RSA Key Pair**

```bash
# Generate private key (no encryption for automation, use encryption for manual access)
openssl genrsa 2048 | openssl pkcs8 -topk8 -inform PEM -out rsa_key.p8 -nocrypt

# Generate public key
openssl rsa -in rsa_key.p8 -pubout -out rsa_key.pub

# Get public key fingerprint (needed for Snowflake)
openssl rsa -pubin -in rsa_key.pub -outform DER | openssl dgst -sha256 -binary | openssl enc -base64
```

**2. Register Public Key with Snowflake**

Log in to Snowflake Web UI and run:

```sql
-- Get your current public key (if any)
DESC USER MCP_USER;

-- Set the public key (paste contents of rsa_key.pub, removing header/footer)
ALTER USER MCP_USER SET RSA_PUBLIC_KEY='MIIBIjANBgkqhki...';

-- Verify
DESC USER MCP_USER;
-- Should show RSA_PUBLIC_KEY_FP (fingerprint)
```

**3. Configure MCP Server**

Update `.env`:
```bash
SNOWFLAKE_ACCOUNT=xy12345.us-east-1.aws
SNOWFLAKE_USER=MCP_USER
# Remove or comment out SNOWFLAKE_PASSWORD
# SNOWFLAKE_PASSWORD=

# Add private key path
SNOWFLAKE_PRIVATE_KEY_PATH=/path/to/rsa_key.p8
# Or use private key passphrase if key is encrypted
# SNOWFLAKE_PRIVATE_KEY_PASSPHRASE=your_passphrase

SNOWFLAKE_WAREHOUSE=COMPUTE_WH
SNOWFLAKE_DATABASE=DENTAL_ERP_DW
SNOWFLAKE_SCHEMA=PUBLIC
SNOWFLAKE_ROLE=MCP_ROLE
```

**4. Update Snowflake Connector (already supported)**

Our connector already supports key-pair authentication. It will automatically detect if `SNOWFLAKE_PRIVATE_KEY_PATH` is set and use key-pair auth instead of password.

**5. Test**
```bash
./test-snowflake.sh
```

### Code Changes Required

Update `mcp-server/src/core/config.py`:

```python
class Settings(BaseSettings):
    # ... existing fields ...

    snowflake_private_key_path: Optional[str] = None
    snowflake_private_key_passphrase: Optional[str] = None
```

Update `mcp-server/src/connectors/snowflake.py` in `get_connection()`:

```python
async def get_connection(self):
    if not self.is_enabled:
        return None

    if self._connection is None:
        try:
            import snowflake.connector

            logger.info("Initializing Snowflake connection...")

            # Build connection parameters
            conn_params = {
                'account': settings.snowflake_account,
                'user': settings.snowflake_user,
                'warehouse': settings.snowflake_warehouse,
                'database': settings.snowflake_database,
                'schema': settings.snowflake_schema or 'PUBLIC',
                'role': settings.snowflake_role,
                'client_session_keep_alive': True,
                'network_timeout': 30,
                'autocommit': True,
            }

            # Use key-pair authentication if private key is provided
            if settings.snowflake_private_key_path:
                from cryptography.hazmat.backends import default_backend
                from cryptography.hazmat.primitives import serialization

                logger.info("Using key-pair authentication")

                with open(settings.snowflake_private_key_path, 'rb') as key_file:
                    if settings.snowflake_private_key_passphrase:
                        password = settings.snowflake_private_key_passphrase.encode()
                    else:
                        password = None

                    private_key = serialization.load_pem_private_key(
                        key_file.read(),
                        password=password,
                        backend=default_backend()
                    )

                    pkb = private_key.private_bytes(
                        encoding=serialization.Encoding.DER,
                        format=serialization.PrivateFormat.PKCS8,
                        encryption_algorithm=serialization.NoEncryption()
                    )

                    conn_params['private_key'] = pkb
            else:
                # Use username/password authentication
                logger.info("Using username/password authentication")
                conn_params['password'] = settings.snowflake_password

            self._connection = snowflake.connector.connect(**conn_params)

            logger.info(f"✅ Snowflake connected: {settings.snowflake_database}")

        except Exception as e:
            logger.error(f"Failed to connect to Snowflake: {e}")
            self._is_enabled = False
            return None

    return self._connection
```

### Security Best Practices

✅ **Store private key securely**:
- Use environment variables or secrets manager
- Set file permissions: `chmod 600 rsa_key.p8`
- Never commit private keys to git

✅ **Rotate keys regularly**:
```sql
-- Add new key (allows dual-key period)
ALTER USER MCP_USER SET RSA_PUBLIC_KEY_2='NEW_PUBLIC_KEY';

-- After confirming new key works, remove old
ALTER USER MCP_USER UNSET RSA_PUBLIC_KEY;
ALTER USER MCP_USER SET RSA_PUBLIC_KEY=RSA_PUBLIC_KEY_2;
ALTER USER MCP_USER UNSET RSA_PUBLIC_KEY_2;
```

✅ **Use encrypted keys for interactive use**:
```bash
# Generate encrypted private key
openssl genrsa 2048 | openssl pkcs8 -topk8 -inform PEM -out rsa_key_encrypted.p8
# Will prompt for passphrase
```

---

## 🏢 Method 3: OAuth (Enterprise)

### When to Use
- You have an OAuth provider (Okta, Azure AD, etc.)
- Need centralized identity management
- Want SSO integration

### Setup Overview

1. **Configure OAuth in Snowflake**
   ```sql
   CREATE SECURITY INTEGRATION oauth_integration
   TYPE = EXTERNAL_OAUTH
   ENABLED = TRUE
   EXTERNAL_OAUTH_TYPE = OKTA
   EXTERNAL_OAUTH_ISSUER = 'https://your-okta-domain.okta.com'
   EXTERNAL_OAUTH_TOKEN_USER_MAPPING_CLAIM = 'sub'
   EXTERNAL_OAUTH_SNOWFLAKE_USER_MAPPING_ATTRIBUTE = 'LOGIN_NAME';
   ```

2. **Get OAuth Token**
   - Implement OAuth flow in your application
   - Exchange for access token

3. **Use Token with Connector**
   ```python
   conn = snowflake.connector.connect(
       account='xy12345',
       token='oauth_access_token',
       authenticator='oauth'
   )
   ```

**Note**: Full OAuth setup is complex. See Snowflake OAuth documentation for details.

---

## 🎫 Method 4: Programmatic Access Tokens (Newest)

### When to Use
- Snowflake 2024+ features available
- Want simpler alternative to key-pair auth
- Service account automation

### Setup

1. **Create PAT in Snowflake UI**
   - Account Settings → Security → Tokens
   - Create new token
   - Copy token secret (shown once)

2. **Configure MCP**
   ```bash
   SNOWFLAKE_ACCOUNT=xy12345.us-east-1.aws
   SNOWFLAKE_PAT_TOKEN=snowflake_pat_xxx...
   ```

3. **Use with Connector**
   ```python
   conn = snowflake.connector.connect(
       account='xy12345',
       token='snowflake_pat_xxx...',
       authenticator='snowflake_jwt'
   )
   ```

---

## 📊 Recommended Setup by Environment

| Environment | Recommended Method | Why |
|-------------|-------------------|-----|
| **Local Dev** | Username/Password | Quick, easy to reset |
| **CI/CD** | Key-Pair | No password exposure, works in pipelines |
| **Staging** | Key-Pair or PAT | Secure, automated |
| **Production** | Key-Pair | Most secure, industry standard |
| **Enterprise** | OAuth + Key-Pair | Centralized auth + automation |

---

## 🔒 Security Checklist

- [ ] Use key-pair authentication for production
- [ ] Store private keys in secrets manager (AWS Secrets Manager, HashiCorp Vault)
- [ ] Set minimal role permissions (not ACCOUNTADMIN)
- [ ] Enable MFA for interactive users
- [ ] Rotate keys every 90 days
- [ ] Use encrypted private keys with passphrases
- [ ] Monitor authentication logs
- [ ] Set up network policies to restrict IP access
- [ ] Never commit credentials to git
- [ ] Use separate credentials per environment

---

## 🧪 Testing Different Auth Methods

```bash
# Test username/password
SNOWFLAKE_PASSWORD=xxx ./test-snowflake.sh

# Test key-pair
SNOWFLAKE_PRIVATE_KEY_PATH=/path/to/key.p8 ./test-snowflake.sh

# Test with encrypted key
SNOWFLAKE_PRIVATE_KEY_PATH=/path/to/key.p8 \
SNOWFLAKE_PRIVATE_KEY_PASSPHRASE=xxx \
./test-snowflake.sh
```

---

## 📚 Additional Resources

- **Snowflake Key-Pair Auth**: https://docs.snowflake.com/en/user-guide/key-pair-auth
- **Snowflake OAuth**: https://docs.snowflake.com/en/user-guide/oauth
- **Python Connector**: https://docs.snowflake.com/en/developer-guide/python-connector/python-connector
- **Security Best Practices**: https://docs.snowflake.com/en/user-guide/security

---

## 💡 Quick Decision Guide

**"Which auth method should I use?"**

```
Are you just getting started?
├─ YES → Use Username/Password (5 min setup)
└─ NO → Continue...

Is this for production?
├─ YES → Use Key-Pair Authentication (10 min setup)
└─ NO → Continue...

Do you have enterprise OAuth?
├─ YES → Use OAuth (complex setup)
└─ NO → Use Key-Pair Authentication
```

---

**Current Implementation Status**:
- ✅ Username/Password: Fully working
- ⚠️ Key-Pair: Code changes needed (see above)
- ❌ OAuth: Not implemented
- ❌ PAT: Not implemented

**Recommendation**: Start with username/password for testing, migrate to key-pair for production.

---

**Last Updated**: October 29, 2025
**Snowflake Connector Version**: 3.6.0
