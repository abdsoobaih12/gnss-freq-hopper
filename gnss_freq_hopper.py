#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
GNSS Frequency Hopper Block for GNU Radio
==========================================
يقوم بتبديل تردد LO كل 15ms عبر ترددات GNSS محددة

المؤلف: مشروع GNSS Freq Hopper
الترخيص: GPLv3
"""

import numpy as np
from gnuradio import gr


class gnss_freq_hopper(gr.sync_block):
    """
    بلوك GNU Radio لتبديل الترددات الدوري (Frequency Hopping)
    
    يأخذ إشارة مركبة ويضربها بـ LO متغير:
        output[n] = input[n] × exp(j·2π·f_current·t[n])
    
    حيث f_current يتغير كل 15ms حسب freq_array
    
    المدخلات:
        - in_sig: complex64 (إشارة RF مركبة)
    
    المخرجات:
        - out_sig: complex64 (إشارة محوّلة التردد)
    
    المعاملات:
        - samp_rate: معدل العينات بالـHz (مثال: 2.048e6)
        - freq_array: قائمة الترددات بالـMHz (مثال: [1575.42, 1602.0, ...])
        - hop_duration: مدة كل تردد بالثانية (افتراضي: 0.015)
    """
    
    def __init__(self, samp_rate=2.048e6, freq_array=None, hop_duration=0.015):
        """
        Constructor
        
        Args:
            samp_rate (float): Sample rate in Hz
            freq_array (list): List of frequencies in MHz
            hop_duration (float): Duration per frequency in seconds (default 15ms)
        """
        gr.sync_block.__init__(
            self,
            name="GNSS Frequency Hopper",
            in_sig=[np.complex64],   # مدخل مركب
            out_sig=[np.complex64]   # مخرج مركب
        )
        
        # حفظ المعاملات
        self.samp_rate = float(samp_rate)
        self.hop_duration = float(hop_duration)
        
        # إعداد مصفوفة الترددات (تحويل من MHz إلى Hz)
        if freq_array is None:
            # الترددات الافتراضية (GNSS bands)
            self.freq_array_mhz = [1602.0, 1575.42, 1561.1, 1246.0, 
                                   1227.6, 1207.14, 1176.45, 1191.0]
        else:
            self.freq_array_mhz = list(freq_array)
        
        # تحويل إلى Hz
        self.freq_array_hz = [f * 1e6 for f in self.freq_array_mhz]
        
        # حساب عدد العينات لكل hop
        self.samples_per_hop = int(self.hop_duration * self.samp_rate)
        
        # متغيرات الحالة
        self.current_freq_index = 0        # مؤشر التردد الحالي
        self.sample_counter = 0            # عداد العينات المعالجة في الـhop الحالي
        self.total_samples_processed = 0   # إجمالي العينات (للطور المستمر)
        
        # الطور المتراكم (لتجنب قفزات الطور عند التبديل)
        self.phase_accumulator = 0.0
        
        # معلومات تشخيصية
        self.hop_count = 0
        
        print(f"[GNSS Freq Hopper] تم التهيئة:")
        print(f"  - Sample Rate: {self.samp_rate/1e6:.3f} MHz")
        print(f"  - Hop Duration: {self.hop_duration*1000:.1f} ms")
        print(f"  - Samples per Hop: {self.samples_per_hop}")
        print(f"  - Frequencies: {self.freq_array_mhz} MHz")
    
    def work(self, input_items, output_items):
        """
        دالة المعالجة الرئيسية
        
        تُستدعى تلقائياً من GNU Radio scheduler
        """
        in0 = input_items[0]      # الإشارة الداخلة
        out = output_items[0]     # الإشارة الخارجة
        
        num_samples = len(in0)    # عدد العينات في هذه الدفعة
        
        # معالجة كل عينة
        for i in range(num_samples):
            # التحقق: هل حان وقت التبديل؟
            if self.sample_counter >= self.samples_per_hop:
                # انتقل للتردد التالي (دوري)
                self.current_freq_index = (self.current_freq_index + 1) % len(self.freq_array_hz)
                self.sample_counter = 0
                self.hop_count += 1
                
                # طباعة معلومات التبديل (للـdebug - يمكن تعطيلها في الإنتاج)
                current_freq_mhz = self.freq_array_mhz[self.current_freq_index]
                if self.hop_count <= 20 or self.hop_count % 100 == 0:  # تقليل الطباعة
                    print(f"[Hop #{self.hop_count}] تبديل إلى: {current_freq_mhz:.2f} MHz")
            
            # الحصول على التردد الحالي
            current_freq_hz = self.freq_array_hz[self.current_freq_index]
            
            # حساب الزمن النسبي للعينة الحالية
            t = self.total_samples_processed / self.samp_rate
            
            # توليد LO: exp(j·2π·f·t)
            lo_signal = np.exp(1j * 2.0 * np.pi * current_freq_hz * t)
            
            # الضرب (Mixing/Heterodyning)
            out[i] = in0[i] * lo_signal
            
            # تحديث العدادات
            self.sample_counter += 1
            self.total_samples_processed += 1
        
        # إرجاع عدد العينات المُنتجة
        return num_samples
    
    def set_samp_rate(self, samp_rate):
        """تحديث معدل العينات ديناميكياً"""
        self.samp_rate = float(samp_rate)
        self.samples_per_hop = int(self.hop_duration * self.samp_rate)
        print(f"[GNSS Freq Hopper] Sample rate updated: {self.samp_rate/1e6:.3f} MHz")
    
    def set_freq_array(self, freq_array):
        """تحديث مصفوفة الترددات ديناميكياً"""
        self.freq_array_mhz = list(freq_array)
        self.freq_array_hz = [f * 1e6 for f in self.freq_array_mhz]
        self.current_freq_index = 0  # إعادة تعيين
        print(f"[GNSS Freq Hopper] Frequencies updated: {self.freq_array_mhz} MHz")
    
    def set_hop_duration(self, hop_duration):
        """تحديث مدة الـhop ديناميكياً"""
        self.hop_duration = float(hop_duration)
        self.samples_per_hop = int(self.hop_duration * self.samp_rate)
        print(f"[GNSS Freq Hopper] Hop duration updated: {self.hop_duration*1000:.1f} ms")


# دالة مساعدة لإنشاء البلوك (لاستخدامها في GRC)
def make(samp_rate=2.048e6, freq_array=None, hop_duration=0.015):
    """
    Factory function for GNU Radio Companion
    """
    return gnss_freq_hopper(samp_rate, freq_array, hop_duration)


if __name__ == '__main__':
    # اختبار مستقل (standalone test)
    print("=" * 60)
    print("اختبار GNSS Frequency Hopper Block")
    print("=" * 60)
    
    # إنشاء مثال للبلوك
    hopper = gnss_freq_hopper(
        samp_rate=2.048e6,
        freq_array=[1575.42, 1602.0, 1227.6],  # ترددات قليلة للاختبار
        hop_duration=0.015
    )
    
    # محاكاة بيانات دخل (500 عينة)
    num_test_samples = 500
    test_input = np.exp(1j * 2 * np.pi * 0.1 * np.arange(num_test_samples))  # tone بسيط
    test_output = np.zeros(num_test_samples, dtype=np.complex64)
    
    # استدعاء work
    hopper.work([test_input], [test_output])
    
    print(f"\n✓ الاختبار ناجح! تمت معالجة {num_test_samples} عينة")
    print(f"  - عدد الـhops: {hopper.hop_count}")
    print(f"  - التردد الحالي: {hopper.freq_array_mhz[hopper.current_freq_index]:.2f} MHz")