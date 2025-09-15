#!/usr/bin/env python3
"""
QBO OAuth Token Management
Replaces the Google Apps Script functionality for getting and refreshing QBO tokens
"""

import os
import requests
import base64
import json
from dotenv import load_dotenv
from utils.logger import logger

# Load environment variables
load_dotenv()

class QBOOAuth:
    """QuickBooks Online OAuth token management"""
    
    def __init__(self):
        self.client_id = os.getenv('QBO_CLIENT_ID')
        self.client_secret = os.getenv('QBO_CLIENT_SECRET')
        self.company_id = os.getenv('QBO_COMPANY_ID')
        self.redirect_uri = "https://developer.intuit.com/v2/OAuth2Playground/RedirectUrl"
        
        if not all([self.client_id, self.client_secret, self.company_id]):
            raise ValueError("Missing QBO credentials in .env file")
    
    def get_authorization_url(self):
        """Get the authorization URL for OAuth flow"""
        auth_url = (
            f"https://appcenter.intuit.com/connect/oauth2?"
            f"client_id={self.client_id}&"
            f"response_type=code&"
            f"scope=com.intuit.quickbooks.accounting&"
            f"redirect_uri={self.redirect_uri}&"
            f"state=test"
        )
        return auth_url
    
    def exchange_code_for_tokens(self, authorization_code):
        """Exchange authorization code for access and refresh tokens"""
        token_url = "https://oauth.platform.intuit.com/oauth2/v1/tokens/bearer"
        
        # Create basic auth header
        credentials = f"{self.client_id}:{self.client_secret}"
        encoded_credentials = base64.b64encode(credentials.encode()).decode()
        
        headers = {
            "Authorization": f"Basic {encoded_credentials}",
            "Content-Type": "application/x-www-form-urlencoded"
        }
        
        data = {
            "grant_type": "authorization_code",
            "code": authorization_code,
            "redirect_uri": self.redirect_uri
        }
        
        logger.info("Exchanging authorization code for tokens...")
        response = requests.post(token_url, headers=headers, data=data)
        
        if response.status_code == 200:
            result = response.json()
            access_token = result.get('access_token')
            refresh_token = result.get('refresh_token')
            expires_in = result.get('expires_in', 3600)
            
            logger.info("✅ Successfully obtained tokens!")
            logger.info(f"Access Token: {access_token[:20]}...")
            logger.info(f"Refresh Token: {refresh_token[:20]}...")
            logger.info(f"Token expires in: {expires_in} seconds")
            
            # Save tokens to .env file
            self._save_tokens_to_env(access_token, refresh_token)
            
            return {
                'access_token': access_token,
                'refresh_token': refresh_token,
                'expires_in': expires_in
            }
        else:
            logger.error(f"❌ Failed to get tokens: {response.status_code} - {response.text}")
            return None
    
    def refresh_access_token(self, refresh_token=None):
        """Refresh the access token using refresh token"""
        if not refresh_token:
            refresh_token = os.getenv('QBO_REFRESH_TOKEN')
        
        if not refresh_token:
            logger.error("❌ No refresh token available")
            return None
        
        token_url = "https://oauth.platform.intuit.com/oauth2/v1/tokens/bearer"
        
        # Create basic auth header
        credentials = f"{self.client_id}:{self.client_secret}"
        encoded_credentials = base64.b64encode(credentials.encode()).decode()
        
        headers = {
            "Authorization": f"Basic {encoded_credentials}",
            "Content-Type": "application/x-www-form-urlencoded"
        }
        
        data = {
            "grant_type": "refresh_token",
            "refresh_token": refresh_token
        }
        
        logger.info("Refreshing access token...")
        response = requests.post(token_url, headers=headers, data=data)
        
        if response.status_code == 200:
            result = response.json()
            access_token = result.get('access_token')
            new_refresh_token = result.get('refresh_token', refresh_token)  # Use new refresh token if provided
            
            logger.info("✅ Successfully refreshed access token")
            
            # Save updated tokens to .env file
            self._save_tokens_to_env(access_token, new_refresh_token)
            
            return {
                'access_token': access_token,
                'refresh_token': new_refresh_token,
                'expires_in': result.get('expires_in', 3600)
            }
        else:
            logger.error(f"❌ Failed to refresh token: {response.status_code} - {response.text}")
            return None
    
    def get_valid_access_token(self):
        """Get a valid access token (refresh if needed)"""
        current_token = os.getenv('QBO_ACCESS_TOKEN')
        if current_token:
            return current_token
        
        # Try to refresh if we have a refresh token
        return self.refresh_access_token()
    
    def _save_tokens_to_env(self, access_token, refresh_token):
        """Save tokens to .env file"""
        try:
            # Read current .env file
            env_path = '.env'
            if os.path.exists(env_path):
                with open(env_path, 'r') as f:
                    lines = f.readlines()
            else:
                lines = []
            
            # Update or add token lines
            token_lines = {
                'QBO_ACCESS_TOKEN': access_token,
                'QBO_REFRESH_TOKEN': refresh_token
            }
            
            # Update existing lines or add new ones
            updated_lines = []
            found_keys = set()
            
            for line in lines:
                line_stripped = line.strip()
                if '=' in line_stripped:
                    key = line_stripped.split('=')[0].strip()
                    if key in token_lines:
                        updated_lines.append(f"{key}={token_lines[key]}\n")
                        found_keys.add(key)
                    else:
                        updated_lines.append(line)
                else:
                    updated_lines.append(line)
            
            # Add any missing keys
            for key, value in token_lines.items():
                if key not in found_keys:
                    updated_lines.append(f"{key}={value}\n")
            
            # Write back to file
            with open(env_path, 'w') as f:
                f.writelines(updated_lines)
            
            logger.info("✅ Updated tokens in .env file")
            
        except Exception as e:
            logger.error(f"Failed to save tokens to .env: {e}")

