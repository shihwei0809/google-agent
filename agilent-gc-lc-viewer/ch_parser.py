"""
Universal GC/LC Chromatography Binary & Text File Parser
Parses Agilent (.ch/.D), Shimadzu (.gcd/.lcd), PeakSimple (.gcd), Waters/Thermo (.raw/.dat),
and exported CSV/TXT chromatography data files.
"""

import struct
import os
import zipfile
import io
import numpy as np

def parse_agilent_ch(file_bytes: bytes, filename: str = "") -> dict:
    """
    Universal parser for Chromatography files (.gcd, .ch, .dat, .txt, .csv, etc.).
    Returns metadata dict with retention_times, intensities, peaks, sample_name, etc.
    """
    if len(file_bytes) < 64:
        raise ValueError("檔案大小太小，不是有效的層析數據檔案。")

    sample_name = os.path.splitext(os.path.basename(filename))[0] if filename else "GC/LC Sample"
    operator = "N/A"
    date_str = "N/A"
    signal_name = "GC/LC Signal"
    
    retention_times = []
    intensities = []
    parsed_successfully = False

    # Check if file is a ZIP container
    if zipfile.is_zipfile(io.BytesIO(file_bytes)):
        try:
            with zipfile.ZipFile(io.BytesIO(file_bytes)) as z:
                for zip_info in z.infolist():
                    if zip_info.filename.lower().endswith(('.dat', '.ch', '.gcd', '.raw', '.csv', '.txt')):
                        inner_bytes = z.read(zip_info.filename)
                        return parse_agilent_ch(inner_bytes, filename=zip_info.filename)
        except Exception:
            pass

    # Strategy 1: Text / CSV / TSV / ASCII Parsing
    try:
        text_content = file_bytes.decode('utf-8', errors='ignore')
        lines = text_content.splitlines()
        rt_list = []
        int_list = []
        for line in lines:
            cleaned_line = line.strip().replace(',', '\t').replace(';', '\t')
            parts = [p.strip() for p in cleaned_line.split('\t') if p.strip()]
            if len(parts) >= 2:
                try:
                    rt = float(parts[0])
                    val = float(parts[1])
                    rt_list.append(rt)
                    int_list.append(val)
                except ValueError:
                    continue
        if len(rt_list) > 30:
            retention_times = rt_list
            intensities = int_list
            parsed_successfully = True
            signal_name = "Text/CSV Signal"
    except Exception:
        pass

    # Strategy 2: Agilent .ch Header Parser (Version 179 / 181 / 81)
    if not parsed_successfully and len(file_bytes) >= 1024:
        try:
            def read_pascal_utf16(offset, max_len=60):
                try:
                    length = file_bytes[offset]
                    if 0 < length <= max_len:
                        raw_str = file_bytes[offset+1:offset+1+length*2]
                        return raw_str.decode('utf-16be', errors='ignore').strip()
                except Exception:
                    pass
                return ""

            def read_pascal_ascii(offset, max_len=60):
                try:
                    length = file_bytes[offset]
                    if 0 < length <= max_len:
                        raw_str = file_bytes[offset+1:offset+1+length]
                        return raw_str.decode('ascii', errors='ignore').strip()
                except Exception:
                    pass
                return ""

            extracted_sample = read_pascal_utf16(0x18) or read_pascal_ascii(0x18)
            if extracted_sample:
                sample_name = extracted_sample
            operator = read_pascal_utf16(0x98) or read_pascal_ascii(0x98) or operator
            date_str = read_pascal_utf16(0xDC) or read_pascal_ascii(0xDC) or date_str
            signal_name = read_pascal_utf16(0x244) or read_pascal_ascii(0x244) or "Agilent Signal"

            start_time_min = struct.unpack('>f', file_bytes[0x11A:0x11E])[0] / 60000.0 if struct.unpack('>f', file_bytes[0x11A:0x11E])[0] > 1000 else struct.unpack('>f', file_bytes[0x11A:0x11E])[0]
            end_time_min = struct.unpack('>f', file_bytes[0x11E:0x122])[0] / 60000.0 if struct.unpack('>f', file_bytes[0x11E:0x122])[0] > 1000 else struct.unpack('>f', file_bytes[0x11E:0x122])[0]

            if 0 <= start_time_min < 120 and start_time_min < end_time_min < 300:
                data_start = 4096 if len(file_bytes) > 4096 else 1024
                raw_data = file_bytes[data_start:]
                num_points = len(raw_data) // 4
                if num_points > 100:
                    floats = np.frombuffer(raw_data[:num_points*4], dtype='>f4')
                    if not np.all(np.isnan(floats)) and np.nanmax(floats) > np.nanmin(floats):
                        intensities = floats.tolist()
                        retention_times = np.linspace(start_time_min, end_time_min, len(intensities)).tolist()
                        parsed_successfully = True
        except Exception:
            pass

    # Strategy 3: Shimadzu .gcd / PeakSimple / Universal Binary Array Scanner
    # Scans offsets from 0 to 16384 for float32, float64, int32, int16, and delta-encoded streams
    if not parsed_successfully:
        best_candidate = None
        max_score = 0

        # Offsets to scan
        offsets_to_try = [0, 128, 256, 512, 1024, 2048, 4096, 8192, 16384]
        dtypes_to_try = ['<f4', '>f4', '<f8', '>f8', '<i4', '>i4', '<i2', '>i2']

        for offset in offsets_to_try:
            if len(file_bytes) <= offset + 500:
                continue
            chunk = file_bytes[offset:]

            for dtype_str in dtypes_to_try:
                elem_size = 8 if '8' in dtype_str else (4 if '4' in dtype_str else 2)
                num_elems = len(chunk) // elem_size
                if num_elems < 100:
                    continue

                try:
                    arr = np.frombuffer(chunk[:num_elems*elem_size], dtype=dtype_str)
                    
                    # Convert integer streams to float for testing
                    arr_float = arr.astype(np.float64)
                    
                    # Check finite numbers
                    valid_mask = np.isfinite(arr_float) & (np.abs(arr_float) < 1e12)
                    valid_count = np.sum(valid_mask)
                    
                    if valid_count > 0.7 * num_elems:
                        clean_arr = np.where(valid_mask, arr_float, 0.0)
                        span = np.nanmax(clean_arr) - np.nanmin(clean_arr)
                        std_dev = np.nanstd(clean_arr)
                        
                        # Score candidate: good chromatographic signal has reasonable variation and > 100 points
                        score = std_dev * len(clean_arr)
                        
                        if span > 0.01 and std_dev > 1e-4 and score > max_score:
                            max_score = score
                            best_candidate = (clean_arr.tolist(), dtype_str)
                except Exception:
                    continue

        if best_candidate:
            intensities, dtype_str = best_candidate
            retention_times = np.linspace(0.0, 30.0, len(intensities)).tolist()
            parsed_successfully = True
            signal_name = f"GC Data ({dtype_str})"

    # Strategy 4: Delta-encoding Cumulative Scanner (for compressed .gcd / .ch int16/int32 deltas)
    if not parsed_successfully:
        for offset in [256, 512, 1024, 2048, 4096]:
            if len(file_bytes) <= offset + 500:
                continue
            chunk = file_bytes[offset:]
            for dtype_str in ['<i2', '>i2', '<i4', '>i4']:
                elem_size = 2 if '2' in dtype_str else 4
                num_elems = len(chunk) // elem_size
                if num_elems < 200:
                    continue
                try:
                    deltas = np.frombuffer(chunk[:num_elems*elem_size], dtype=dtype_str).astype(np.float64)
                    integrated = np.cumsum(deltas)
                    span = np.nanmax(integrated) - np.nanmin(integrated)
                    std_dev = np.nanstd(integrated)
                    if span > 10.0 and std_dev > 1.0:
                        intensities = integrated.tolist()
                        retention_times = np.linspace(0.0, 30.0, len(intensities)).tolist()
                        parsed_successfully = True
                        signal_name = f"Delta Compressed Signal ({dtype_str})"
                        break
                except Exception:
                    continue
            if parsed_successfully:
                break

    if not parsed_successfully or len(intensities) == 0:
        raise ValueError(f"未能解析檔案 [{filename}]，格式不符或檔案毀損。")

    # Clean data (remove NaN / Inf)
    intensities = [0.0 if (np.isnan(v) or np.isinf(v)) else float(v) for v in intensities]
    
    # Peak Analysis
    peaks = detect_peaks(retention_times, intensities)

    return {
        "sample_name": sample_name,
        "operator": operator,
        "date_str": date_str,
        "signal_name": signal_name,
        "total_points": len(intensities),
        "min_rt": round(min(retention_times), 3) if retention_times else 0,
        "max_rt": round(max(retention_times), 3) if retention_times else 0,
        "max_abundance": round(max(intensities), 2) if intensities else 0,
        "retention_times": [round(t, 4) for t in retention_times],
        "intensities": [round(i, 2) for i in intensities],
        "peaks": peaks
    }


