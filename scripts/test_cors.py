# Test CORS validation in production mode
import os
os.environ['DEBUG'] = 'False'
os.environ['BACKEND_CORS_ORIGINS'] = '["*"]'

from src.config import settings

try:
    settings.validate_production_config()
    print('❌ FAIL: Should reject wildcard')
except ValueError as e:
    print(f'✅ PASS: Wildcard rejected - {e}')
