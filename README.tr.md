# Zelij Core

[English](README.en.md) · [简体中文](README.zh-CN.md) · [繁體中文](README.zh-TW.md) · [日本語](README.ja.md) · [한국어](README.ko.md) · **Türkçe** · [Русский](README.ru.md) · [Tiếng Việt](README.vi.md) · [ไทย](README.th.md) · [Deutsch](README.de.md) · [Español](README.es.md) · [Français](README.md) · [Українська](README.uk.md) · [Polski](README.pl.md) · [Português (Brasil)](README.pt-BR.md) · [العربية](README.ar.md) · [فارسی](README.fa.md) · [Bahasa Indonesia](README.id.md) · [Italiano](README.it.md) · [Ελληνικά](README.el.md) · [മലയാളം](README.ml.md) · [Roman Urdu](README.ur.md) · [Română](README.ro.md)

[![ci](https://github.com/zelij-ai/zelij-core/actions/workflows/ci.yml/badge.svg)](https://github.com/zelij-ai/zelij-core/actions/workflows/ci.yml) [![version](https://img.shields.io/github/v/release/zelij-ai/zelij-core?label=version)](https://github.com/zelij-ai/zelij-core/releases) [![license](https://img.shields.io/badge/license-AGPL--3.0-1c1917)](LICENSE)

**%100 yapay zekâ yerlisi girişiminizi kurun.** Dört ajanın sizin için çalıştığı tek bir ofis: onlar önerir, siz karar verirsiniz. Sizin makineniz, sizin Claude anahtarınız, sizin verileriniz; hiçbir şey dışarıya bilgi göndermez.

![Zelij Core akvaryumu: kurucu ve dört ajan konuşuyor, kararlar öneriyor ve onaylananları uyguluyor](docs/img/aquarium.gif)

*Simüle edilmiş bir günün akvaryumu (burada Fransızca gösterilmiştir). Kendi kurulumunuzda her kart, ajanlarınızın gerçek bir eylemidir; canlıdır ve yirmi dört saat boyunca yeniden oynatılabilir. Altın rengi sizsiniz: sizin kararınızdan önce bağlayıcı hiçbir şey olmaz. Yüzler kurgusal karakterlere aittir.*

## Çekirdek ne yapar

- **Ofis**: tek bir sayfa. Bekleyen kararlar, özel kalem müdürüne bir talep, maliyetleriyle birlikte son çalıştırmalar, günlük, ajanlar, kurulu modüller.
- **Karar paketi**: amaç, öneri, neden şimdi, seçenekler, tavsiye, riskler, geri alınabilirlik, plan, geri dönüş, etki. Eksik bir paket açılmaz. Onaylayın, reddedin ya da ajana iletilen zorunlu bir talimatla değişiklik isteyin.
- **Ev kuralları**: bağlayıcı hiçbir şey (para, kamuya açıklık, silme, geri alınamaz olan) kararsız yapılmaz; bir olgu tarihli ve kaynaklıdır ya da «doğrulanmadı» olarak işaretlenir; günlük asla silinmez.
- **Geçit**: kurucunun Claude anahtarı, her çağrının maliyeti kullanımdan ve tarihli kamu fiyatlarından hesaplanır, aşıldığında engelleyen aylık tavan.
- **Yürütücü**: sınırlı bir çağrı döngüsü (ajan başına tur bütçesi), ölçülü araçlar, modelin reddi bir sonuç olarak ele alınır.
- **Modüller**: çekirdeği genişletmenin tek yolu. Kararlı arayüz, yayıncı tarafından Ed25519 ile imzalanmış `pack.json` bildirimi, her dosyanın özeti imza kapsamında, kurulumdan önce doğrulama. Dağıtım hedefleri ve ek ajanlar hep bu yoldan gelir.
- **Finans**: teyit edilmiş satışlar (salt okunur Stripe içe aktarımı ya da kanıtla elle giriş), her ay yinelenen beyan edilmiş giderler, ölçülen ajan maliyeti, aylık defter, muhasebeci için CSV dışa aktarımı. Hiçbir şey beyan edilmez ya da faturalanmaz.
- **Kişiler**: kişi başına bir kart, zorunlu yasal dayanak, saklama süresi, yazışmalar, kullanılan haklar; itiraz eden bir kişi artık hiçbir şey almaz, süresi dolan bir kişi unutulur ve yalnızca haklar günlüğü kalır.
- **Yayınlama**: pazarlama ajanının yazdığı bir sayfa önce taslak, sonra bir karar olur; onaylandığında siteye GitHub çekme isteği ya da WordPress taslağı olarak önerilir. Son hamle, birleştirmek ya da yayınlamak, sizindir.
- **Cebinizde**: her karar telefonunuza ulaşır; iki imzalı tek kullanımlık bağlantı içeren e-postayla ya da üç düğmeli Telegram ile. Metro kuyruğunda onaylarsınız; akvaryum yanıt verir vermez hareket eder. Masadakiyle aynı kapı, aynı günlük.
- **Akvaryum**: ajanlarınızın çalışmasını izleyin; her baloncuk son 24 saatin gerçek bir eylemidir, noktalı halkalar açık pozisyonlardır. «by zelij.ai» rozetli, paylaşılabilir herkese açık bir sayfa.
- **Katalog**: ücretsiz sürümün içermediği şeyler dürüstçe adlandırılmış; yayıncıdan satın alınan bir modül buraya imzalı ve doğrulanmış olarak kurulur. Hiçbir ödeme ofisten geçmez.
- **Yazılım fabrikası**: İnşaatçı tek bir depoda okur ve önerir; güvenlik kapısından geçen çekme istekleriyle (300 satır, yalnızca metin, gizli bilgi yok, altyapı dosyası yok, OSV'ye göre bilinen açığı olmayan bağımlılıklar); SSH üzerinden bir Linux sunucusuna ya da OVH'ye (alan adı ve DNS API ile) atomik geçiş, duman testi ve geri dönüşle dağıtım; alan adı sondası; ofisin günlük yedeği. Asla birleştirmez, asla ödeme yapmaz, ofise asla dokunmaz.
- **Ajanlar**: ajan başına bir klasör, basit bir başlık ve Fransızca talimatlar içeren bir `agent.md`. Dört ajan: Camille Aubert (özel kalem müdürü), Élise Tanguy (büyüme, pazarlama ve ürünler), Nour Bellamy (finans ve müşteriler), Sacha Ferrand (inşaatçı, yazılım fabrikası). Kurucu ofisten her birine doğrudan seslenir; bir ajanı ve bir görevi belirten onaylanmış bir paket, planın sınırları içinde hemen çalışır.

## Anahtarsız, bir dakikada deneyin

```bash
git clone https://github.com/zelij-ai/zelij-core.git && cd zelij-core
docker compose -f docker-compose.demo.yml up --build
```

`http://localhost:8000` adresini açın ve gösterime girin: kurgusal bir şirket, dört simüle ajan, onaylanacak kararlar, günlerini yeniden oynatan akvaryum. Anahtar yok, hesap yok, maliyet yok; hiçbir modele hiçbir şey gönderilmez ve durdurduğunuzda her şey kaybolur. İkna olduğunuzda aşağıdaki gerçek kuruluma geçin. Ofisin kendisi Fransızcadır.

## Başlatma

```bash
cp .env.example .env     # Claude anahtarı, tavan, SECRET_KEY, veritabanı parolası
docker compose up -d --build
```

Ofis `http://localhost:8000` adresinde yanıt verir. SMTP olmadan giriş bağlantısı konteyner günlüklerine yazılır (`docker compose logs core-app`).

Tam kılavuzlar (İngilizce): **[Kurulum](docs/INSTALLATION.en.md)** (boş makineden https ofise, SMTP, yazılım fabrikası, yedekler, sorun giderme), **[Kullanım kılavuzu](docs/MODE-D-EMPLOI.en.md)** (her sayfa, ajanlar, kararlar, maliyet). Kurucunun ve ajanların fotoğrafları [`portraits/`](portraits/README.md) klasörüne konur (açıklama Fransızca).

Yerel derleme olmadan yayınlanmış imajdan (sürümü sabitlemek için `.env` içinde `CORE_IMAGE_TAG=v…`):

```bash
docker compose -f docker-compose.yml -f docker-compose.image.yml up -d
```

Docker olmadan yerelde:

```bash
pip install -r requirements-dev.txt
uvicorn core.bureau.app:app --reload
```

## Yayıncının açık anahtarı

Katalog modülleri zelij.ai tarafından imzalanır. `ZELIJ_CLE_PUBLIQUE` içine konacak açık anahtar (`.env.example` içinde zaten doldurulmuştur):

```
8da6c92455558c15a1566b333cef22fb5fc60aad9ffbf811f372e4bb7eacc42a
```

## Güvenlik

Çekirdeğin garanti ettiği ve test edilen şeyler (`tests/test_securite.py`):

- **Modüller**: bir modül yalnızca yayıncı tarafından imzalanmışsa (Ed25519) kurulur ve çalışır; imza her kod dosyasının SHA-256 özetini kapsar: imzadan sonra değiştirilen, eklenen ya da kaldırılan bir dosya modülü devre dışı bırakır.
- **Giriş**: 20 dakikalık tek kullanımlık bağlantılar, veritabanında özetlenmiş; bağlantı taleplerinde adres başına, IP başına ve genel frenler, böylece ofis asla bir e-posta aktarıcısı olmaz; üretimde SMTP yapılandırılmamışsa hiçbir bağlantı oluşturulmaz ya da günlüğe yazılmaz.
- **Formlar**: HMAC oturum çerezi, `HttpOnly`, `SameSite=Strict`, her POST'ta köken denetimi ve oturum başına CSRF karşıtı belirteç.
- **Sayfalar**: katı içerik güvenlik politikası (`default-src 'self'`, satır içi betik yok, çerçeve yok), `nosniff`, `X-Frame-Options`, `Referrer-Policy`, köken https ise HSTS.
- **Ajanlar**: bir ajanın okuduğu her şey (web sayfası, depo dosyası) ona dış içerik olarak çerçevelenmiş gelir, asla talimat olarak değil; bir ajan yalnızca kartındaki araçları çalıştırır ve özel bir veri okuduğu andan itibaren yalnızca şirketin kendi sitesini çağırabilir; yalnızca herkese açık https adreslerini okur (özel, geri döngü, yerel bağlantı adresleri ve iç adlar her yönlendirme adımında reddedilir, yanıt sınırlıdır); güvenlik kapısı gizli bilgileri, altyapı dosyalarını, üçüncü taraf betiklerini, çerçeveleri ve ağ çağrılarını engeller.
- **Konteyner**: ayrıcalıksız kullanıcı, salt okunur dosya sistemi, yetenek yok, ayrıcalık yükseltme yok; SSH sunucusunun ana bilgisayar anahtarı sabitlenebilir (`SSH_CLE_HOTE`).
- **Muhasebe dışa aktarımı**: elektronik tablo formülüne benzeyen hücreler etkisizleştirilir.

Bir açığı, düzeltmeden önce yayımlamadan `securite@zelij.ai` adresine bildirin. Her sürümden önce `pip-audit -r requirements.txt` ve `bandit -r core scripts -ll` boş dönmelidir.

## Katkı ve sürümler

`CONTRIBUTING.md` (Fransızca) bir katkının bir sürüme nasıl girdiğini anlatır; katkıda bulunulan bir dağıtım hedefinin, karşılık gelen paketi ömür boyu ücretsiz kazandırdığı kuralı da dahil. `SECURITY.md` bir açığın nasıl bildirileceğini, `CHANGELOG.md` her sürümün neyi değiştirdiğini ve kurucuya ne kaldığını anlatır.

## Testler ve yayın denetimi

```bash
python -m pytest -q
python scripts/controle_publication.py
```

Yayın denetimi anahtarları, IP adreslerini, iç kodları, kişisel e-posta adreslerini, açık metin parolaları ve depoda asla yer almayan özel bir listenin (`ZELIJ_CORE_INTERDITS`) terimlerini reddeder.

## Lisans

GNU AGPL v3. Telif hakkı (C) 2026 zelij.ai. Değişikliklerinizi aynı lisansla yayımlamanız koşuluyla çekirdeği kullanabilir, değiştirebilir ve yeniden dağıtabilirsiniz. zelij.ai'yi çalıştıran tam sürüm yayıncıya aittir.

by zelij.ai — https://zelij.ai/