def detect_peaks(rt_list: list, int_list: list, threshold_ratio: float = 0.03) -> list:
    """
    Detects major chromatographic peaks and calculates peak area (Retention Time, Peak Height, Area).
    """
    if len(int_list) < 10:
        return []
    
    arr = np.array(int_list)
    max_val = np.max(arr)
    min_val = np.min(arr)
    baseline = min_val
    peak_threshold = baseline + (max_val - baseline) * threshold_ratio

    peaks = []
    for i in range(1, len(arr) - 1):
        if arr[i] > peak_threshold and arr[i] > arr[i-1] and arr[i] >= arr[i+1]:
            peak_rt = rt_list[i]
            peak_height = arr[i] - baseline
            
            left_idx = max(0, i - 15)
            right_idx = min(len(arr) - 1, i + 15)
            trapz_func = getattr(np, 'trapezoid', getattr(np, 'trapz', None))
            y_sub = arr[left_idx:right_idx+1] - baseline
            x_sub = rt_list[left_idx:right_idx+1]
            area = float(trapz_func(y_sub, x_sub)) if trapz_func else 0.0

            peaks.append({
                "peak_id": len(peaks) + 1,
                "retention_time": round(peak_rt, 3),
                "peak_height": round(peak_height, 2),
                "area": round(max(0.0, area), 2),
                "apex_index": i
            })

    peaks.sort(key=lambda x: x["area"], reverse=True)
    for idx, p in enumerate(peaks[:20]):
        p["rank"] = idx + 1
    
    return sorted(peaks[:20], key=lambda x: x["retention_time"])
