#!/usr/bin/env python3
"""
Comprehensive Feature Test Suite
Tests all implemented features in the AI Vision Assistant system
"""

import sqlite3
import json
from datetime import datetime, timedelta
from pathlib import Path
import sys

class FeatureTester:
    def __init__(self):
        self.db_path = 'activities.db'
        self.passed = 0
        self.failed = 0
        self.warnings = 0

    def test(self, name, condition, error_msg=""):
        """Test a condition and track results"""
        if condition:
            print(f"✅ {name}")
            self.passed += 1
            return True
        else:
            print(f"❌ {name}")
            if error_msg:
                print(f"   Error: {error_msg}")
            self.failed += 1
            return False

    def warn(self, name, condition, warning_msg=""):
        """Warn if condition is not met but don't fail"""
        if not condition:
            print(f"⚠️  {name}")
            if warning_msg:
                print(f"   Warning: {warning_msg}")
            self.warnings += 1
        else:
            print(f"✅ {name}")
            self.passed += 1

    def section(self, title):
        """Print section header"""
        print(f"\n{'='*60}")
        print(f"{title}")
        print('='*60)

    def test_database_schema(self):
        """Test that all required database tables exist"""
        self.section("1. DATABASE SCHEMA")

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        required_tables = [
            'activities', 'users', 'sessions', 'access_logs', 'camera_settings',
            'persons', 'tracked_objects', 'object_detections', 'camera_status',
            'cost_settings', 'user_settings', 'user_streaks', 'voice_queries'
        ]

        existing_tables = [row[0] for row in cursor.execute(
            "SELECT name FROM sqlite_master WHERE type='table'"
        ).fetchall()]

        for table in required_tables:
            self.test(f"Table '{table}' exists", table in existing_tables)

        # Check activities table columns
        columns = [row[1] for row in cursor.execute('PRAGMA table_info(activities)').fetchall()]
        required_columns = ['category', 'person_name', 'duration_minutes', 'tokens_used',
                          'category_confidence', 'person_id']

        for col in required_columns:
            self.test(f"Activities column '{col}' exists", col in columns)

        conn.close()

    def test_config_files(self):
        """Test that required configuration files exist"""
        self.section("2. CONFIGURATION FILES")

        config_files = [
            ('config.example.json', False),
            ('.env.example', False),
            ('config.json', True),  # Should exist for operation
        ]

        for file_path, required in config_files:
            exists = Path(file_path).exists()
            if required:
                self.test(f"Config file '{file_path}' exists", exists)
            else:
                self.warn(f"Example file '{file_path}' exists", exists,
                         "Users should copy this to create actual config")

    def test_core_modules(self):
        """Test that core Python modules are importable"""
        self.section("3. CORE MODULES")

        modules = [
            ('src.core.database_setup', 'Database Setup'),
            ('src.core.camera_manager', 'Camera Manager'),
            ('src.core.activity_detector', 'Activity Detector'),
            ('src.core.voice_assistant', 'Voice Assistant'),
            ('src.core.categorize_activities', 'Activity Categorization'),
            ('src.core.calculate_durations', 'Duration Calculation'),
        ]

        for module_path, name in modules:
            try:
                __import__(module_path.replace('/', '.'))
                self.test(f"Module '{name}' is importable", True)
            except Exception as e:
                self.test(f"Module '{name}' is importable", False, str(e))

    def test_api_server(self):
        """Test that API server module is valid"""
        self.section("4. API SERVER")

        try:
            sys.path.insert(0, str(Path.cwd()))
            from src.web.dashboard import app

            self.test("Dashboard module imports successfully", True)

            # Check that routes are registered
            routes = [rule.rule for rule in app.url_map.iter_rules()]

            required_routes = [
                '/api/auth/login',
                '/api/auth/logout',
                '/api/activities',
                '/api/statistics',
                '/api/timeline',
                '/api/cost/today',
                '/api/cost/settings',
                '/api/cameras/status',
                '/api/voice/query',
            ]

            for route in required_routes:
                self.test(f"Route '{route}' registered", route in routes)

        except Exception as e:
            self.test("Dashboard module imports successfully", False, str(e))

    def test_activity_categorization(self):
        """Test activity categorization system"""
        self.section("5. ACTIVITY CATEGORIZATION")

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Check if categorization columns exist
        columns = [row[1] for row in cursor.execute('PRAGMA table_info(activities)').fetchall()]
        self.test("Category column exists", 'category' in columns)
        self.test("Category confidence column exists", 'category_confidence' in columns)

        # Check if cost_settings has default values
        settings = cursor.execute('SELECT * FROM cost_settings WHERE id = 1').fetchone()
        self.test("Cost settings initialized", settings is not None)

        if settings:
            self.test("Daily cap is set", settings[1] > 0)
            self.test("Notification threshold is set", settings[2] > 0)

        conn.close()

    def test_duration_tracking(self):
        """Test activity duration tracking"""
        self.section("6. DURATION TRACKING")

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        columns = [row[1] for row in cursor.execute('PRAGMA table_info(activities)').fetchall()]
        self.test("Duration_minutes column exists", 'duration_minutes' in columns)

        # Check if calculate_durations module exists
        self.test("Duration calculation script exists",
                 Path('src/core/calculate_durations.py').exists())

        conn.close()

    def test_camera_status_tracking(self):
        """Test camera status tracking system"""
        self.section("7. CAMERA STATUS TRACKING")

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Check table structure
        columns = [row[1] for row in cursor.execute('PRAGMA table_info(camera_status)').fetchall()]

        required_columns = ['camera_name', 'is_connected', 'last_successful_connection',
                          'consecutive_failures', 'error_message']

        for col in required_columns:
            self.test(f"Camera status has '{col}' column", col in columns)

        conn.close()

    def test_cost_monitoring(self):
        """Test cost monitoring system"""
        self.section("8. COST MONITORING")

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Check cost_settings table
        columns = [row[1] for row in cursor.execute('PRAGMA table_info(cost_settings)').fetchall()]

        required_columns = ['daily_cap', 'notification_threshold', 'warning_sent_today',
                          'last_reset_date']

        for col in required_columns:
            self.test(f"Cost settings has '{col}' column", col in columns)

        # Check if activities track cost
        act_columns = [row[1] for row in cursor.execute('PRAGMA table_info(activities)').fetchall()]
        self.test("Activities track cost", 'cost' in act_columns)
        self.test("Activities track tokens", 'tokens_used' in act_columns)

        conn.close()

    def test_voice_queries(self):
        """Test voice query system"""
        self.section("9. VOICE QUERY SYSTEM")

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Check voice_queries table
        columns = [row[1] for row in cursor.execute('PRAGMA table_info(voice_queries)').fetchall()]

        required_columns = ['query_text', 'response_text', 'tokens_used', 'cost',
                          'execution_time_ms']

        for col in required_columns:
            self.test(f"Voice queries has '{col}' column", col in columns)

        conn.close()

    def test_person_tracking(self):
        """Test person tracking system"""
        self.section("10. PERSON TRACKING")

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Check persons table
        columns = [row[1] for row in cursor.execute('PRAGMA table_info(persons)').fetchall()]

        required_columns = ['name', 'description', 'created_at', 'last_seen', 'is_active']

        for col in required_columns:
            self.test(f"Persons table has '{col}' column", col in columns)

        # Check activities link to persons
        act_columns = [row[1] for row in cursor.execute('PRAGMA table_info(activities)').fetchall()]
        self.test("Activities have person_name column", 'person_name' in act_columns)
        self.test("Activities have person_id column", 'person_id' in act_columns)

        conn.close()

    def test_object_tracking(self):
        """Test object tracking system"""
        self.section("11. OBJECT TRACKING")

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Check tracked_objects table
        columns = [row[1] for row in cursor.execute('PRAGMA table_info(tracked_objects)').fetchall()]

        required_columns = ['name', 'category', 'last_seen_location', 'status',
                          'last_seen_timestamp']

        for col in required_columns:
            self.test(f"Tracked objects has '{col}' column", col in columns)

        # Check object_detections table
        det_columns = [row[1] for row in cursor.execute('PRAGMA table_info(object_detections)').fetchall()]

        detection_columns = ['object_id', 'camera_name', 'timestamp', 'confidence',
                           'bbox_x', 'bbox_y']

        for col in detection_columns:
            self.test(f"Object detections has '{col}' column", col in det_columns)

        conn.close()

    def test_authentication_system(self):
        """Test authentication and user management"""
        self.section("12. AUTHENTICATION & SECURITY")

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Check users table
        users_count = cursor.execute('SELECT COUNT(*) FROM users').fetchone()[0]
        self.test("Default admin user created", users_count > 0)

        # Check sessions table
        columns = [row[1] for row in cursor.execute('PRAGMA table_info(sessions)').fetchall()]
        required_columns = ['user_id', 'session_token', 'expires_at']

        for col in required_columns:
            self.test(f"Sessions table has '{col}' column", col in columns)

        # Check access_logs table
        self.test("Access logs table exists",
                 'access_logs' in [row[0] for row in cursor.execute(
                     "SELECT name FROM sqlite_master WHERE type='table'"
                 ).fetchall()])

        conn.close()

    def test_indexes(self):
        """Test database indexes for performance"""
        self.section("13. DATABASE INDEXES")

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        indexes = [row[1] for row in cursor.execute(
            "SELECT * FROM sqlite_master WHERE type='index'"
        ).fetchall()]

        required_indexes = [
            'idx_activities_timestamp',
            'idx_activities_camera',
            'idx_activities_category',
            'idx_sessions_token',
        ]

        for idx in required_indexes:
            self.test(f"Index '{idx}' exists", idx in indexes)

        conn.close()

    def test_file_structure(self):
        """Test that required files and directories exist"""
        self.section("14. FILE STRUCTURE")

        required_paths = [
            ('src/core', True, 'Core modules directory'),
            ('src/web', True, 'Web API directory'),
            ('src/core/camera_manager.py', True, 'Camera manager'),
            ('src/core/activity_detector.py', True, 'Activity detector'),
            ('src/core/database_setup.py', True, 'Database setup'),
            ('src/web/dashboard.py', True, 'API server'),
            ('start.py', True, 'System launcher'),
            ('README.md', True, 'Documentation'),
            ('requirements.txt', True, 'Dependencies'),
            ('frames', False, 'Frames directory (created on first run)'),
        ]

        for path, required, description in required_paths:
            exists = Path(path).exists()
            if required:
                self.test(f"{description} exists", exists)
            else:
                self.warn(f"{description} exists", exists,
                         "Will be created automatically")

    def run_all_tests(self):
        """Run all tests and print summary"""
        print("\n" + "="*60)
        print("🧪 AI VISION ASSISTANT - COMPREHENSIVE FEATURE TEST")
        print("="*60)

        self.test_database_schema()
        self.test_config_files()
        self.test_core_modules()
        self.test_api_server()
        self.test_activity_categorization()
        self.test_duration_tracking()
        self.test_camera_status_tracking()
        self.test_cost_monitoring()
        self.test_voice_queries()
        self.test_person_tracking()
        self.test_object_tracking()
        self.test_authentication_system()
        self.test_indexes()
        self.test_file_structure()

        # Print summary
        print("\n" + "="*60)
        print("TEST SUMMARY")
        print("="*60)
        total = self.passed + self.failed
        print(f"✅ Passed:   {self.passed}/{total}")
        print(f"❌ Failed:   {self.failed}/{total}")
        print(f"⚠️  Warnings: {self.warnings}")

        if self.failed == 0:
            print("\n🎉 All tests passed! System is ready.")
            return 0
        else:
            print(f"\n⚠️  {self.failed} test(s) failed. Please review above.")
            return 1

def main():
    tester = FeatureTester()
    return tester.run_all_tests()

if __name__ == '__main__':
    sys.exit(main())
