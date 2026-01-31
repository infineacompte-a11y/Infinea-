#!/usr/bin/env python3
"""
InFinea Backend API Testing Suite
Tests all endpoints including auth, actions, AI suggestions, sessions, and payments
"""

import requests
import json
import sys
from datetime import datetime
import time

class InFineaAPITester:
    def __init__(self, base_url="https://complete-saas-2.preview.emergentagent.com"):
        self.base_url = base_url
        self.api_url = f"{base_url}/api"
        self.session_token = None
        self.user_data = None
        self.tests_run = 0
        self.tests_passed = 0
        self.test_results = []

    def log_test(self, name, success, details="", error=""):
        """Log test result"""
        self.tests_run += 1
        if success:
            self.tests_passed += 1
            print(f"✅ {name}")
        else:
            print(f"❌ {name} - {error}")
        
        self.test_results.append({
            "test": name,
            "success": success,
            "details": details,
            "error": error
        })

    def make_request(self, method, endpoint, data=None, headers=None):
        """Make HTTP request with proper headers"""
        url = f"{self.api_url}/{endpoint}"
        
        default_headers = {'Content-Type': 'application/json'}
        if self.session_token:
            default_headers['Authorization'] = f'Bearer {self.session_token}'
        
        if headers:
            default_headers.update(headers)

        try:
            if method == 'GET':
                response = requests.get(url, headers=default_headers, timeout=30)
            elif method == 'POST':
                response = requests.post(url, json=data, headers=default_headers, timeout=30)
            elif method == 'PUT':
                response = requests.put(url, json=data, headers=default_headers, timeout=30)
            elif method == 'DELETE':
                response = requests.delete(url, headers=default_headers, timeout=30)
            
            return response
        except requests.exceptions.RequestException as e:
            print(f"Request error for {method} {url}: {e}")
            return None
        except Exception as e:
            print(f"Unexpected error for {method} {url}: {e}")
            return None

    def test_root_endpoint(self):
        """Test API root endpoint"""
        response = self.make_request('GET', '')
        if response and response.status_code == 200:
            data = response.json()
            self.log_test("API Root Endpoint", True, f"Message: {data.get('message', '')}")
        else:
            self.log_test("API Root Endpoint", False, error=f"Status: {response.status_code if response else 'No response'}")

    def test_user_registration(self):
        """Test user registration"""
        timestamp = int(time.time())
        test_user = {
            "email": f"test_{timestamp}@infinea.test",
            "password": "TestPass123!",
            "name": f"Test User {timestamp}"
        }
        
        print(f"Attempting registration with: {test_user}")
        response = self.make_request('POST', 'auth/register', test_user)
        
        if response is None:
            self.log_test("User Registration", False, error="No response received")
            return False
            
        print(f"Registration response status: {response.status_code}")
        print(f"Registration response text: {response.text}")
        
        if response.status_code == 200:
            data = response.json()
            self.session_token = data.get('token')
            self.user_data = data
            self.log_test("User Registration", True, f"User ID: {data.get('user_id')}")
            return True
        else:
            try:
                error_msg = response.json().get('detail', 'Unknown error')
            except:
                error_msg = response.text
            self.log_test("User Registration", False, error=f"Status {response.status_code}: {error_msg}")
            return False

    def test_user_login(self):
        """Test user login with existing credentials"""
        if not self.user_data:
            self.log_test("User Login", False, error="No user data from registration")
            return False
            
        login_data = {
            "email": self.user_data['email'],
            "password": "TestPass123!"
        }
        
        response = self.make_request('POST', 'auth/login', login_data)
        if response and response.status_code == 200:
            data = response.json()
            self.session_token = data.get('token')
            self.log_test("User Login", True, f"Token received: {bool(self.session_token)}")
            return True
        else:
            error_msg = response.json().get('detail', 'Unknown error') if response else 'No response'
            self.log_test("User Login", False, error=error_msg)
            return False

    def test_auth_me(self):
        """Test getting current user info"""
        if not self.session_token:
            self.log_test("Auth Me", False, error="No session token")
            return False
            
        response = self.make_request('GET', 'auth/me')
        if response and response.status_code == 200:
            data = response.json()
            self.log_test("Auth Me", True, f"User: {data.get('name')}")
            return True
        else:
            error_msg = response.json().get('detail', 'Unknown error') if response else 'No response'
            self.log_test("Auth Me", False, error=error_msg)
            return False

    def test_seed_actions(self):
        """Test seeding micro-actions"""
        response = self.make_request('POST', 'admin/seed')
        if response and response.status_code == 200:
            data = response.json()
            self.log_test("Seed Actions", True, data.get('message', ''))
            return True
        else:
            error_msg = response.json().get('detail', 'Unknown error') if response else 'No response'
            self.log_test("Seed Actions", False, error=error_msg)
            return False

    def test_get_actions(self):
        """Test getting micro-actions"""
        response = self.make_request('GET', 'actions')
        if response and response.status_code == 200:
            data = response.json()
            self.log_test("Get Actions", True, f"Found {len(data)} actions")
            return data
        else:
            error_msg = response.json().get('detail', 'Unknown error') if response else 'No response'
            self.log_test("Get Actions", False, error=error_msg)
            return []

    def test_get_action_by_id(self, action_id):
        """Test getting specific action"""
        response = self.make_request('GET', f'actions/{action_id}')
        if response and response.status_code == 200:
            data = response.json()
            self.log_test("Get Action by ID", True, f"Action: {data.get('title')}")
            return True
        else:
            error_msg = response.json().get('detail', 'Unknown error') if response else 'No response'
            self.log_test("Get Action by ID", False, error=error_msg)
            return False

    def test_ai_suggestions(self):
        """Test AI suggestions endpoint"""
        if not self.session_token:
            self.log_test("AI Suggestions", False, error="No session token")
            return False
            
        suggestion_request = {
            "available_time": 5,
            "energy_level": "medium",
            "preferred_category": "learning"
        }
        
        response = self.make_request('POST', 'suggestions', suggestion_request)
        if response and response.status_code == 200:
            data = response.json()
            self.log_test("AI Suggestions", True, f"Suggestion: {data.get('suggestion', '')}")
            return data
        else:
            error_msg = response.json().get('detail', 'Unknown error') if response else 'No response'
            self.log_test("AI Suggestions", False, error=error_msg)
            return None

    def test_start_session(self, action_id):
        """Test starting a session"""
        if not self.session_token:
            self.log_test("Start Session", False, error="No session token")
            return None
            
        session_data = {"action_id": action_id}
        response = self.make_request('POST', 'sessions/start', session_data)
        if response and response.status_code == 200:
            data = response.json()
            self.log_test("Start Session", True, f"Session ID: {data.get('session_id')}")
            return data
        else:
            error_msg = response.json().get('detail', 'Unknown error') if response else 'No response'
            self.log_test("Start Session", False, error=error_msg)
            return None

    def test_complete_session(self, session_id):
        """Test completing a session"""
        if not self.session_token:
            self.log_test("Complete Session", False, error="No session token")
            return False
            
        completion_data = {
            "session_id": session_id,
            "actual_duration": 5,
            "completed": True,
            "notes": "Test session completed"
        }
        
        response = self.make_request('POST', 'sessions/complete', completion_data)
        if response and response.status_code == 200:
            data = response.json()
            self.log_test("Complete Session", True, data.get('message', ''))
            return True
        else:
            error_msg = response.json().get('detail', 'Unknown error') if response else 'No response'
            self.log_test("Complete Session", False, error=error_msg)
            return False

    def test_get_stats(self):
        """Test getting user stats"""
        if not self.session_token:
            self.log_test("Get Stats", False, error="No session token")
            return False
            
        response = self.make_request('GET', 'stats')
        if response and response.status_code == 200:
            data = response.json()
            self.log_test("Get Stats", True, f"Total time: {data.get('total_time_invested', 0)} min")
            return True
        else:
            error_msg = response.json().get('detail', 'Unknown error') if response else 'No response'
            self.log_test("Get Stats", False, error=error_msg)
            return False

    def test_stripe_checkout(self):
        """Test Stripe checkout creation"""
        if not self.session_token:
            self.log_test("Stripe Checkout", False, error="No session token")
            return False
            
        checkout_data = {"origin_url": "https://complete-saas-2.preview.emergentagent.com"}
        response = self.make_request('POST', 'payments/checkout', checkout_data)
        if response and response.status_code == 200:
            data = response.json()
            self.log_test("Stripe Checkout", True, f"Session created: {bool(data.get('session_id'))}")
            return True
        else:
            error_msg = response.json().get('detail', 'Unknown error') if response else 'No response'
            self.log_test("Stripe Checkout", False, error=error_msg)
            return False

    def test_logout(self):
        """Test user logout"""
        if not self.session_token:
            self.log_test("Logout", False, error="No session token")
            return False
            
        response = self.make_request('POST', 'auth/logout')
        if response and response.status_code == 200:
            self.session_token = None
            self.log_test("Logout", True, "Successfully logged out")
            return True
        else:
            error_msg = response.json().get('detail', 'Unknown error') if response else 'No response'
            self.log_test("Logout", False, error=error_msg)
            return False

    def run_all_tests(self):
        """Run complete test suite"""
        print("🚀 Starting InFinea Backend API Tests")
        print(f"📍 Testing: {self.base_url}")
        print("=" * 50)
        
        # Basic API tests
        self.test_root_endpoint()
        
        # Authentication flow
        if self.test_user_registration():
            self.test_auth_me()
        
        # Seed data
        self.test_seed_actions()
        
        # Actions tests
        actions = self.test_get_actions()
        if actions:
            # Test getting specific action
            self.test_get_action_by_id(actions[0]['action_id'])
            
            # AI suggestions
            self.test_ai_suggestions()
            
            # Session flow
            session_data = self.test_start_session(actions[0]['action_id'])
            if session_data:
                self.test_complete_session(session_data['session_id'])
        
        # Stats
        self.test_get_stats()
        
        # Payment
        self.test_stripe_checkout()
        
        # Logout
        self.test_logout()
        
        # Print summary
        print("\n" + "=" * 50)
        print(f"📊 Test Results: {self.tests_passed}/{self.tests_run} passed")
        print(f"✅ Success Rate: {(self.tests_passed/self.tests_run)*100:.1f}%")
        
        if self.tests_passed < self.tests_run:
            print("\n❌ Failed Tests:")
            for result in self.test_results:
                if not result['success']:
                    print(f"  - {result['test']}: {result['error']}")
        
        return self.tests_passed == self.tests_run

def main():
    tester = InFineaAPITester()
    success = tester.run_all_tests()
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())