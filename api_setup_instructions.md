
# Step-by-Step Setup Instructions for Michael's AI Assistant

## 1. Required API Keys and Secrets

You need to set up the following in your Replit Secrets:

### Essential (Required for basic functionality):
- `OPENAI_API_KEY` - Get from https://platform.openai.com/api-keys
- `PINECONE_API_KEY` - Get from https://www.pinecone.io/

### Google Services (Calendar, Gmail, Drive):
- `GOOGLE_CLIENT_ID` - From Google Cloud Console
- `GOOGLE_CLIENT_SECRET` - From Google Cloud Console

### Notion Integration:
- `NOTION_WORKSPACES` - JSON containing your workspace tokens
- `SYNC_INTERVAL_MIN` - How often to sync Notion (default: 240 minutes)

### Business Tools:
- `DUBSADO_API_KEY` - From your Dubsado account
- `QUICKBOOKS_CLIENT_ID` - From QuickBooks Developer
- `SLACK_BOT_TOKEN` - From Slack App settings
- `ZOOM_API_KEY` - From Zoom Marketplace

## 2. Notion Setup (Comprehensive Access)

### Step 1: Create Notion Integration
1. Go to https://www.notion.so/my-integrations
2. Click "New integration"
3. Name it "Michael's AI Assistant"
4. Select your workspace
5. Copy the "Internal Integration Token"

### Step 2: Grant Access to All Pages
For EACH workspace you want the AI to access:
1. Go to any page in that workspace
2. Click "..." menu → "Add connections"
3. Select your "Michael's AI Assistant" integration
4. Choose "All pages in this workspace"

### Step 3: Configure NOTION_WORKSPACES Secret
In Replit Secrets, add `NOTION_WORKSPACES` with this format:
```json
{
  "personal": {
    "token": "secret_XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX"
  },
  "business": {
    "token": "secret_YYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYY"
  }
}
```

## 3. Google Services Setup (Calendar, Gmail, Drive)

### Step 1: Google Cloud Console Setup
1. Go to https://console.cloud.google.com/
2. Create a new project or select existing
3. Enable APIs:
   - Google Calendar API
   - Gmail API
   - Google Drive API

### Step 2: Create OAuth Credentials
1. Go to "Credentials" → "Create Credentials" → "OAuth 2.0 Client IDs"
2. Application type: "Web application"
3. Authorized redirect URIs: `https://your-repl-url.replit.dev/auth/google/callback`
4. Copy Client ID and Client Secret to Replit Secrets

### Step 3: Complete OAuth Flow
1. Visit `/auth/google` on your running app
2. Complete Google authorization
3. The app will store your refresh token automatically

## 4. Business Tools Integration

### Dubsado (CRM/Project Management):
1. Login to Dubsado → Settings → Integrations → API
2. Generate API key
3. Add `DUBSADO_API_KEY` to secrets

### QuickBooks (Accounting):
1. Go to https://developer.intuit.com/
2. Create app → Get production keys
3. Add `QUICKBOOKS_CLIENT_ID` and `QUICKBOOKS_CLIENT_SECRET`

### Slack (Team Communication):
1. Go to https://api.slack.com/apps
2. Create new app → Bot Token Scopes:
   - `channels:read`
   - `chat:write`
   - `users:read`
3. Install app to workspace
4. Add `SLACK_BOT_TOKEN` to secrets

### Zoom (Meetings):
1. Go to https://marketplace.zoom.us/
2. Develop → Build App → Server-to-Server OAuth
3. Add scopes: `meeting:read`, `user:read`
4. Add credentials to secrets

## 5. Data Upload for Personal Knowledge

### PDF Documents:
1. Create folder `data/raw/` in your Replit
2. Upload PDFs with your personal information:
   - Resume/CV
   - Business plans
   - SOPs (Standard Operating Procedures)
   - Project documentation
   - Personal notes/journals
3. Run `python ingest.py` to process and embed documents

### What to Include:
- **Personal**: Life story, relationships, goals, preferences, health data
- **Business**: Company info, client list, processes, financial summaries
- **Projects**: Past work, portfolios, case studies
- **Procedures**: How you do things, templates, checklists

## 6. Synology NAS Integration (Manual Setup)

### Requirements:
- Synology NAS with DSM 7.0+
- File Station API enabled
- Shared folders configured

### Setup:
1. NAS Control Panel → File Services → SMB → Advanced → Enable SMB service
2. Create dedicated user for API access
3. Add network credentials to secrets:
   - `SYNOLOGY_HOST`
   - `SYNOLOGY_USERNAME`
   - `SYNOLOGY_PASSWORD`

## 7. Testing Your Setup

### Check System Status:
1. Visit your app URL
2. Check the "System Status" panel
3. All items should show ✓

### Test Knowledge Base:
1. Ask: "What do you know about me?"
2. Ask: "What's my schedule today?"
3. Ask: "Show me my recent Notion pages"

### Verify Integrations:
1. Go to `/integrations` endpoint
2. All connected services should show "Connected: true"

## 8. Maintenance & Monitoring

### Regular Tasks:
- Add new PDFs to `data/raw/` and re-run ingest
- Update API tokens when they expire
- Monitor sync logs for Notion updates

### Troubleshooting:
- Check Replit logs for error messages
- Verify all secrets are properly set
- Test individual API endpoints manually

## 9. Privacy & Security Notes

- All data stays in your Replit environment
- API tokens are encrypted in Replit Secrets
- Pinecone embeddings are anonymous vectors
- Consider setting up 2FA on all connected accounts

## 10. Next Steps After Setup

Once everything is configured, your AI will automatically:
- Sync Notion workspaces every 4 hours
- Learn from all your uploaded documents
- Access your calendar and email when needed
- Help organize your business and personal life

Ask questions like:
- "What are my priorities this week?"
- "Help me plan my day"
- "What projects need attention?"
- "Draft an email to [client]"
- "What did I learn from [project]?"
