#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
تحليل طيفي لخرج GNSS Frequency Hopper
يقرأ الملف المُنتَج ويعرض waterfall وspectrum لكل hop
"""

import numpy as np
import matplotlib.pyplot as plt
from matplotlib.gridspec import GridSpec
import sys


def read_complex_file(filename):
    """قراءة ملف complex64"""
    try:
        data = np.fromfile(filename, dtype=np.complex64)
        print(f"✓ تم قراءة {len(data):,} عينة من {filename}")
        return data
    except FileNotFoundError:
        print(f"❌ خطأ: الملف {filename} غير موجود")
        sys.exit(1)


def analyze_hopping(data, samp_rate=2.048e6, hop_duration=0.015, 
                    expected_freqs=[1602.0, 1575.42, 1561.1, 1246.0, 
                                   1227.6, 1207.14, 1176.45, 1191.0]):
    """
    تحليل frequency hopping
    
    Args:
        data: البيانات المركبة
        samp_rate: معدل العينات
        hop_duration: مدة كل hop
        expected_freqs: الترددات المتوقعة (MHz)
    """
    samples_per_hop = int(hop_duration * samp_rate)
    num_hops = len(data) // samples_per_hop
    
    print(f"\n{'='*60}")
    print(f"تحليل Frequency Hopping")
    print(f"{'='*60}")
    print(f"إجمالي العينات: {len(data):,}")
    print(f"العينات لكل hop: {samples_per_hop:,}")
    print(f"عدد الـhops: {num_hops}")
    print(f"الترددات المتوقعة: {expected_freqs}")
    print(f"{'='*60}\n")
    
    # إنشاء figure مع subplots
    fig = plt.figure(figsize=(16, 10))
    gs = GridSpec(3, 2, figure=fig, hspace=0.3, wspace=0.3)
    
    # 1. Waterfall Plot (عرض كل الـhops)
    ax_waterfall = fig.add_subplot(gs[0, :])
    
    # بناء مصفوفة 2D للـwaterfall (كل صف = FFT لـhop واحد)
    fft_size = 2048
    waterfall_data = []
    
    for hop_idx in range(min(num_hops, 100)):  # أول 100 hop للسرعة
        start_idx = hop_idx * samples_per_hop
        end_idx = start_idx + min(fft_size, samples_per_hop)
        segment = data[start_idx:end_idx]
        
        if len(segment) < fft_size:
            segment = np.pad(segment, (0, fft_size - len(segment)))
        
        # FFT
        spectrum = np.fft.fftshift(np.fft.fft(segment, fft_size))
        power_db = 20 * np.log10(np.abs(spectrum) + 1e-12)
        waterfall_data.append(power_db)
    
    waterfall_data = np.array(waterfall_data)
    
    # رسم الـwaterfall
    extent = [-samp_rate/2/1e6, samp_rate/2/1e6, 0, len(waterfall_data) * hop_duration * 1000]
    im = ax_waterfall.imshow(
        waterfall_data, 
        aspect='auto', 
        extent=extent,
        cmap='viridis',
        origin='lower',
        interpolation='nearest'
    )
    ax_waterfall.set_xlabel('التردد (MHz) - نسبة إلى المركز')
    ax_waterfall.set_ylabel('الزمن (ms)')
    ax_waterfall.set_title('Waterfall: Frequency Hopping عبر الزمن')
    ax_waterfall.grid(True, alpha=0.3)
    plt.colorbar(im, ax=ax_waterfall, label='القدرة (dB)')
    
    # 2. Spectrum لأول 4 hops
    detected_freqs = []
    
    for i in range(min(4, num_hops)):
        ax = fig.add_subplot(gs[1 + i//2, i%2])
        
        start_idx = i * samples_per_hop
        end_idx = start_idx + samples_per_hop
        segment = data[start_idx:end_idx]
        
        # FFT
        spectrum = np.fft.fftshift(np.fft.fft(segment))
        freqs = np.fft.fftshift(np.fft.fftfreq(len(segment), 1/samp_rate))
        power_db = 20 * np.log10(np.abs(spectrum) + 1e-12)
        
        # إيجاد الذروة
        peak_idx = np.argmax(power_db)
        peak_freq = freqs[peak_idx]
        detected_freqs.append(peak_freq)
        
        # رسم
        ax.plot(freqs/1e6, power_db, linewidth=0.8)
        ax.axvline(peak_freq/1e6, color='r', linestyle='--', alpha=0.7, 
                   label=f'Peak: {peak_freq/1e6:.2f} MHz')
        ax.set_xlabel('التردد (MHz)')
        ax.set_ylabel('القدرة (dB)')
        ax.set_title(f'Hop #{i+1} Spectrum')
        ax.grid(True, alpha=0.3)
        ax.legend(fontsize=8)
        ax.set_xlim([-samp_rate/2/1e6, samp_rate/2/1e6])
    
    plt.suptitle('GNSS Frequency Hopper - Spectrum Analysis', 
                 fontsize=16, fontweight='bold')
    
    # 3. طباعة الترددات المكتشفة
    print("\n📊 الترددات المكتشفة في أول 4 hops:")
    print("-" * 40)
    for i, freq in enumerate(detected_freqs):
        expected = expected_freqs[i % len(expected_freqs)]
        print(f"Hop #{i+1}: {freq/1e6:>10.2f} MHz (متوقع: {expected:>10.2f} MHz)")
    print("-" * 40)
    
    # حفظ الصورة
    output_filename = 'gnss_hopper_analysis.png'
    plt.savefig(output_filename, dpi=150, bbox_inches='tight')
    print(f"\n💾 تم حفظ التحليل في: {output_filename}")
    
    # عرض
    plt.show()


def main():
    """دالة رئيسية"""
    if len(sys.argv) < 2:
        print("الاستخدام: python analyze_output.py <input_file.dat>")
        print("مثال: python analyze_output.py gnss_hopper_output.dat")
        sys.exit(1)
    
    filename = sys.argv[1]
    
    print("\n" + "📡 "*20)
    print("بدء تحليل GNSS Frequency Hopper Output")
    print("📡 "*20)
    
    # قراءة البيانات
    data = read_complex_file(filename)
    
    # التحليل
    analyze_hopping(data)
    
    print("\n✅ التحليل مكتمل!\n")


if __name__ == '__main__':
    main()