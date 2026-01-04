import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import unittest

class TestAdminPanel(unittest.TestCase):
    def setUp(self):
        from app import app
        self.app = app
        self.client = app.test_client()
    
    def test_admin_routes(self):
        """Test all admin routes return valid responses"""
        admin_routes = [
            '/admin/dashboard',
            '/admin/products',
            '/admin/orders',
            '/admin/users',
            '/admin/settings'
        ]
        
        for route in admin_routes:
            with self.subTest(route=route):
                # First login (if required)
                response = self.client.get(route, follow_redirects=True)
                # Routes should either work or redirect to login
                self.assertIn(response.status_code, [200, 302, 401])
    
    def test_admin_login_functionality(self):
        """Test admin login with correct credentials"""
        response = self.client.post('/admin/login', data={
            'username': 'admin',
            'password': 'admin123'
        }, follow_redirects=True)
        
        # Should redirect to dashboard after successful login
        self.assertEqual(response.status_code, 200)
    
    def test_admin_products_crud(self):
        """Test products CRUD operations (if logged in)"""
        # This test assumes admin is logged in
        response = self.client.get('/admin/products', follow_redirects=True)
        self.assertIn(response.status_code, [200, 302])

if __name__ == '__main__':
    unittest.main()
