# 🔧 Troubleshooting Guide

## Common Issues & Solutions

### 📁 1. File Upload Issues

#### Issue: "File is not valid CSV"

**Cause:** File encoding not UTF-8
**Solution:**

1. Open file in Excel
2. Save As → CSV UTF-8 (.csv)
3. Try uploading again

#### Issue: "Tên file không hợp lệ"

**Cause:** File name doesn't match format
**Current:** `2600_20251231.csv`
**Should be:** `2600_dp01_20251231.csv`
**Solution:**

- Rename file: Add `_dp01_` between branch code and date

#### Issue: "Thiếu file ở 1 bên"

**Cause:** T1 and T2 don't have same branch codes
**Example:**

- T1 has: `2600_dp01_20251231.csv`, `2602_dp01_20251231.csv`
- T2 has: `2600_dp01_20260228.csv` (missing 2602)
  **Solution:**
- Ensure both T1 and T2 have files for all branches

---

### 📊 2. Data Processing Issues

#### Issue: No data appears after processing

**Cause:** All data filtered out by DP_TYPE exclusion
**Solution:**

1. Check if all records have DP_TYPE = "401" or "101"
2. Modify EXCLUDE_DP_TYPES in `config.py` if needed
3. Re-run processing

#### Issue: Huge DELTA values (missing data?)

**Cause:** Missing balance in T1 or T2 causes 0 fill
**Solution:**

1. Check for empty values in CURRENT_BALANCE
2. Fill zeros before export
3. Verify source data completeness

#### Issue: Outliers show normal values

**Cause:** IQR threshold too high
**Solution:**
In `config.py`, reduce `IQR_MULTIPLIER`:

```python
IQR_MULTIPLIER = 1.0  # More sensitive (was 1.5)
```

---

### 💾 3. Excel Export Issues

#### Issue: "❌ Lỗi xuất báo cáo"

**Cause:** Insufficient disk space or file locked
**Solution:**

1. Close any open Excel files
2. Free up disk space (>100MB)
3. Check write permissions to directory
4. Try again

#### Issue: Excel file opens but is blank

**Cause:** Export process incomplete
**Solution:**

1. Use latest openpyxl: `pip install --upgrade openpyxl`
2. Try exporting smaller dataset first
3. Check available memory

#### Issue: Numbers show as ##### in Excel

**Cause:** Column too narrow for formatted numbers
**Solution:** Auto-width is set, but if still occurs:

1. Open Excel file
2. Select all (Ctrl+A)
3. Format → Column → Auto Fit

---

### 🖥️ 4. Streamlit UI Issues

#### Issue: "ModuleNotFoundError: No module named 'streamlit'"

**Cause:** Virtual environment not activated or packages not installed
**Solution:**

```bash
# Activate venv
venv\Scripts\activate        # Windows
source venv/bin/activate      # macOS/Linux

# Install packages
pip install -r requirements.txt

# Run again
streamlit run app.py
```

#### Issue: App crashes after clicking "Xử Lý Đối Chiếu"

**Cause:** Corrupted CSV or too large dataset
**Solution:**

1. Check CSV file with Excel first
2. Reduce number of records (test with <1000)
3. Look at Streamlit console for error details
4. Report error message

#### Issue: Page is very slow to load

**Cause:** Large dataset or slow computer
**Solution:**

1. Filter data first in "Chi Tiết Khách Hàng" tab
2. Reduce number of charts shown
3. Try on faster computer
4. Split into smaller branches

#### Issue: Can't see all columns in table

**Cause:** Table too wide for screen
**Solution:**

1. Streamlit adjusts automatically
2. Scroll right to see more columns
3. Use Excel export for full view
4. Try zooming out browser (Ctrl+- or Cmd+-)

---

### 🔐 5. Data Validation Issues

#### Issue: "Tất cả file trong T1 phải có cùng yyyymmdd"

**Cause:** Files have different dates
**Example:** T1 has `20251231` and `20260101`
**Solution:**

- Use files from same date only
- In file manager, sort by date
- Verify all T1 files end with same 8 digits

#### Issue: "Mã chi nhánh không khớp"

**Missing branches in T1:**

- T2 has: 2600, 2602, 2604
- T1 has: 2600, 2602 (missing 2604)
  **Solution:**
- Find missing `2604_dp01_*.csv` file for T1
- Add it to upload

#### Issue: "File thiếu cột MA_KH"

