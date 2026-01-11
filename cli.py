# cli.py
import sys
import click
import getpass
from datetime import datetime

# Color codes for terminal
class Colors:
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    BLUE = '\033[94m'
    MAGENTA = '\033[95m'
    CYAN = '\033[96m'
    WHITE = '\033[97m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'
    END = '\033[0m'

def print_header(text):
    print(f"\n{Colors.BOLD}{Colors.CYAN}{'='*60}{Colors.END}")
    print(f"{Colors.BOLD}{Colors.CYAN}{text.center(60)}{Colors.END}")
    print(f"{Colors.BOLD}{Colors.CYAN}{'='*60}{Colors.END}\n")

def print_success(text):
    print(f"{Colors.GREEN}✓ {text}{Colors.END}")

def print_error(text):
    print(f"{Colors.RED}✗ {text}{Colors.END}")

def print_warning(text):
    print(f"{Colors.YELLOW}⚠ {text}{Colors.END}")

def print_info(text):
    print(f"{Colors.BLUE}ℹ {text}{Colors.END}")

# আমরা app context ছাড়া কাজ করবো
def init_app():
    """Initialize Flask app context"""
    try:
        # Late import to avoid circular import
        from app import app, db
        from models import Product, Category, Vendor
        
        app.app_context().push()
        return app, db, Product, Category, Vendor
    except ImportError as e:
        print_error(f"Import error: {e}")
        print_info("Make sure you're in the project directory")
        return None, None, None, None, None
