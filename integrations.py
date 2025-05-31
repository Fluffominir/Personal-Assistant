
import os
import json
import requests
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional

class IntegrationManager:
    """Manages all external integrations for Michael's AI Assistant"""
    
    def __init__(self):
        self.google_token = os.environ.get("GOOGLE_ACCESS_TOKEN")
        self.notion_token = os.environ.get("NOTION_API_KEY")
        self.dubsado_token = os.environ.get("DUBSADO_API_KEY")
        self.slack_token = os.environ.get("SLACK_BOT_TOKEN")
        
    def get_calendar_events(self, days_ahead: int = 7) -> List[Dict]:
        """Get upcoming calendar events"""
        if not self.google_token:
            return []
            
        headers = {"Authorization": f"Bearer {self.google_token}"}
        now = datetime.utcnow()
        time_min = now.isoformat() + 'Z'
        time_max = (now + timedelta(days=days_ahead)).isoformat() + 'Z'
        
        url = "https://www.googleapis.com/calendar/v3/calendars/primary/events"
        params = {
            'timeMin': time_min,
            'timeMax': time_max,
            'singleEvents': True,
            'orderBy': 'startTime',
            'maxResults': 20
        }
        
        try:
            response = requests.get(url, headers=headers, params=params)
            if response.status_code == 200:
                events = response.json().get('items', [])
                return [
                    {
                        'title': event.get('summary', 'No title'),
                        'start': event['start'].get('dateTime', event['start'].get('date')),
                        'end': event['end'].get('dateTime', event['end'].get('date')),
                        'description': event.get('description', ''),
                        'location': event.get('location', ''),
                        'attendees': [att.get('email') for att in event.get('attendees', [])]
                    }
                    for event in events
                ]
        except Exception as e:
            print(f"Error fetching calendar: {e}")
            
        return []
    
    def get_important_emails(self, max_results: int = 10) -> List[Dict]:
        """Get important/unread emails"""
        if not self.google_token:
            return []
            
        headers = {"Authorization": f"Bearer {self.google_token}"}
        
        # First get message IDs
        url = "https://www.googleapis.com/gmail/v1/users/me/messages"
        params = {
            'q': 'is:unread OR is:important OR from:client',
            'maxResults': max_results
        }
        
        try:
            response = requests.get(url, headers=headers, params=params)
            if response.status_code == 200:
                messages = response.json().get('messages', [])
                emails = []
                
                for msg in messages[:5]:  # Limit to avoid API overuse
                    msg_url = f"https://www.googleapis.com/gmail/v1/users/me/messages/{msg['id']}"
                    msg_response = requests.get(msg_url, headers=headers)
                    
                    if msg_response.status_code == 200:
                        msg_data = msg_response.json()
                        payload = msg_data.get('payload', {})
                        headers_list = payload.get('headers', [])
                        
                        sender = next((h['value'] for h in headers_list if h['name'] == 'From'), 'Unknown')
                        subject = next((h['value'] for h in headers_list if h['name'] == 'Subject'), 'No subject')
                        
                        emails.append({
                            'sender': sender,
                            'subject': subject,
                            'snippet': msg_data.get('snippet', ''),
                            'labels': msg_data.get('labelIds', []),
                            'id': msg['id']
                        })
                
                return emails
        except Exception as e:
            print(f"Error fetching emails: {e}")
            
        return []
    
    def get_notion_pages(self, database_id: str) -> List[Dict]:
        """Get pages from a Notion database"""
        if not self.notion_token:
            return []
            
        headers = {
            "Authorization": f"Bearer {self.notion_token}",
            "Content-Type": "application/json",
            "Notion-Version": "2022-06-28"
        }
        
        url = f"https://api.notion.com/v1/databases/{database_id}/query"
        
        try:
            response = requests.post(url, headers=headers, json={})
            if response.status_code == 200:
                return response.json().get('results', [])
        except Exception as e:
            print(f"Error fetching Notion data: {e}")
            
        return []
    
    def send_slack_message(self, channel: str, message: str) -> bool:
        """Send a message to Slack"""
        if not self.slack_token:
            return False
            
        headers = {
            "Authorization": f"Bearer {self.slack_token}",
            "Content-Type": "application/json"
        }
        
        data = {
            "channel": channel,
            "text": message
        }
        
        try:
            response = requests.post(
                "https://slack.com/api/chat.postMessage",
                headers=headers,
                json=data
            )
            return response.status_code == 200
        except Exception as e:
            print(f"Error sending Slack message: {e}")
            return False
    
    def create_calendar_event(self, title: str, start_time: str, end_time: str, description: str = "") -> bool:
        """Create a new calendar event"""
        if not self.google_token:
            return False
            
        headers = {
            "Authorization": f"Bearer {self.google_token}",
            "Content-Type": "application/json"
        }
        
        event_data = {
            'summary': title,
            'description': description,
            'start': {'dateTime': start_time, 'timeZone': 'America/Los_Angeles'},
            'end': {'dateTime': end_time, 'timeZone': 'America/Los_Angeles'}
        }
        
        try:
            response = requests.post(
                "https://www.googleapis.com/calendar/v3/calendars/primary/events",
                headers=headers,
                json=event_data
            )
            return response.status_code == 200
        except Exception as e:
            print(f"Error creating calendar event: {e}")
            return False
    
    def get_system_summary(self) -> Dict[str, Any]:
        """Get a comprehensive summary of all systems"""
        summary = {
            'calendar_events': self.get_calendar_events(3),  # Next 3 days
            'important_emails': self.get_important_emails(5),  # Top 5 emails
            'integrations_status': {
                'google': bool(self.google_token),
                'notion': bool(self.notion_token),
                'dubsado': bool(self.dubsado_token),
                'slack': bool(self.slack_token)
            },
            'timestamp': datetime.now().isoformat()
        }
        
        return summary

# Global instance
integration_manager = IntegrationManager()
