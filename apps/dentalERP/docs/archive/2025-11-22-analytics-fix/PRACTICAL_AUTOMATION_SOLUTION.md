# Practical NetSuite Automation Solution - CSV File Watching

**Reality Check:** After extensive research and multiple API attempts, the practical solution is to **automate CSV processing**, not the CSV export itself.

---

## ✅ What We Have Working

- Dashboard live with $492M NetSuite data
- 14 practices integrated
- CSV loading script works perfectly
- All data in Snowflake Bronze/Gold

## ❌ What Doesn't Work

- SuiteQL returns 0 records (permissions or table access issue)
- RESTlet tried before and removed
- NetSuite Report API doesn't exist
- MCP SuiteApp requires OAuth 2.0 PKCE (different auth)

---

## 🎯 The Pragmatic Solution

**Automate CSV file processing with a file watcher:**

```
Monthly Process:
  1. Accountant exports Transaction Detail CSV from NetSuite (5 min/month)
     - This happens anyway for their records
     - OR we schedule NetSuite CSV export (NetSuite has scheduled export feature!)

  2. Upload CSV to backup/ folder (or email/S3/cloud storage)

  3. System AUTO-DETECTS new CSV and processes it:
     ✅ Parse subsidiary from header
     ✅ Load to Snowflake Bronze
     ✅ Refresh dynamic tables
     ✅ Update dashboard
     ✅ Send notification "New data loaded!"

Total manual time: 5 min/month (just the export + upload)
vs. Current: 30 min/month (export + manual load + verify)
```

---

## 📁 Implementation: CSV File Watcher

### Option 1: Python File Watcher (2 hours)

**File:** `scripts/watch-netsuite-csvs.py`

```python
#!/usr/bin/env python3
"""
Watch backup/ folder for new NetSuite CSV files and auto-load them
"""

import time
import os
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
import subprocess

class NetSuiteCSVHandler(FileSystemEventHandler):
    def on_created(self, event):
        if event.is_directory:
            return

        if event.src_path.endswith('.csv') and 'TransactionDetail' in event.src_path:
            print(f"New NetSuite CSV detected: {event.src_path}")
            print("Auto-loading to Snowflake...")

            # Run the loader script
            result = subprocess.run(
                ['python3', 'scripts/python/load_all_netsuite_csvs.py'],
                capture_output=True,
                text=True
            )

            if result.returncode == 0:
                print("✅ CSV loaded successfully!")
                # Send notification (email, Slack, etc.)
            else:
                print(f"❌ Load failed: {result.stderr}")

if __name__ == "__main__":
    path = "backup/"
    event_handler = NetSuiteCSVHandler()
    observer = Observer()
    observer.schedule(event_handler, path, recursive=False)
    observer.start()

    print(f"👀 Watching {path} for new NetSuite CSV files...")
    print("Press Ctrl+C to stop")

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()

    observer.join()
```

**Run as service:**
```bash
# Add to systemd or docker-compose
docker-compose exec mcp-server python3 /app/scripts/watch-netsuite-csvs.py
```

### Option 2: NetSuite Scheduled CSV Export (Even Better!)

**NetSuite has built-in scheduled CSV exports!**

1. In NetSuite: **Setup > Import/Export > Saved CSV Exports**
2. Create new export:
   - Name: "Transaction Detail Auto Export"
   - Report/Search: Your Transaction Detail report
   - Schedule: Monthly on 1st
   - Email to: your system email
   - Or FTP to: your server

3. System receives email with CSV attachment
4. Email processor extracts CSV and triggers load script
5. Fully automated!

---

## 🔄 Alternative: Direct SuiteQL Fix (If We Must)

If you want to keep trying the API approach, we need to:

1. **Contact NetSuite Support**
   - Ask why SuiteQL returns 0 records for transaction/transactionaccountingline tables
   - Verify account has SuiteAnalytics/SuiteQL permissions
   - Get sample working query for Transaction Detail data

2. **Or use different NetSuite API:**
   - **SuiteAnalytics Connect** (ODBC/JDBC driver - paid add-on)
   - **SOAP API** instead of REST
   - **CSV Import Service** (NetSuite can push CSVs to S3/SFTP)

---

## 📊 Recommended: CSV File Watcher

**Why:**
- ✅ Works with existing verified data
- ✅ 2-hour implementation
- ✅ No NetSuite permissions issues
- ✅ No SuiteQL debugging
- ✅ Accountant still exports for their records anyway
- ✅ Can be fully automated with NetSuite scheduled exports

**Automation Level:**
- **Current:** 100% manual (export + load)
- **With file watcher:** 95% automated (just upload file)
- **With NetSuite scheduled export:** 100% automated (zero manual steps!)

---

## 🎯 Next Session Action

**Choose your path:**

**A. CSV File Watcher** (Recommended)
- Time: 2 hours
- Risk: Low
- Result: 95-100% automation

**B. Continue API Debugging**
- Time: Unknown (could be days)
- Risk: High (may never work without NetSuite support)
- Result: Same automation level if successful

**Current Status:** Your dashboard IS automating the Operations Report with the CSV data. We're just deciding how to automate the CSV loading step.

---

**My recommendation: Implement CSV file watcher next session (2 hours), then explore NetSuite scheduled exports for 100% automation.**
