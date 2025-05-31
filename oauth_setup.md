
# OAuth Setup Instructions for Michael's AI Assistant

## Google Workspace (Gmail, Calendar, Drive)

### 1. Create Google Cloud Project
1. Go to [Google Cloud Console](https://console.cloud.google.com)
2. Create new project: "Michael's AI Assistant"
3. Enable these APIs:
   - Gmail API
   - Google Calendar API  
   - Google Drive API

### 2. Create OAuth Credentials
1. Go to "Credentials" → "Create Credentials" → "OAuth 2.0 Client ID"
2. Application type: "Web application"
3. Authorized redirect URIs: 
   - `https://your-repl-name.your-username.repl.co/auth/google/callback`
   - `http://localhost:5000/auth/google/callback`

### 3. Configure Consent Screen
1. Go to "OAuth consent screen"
2. User Type: External
3. Add your email as test user
4. Scopes: Add Gmail, Calendar, Drive scopes

### 4. Add to Replit Secrets
```
GOOGLE_CLIENT_ID=your_client_id_here
GOOGLE_CLIENT_SECRET=your_client_secret_here
```

## Notion Integration

### 1. Create Notion Integration
1. Go to [notion.so/my-integrations](https://notion.so/my-integrations)
2. Create "New integration"
3. Name: "Michael's AI Assistant"
4. Copy the "Internal Integration Token"

### 2. Share Databases
1. Go to each Notion database you want to access
2. Click "Share" → Search for your integration
3. Add with "Can edit" permissions

### 3. Add to Replit Secrets
```
NOTION_API_KEY=secret_your_token_here
```

## Dubsado Integration

### 1. Get API Key
1. Login to Dubsado
2. Go to Settings → API
3. Generate new API key
4. Note your subdomain (yourname.dubsado.com)

### 2. Add to Replit Secrets
```
DUBSADO_API_KEY=your_api_key_here
DUBSADO_SUBDOMAIN=yourname
```

## QuickBooks Integration

### 1. Create Intuit App
1. Go to [developer.intuit.com](https://developer.intuit.com)
2. Create new app for QuickBooks Online
3. Get Client ID and Secret

### 2. Add to Replit Secrets
```
QUICKBOOKS_CLIENT_ID=your_client_id
QUICKBOOKS_CLIENT_SECRET=your_client_secret
```

## Slack Integration

### 1. Create Slack App
1. Go to [api.slack.com/apps](https://api.slack.com/apps)
2. Create new app for your workspace
3. Add bot scopes: chat:write, channels:read, users:read

### 2. Add to Replit Secrets
```
SLACK_BOT_TOKEN=xoxb-your-bot-token
SLACK_SIGNING_SECRET=your_signing_secret
```

## Next Steps After Setup

1. Run the OAuth flows to get access tokens
2. Test each integration through the dashboard
3. Configure automation workflows
4. Set up daily/weekly reports

## Security Notes

- Never share these tokens publicly
- Regularly rotate API keys
- Use least-privilege access for each integration
- Monitor usage through each platform's dashboard