def main():
    """Main function for command line usage"""
    import sys
    
    if len(sys.argv) < 2:
        print("Usage:")
        print("  python qbo_oauth.py auth-url                    # Get authorization URL")
        print("  python qbo_oauth.py exchange <auth_code>        # Exchange code for tokens")
        print("  python qbo_oauth.py refresh                     # Refresh access token")
        print("  python qbo_oauth.py get-token                   # Get valid access token")
        return
    
    try:
        oauth = QBOOAuth()
        
        if sys.argv[1] == "auth-url":
            url = oauth.get_authorization_url()
            print(f"\n🔗 Authorization URL:")
            print(url)
            print(f"\n📋 Steps:")
            print("1. Copy the URL above and paste it in your browser")
            print("2. Log into QuickBooks Online and authorize the app")
            print("3. You'll be redirected to the OAuth Playground")
            print("4. Copy the authorization code from the playground page")
            print("5. Run: python qbo_oauth.py exchange <auth_code>")
            
        elif sys.argv[1] == "exchange":
            if len(sys.argv) < 3:
                print("❌ Please provide authorization code")
                print("Usage: python qbo_oauth.py exchange <auth_code>")
                return
            
            auth_code = sys.argv[2]
            result = oauth.exchange_code_for_tokens(auth_code)
            if result:
                print("✅ Tokens saved to .env file")
            else:
                print("❌ Failed to get tokens")
                
        elif sys.argv[1] == "refresh":
            result = oauth.refresh_access_token()
            if result:
                print("✅ Access token refreshed and saved to .env file")
            else:
                print("❌ Failed to refresh token")
                
        elif sys.argv[1] == "get-token":
            token = oauth.get_valid_access_token()
            if token:
                print(f"✅ Valid access token: {token[:20]}...")
            else:
                print("❌ Failed to get valid access token")
                
        else:
            print(f"❌ Unknown command: {sys.argv[1]}")
            
    except Exception as e:
        logger.error(f"Error: {e}")

if __name__ == "__main__":
    main()