**Cause:** CSV missing required column
**Solution:**

1. Open file in Excel
2. Check headers - should be exactly:
   - MA_KH, TEN_KH, DP_TYPE, CURRENT_BALANCE, CUST_TYPE_NAME
3. Rename columns if needed
4. Save and re-upload

---

### 📈 6. Chart Issues

#### Issue: Charts not showing

**Cause:** Data may be empty or malformed
**Solution:**

1. Download Excel to verify data exists
2. Check "Chi Tiết Khách Hàng" tab first
3. Ensure filters include data

#### Issue: Chart shows wrong colors

**Cause:** Browser theme or plotly version
**Solution:**

1. Refresh browser (F5)
2. Update plotly: `pip install --upgrade plotly`
3. Clear browser cache (Ctrl+Shift+Delete)

---

### 🔍 7. Data Quality Issues

#### Issue: Negative balances or suspicious values

**Cause:** Source data quality
**Solution:**

1. Check tab "Bất Thường" for anomalies
2. Review source CSV files
3. Contact data source owner
4. Filter in Excel before uploading

#### Issue: Customer appears in T2 but not T1

**Result:** Classified as MO_MOI (new customer)
**Is this correct?** Yes, new customers are normal
**If not intended:**

- Check T1 file includes this customer
- Verify correct date range files

#### Issue: Same customer different MA_KH

**Cause:** Data inconsistency
**Solution:**

- Contact data team to reconcile
- Filter duplicates before upload if possible

---

### 🔄 8. Process Issues

#### Issue: Processing takes very long

**Cause:** Large dataset or slow computer
**What's normal?**

- 1,000 customers: <5 seconds
- 10,000 customers: <30 seconds
- 100,000+ customers: 1-5 minutes

**Solution:**

1. Close other applications
2. Check Task Manager (CPU, RAM)
3. Reduce dataset size for testing
4. May need more powerful server

#### Issue: Session resets/data disappears

**Cause:** Browser tab refresh or inactivity
**Streamlit Behavior:** This is normal
**Solution:**

1. Always download Excel export
2. Keep browser tab open
3. Don't refresh during processing
4. Fastest: Process → Export immediately

---

### 🆘 9. Emergency Solutions

#### "Nothing works!" - Full Reset

```bash
# 1. Kill all Python processes
# Windows: Ctrl+Shift+Esc → Python → End Task
# macOS: Activity Monitor → Python → Force Quit
# Linux: pkill python

# 2. Clear Streamlit cache
rm -rf .streamlit/
del .streamlit\           # Windows

# 3. Reinstall everything
pip uninstall -r requirements.txt -y
pip install -r requirements.txt

# 4. Try again
streamlit run app.py
```

#### Database/File Corruption

```bash
# Delete temp files
rm -rf temp/
rm -rf __pycache__/
del temp\            # Windows
del __pycache__\     # Windows

# Reinstall packages
pip install --upgrade --force-reinstall -r requirements.txt
```

---

### 📞 10. Getting Help

**Where to look:**

1. **README.md** - General documentation
2. **QUICKSTART.md** - Setup & basic usage
3. **config.py** - Settings explanation
4. **Streamlit console** - Error messages
5. This file - Troubleshooting guide

**What to include when reporting:**

1. Error message (exact text)
2. Your file format (names, structure)
3. File size (number of records)
4. Python version: `python --version`
5. Streamlit version: `streamlit --version`
6. Operating system (Windows/Mac/Linux)

**Quick Debug:**
Run this to verify setup:

```bash
python -c "import pandas, streamlit, plotly; print('✅ All packages OK')"
```

---

## Performance Tips

### Speed Up Processing

1. ✅ Close other applications
2. ✅ Use SSD for file storage
3. ✅ Split large datasets into multiple runs
4. ✅ Disable unnecessary charts

### Optimize Files

1. ✅ Clean data before uploading
2. ✅ Remove extra columns
3. ✅ Use consistent formatting
4. ✅ Compress if >500MB

### Browser Optimization

1. ✅ Clear cache monthly
2. ✅ Close unused tabs
3. ✅ Use Chrome/Edge (better than Firefox)
4. ✅ Disable auto-refresh

---

**Last Updated:** 2024  
**Status:** Complete

If issue not resolved, verify:

- [ ] Virtual environment activated
- [ ] All packages installed
- [ ] File format correct
- [ ] Data complete
- [ ] Browser cache cleared
- [ ] Disk space available
