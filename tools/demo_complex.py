import sys, warnings
warnings.filterwarnings("ignore"); sys.stdout.reconfigure(encoding="utf-8")
import ethosoft_math as em

taslak = """Soru: Bir şirket 25000 TL'yi yıllık %18 bileşik faizle 3 yıl yatırıyor. Elde ettiği tutardan 12000 TL'lik bir makine alıyor, kalan parayla daire şeklindeki bir bahçeye çit çektiriyor (çitin metresi 85 TL). Bahçenin yarıçapı kaç metredir? Ayrıca yarıçap r ise r^2 - 7r + 12 = 0 denklemini çözüp en büyük kökü ile karşılaştır.

Çözüm:
1) 3 yıl sonraki tutar: <arac_cagrisi>carp(25000, us(bol(118, 100), 3))</arac_cagrisi>
2) Makineden sonra kalan: <arac_cagrisi>cikar(41075.8, 12000)</arac_cagrisi>
3) Çit uzunluğu (metre): <arac_cagrisi>bol(29075.8, 85)</arac_cagrisi>
4) Çevre = 2πr olduğundan r: <arac_cagrisi>ondalik("342.0682352941176/(2*pi)", 6)</arac_cagrisi>
5) Denklem: <arac_cagrisi>coz("r^2 - 7*r + 12 = 0", "r")</arac_cagrisi>
6) Kontrol: <arac_cagrisi>kombinasyon(10, 3)</arac_cagrisi> ve <arac_cagrisi>esit_mi("(r-3)*(r-4)", "r^2 - 7*r + 12")</arac_cagrisi>
"""
print(em.fill_results(taslak))
