#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
سكريبت اختبار مستقل لـ GNSS Frequency Hopper
يقوم بتوليد إشارة اختبار وتمريرها عبر البلوك وحفظ النتيجة
"""

import numpy as np
from gnuradio import gr, blocks, analog
from gnuradio import filter as gr_filter
from gnuradio.fft import window
import time
import sys

# استيراد البلوك المخصص
try:
    from gnss_freq_hopper import gnss_freq_hopper
except ImportError:
    print("❌ خطأ: لم يتم العثور على gnss_freq_hopper.py")
    print("   تأكد من وجود الملف في نفس المجلد أو في PYTHONPATH")
    sys.exit(1)


class test_gnss_hopper(gr.top_block):
    """
    Flowgraph للاختبار:
    Signal Source → GNSS Hopper → File Sink
                              ↘ Throttle → (اختياري: GUI sinks)
    """
    
    def __init__(self):
        gr.top_block.__init__(self, "GNSS Hopper Test")
        
        ##################################################
        # المتغيرات
        ##################################################
        self.samp_rate = samp_rate = 2.048e6  # 2.048 MHz
        
        # ترددات GNSS (MHz)
        self.gnss_freqs = [1602.0, 1575.42, 1561.1, 1246.0, 
                           1227.6, 1207.14, 1176.45, 1191.0]
        
        ##################################################
        # البلوكات
        ##################################################
        
        # 1. مصدر الإشارة: Tone بسيط عند 1 kHz
        self.analog_sig_source = analog.sig_source_c(
            samp_rate, 
            analog.GR_COS_WAVE, 
            1e3,      # 1 kHz tone
            1.0,      # Amplitude
            0         # Offset
        )
        
        # 2. البلوك المخصص
        self.gnss_hopper = gnss_freq_hopper(
            samp_rate=samp_rate,
            freq_array=self.gnss_freqs,
            hop_duration=0.015  # 15ms
        )
        
        # 3. Throttle (لمنع استهلاك 100% CPU)
        self.blocks_throttle = blocks.throttle(
            gr.sizeof_gr_complex, 
            samp_rate, 
            True
        )
        
        # 4. File Sink (حفظ إلى ملف)
        self.blocks_file_sink = blocks.file_sink(
            gr.sizeof_gr_complex, 
            'gnss_hopper_output.dat', 
            False
        )
        self.blocks_file_sink.set_unbuffered(False)
        
        # 5. Head (تحديد عدد العينات - للاختبار فقط)
        # نريد تسجيل 5 دورات كاملة عبر 8 ترددات
        # 5 دورات × 8 ترددات × 15ms × 2.048MHz = 1.2288M عينة
        num_samples = int(5 * 8 * 0.015 * samp_rate)
        self.blocks_head = blocks.head(gr.sizeof_gr_complex, num_samples)
        
        ##################################################
        # الاتصالات
        ##################################################
        self.connect((self.analog_sig_source, 0), (self.gnss_hopper, 0))
        self.connect((self.gnss_hopper, 0), (self.blocks_throttle, 0))
        self.connect((self.blocks_throttle, 0), (self.blocks_head, 0))
        self.connect((self.blocks_head, 0), (self.blocks_file_sink, 0))
        
        print("\n" + "="*60)
        print("تم بناء Flowgraph للاختبار")
        print("="*60)
        print(f"Sample Rate: {samp_rate/1e6:.3f} MHz")
        print(f"عدد العينات المُسجّلة: {num_samples:,}")
        print(f"المدة الزمنية: {num_samples/samp_rate:.2f} ثانية")
        print(f"الملف المُخرَج: gnss_hopper_output.dat")
        print("="*60 + "\n")


def main():
    """
    دالة الاختبار الرئيسية
    """
    print("\n" + "🚀 "*20)
    print("بدء اختبار GNSS Frequency Hopper")
    print("🚀 "*20 + "\n")
    
    # إنشاء وتشغيل الـflowgraph
    tb = test_gnss_hopper()
    
    try:
        print("▶️  تشغيل الـFlowgraph...")
        tb.start()
        
        # الانتظار حتى اكتمال المعالجة
        tb.wait()
        
        print("\n✅ الاختبار اكتمل بنجاح!")
        print(f"📁 تم حفظ البيانات في: gnss_hopper_output.dat")
        print(f"📊 لتحليل البيانات، استخدم:")
        print(f"   python analyze_output.py gnss_hopper_output.dat")
        
    except KeyboardInterrupt:
        print("\n⚠️  تم إيقاف الاختبار بواسطة المستخدم")
    finally:
        tb.stop()
        tb.wait()
        print("\n🏁 الاختبار منتهي.\n")


if __name__ == '__main__':
    main()