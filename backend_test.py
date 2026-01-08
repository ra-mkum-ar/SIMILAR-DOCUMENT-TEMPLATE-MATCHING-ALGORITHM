#!/usr/bin/env python3
"""
Backend API Testing for Document Template Matching Application
Tests all CRUD operations, document matching, and AI integration
"""

import requests
import sys
import os
from datetime import datetime
import json

class DocumentMatcherAPITester:
    def __init__(self, base_url="https://docsimilarity.preview.emergentagent.com"):
        self.base_url = base_url
        self.api_url = f"{base_url}/api"
        self.tests_run = 0
        self.tests_passed = 0
        self.uploaded_templates = []
        
    def log(self, message):
        """Log test messages with timestamp"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        print(f"[{timestamp}] {message}")

    def run_test(self, name, method, endpoint, expected_status, files=None, data=None):
        """Run a single API test"""
        url = f"{self.api_url}/{endpoint}"
        headers = {}
        
        self.tests_run += 1
        self.log(f"🔍 Testing {name}...")
        
        try:
            if method == 'GET':
                response = requests.get(url, headers=headers, timeout=30)
            elif method == 'POST':
                if files:
                    response = requests.post(url, files=files, headers=headers, timeout=60)
                else:
                    headers['Content-Type'] = 'application/json'
                    response = requests.post(url, json=data, headers=headers, timeout=60)
            elif method == 'DELETE':
                response = requests.delete(url, headers=headers, timeout=30)
            
            success = response.status_code == expected_status
            if success:
                self.tests_passed += 1
                self.log(f"✅ {name} - Status: {response.status_code}")
                try:
                    return True, response.json()
                except:
                    return True, response.text
            else:
                self.log(f"❌ {name} - Expected {expected_status}, got {response.status_code}")
                self.log(f"   Response: {response.text[:200]}")
                return False, {}
                
        except Exception as e:
            self.log(f"❌ {name} - Error: {str(e)}")
            return False, {}

    def test_api_health(self):
        """Test basic API connectivity"""
        success, response = self.run_test(
            "API Health Check",
            "GET", 
            "",
            200
        )
        return success

    def test_template_upload(self, file_path, expected_status=200):
        """Test template upload functionality"""
        if not os.path.exists(file_path):
            self.log(f"❌ Test file not found: {file_path}")
            return False, {}
            
        filename = os.path.basename(file_path)
        with open(file_path, 'rb') as f:
            files = {'file': (filename, f, 'application/octet-stream')}
            success, response = self.run_test(
                f"Upload Template ({filename})",
                "POST",
                "templates/upload",
                expected_status,
                files=files
            )
            
        if success and 'template_id' in response:
            self.uploaded_templates.append({
                'id': response['template_id'],
                'name': filename
            })
            
        return success, response

    def test_get_templates(self):
        """Test getting all templates"""
        success, response = self.run_test(
            "Get All Templates",
            "GET",
            "templates",
            200
        )
        
        if success:
            self.log(f"   Found {len(response)} templates")
            
        return success, response

    def test_single_document_match(self, file_path):
        """Test single document matching"""
        if not os.path.exists(file_path):
            self.log(f"❌ Query file not found: {file_path}")
            return False, {}
            
        filename = os.path.basename(file_path)
        with open(file_path, 'rb') as f:
            files = {'file': (filename, f, 'application/octet-stream')}
            success, response = self.run_test(
                f"Single Document Match ({filename})",
                "POST",
                "match/single",
                200,
                files=files
            )
            
        if success and 'matches' in response:
            matches = response['matches']
            self.log(f"   Found {len(matches)} matches")
            if matches:
                best_match = matches[0]
                self.log(f"   Best match: {best_match['template_name']} ({best_match['overall_score']:.2f})")
                
        return success, response

    def test_batch_document_match(self, file_paths):
        """Test batch document matching"""
        files = []
        for file_path in file_paths:
            if os.path.exists(file_path):
                filename = os.path.basename(file_path)
                files.append(('files', (filename, open(file_path, 'rb'), 'application/octet-stream')))
        
        if not files:
            self.log("❌ No valid files for batch testing")
            return False, {}
            
        try:
            success, response = self.run_test(
                f"Batch Document Match ({len(files)} files)",
                "POST",
                "match/batch",
                200,
                files=files
            )
            
            if success and 'results' in response:
                results = response['results']
                successful = sum(1 for r in results if r['status'] == 'success')
                self.log(f"   Processed {len(results)} files, {successful} successful")
                
        finally:
            # Close file handles
            for _, (_, f, _) in files:
                f.close()
                
        return success, response

    def test_match_history(self):
        """Test getting match history"""
        success, response = self.run_test(
            "Get Match History",
            "GET",
            "match/history",
            200
        )
        
        if success:
            self.log(f"   Found {len(response)} history records")
            
        return success, response

    def test_template_deletion(self):
        """Test template deletion"""
        if not self.uploaded_templates:
            self.log("⚠️  No templates to delete")
            return True
            
        template = self.uploaded_templates[0]
        success, response = self.run_test(
            f"Delete Template ({template['name']})",
            "DELETE",
            f"templates/{template['id']}",
            200
        )
        
        if success:
            self.uploaded_templates.remove(template)
            
        return success

    def test_file_validation(self):
        """Test file type validation"""
        # Create a fake text file
        fake_file_path = '/tmp/fake.txt'
        with open(fake_file_path, 'w') as f:
            f.write("This is not a PDF or DOCX file")
            
        try:
            with open(fake_file_path, 'rb') as f:
                files = {'file': ('fake.txt', f, 'text/plain')}
                success, response = self.run_test(
                    "File Validation (Invalid Type)",
                    "POST",
                    "templates/upload",
                    400,  # Expecting error
                    files=files
                )
        finally:
            os.remove(fake_file_path)
            
        return success

    def test_empty_templates_scenario(self):
        """Test matching when no templates exist"""
        # First, delete all templates
        templates_response = requests.get(f"{self.api_url}/templates")
        if templates_response.status_code == 200:
            templates = templates_response.json()
            for template in templates:
                requests.delete(f"{self.api_url}/templates/{template['id']}")
        
        # Try to match a document
        query_file = '/app/test_files/query_agreement.docx'
        if os.path.exists(query_file):
            with open(query_file, 'rb') as f:
                files = {'file': ('query.docx', f, 'application/octet-stream')}
                success, response = self.run_test(
                    "Match with No Templates",
                    "POST",
                    "match/single",
                    404,  # Expecting "no templates found" error
                    files=files
                )
        else:
            self.log("⚠️  Query file not found for empty templates test")
            success = False
            
        return success

def main():
    """Main test execution"""
    tester = DocumentMatcherAPITester()
    
    print("=" * 60)
    print("🚀 DOCUMENT MATCHER API TESTING")
    print("=" * 60)
    
    # Test files
    template_files = [
        '/app/test_files/template_contract.pdf',
        '/app/test_files/template_manual.docx',
        '/app/test_files/template_research.pdf'
    ]
    
    query_files = [
        '/app/test_files/query_agreement.docx',
        '/app/test_files/query_installation.pdf'
    ]
    
    # Run tests
    test_results = []
    
    # 1. Basic API Health
    test_results.append(tester.test_api_health())
    
    # 2. File validation
    test_results.append(tester.test_file_validation())
    
    # 3. Template upload
    for template_file in template_files:
        success, _ = tester.test_template_upload(template_file)
        test_results.append(success)
    
    # 4. Get templates
    test_results.append(tester.test_get_templates()[0])
    
    # 5. Single document matching
    for query_file in query_files:
        success, _ = tester.test_single_document_match(query_file)
        test_results.append(success)
    
    # 6. Batch document matching
    test_results.append(tester.test_batch_document_match(query_files)[0])
    
    # 7. Match history
    test_results.append(tester.test_match_history()[0])
    
    # 8. Template deletion
    test_results.append(tester.test_template_deletion())
    
    # 9. Empty templates scenario
    test_results.append(tester.test_empty_templates_scenario())
    
    # Print results
    print("\n" + "=" * 60)
    print("📊 TEST RESULTS SUMMARY")
    print("=" * 60)
    print(f"Tests Run: {tester.tests_run}")
    print(f"Tests Passed: {tester.tests_passed}")
    print(f"Success Rate: {(tester.tests_passed/tester.tests_run*100):.1f}%")
    
    if tester.tests_passed == tester.tests_run:
        print("🎉 ALL TESTS PASSED!")
        return 0
    else:
        print("❌ SOME TESTS FAILED")
        return 1

if __name__ == "__main__":
    sys.exit(main())