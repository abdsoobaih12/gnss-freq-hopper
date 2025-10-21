<p align="center">
  <img src="213.png" alt="GNSS Frequency Hopper Logo" width="250"/>
</p>

<h1 align="center">🛰️ GNSS Frequency Hopper</h1>
<p align="center">
  <b>Python + GNU Radio</b> project for frequency hopping across GNSS bands (GPS / GLONASS / Galileo)
</p>

---

## 🌍 الفكرة

مشروع لتطبيق مفهوم <b>تبديل التردد (Frequency Hopping)</b> ضمن نطاقات GNSS باستخدام Python و GNU Radio.  
يقوم البرنامج بتغيير التردد كل <b>15ms</b> بشكل متتابع عبر مجموعة من الترددات المعرفة في المصفوفة:

```python
freq_array = [1602.0, 1575.42, 1561.1, 1246.0, 1227.6, 1207.14, 1176.45, 1191.0]
