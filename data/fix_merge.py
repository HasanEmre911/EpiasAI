import pandas as pd
import glob
import os
import warnings

# Gereksiz uyarıları gizle
warnings.simplefilter(action='ignore', category=FutureWarning)
warnings.simplefilter(action='ignore', category=UserWarning)

def robust_import():
    # Kodun çalıştığı klasörü bul
    current_dir = os.path.dirname(os.path.abspath(__file__))
    output_file = os.path.join(current_dir, 'merged_data.csv')
    
    print(f"📂 Çalışma Dizini: {current_dir}")
    print("🕵️  Dosyalar taranıyor (CSV ve Excel)...")

    # Hem .csv hem .xlsx dosyalarını bul
    files_csv = glob.glob(os.path.join(current_dir, "*.csv"))
    files_xlsx = glob.glob(os.path.join(current_dir, "*.xlsx"))
    files_xls = glob.glob(os.path.join(current_dir, "*.xls"))
    
    all_files = files_csv + files_xlsx + files_xls
    
    # Çıktı dosyasını listeden çıkar (varsa)
    all_files = [f for f in all_files if "merged_data.csv" not in f and "fix_merge" not in f]
    
    if not all_files:
        print("❌ HATA: Klasörde hiç veri dosyası bulunamadı!")
        return

    print(f"📄 Toplam {len(all_files)} dosya bulundu. İşleniyor...")
    df_list = []

    for filename in all_files:
        file_name_short = os.path.basename(filename)
        df = None
        
        # --- STRATEJİ 1: Excel Olarak Oku (En garantisi bu, uzantı csv olsa bile dene) ---
        try:
            df = pd.read_excel(filename)
            # print(f"  -> {file_name_short} Excel olarak okundu.")
        except:
            # --- STRATEJİ 2: CSV Olarak Oku (Virgül) ---
            try:
                df = pd.read_csv(filename, sep=',')
            except:
                # --- STRATEJİ 3: CSV Olarak Oku (Noktalı Virgül) ---
                try:
                    df = pd.read_csv(filename, sep=';')
                except:
                    print(f"❌ OKUNAMADI: {file_name_short} (Format belirsiz)")
                    continue

        # Veri Yüklendiyse Temizle
        if df is not None:
            try:
                # Sütun isimlerini temizle (Küçük harf, Türkçe karakter temizliği)
                df.columns = [str(c).lower().strip().replace(' ', '_').replace('.', '').replace('(', '').replace(')', '').replace('/', '') for c in df.columns]
                
                # PTF Sütununu Akıllıca Bul
                ptf_cols = [c for c in df.columns if 'ptf' in c]
                
                if ptf_cols:
                    # 'tl' yazanı önceliklendir, yoksa ilkini al
                    target = next((c for c in ptf_cols if 'tl' in c), ptf_cols[0])
                    df = df.rename(columns={target: 'ptf'})
                    
                    # Tarih Sütununu Bul
                    date_col = next((c for c in df.columns if 'tarih' in c), None)
                    if date_col:
                        df = df.rename(columns={date_col: 'tarih'})
                    
                        # Tarih ve Saat Birleştirme
                        if 'saat' in df.columns:
                            # Saat sütunu bazen "00:00" bazen "0" gelebilir, string yapıp topla
                            df['tarih'] = pd.to_datetime(df['tarih'].astype(str) + ' ' + df['saat'].astype(str))
                        else:
                            df['tarih'] = pd.to_datetime(df['tarih'])

                        # Sayı Formatı Düzeltme (1.234,56 -> 1234.56)
                        if df['ptf'].dtype == object:
                            df['ptf'] = df['ptf'].astype(str).str.replace('.', '').str.replace(',', '.').astype(float)
                        
                        # Sadece lazım olanları al ve listeye ekle
                        temp_df = df[['tarih', 'ptf']].copy()
                        # Boş satırları at
                        temp_df = temp_df.dropna()
                        df_list.append(temp_df)
                        print(f"  ✅ OKUNDU: {file_name_short} ({len(temp_df)} satır)")
                    else:
                        print(f"  ⚠️ Tarih sütunu yok: {file_name_short}")
                else:
                    print(f"  ⚠️ PTF sütunu yok: {file_name_short}")

            except Exception as e:
                print(f"  ❌ İŞLEME HATASI ({file_name_short}): {e}")

    # BİRLEŞTİRME VE KAYDETME
    if df_list:
        full_df = pd.concat(df_list).sort_values('tarih').reset_index(drop=True)
        # Yinelenen tarihleri temizle (Aynı dosya 2 kez indirilmişse)
        full_df = full_df.drop_duplicates(subset=['tarih'])
        
        full_df.to_csv(output_file, index=False)
        print("\n" + "="*40)
        print(f"🎉 BÜYÜK BAŞARI! Dosyalar birleştirildi.")
        print(f"📂 Kaydedilen Yer: {output_file}")
        print(f"📊 Toplam Veri: {len(full_df)} satır")
        print(f"📅 Tarih Aralığı: {full_df['tarih'].min()} - {full_df['tarih'].max()}")
        print("="*40)
    else:
        print("\n❌ Hiçbir dosya kurtarılamadı. Dosyaların bozuk olmadığından emin ol.")

if __name__ == "__main__":
    # Gerekli kütüphane kontrolü
    try:
        import openpyxl
    except ImportError:
        print("⚠️ UYARI: 'openpyxl' kütüphanesi eksik olabilir. Excel okumak için gereklidir.")
        print("Terminalden şunu çalıştırabilirsin: pip install openpyxl")
    
    robust_import()