# Header-Based Authentication

This application now supports both OAuth and header-based authentication, allowing it to work seamlessly in environments like Databricks App mode and Azure App Service.

## Authentication Methods

### 1. OAuth Authentication (Existing)
- **Providers**: GitHub, Google, Microsoft
- **Use Case**: Public-facing applications, traditional web applications
- **Flow**: User clicks login → redirected to provider → callback with code → JWT token created

### 2. Header-Based Authentication (New)
- **Providers**: Databricks App mode, Azure App Service
- **Use Case**: Enterprise/internal deployments, platform-as-a-service environments
- **Flow**: Headers injected by platform → automatic authentication

## Configuration

Add these environment variables to your `.env` file:

```env
# Enable header-based authentication
HEADER_AUTH_ENABLED=True

# Enable specific providers
DATABRICKS_HEADER_AUTH=True
AZURE_APP_SERVICE_AUTH=True

# Trusted proxy IPs (for security)
TRUSTED_HEADER_PROXIES=127.0.0.1,::1,10.0.0.0/8
```

## Provider-Specific Configuration

### Databricks App Mode

Databricks automatically injects user information in HTTP headers:

- `X-Databricks-User-Email`: User's email address
- `X-Databricks-User-Name`: User's display name

**Setup:**
1. Set `DATABRICKS_HEADER_AUTH=True`
2. Deploy your app as a Databricks App
3. Users will be automatically authenticated when accessing the app

### Azure App Service

Azure App Service provides authentication through the `X-MS-CLIENT-PRINCIPAL` header:

- `X-MS-CLIENT-PRINCIPAL`: Base64-encoded JSON with user details

**Setup:**
1. Enable App Service Authentication in your Azure App Service
2. Set `AZURE_APP_SERVICE_AUTH=True`
3. Configure your preferred identity provider (Azure AD, Google, etc.)
4. Users will be automatically authenticated

## Authentication Flow

The application automatically tries authentication methods in this order:

1. **JWT Token from Cookie** (OAuth flow)
2. **Header-Based Authentication** (if headers present and enabled)
3. **Redirect to Login** (if no authentication found)

## Security Considerations

### Trusted Proxies
Header-based authentication only works from trusted IP addresses to prevent header spoofing. Configure `TRUSTED_HEADER_PROXIES` with your environment's IP ranges.

### Header Validation
Each provider validates the presence and format of expected headers before proceeding with authentication.

### User Creation
New users from header-based authentication are automatically created in the database with:
- Email and name from headers
- Provider set to `databricks` or `azure_app_service`
- Provider ID derived from unique identifier

## API Endpoints

### Get Current User
```http
GET /auth/providers
```
Returns available authentication providers for the current request.

### Header Login Redirect
```http
GET /auth/header-login
```
Useful for triggering header-based authentication redirect.

## Testing

You can test header authentication manually:

```bash
# Test Databricks headers
curl -H "X-Databricks-User-Email: test@example.com" \
     -H "X-Databricks-User-Name: Test User" \
     http://localhost:9999

# Test Azure App Service headers
PRINCIPAL=$(echo '{"userDetails":"azureuser@example.com","userId":"123"}' | base64)
curl -H "X-MS-CLIENT-PRINCIPAL: $PRINCIPAL" \
     http://localhost:9999
```

## Migration from OAuth-only

Existing OAuth configurations continue to work unchanged. The header-based authentication is additive - it doesn't remove any existing functionality.

### Benefits of Adding Header Auth

1. **Zero-Click Authentication**: Users are automatically logged in based on platform身份
2. **Enterprise Integration**: Seamless integration with enterprise identity systems
3. **Multiple Environments**: Same codebase works across different deployment targets
4. **Backward Compatibility**: OAuth continues to work for public-facing deployments

### Deployment Examples

**Databricks App:**
```env
HEADER_AUTH_ENABLED=True
DATABRICKS_HEADER_AUTH=True
AZURE_APP_SERVICE_AUTH=False
```

**Azure App Service:**
```env
HEADER_AUTH_ENABLED=True
DATABRICKS_HEADER_AUTH=False
AZURE_APP_SERVICE_AUTH=True
```

**Development (OAuth only):**
```env
HEADER_AUTH_ENABLED=False
DATABRICKS_HEADER_AUTH=False
AZURE_APP_SERVICE_AUTH=False
```

**Production (All methods):**
```env
HEADER_AUTH_ENABLED=True
DATABRICKS_HEADER_AUTH=True
AZURE_APP_SERVICE_AUTH=True
```

This flexibility allows your application to adapt to any deployment environment while maintaining a consistent authentication experience for users.