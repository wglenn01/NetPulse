"""Backend API Testing for NetPulse Network Visibility App"""
import requests
import sys
import time
from datetime import datetime

BASE_URL = "https://dark-net-monitor.preview.emergentagent.com/api"

class NetPulseAPITester:
    def __init__(self):
        self.base_url = BASE_URL
        self.tests_run = 0
        self.tests_passed = 0
        self.tests_failed = 0
        self.failures = []
        self.test_device_id = None
        self.test_dashboard_id = None

    def log(self, msg, level="INFO"):
        print(f"[{level}] {msg}")

    def run_test(self, name, method, endpoint, expected_status=200, data=None, params=None, validate_fn=None):
        """Run a single API test with optional validation function"""
        url = f"{self.base_url}/{endpoint}"
        self.tests_run += 1
        
        try:
            if method == 'GET':
                response = requests.get(url, params=params, timeout=10)
            elif method == 'POST':
                response = requests.post(url, json=data, timeout=10)
            elif method == 'PUT':
                response = requests.put(url, json=data, timeout=10)
            elif method == 'PATCH':
                response = requests.patch(url, json=data, timeout=10)
            elif method == 'DELETE':
                response = requests.delete(url, timeout=10)
            else:
                raise ValueError(f"Unsupported method: {method}")

            status_ok = response.status_code == expected_status
            
            if not status_ok:
                self.tests_failed += 1
                msg = f"❌ FAILED: {name} - Expected {expected_status}, got {response.status_code}"
                self.log(msg, "ERROR")
                self.failures.append({"test": name, "reason": f"Status {response.status_code} != {expected_status}", "response": response.text[:200]})
                return False, None

            # Additional validation
            if validate_fn:
                try:
                    result = response.json() if response.text else {}
                    validation_result = validate_fn(result)
                    if validation_result is not True:
                        self.tests_failed += 1
                        msg = f"❌ FAILED: {name} - Validation failed: {validation_result}"
                        self.log(msg, "ERROR")
                        self.failures.append({"test": name, "reason": validation_result, "response": str(result)[:200]})
                        return False, result
                except Exception as e:
                    self.tests_failed += 1
                    msg = f"❌ FAILED: {name} - Validation error: {str(e)}"
                    self.log(msg, "ERROR")
                    self.failures.append({"test": name, "reason": f"Validation error: {str(e)}"})
                    return False, None

            self.tests_passed += 1
            self.log(f"✅ PASSED: {name}", "SUCCESS")
            return True, response.json() if response.text else {}

        except requests.exceptions.Timeout:
            self.tests_failed += 1
            msg = f"❌ FAILED: {name} - Request timeout"
            self.log(msg, "ERROR")
            self.failures.append({"test": name, "reason": "Timeout"})
            return False, None
        except Exception as e:
            self.tests_failed += 1
            msg = f"❌ FAILED: {name} - Error: {str(e)}"
            self.log(msg, "ERROR")
            self.failures.append({"test": name, "reason": str(e)})
            return False, None

    def test_overview(self):
        """Test GET /api/overview"""
        def validate(data):
            if 'counts' not in data:
                return "Missing 'counts' field"
            counts = data['counts']
            if counts.get('total') != 13:
                return f"Expected 13 total devices, got {counts.get('total')}"
            if counts.get('up') < 11:  # At least 11 should be up (12 expected, but allow some margin)
                return f"Expected at least 11 devices up, got {counts.get('up')}"
            if 'bandwidth' not in data:
                return "Missing 'bandwidth' field"
            if 'top_interfaces' not in data:
                return "Missing 'top_interfaces' field"
            if len(data['top_interfaces']) == 0:
                return "top_interfaces is empty - should have data"
            if 'recent_alerts' not in data:
                return "Missing 'recent_alerts' field"
            return True

        self.run_test("GET /api/overview", "GET", "overview", validate_fn=validate)

    def test_devices_list(self):
        """Test GET /api/devices"""
        def validate(data):
            if not isinstance(data, list):
                return "Response should be a list"
            if len(data) != 13:
                return f"Expected 13 devices, got {len(data)}"
            # Check first device has required fields
            if len(data) > 0:
                dev = data[0]
                required = ['id', 'name', 'ip', 'vendor', 'up', 'latency_ms', 'total_in_bps', 'total_out_bps', 'iface_count']
                for field in required:
                    if field not in dev:
                        return f"Device missing field: {field}"
            return True

        self.run_test("GET /api/devices", "GET", "devices", validate_fn=validate)

    def test_device_detail(self):
        """Test GET /api/devices/core-rtr-01"""
        def validate(data):
            if data.get('id') != 'core-rtr-01':
                return f"Expected device id 'core-rtr-01', got {data.get('id')}"
            if 'state' not in data:
                return "Missing 'state' field"
            state = data['state']
            if state is None:
                return "State is None - device not polled yet"
            if 'sysinfo' not in state:
                return "State missing 'sysinfo'"
            if 'interfaces' not in state:
                return "State missing 'interfaces'"
            if len(state['interfaces']) == 0:
                return "Interfaces array is empty"
            # Check that interfaces have bandwidth data
            iface = state['interfaces'][0]
            if 'in_bps' not in iface or 'out_bps' not in iface or 'util' not in iface:
                return "Interface missing bandwidth fields (in_bps, out_bps, util)"
            return True

        self.run_test("GET /api/devices/core-rtr-01", "GET", "devices/core-rtr-01", validate_fn=validate)

    def test_topology(self):
        """Test GET /api/topology - NEW: verify nodes have ports array and edges have interface details"""
        def validate(data):
            if 'nodes' not in data or 'edges' not in data:
                return "Missing 'nodes' or 'edges' field"
            if len(data['nodes']) != 13:
                return f"Expected 13 nodes, got {len(data['nodes'])}"
            if len(data['edges']) < 12:
                return f"Expected at least 12 edges, got {len(data['edges'])}"
            
            # NEW: Check that nodes have 'ports' array
            node = data['nodes'][0]
            if 'ports' not in node:
                return "Node missing 'ports' array"
            if not isinstance(node['ports'], list):
                return "Node 'ports' should be a list"
            if len(node['ports']) > 0:
                port = node['ports'][0]
                required_port_fields = ['name', 'speed_mbps', 'oper', 'util']
                for field in required_port_fields:
                    if field not in port:
                        return f"Port missing field: {field}"
            
            # NEW: Check that edges have interface details
            edge = data['edges'][0]
            required_edge_fields = ['a_ifname', 'b_ifname', 'speed_mbps', 'util', 'in_bps', 'out_bps', 'status']
            for field in required_edge_fields:
                if field not in edge:
                    return f"Edge missing field: {field}"
            
            # Check for status variety
            statuses = set(e['status'] for e in data['edges'])
            if 'active' not in statuses and 'idle' not in statuses:
                return "No 'active' or 'idle' status found in edges"
            
            return True

        self.run_test("GET /api/topology", "GET", "topology", validate_fn=validate)

    def test_device_metrics(self):
        """Test GET /api/metrics/device/core-rtr-01?minutes=30"""
        def validate(data):
            if not isinstance(data, list):
                return "Response should be a list"
            if len(data) == 0:
                return "Metrics array is empty - should have timeseries data"
            # Check first metric has required fields
            if len(data) > 0:
                m = data[0]
                required = ['device_id', 'ts', 'up', 'latency_ms', 'in_bps', 'out_bps']
                for field in required:
                    if field not in m:
                        return f"Metric missing field: {field}"
            return True

        self.run_test("GET /api/metrics/device/core-rtr-01", "GET", "metrics/device/core-rtr-01", 
                     params={'minutes': 30}, validate_fn=validate)

    def test_interface_metrics(self):
        """Test GET /api/metrics/interface/dist-sw-02?if_name=to-bh-east&minutes=30"""
        def validate(data):
            if not isinstance(data, list):
                return "Response should be a list"
            if len(data) == 0:
                return "Interface metrics array is empty - should have timeseries data"
            if len(data) > 0:
                m = data[0]
                required = ['device_id', 'if_name', 'ts', 'in_bps', 'out_bps', 'util']
                for field in required:
                    if field not in m:
                        return f"Interface metric missing field: {field}"
            return True

        self.run_test("GET /api/metrics/interface/dist-sw-02", "GET", "metrics/interface/dist-sw-02",
                     params={'if_name': 'to-bh-east', 'minutes': 30}, validate_fn=validate)

    def test_discovery_run(self):
        """Test POST /api/discovery/run"""
        def validate(data):
            if 'found' not in data:
                return "Missing 'found' field"
            # Should find edge-rtr-lab on 127.0.0.1:1612
            found = data['found']
            edge_rtr = None
            for device in found:
                if device.get('sys_name') == 'edge-rtr-lab' or 'edge-rtr-lab' in device.get('sys_descr', ''):
                    edge_rtr = device
                    break
            if not edge_rtr:
                return "Did not find 'edge-rtr-lab' in discovery results"
            if not edge_rtr.get('snmp_ok'):
                return "edge-rtr-lab snmp_ok is False"
            if edge_rtr.get('vendor') != 'mikrotik':
                return f"edge-rtr-lab vendor should be 'mikrotik', got {edge_rtr.get('vendor')}"
            return True

        self.run_test("POST /api/discovery/run", "POST", "discovery/run", 
                     data={}, validate_fn=validate)

    def test_discovery_add(self):
        """Test POST /api/discovery/add"""
        # First run discovery to get a device
        success, disco_data = self.run_test("POST /api/discovery/run (for add)", "POST", "discovery/run", data={})
        if not success or not disco_data:
            self.log("Skipping discovery/add test - discovery/run failed", "WARN")
            return

        found = disco_data.get('found', [])
        if len(found) == 0:
            self.log("Skipping discovery/add test - no devices found", "WARN")
            return

        # Find edge-rtr-lab
        edge_rtr = None
        for device in found:
            if device.get('sys_name') == 'edge-rtr-lab' or 'edge-rtr-lab' in device.get('sys_descr', ''):
                edge_rtr = device
                break

        if not edge_rtr:
            self.log("Skipping discovery/add test - edge-rtr-lab not found", "WARN")
            return

        # Add it
        add_data = {
            "devices": [{
                "ip": edge_rtr['ip'],
                "port": 1612,
                "community": "public",
                "name": "edge-rtr-lab",
                "vendor": edge_rtr.get('vendor', 'mikrotik'),
                "role": edge_rtr.get('role', 'router')
            }]
        }

        def validate(data):
            if 'added' not in data:
                return "Missing 'added' field"
            if len(data['added']) == 0:
                return "No devices were added"
            return True

        success, result = self.run_test("POST /api/discovery/add", "POST", "discovery/add", 
                                       data=add_data, validate_fn=validate)
        
        # Store the added device ID for cleanup
        if success and result and len(result.get('added', [])) > 0:
            added_id = result['added'][0].get('id')
            if added_id:
                # Clean up - delete the added device
                self.run_test("DELETE discovered device (cleanup)", "DELETE", f"devices/{added_id}", expected_status=200)

    def test_device_crud(self):
        """Test Device CRUD operations"""
        # CREATE
        create_data = {
            "name": "test-rtr",
            "ip": "10.9.9.9",
            "vendor": "mikrotik",
            "role": "router",
            "site": "Test Site",
            "community": "public",
            "snmp_port": 161
        }

        def validate_create(data):
            if 'id' not in data:
                return "Created device missing 'id'"
            if data.get('name') != 'test-rtr':
                return f"Created device name should be 'test-rtr', got {data.get('name')}"
            return True

        success, created = self.run_test("POST /api/devices (create)", "POST", "devices",
                                        data=create_data, expected_status=200, validate_fn=validate_create)
        
        if not success or not created:
            return

        device_id = created.get('id')
        self.test_device_id = device_id

        # UPDATE
        update_data = {
            "name": "test-rtr-updated",
            "site": "Updated Site"
        }

        def validate_update(data):
            if data.get('name') != 'test-rtr-updated':
                return f"Updated device name should be 'test-rtr-updated', got {data.get('name')}"
            return True

        self.run_test("PUT /api/devices/{id} (update)", "PUT", f"devices/{device_id}",
                     data=update_data, validate_fn=validate_update)

        # PATCH position
        position_data = {"x": 500.0, "y": 300.0}
        self.run_test("PATCH /api/devices/{id}/position", "PATCH", f"devices/{device_id}/position",
                     data=position_data)

        # DELETE
        self.run_test("DELETE /api/devices/{id}", "DELETE", f"devices/{device_id}")

    def test_alerts(self):
        """Test Alerts endpoints"""
        # GET alerts with state=firing
        def validate_alerts(data):
            if not isinstance(data, list):
                return "Response should be a list"
            # Check for expected alerts (device_down for ap-west-02, etc.)
            # Note: alerts may vary based on live data
            return True

        success, alerts = self.run_test("GET /api/alerts?state=firing", "GET", "alerts",
                                       params={'state': 'firing'}, validate_fn=validate_alerts)

        if success and alerts and len(alerts) > 0:
            # Try to acknowledge first alert
            alert_id = alerts[0].get('id')
            if alert_id:
                self.run_test("POST /api/alerts/{id}/ack", "POST", f"alerts/{alert_id}/ack")
                
                # Try to resolve (note: this changes alert state, but it's a test)
                # We'll skip resolve to not interfere with the demo

    def test_rules(self):
        """Test Rules endpoints"""
        def validate_rules(data):
            if not isinstance(data, list):
                return "Response should be a list"
            if len(data) != 5:
                return f"Expected 5 rules, got {len(data)}"
            return True

        success, rules = self.run_test("GET /api/rules", "GET", "rules", validate_fn=validate_rules)

        if success and rules:
            # Find high_util rule and update threshold
            high_util = None
            for rule in rules:
                if rule.get('type') == 'high_util':
                    high_util = rule
                    break

            if high_util:
                rule_id = high_util.get('id')
                update_data = {"threshold": 90}
                
                def validate_update(data):
                    if data.get('threshold') != 90:
                        return f"Updated threshold should be 90, got {data.get('threshold')}"
                    return True

                self.run_test("PUT /api/rules/{id} (update threshold)", "PUT", f"rules/{rule_id}",
                             data=update_data, validate_fn=validate_update)

    def test_settings(self):
        """Test Settings endpoints"""
        def validate_settings(data):
            if 'poll_interval' not in data:
                return "Missing 'poll_interval' field"
            return True

        success, settings = self.run_test("GET /api/settings", "GET", "settings", validate_fn=validate_settings)

        if success and settings:
            # Update poll_interval
            update_data = {"poll_interval": 8}
            self.run_test("PUT /api/settings (update poll_interval)", "PUT", "settings", data=update_data)

        # Test Discord webhook (should return 400 when no webhook configured - this is CORRECT)
        self.run_test("POST /api/settings/test-discord (no webhook)", "POST", "settings/test-discord",
                     data={}, expected_status=400)

    def test_dashboards(self):
        """Test Dashboards CRUD"""
        # GET dashboards
        def validate_dashboards(data):
            if not isinstance(data, list):
                return "Response should be a list"
            # Should have at least the default dashboard
            if len(data) == 0:
                return "No dashboards found - should have default dashboard"
            return True

        success, dashboards = self.run_test("GET /api/dashboards", "GET", "dashboards", validate_fn=validate_dashboards)

        # CREATE dashboard
        create_data = {
            "name": "Test Dashboard",
            "layout": [
                {"i": "w1", "x": 0, "y": 0, "w": 4, "h": 2, "widget": "stat", "config": {"metric": "devices_up"}}
            ],
            "is_default": False
        }

        def validate_create(data):
            if 'id' not in data:
                return "Created dashboard missing 'id'"
            if data.get('name') != 'Test Dashboard':
                return f"Created dashboard name should be 'Test Dashboard', got {data.get('name')}"
            return True

        success, created = self.run_test("POST /api/dashboards (create)", "POST", "dashboards",
                                        data=create_data, validate_fn=validate_create)

        if success and created:
            dash_id = created.get('id')
            self.test_dashboard_id = dash_id

            # UPDATE dashboard
            update_data = {
                "name": "Test Dashboard Updated",
                "layout": create_data['layout'],
                "is_default": False
            }

            def validate_update(data):
                if data.get('name') != 'Test Dashboard Updated':
                    return f"Updated dashboard name should be 'Test Dashboard Updated', got {data.get('name')}"
                return True

            self.run_test("PUT /api/dashboards/{id} (update)", "PUT", f"dashboards/{dash_id}",
                         data=update_data, validate_fn=validate_update)

            # DELETE dashboard
            self.run_test("DELETE /api/dashboards/{id}", "DELETE", f"dashboards/{dash_id}")

    def test_links_crud(self):
        """Test Links CRUD - NEW feature"""
        # GET links
        def validate_links(data):
            if not isinstance(data, list):
                return "Response should be a list"
            # Should have demo links
            if len(data) < 12:
                return f"Expected at least 12 demo links, got {len(data)}"
            return True

        success, links = self.run_test("GET /api/links", "GET", "links", validate_fn=validate_links)

        # CREATE link
        create_data = {
            "a_device": "core-rtr-01",
            "a_ifname": "ether1",
            "b_device": "dist-sw-01",
            "b_ifname": "ether1",
            "label": "Test Link"
        }

        def validate_create(data):
            if 'id' not in data:
                return "Created link missing 'id'"
            if data.get('a_device') != 'core-rtr-01':
                return f"Created link a_device should be 'core-rtr-01', got {data.get('a_device')}"
            if data.get('label') != 'Test Link':
                return f"Created link label should be 'Test Link', got {data.get('label')}"
            return True

        success, created = self.run_test("POST /api/links (create)", "POST", "links",
                                        data=create_data, validate_fn=validate_create)

        if success and created:
            link_id = created.get('id')
            
            # DELETE link (cleanup)
            self.run_test("DELETE /api/links/{id}", "DELETE", f"links/{link_id}")

    def test_vendor_config(self):
        """Test Vendor Config endpoints - NEW feature"""
        # GET vendor-config
        def validate_config(data):
            if 'mikrotik' not in data:
                return "Missing 'mikrotik' block"
            if 'unifi' not in data:
                return "Missing 'unifi' block"
            if 'cambium' not in data:
                return "Missing 'cambium' block"
            
            # Check mikrotik defaults
            mt = data['mikrotik']
            if mt.get('port') != 8728:
                return f"MikroTik default port should be 8728, got {mt.get('port')}"
            
            # Check unifi defaults
            uf = data['unifi']
            if uf.get('port') != 443:
                return f"UniFi default port should be 443, got {uf.get('port')}"
            
            return True

        success, config = self.run_test("GET /api/vendor-config", "GET", "vendor-config", validate_fn=validate_config)

        if success and config:
            # PUT vendor-config (partial update)
            update_data = {
                "mikrotik": {
                    "host": "192.168.1.1",
                    "username": "admin"
                }
            }

            def validate_update(data):
                if data['mikrotik'].get('host') != '192.168.1.1':
                    return f"MikroTik host should be '192.168.1.1', got {data['mikrotik'].get('host')}"
                # Check that other fields are preserved
                if data['mikrotik'].get('port') != 8728:
                    return "MikroTik port should be preserved (8728)"
                if 'unifi' not in data:
                    return "UniFi block should be preserved"
                return True

            self.run_test("PUT /api/vendor-config (partial update)", "PUT", "vendor-config",
                         data=update_data, validate_fn=validate_update)

    def test_vendor_config_test(self):
        """Test Vendor Config test endpoint - NEW feature"""
        # Test MikroTik
        def validate_mikrotik(data):
            if not data.get('ok'):
                return "Test should return ok:true"
            if not data.get('simulated'):
                return "Test should return simulated:true (preview mode)"
            if 'message' not in data:
                return "Missing 'message' field"
            return True

        self.run_test("POST /api/vendor-config/test (mikrotik)", "POST", "vendor-config/test",
                     data={"vendor": "mikrotik"}, validate_fn=validate_mikrotik)

        # Test UniFi
        self.run_test("POST /api/vendor-config/test (unifi)", "POST", "vendor-config/test",
                     data={"vendor": "unifi"}, validate_fn=validate_mikrotik)

        # Test Cambium
        self.run_test("POST /api/vendor-config/test (cambium)", "POST", "vendor-config/test",
                     data={"vendor": "cambium"}, validate_fn=validate_mikrotik)

        # Test invalid vendor (should return 400)
        self.run_test("POST /api/vendor-config/test (invalid vendor)", "POST", "vendor-config/test",
                     data={"vendor": "invalid"}, expected_status=400)

    def test_device_enrichment(self):
        """Test Device Enrichment endpoint - NEW feature"""
        # Test MikroTik device (core-rtr-01)
        def validate_mikrotik(data):
            if data.get('vendor') != 'mikrotik':
                return f"Expected vendor 'mikrotik', got {data.get('vendor')}"
            if not data.get('available'):
                return "Enrichment should be available for MikroTik"
            if not data.get('simulated'):
                return "Enrichment should be simulated (preview mode)"
            if 'sections' not in data:
                return "Missing 'sections' field"
            if len(data['sections']) == 0:
                return "Sections array is empty"
            # Check first section has expected structure
            section = data['sections'][0]
            if 'title' not in section or 'type' not in section:
                return "Section missing 'title' or 'type'"
            return True

        self.run_test("GET /api/devices/core-rtr-01/enrichment (MikroTik)", "GET", 
                     "devices/core-rtr-01/enrichment", validate_fn=validate_mikrotik)

        # Test Ubiquiti device (ap-north-01)
        def validate_ubiquiti(data):
            if data.get('vendor') != 'ubiquiti':
                return f"Expected vendor 'ubiquiti', got {data.get('vendor')}"
            if not data.get('available'):
                return "Enrichment should be available for Ubiquiti"
            if not data.get('simulated'):
                return "Enrichment should be simulated (preview mode)"
            if 'sections' not in data:
                return "Missing 'sections' field"
            return True

        self.run_test("GET /api/devices/ap-north-01/enrichment (Ubiquiti)", "GET",
                     "devices/ap-north-01/enrichment", validate_fn=validate_ubiquiti)

        # Test Cambium device (ap-east-01)
        def validate_cambium(data):
            if data.get('vendor') != 'cambium':
                return f"Expected vendor 'cambium', got {data.get('vendor')}"
            if not data.get('available'):
                return "Enrichment should be available for Cambium"
            if not data.get('simulated'):
                return "Enrichment should be simulated (preview mode)"
            if 'sections' not in data:
                return "Missing 'sections' field"
            return True

        self.run_test("GET /api/devices/ap-east-01/enrichment (Cambium)", "GET",
                     "devices/ap-east-01/enrichment", validate_fn=validate_cambium)

        # Test Mimosa device (bh-ridge-01) - should return available:false
        def validate_mimosa(data):
            if data.get('vendor') != 'mimosa':
                return f"Expected vendor 'mimosa', got {data.get('vendor')}"
            if data.get('available'):
                return "Enrichment should NOT be available for Mimosa"
            if 'reason' not in data:
                return "Missing 'reason' field for unavailable enrichment"
            return True

        self.run_test("GET /api/devices/bh-ridge-01/enrichment (Mimosa - unavailable)", "GET",
                     "devices/bh-ridge-01/enrichment", validate_fn=validate_mimosa)

    def run_all_tests(self):
        """Run all backend tests"""
        self.log("=" * 80)
        self.log("Starting NetPulse Backend API Tests")
        self.log("=" * 80)
        
        # Wait a bit for the poller to collect some data
        self.log("Waiting 5 seconds for poller to collect initial data...")
        time.sleep(5)

        self.log("\n--- Testing Core Endpoints ---")
        self.test_overview()
        self.test_devices_list()
        self.test_device_detail()
        self.test_topology()

        self.log("\n--- Testing Metrics ---")
        self.test_device_metrics()
        self.test_interface_metrics()

        self.log("\n--- Testing Discovery ---")
        self.test_discovery_run()
        self.test_discovery_add()

        self.log("\n--- Testing Device CRUD ---")
        self.test_device_crud()

        self.log("\n--- Testing Alerts ---")
        self.test_alerts()

        self.log("\n--- Testing Rules ---")
        self.test_rules()

        self.log("\n--- Testing Settings ---")
        self.test_settings()

        self.log("\n--- Testing Dashboards ---")
        self.test_dashboards()

        self.log("\n--- Testing NEW Features: Links CRUD ---")
        self.test_links_crud()

        self.log("\n--- Testing NEW Features: Vendor Config ---")
        self.test_vendor_config()
        self.test_vendor_config_test()

        self.log("\n--- Testing NEW Features: Device Enrichment ---")
        self.test_device_enrichment()

        self.log("\n" + "=" * 80)
        self.log(f"Tests Complete: {self.tests_passed}/{self.tests_run} passed, {self.tests_failed} failed")
        self.log("=" * 80)

        if self.failures:
            self.log("\n❌ FAILED TESTS:")
            for f in self.failures:
                self.log(f"  - {f['test']}: {f['reason']}")

        return 0 if self.tests_failed == 0 else 1

def main():
    tester = NetPulseAPITester()
    return tester.run_all_tests()

if __name__ == "__main__":
    sys.exit(main())
