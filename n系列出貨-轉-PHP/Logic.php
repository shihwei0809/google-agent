<?php
class ShippingHelper {
    public static function toHalfWidth($str) {
        return mb_convert_kana($str, "as", "UTF-8");
    }

    public static function normalizeBatch($str) {
        if (!$str) return "";
        $half = self::toHalfWidth($str);
        return preg_replace('/[^a-zA-Z0-9]/', '', $half);
    }

    public static function cleanMatMaster($str) {
        if (!$str) return "";
        $s = strtoupper(trim((string)$str));
        if (str_contains($s, ' ')) $s = explode(' ', $s)[0];
        $s = preg_replace('/^\d+L/', 'L', $s);
        return $s;
    }
}
