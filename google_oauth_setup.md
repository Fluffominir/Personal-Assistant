
# Google OAuth Setup Instructions

## Step 1: Google Cloud Console Setup

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select an existing one
3. Enable the required APIs:
   - Go to "APIs & Services" → "Library"
   - Search for and enable:
     - Google Calendar API
     - Gmail API
     - Google Drive API

## Step 2: Create OAuth 2.0 Credentials

1. Go to "APIs & Services" → "Credentials"
2. Click "Create Credentials" → "OAuth 2.0 Client IDs"
3. If prompted, configure the OAuth consent screen:
   - Choose "External" for user type
   - Fill in app name, user support email, and developer contact
   - Add scopes: calendar, gmail.readonly, drive.readonly
4. For Application type, select "Web application"
5. Add Authorized redirect URIs:
   - `https://your-repl-name.your-username.repl.co/auth/google/callback`
   - Replace with your actual Replit URL
6. Click "Create"
7. Copy the Client ID and Client Secret

## Step 3: Configure Replit Secrets

Add these secrets to your Replit project:

```
GOOGLE_CLIENT_ID=your_client_id_here
GOOGLE_CLIENT_SECRET=your_client_secret_here
GOOGLE_REDIRECT_URI=https://your-repl-name.your-username.repl.co/auth/google/callback
```

## Step 4: Test the Integration

1. Start your Replit app
2. Visit `/auth/google` to begin OAuth flow
3. Grant permissions to your app
4. You should be redirected back with authentication success
5. Test calendar and email endpoints:
   - `/calendar/today` - Today's events
   - `/calendar/week` - This week's events
   - `/email/priority` - Important emails

## Troubleshooting

- **"redirect_uri_mismatch" error**: Make sure your redirect URI in Google Console exactly matches your Replit URL
- **"unauthorized_client" error**: Check that your client ID and secret are correct
- **API not enabled**: Make sure you've enabled the Calendar and Gmail APIs in Google Cloud Console
- **Scope errors**: Verify you've added the correct scopes in the OAuth consent screen

## Security Notes

- Keep your client secret private
- Only request the minimum scopes you need
- Consider implementing user-specific token storage for production use
