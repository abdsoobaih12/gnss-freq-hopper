# gnss-freq-hopper
# 🛰️ GNSS Frequency Hopper

مشروع تجريبي باستخدام **GNU Radio** و **Python** لتنفيذ قافز ترددي (Frequency Hopper) بين ترددات أنظمة GNSS المختلفة (GPS / GLONASS / Galileo).

---

## 🎯 الفكرة
يقوم البرنامج بتوليد إشارة (أو استقبالها) ثم تغيير ترددها كل **15ms** بالتتابع بين مجموعة من الترددات المحددة في مصفوفة `freq_array`.

---

## ⚙️ المتطلبات

```bash
conda create -n gnuradio python=3.10
conda activate gnuradio
conda install -c conda-forge gnuradio numpy matplotlib
